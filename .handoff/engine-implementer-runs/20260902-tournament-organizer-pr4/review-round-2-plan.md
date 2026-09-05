# Implementation Plan — matthewevans review round 2: credential exposure, frontend policy duplication, input parsing, locale formatting, stale-continuation race

**Run:** `20260902-tournament-organizer-pr4` · **PR:** phase-rs/phase#8325 (PR 4/4 frontend rollout)
**Driver:** `matthewevans` CHANGES_REQUESTED — 3 blockers ([HIGH] ×2, [MED] ×1), 1 non-blocking [LOW], plus 1 CodeRabbit actionable finding.
**Mode:** engine-planner, ordinary mode. Produces the full plan; the orchestrator owns the phase-fit gate and the charter loop.
**Worktree:** `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend` (branch `feat/tournament-organizer-pr4-frontend`), HEAD `5027f1bcd0790a0035326d13cdef8f472fe9f09e` — **verified**, this worktree's HEAD *is* the commit the review pinned.

**Predecessor:** `rpc-correlation-plan.md` (revision 5, ACCEPTED, landed as `59baf44b2`/`c35068e02`/`5027f1bcd`). Its conventions are load-bearing here and are followed rather than re-derived: additive-optional serde fields in both directions, `LOBBY_PROTOCOL_VERSION` bump discipline, **named frozen capability floors** (never the current version), cross-language version pinning through `scripts/check-protocol-version.mjs`, doc-comment cross-reference discipline, and paired positive reach-guards on every negative assertion.

---

## 0. Premise verification (Step 0 gate)

The Step 0 gate is written for card Oracle text. **No card is involved** — this is WebSocket protocol, credential storage, and React state. The gate is discharged against the equivalent authority: **every line-range citation in the review was read at source in this worktree before any design work**, per this engagement's standing norm of independent verification.

| # | Reviewer's claim | Verified? | Evidence read at source |
|---|---|---|---|
| 1 | `multiplayerStore.ts:973-977` defines both bearer authorities | **Yes** | `TournamentCredential` — `organizerToken?`, `playerToken?`, `playerKey?`, `updatedAt` |
| 2 | `:2340-2344`, `:2364-2368` retain them | **Yes** | `createTournament` → `rememberTournamentCredential(…, { organizerToken })`; `joinTournament` → `{ playerToken, playerKey }` |
| 3 | `:2445-2451` persists them | **Yes** | `partialize` returns `tournamentCredentials`; **`storage:` is not set, so zustand defaults to `localStorage`** |
| 4 | `tournamentPageState.ts:181-187` reimplements report legality | **Yes** | `isReportable` — arm-selective walk over `PairingOutcome` |
| 5 | `:432-434` reimplements the arity default | **Yes** | `defaultScoringForArity` → `{ win_points: 2 * arity - 1, draw_points: 1, loss_points: 0 }` |
| 6 | `:585-592` reimplements post-drop eligibility | **Yes** | `isActiveEntrant` |
| 7 | `TournamentPage.tsx:137-143`, `:478-513` consume the duplicated logic | **Yes** | `canPlayerAct`, `mine`, the `canPlayerAct &&` drop block, `onReport={canPlayerAct ? … : undefined}` |
| 8 | `CreateTournamentForm.tsx:47-60` consumes the duplicated default | **Yes** | `useState(() => defaultScoringForArity(initialArity))`, `changeArity` |
| 9 | Broker authority at `tournament.rs:217-226` (`default_for_arity`) and `:1721-1757` (`report_result`) | **Yes** | `2 * n - 1` in `u16` with checked downcast; `Bye`/`Forfeit` arms return `Err` before `validate_match_result` |
| 10 | Broker authority at `broker.rs:1166-1182`, `:1352-1373` | **Yes** | `authorize_player` (token ∧ `!dropped`); `handle_report_match_result`'s seat conjunct |
| 11 | `CreateTournamentForm.tsx:22-24,76-83` uses `Number.parseInt` | **Yes** | `parsedOr` and the submit handler |
| 12 | `ReportResultDialog.tsx:237-246` uses `Number.parseInt` | **Yes** | at `:238` |
| 13 | `tournamentPageState.ts:285-289` uses `toFixed` | **Yes** | `formatTiebreakValue` |
| 14 | `TournamentStandingsTable.tsx:85` does not pass `i18n.language` | **Yes** | destructures `{ t }` only; never constructs `i18n` |
| 15 | CodeRabbit: `shownCode` cannot distinguish visit 1 of A from visit 2 of A | **Yes** | `useRef(code)` at `:109`, reassigned at `:183`, compared at `:160`, `:303`, `:340` — a **string** comparison, carrying no visit identity |

**All fifteen citations are accurate.** Two premise *corrections* are recorded below (§0.1, §0.2); neither contradicts the reviewer, both extend the finding.

### 0.1 Correction — the policy duplication is not merely a future hazard; one instance is already live

The reviewer's rationale is *"a later protocol change can make the UI claim legality the broker denies."* Measured against source, **the UI already claims legality the broker already denies**, on today's code, for all four gated actions.

`report_result` (`tournament.rs`) opens with `if meta.status.is_terminal()` **before** the outcome-arm match. `start_round`, `complete_tournament` and `drop_player` each open with the identical guard (`is_terminal()` returns `true` for `Completed | Abandoned`). **`isReportable` mirrors only the outcome-arm conjunct and drops the status conjunct entirely**, and no gate anywhere on `TournamentPage.tsx` consults `view.summary.status`:

- `roles.has("organizer")` renders **Start Round** and **End Tournament** with no status test.
- `canPlayerAct = view !== null && roles.has("player") && isActiveEntrant(...)` — no status test; a non-dropped entrant of a `Completed` event satisfies it.
- `isReportable` returns `true` for `Reported(_)` and `null` outcomes regardless of status.

So on a `Completed` or `Abandoned` tournament every control still renders and **every dispatch is refused by the broker every time**. This is not a hypothetical drift introduced by a later protocol change; it is the same defect class, present now, and it exists precisely *because* the mirror was hand-copied conjunct-by-conjunct and one conjunct was missed. It is also the discriminating regression this plan's U1 is measured by (V4/V5), and it fails against today's code.

`isReportable`'s own doc comment asserts it "mirrors the broker's own `TournamentStatus::is_terminal()` guard, called earlier in this same function (`:1730`)". **It does not.** It *names* the guard while implementing only the arm match. A comment claiming a conjunct the code does not have is worse than a missing comment, and the fix removes both.

### 0.2 Correction — the three sub-findings of blocker 2 have three *different* correct placements

The reviewer groups three duplications under one blocker. They are not one repair, and treating them as one produces a wrong design. Measured:

| Sub-finding | Is the decision viewer-dependent? | Correct carrier |
|---|---|---|
| Which outcomes may be reported | **No** — `report_result`'s non-authorization gate reads only `meta.status` and `pairing.outcome` | Additive field on `PairingView` (a broadcast-safe, viewer-independent fact) |
| Whether a credential holder is still an eligible actor | **Partly** — `authorize_player` is `token ∧ !dropped`; `dropped` is already on the wire (`PlayerSummary.dropped`), token possession is irreducibly client-local | The *tournament-level* conjunct moves to the wire; the credential conjunct stays client-side **by necessity** (§D3) |
| Arity-derived default scoring | **No**, and it is needed *before a tournament exists* | Wire-optional `scoring`, broker fills the default (§D5) |

**This distinction is forced by the transport, not chosen.** `TournamentView` reaches clients through `Outbound::ToSubscribers` — *one* payload fanned to *every* subscriber — and also through `handle_get_tournament`'s `ToSelf`, in the identical shape. It therefore **cannot carry per-viewer data at all**. This is the same constraint the predecessor plan's D2 established when it rejected putting `request_id` on `TournamentUpdate`, and the same reasoning applies unchanged. Any design that answers "may *I* report this" on `TournamentView` is broadcasting one viewer's answer to everyone.

### 0.3 Correction — HttpOnly cookies are structurally infeasible on this transport

Verified against source (§D1). The reviewer's own suggested fix offers two alternatives — *"a server-managed HttpOnly session **or** short-lived, scoped, revocable credentials"*. The first is not achievable here; the second is, and is what this plan builds. The underlying security property he names is preserved.

---

## 1. Analogous trace (Step 2 hard gate)

**Traced feature: `total_rounds`, the one `CreateTournament` field that is already wire-optional with the broker owning its default.** It is the exact shape U2 needs, in the same wire variant and the same form component.

Full trace path, every layer read:

1. `crates/lobby-broker/src/protocol.rs` — `LobbyClientMessage::CreateTournament { …, #[serde(default)] total_rounds: Option<u32> }`, doc comment *"Organizer override for the scheduled round count. `None` uses the bracket- and arity-selected default."*
2. `crates/lobby-broker/src/tournament.rs` — `default_total_rounds` / `TournamentMeta::total_rounds()`, documented as *"the single authority that resolves the organizer override, the latched default, and the live default in that order."*
3. `crates/lobby-broker/src/protocol.rs` — `TournamentSummary.total_rounds: u32`, **resolved server-side and sent back concrete**, doc-linked to that single authority.
4. `client/src/services/tournamentClient.ts` — `CreateTournamentRequest.totalRounds: number | null`.
5. `client/src/components/tournament/CreateTournamentForm.tsx` — `roundsInput: string`, `""` means Automatic, `placeholder={t("create.totalRoundsAuto")}`, submitted as `null`.
6. `client/src/i18n/locales/{en,de,es,fr,it,pl,pt}/tournament.json` — `create.totalRoundsAuto`.

**Three properties carry over verbatim to `scoring`, and each answers a design question below:** (a) the wire field is `Option`, absence meaning "broker decides"; (b) the *resolved* value comes back on the summary so the client never re-derives it; (c) the form expresses absence as an empty control with an "Automatic" placeholder, not as a client-computed prefill.

**Second trace, for U3/U4 (credential lifetime):** `client/src/services/multiplayerSession.ts` — a standalone service module (deliberately **not** a zustand-persisted slice) holding the full-server session token with `WS_SESSION_TTL_MS = 2h`, an `isWsSessionValid` predicate consulted on every load, and `loadWsSession`/`saveWsSession`/`clearWsSession`. This is the in-repo shape for "a bearer credential the client must hold, bounded in time."

**Third trace, for U6 (locale formatting):** `client/src/utils/byteSize.ts` — `export function formatByteSize(bytes: number, locale: string): string` using `new Intl.NumberFormat(locale, {...})`, called as `formatByteSize(x, i18n.language)` from `PackStatus.tsx`/`VisualPackManager.tsx`. A **pure formatter taking locale as a parameter** — which is the only shape compatible with `tournamentPageState.ts`'s mandated purity (§D8).

---

## 2. Architectural decisions

### D1 — Blocker 1, part 1: HttpOnly is infeasible; the property is preserved by the reviewer's own second alternative

**Decision: do not attempt a cookie session. Implement short-lived, rotating, revocable credentials, and stop persisting them durably.**

This is argued from source, not assumed, because the brief explicitly required checking feasibility before adopting the suggested mechanism.

**Four independent blockers, each sufficient alone:**

1. **The broker checks a token from the message body, never the connection.** `protocol.rs` states it as the model's whole point: *"Authority on every gated variant below is the TOKEN carried in the payload, compared against the stored `organizer_token`/`player_token` — **never the socket's `ConnState`**."* An HttpOnly cookie is by definition unreadable from JS, so the client **cannot place it into the field the broker actually checks**.
2. **The browser `WebSocket` constructor cannot set headers**, so a cookie could only ever ride the upgrade request — i.e. authority would have to bind to the *connection*.
3. **Binding authority to the connection is the bug this feature exists to fix.** `docs/proposals/tournament-organizer/PLAN.md` §3: the token model exists so that *"closing/reopening the tournament page's socket does **not** unregister the tournament or drop a player's standing — exactly the bug class #4615 shipped."* Adopting a cookie session re-introduces #4615.
4. **The client is cross-origin to the broker, and the broker address is user-editable.** Site `phase-rs.dev` → broker `wss://lobby.phase-rs.dev/ws`; `serverAddress` is a persisted user-editable field and self-hosted brokers are supported. Any cookie is third-party, blocked by default in modern browsers, and undefined for self-hosted addresses.

Additionally, `Outbound` (`broker.rs`) has exactly five variants (`ToSelf`, `ToSubscribers`, `AddSubscriber`, `RemoveSubscriber`, `SendPlayerCountToSelf`) — **the transport-free core cannot express an HTTP response header at all**, and `crates/lobby-broker/` is documented as having "no tokio, no axum". A cookie would have to be minted in the shells, diverging native and edge behavior in exactly the layer the design keeps identical.

**The honest statement of what is achievable, which the plan must not overstate.** On this transport, mutation authority is *necessarily JS-readable*: the client must read the token to put it in the frame. Full non-extractability is unreachable without connection-bound authority. What is achievable — and what the reviewer's second alternative asks for — is to **bound the blast radius in time, scope and revocability**, so that a compromised dependency obtains a credential valid for hours in one tab rather than one valid for up to 37 days across every future visit to the origin. §D2's measurement is what makes that contrast concrete.

### D2 — Blocker 1, part 2: what is actually wrong today, measured

Three properties compound, and the fix addresses all three:

1. **Unbounded lifetime.** Tokens are 128 bits of CSPRNG hex (`generate_player_token`, `crates/server-core/src/session.rs`; byte-identical `WorkerEnv` copy in `lobby-worker/broker-wasm/src/lib.rs`) with **no expiry, no rotation and no revocation anywhere**. A token dies only when its whole record is reaped: `IN_PROGRESS_ABANDON_SECS = 7 days` idle plus `TERMINAL_RETENTION_SECS = 30 days`.
2. **Durable, origin-wide client storage.** `partialize` writes the map to `localStorage` under `phase-multiplayer`, surviving browser restarts indefinitely, capped only by `MAX_TOURNAMENT_CREDENTIALS = 32` and cleared only on `TournamentRemoved` (which fires only while subscribed).
3. **Non-constant-time comparison.** `authorize_organizer` uses `meta.organizer_token != presented`; `authorize_player` uses `p.player_token == presented`. The same repo deliberately uses a constant-time `tokens_match` for the admin bearer (`phase-server/src/main.rs`), so the primitive exists and the asymmetry is unjustified.

**The durability requirement the persistence was built to satisfy was never specified.** The doc comment justifies it as *"losing it is unrecoverable, which is why this map is persisted rather than held in memory."* But the design docs specify durability **against socket bounces only** — verbatim, PLAN.md: *"closing and reopening a connection must not cost an organizer their event."* The strings "page reload", "refresh", "browser restart" and "tab close" appear **nowhere** in CONTEXT.md, RESEARCH.md or PLAN.md, and client-side persistence is named nowhere in any of the three. `localStorage` was an implementation-time choice satisfying an unspecified requirement, never weighed against a threat model (the docs contain no security section at all). It is therefore available to revise on its own merits rather than being a design commitment.

**Two in-repo precedents make the direction unambiguous**, and one of them is on the server side of this very feature:
- `broker.rs` removed the token from `joined_tournaments` because retaining it *"turned a non-authority convenience record into **monotonic secret retention in storage that outlives the socket**."* `phase-server/src/main.rs`: *"The core deliberately does not retain the `player_token` here, precisely because this per-socket identity is where such a secret would be held long past the operation that minted it."* **The engine went out of its way to keep these tokens out of long-lived server storage, and the client then wrote them to `localStorage`.**
- Client-side: `p2pSession.ts` — pre-game tokens *"are **intentionally NOT persisted**"*; `RememberedHostConfig` *"deliberately excludes per-match / sensitive fields (room name, password)"*; guest join passwords go to **`sessionStorage`, not `localStorage`**, so the secret never outlives the tab. Tournament tokens are today the **only** client-held secret with neither a TTL nor a tab-scoped backing store (session token: 2h TTL; P2P token: 4h TTL; password: sessionStorage; reservation token: never persisted).

**Decision, three parts:**

**(a) Server — bounded, rotating, revocable.** `TournamentPlayer` and `TournamentMeta` carry their token inside a typed credential rather than a bare `String`:

```rust
/// One tournament bearer credential: the secret, and the instant it stops
/// being accepted.
///
/// A newtype-with-expiry rather than a bare `String` so that "a token" and
/// "a token that is still valid" cannot be confused at a call site — the
/// same reason `TournamentRequestId` is a newtype rather than a second bare
/// integer beside `PairingId`. Expiry is checked against the injected
/// `BrokerEnv` clock, never `SystemTime`, so the identical logic runs in the
/// native shell and the Durable Object.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TournamentCredential {
    secret: String,
    expires_at_ms: u64,
}
```

`expires_at_ms` follows the established in-repo expiry idiom — `lobby.rs`'s seat reservation already stores `expires_at_ms: Some(now + PUBLIC_SEAT_RESERVATION_MS)`. The field is **private with an `accepts(&self, presented: &str, now_ms: u64) -> bool` accessor performing a constant-time compare**, so no call site can spell a plaintext `==` against it and no call site can forget the expiry conjunct — the same "single authority, enforced by the type system" device the predecessor plan's D5 used for `settle_gated`.

**(b) Server — renewal by rotation.** A new ungated-by-role but token-gated client message `RenewTournamentCredential { code, token, role }` answers `ToSelf(TournamentCredentialRenewed { code, role, token, expires_at_ms })` with a **freshly minted secret**, invalidating the presented one. Rotation rather than extension is deliberate: it bounds a stolen token even against a thief who keeps renewing, because the legitimate holder's next renewal locks the thief out (and vice versa — a detectable, reportable failure rather than silent indefinite shared access).

`role` is the existing `TournamentRole` axis rather than two sibling messages (`RenewOrganizerCredential`/`RenewPlayerCredential`), per **parameterize, don't proliferate**; the client already has this exact union.

**(c) Client — tab-scoped, TTL-checked, renewed on connect.** `tournamentCredentials` **leaves `partialize`**. A new `client/src/services/tournamentCredentialStore.ts` models itself directly on `multiplayerSession.ts`: `sessionStorage`, an explicit expiry carried from the server's `expires_at_ms`, a validity predicate consulted on every read, and `load`/`save`/`clear`. The store renews on socket (re)connect whenever a held credential is inside its renewal window.

**What each part buys, stated without overclaim.** (c) alone removes *durability* (browser restart, and cross-tab reach) but not *readability* — `sessionStorage` is same-origin-script-readable exactly as `localStorage` is. (a)+(b) are what bound the value of a read credential in time and make it revocable. **Neither half is sufficient alone**, which is why they are one unit boundary in the charter (U3→U4 is a dependency edge, not two independent fixes).

**TTL value.** `TOURNAMENT_CREDENTIAL_TTL_MS` is set at **12 hours**, chosen against the two constraints that actually bound it rather than picked round: it must comfortably exceed a real event (a Swiss event of 8-9 rounds runs well under a day) and it must sit far below `IN_PROGRESS_ABANDON_SECS = 7 days`, so a credential expires long before the record it authorizes is reaped. It is longer than the session token's 2h because an organizer's authority spans an entire event rather than one game, and renewal-on-connect makes the practical ceiling the event's duration rather than the TTL.

### D3 — Blocker 2, part 1: what moves to the wire, and the one conjunct that provably cannot

**Decision: carry the broker's *non-authorization* gate for each gated action on the wire, per its natural scope. Leave exactly one conjunct client-side, and say why in the code.**

The broker's report gate is a conjunction of four things. Three are broadcast-safe; one is not:

| Conjunct | Broker site | Viewer-dependent? | Where it goes |
|---|---|---|---|
| `!status.is_terminal()` | `report_result` | No | wire |
| outcome arm ∉ {`Bye`, `Forfeit`} | `report_result` | No | wire |
| reporter seated in this pairing | `handle_report_match_result` | No — `pairing.players` is already on the wire | already there; read, not re-derived |
| token resolves, and `!dropped` | `authorize_player` | **Yes** | **must stay client-side** |

The last row is not a design preference. `TournamentView` is `Outbound::ToSubscribers` — one payload fanned to every subscriber, and emitted in the *identical* shape from `handle_get_tournament`'s `ToSelf`. A per-viewer answer on it would be broadcast to everyone. Its two inputs are, respectively, a map the client itself owns (`tournamentCredentials` — which the predecessor plan's D8.1 already established as *the* store-owned fact, distinguishing `not_authorized` from every wire-derived reason) and `PlayerSummary.dropped`, **which is already a server-provided field**.

So after this change the client composes *server-provided facts with its own credential map* and re-derives **no rule**. That is precisely the layering CLAUDE.md licenses — *"Formatting for display … is acceptable; calculating, filtering, or inferring game state is not"* — and precisely what the reviewer asked for: *"carry the relevant affordance/default data through the server protocol and render it."*

**The two new wire carriers, and why two rather than one.**

```rust
/// Whether the broker would accept a `ReportMatchResult` for this pairing
/// from a correctly credentialed, seated, non-dropped entrant — i.e. every
/// conjunct of `TournamentManager::report_result`'s gate that does not
/// depend on WHO is asking.
///
/// Viewer-independent by construction, which is what makes it safe on a
/// frame that is fanned to every subscriber. The authorization conjuncts
/// (`Broker::authorize_player`'s token and `dropped` checks, and
/// `handle_report_match_result`'s seat check) are deliberately NOT folded in
/// here and cannot be: this frame has one payload for all viewers.
///
/// Carries the REASON, not a bool, so a client can say why a control is
/// absent and so a new refusal arm is a compile error at every consumer
/// rather than a silently-flipped boolean.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReportGate {
    /// `report_result` would proceed to `validate_match_result`.
    Open,
    /// The tournament is no longer running (`TournamentStatus::is_terminal`).
    TournamentNotRunning,
    /// Server-assigned bye — nothing was played.
    Bye,
    /// Server-assigned forfeit, from `drop_player`'s auto-settlement.
    Forfeit,
}
```

added to `PairingView` as `pub report_gate: ReportGate`, and:

```rust
/// Which tournament-scoped gated actions the broker would currently admit
/// from a correctly credentialed actor, independent of who is asking.
///
/// A SET over one typed axis rather than three sibling `can_*: bool` fields
/// — that shape would be CLAUDE.md's sibling-cluster smell, and a fourth
/// action later would make it four. Reporting is deliberately absent: its
/// gate is pairing-scoped, and lives on `PairingView::report_gate`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum TournamentAction { StartRound, EndTournament, Drop }
```

added to `TournamentSummary` as `pub open_actions: BTreeSet<TournamentAction>`.

**Why the split across two carriers is a categorical boundary and not a smell.** The two differ in *scope*, which is a real property: `report_gate` answers a question about **one pairing** and must vary per row; `open_actions` answers a question about **the tournament** and is constant across rows. Folding reporting into `open_actions` would force one tournament-wide answer for a per-pairing question; folding `open_actions` onto every `PairingView` would replicate one fact N times and leave it undefined during `Registration`, when no pairings exist yet (and `StartRound` is exactly the action available then). `TournamentSummary` is also the right home for the second because it already carries `status`, `current_round` and `total_rounds` — the very inputs those gates read — and because the **tournament list** page can then gate its affordances off the same field without fetching a full view.

**`open_actions` is computed by one server-side function, never by three.** A single `TournamentMeta::open_actions(&self) -> BTreeSet<TournamentAction>` is the sole producer, and each of the three handler guards is refactored to consult it, so the wire value and the handler's refusal cannot disagree. Without that, this change would install a *second* server-side authority beside the handlers — a strictly worse outcome than the client-side duplication it replaces.

**Rejected alternative — a per-viewer affordance frame.** A new `ToSelf(TournamentAffordances { … })` computed for the asking connection would fold the credential conjunct in too. Rejected: the broker cannot know which credentials a browser holds (they are client-held bearer tokens, presented per-action and never registered against a connection — see D1's quote), so it could only answer for a token the client presents, which means a round trip per render. It would also re-introduce socket-bound identity, the #4615 bug class.

### D4 — Blocker 2, part 2: `LOBBY_PROTOCOL_VERSION` 5 → 6, and the additivity direction that matters

`ReportGate` and `TournamentAction` are new types and `PairingView`/`TournamentSummary` gain **required** fields. Per that constant's own four-trigger policy this is a mandatory bump: **5 → 6**, with a new changelog entry.

`PROTOCOL_VERSION` (55) does **not** move, `MIN_SUPPORTED_LOBBY_PROTOCOL` (2) does **not** move, and `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` (5) does **not** move — the predecessor plan froze the last of these deliberately and `scripts/check-protocol-version.mjs` already pins it with an error message saying why. **Bumping it alongside the version bump is the single most likely executor error in this plan** and is called out in §3 as a do-not.

**Direction analysis.** `PairingView`/`TournamentSummary` are **server→client**. The consumer is TypeScript, which ignores unknown fields, so a *new* broker's frame reaching an *old* client is harmless. `PairingView` and `TournamentSummary` are **re-exported**, not mirrored, into `crates/server-core/src/protocol.rs` (`pub use lobby_broker::protocol::{PairingView, PlayerSummary, TournamentRequestId, TournamentSummary, TournamentView}`), so there is exactly one definition and no parallel copy to drift. The only Rust deserializers are the crate's own tests and `broker-wasm`, both of which move in lockstep.

The direction that **does** bite is U2's, and it is measured rather than assumed — see D5.

### D5 — Blocker 2, part 3: `scoring` becomes wire-optional; `defaultScoringForArity` is deleted

**Decision: `CreateTournament.scoring` becomes `Option<ScoringPolicy>`, `None` meaning "broker applies `ScoringPolicy::default_for_arity`". `defaultScoringForArity` is deleted outright, not moved.**

This is the traced `total_rounds` shape (§1) applied to the sibling field in the same variant — extend, don't hack. The form's scoring inputs become empty-means-default with a `create.scoringAuto` placeholder, exactly as the rounds input already is.

**Probe P1 — the additivity direction, measured.** Relaxing a *required* field to optional is **not** symmetric with adding a new optional field, and the predecessor plan's P1 result does not transfer. A standalone `serde`/`serde_json` crate replicating protocol.rs's exact `#[serde(tag="type", content="data")]` shape (source retained at `<scratchpad>/scoringprobe/src/main.rs`; regenerate with `cargo run` there — it depends only on `serde`/`serde_json` and never touches the repo target dir):

| # | Case | Result |
|---|---|---|
| B1 | old frame (`scoring` present) → **new** enum | `Ok(Some(..))` |
| **B2** | **new frame (`scoring` omitted) → old enum** | **`Err("missing field \`scoring\`", line: 1, column: 74)`** |
| B3 | new frame (omitted) → new enum | `Ok(None)` |
| B4 | new frame (**present**) → old enum | `Ok` |
| B5 | `Some(..)` serialization vs today's required-field frame | **byte-identical** |
| B6 | reach-guard: `Option` field with **no** `#[serde(default)]`, frame omitting it | `Ok` |

**B2 is the decisive result and forces the capability gate.** A new client that omits `scoring` against a pre-bump broker gets a hard parse failure — which, at the edge, becomes `ParsedFrame::Malformed` → `reject_reply`'s bare `Error`, and `createTournamentOver` is one of the three *uncorrelated* helpers that still settles on a bare `Error`. So the organizer would see a raw serde message. **B2 also doubles as this probe's reach-guard**: it proves the deserializer genuinely fails on a missing required field, so B3's `Ok(None)` is attributable to the type change rather than to an insensitive instrument.

**B6 is a secondary honest finding that must not be misread:** serde treats `Option<T>` fields as implicitly defaulting to `None`, so `#[serde(default)]` is *redundant* on such a field. It is written anyway, because `total_rounds` and every other optional field in this enum carry it and consistency in a wire contract is worth more than terseness. The plan states this so a reviewer does not read the attribute as load-bearing when it is not.

**Decision: a second named frozen capability floor.**

```ts
/**
 * Lowest broker `LOBBY_PROTOCOL_VERSION` that accepts a `CreateTournament`
 * frame with `scoring` OMITTED, i.e. that owns the arity-derived default.
 *
 * A FLOOR frozen at the version that introduced broker-owned scoring, not a
 * moving target — the same kind of number as
 * {@link MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK} and for the same reason.
 * It must NOT be bumped when `LOBBY_PROTOCOL_VERSION` moves: a v7 broker
 * still accepts the omission, and raising this would silently push every
 * organizer back onto the explicit-entry path against servers that work
 * perfectly. Deliberately no ceiling.
 *
 * Unlike the ack floor, falling below this one is NOT a soft degrade: probe
 * B2 shows a pre-v6 broker answers an omitted `scoring` with a hard parse
 * error, so the client must send an explicit policy below this floor.
 */
export const MIN_LOBBY_PROTOCOL_FOR_DEFAULT_SCORING = 6;
```

pinned in `scripts/check-protocol-version.mjs` by the same bare-integer-literal regex device the four existing lobby pins use (so re-deriving it from another constant fails to match).

**Below the floor, the form requires explicit entry and computes no default.** The three scoring inputs render as required, submit is disabled until all three are filled, and a hint explains that this server needs an explicit scoring policy. **No client-side default constant survives anywhere** — that is the whole point of the blocker, and re-introducing one "just for old servers" would leave the duplicated rule in place under a different name. The cost is a small, honest UX degradation on pre-v6 self-hosted brokers (type three numbers), and it is the correct trade: degrade the legacy path, never duplicate the rule. Hosted deployments are largely protected by `deploy.yml`'s existing gate, which requires the Worker to be redeployed before the client deploy proceeds.

**The resolved policy comes back on the wire.** `TournamentSummary` gains `pub scoring: crate::tournament::ScoringPolicy` — the *resolved* value, mirroring how `total_rounds` is already resolved server-side and sent back concrete. Without it the organizer cannot see what their event actually scores, which would be a regression introduced by the fix itself.

### D6 — Blocker 3: `Number.parseInt` → `Number`, and `null` reserved for empty

**Decision, verbatim to the reviewer's ask:** use `Number(raw)`, reserve `null` for an explicitly empty rounds field, and add decimal/exponent regressions proving broker rejection.

`Number.parseInt("2.5", 10)` is `2` and `Number.parseInt("1e3", 10)` is `1` — both **silently well-formed**, so the broker's authoritative validator never sees the malformed value and the organizer gets a tournament they did not ask for. `Number("2.5")` is `2.5` and `Number("1e3")` is `1000`; both then reach the broker and are refused by `MatchArity::new` / `ScoringPolicy::new`, which is the correct authority. `Number("")` is `0`, which is why empty must be handled *before* the conversion rather than by a `Number.isNaN` test — the trap that makes this a real bug rather than a style nit.

```ts
/**
 * Parses a numeric field, keeping the previous value only when the field
 * cannot be read as a number at all.
 *
 * `Number`, never `Number.parseInt`: `parseInt("2.5")` is `2` and
 * `parseInt("1e3")` is `1`, so a malformed entry is silently rounded into a
 * well-formed one and the broker's authoritative validator never sees what
 * the organizer typed. `Number` preserves `2.5` and `1000` so
 * `MatchArity::new` / `ScoringPolicy::new` can refuse them.
 *
 * Still deliberately no clamping or range check here — those bounds are the
 * broker's, and a second copy would drift.
 */
function parsedOr(raw: string, fallback: number): number {
  if (raw.trim() === "") return fallback;   // `Number("")` is 0, not NaN
  const parsed = Number(raw);
  return Number.isNaN(parsed) ? fallback : parsed;
}
```

and the rounds field, where `null` is a *distinct meaning* rather than a parse failure:

```ts
// `null` is the "Automatic" affordance, reserved for an EXPLICITLY empty
// field — never for an unparseable one, which must reach the broker as the
// number it is so the broker can refuse it.
const trimmed = roundsInput.trim();
const totalRounds = trimmed === "" ? null : Number(trimmed);
```

`ReportResultDialog`'s game-wins input takes the same treatment. Its current `Number.isNaN(parsed) ? 0 : parsed` coerces an unparseable entry to `0` — a **valid tally value**, so a typo silently reports a real result. Empty becomes `undefined` (the field's own `Record<string, number | undefined>` already models absence) and the submit path's existing `?? 0` continues to own the default.

### D7 — CodeRabbit finding: a page-generation token, extending the `shownCode` mechanism rather than replacing it

**The existing mechanism is sound and its reasoning is preserved verbatim.** `shownCode` correctly scopes A→B, and its doc comment's four-writes census, its "assigned in the effect, immediately before the state resets" placement argument, and its "declining a stale write strands nothing" pairing with the effect's resets all remain true and must survive the edit. The gap is narrow and real: the guard compares a **string**, so it cannot distinguish visit 1 of A from visit 2 of A.

**Verified reachable.** On A→B→A the subscription effect re-runs for visit 2, resetting `view`/`removed`/`failure`/`reporting`/`offline`/`busy`, and reassigns `shownCode.current = "A"`. A continuation from visit 1 then settles with `shownCode.current === code` **true**, and writes:
- `run`: `setBusy(null)` — which is exactly the double-dispatch window that comment at `:296-302` was written to close, now reachable by a different route; and `setFailure(failureLabel(r))`, rendering visit 1's rejection on visit 2's page.
- `handleReport`: `setReporting(null)`, closing a dialog visit 2 may have opened and discarding the selection entered in it — the precise harm its own comment at `:334-339` describes.

**Decision: replace the string ref with a monotonic generation ref, captured per visit.**

```ts
/**
 * Which VISIT to a tournament page the caller belongs to.
 *
 * A monotonic counter, not the code string. `shownCode` alone scoped a
 * settling continuation correctly for a straightforward A → B navigation,
 * because the closed-over code no longer matched. It could not scope
 * A → B → A: on the return the ref holds `"A"` again, so a continuation
 * issued during the FIRST visit passes a string comparison and writes into
 * the SECOND visit's state — re-enabling a control the current visit is
 * holding disabled for its own in-flight action, rendering the old visit's
 * rejection, or closing a report dialog the viewer has since reopened.
 *
 * The generation is bumped by the subscription effect on every run, so each
 * visit — including a repeat visit to the same code — gets its own value.
 * Continuations capture it at DISPATCH time and compare it at settlement.
 * Comparing generations subsumes comparing codes (a `:code` change always
 * re-runs the effect and so always bumps), which is why this replaces the
 * code comparison rather than joining it: carrying both would imply the code
 * conjunct still decides something, and it does not.
 */
const pageGeneration = useRef(0);
```

The effect's assignment moves in place, keeping the placement argument the existing comment already makes (*"the ref moves first, so that an RPC settling in the window between this commit and this effect is covered by the reset that follows rather than by the guard"*) — that reasoning is generation-agnostic and stays exactly as written:

```ts
pageGeneration.current += 1;
setView(null);
// … the five existing resets, unchanged
```

Each continuation captures at dispatch and compares at settlement:

```ts
const run = useCallback(async (kind, action) => {
  const generation = pageGeneration.current;   // captured at DISPATCH
  setBusy(kind);
  setFailure(null);
  const r = await action();
  if (pageGeneration.current === generation) {
    setBusy(null);
    if (!r.ok) setFailure(failureLabel(r));
  }
  return r.ok;
}, []);
```

Note `run`'s dependency array becomes `[]` — `code` was a dependency only for the guard. `seed` keeps `[getTournament, code]` (it still *sends* `code`) and captures the generation the same way. `handleReport` likewise.

**`onTournamentUpdate`/`onTournamentRemoved` keep their `broadcastCode === code` conjunct unchanged.** Those are subscription handlers, not promise continuations: they are detached by the effect's cleanup on navigation, so they cannot be stale in the visit sense, and the code conjunct there discriminates *which tournament a broadcast is about* — a genuinely different question. The doc comment must not blur the two.

### D8 — Non-blocking [LOW]: locale-aware formatting, with purity preserved

**Decision: `formatTiebreakValue(cell: TiebreakCell, locale: string): string`, using `Intl.NumberFormat`, with the caller passing `i18n.language`.**

The locale is a **parameter**, not a hook call, and this is forced rather than stylistic: `tournamentPageState.ts`'s module header mandates *"no React, no store runtime, no I/O, no clock"* and *"**Every import here is `import type`, by design**"*, pinned by a static source assertion in its own test. Calling `useTranslation` there would violate all of that. `formatByteSize(bytes, locale)` (§1, third trace) is the established in-repo shape for exactly this.

```ts
if (cell.format === "percent") {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(cell.value);
}
if (cell.format === "points") {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(cell.value);
}
```

**Two traps this must not fall into, both called out for the executor.** (1) `style: "percent"` multiplies by 100 itself — the existing `* 100` **must be deleted**, or every percentage renders 100× too large. This is the single highest-risk line in U6 and V15 exists to catch it. (2) `minimumFractionDigits` must be set alongside `maximumFractionDigits`; `toFixed(1)`/`toFixed(2)` pad trailing zeros and `Intl.NumberFormat` does not by default, so omitting the minimum silently changes `50.0%` to `50%` and `2.00` to `2`. The existing doc comment's precision rationale (*"One decimal place … is a display decision, not a rules claim"*) stays accurate and is preserved.

`TournamentStandingsTable.tsx` changes `const { t } = useTranslation(...)` to `const { t, i18n } = useTranslation(...)` and passes `i18n.language`.

### D9 — CR annotations: N/A, checked explicitly

Checked per the mandatory gate rather than waved off. This change spans a WebSocket lobby broker, a Cloudflare Durable Object shell, credential storage and React state. It implements **no** MTG game rule: no turn structure, priority, stack, state-based actions, zones, or object properties. `crates/engine/` is not modified by any unit.

The one CR-adjacent string in scope is `RememberedHostConfig.loopDetection`'s existing `// CR 732.2a` annotation, which this plan does not touch.

`docs/MagicCompRules.txt` is **absent from this worktree** (gitignored; `./scripts/fetch-comp-rules.sh` never run here), which independently forbids writing any CR annotation, since CLAUDE.md requires every CR number be grep-verified against that file first. **Zero CR annotations may be added.** This matches every prior phase of this engagement.

### D10 — `add-engine-variant` gate: does not apply mechanically; principle applied by hand

`crates/engine-inventory-gen/src/main.rs` declares `const TARGET_DIRS: &[&str] = &["crates/engine/src"]`. Every enum this plan adds (`ReportGate`, `TournamentAction`) lives in `crates/lobby-broker/src/protocol.rs` or `tournament.rs` — **structurally outside** what `cargo engine-inventory` walks — and the enums the skill gates (`QuantityRef`, `Effect`, `TargetFilter`, `Keyword`, …) are engine AST types. `data/engine-inventory.json` cannot answer an existence or sibling-cluster question about a wire enum, and running it would be theater. This matches the predecessor plan's D11 finding, re-verified.

**The principle was applied by hand and is the substance of D3:** three sibling `can_start: bool` / `can_end: bool` / `can_drop: bool` fields were identified as the textbook sibling-cluster smell and rejected in favour of one `BTreeSet<TournamentAction>` over a typed axis; and `ReportGate` is a reason-carrying enum rather than a bool specifically so a new refusal arm is a compile error at every consumer. Existence check done by exhaustive read of both protocol enums — no `ReportGate`, `TournamentAction`, `open_actions` or `report_gate` exists today.

---

## 3. Charter — seven units, and why this cannot be one phase

Written as a charter because the Sizing section's own numbers force it (§5). The orchestrator runs the phase-fit gate; this section supplies its input.

| Unit | Goal | Depends on |
|---|---|---|
| **U1** | `ReportGate` + `TournamentAction`/`open_actions` on the wire; `TournamentMeta::open_actions` as sole server authority; the three handler guards refactored to consult it | — |
| **U2** | `CreateTournament.scoring` wire-optional; resolved `scoring` on `TournamentSummary`; `MIN_LOBBY_PROTOCOL_FOR_DEFAULT_SCORING`; version bump 5→6 and all pins | shares the version bump with U1 |
| **U3** | `TournamentCredential` with expiry + constant-time `accepts`; `RenewTournamentCredential`/`TournamentCredentialRenewed` | shares the version bump |
| **U4** | Client credential store: out of `partialize`, into a TTL'd `sessionStorage` service module; renew-on-connect | **U3** |
| **U5** | Client consumption of U1/U2: delete `isReportable`/`defaultScoringForArity`, rewrite the `canPlayerAct` conjunction, form rework, locale keys | **U1, U2** |
| **U6** | `Number()` parsing + `null`-for-empty in both components | — |
| **U7** | `pageGeneration` ref; locale-aware `formatTiebreakValue` | — |

**Ordering.** U1+U2+U3 land together as the Rust wire contract (one `LOBBY_PROTOCOL_VERSION` bump serves all three — three separate bumps would be three protocol versions for one release and would break `check-protocol-version.mjs`'s single-value pin). U4 and U5 then land against it. U6 and U7 are independent of everything and can land first or last.

**Seam note.** `crates/lobby-broker/src/protocol.rs`, `broker.rs` and `client/src/adapter/types.ts` are touched by several units and are the collision points; units sharing them must not execute concurrently.

**Deferral list.** If U1-U3 land as one phase, that phase defers: all client consumption (U4, U5), the `sessionStorage` migration, the form rework, the seven locale keys, and verification rows V5-V12 and V16-V22 — each attributed to the phase that lands it. That phase's interim verification is structural: green tree built `--all-targets`, existing Rust and TypeScript suites passing with assertions unmoved, plus its own contract tests V1-V4, V13-V15 and V23.

**A do-not, repeated because it is the likeliest executor error:** the version bump moves `LOBBY_PROTOCOL_VERSION` 5→6 and `EXPECTED_LOBBY_PROTOCOL_VERSION` 5→6 **only**. `MIN_SUPPORTED_LOBBY_PROTOCOL` (2), `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` (5) and `PROTOCOL_VERSION` (55) **do not move**. The ack floor is frozen at 5 forever by its own doc comment and by an error message in `check-protocol-version.mjs`.

---

## 4. Implementation steps

### 4.1 `crates/lobby-broker/src/tournament.rs` (U1, U2, U3)
- Add `TournamentCredential { secret, expires_at_ms }` with a private secret, `fn accepts(&self, presented: &str, now_ms: u64) -> bool` doing a **constant-time** compare plus the expiry conjunct, and `fn mint(env, now_ms) -> Self`. Add `TOURNAMENT_CREDENTIAL_TTL_MS` beside the existing retention constants, doc-commented against `IN_PROGRESS_ABANDON_SECS`.
- Change `TournamentMeta::organizer_token` and `TournamentPlayer::player_token` to that type. Update the two mint sites (`env.new_token()` call sites in `create_tournament` and the join path).
- Add `TournamentAction` and `TournamentMeta::open_actions(&self) -> BTreeSet<TournamentAction>` as the sole authority; refactor the `is_terminal()` guards in `start_round`, `complete_tournament` and `drop_player` to consult it, so wire value and refusal cannot disagree.
- Add `TournamentMeta::report_gate(&self, pairing) -> ReportGate`; refactor `report_result`'s status check and outcome-arm match to consult it, same reason.
- Add credential rotation: `fn renew_credential(&mut self, code, role, presented, env) -> Result<(String, u64), String>`.

### 4.2 `crates/lobby-broker/src/protocol.rs` (U1, U2, U3)
- `LOBBY_PROTOCOL_VERSION` 5 → **6**, plus changelog entry 6 above it naming all three additions.
- `ReportGate` enum; `PairingView.report_gate`; `TournamentSummary.open_actions` and `TournamentSummary.scoring`; extend both `From` impls.
- `CreateTournament.scoring` → `#[serde(default)] Option<ScoringPolicy>`, doc comment written in `total_rounds`'s voice.
- New `LobbyClientMessage::RenewTournamentCredential { code, role, token }` and `LobbyServerMessage::TournamentCredentialRenewed { code, role, token, expires_at_ms }`.
- **Update `LobbyClientMessage::tournament_request_id`'s exhaustive match** for the new variant — the predecessor plan built that accessor precisely so a new variant is visible here. `RenewTournamentCredential` returns `None` (it is not one of the four correlated gated actions).
- Update `lobby_protocol_version_is_independent_of_the_full_game_one`'s first `assert_eq!` to 6; leave its `MIN_SUPPORTED_LOBBY_PROTOCOL` assertion, `assert_ne!` and `const` floor block untouched. `tournament_lobby_version_follows_the_format_config_bump`'s premise (`PRE_TOURNAMENT_LOBBY_VERSION + 1`) no longer holds at 6 — it must be re-expressed or retired, not silently edited to pass.

### 4.3 `crates/lobby-broker/src/broker.rs` (U1, U3)
- `authorize_organizer`/`authorize_player` call `credential.accepts(presented, env.now_ms())`; the plaintext `==`/`!=` comparisons are deleted. Both gain an expiry-refusal `Err` arm with its own message, distinct from the invalid-token one (the doc comment's "three distinct `Err` shapes" rationale extends to four).
- New `handle_renew_tournament_credential`, dispatched in `Broker::handle`.
- Handler guards refactored per 4.1.

### 4.4 `crates/lobby-broker/src/validation.rs`, `crates/server-core/src/client_message_wire_guard.rs`, `crates/server-core/src/protocol.rs`, `crates/phase-server/src/main.rs`, `lobby-worker/broker-wasm/src/lib.rs` (U1-U3)
Absorb the new variants and fields. `ReportGate`/`TournamentAction` join the existing `pub use` re-export list in `server-core/src/protocol.rs`. The two `ScoringPolicy::default()` fixture literals in `client_message_wire_guard.rs` become `Some(ScoringPolicy::default())`.

**Enumerate the full site list with the compiler, not by reading**, using the predecessor plan's §3A.9 recipe: add the fields, run `cargo check --workspace --all-targets` in an **isolated `CARGO_TARGET_DIR`** (never the shared `C:/git/phase/target`, and never while Tilt owns it), absorb library-level errors first, re-run, and confirm `git status --porcelain` is clean after reverting probe edits.

### 4.5 Version pins (U2)
`scripts/check-protocol-version.mjs`: `EXPECTED_LOBBY_PROTOCOL_VERSION` 5 → 6; add `EXPECTED_MIN_LOBBY_PROTOCOL_FOR_DEFAULT_SCORING = 6` with a bare-integer-literal regex and a "why it is frozen" error message. `client/src/adapter/ws-adapter.ts`: `LOBBY_PROTOCOL_VERSION` 5 → 6 plus changelog prose; add `MIN_LOBBY_PROTOCOL_FOR_DEFAULT_SCORING` immediately after `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK`.

### 4.6 `client/src/services/tournamentCredentialStore.ts` (U4, new file)
Modelled on `multiplayerSession.ts`: `sessionStorage`, `TOURNAMENT_CREDENTIAL_STORAGE_KEY`, an expiry carried from the server, an `isValid` predicate consulted on every read, `load`/`save`/`clear`. Every access wrapped in `try/catch` (the existing session module's posture; `sessionStorage` throws in some privacy modes).

### 4.7 `client/src/stores/multiplayerStore.ts` (U4)
`tournamentCredentials` **removed from `partialize`**. `merge`'s `normalizeTournamentCredentials` call rehydrates from the new service module instead of from the persisted blob. **A `version` bump to 6 plus a `migrate` step that deletes any `tournamentCredentials` key already written to `localStorage`** — otherwise every returning browser keeps its durable tokens forever and the fix does nothing for existing users. This is the single most-likely-missed step in U4. `runGatedTournamentRpc` reads through the service module. Renew-on-connect wiring. The `TournamentCredential` doc comment's *"losing it is unrecoverable, which is why this map is persisted"* sentence is now false and is rewritten.

### 4.8 `client/src/pages/tournamentPageState.ts` (U5, U7)
Delete `isReportable` and `defaultScoringForArity`. Rewrite `isActiveEntrant`'s doc comment: it now reads a server-provided `dropped` flag as one conjunct of a client-composed authority check, and no longer claims to mirror a broker rule. `formatTiebreakValue` gains its `locale` parameter. The module header's "renders nothing and *formats* only" claim becomes strictly more true and should say so.

### 4.9 `client/src/pages/TournamentPage.tsx` (U5, U7)
`pageGeneration` per D7. Organizer controls gate on `view.summary.open_actions`; the drop control on `open_actions` **and** the credential conjunct; `onReport` unchanged in shape but `PairingsList` now reads `pairing.report_gate`.

### 4.10 `client/src/components/tournament/{PairingsList,CreateTournamentForm,ReportResultDialog,TournamentStandingsTable}.tsx` (U5, U6, U7)
Per D5, D6, D8. `PairingsList` switches from `isReportable(pairing.outcome)` to `pairing.report_gate === "Open"`; its long doc comment citing `tournament.rs:1741-1753` is replaced by one citing the server-side authority instead of restating its arms.

### 4.11 `client/src/adapter/types.ts` and the seven locale catalogs (U5)
`ReportGate`, `TournamentAction`, the two new fields, the two new reply types. New keys `create.scoringAuto`, `create.scoringRequiredHint`, and reason copy for the non-`Open` `ReportGate` arms — in **all seven** catalogs in the same commit, since `localeParity.test.ts`'s `"%s has exactly the English key set"` check is unconditional and never consults `KNOWN_PLACEHOLDER_GAPS`.

---

## 5. Sizing

**Units: 7** (§3). A unit = one coherent behavior implementable by a single skill-checklist pass, regardless of how many layers it moves in lockstep.

**Scope-path count**, under the phase-fit counting rule (test fixtures excluded; translation mirrors grouped with their source; directories expanded):

| Group | Paths |
|---|---|
| Rust — `lobby-broker/src/{protocol,tournament,broker,validation}.rs` | 4 |
| Rust — `server-core/src/{protocol,client_message_wire_guard}.rs` | 2 |
| Rust — `phase-server/src/main.rs`, `lobby-worker/broker-wasm/src/lib.rs` | 2 |
| Scripts — `check-protocol-version.mjs` | 1 |
| Client — `adapter/{types,ws-adapter}.ts` | 2 |
| Client — `services/{tournamentClient,tournamentCredentialStore}.ts` | 2 |
| Client — `stores/multiplayerStore.ts` | 1 |
| Client — `pages/{tournamentPageState.ts,TournamentPage.tsx}` | 2 |
| Client — `components/tournament/` ×4 | 4 |
| Locales — 7 catalogs grouped as one | 1 |
| **Total (grouped)** | **21** |

Counting the seven catalogs separately gives **27**. **T1 fires at 7 units and T2 fires at 21 ≥ 13 under both conventions**, so the conjunction holds under every reading and the split is not a judgment call.

**Recursive check.** A Rust-contract phase (U1+U2+U3) is 9 paths — T2 fails, so it does not re-trip. U4+U5 is ~9 paths and 2 units — T2 fails. U6+U7 is 4 paths and 2 units — T2 fails. The recursion terminates at three phases.

---

## 6. Verification Matrix

Every negative names its paired positive reach-guard. Rows marked `DEFERRED(phase n)` structurally cannot exist until that phase lands.

| # | Claim | Seam / entry point | Test | Revert-failing assertion | Hostile fixture |
|---|---|---|---|---|---|
| V1 | `open_actions` is empty of `StartRound`/`EndTournament`/`Drop` once terminal | `TournamentMeta::open_actions` | Rust unit, `tournament.rs` | set `Completed`; assert empty. **Positive control: same fixture in `InProgress` asserts all three present** | `Abandoned` (the second terminal arm); `Registration` (only `StartRound`+`Drop`) |
| V2 | `report_gate` returns each of its four arms | `TournamentMeta::report_gate` | Rust unit | one case per arm | pairing with `Reported(_)` → **`Open`**, not a "already reported" refusal — re-reporting is legal and this is the arm most likely to be wrongly narrowed |
| V3 | `open_actions` and the handler guards cannot disagree | the three handlers | Rust integration | for a terminal event, assert `open_actions` excludes the action **and** the handler returns `Err` — one fixture, both assertions | an event that becomes terminal *between* view and dispatch: assert the handler still refuses (the wire value is advisory, never authoritative) |
| V4 | **Today's bug**: a `Completed` tournament exposes no report affordance | `PairingsList` + `TournamentPage` | Vitest | render a `Completed` view with a seated non-dropped credential; assert no Report button. **Fails on today's code** | positive control: identical fixture in `InProgress` **does** render it |
| V5 | Organizer controls hidden once terminal | `TournamentPage` | Vitest | `Completed` → no Start/End. Positive: `InProgress` → both | `Registration` → Start present, End present, per `open_actions` |
| V6 | Omitted `scoring` yields `default_for_arity` | `handle_create_tournament` | Rust integration | create with `scoring: None`, arity 4 → `7/1/0`; assert via the resolved `TournamentSummary.scoring` | arity 2 → `3/1/0` (guards against an arity-independent constant); explicit `Some(9/2/1)` survives unchanged |
| V7 | Old frame with `scoring` present still parses | protocol round-trip | Rust unit | probe B1/B4 as a committed test | B2's failing direction pinned as an **expected** parse error, so the floor's necessity is documented in code |
| V8 | Below the floor, the client sends explicit scoring | `createTournamentOver` | Vitest | `lobbyProtocolVersion: 5` → frame **has** `scoring`. Positive: `6` → frame omits it | `undefined` → treated as below the floor |
| V9 | No client-side scoring default survives | repo-wide | static assertion in `tournamentPageState.test.ts` | `defaultScoringForArity` is not exported and `2 * arity - 1` appears nowhere in `client/src` | — |
| V10 | An expired credential is refused | `authorize_organizer`/`authorize_player` | Rust unit | advance the injected clock past `expires_at_ms` → `Err`. **Positive control: one ms before → `Ok`** | a valid-but-rotated secret after renewal → `Err`; the *new* secret → `Ok` |
| V11 | Renewal rotates rather than extends | `renew_credential` | Rust unit | the presented secret is refused afterwards; the returned one accepted | renewing with an already-expired token → `Err` (no self-resurrection) |
| V12 | Tokens never reach `localStorage` | `partialize` + the new service module | Vitest | drive create+join, assert `localStorage` blob contains neither token, and `sessionStorage` does. **Positive: the store still functions — a gated RPC sends the token** (guards against "removed by breaking the feature") | the `migrate` step deletes a pre-existing persisted `tournamentCredentials` key |
| V13 | `LOBBY_PROTOCOL_VERSION` is 6 and the two floors did not move | `check-protocol-version.mjs` | `node scripts/check-protocol-version.mjs` | exit 0 with 6/5/6/2/55 | flipping `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` to 6 must **fail** the script |
| V14 | `tournament_request_id` stays exhaustive | the accessor | Rust unit | `RenewTournamentCredential` → `None` | positive: a gated variant still → `Some` |
| V15 | Percent values are not 100× wrong | `formatTiebreakValue` | Vitest | `0.5` → `"50.0%"` in `en`. **This is the `style:"percent"` double-multiply guard** | `de` → `"50,0 %"`; `points` `2` → `"2.00"` / `"2,00"`; `0` → `"0.0%"` not `""` |
| V16 | Locale actually reaches the formatter | `TournamentStandingsTable` | Vitest | render under `de`, assert a comma decimal in the DOM. Positive: `en` renders a period | guards against `i18n.language` being passed but ignored |
| V17 | `2.5` and `1e3` reach the wire unrounded | `CreateTournamentForm` | Vitest | type `2.5` into arity → submitted `arity` is `2.5`, **not `2`**; `1e3` → `1000`, not `1` | empty rounds → `null`; `"abc"` rounds → falls back, never `NaN`; empty arity → previous value, not `0` |
| V18 | The broker refuses those values | `MatchArity::new` / `ScoringPolicy::new` | Rust unit | `2.5` and `1e3` rejected — the reviewer's explicit ask | `win_points: 0` still rejected (unchanged guard, reach-guard for the fixture) |
| V19 | Game-wins typo does not silently become `0` | `ReportResultDialog` | Vitest | `"abc"` leaves the field absent, not `0`. Positive: `"2"` records `2` | empty string → absent; submit path's `?? 0` still supplies `0` |
| V20 | **A→B→A does not leak visit 1's settlement into visit 2** | `run` in `TournamentPage` | Vitest, `:code navigation` describe block | dispatch End on TOUR01, `navigateToCode` TOUR02, `navigateToCode` TOUR01, then deliver `TournamentActionRejected` **correlated to visit 1's `request_id`**; assert no alert and `busy` still held by visit 2's own action. **Fails on today's code** | **Positive control, mandatory**: visit 2's *own* rejection **does** render — without it a page that lost its alert region passes vacuously |
| V21 | Same for `handleReport` | `handleReport` | Vitest | A→B→A with a report in flight; visit 2's open dialog is **not** closed | positive: visit 2's own successful report closes it |
| V22 | Same for `seed` | `seed` | Vitest | A→B→A with the mount seed unanswered; no alert | positive: visit 2's own seed failure renders |
| V23 | The A→B case still works | existing tests | the three existing `:code navigation` tests | unchanged and green | they are the reach-guard that the generation ref did not *loosen* the guard |

**Coverage-status impact: none.** No `crates/engine/` file is touched, no Oracle text is parsed, and no card's supported/unsupported status moves. No `Effect::unimplemented` or strict-failure marker is involved.

**Parser changes: none.** No file under `crates/engine/src/parser/` is modified, so the Nom Compliance section is N/A by construction rather than by exemption.

---

## 7. Identity / Provenance Contract

| Binding | Source concept | Authority + value | Binding time | Live vs latched | Storage | Consumer | Invalidation | Hostile fixture |
|---|---|---|---|---|---|---|---|---|
| **Page visit** | "this page's current visit", CodeRabbit's finding | `pageGeneration.current`, a `u32`-ish monotonic counter | **dispatch** time of each continuation | **Latched** at dispatch; compared against live at settlement. Latching is the whole mechanism | `useRef` (never state — a re-render must not restart it) | `run`, `seed`, `handleReport` | bumped by the subscription effect on every run, including a repeat visit to the same code | V20-V22: A→B→A with a visit-1 request still pending |
| **Tournament credential** | organizer/player bearer authority | `TournamentCredential { secret, expires_at_ms }`, 128-bit CSPRNG | mint at create/join; **re-bound on every renewal** | **Live**: `accepts()` re-reads the injected clock each call, never a cached "is valid" flag | server: `TournamentMeta`/`TournamentPlayer` (+ DO snapshot); client: `sessionStorage` | `authorize_organizer`, `authorize_player` | expiry, rotation-on-renewal, `TournamentRemoved`, tab close, record reap | V10/V11: rotated-then-presented old secret; clock advanced past expiry |
| **Report affordance** | `report_result`'s non-authorization gate | `PairingView.report_gate: ReportGate` | computed per `TournamentView` construction | **Snapshot** — explicitly advisory. The handler re-decides on dispatch | wire frame only; never cached client-side | `PairingsList` | superseded by the next `TournamentUpdate` | V3: event turns terminal between view and dispatch; handler still refuses |
| **Tournament-action affordance** | the three `is_terminal` guards | `TournamentSummary.open_actions: BTreeSet<TournamentAction>` | per view construction | **Snapshot**, advisory, same as above | wire frame only | `TournamentPage` | next `TournamentUpdate` | V3 |
| **Scoring policy** | organizer choice vs broker default | `Option<ScoringPolicy>` on the request; resolved `ScoringPolicy` on the summary | resolved **once**, at `handle_create_tournament` | **Latched** at creation — the resolved value is stored, never recomputed per read (unlike `total_rounds()`, which resolves three sources at read time; the asymmetry is deliberate and must be documented) | `TournamentMeta` | `standings`, `TournamentSummary` | never — scoring is immutable for a tournament's life | V6: arity 2 vs 4 vs explicit override |

---

## 8. Remaining mandatory sections

**Pattern Coverage.** Not a card class. Three classes, each measured rather than asserted. (i) **Server-owned decisions the client re-derives**: enumerated exhaustively by reading every exported function in `tournamentPageState.ts` — three (`isReportable`, `defaultScoringForArity`, and the eligibility conjunction), all three addressed; the other nine exports are projections or formatters that decide nothing. The `ReportGate`/`open_actions` mechanism is generic over the action axis, so a fifth gated action reuses it by adding an enum arm rather than a new field. (ii) **Numeric inputs coerced before the authoritative validator sees them**: every `Number.parseInt` on a form input under `client/src/components/tournament/` — four call sites across two files, all four fixed. (iii) **Promise continuations scoped by a value that repeats**: all three on `TournamentPage.tsx`, fixed by one shared mechanism rather than three guards. Class (iii) generalizes beyond this page — the generation-ref shape is directly reusable by any route-param-scoped page with async continuations.

**Building Blocks.** Composed from, not reinvented: `BrokerEnv::now_ms` (injected clock, so native and WASM shells stay identical); `tokens_match` (`phase-server/src/main.rs`) for constant-time compare; `env.new_token()` for minting; `TournamentRole` (existing) as the renewal axis rather than a new enum; `MatchArity::new`/`ScoringPolicy::new` as the sole validators; `Intl.NumberFormat` via `byteSize.ts`'s `(value, locale)` shape; `multiplayerSession.ts`'s load/save/validate module shape; `createMemoryRouter` + the existing `navigateToCode` helper in `TournamentPage.test.tsx`; `LobbyClientMessage::tournament_request_id`'s exhaustive accessor. **One new helper is justified**: `tournamentCredentialStore.ts`, because the existing `multiplayerSession.ts` is keyed to a single game session while credentials are a per-code map with independent expiries — a shape it cannot express.

**Logic Placement.** Rules → `tournament.rs` (`open_actions`, `report_gate`, credential expiry) because that is where `TournamentManager` already owns them and where the handlers must consult them. Wire shape → `protocol.rs`. Dispatch/authorization → `broker.rs`. Storage policy → the client service module. Presentation → components. **No game rule moves to the client, and no display concern moves to the broker** — `ReportGate` carries a *reason*, not display copy; the seven locale catalogs own the words.

**Rust Idioms.** Typed enums over bools throughout (`ReportGate` not `reportable: bool`; `BTreeSet<TournamentAction>` not three `can_*` flags). Exhaustive `match` with no wildcard on both new enums and on `tournament_request_id`. A private field with an `accepts()` accessor so no call site can spell a plaintext comparison — the type system as the single authority, mirroring the predecessor plan's `Result<GatedEffect, String>` device. `BTreeSet` rather than `HashSet` for deterministic serialization. Checked conversion retained in `default_for_arity` (untouched). `u16` intermediate arithmetic preserved.

**Extension vs Creation.** Every part extends: `scoring` copies `total_rounds`'s established optionality in the same variant; the capability floor copies `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK`'s frozen-floor shape and pin mechanism; the credential module copies `multiplayerSession.ts`; the formatter copies `formatByteSize`; the generation ref extends `shownCode`'s documented mechanism rather than replacing its reasoning. **One genuinely new pattern**: credential rotation-on-renewal, which has no in-repo precedent (`reservation_auth` expires but never rotates). It is justified in D2 and is the minimum that makes a bearer credential revocable on a transport where it must remain JS-readable.

**Analogous Trace.** Named and traced in §1: `total_rounds` through `protocol.rs` → `tournament.rs` (`default_total_rounds`/`total_rounds()`) → `TournamentSummary` → `tournamentClient.ts` → `CreateTournamentForm.tsx` → the seven locale catalogs. Plus `multiplayerSession.ts` for U3/U4 and `byteSize.ts` for U6.

**Variant Discoverability.** §D10 — `cargo engine-inventory` structurally cannot answer for wire enums (`TARGET_DIRS = ["crates/engine/src"]`); the parameterization and existence checks were performed by hand and are recorded there.

**Nom Compliance.** N/A — no file under `crates/engine/src/parser/` is touched by any unit.

---

## 9. Probe ledger — measured vs. read

**Measured (compiled and run):**
- **P1 / B1-B6** — serde additivity for relaxing `scoring` to `Option`. Run in an isolated `CARGO_TARGET_DIR`, exited cleanly, all six cases printed. **B2 is the load-bearing result** and doubles as the reach-guard.

**Read at source, not executed (labelled, not promoted to fact):**
- The four `is_terminal()` guards and the resulting live drift (§0.1). Read in `tournament.rs`; the *rendering* consequence is inferred from `TournamentPage.tsx`'s gates. **V4/V5 are written to measure it**, and if either passes on today's code the §0.1 premise is wrong and must be re-derived before implementing.
- `Outbound`'s five variants and the absence of any HTTP-shaped effect — exhaustive read of the enum.
- Zero cookie usage repo-wide — grep, not execution.
- The A→B→A reachability argument — reasoned from React's scheduling plus the existing effect's reset order. **V20-V22 measure it**; the same falsification rule applies.
- Token lifetime arithmetic (7d + 30d) — read from the retention constants.

**Not probed, and flagged as such:** whether `sessionStorage` is available in every supported browser/privacy mode. Mitigated structurally rather than by measurement — every access is `try/catch`-wrapped and a failed read degrades to "no credential held", which renders spectator affordances rather than throwing. Worth an explicit test in the U4 phase.
