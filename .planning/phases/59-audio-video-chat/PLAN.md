# Phase 59 — Player-to-Player Audio/Video Chat — PLAN

Research-and-design only. This document proposes an architecture, a consent/UX
flow, a scope gate, and a sequencing plan. Items marked **[CONFIRM]** are
recommendations framed for human decision, not settled calls.

## 1. Technical architecture

### 1.1 Reuse the existing PeerJS `Peer` — no new connectivity stack

The single most important design decision follows directly from RESEARCH §1–§3:
**A/V rides the `Peer` object the game already owns.** We do **not** create a new
`Peer`, a new signaling path, or a new STUN/TURN answer.

- Add a media transport built on PeerJS `MediaConnection`:
  - Enabling side calls `peer.call(remotePeerId, localStream)`.
  - Receiving side handles `peer.on("call", mc => ...)` (after consent, §2) and
    replies with `mc.answer(localStreamOrUndefined)`.
- The `remotePeerId` is already in scope on both sides (RESEARCH §1): guest knows
  `hostPeerId`; host learns each guest's `conn.peer`. Expose these to the media
  layer through a thin accessor on the adapters — **without** moving any game logic.
- Reuse `getPeerConfig()` ICE config (RESEARCH §2) — `MediaConnection` inherits the
  `Peer`'s config, so STUN/TURN is automatic.

### 1.2 New, isolated frontend module — `client/src/media/`

Per RESEARCH §7, keep this entirely separate from `client/src/audio/`. Proposed
shape (names indicative):

- `client/src/media/mediaSession.ts` — wraps a PeerJS `MediaConnection`: manages
  `getUserMedia`, local track enable/disable (mute mic / stop camera), remote
  stream exposure, teardown. Mirrors the shape/rigor of
  `network/peer.ts`'s `PeerSession` (lifecycle, keep-alive-agnostic, explicit
  close).
- `client/src/media/mediaController.ts` — per-match orchestration: which remote
  peers to call, consent state, wiring to adapter events
  (`P2PAdapterEvent`). One `MediaSession` per remote peer.
- `client/src/media/useMediaChat.ts` — React hook exposing state (per-peer:
  offered / connecting / live / muted / declined) and actions (enable mic, enable
  camera, mute, stop, accept, decline, disable-all) to the UI.
- `client/src/components/media/` — UI: an opt-in control (mic/camera toggles), a
  consent prompt, small video tiles, and a one-click mid-match kill switch.
- A runtime feature flag (default **off**) gates the entire module so the feature
  is invisible unless explicitly enabled (supports the fork-first posture in
  CONTEXT).

### 1.3 What must NOT change

- **`crates/engine/` — untouched.** A/V carries no game state and no rules. This is
  the constraint check from CONTEXT §6: it holds cleanly. No new engine variant, no
  new `GameAction`, no state field.
- **The game data channel is unaffected.** A/V uses a *separate*
  `RTCPeerConnection` (via `MediaConnection`) over the same `Peer`. Media
  congestion never touches `state_update` ordering.
- **No new signaling/broker code.** RESEARCH §3 — PeerJS handles media SDP/ICE.

### 1.4 Infra changes required (small, real)

- **Tauri CSP** (RESEARCH §5): add `mediastream:` (and likely `blob:`) to
  `media-src`; verify `connect-src` reaches the TURN credential + Realtime
  endpoints for the desktop build.
- **macOS desktop packaging:** add `NSCameraUsageDescription` /
  `NSMicrophoneUsageDescription` to the bundle Info.plist for the camera/mic OS
  permission prompt. (Windows WebView2 and Linux WebKitGTK handle this at the OS
  level differently; test per target.)
- **No new server infra** — the TURN worker (`lobby-worker/src/turn.ts`) is reused
  as-is; only its *bandwidth usage* rises for relayed media sessions (monitor via
  existing telemetry).

## 2. Consent / privacy / UX flow

Design principle: **A/V is only ever what YOU choose to send, and you are never
surprised by what you receive.**

### 2.1 Recommended model **[CONFIRM]** — independent outbound opt-in + one-time inbound accept

- **Default off, always.** Nothing is captured and no permission is requested on
  page load or match start. `getUserMedia` fires only on an explicit user tap of
  "Enable microphone" / "Enable camera."
- **Outbound is unilateral and per-stream.** Each player independently enables
  their *own* mic and/or camera. This matches the task's framing ("each player can
  independently choose to enable their own microphone and/or camera"). You cannot
  enable someone else's devices, and you are never forced to send.
- **Inbound requires a one-time per-match accept.** The first time a peer offers
  A/V, the receiver sees a non-blocking prompt: *"Player X wants to start
  voice/video in this match — Accept / Decline."* This prevents a stranger's voice
  or face from appearing unannounced. After accept, either side may toggle their
  own streams freely for the rest of the match. Decline hard-blocks that peer's
  A/V for the match.
- **Always-available mid-match controls:** one-tap mute-mic, stop-camera (local),
  mute-incoming / hide-incoming (per remote), and a single "Turn off A/V" that
  tears down the `MediaConnection` entirely and revokes the media tracks.
- **Persistence:** remember device *selection* (which mic/camera) across sessions
  is fine; **do not** persist an "auto-enable / always broadcast" state. Enabling is
  an explicit affirmative action each match.

Rationale: this is the least-surprising model that still honors "independent
per-player opt-in." Outbound stays fully in the sender's control (privacy), while
the one-time inbound accept gives the receiver consent over what appears on their
screen/speakers (anti-harassment). It avoids the heavier symmetric "call invite"
handshake (model A) while being safer than pure independent streaming (model B),
which would let audio from a stranger start with no acceptance step.

### 2.2 Rejected alternatives (documented)

- **Symmetric "start a call, other accepts, both-or-nothing" (model A):** simplest
  consent story, but breaks the "each player independently enables their own
  devices" framing (you couldn't send audio while your opponent sends none).
- **Pure independent streaming, no accept step (model B):** matches the framing
  most literally but lets a stranger's mic/camera reach you with no gate — bad for
  the public-matchmaking harassment surface. The one-time accept in §2.1 is the
  minimal fix.

## 3. Scope gate — private games only, initially **[CONFIRM]**

Recommend **gating A/V availability to non-public games** using the existing
`public: bool` broker field (RESEARCH §4). Live A/V is offered only in matches
reached by a deliberately-shared room code / password, i.e. where both players
already have an out-of-band relationship (friends). It is **not** offered in public
matchmaking against strangers.

Rationale: public matchmaking pairs strangers; a live A/V channel there is a
harassment vector with no moderation tooling (no reporting-with-evidence, no
blocking infra, no recording) in the codebase today. Private-only gating removes
the stranger surface almost entirely at zero infra cost, using a field that already
exists. Revisit public-matchmaking A/V only if/when moderation tooling exists — and
that revisit may reasonably never happen upstream (CONTEXT).

## 4. Sequencing — audio first, then video, multi-party last

Recommended increments, smallest/lowest-risk first:

- **Phase 0 — Scaffolding & consent plumbing (no media yet).**
  New `client/src/media/` module skeleton, feature flag (default off), consent
  state machine + UI, adapter peer-id accessors, CSP + macOS Info.plist changes.
  Verifiable without any camera/mic by exercising the consent state machine.

- **Phase 1 — Audio-only, 2-player private games. [recommended first shippable]**
  `MediaConnection` with an audio-only `getUserMedia` stream between the two peers
  in a private match. Lowest bandwidth (Opus ~24–48 kbps → cheapest TURN relay,
  RESEARCH §2), smallest UI (no video tiles), lowest harassment surface. This
  validates the entire "media over the existing `Peer`" approach end-to-end.

- **Phase 2 — Video, 2-player private games.**
  Add camera capture, local/remote video tiles, resolution/bitrate caps, and reuse
  the existing relayed-session telemetry (`logSelectedIceCandidate`, `turn.ts`) to
  watch TURN relay bandwidth. The bitrate cap is the primary cost lever.

- **Phase 3 — Multi-party (3–6p) A/V. [defer; optional]**
  Blocked on the hub-and-spoke topology gap (RESEARCH §1): guests are not
  peer-connected to each other. Options: (a) a full mesh of `MediaConnection`s
  (each human calls each other human — N² connections, acceptable at ≤4 players),
  or (b) host-relayed media (worse quality, host CPU/bandwidth burden). Recommend a
  full mesh for small pods, but **defer entirely until 2p is proven** and only if
  demand exists.

- **Public-matchmaking A/V — deferred indefinitely**, pending moderation tooling
  (report, block, mute-by-default). May remain permanently fork-only (CONTEXT).

Rationale for audio-first: it delivers the majority of the "talk while we play"
value at a fraction of video's bandwidth cost, harassment surface, and UI
complexity, and it de-risks the core plumbing before video is layered on.

## 5. Verification approach (per increment)

- Phase 0: unit-test the consent state machine and feature-flag gating; no media.
- Phase 1/2: manual two-browser (and two-desktop-build) smoke test — enable audio,
  confirm two-way; confirm consent prompt on the receiver; confirm mid-match kill
  switch tears down tracks; confirm the game data channel is unaffected during a
  media call; confirm `logSelectedIceCandidate` reports direct vs. relayed so relay
  cost is observable. Verify getUserMedia permission + CSP on each real target
  (web, Windows/WebView2, macOS/WKWebView, Linux/WebKitGTK).
- The engine test suites are irrelevant here (no engine change) — a positive signal
  that the architectural constraint held.

## 6. Summary of recommendations needing human confirmation

1. **Consent model:** independent outbound opt-in + one-time inbound accept (§2.1).
2. **Scope gate:** private games only, initially, via the existing `public` flag (§3).
3. **Sequencing:** audio-only first, then video, multi-party deferred (§4).
4. **Upstream posture:** ship as an isolated, default-off, private-only module that
   *could* upstream but is realistically fork-first — the maintainer decides based on
   appetite for the privacy/moderation/infra/legal surface (CONTEXT).
