# Phase 60 — Watch Game / Spectator Mode — RESEARCH

All paths are relative to the worktree
`C:\git\phase\.claude\worktrees\research-watch-game`. Line numbers were current at
research time; treat them as anchors, re-grep before editing.

## 1. Engine: per-viewer hidden-information redaction (the security foundation)

**`crates/engine/src/game/visibility.rs`** — `filter_state_for_viewer(state, viewer) -> GameState`
(fn at line 16). This is the authoritative, server-enforced redaction. Highlights:

- Clones state, then **zeroes `rng_seed` and reseeds `rng`** (lines 32-33) with a
  documented rationale: the ChaCha20 seed is a serialized field of `GameState`;
  broadcasting it would let any recipient predict every future shuffle/draw/flip
  and reconstruct hidden library order. So redaction is not just about hands — it
  closes an RNG wire leak too.
- `can_view_private_for_player` closure (line 35) — a player sees private data only
  for themselves or (2HG) the active-turn player they control.
- Opponent hand cards hidden unless revealed or under a private "look" (lines 52-63).
- Also redacts `OpponentGuess` secrets (82), `ManifestDreadChoice` (111),
  `DigChoice` (126), pending-trigger private payloads per controller, deck pools,
  etc. This is a mature, well-tested redaction layer (many `#[cfg(test)]` cases in
  `crates/server-core/src/filter.rs`).

**`crates/engine/src/game/players.rs`** — `opponents(state, player)` (line 160)
filters `seat_order` by `is_opponent(...) && is_alive(...)`. For a non-seat viewer
like `PlayerId(255)`, **no real seat equals the viewer**, so every player is an
"opponent" and every hand/library is hidden → the sentinel yields a fully public
(hidden-info) view. This is why `PlayerId(u8::MAX)` works as a neutral spectator.

**`crates/server-core/src/filter.rs`** — thin wrappers `filter_state_for_player`
(line 9) and `filter_events_for_player` (line 14) delegating to the engine. Tests
in this file prove the sentinel behavior:
- `non_seat_spectator_sees_no_player_hands` (line 123) — filters with
  `PlayerId(u8::MAX)` and asserts *every* player's hand is `"Hidden Card"`,
  face-down, no abilities. **This is the spectator hidden-info contract, tested.**
- `own_hand_is_fully_visible`, `opponent_hand_cards_are_hidden`,
  `library_contents_hidden_for_both`, `redacts_opponent_deck_pool_details`,
  `manifest_dread_hides_card_ids_from_opponent`, plus per-group pending-trigger
  redaction tests.

## 2. Server: `phase-server/src/main.rs` — the live-game spectator implementation

Spectator support here is complete. Key sites:

- **Constant** — `const SPECTATOR_PLAYER_ID: PlayerId = PlayerId(u8::MAX);` (line 88).
- **Fan-out registry** — `type SharedGameSpectators = Arc<Mutex<HashMap<String,
  Vec<mpsc::UnboundedSender<ServerMessage>>>>>` (line 103): per-`game_code` list of
  spectator senders. (Draft has a parallel `SharedDraftSpectators` that also carries
  a `SpectatorVisibility` per sender, line 90.)
- **Slot management** — `reserve_game_spectator_slot` (135), `switch_game_spectator_slot`
  (153), `remove_game_spectator_sender` (121). Prunes closed senders, idempotent for
  the same channel, enforces cap via `guard_game_spectator_capacity`.
- **Spectator message builders**:
  - `build_spectator_game_started_message(session)` (347): calls
    `filter_state_for_player(&session.state, SPECTATOR_PLAYER_ID)`, sets
    `your_player = SPECTATOR_PLAYER_ID`, `legal_actions = []`,
    `legal_actions_by_object = {}`, no `player_token`. (lines 348-364)
  - `build_spectator_state_update_message(raw_state, events, log_entries)` (367):
    same redaction, empty legal actions, forwards filtered events + log entries.
- **`ClientMessage::SpectatorJoin { game_code }` handler** (line 5020):
  validates code (`guard_spectator_join`), requires the session to exist and
  `game_started` (rejects with `Error` otherwise), reserves a spectator slot,
  sends the redacted `GameStarted`, records `identity.spectator_game_code`. (5020-5095)
- **Broadcast on updates** — spectators receive a fresh redacted `StateUpdate`
  on the normal action-broadcast path (lines 3336, 3427) and on `GameStarted`
  broadcast (2713), plus a synthetic `StateUpdate` after a takeback rollback (2855)
  so they don't freeze.
- **Cleanup** — on socket close, `remove_game_spectator_sender` (1602).
- **Read-only by construction** — `SocketIdentity` keeps `spectator_game_code`
  **separate** from `game_code`/`player_id` precisely "so spectator sockets remain
  read-only" (comment, lines 533-535). The `ClientMessage::Action` handler (3125)
  begins with `let game_code = match &identity.game_code { ... }` (3126), which is
  `None` for a spectator → the action is dropped. No explicit "reject spectator
  action" branch is needed; it's structural.
- **Mode gating** — `SpectatorJoin` is grouped with game-state messages that are
  **Full-mode only** (lines 635-648): in `LobbyOnly` (P2P broker) mode it is
  rejected with `LOBBY_ONLY_REJECTION`. So **P2P games cannot be spectated**.
- **Capacity guard** — `crates/server-core/src/spectator_wire_guard.rs`:
  `MAX_GAME_SPECTATORS_PER_GAME = 32` (line 10), `guard_spectator_join` (17),
  `guard_game_spectator_capacity` (22). Draft equivalents alongside.
- **Tests** — `mod live_spectator_tests` (line 6044):
  `spectator_state_update_keeps_public_status_without_actions`,
  `game_spectator_reservation_rejects_when_game_is_at_cap`,
  `..._prunes_closed_senders_before_cap_check`, `..._is_idempotent_for_same_channel`,
  `game_spectator_switch_keeps_previous_game_when_new_game_is_full`, plus a
  `SpectatorJoin` dispatch test (line 6513).

### Confirmed server-side gaps

- **No `GameOver`/`Conceded` to spectators** (comment, lines 2850-2854): "they
  never receive `Conceded`/`GameOver`, just like [not] `TakebackResolved`." A
  spectator sees the final `StateUpdate` (with game result reflected in state) but
  no explicit winner/reason/ranked-result message.
- **No full-info mode** for games — `SPECTATOR_PLAYER_ID` is the only spectator
  viewer, always fully redacted. No omniscient path.

## 3. Wire protocol: `crates/server-core/src/protocol.rs`

- `ClientMessage::SpectatorJoin { game_code }` (line 176). `ClientMessage::SpectateDraft
  { draft_code }` (229) is the draft analog.
- Spectators receive the **standard** `ServerMessage::GameStarted` (279) and
  `ServerMessage::StateUpdate` (315) — there is **no dedicated spectator message
  type** for games (they reuse the player messages with redacted payload + empty
  legal actions). Draft, by contrast, has a bespoke `ServerMessage::DraftSpectatorView
  { view: SpectatorDraftView }` (465).
- No spectator-count field on `LobbyGame` (re-exported from `lobby-broker`,
  line 60).

## 4. Draft spectating — the two-mode precedent

**`crates/draft-core/src/types.rs`** (line 33):
```rust
pub enum SpectatorVisibility {
    #[default]
    Public,      // battlefield/standings/pairings visible; pools & packs hidden
    Omniscient,  // all pools & current packs visible (host must explicitly enable for Casual)
}
```
**`crates/draft-core/src/view.rs`** — `filter_for_spectator(session, visibility) ->
SpectatorDraftView` (line 124): branches on `Public` vs `Omniscient` to decide
whether to expose pools/packs. Host sets `config.spectator_visibility` at draft
creation. Tests: `spectator_public_view_hides_pools_and_packs` (950),
`spectator_omniscient_view_exposes_all_pools` (963).

This is the model to mirror for games (see PLAN.md). Note draft carries the chosen
visibility **per spectator sender** in `SharedDraftSpectators` (main.rs:90) and
per draft config; a game equivalent would live in `GameSession` config + the
game spectator registry.

## 5. Frontend — game spectating is reachable end-to-end

(Findings corroborated by direct reads of the linchpin sites.)

- **`client/src/constants/game.ts:40`** — `export const SPECTATOR_PLAYER_ID = 255;`
  (documented as matching the server sentinel).
- **`client/src/adapter/ws-adapter.ts`** — adapter constructor takes
  `mode: "host" | "join" | "spectate"` (line 161); on init, `"spectate"` sends
  `{ type: "SpectatorJoin", data: { game_code } }` (231-232). Also a standalone
  `sendSpectatorJoin(gameCode)` (438-440). `GameStarted`/`StateUpdate` are handled
  generically: `this._playerId = data.your_player` (633) so `255` flows through and
  the empty `legal_actions` yield no available actions.
- **`client/src/pages/MultiplayerPage.tsx`** — `handleSpectate(code, context?)`
  (553): draft codes (or lookup `not_found`) route to `/draft-spectator?code=...`;
  otherwise `navigate('/game/${gameId}?mode=spectate&code=${code}')` (575).
- **`client/src/App.tsx`** — routes: `/game/:id` (line 123, reused for spectating
  via query param) and `/draft-spectator` (121). **No dedicated `/spectate/:code`
  or `/watch/...` route** — game spectating overloads the standard game route.
- **`client/src/components/lobby/LobbyView.tsx`** — a "Watch" button
  (`t("lobbyView.watch")`) rendered when `isServer && onSpectate` (440-454); wired
  in `MultiplayerPage` to `handleSpectate` for `connectionMode === "server"`.
- **`client/src/game/dispatch.ts:543`** — `dispatchAction` returns early if
  `gameMode === "spectate" || actor === SPECTATOR_PLAYER_ID`. Client-side hard block.
- **`client/src/hooks/useSpectatorMode.ts`** — returns true if
  `gameMode === "spectate" || isSpectator || playerId === SPECTATOR_PLAYER_ID`.
- **`client/src/pages/GamePage.tsx`** — calls `useSpectatorMode()` (838); gates
  action clusters (`{!isSpectatorMode && ...}` 1404), shows `TurnStatusLine`
  instead of controls (1429-1431), renders `<SpectatorChrome />` (1228). Same board
  component tree, read-only flag threaded through.
- **`client/src/components/spectator/SpectatorChrome.tsx`** — fixed banner + "Leave"
  (→ `/multiplayer`) + "watching with {names}" from `multiplayerStore.spectators`.
- **Stores** — `multiplayerStore`: `isSpectator` (+ `setIsSpectator`), `spectators:
  string[]`. `gameStore`: `GameMode` union includes `"spectate"`;
  `isMultiplayerMode()` treats spectate as multiplayer.
- **Draft-spectate frontend (parallel, complete)** — `DraftSpectatorPage.tsx`,
  `stores/draftSpectatorStore.ts`, `services/draftSpectatorSession.ts`,
  `components/draft/DraftSpectatorDashboard.tsx`.

### Confirmed frontend gaps

- No UI to *choose* a visibility level when spectating a game (there's only one
  mode server-side, so nothing to choose yet).
- No explicit game-over banner for spectators (server never sends `GameOver`).
- No spectator-count display on lobby rows.

## 6. Summary table — what exists vs. what's missing

| Concern | Status |
|---|---|
| Engine per-viewer redaction | DONE, robust, tested |
| Spectator = `PlayerId(255)` neutral view | DONE, tested |
| Server `SpectatorJoin` + fan-out | DONE, tested |
| Spectator read-only enforcement | DONE (structural) |
| Per-game spectator cap (32) | DONE, tested |
| Frontend Watch button + route + adapter + read-only board | DONE |
| Draft spectating (separate) | DONE, incl. Public/Omniscient |
| **Full-info / Omniscient mode for games** | **MISSING** |
| **P2P game spectating** | **MISSING (Full-mode only)** |
| **`GameOver`/`Conceded` to spectators** | **MISSING** |
| **Spectator discovery / count** | **MISSING** |
| **Pre-join log/history backfill** | **MISSING** |
