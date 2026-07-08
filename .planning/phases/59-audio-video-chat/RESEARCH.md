# Phase 59 — Player-to-Player Audio/Video Chat — RESEARCH

All citations are against this worktree
(`.claude/worktrees/research-audio-video`) at branch
`research/audio-video-gameplay`.

## 1. The existing multiplayer transport is true WebRTC P2P (not relayed WS)

**Finding: genuine browser-to-browser WebRTC via PeerJS. A/V can piggyback on the
existing `Peer`.**

- `client/package.json` declares `"peerjs": "^1.5.5"` as the only P2P dependency.
  There is no simple-peer, no raw `RTCPeerConnection` wrapper, no relayed-socket
  game transport. (`ws-adapter.ts` exists but is the *server-authoritative* mode,
  a separate path; the P2P mode is PeerJS.)
- `client/src/network/connection.ts:1` — `import Peer from "peerjs"`. `hostRoom()`
  (`connection.ts:328`) and `joinRoom()` (`connection.ts:446`) create real PeerJS
  `Peer`s that register on the public `0.peerjs.com` signaling cloud, namespaced
  with a `phase2-` peer-id prefix (`connection.ts:20`).
- The game-state channel is an `RTCDataChannel`: `joinRoom` calls
  `peer.connect(peerId, { serialization: "binary", reliable: true })`
  (`connection.ts:481`), yielding a PeerJS `DataConnection`. `peer.ts` wraps it as
  a `PeerSession` and confirms it is backed by an `RTCPeerConnection` —
  `connection.ts:107` types `IceStatsSource.peerConnection?: RTCPeerConnection`
  and `logSelectedIceCandidate` reads `conn.peerConnection.getStats()`.
- **Topology is hub-and-spoke** (`p2p-adapter.ts:233-244` doc comment): the host
  runs the authoritative WASM engine and holds one `PeerSession` per guest
  (`guestSessions: Map<PlayerId, PeerSession>`, `p2p-adapter.ts:249`). In a 2-player
  game this is a single direct host↔guest WebRTC connection. In 3–6 player games
  guests connect to the host but **not to each other** — a fact that matters for
  multi-party A/V (see PLAN §Sequencing).
- Both adapters retain their `Peer` and the remote peer ID, which is exactly what
  `peer.call()` needs:
  - Host: `P2PHostAdapter` is constructed with `hostPeer: Peer`
    (`p2p-adapter.ts:312`); each inbound guest `DataConnection` carries the guest's
    peer id on `conn.peer`.
  - Guest: `P2PGuestAdapter` holds `hostPeer` and `hostPeerId`
    (`p2p-adapter.ts:1592`, `:1623`, and dials with
    `this.hostPeer.connect(this.hostPeerId)` at `:1988`).

**Consequence:** the hard part of WebRTC A/V — signaling, ICE negotiation, NAT
traversal setup — is *already done* and reusable. This is the "small extension"
case, not the "separate connection-establishment stack" case.

## 2. STUN/TURN infrastructure — already provisioned, operational, and paid

**Finding: A/V reuses the existing ICE config verbatim. No new STUN/TURN answer
needed. The only honest new cost is *media relay bandwidth* on sessions that fall
back to TURN.**

- `client/src/network/connection.ts:34-74`: ICE config is fetched from
  `https://lobby.phase-rs.dev/turn-credentials` (`TURN_CREDENTIALS_URL`,
  `connection.ts:39`), cached 6h (`ICE_CONFIG_CACHE_MS`), with a STUN-only
  fallback `stun:stun.cloudflare.com:3478` (`FALLBACK_ICE_CONFIG`,
  `connection.ts:44`). Every `new Peer(...)` is built with this config
  (`connection.ts:252` host, `:454` guest).
- `lobby-worker/src/turn.ts` is the credential minter. It POSTs to Cloudflare
  Realtime's `.../v1/turn/keys/{id}/credentials/generate-ice-servers`
  (`turn.ts:84`) using a secret token, returns `{ iceServers }` with a 24h TTL
  (`turn.ts:82`), and **already instruments relay usage per client network**
  (`clientContext` / `customIdentifier`, `turn.ts:45-56`) precisely to track "which
  carriers (notably CGNAT / symmetric-NAT mobile networks) actually drive relay
  demand" and flag quota burn (`turn.ts:38-43`).
- The client *already* observes and logs whether a session went direct vs.
  TURN-relayed: `logSelectedIceCandidate` (`connection.ts:111-146`) marks relayed
  pairs `"⚠️ RELAYED VIA TURN (paid bandwidth)"` vs `"✓ direct"`, with a comment
  noting the free-tier quota and 2× relay traffic multiplication.

**Cost honesty for A/V (the part the design must name plainly):**
- Game-state relay today is negligible (compressed KB-sized `state_update`s).
- Most WebRTC sessions connect **directly** (host/srflx candidates); only
  symmetric-NAT / CGNAT peers relay via TURN. So relay applies to a *fraction* of
  sessions.
- But **media is orders of magnitude larger** than game state: Opus voice is
  ~24–48 kbps; VP8/VP9 video is ~0.3–2.5 Mbps per stream. On a relayed session
  these bytes traverse the Cloudflare Realtime TURN relay (billed per GB) for the
  full multi-minute-to-hour duration of a game, doubled (ingress + egress). This is
  a **real, variable, usage-scaling cost** that does not exist today at meaningful
  volume. Audio-only is dramatically cheaper than video and is the reason PLAN
  sequences audio first. The existing relay telemetry (`turn.ts`,
  `logSelectedIceCandidate`) can be reused to monitor A/V relay burn from day one.

## 3. Signaling — reuse the existing PeerJS `Peer`; do NOT build a second mechanism

**Finding: PeerJS's native media API rides the existing signaling.**

- PeerJS `Peer` exposes `peer.call(peerId, MediaStream)` → `MediaConnection`, and
  `peer.on("call", (mc) => mc.answer(localStream))` for the receiving side. These
  use the *same* signaling-server registration and the *same* ICE `config` the
  `DataConnection` already uses. No SDP/ICE relay code needs to be written — it is
  handled inside PeerJS, identically to how the data channel is handled today.
- A `MediaConnection` opens its own `RTCPeerConnection` (separate from the data
  channel's), but shares the `Peer`. So "reuse the existing signaling/ICE
  machinery" is literally true: same `Peer`, same STUN/TURN, new media transport.
- The lobby broker (`crates/lobby-broker/`, `lobby-worker/src/lobby-do.ts`) brokers
  *lobby discovery and peer-id exchange*, not per-connection SDP — that already
  lives in PeerJS. So there is nothing to add on the broker/signaling side for A/V.

## 4. Public vs. private matchmaking — a clean, pre-existing gate

**Finding: the broker already models public/private; gating A/V to private games
is a natural scope reduction.**

- `crates/lobby-broker/src/lobby.rs:33` — `RegisterGameRequest { public: bool, ...,
  password: Option<String> }`.
- `lobby.rs:293` `public_game()` and `:301` `public_games()` filter to `meta.public`;
  the broker fans out public listings (`broker.rs:166`, `:271`, `:422`). Private
  games are reachable only by code/password.
- **Implication:** A/V availability can be gated on "this match is not a public
  matchmaking game" using an already-present field, confining live A/V to matches
  where both players deliberately shared a room code / password (i.e., have an
  out-of-band relationship). This shrinks the stranger-harassment surface to near
  zero without new infrastructure.

## 5. Browser / desktop compatibility — grounded in real deployment targets

**Finding: web (HTTPS) + Tauri desktop (macOS/Windows/Linux). No mobile. Two
concrete, real changes are needed: getUserMedia gating and CSP.**

- `client/src-tauri/tauri.conf.json`: `bundle.targets: "all"`, icons for macOS
  (`.icns`), Windows (`.ico`), Linux; `externalBin: ["binaries/phase-server"]`.
  There is **no iOS/Android target** — so generic "mobile WebView getUserMedia is
  spotty" boilerplate does not apply here.
- **`getUserMedia` requires a secure context.** The production web app is served
  over HTTPS (`phase-rs.dev`) and localhost is exempt, so this is satisfied on the
  web. The Tauri webview serves from a custom scheme and is a secure context.
- **CSP will block media as currently written** (`tauri.conf.json` `security.csp`):
  - `media-src 'self' https://data.phase-rs.dev` — does **not** include
    `mediastream:` / `blob:`. A `MediaStream` assigned to a `<video>.srcObject` is
    governed by `media-src` in some engines; the desktop CSP must add `mediastream:`
    (and likely `blob:`) for local/remote camera preview to render.
  - `connect-src` includes `wss:` (covers the PeerJS `0.peerjs.com` signaling
    socket) but the TURN credential fetch to `lobby.phase-rs.dev` and the Cloudflare
    Realtime TURN endpoints must be reachable; verify `connect-src` covers them for
    the desktop build (the web build has no such CSP restriction unless one is set
    at the server).
  - The web build's CSP (if any is set server-side) needs the same audit.
- **Desktop webview engines differ.** Tauri uses the OS webview: WebView2
  (Chromium) on Windows — full getUserMedia support; WKWebView on macOS — supports
  getUserMedia in recent macOS but with stricter permission prompting; WebKitGTK on
  Linux — getUserMedia support is the least consistent and may require the
  `webkit2gtk` build to have the right multimedia backend. The desktop OS-level
  camera/mic **permission** (separate from the browser prompt) must also be
  granted; on macOS this requires `NSCameraUsageDescription` /
  `NSMicrophoneUsageDescription` entries in the bundle's Info.plist. This is a real
  packaging task for the desktop target, distinct from the browser permission
  prompt.

## 6. Consent / privacy primitives available today

- The adapters already have a clean per-match lifecycle with typed events
  (`P2PAdapterEvent`, `p2p-adapter.ts:46-86`) and explicit teardown
  (`dispose()` / `terminateGame()`, `p2p-adapter.ts:1144`, `:1183`). A/V enable /
  disable / mid-match kill-switch maps naturally onto this event + lifecycle model
  without inventing a new one.
- There is no existing user-facing consent surface for media (none is needed today)
  — so the consent UX in PLAN §Consent is greenfield and can be designed
  conservatively from the start (default-off, explicit affirmative action).

## 7. Existing audio module convention (light-touch note)

**Finding: `client/src/audio/` exists for game sound/music and is an unrelated
concern. A/V should get its own module.**

- `client/src/audio/` contains `AudioManager.ts`, `themeRegistry.ts`,
  `planeswalkerTheme.ts`, `audioCache.ts`, `useAudioContext.ts`, `types.ts` — this
  is Web Audio API playback of sound effects / music themes (synthesized/sample
  output to speakers). It has **no microphone, camera, or WebRTC involvement.**
- The only thing A/V shares with it is "the word audio." Mixing mic/camera capture
  into `client/src/audio/` would conflate two unrelated subsystems. PLAN scaffolds a
  **separate** module (`client/src/media/`) following the existing
  one-directory-per-concern convention (`network/`, `adapter/`, `audio/`).
