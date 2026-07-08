# Phase 59 — Player-to-Player Audio/Video Chat — CONTEXT

## Why this matters

Players in a live multiplayer MTG match currently have no in-app way to talk to
each other. Voice (and optionally video) chat between the humans in a match is a
quality-of-life feature for friend games and remote play — the "kitchen table"
experience of playing paper Magic with someone in the room, reconstructed over
the network. This is explicitly **person-to-person live communication layered
onto an existing game session**, not:

- spectator broadcast / streaming,
- game sound effects or music (that is `client/src/audio/`, a separate concern —
  see RESEARCH §7),
- text-to-speech or any synthesized audio,
- recorded or persisted content.

Each player independently opts in to enabling their **own** microphone and/or
camera. It is a communication channel, carrying **zero game state and zero game
rules**.

## Confirmed facts (see RESEARCH.md for file:line citations)

1. **The existing multiplayer transport is true WebRTC peer-to-peer**, built on
   PeerJS 1.5.5. Game-state sync flows over an `RTCDataChannel`
   (`DataConnection`). This is *not* a relayed-WebSocket-through-a-server model —
   it is genuine browser-to-browser WebRTC. This is the single most important
   fact: audio/video is a **small, well-understood extension** of infrastructure
   that already exists and works in production, not a new connectivity stack.

2. **STUN and TURN are already provisioned, operational, and paid for.** The
   project runs a Cloudflare Worker (`lobby-worker/src/turn.ts`) that mints
   short-lived Cloudflare Realtime TURN credentials, with a STUN fallback
   (`stun.cloudflare.com:3478`). Every PeerJS `Peer` is already constructed with
   this ICE config. Audio/video reuses it verbatim — **no new STUN/TURN answer is
   required.**

3. **PeerJS has first-class media support.** `peer.call(peerId, mediaStream)` and
   `peer.on("call", ...)` establish a `MediaConnection` over the *same* `Peer`
   object (same signaling registration, same ICE config) that the data channel
   already uses. Both adapters retain their `Peer` and the remote peer ID.

4. **Multiplayer already distinguishes public matchmaking from private games.**
   The lobby broker's `RegisterGameRequest` carries `public: bool` and
   `password: Option<String>`; public games appear in a listing, private/friend
   games are code- or password-gated. This is a clean, pre-existing gate point.

5. **Deployment targets are web (browser over HTTPS) + a Tauri desktop app**
   (macOS/Windows/Linux). There is **no mobile/iOS/Android target** in the Tauri
   config. This bounds the browser-compatibility analysis to real targets.

6. **The engine constraint holds cleanly.** A/V touches no game state and no
   rules. It lives entirely in the frontend plus the already-existing PeerJS +
   lobby-worker layer. **It does not touch `crates/engine/` at all.** The only
   backend surface it reuses (the TURN worker) already exists. We found no reason
   the "engine owns all logic / frontend is display-only" constraint is violated —
   A/V is neither logic nor display *of game state*; it is an orthogonal
   communication channel bolted onto the same transport.

## Open / unresolved questions (for human decision)

- **Consent model:** unilateral outbound opt-in vs. symmetric "call invite +
  accept" handshake. PLAN §Consent recommends a hybrid; needs confirmation.
- **Scope gate:** private-games-only vs. also public matchmaking. PLAN
  recommends private-only initially; needs confirmation.
- **Audio-first vs. audio+video together.** PLAN recommends audio-first
  sequencing; needs confirmation.
- **Upstream vs. fork-only** (see below) — the central product/governance call.

## Is this realistically upstream-mergeable?

This is a genuine judgement call for the project maintainer, not something an
agent should decide. Laying out both sides honestly:

### Arguments *for* upstream mergeability

- **Purely additive and opt-in.** Default-off; a user who never enables it sees
  zero behavior change and grants no permissions.
- **Architecturally clean.** Zero engine involvement — it respects the project's
  #1 hard constraint (engine owns all logic) without strain, because A/V simply
  isn't game logic. It slots into the existing PeerJS transport as an isolated
  frontend module.
- **Reuses existing, already-paid infrastructure.** STUN/TURN, signaling, and ICE
  config all exist. The marginal *code* footprint is small and the marginal
  *operational* footprint is bounded and already-monitored (the codebase already
  logs TURN-relayed sessions and tracks relay quota — see RESEARCH §2).
- **Private-game gating shrinks the abuse surface dramatically** — the feature can
  ship where both players deliberately shared a code, not to strangers.

### Arguments *against* (real maintainer concerns)

- **Privacy / data-class mismatch.** Live camera and microphone streams of real
  people are a categorically different and more sensitive data class than an MTG
  rules engine. A maintainer may reasonably not want the project to *own the
  responsibility* of carrying people's faces and voices, even peer-to-peer.
- **Moderation / harassment surface.** A live A/V channel enables abuse that text
  filtering cannot catch (showing or saying something over live video). No
  reporting, blocking-with-evidence, or moderation tooling exists today. Private-
  only gating reduces but does not eliminate this.
- **Variable, usage-scaling infra cost.** Today's data-channel TURN relay is
  negligible (kilobytes). *Video* relay for the fraction of sessions behind
  symmetric NAT/CGNAT is a materially larger, variable bandwidth cost on
  Cloudflare Realtime TURN that the maintainer would carry — a usage spike could
  burn quota or incur real bills. Audio-only is far cheaper.
- **Mission fit and maintenance burden.** The project's identity is an idiomatic
  Rust MTG rules engine. A WebRTC media-chat feature is orthogonal to that
  mission, adds frontend surface area, and brings a permanent maintenance tail
  (PeerJS media quirks, browser API churn, permission-model changes) with no
  engine/rules value in return.
- **Legal/consent exposure.** Even without recording, live A/V touches
  jurisdiction-specific consent expectations (GDPR, two-party-consent
  wiretap-style laws). A maintainer may not want that exposure on the project.

### Recommendation (for human confirmation)

**Build it as an isolated, default-off, private-games-only, frontend-only module
that *could* be upstreamed but is realistically fork-first.** Concretely: keep
100% of it in a new `client/src/media/` module behind a runtime feature flag that
defaults off, reuse the existing infra, and present it to the maintainer as a
self-contained, opt-in feature. The maintainer then makes the one call an agent
cannot: whether they are comfortable *owning* the privacy, moderation, infra-cost,
and legal surface that live A/V brings. If yes, the isolation makes it a low-risk
merge; if no, the same isolation makes it a clean, low-friction fork carry. The
honest expectation, given the concerns above, is **fork-first with an upstream
door left open** — matching the requester's own "probably wouldn't get merged
upstream ever, but maybe."
