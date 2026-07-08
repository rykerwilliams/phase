# Phase 60 — Watch Game / Spectator Mode — PLAN

## Framing

Live-game spectating already works end-to-end in hidden-information mode (see
CONTEXT / RESEARCH). This plan therefore proposes **enhancements to a working
feature**, not a build-from-scratch. Every recommendation below is framed for
human confirmation — decide which, if any, are in scope before implementation.

If the answer to "what do we want from watch-game mode?" is *only* "let a friend
watch my live server game without seeing hands," **then nothing needs to be built
— it already exists.** The proposals below matter only if we want (a) full-info
broadcast/commentary spectating, (b) P2P-game spectating, or (c) discovery/UX
polish.

---

## Decision 1 (the crux): full-info vs hidden-info spectating

### Finding
Games currently support **one** mode: hidden-info (all hands hidden), via the
`PlayerId(255)` neutral viewer. Draft already supports **two**
(`SpectatorVisibility::{Public, Omniscient}`, host-configured). Different use
cases genuinely want different answers:

- **"Watch my friend's game"** — the watcher should see only what a fair observer
  could: public board, life totals, graveyards, stack. Hidden info stays hidden.
  This is the current behavior and is the safe default.
- **"Broadcast / commentary desk"** — a streamer or caster, with the players'
  consent, wants to see both hands (full information) to explain the game.

### Recommendation (for confirmation)
**Model this as two distinct modes, not one setting flipped in isolation** —
mirroring draft's `SpectatorVisibility`. Concretely:

1. Add a `SpectatorVisibility { Public, Omniscient }` (reuse the draft enum shape;
   consider promoting it to a shared crate rather than duplicating, but a small
   game-local enum is acceptable — decide during implementation) to the game's
   `GameSession` config, defaulted to `Public`.
2. **`Public` = today's behavior** (redact via `filter_state_for_viewer(state,
   PlayerId(255))`). No change.
3. **`Omniscient` = full-information view.** This needs a new engine path, because
   `filter_state_for_viewer` *always* redacts a non-seat viewer. Options
   (recommend Option A):
   - **Option A (recommended):** add an explicit
     `filter_state_for_spectator(state, visibility)` in the engine that, for
     `Omniscient`, returns a copy with **only the fairness/RNG redaction applied**
     (still zero the `rng_seed` — see visibility.rs:32-33; leaking it is never
     acceptable even to an omniscient spectator) but hands/libraries left visible.
     Keep it in the engine (CLAUDE.md: engine owns all logic). Public delegates to
     the existing `filter_state_for_viewer`.
   - Option B: bypass the filter entirely for Omniscient. **Rejected** — it would
     leak the RNG seed and any other future wire-sensitive fields, and scatters the
     redaction authority. The single-authority principle says all spectator views
     must go through one engine function.
4. **Gating — Omniscient must require consent, not just host opt-in.** Draft lets
   the host alone enable Omniscient. For games this is more sensitive (a host
   could otherwise broadcast their opponent's hand). Recommend: Omniscient is
   selectable at game creation **and** requires affirmative consent from **every
   human seat** before any Omniscient spectator is fed a full view. Until consent
   is unanimous, Omniscient spectators fall back to the `Public` view. (Confirm
   the exact consent UX with product — a per-game "allow full-information
   spectators" toggle each human accepts in the pre-game room is the natural fit.)
5. Carry the chosen visibility **per spectator sender** in the game spectator
   registry (exactly as `SharedDraftSpectators` already carries it, main.rs:90),
   or per-game if it's a single game-wide setting. Per-game is simpler and matches
   draft's "host sets it at creation"; per-sender only matters if you want mixed
   Public+Omniscient watchers on the same game. **Recommend per-game** for v1.

### Why two modes rather than a single boolean
The two use cases have different **default** and different **trust** requirements.
A single toggle invites the failure mode where a hidden-info watcher is
accidentally shown hands, or a broadcast desk can't get full info without the host
downgrading everyone. Two named modes with distinct gating make the safe thing the
default and the powerful thing explicit and consented — consistent with draft.

---

## Decision 2: P2P game spectating (recommend: out of scope for v1)

`SpectatorJoin` is Full-server-mode only; P2P (`LobbyOnly` broker) games run the
engine on the host, and the server has no state to fan out. Spectating P2P games
would require the **host** to relay redacted snapshots to spectators (either
through the broker as a dumb relay, or via additional P2P data connections).

**Recommendation:** defer. It is a materially larger lift (host-side fan-out,
redaction running client-side in WASM, new relay path) and orthogonal to the
full-info question. Document it as a known limitation: "only server-run (Full)
games can be spectated." Revisit only if P2P is the dominant play mode and users
ask for it.

---

## Decision 3: explicit game-end signal to spectators (recommend: small, do it)

Today spectators never receive `GameOver`/`Conceded` (main.rs:2850-2854); they see
the final `StateUpdate` but no winner banner. Low-effort, high-polish fix:

- On game end, after the players' `GameOver` broadcast, also send spectators an
  appropriate terminal message. Simplest correct approach: forward a
  **spectator-safe `GameOver`** (winner/reason are public; **omit `ranked_result`**
  — rating deltas are player-private) to the spectator registry, and have the
  spectator frontend render its existing game-over UI. Alternatively send a final
  `StateUpdate` plus a public `Conceded` when applicable.
- Confirm the frontend spectator path renders a game-over state from whichever
  message is chosen.

---

## Decision 4: discovery & UX polish (recommend: optional, low priority)

- **Spectator count:** add an optional `spectator_count` to the lobby row
  (`LobbyGame`) and a "N watching" badge. Requires the fan-out registry to report
  counts to the lobby broadcast path. Purely additive.
- **Pre-join history:** backfill recent `log_entries` to a joining spectator so
  they get context. The engine already retains a game log; send a bounded tail in
  the initial spectator `GameStarted`. Optional.
- Neither is required for a functional watch experience.

---

## Sequencing plan

Ordered by value-to-effort; each step is independently shippable. Steps 0 and 1
are the only ones that touch the "crux" question.

- **Step 0 — Confirm scope (human).** Decide: is hidden-info-only sufficient
  (ship nothing), or do we want Omniscient broadcast mode? Answer Decisions 1-4
  above. Nothing below proceeds without this.

- **Step 1 — Omniscient game-spectator mode** (only if Decision 1 = yes):
  1. Engine: add `filter_state_for_spectator(state, visibility)` (Public delegates
     to existing filter; Omniscient = RNG-redact-only). Unit-test both against the
     existing `filter.rs` test patterns — assert Omniscient shows hands but still
     zeroes the RNG seed. Annotate with the relevant hidden-information CR rules
     (CR 400.2 / 720-series info rules — verify exact numbers against
     `docs/MagicCompRules.txt` before annotating).
  2. Server: add visibility to `GameSession` config + creation message; route
     spectator snapshot builders through the new engine fn; gate Omniscient behind
     unanimous human consent (fall back to Public otherwise).
  3. Frontend: creation-room toggle + per-human consent UI; spectator lands in the
     appropriate view. Reuse the existing spectate route/board.
  - Follow `/add-interactive-effect` or the relevant skill checklist for any new
    WaitingFor/consent round-trip; run risk-scaled verification (this touches
    shared server routing → collect stronger Tilt evidence, not just the parser
    gate).

- **Step 2 — Game-end signal to spectators** (Decision 3): small server change +
  frontend render. Independent of Step 1.

- **Step 3 — Discovery polish** (Decision 4): spectator count badge, optional log
  backfill. Independent.

- **Non-goal this phase:** P2P spectating (Decision 2), spectator chat, A/V
  channels.

## Cross-feature note (audio/video research)

A separate research effort is examining player audio/video chat. This plan does
**not** design any spectator A/V or commentary channel. If both features ship, the
`SharedGameSpectators` fan-out registry (phase-server) is the natural integration
point for a spectator-side channel, and the `SpectatorVisibility` consent model
here should be reconciled with any A/V consent model there. Flagged for the future
reconciler; **not in scope now.**

## Architectural guardrails for whoever implements

- **Engine owns redaction.** All spectator views must be produced by a single
  engine function. Never redact in the server or client.
- **Never leak the RNG seed**, even to Omniscient spectators (visibility.rs:32-33).
- **Keep spectators read-only structurally** — do not give a spectator socket a
  `player_id`/`game_code`; the current design relies on their absence.
- **Mirror draft, don't reinvent.** `SpectatorVisibility`, `filter_for_spectator`,
  and the per-sender-visibility registry already exist for draft; follow that
  shape for consistency.
- **Consent for Omniscient is a rules-and-fairness matter**, not just UX — a
  full-info leak to a spectator during a ranked game is an integrity failure.
  Default to Public; require explicit, unanimous, human consent for Omniscient.
