# Phase 61 — Swiss-Pairing Tournament Organizer — CONTEXT

## Why this matters

phase.rs has rich casual matchmaking (`lobby-broker`) but no support for
organized multi-round events. Running a Swiss tournament for a playgroup today
means tracking pairings and standings by hand outside the app. This has
already been proposed once (issue **phase-rs/phase#4612**), attempted once
(PR **phase-rs/phase#4615**, closed unmerged after review found real bugs —
not because the architecture was wrong), and is now being picked back up via a
second design pass, GitHub Discussion **phase-rs/phase#5314**, which grounds
the scoring/tiebreaker rules in the actual current Magic Tournament Rules
(MTR, effective 2026-02-27) instead of inventing convention from memory.

This document is a from-scratch, independent verification of every
repo-architecture claim in #5314 against the code actually on `main` today,
plus the real (not paraphrased) review findings from #4615, plus an informed
opinion on whether tournament scoring policy should hook into the sibling
custom-format-engine research effort (phase 58).

**Bottom line up front: the discussion's architecture claims all check out.**
Nothing in #5314 mischaracterizes the codebase in a way that would change the
proposed design. One phrase ("the existing `lobby_subscribers` broadcast
channel") is imprecise about which crate that channel actually lives in, but
the underlying mechanism it's pointing at is real and the proposed reuse is
still correct. Full citations are in RESEARCH.md; this file is the synthesis.

## Confirmed facts — verified against code this session

Everything below was checked directly against `main` (via a worktree at
`myfork/main`, commit `d65111246` at time of research) unless marked
otherwise. See RESEARCH.md for exact file:line evidence.

1. **Greenfield, confirmed.** No `tournament.rs`, `TournamentManager`, or any
   tournament-related type exists anywhere in `crates/lobby-broker/src/` (or
   elsewhere in the workspace) on `main` today. `ls crates/lobby-broker/src/`
   shows only `broker.rs`, `env.rs`, `inbound_guard.rs`, `lib.rs`, `lobby.rs`,
   `protocol.rs`, `reservation_auth.rs`, `validation.rs`. #4615 was closed
   without merging, so none of its work landed. This is a true from-scratch
   design, not a partially-built stub.

2. **`LobbyManager` + `Broker::handle` + `ConnState` + functional-core pattern
   — confirmed exactly as described.** `crates/lobby-broker/src/lobby.rs:96`
   defines `pub struct LobbyManager`. `crates/lobby-broker/src/broker.rs:136`
   defines `pub fn handle(&mut self, conn: &mut ConnState, msg:
   LobbyClientMessage, env: &impl BrokerEnv) -> Vec<Outbound>` — single entry
   point, pure function of `(state, conn, msg, env)` returning ordered side
   effects, exactly the "no I/O, no locking, no tokio" functional core the
   module doc comment (`broker.rs:1-7`) claims. `ConnState`
   (`broker.rs:46-58`) already has the "ownership stamp" idiom the discussion
   cites: `host_game: Option<String>` records which game this connection
   registered as host, torn down on disconnect. A `tournament_organizer` /
   `joined_tournaments` pair would be the direct sibling extension — but see
   finding #3 below on *how* that extension should be shaped (as tokens, per
   the #4615 review).

3. **The "existing `lobby_subscribers` broadcast channel" claim is correct in
   substance but the name lives one layer up from where the discussion
   implies.** There is no `lobby_subscribers` identifier inside
   `crates/lobby-broker`. The broker core is transport-agnostic: it emits
   abstract `Outbound::AddSubscriber` / `Outbound::RemoveSubscriber` /
   `Outbound::ToSubscribers(LobbyServerMessage)` (`broker.rs:63-76`), and each
   shell owns the actual registry. The *native* shell's registry is named
   `lobby_subscribers` — confirmed at `crates/phase-server/src/main.rs:84`
   (`type SharedLobbySubscribers = Arc<Mutex<Vec<mpsc::UnboundedSender<...>>>>`)
   and instantiated at `main.rs:824`. So "reuse `lobby_subscribers`, no new
   subscriber registry needed" is true for the native server, and the
   Cloudflare Worker shell has its own equivalent DO-connection fan-out — but
   a `TournamentManager` reuses this by emitting the *same* `Outbound`
   variants the lobby core already emits, not by directly touching a
   `lobby_subscribers` field that lives inside `lobby-broker` itself (no such
   field exists there). This is a precision correction, not a substantive
   correction — the reuse plan in #5314 is still exactly right.

4. **`PROTOCOL_VERSION` is currently 13, not 12.** Confirmed at
   `crates/lobby-broker/src/protocol.rs:38` (`pub const PROTOCOL_VERSION: u32
   = 13;`), re-exported through `crates/server-core/src/protocol.rs:17` and
   asserted by an existing test at `server-core/src/protocol.rs:1810`. Git
   history (`git log -p -- crates/lobby-broker/src/protocol.rs`) shows the
   12→13 bump landed in commit `360bf24cb` ("fix(engine): resolve mulligan
   bottoming at each player's declare point (CR 103.5b) (#5236)") — an
   unrelated mulligan fix, exactly as the task brief anticipated. **PR 2 in
   the discussion's rollout must bump from 13→14, not 12→13** — the discussion
   text doesn't hardcode the number so this doesn't require a doc change, but
   it's worth flagging so whoever picks this up doesn't copy #4615's stale
   "protocol v12" language from its own PR description.

5. **The Cloudflare Worker `is_empty()` predicate genuinely only checks lobby
   games today — bug #4 in the discussion is real and reproducible against
   current `main`.** `lobby-worker/broker-wasm/src/lib.rs:168-170`:
   ```rust
   pub fn is_empty(&self) -> bool {
       self.inner.lobby().is_empty()
   }
   ```
   `Broker` (`crates/lobby-broker/src/broker.rs:108-111`) currently has a
   single field, `lobby: LobbyManager`. Adding a `tournaments: TournamentManager`
   field to `Broker` without updating this predicate would reproduce exactly
   the bug #4615's review caught: a Durable Object holding only tournament
   state would report `is_empty() == true` and stop rescheduling its cleanup
   alarm. This must be fixed as part of PR 3 in the rollout, not deferred.

6. **Draft-pod session reconnect genuinely uses per-seat tokens, not socket
   identity — confirmed, and it's a good analogy.**
   `crates/server-core/src/draft_session.rs:27-28` stores `player_tokens:
   Vec<String>` per seat, generated via `generate_player_token()`
   (`crate::session::SessionManager`, imported at line 18). Lookup is by
   token: `seat_for_token(&self, token: &str) -> Option<usize>`
   (`draft_session.rs:44-47`) scans `player_tokens` for a match, and action
   dispatch (`draft_session.rs:274-290`) resolves the acting seat via
   `seat_for_token` before applying anything — never via the connection's
   socket identity. This is a real, load-bearing precedent in the same crate
   family (`server-core`) for "authority survives a socket bounce," and
   directly supports the discussion's proposed organizer/player-token fix.

7. **All seven of #4615's review findings are real bugs in the actual closed
   PR diff, not a summary embellishment.** Fetched via `gh api
   repos/phase-rs/phase/pulls/4615/reviews` and `.../comments` (the real
   review, from human reviewer `matthewevans` plus an automated Gemini
   pass) — not just the discussion's paraphrase. Cross-checked each against
   `gh pr diff 4615`:
   - **Backtracking base case bug — confirmed exactly.** The diff's
     `backtrack_pair` (added code, diff line ~2602) has:
     ```rust
     if players.is_empty() { return Some(acc.clone()); }
     if players.len() == 1 { return None; }
     ```
     For any odd-sized bracket, every recursive branch bottoms out at
     `players.len() == 1` and returns `None`, so the *entire* backtracking
     search fails for odd brackets and falls back to a greedy pairing that
     can produce avoidable rematches. The reviewer's suggested fix
     (`return Some(acc.clone())` for the one-remaining-player case, treating
     it as the float) is correct and cheap — a one-line base-case fix, not a
     redesign.
   - **Missing winner validation — confirmed exactly.** The diff's
     `validate_match_result` (diff line ~2219) only checks (a) the winner is
     one of the two paired players and (b) a draw has no winner. It never
     compares `winner_player_key` against which player actually has more
     game wins. A client can report `player_a_wins: 2, player_b_wins: 0,
     winner_player_key: Some(player_b)` and it passes validation, corrupting
     standings.
   - **Expiry keyed off `created_at`, never updated — confirmed exactly.**
     The diff's `check_expired` (diff line ~2179) filters
     `t.created_at < cutoff` with no `last_activity_at` field anywhere in the
     diff's `TournamentMeta`. The native reaper calls
     `broker.reap_expired(300, &SysEnv)` today for lobby entries
     (`crates/phase-server/src/main.rs:1000`, confirmed still 300s on
     current `main`) — the PR wired the same 300-second timeout to
     tournaments via `check_expired`, so any tournament whose *rounds* run
     longer than 5 minutes total (essentially all of them) would be deleted
     out from under active players.
   - **The four WebSocket-leak findings and the i18n finding** are all
     frontend-only (`TournamentLandingPage.tsx`, `TournamentPage.tsx`,
     `tournamentClient.ts`) and independently confirmed present in the actual
     diff at the cited lines. Not re-verified line-by-line here since the
     rollout plan (PR 4) rebuilds the frontend from scratch rather than
     reusing #4615's frontend code, but they're real, and PR 4 must not
     reintroduce them.

## What this session did NOT re-verify (explicitly out of scope per the task)

The Magic Tournament Rules citations in #5314 (match points 3/1/0 at MTR
§2.1, tiebreaker order and 0.33 floors at MTR §3.1/Appendix C, bye scoring at
Appendix C, the round-count table at Appendix E, self-reporting at §2.4) are
taken as given from an external, official source already cited with URLs.
This is a code-architecture verification pass, not an MTR fact-check.

## Open questions for the maintainer

These are the discussion's own open questions, unchanged by this
verification pass — nothing found this session resolves them unilaterally:

1. **Is a flat `ScoringPolicy{win,draw,loss}` sufficient for v1**, or should
   it anticipate hooking into the custom-format-engine research (phase 58)
   if/when that lands? **This session's opinion, argued in PLAN.md: no — keep
   them separate.** `ScoringPolicy` is tournament-administration state that
   lives in `lobby-broker` and never touches a `GameState`; phase 58's
   `LegacyRuleSet` is in-game CR-rule-variation state that lives in the
   `engine` crate's `FormatConfig` and is consumed mid-game. They sit in
   different crates, different lifecycles (one tournament-scoped, one
   game-scoped), and different CR categories (MTR tournament administration
   vs. Comprehensive Rules game mechanics). Phase 58's own CONTEXT.md
   independently reached the same conclusion from the other side (see
   "Relationship to adjacent work" below) — this is not a contested call.
2. **Round advancement**: organizer-gated only for v1, or build an
   auto-advance timer now? No new evidence found either way this session;
   still a product-scope call, not an architecture one — a timer is additive
   later regardless of which is chosen for v1.
3. **Confirm v1 stays lobby-only** (no auto-launched `GameSession` per
   pairing), with full-mode integration as an explicit fast-follow. Confirmed
   this matches #4612's original framing exactly, and nothing found this
   session suggests otherwise. Recommend confirming as stated.

## Relationship to adjacent work — scope boundaries

- **Custom-format-engine (phase 58, branch `research/custom-format-engine`).**
  Read that phase's CONTEXT.md and PLAN.md in full for this cross-reference.
  Phase 58 already independently confirmed, from its own investigation, that
  **phase.rs has no match-level concept at all today** — "no best-of-N, no
  tournament round, no draw/tiebreak state machine; the engine models single
  games only" — and explicitly flagged its own adjacent open question
  (draw/tiebreak resolution mechanics) as **out of scope for the
  custom-format engine itself**, deferring it to "a separate, later
  tournament/match structure design" — i.e., exactly this phase. Phase 58's
  `LegacyRuleSet` (mana burn, damage-uses-stack, pre-M10 Wish templating,
  legend-rule scope) is a set of **in-game CR-rule-variation toggles** that
  live on `FormatConfig` in the `engine` crate and are read during game
  resolution. `ScoringPolicy` (win/draw/loss match points feeding
  match-point accumulation and tiebreaker math) is **tournament
  bookkeeping** that lives in `lobby-broker`, never enters a `GameState`, and
  is applied *after* a game/match ends, not during it. These are two
  different CR-adjacent categories (MTR administrative scoring vs. CR game
  rules) living in two different crates with no shared runtime state — the
  same "categorical boundary" reasoning this repo's CLAUDE.md applies to
  keep Life (CR 119) and Power/Toughness (CR 208/209) from being unified
  under one enum applies here at a coarser grain. **Recommendation: do not
  make `ScoringPolicy` a field of `CustomFormatDef`/`LegacyRuleSet`, or wait
  on phase 58 landing.** `TournamentManager`'s `ScoringPolicy` should be
  designed and shipped independently in `lobby-broker`. If a future format
  ever wants scoring defaults to travel with a format preset (e.g., "Old
  School events on this site default to draws=0"), that is a *product*
  wiring question for whichever UI creates a tournament to read a suggested
  default off the chosen format — not an architectural coupling between the
  two crates. No blocking dependency exists in either direction; phase 58 and
  this phase can land in either order.
- **Watch-game-mode (phase 60) and audio/video-chat (phase 59)** — no
  meaningful overlap found. Tournaments organize P2P tables via the existing
  `CreateGameWithSettings`/`JoinGameWithPassword` flow per #4612; whether a
  tournament's tables are individually spectatable is exactly phase 60's
  existing "is a P2P game spectatable" open question (currently: no, P2P
  games can't be spectated at all — see phase 60 Open Q2), not something this
  phase needs to solve. Flagged for awareness only.
- **Issue #4612 / PR #4615** — this phase supersedes neither; it is the
  second design pass on the same feature request, incorporating the first
  attempt's real review findings as day-one design constraints rather than
  post-hoc fixes. #4612 stays open until this design ships; #4615 stays
  closed (its code never merged and is not being resurrected — PR 1 of the
  rollout is a clean rewrite of `tournament.rs`, not a rebase of #4615's
  branch).
