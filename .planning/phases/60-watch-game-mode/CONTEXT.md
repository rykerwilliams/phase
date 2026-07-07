# Phase 60 — Watch Game / Spectator Mode — CONTEXT

## The single most important finding, up front

**Live-game spectator mode already exists and is wired end-to-end — server, engine
redaction, WebSocket routing, and a reachable frontend UI.** This is NOT a
design-from-scratch task and NOT a "complete a half-built stub" task. The happy
path (open a live server game, click "Watch" in the lobby / type a code, land on
a read-only board that updates live) is implemented and functional today.

The lead in the task brief ("there may already be a `spectator_wire_guard`
module") dramatically understated what exists. `spectator_wire_guard.rs` is only
the input-validation/capacity-cap leaf of a much larger, complete feature that was
landed across several PRs:

- `#1884` feat: implement live multiplayer spectator mode in phase-server with privacy-safe state fanout
- `#1916` fix: per-game spectator cap for live SpectatorJoin
- `#1925` fix: cap spectators per game and draft before snapshot work
- `#1867` fix: validate spectator wire codes before lookup paths
- `#2132` feat(client): spectator mode, draft watch, log tools, deck playtest
- `#2247` feat(client): replays, content i18n, spectator dashboard, 2HG UI

(Historical note: a *different* prior "phase 60" numbering — `60-02`, `60-04` in
git — was used for **draft** spectating. That is unrelated to this document's
phase directory; the number collision is incidental. `.planning/` is gitignored
and was not present in this worktree, so this directory was created fresh.)

## Confirmed facts (verified against code — see RESEARCH.md for citations)

1. **Per-viewer hidden-information redaction EXISTS and is robust.** The engine
   has `filter_state_for_viewer` (`crates/engine/src/game/visibility.rs`) which
   produces a per-recipient redacted `GameState`: opponent hands hidden, all
   libraries hidden, the RNG seed zeroed (so clients can't predict shuffles),
   plus per-controller redaction of pending triggers, manifest/dig/guess secrets,
   deck pools, etc. Server broadcasts already send each *player* their own
   filtered view. **This is server-enforced, not client-trusted.** (This answers
   the task's "loud flag" question: information-hiding is NOT client-trusted —
   the engine redacts on the wire.)

2. **Spectators are modeled as a non-seat viewer, `PlayerId(u8::MAX)` (255).**
   Feeding that sentinel into `filter_state_for_viewer` hides *all* players'
   hands and libraries (a spectator is nobody's teammate), producing a
   hidden-information-respecting public view. There is an explicit engine test
   for this (`non_seat_spectator_sees_no_player_hands`).

3. **The server fans out state to spectators.** `phase-server` keeps a per-game
   spectator sender registry, handles `ClientMessage::SpectatorJoin { game_code }`,
   sends the joining spectator a redacted `GameStarted`, and pushes a redacted
   `StateUpdate` to every spectator on each subsequent game update. Spectators are
   read-only *by construction* (their socket never holds a `player_id`/`game_code`,
   so the `Action` handler ignores them), and capacity is capped at 32/game.

4. **The frontend can actually start and render a game spectate.** A "Watch"
   button in the lobby → `MultiplayerPage.handleSpectate` → navigate to
   `/game/:id?mode=spectate&code=...` (it reuses the normal game route with a
   query param) → the WS adapter sends `SpectatorJoin` → `GamePage` renders the
   real board with action UI gated off and a `SpectatorChrome` banner; the
   dispatch layer hard-blocks any action when `gameMode === "spectate"`.

5. **Draft spectating is a separate, parallel, also-complete feature** with its
   own route (`/draft-spectator`), store, and dashboard — and, importantly, it
   already has a **two-level visibility toggle**: `SpectatorVisibility::{Public,
   Omniscient}` (`crates/draft-core/src/types.rs`), host-configured at draft
   creation. Public = hidden info; Omniscient = full info. This is the exact
   precedent for the open question below.

6. **Spectator capacity is decoupled from lobby seats.** The `lobby-broker` crate
   has *zero* spectator references. Spectator slots are a phase-server fan-out
   registry keyed by `game_code`, entirely separate from player-seat/matchmaking
   logic. Draft's `SpectatorVisibility` lives in `draft-core`, not the broker.

## What is therefore actually open (the real scope of this phase)

Because the baseline feature works, the meaningful questions are about
**limitations and enhancements**, not core plumbing:

- **Open Q1 — Full-info vs hidden-info (the crux).** Games today support **only**
  the hidden-info-respecting view (all hands hidden). There is **no full-info /
  "omniscient" mode for games**, even though draft already has one. So the
  "streamer / commentary desk sees both hands, players consented" use case is
  currently impossible for games. Do we want to add an Omniscient game-spectator
  mode mirroring draft's? This likely needs to be **two distinct modes**, not one
  (see PLAN.md).

- **Open Q2 — P2P games are un-spectatable.** `SpectatorJoin` is rejected in
  `LobbyOnly` (P2P broker) mode because the server never runs the engine for P2P
  games. Casual P2P games therefore cannot be watched at all. Is that acceptable,
  or is P2P spectating (host-relayed) in scope?

- **Open Q3 — No explicit game-end signal to spectators.** Spectators receive
  `StateUpdate` only; they never get `Conceded` / `GameOver` (with winner/reason/
  ranked result). They must infer the result from the final state. Minor, but a
  visible UX gap (no win/loss banner for watchers).

- **Open Q4 — Discovery.** You can only watch a game whose code you already have
  (typed, or a lobby row you can see). `LobbyGame` carries no spectator count and
  there is no "spectatable games" browser or "N watching" badge.

- **Open Q5 — Pre-join history.** A spectator who joins mid-game gets the current
  snapshot and forward log entries only; earlier game-log history is not
  backfilled.

## Explicitly out of scope for this phase

- **Audio/video spectator channels.** A separate, unrelated research effort is
  looking at player audio/video chat. Whether spectators should ever get a
  commentary voice channel, or be able to see/hear players' A/V if players opt
  in, is a genuine cross-feature question — but it is **explicitly deferred**
  here. Flagged only so that whoever reconciles both features later is aware the
  spectator fan-out registry (`SharedGameSpectators`) is the natural join point
  if a spectator-side channel is ever wanted. Do not design it in this phase.

- **Spectator chat / emotes.** Players have emotes; spectators currently do not
  send anything. Out of scope unless explicitly requested.

- **Rewatch / VOD / replay of finished games — correction to an earlier draft
  of this doc.** An earlier pass cited PR `#2247` as "a replay feature exists
  separately." Verified directly (`gh pr view 2247`) and that's wrong: despite
  a stale title ("feat(client): replays, content i18n, spectator dashboard,
  2HG UI"), the PR's actual merged body is a pure mechanical refactor of
  `CardChoiceModal.tsx` with **no replay/spectator/i18n content** — its own
  description says those features were explicitly split out per review
  feedback ("keep this as a small, atomic PR... not bundled with replays,
  i18n, spectator"). So replay is **not** confirmed shipped anywhere. The
  real, still-open, unclaimed request is **phase-rs/phase#4613** ("Add
  action-based game replay system"), created 2026-06-29: export a
  deterministic `(header, ordered actions)` replay log from a local/AI game,
  reconstruct/seek/scrub it later in a read-only Replay Viewer reusing the
  existing spectate-mode `GameBoard` rendering path. This is a genuinely
  different problem from this phase's live spectating (post-hoc file-based
  playback of a finished/local game vs. live-viewing an in-progress
  multiplayer one) — not a duplicate, not blocked by or blocking this phase —
  but it's worth being aware both land on the same "read-only board UI" seam
  (`gameMode: "spectate"` disabling action dispatch), so a future contributor
  building #4613 will likely reuse the same visibility/redaction thinking
  this phase's RESEARCH.md documents for live spectators. Still out of scope
  here; flagged for awareness, not action.
