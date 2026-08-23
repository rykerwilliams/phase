# Phase 61 — Swiss-Pairing Tournament Organizer — RESEARCH

Evidence trail for CONTEXT.md. Everything under a numbered section marked
**[VERIFIED THIS SESSION]** was checked directly against a worktree of
`myfork/main` (commit `d65111246`) and/or the live GitHub API this session.
Everything under **[FROM DISCUSSION #5314, NOT RE-VERIFIED]** is taken as
given per the task's scope (MTR facts are out of scope for re-derivation).

## 1. Issue #4612 — the original proposal (full body)

`gh issue view 4612 --repo phase-rs/phase --json body` — fetched in full this
session (the task brief only pasted the first ~1500 chars). Key structural
points not visible in the truncated version the task gave:

- Explicitly scoped as **lobby-only** for v1: "Matches themselves are not
  orchestrated by the broker — exactly like today's P2P lobby, the broker
  only handles discovery/pairing/standings; players start their own game via
  the existing `CreateGameWithSettings`/`JoinGameWithPassword` flow for each
  paired table and self-report the result back to the tournament."
- Names the exact `ConnState` extension pattern it expects: "the existing
  `ConnState` ownership-stamp idiom (`host_game` → `tournament_organizer`)."
  This is the literal analogy #5314 uses to justify the token-based fix — the
  original issue proposed a bare-field stamp; the discussion's day-one fix is
  to make that stamp a token instead of a raw bool/socket-bound value.
- Full proposed protocol surface: client messages `CreateTournament`,
  `JoinTournament`, `DropFromTournament`, `StartTournamentRound`,
  `ReportMatchResult`, `EndTournament`, `ListTournaments`; server messages
  `TournamentCreated`, `TournamentUpdate`, `TournamentCompleted`,
  `TournamentListUpdate`; view types `TournamentView`, `TournamentSummary`,
  `TournamentStanding`, `PairingView`.
- Explicitly calls out "No central auth" as a *known, accepted* v1
  limitation in the original issue: "Match-result reporting trusts either
  paired player ... or the organizer, last-write-wins on conflicting
  reports — consistent with the rest of the broker, which already trusts
  client-supplied identity (e.g. deck contents aren't server-validated
  either)." This is worth noting: the *authority-token* fix from #5314 is
  about **who is allowed to report at all and whether that authority
  survives a socket bounce**, not about validating the reported score against
  some ground truth (there is none — MTR self-reporting, confirmed at MTR
  §2.4, is the model). Trusting a paired player's report content is
  deliberate and unchanged; only the identity/authority layer is being
  hardened.

## 2. PR #4615 — metadata and full file list

`gh pr view 4615 --repo phase-rs/phase --json body,files,state,createdAt,closedAt`:

- State: `CLOSED`, created 2026-06-29T21:46:06Z, closed 2026-06-30T02:21:47Z
  (same day — fast review-and-close cycle, not a long-lived stale PR).
- Test plan self-reported by the author: `cargo test -p lobby-broker` (90
  tests passing), `cargo test -p server-core --test lobby_wire_contract` (5
  tests), `cargo check -p phase-server` all green — i.e., the bugs the review
  found were **logic/architecture bugs that unit tests didn't catch**, not
  compile or obvious-crash failures. This matters for the rollout plan: PR 1
  of the new attempt needs tests that specifically exercise the odd-bracket
  backtracking path and the unequal-game-wins validation path, since #4615's
  90 passing tests didn't catch either.
- 24 files changed, +2586/-33 total. Full list confirms the scope described
  in #4612: `crates/lobby-broker/{broker.rs,lib.rs,protocol.rs,tournament.rs
  (new, 972 lines),validation.rs}`, `crates/phase-server/src/main.rs`,
  `crates/server-core/src/{client_message_wire_guard.rs,protocol.rs}`,
  `lobby-worker/broker-wasm/src/lib.rs`, `lobby-worker/src/{hello-gate.ts,
  lobby-do.ts}`, and 12 frontend files under `client/src/`.

## 3. PR #4615 — the actual review (not the discussion's paraphrase)

Fetched via `gh api repos/phase-rs/phase/pulls/4615/reviews` and
`.../pulls/4615/comments` — the real GitHub review objects, independent of
how discussion #5314 summarized them.

**Two reviews exist:**
1. `gemini-code-assist[bot]`, state `COMMENTED` — a summary comment
   correctly characterizing the PR's shape and flagging "a backtracking bug
   in the pairing algorithm for odd-sized brackets, missing winner validation
   on unequal game wins, premature tournament expiration due to static
   creation timestamps, and multiple WebSocket connection leaks."
2. `matthewevans` (human), state `CHANGES_REQUESTED` — the substantive
   review, with a body containing exactly seven numbered findings tagged
   HIGH/MED/LOW. This is the review #5314's "What #4615's review already
   surfaced" section is summarizing. Verified the discussion's summary is
   faithful to this review — no invented findings, no dropped findings,
   severity tags match.

**The seven findings, verbatim evidence + this session's independent check
against `gh pr diff 4615`:**

| # | Severity | Finding | Evidence cited by reviewer | Independently confirmed in diff? |
|---|----------|---------|------------------------------|-----------------------------------|
| 1 | HIGH | Tournament authority stored on socket (`ConnState`); UI closes socket immediately after creating, triggering `on_disconnect` → tournament unregistered; joined players lose `joined_tournaments` too | `TournamentLandingPage.tsx:66`; `broker.rs:353` | Not independently re-derived line-by-line (frontend timing bug), but structurally consistent with the diff's `ConnState` extension being bare fields, not tokens |
| 2 | HIGH | `validate_match_result` doesn't check winner against game-win score | `tournament.rs:326` | **Yes — confirmed exactly**, see §4 below |
| 3 | HIGH | Tournaments expire by `created_at`, never updated | `tournament.rs:275`; `main.rs:1004` | **Yes — confirmed exactly**, see §4 below |
| 4 | MED | `is_empty()` in broker-wasm only checks lobby games | `lobby-worker/broker-wasm/src/lib.rs:175` | **Yes — and still true on current `main` today** (no tournament state exists yet to check), see CONTEXT.md finding #5 |
| 5 | MED | Odd-sized brackets always miss the backtracking success path | `tournament.rs:698` | **Yes — confirmed exactly**, see §4 below |
| 6 | MED | Tournament subscription cleanup unsubscribes but never closes the socket | `tournamentClient.ts:296` | Not re-derived (frontend), consistent with the four separate Gemini inline WebSocket-leak comments (§3b) |
| 7 | LOW | New tournament UI chrome bypasses `t()`/i18n | `TournamentLandingPage.tsx:87` | Not re-derived (frontend), plausible given the PR introduces multiple new pages with hardcoded English strings visible in the diff (`"Create Tournament"`, `"Join Tournament"`, etc. appear as raw JSX text) |

**3b. Gemini's inline (line-anchored) review comments** — `gh api
repos/phase-rs/phase/pulls/4615/comments` returned 10 inline suggestion
comments (Gemini's automated per-line pass), which is a *superset* of the
human review's seven findings plus additional WebSocket-leak instances the
human review's prose collapsed into one bullet:
- Backtracking bug, `tournament.rs:700` (suggests `return Some(acc.clone());`)
- Winner validation, `tournament.rs:328` (suggests the exact comparator fix)
- Expiration, `tournament.rs:288`
- WebSocket leak on unmount, `TournamentLandingPage.tsx:35`
- WebSocket leak on RPC error (create), `TournamentLandingPage.tsx:75`
- WebSocket leak on unmount, `TournamentPage.tsx:45`
- WebSocket leak on RPC error (join), `TournamentPage.tsx:90`
- WebSocket leak on RPC error (start round), `TournamentPage.tsx:101`
- WebSocket leak on RPC error (report result), `TournamentPage.tsx:117`
- WebSocket leak on RPC error (drop), `TournamentPage.tsx` (comment
  truncated in the raw API response but same pattern)

This confirms the discussion's bullet 6 ("Frontend must close the tournament
socket on unmount, including the cancelled-connect path") actually covers
**six distinct leak sites** in the closed PR, not one — every RPC handler in
both tournament pages leaked a socket on its error path by jumping to `catch`
before a `client.close()`. Whoever writes PR 4 should structure the new
`tournamentClient.ts` so a single `finally`-based close (or a request
wrapper that owns connect/close) makes this class of bug structurally
impossible, rather than relying on each handler remembering to close in its
own `finally`.

## 4. Line-exact confirmation of the three backend bugs, read from `gh pr diff 4615`

Saved the full diff to a scratch file and grepped/read it directly (diff line
numbers below are within the diff output, i.e. the `+`-prefixed added lines
of the closed PR — these never landed on `main`, this is purely forensic).

**Backtracking (diff line ~2594-2624):**
```rust
fn backtrack_pair(
    players: &[String],
    prior_pairs: &HashSet<(String, String)>,
    acc: &mut Vec<(String, String)>,
) -> Option<Vec<(String, String)>> {
    if players.is_empty() {
        return Some(acc.clone());
    }
    if players.len() == 1 {
        return None;               // <-- BUG: should be Some(acc.clone())
    }
    let first = &players[0];
    for (i, partner) in players.iter().enumerate().skip(1) {
        ...
        if let Some(solution) = backtrack_pair(&rest, prior_pairs, acc) {
            return Some(solution);
        }
        acc.pop();
    }
    None
}
```
Every odd-length input recurses down to exactly one remaining player at the
base of its final recursive call and returns `None` there, which propagates
all the way back up as total failure — even though a valid pairing (with one
player floated) exists. Confirmed the reviewer's suggested one-line fix
(`return Some(acc.clone())`, treating the lone survivor as the bye/float) is
correct and requires no other structural change to the function.

**Winner validation (diff line ~2219-2234):**
```rust
fn validate_match_result(pairing: &TournamentPairing, result: &MatchResult) -> Result<(), String> {
    let player_b = pairing.player_b.as_ref().ok_or_else(|| "Invalid pairing".to_string())?;
    let valid_keys = [&pairing.player_a, player_b];
    if let Some(winner) = &result.winner_player_key {
        if !valid_keys.iter().any(|k| *k == winner) {
            return Err("Winner must be one of the paired players".to_string());
        }
    }
    if result.player_a_wins == result.player_b_wins && result.winner_player_key.is_some() {
        return Err("Draw results must not specify a winner".to_string());
    }
    Ok(())
}
```
Confirmed: there is no branch comparing `result.player_a_wins` vs
`result.player_b_wins` when they're *unequal* to require `winner_player_key`
match the higher-wins player. A `2-0` result naming the loser as winner
passes validation untouched.

**Expiry (diff line ~2179-2192):**
```rust
pub fn check_expired(&mut self, timeout_secs: u64, env: &impl BrokerEnv) -> Vec<String> {
    let now = env.now_ms();
    let cutoff = now.saturating_sub(timeout_secs.saturating_mul(1000));
    let expired: Vec<String> = self.tournaments.iter()
        .filter(|(_, t)| t.created_at < cutoff)
        .map(|(code, _)| code.clone())
        .collect();
    ...
}
```
Confirmed: filters purely on `created_at`, which is set once at creation
(diff line ~2044, `created_at: env.now_ms()`) and never mutated anywhere else
in the 972-line `tournament.rs` diff (grepped the whole file's added lines
for `created_at =` / `.created_at =` — no write site other than
construction). Cross-checked the native reaper's actual call site on current
`main`: `crates/phase-server/src/main.rs:1000`,
`broker.reap_expired(300, &SysEnv)` — still a 300-second timeout today,
confirming the review's claim that this specific timeout value would delete
an in-progress tournament well before most real Swiss rounds finish.

## 5. `lobby-broker`/`broker.rs` architecture — full verification

`crates/lobby-broker/src/broker.rs` read in full (`lines 1-140` shown in
detail; remainder skimmed for `Outbound` usage). Confirmed:

- Module doc comment (lines 1-12) explicitly states the functional-core
  contract: "No I/O, no locking, no tokio: the only impurity is `env`
  (time/rng), `&mut self` (the lobby map), and `&mut conn` (this connection's
  lobby state)."
- `pub struct Broker { lobby: LobbyManager }` (lines 108-111) — currently a
  single field. A `tournaments: TournamentManager` field is a direct,
  additive sibling with no restructuring needed, exactly as #4612/#5314
  propose.
- `pub fn handle(&mut self, conn: &mut ConnState, msg: LobbyClientMessage,
  env: &impl BrokerEnv) -> Vec<Outbound>` (line 136) is the single dispatch
  entry point every lobby message goes through today; new
  `LobbyClientMessage` variants for tournament actions would add match arms
  here (or a delegated `handle_tournament_message` called from within this
  match, mirroring how `handle_create_game`/`handle_join`/etc. are already
  factored out as private helpers at lines 316, 434, 527, 669, 705).
- `ConnState` (lines 46-58) fields today: `client_hello`, `subscribed`,
  `host_game: Option<String>`, `reservations: Vec<(String, String)>`. No
  tournament fields exist yet (confirms greenfield). The `host_game` shape
  the discussion analogizes from is a bare `Option<String>` game-code stamp
  — the discussion's proposed `organizer_token`/`joined_tournaments` fields
  should NOT copy this bare-stamp shape verbatim (that's the exact pattern
  #4615 got bitten by); they should hold **tokens**, mirroring
  `draft_session.rs`'s `player_tokens` pattern (§7 below), not bare
  socket-owned identifiers.
- `Outbound` enum (lines 63-76): `ToSelf`, `ToSubscribers`, `AddSubscriber`,
  `RemoveSubscriber`, `SendPlayerCountToSelf`. A tournament manager reuses
  `ToSubscribers`/`AddSubscriber`/`RemoveSubscriber` for broadcasting
  tournament updates — no new `Outbound` variant needed for basic fan-out,
  confirming #4612's claim.

## 6. Where "`lobby_subscribers`" actually lives

Grepped the whole workspace for `lobby_subscribers` (not `subscribers` in
general, which also appears inside `broker.rs`'s doc comments/`Outbound`
naming as shown above). Zero hits inside `crates/lobby-broker/`. Hits
concentrated entirely in `crates/phase-server/src/main.rs`:
- `type SharedLobbySubscribers = Arc<Mutex<Vec<mpsc::UnboundedSender<ServerMessage>>>>;` (line 84)
- `let lobby_subscribers: SharedLobbySubscribers = Arc::new(Mutex::new(Vec::new()));` (line 824)
- Used throughout `apply_outbounds`/`broadcast_to_lobby_subscribers`/
  `broadcast_player_count` to interpret the broker core's abstract
  `Outbound::AddSubscriber`/`ToSubscribers`/`RemoveSubscriber` into actual
  socket sends.

So "the existing `lobby_subscribers` broadcast channel" is a true statement
about the **native server shell**, not the `lobby-broker` crate itself. The
Cloudflare Worker shell (`lobby-worker/src/lobby-do.ts`) has its own
equivalent fan-out over Durable Object WebSocket connections — grepped
`lobby-do.ts` for `ConnAttachment`/`DEFAULT_CONN` (lines 25, 63, 134, 150,
167, 207) confirming per-connection attachment state exists there too, in
the TypeScript shell, separate from the Rust `lobby_subscribers` map. A
`TournamentManager` living in the shared `lobby-broker` core is transport
description via `Outbound`, and each shell (native Rust, Worker TS)
interprets those `Outbound`s using its own pre-existing fan-out mechanism —
neither shell needs a *new* subscriber registry, which is the substance of
what #4612/#5314 claim; the discussion's wording just slightly overstates
which crate literally owns the name `lobby_subscribers`.

## 7. Draft-pod token-based reconnect — the analogy source

`crates/server-core/src/draft_session.rs`, read in full for the relevant
sections:
- Line 18: `use crate::session::{generate_player_token, SessionManager};`
- Lines 27-28: `pub player_tokens: Vec<String>` — "Per-seat player tokens
  (seat_index -> token). Empty string = seat not claimed."
- Lines 44-47: `pub fn seat_for_token(&self, token: &str) -> Option<usize>`
  — resolves a seat purely from a token value, no socket/connection
  reference anywhere in the signature or body.
- Lines 141-211 (`create_draft`) and 214-271 (`join_draft`): both mint a
  fresh `player_token` via `generate_player_token()` and store it in
  `token_to_draft: HashMap<String, String>` (line 129) for O(1) reverse
  lookup, independent of any WebSocket connection object.
- Lines 274-320 (`apply_player_action`): takes `token: &str` as a parameter
  and resolves the seat via `seat_for_token` (line 289) before applying
  anything — the connection that happens to deliver the token is
  incidental; the token itself is the authority.

This is a real, in-repo, same-crate-family precedent for "authority is a
token minted at creation/join time, independent of the connection that holds
it" — directly supporting #5314's proposed fix for #4615's finding #1
(organizer authority must not live on `ConnState`/the socket).

## 8. MTR facts cited in #5314 — explicitly not re-verified

Per the task's scope, the following are taken as given from the discussion's
own citations and were not independently re-fetched or fact-checked this
session:
- Match points 3/1/0 (MTR §2.1)
- Tiebreaker order: match points → opponents' match-win % → game-win % →
  opponents' game-win % (MTR §3.1)
- 0.33 floor on match-win %/game-win % (MTR Appendix C)
- Bye = 2-0 win (3 points/6 game points), excluded (not zero-filled) from
  opponents'-percentage averaging (MTR Appendix C)
- Player-count → round-count table, 4-8 players → single elimination
  (MTR Appendix E)
- Self-reporting model (MTR §2.4)
- No codified Swiss pairing algorithm in the MTR itself (§10.4 just says
  "follow the Swiss pairing algorithm" without detailing mechanics)

If these ever need re-verification, the discussion cites both the PDF
(`https://media.wizards.com/ContentResources/WPN/MTG_MTR_2026_Feb27_EN.pdf`)
and the HTML judge-blog mirror (`https://blogs.magicjudges.org/rules/mtr/`
and per-section pages) as primary sources.

## 9. Custom-format-engine (phase 58) cross-reference — evidence

Read `.planning/phases/58-custom-format-engine/CONTEXT.md` and `PLAN.md` in
full from `myfork/research/custom-format-engine` (via `git show
"myfork/research/custom-format-engine:.planning/phases/58-custom-format-engine/CONTEXT.md"`,
`MSYS_NO_PATHCONV=1` needed on this Windows/git-bash environment to prevent
the `branch:path` argument from being mis-parsed as a Windows path).

Key finding, phase 58 CONTEXT.md "Open" section, item 4, quoted verbatim:

> **Draw/tiebreaker resolution mechanics** (generalizing the Chaos Orb
> tiebreaker and the foreign-card-identification convention above): both are
> instances of a "how does this table resolve an otherwise-undecided
> outcome" hook, not an in-game rule. Confirmed via grep (`crates/draft-core`,
> `server-core`) that phase.rs has **no match-level concept at all today** —
> no best-of-N, no tournament round, no draw/tiebreak state machine; the
> engine models single games only. ... Given no match-level structure
> exists, this is flagged as **out of scope for the custom-format engine
> itself** and, if ever pursued, belongs to a separate, later
> "tournament/match structure" design, not bundled into
> `CustomFormatDef`/`LegacyRuleSet` here.

This is phase 58 independently arriving at the same conclusion this
document reaches from the tournament side: tournament/match structure
(which is what `TournamentManager`/`ScoringPolicy` are) is a categorically
separate concern from `CustomFormatDef`/`LegacyRuleSet` (in-game CR
rule-variation toggles), and phase 58 explicitly declined to design it,
deferring to exactly this phase.

Phase 58 PLAN.md's `LegacyRuleSet` shape, **updated this session — the
version below was current as of phase 58's own review round 4; the original
draft of this section quoted an earlier, now-stale bool-based sketch**:
```rust
LegacyRuleSet {
    mana_burn: ManaBurnPolicy,           // Modern | Obsolete
    damage_timing: CombatDamageTiming,   // Modern | OnStack
    wish_scope: WishOutsideGameScope,    // PostM10SideboardOnly | PreM10ReachesExile
    legend_rule_scope: LegendRuleScope,  // Modern | PreM14AnyController
}
```
Every axis converted from a bare `bool` to a typed enum during phase 58's
own review process (each names a real historical-form-vs-modern-absence
space, not an arbitrary on/off switch — the same reasoning `LegendRuleScope`
already used). `reprint_policy` — present in earlier phase-58 drafts as a
`LegalityRules` field — was moved OUT of the resolved rules struct entirely,
onto a `CustomFormatDef` metadata side, after review found it sitting inside
the enforced-ruleset struct while documented as "never enforced" was an
internal contradiction. None of this changes the conclusion above — it's
still `CustomFormatDef`-scoped, in-engine, single-game state with zero
notion of rounds/match-points/standings, unrelated to `ScoringPolicy` either
way — but citing the current shape rather than a superseded draft avoids
this document going stale the way the original PROTOCOL_VERSION citation
did (§10 below).

This lives inside `CustomFormatDef` (engine crate, `types/format.rs`family),
consumed by in-game resolvers (SBA checks, mana pool draining, Wish
resolution) during a single game. It has no notion of rounds, match points,
byes, or standings — those concepts don't exist anywhere the engine crate
looks. `ScoringPolicy` would need `win_points: u8, draw_points: u8,
loss_points: u8` consumed by tiebreaker math over a *sequence* of games
across a multi-round event — a `lobby-broker` concept with zero engine
crate touchpoints. The two structs don't share a natural parent type, a
consumer, or a lifecycle; forcing them together would violate the
CLAUDE.md categorical-boundary principle at a crate-boundary grain, which is
a stronger violation than the same-crate within-CR-section violations that
principle was originally written to catch.

## 10. Re-verification pass against current `main` — protocol version split

Original research (§ above) pinned this phase's understanding to `main` at
commit `d65111246`. Re-checked directly this session against current `main`:

- `crates/lobby-broker/src/protocol.rs:104`: `pub const PROTOCOL_VERSION: u32
  = 33;` (was 13 at research time — an 20-version jump from unrelated churn,
  not evidence of anything specific to this phase).
- `crates/lobby-broker/src/protocol.rs:133`: `pub const LOBBY_PROTOCOL_VERSION:
  u32 = 1;` — did NOT exist at research time. `git log --oneline --all -S
  "LOBBY_PROTOCOL_VERSION" -- crates/lobby-broker/src/protocol.rs` finds
  exactly one commit, `6db58810b` ("fix(protocol): give the lobby its own
  wire version, decoupled from the full game (#7606)").
- Consequence for PR 2 (protocol + native server): bump
  `LOBBY_PROTOCOL_VERSION`, not `PROTOCOL_VERSION` — tournament messages are
  lobby-scoped (this phase's own architecture matches `LobbyManager`
  exactly), and `6db58810b` exists specifically to let lobby-scoped wire
  changes bump independently of the general game protocol. See CONTEXT.md
  finding #4 (updated) for the full reasoning.

## 11. `crates/draft-core` already has a tested Swiss-pairing implementation

Found via `grep -rln "TournamentManager\|SwissPairing\|swiss_pair\|
tournament_organizer\|joined_tournaments\|ScoringPolicy" crates/
client/src/"` during this session's re-verification pass — the original
research pass did not search for this and missed it entirely.

- `crates/draft-core/src/types.rs:12`: `pub enum TournamentFormat` with
  `Swiss` and `SingleElimination` variants.
- `crates/draft-core/src/session.rs`, dispatch: `TournamentFormat::Swiss =>
  generate_swiss_pairings(session, round, &mut rng)`.
- `generate_swiss_pairings` (same file): builds `players_with_wins: Vec<
  (PlayerId, u8, u8)>` from each seat's `match_records`, sorts descending by
  wins, groups into score-bracket `Vec<Vec<(PlayerId, u8)>>`, shuffles each
  bracket with a seeded `ChaCha20Rng`, builds a `prior_pairs:
  HashSet<(PlayerId, PlayerId)>` rematch set from `session.pairings`, then
  greedily pairs within each bracket (preferring a non-rematch partner via
  `.position(|(pid, _)| !prior_pairs.contains(&(first.0, *pid)))`), carrying
  a lone leftover player (`carry: Option<(PlayerId, u8)>`) down into the
  NEXT bracket rather than backtracking within the current one. A player
  still unpaired after the last bracket takes a bye; the caller credits it
  as a match win (`ensure_match_record(...).match_wins += 1`, in the calling
  function, since a Swiss bye scores as a win per the same MTR convention
  #5314 already cites).
- Sibling `generate_se_pairings` in the same file: standard seeded
  single-elimination bracket (`[(0,7),(1,6),(2,5),(3,4)]` for round 1, then
  pairs winners of adjacent prior-round matches) — gated to exactly 8 seats
  by an `UnsupportedTournamentSize` check earlier in the calling function.
- Tests: `test_swiss_pairings_8_players`, `swiss_pairings_include_bot_filled_seats`
  (same file, `#[cfg(test)]` module).

**Why this matters for #4615's confirmed bug (§4 above):** #4615's
`backtrack_pair` used recursive backtracking with a base case that returned
`None` (search failure) whenever exactly one player remained — killing the
entire search for any odd-sized bracket. `draft-core`'s implementation has
no backtracking recursion at all: an odd leftover is a `carry`, handled by
plain data flow into the next loop iteration, not a search outcome. The bug
class doesn't have a foothold in this shape. This is real, tested, existing
precedent in the same repo for the exact algorithmic problem this phase
needs solved — worth citing explicitly in PR 1 rather than re-deriving
backtracking and re-discovering the same bug independently.

**Scope caveat, so this isn't overclaimed as a drop-in reuse:** `draft-core`'s
version is keyed to a single draft pod's types (`DraftSession`, `PlayerId`,
`DraftPairing`), normally exactly 8 seats, with a lifecycle scoped to one
draft. `TournamentManager`'s Swiss pairing needs to work for arbitrary lobby
player counts (4 to 128+, per MTR Appendix E) across a tournament's full
multi-round lifecycle. The *algorithm shape* transfers; the *code* would
need real adaptation across a crate boundary with different lifecycles —
whether that's done as literal shared code or two independently-tested
implementations of the same shape is a PR 1 implementation decision, not
resolved here.
