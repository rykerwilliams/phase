# Phase 61 — Swiss-Pairing Tournament Organizer — PLAN

This plan captures the rollout sequencing from discussion #5314, refined with
this session's verification findings (CONTEXT.md, RESEARCH.md). No code is
written here — this is the design a future `engine-implementer` pass should
execute against.

## Mandatory architectural sections

### Pattern Coverage — build for the class, not one tournament format

Swiss pairing, tiebreaker math, and bye handling must be built as general
algorithms parameterized by player count and `ScoringPolicy`, not hardcoded
to a specific round count or point values. The MTR round-count table
(Appendix E) is a *default lookup*, not a hardcoded round count — an
organizer overriding total rounds must work identically to the default path.
Single-elimination for 4-8 players (also in Appendix E) is a second bracket
*shape* the same `TournamentManager` must support, not a special case bolted
onto Swiss — see §2 below for how that's scoped.

### Building Blocks — reused, not reinvented

| Need | Existing block reused | Location |
|------|----------------------|----------|
| Dispatch pattern (`handle(conn, msg, env) -> Vec<Outbound>`) | `Broker::handle` | `crates/lobby-broker/src/broker.rs:136` |
| Per-connection state extension pattern | `ConnState` | `crates/lobby-broker/src/broker.rs:46` |
| Fan-out to subscribers | `Outbound::{AddSubscriber,RemoveSubscriber,ToSubscribers}` | `crates/lobby-broker/src/broker.rs:63-76` |
| Deterministic time/rng for WASM-safe pure core | `BrokerEnv` | `crates/lobby-broker/src/env.rs` |
| Token-based authority surviving a socket bounce | `player_tokens`/`seat_for_token`/`generate_player_token` | `crates/server-core/src/draft_session.rs:27-47`, `session.rs` |
| Native reaper wiring pattern | `broker.reap_expired(300, &SysEnv)` call site | `crates/phase-server/src/main.rs:1000` |
| Deterministic test harness for pure broker logic | `FakeEnv` | used throughout `lobby.rs`/`broker.rs` tests |

New building blocks introduced (all general, none single-card/single-format):
`TournamentManager`, `ScoringPolicy`, `SwissPairing` (score-group +
backtracking), `TiebreakStanding` (MTR tiebreak computation), organizer/player
token minting reusing the same primitive `draft_session.rs` already uses.

### Logic Placement

All pairing, scoring, tiebreaker, and expiry logic lives in
`crates/lobby-broker/src/tournament.rs` — the pure core. `phase-server` and
the Cloudflare Worker shell are thin dispatch/serialization boundaries, per
CLAUDE.md's "engine [here: broker core] owns all logic" principle applied to
this crate. The frontend renders `TournamentView`/`TournamentStanding`
exactly as computed server-side; it must not recompute standings, tiebreaks,
or pairing itself.

### Extension vs Creation

This extends `lobby-broker`, it does not fork it: `Broker` gains one
additive field (`tournaments: TournamentManager`), `ConnState` gains two
additive fields (token-shaped, not bare identifiers — see §3), and
`LobbyClientMessage`/`LobbyServerMessage` gain additive variants. No existing
lobby behavior changes.

### Analogous Trace

Traced `LobbyManager`/`Broker::handle`/`ConnState` end-to-end (RESEARCH.md
§5) before designing `TournamentManager`'s shape, and traced
`draft_session.rs`'s token model end-to-end (RESEARCH.md §7) before designing
the organizer/player-token authority fix. Both traces are cited with
file:line evidence in RESEARCH.md, not assumed from the discussion's prose.

## 1. `ScoringPolicy` — first-class, TO-configurable, MTR defaults

```rust
/// Tournament match-point scoring. MTR §2.1 defaults (3/1/0); TO-overridable
/// at tournament creation for communities running variant conventions (e.g.
/// some Old School/93-94-adjacent groups score draws as 0 to discourage
/// intentional draws). Lives in `lobby-broker`, never touches `GameState` —
/// see CONTEXT.md's "Relationship to adjacent work" for why this is NOT a
/// field of the engine crate's `CustomFormatDef`/`LegacyRuleSet` (phase 58).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ScoringPolicy {
    pub win_points: u8,
    pub draw_points: u8,
    pub loss_points: u8,
}

impl Default for ScoringPolicy {
    // MTR §2.1: 3 for a win, 1 for a draw, 0 for a loss.
    fn default() -> Self {
        Self { win_points: 3, draw_points: 1, loss_points: 0 }
    }
}
```

Threaded through match-point accumulation (`points_for(&MatchResult,
ScoringPolicy) -> u32` style helper) and the tiebreaker calculations
identically — a tiebreaker's "total possible points" denominator (3 ×
rounds played, per MTR Appendix C) must use `scoring.win_points`, not a
hardcoded `3`, so a non-default policy's percentages stay internally
consistent. Tiebreaker *order* and the 0.33 floor are not exposed as
overridable per the discussion's framing (less likely to need per-TO
variance than point values) — ship them fixed to the MTR values, revisit
only if a real request surfaces.

`ScoringPolicy` is supplied once at `CreateTournament` time and stored on
the `TournamentMeta`, immutable for the tournament's lifetime (changing
scoring mid-event would retroactively corrupt already-reported standings).

## 2. `TournamentManager` shape

```rust
pub struct TournamentManager {
    tournaments: HashMap<String, TournamentMeta>,
}

pub struct TournamentMeta {
    pub code: String,
    pub name: String,
    pub organizer_token: String,          // minted at creation, NOT socket-bound
    pub scoring: ScoringPolicy,
    pub bracket: BracketShape,            // Swiss | SingleElimination
    pub total_rounds: u32,                // organizer override, else MTR Appendix E default
    pub current_round: u32,
    pub status: TournamentStatus,         // Registration | InProgress | Completed
    pub players: Vec<TournamentPlayer>,
    pub pairings: Vec<TournamentPairing>,
    pub created_at: u64,
    pub last_activity_at: u64,            // bumped on every mutation — fixes #4615 finding #3
}

pub struct TournamentPlayer {
    pub player_key: String,
    pub player_token: String,             // minted at join, NOT socket-bound — fixes #4615 finding #1
    pub display_name: String,
    pub dropped: bool,
    pub had_bye: bool,                    // bye assignment prefers players who haven't had one
}
```

`BracketShape::SingleElimination` covers the MTR Appendix E 4-8 player case
as a sibling bracket shape on the *same* manager, not a separate feature —
per "build for the class," a tournament tool that only does Swiss is
incomplete relative to the MTR table it cites as its own round-count source.

**Swiss pairing algorithm** (score-group pairing with backtracking):
1. Group active (non-dropped) players by current match points into
   descending score groups.
2. Within each group (and floating down from the group above when a group
   has an odd count), attempt to pair without repeating a prior opponent,
   using backtracking search per group — **with the #4615 base-case bug
   fixed**: `backtrack_pair` must treat exactly one remaining player as a
   **successful** partial pairing (the float candidate), not a dead end.
   This is a one-line fix to the base case (`if players.len() == 1 { return
   Some(acc.clone()); }`), not a rewrite — confirmed in RESEARCH.md §4.
3. Bye assignment prefers a player who hasn't already had one this
   tournament (`had_bye` flag) among any players left unpaired after
   float-down.
4. A bye scores as a 2-0 win per MTR Appendix C (3 match points, 6 game
   points via `scoring.win_points`), and the bye round is **excluded** (not
   zero-filled) when computing that player's own opponents'-percentage
   stats for later rounds, since there was no real opponent that round.

**Standings / tiebreaker computation** (MTR §3.1 order, Appendix C floors):
1. Match points (via `ScoringPolicy`).
2. Opponents' match-win percentage (average across opponents actually
   faced, excluding bye rounds).
3. Game-win percentage (game points earned ÷ total possible, floored at
   0.33).
4. Opponents' game-win percentage (average across opponents faced).

**Match result validation** — fixes #4615 finding #2 directly:
```rust
fn validate_match_result(pairing: &TournamentPairing, result: &MatchResult) -> Result<(), String> {
    // existing: winner must be one of the two paired players
    // existing: a draw must not specify a winner
    // NEW: when wins differ, winner_player_key MUST equal whichever
    // player has the higher game-win count.
    if result.player_a_wins != result.player_b_wins {
        let expected = if result.player_a_wins > result.player_b_wins {
            &pairing.player_a
        } else {
            player_b
        };
        if result.winner_player_key.as_ref() != Some(expected) {
            return Err("Winner must match the player with more game wins".to_string());
        }
    }
    Ok(())
}
```

**Expiry** — fixes #4615 finding #3 directly: `last_activity_at` bumped on
every mutating call (`join_tournament`, `start_round`, `report_result`,
`drop_player`), and `check_expired` filters on `last_activity_at`, not
`created_at`. Additionally, per the discussion's proposal, staleness reaping
should be restricted to `TournamentStatus::Registration` (abandoned
registration, nobody ever started) — an `InProgress` tournament should not
be reaped by a fixed timeout at all, only by genuine inactivity, since a
real Swiss event with human players between rounds can easily exceed any
reasonable fixed timeout.

## 3. Authority model — organizer/player tokens, not socket identity

Fixes #4615 finding #1 directly, using the `draft_session.rs` precedent
(RESEARCH.md §7) as the concrete pattern to mirror:
- `CreateTournament` mints an `organizer_token` (reuse
  `generate_player_token()` from `server-core::session`, the same primitive
  draft pods already use) and returns it to the creating client. The
  *tournament's* record of who the organizer is keys off this token, not
  `ConnState`/the socket.
- `JoinTournament` mints a `player_token` per joining player, same mechanism.
- `ConnState` gains `organized_tournaments: Vec<String>` /
  `joined_tournaments: Vec<(String, String)>` (tournament code, player_token)
  purely as **local reconnect convenience** (so a client that already has a
  token doesn't need to re-type it) — never as the source of authority.
  Organizer-gated actions (`StartTournamentRound`, `EndTournament`) validate
  the *token* presented in the message payload against
  `TournamentMeta.organizer_token`; player-gated actions
  (`ReportMatchResult`, `DropFromTournament`) validate against the paired
  `TournamentPlayer.player_token`.
- Consequence: closing/reopening the tournament page's socket does **not**
  unregister the tournament or drop a player's standing — exactly the bug
  class #4615 shipped. The tournament page keeps one socket open for the
  page's lifetime purely as a live-update optimization, per the discussion's
  framing, not because closing it would be unsafe.

## 4. Proposed rollout — four independently reviewable PRs

Unchanged in sequencing from the discussion, refined with this session's
corrections folded in as explicit acceptance criteria per PR:

**PR 1 — pure core, no wiring.**
`crates/lobby-broker/src/tournament.rs`: `TournamentManager`, `ScoringPolicy`,
Swiss pairing (score-group + backtracking with the **fixed** base case),
single-elimination bracket shape, bye assignment, MTR-cited standings.
Exhaustively unit tested with `FakeEnv`, same style as `lobby.rs`/`broker.rs`.
**Acceptance criteria beyond "compiles and has tests":**
- A dedicated test for an odd-sized bracket (5, 7, 9 players) asserting the
  backtracking path succeeds without falling back to greedy rematch-prone
  pairing — this is the exact case #4615's 90 passing tests missed.
- A dedicated test asserting `validate_match_result` rejects a report where
  `player_a_wins != player_b_wins` but `winner_player_key` names the loser.
- Test vectors pinned against the MTR's own worked examples where practical
  (per the discussion's proposal).
- No protocol changes, no shell wiring — reviewable purely as an algorithm +
  state machine, independent of PRs 2-4.

**PR 2 — protocol + native server.**
`protocol.rs` new `LobbyClientMessage`/`LobbyServerMessage` variants and view
types (`TournamentView`, `TournamentSummary`, `TournamentStanding`,
`PairingView`), protocol version bump — **from 13 to 14** (confirmed current
value is 13, not 12 — see CONTEXT.md finding #4; do not copy #4615's stale
"v12" framing). `broker.rs` gains the `tournaments: TournamentManager` field
and the `ConnState` organizer/joined-tournament fields **as tokens** (§3
above, not bare identifiers). Native server dispatch arms in
`phase-server/src/main.rs`. Reaper keyed off `last_activity_at`, restricted
to `Registration`-status tournaments (§2 above).

**PR 3 — Cloudflare Worker shell.**
`lobby-worker/broker-wasm` `mutates_lobby` match extension, `lobby-do.ts`
`ConnAttachment` extension, and **the corrected `is_empty()` predicate**:
```rust
pub fn is_empty(&self) -> bool {
    self.inner.lobby().is_empty() && self.inner.tournaments().is_empty()
}
```
confirmed today's `is_empty()` (`lobby-worker/broker-wasm/src/lib.rs:168-170`)
only checks `self.inner.lobby()` — this predicate MUST be updated in the same
PR that adds the `tournaments` field to `Broker`, not deferred, or a
tournament-only Durable Object will stop rescheduling its cleanup alarm
(exactly #4615's finding #4).

**PR 4 — frontend.**
`adapter/types.ts` mirrors, `tournamentClient.ts`, `TournamentLandingPage.tsx`
/`TournamentPage.tsx` + presentational components, i18n keys from day one, routes/nav
entry. **Acceptance criteria beyond "renders":**
- Every RPC handler must close its socket via a single shared
  connect/request/close wrapper (or a `finally` block) — #4615 leaked a
  socket on the error path of every single RPC handler (six confirmed
  instances, RESEARCH.md §3b), not just one; design the client so this bug
  class is structurally impossible rather than manually replicating
  `finally { client?.close(); }` six times.
- Explicit socket-close on unmount, including the cancelled-connect race
  (the `cancelled` flag pattern from #4615's own code was present but
  incomplete — it set the flag but never called `.close()` on the socket
  that resolved after cancellation).
- All new UI chrome routed through `t()` per `client/src/i18n/README.md`
  from the first commit — no English-only strings landing then retrofitted.

## 5. Explicitly out of scope for v1 (unchanged from discussion, confirmed not contradicted by this session's findings)

- Full-mode (server-managed `GameSession`) auto-launch per pairing — v1
  stays lobby-only, matching #4612's original framing exactly.
- Central validation of *reported score content* beyond winner/game-win
  consistency (§2's `validate_match_result` fix) — MTR's own model is
  self-reporting (§2.4), and the broker already trusts client-supplied
  identity elsewhere (deck contents aren't server-validated either, per
  #4612's own stated limitation). The authority-token fix (§3) is about
  *who* may report, not fact-checking *what* they report.
- `ScoringPolicy` hooking into the custom-format-engine (phase 58) —
  see CONTEXT.md's "Relationship to adjacent work." Recommend building
  `ScoringPolicy` standalone in `lobby-broker` regardless of phase 58's
  landing order.
- Auto-advance round timers — leave organizer-gated for v1 pending
  maintainer input; additive later either way.

## 6. Testing

Per CLAUDE.md's "test the building block, not the special case": tests
target `TournamentManager`'s pairing/standings/expiry functions across their
parameter range (varying player counts including odd/even, varying
`ScoringPolicy` values including a non-default draw-value policy, varying
bracket shapes) — not a single fixed "8-player Swiss tournament" happy-path
test. The two specific regression tests called out in PR 1's acceptance
criteria (odd-bracket backtracking, winner/game-win consistency) exist
precisely because #4615's existing 90 tests didn't cover them; any building
block introduced here needs a test that would have caught each of the seven
review findings, not just tests for the successful path.
