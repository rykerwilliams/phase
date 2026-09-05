# Implementation Plan — Request-Correlated Settlement for Gated Tournament RPCs

**Run:** `20260902-tournament-organizer-pr4` · **PR:** phase-rs/phase#8325 (PR 4/4 frontend rollout)
**Driver:** `matthewevans` CHANGES_REQUESTED — phase 1's own G1/B6 finding, re-opened as a ship blocker.
**Mode:** engine-planner, ordinary mode. Not a chartered phase; a maintainer-mandated addition to the same PR.
**Worktree:** `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend` (branch `feat/tournament-organizer-pr4-frontend`, clean at plan time, HEAD `3ce0f5c54`).

**Revision 5** — supersedes revision 4 (phase-fit entry 66) after plan review round 4 (entry 67: **0 blocking**,
2 material, 2 minor). Every round-4 finding is resolved below; §10 is the round-1 ledger, §11 the round-2
ledger, §12 the round-3 ledger and §13 the round-4 ledger, each mapping a finding to where it landed. The
core wire design — two new `LobbyServerMessage`
variants shared across all four actions, the rejection of per-action sibling variants, the rejection of
`request_id` on `TournamentUpdate`, the D8.1 decision that `"unsupported"` is a **wire** member, the
serde-additivity results, the seven-site emission census, the `ClientHello.lobby_protocol_version`
precedent, the `Result<GatedEffect, String>` broker refactor, the named
`MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` constant, and the two-phase split — has now been independently
re-verified in **four consecutive review rounds** and is **carried forward unchanged**. D8.1 is closed and is
not re-opened here.

**The completeness question is closed.** Round 4 did not merely re-read §3A.9's census — it reproduced the
whole compiler-driven enumeration from scratch in its own isolated target dir, matched it coordinate for
coordinate, then went further than any prior round by *applying* `request_id` at every site the census names
and running `cargo check --workspace --all-targets` to a clean exit 0. A green compile over the complete edit
set is a positive proof of exhaustiveness, not the negative "we found no more" every earlier round rested on.

**Structural change in this revision: none.** Revision 5 is deliberately narrow. It (a) replaces the
`broker-wasm` verification command with the form that actually executes (§3A.8.1, V20), (b) makes one
`main.rs` fixture literal non-vacuous so an **already-existing** test becomes this plan's regression guard
for its own highest-risk silent bug (§3A.5, new row **V23**), (c) names a fifth shared test-fixture builder
that the blanket instruction already covered (§3A.6), and (d) brings this front matter back in step with the
body. Scope paths, sizing, unit counts, phase boundaries and every architectural decision are unchanged.

---

## 0. The defect, restated from source

`startTournamentRoundOver`, `reportMatchResultOver`, `dropFromTournamentOver` and `endTournamentOver`
(`client/src/services/tournamentClient.ts`) all settle through
`matchReply<TournamentUpdateReply>("TournamentUpdate", code)`. That matcher's two conjuncts are the frame
**tag** and the **tournament code** — and its own doc comment says so: *"The `code` conjunct discriminates
tournaments, not requests."*

Server-side, `LobbyServerMessage::TournamentUpdate` is emitted from **one** `ToSelf` site
(`Broker::handle_get_tournament`) and **six** `ToSubscribers` sites (`handle_join_tournament`,
`handle_start_tournament_round`, `handle_report_match_result`, `handle_drop_from_tournament`,
`handle_end_tournament`, and `reap_expired`'s `Abandoned` arm). All seven produce a frame with exactly two
fields, `code` and `view`. There is no request-vs-broadcast discriminator on the wire.

So while one of the four gated helpers is in flight, any same-tournament frame — another participant's report,
the organizer's own concurrent `getTournamentOver`, the reaper — passes the filter, runs `cleanup()`, and
resolves `{ok: true}` with someone else's view. The caller's real `Error` then arrives with no listener and is
dropped. The page treats that as the operation's settlement. **Observable false success.**

The maintainer's ask, verbatim: *extend the wire/protocol with a request-correlating acknowledgement (or
another server-authoritative completion signal) and make the action helpers wait for that signal*, plus a
multi-client regression where an unrelated same-code update precedes a rejected action response.

### 0.1 Premise verification (Step 0 gate)

The engine-planner Step 0 gate is written for *card Oracle text*. **No card is involved** — this is WebSocket
RPC plumbing. The gate is discharged against the equivalent authority for this change, the real source, and
every premise in the maintainer's review was checked against it:

| Maintainer's claim | Verified? | Evidence |
|---|---|---|
| `tournamentClient.ts` sends `StartTournamentRound`/`ReportMatchResult` and settles on any code-matching `TournamentUpdate` | **Yes** | `startTournamentRoundOver`, `reportMatchResultOver`; both pass `matchReply("TournamentUpdate", code)` |
| The matcher documents the ambiguity in its own doc comment and returns the frame regardless | **Yes** | `matchReply`'s doc comment and body |
| A same-tournament update from another participant settles `{ok:true}` before our own result | **Yes** | Already pinned by an existing *characterization* test: `tournamentClient.test.ts` → `"…settles with a foreign actor's view, and a later Error cannot re-settle it"` |
| A later error for the actual request is lost | **Yes** | Same test asserts the post-`cleanup()` `Error` cannot re-settle the promise |
| **Correction — the maintainer named two; the class is four** | **Confirmed** | `dropFromTournamentOver` and `endTournamentOver` use the identical matcher. Module header part 3 names all four. Broker-side, all four are `ToSubscribers`-only |

**One premise correction to the task brief:** the brief says "the six emission sites this engagement's own
phase 1 planning already catalogued." That count is right for `ToSubscribers` but the total is **seven**
`TournamentUpdate` emission sites (6 broadcast + 1 `ToSelf` from `handle_get_tournament`), and the `ToSelf`
one matters here — it is the path by which the *caller's own* concurrent `getTournamentOver` produces a frame
byte-identical to a foreign broadcast. Phase 1 review round 2's residual note (3) flagged exactly this.

**Note on line-number citations in this revision.** Per the planner's durable-claim rule, assertions are
keyed to **symbol names** wherever the symbol is unambiguous, and line numbers appear only where the figure
itself carries information (a census row, a constant's pin site). Round 1 found two line citations had
drifted; carrying fewer of them is the repair that stays true, not a refreshed snapshot.

**And the converse trap, which round 2 caught this plan falling into (M3).** Symbol-keying is only durable if
the symbol is *real*. Revision 2 keyed a census row to a test named `lobby_protocol_version_is_current`, which
does not exist anywhere in the repository — a fabricated symbol is strictly worse than a stale line number,
because a stale line number *looks* stale while a plausible symbol name reads as verified. Every symbol this
revision names was grepped for before it was written. Where this plan *does* transcribe coordinates (§3A.6's
26 construction sites, §3A.8's four literals), the count and the positions *are* the information, and the
regenerating command is given beside them. (The revision number is deliberately absent from that sentence:
it is exactly the kind of figure that goes stale on the next pass — as round 4's m2 caught this document's
own front matter doing.)

---

## 1. The decisive finding: the protocol already solves this, one file over

The brief asked me to check this first, and the answer changes the shape of the fix.

**`crates/lobby-broker/src/protocol.rs` has no *request* correlation mechanism anywhere** — not on the seven
tournament variants, not on the nine pre-existing lobby variants. Exhaustive read of `LobbyClientMessage` and
`LobbyServerMessage`: zero `request_id`, zero nonce, zero sequence field.

### 1.1 Primary precedent — the identical serde shape, same file, same enum

Round 1 found the closest precedent revision 1 had missed, and it is closer than the cross-crate one:
**`LobbyClientMessage::ClientHello.lobby_protocol_version`**, in the *same file* and the *same enum* this
plan extends (`crates/lobby-broker/src/protocol.rs`, `ClientHello` at `:611`, the field at `:620-621`):

```rust
/// The client's [`LOBBY_PROTOCOL_VERSION`]. `None` from clients built
/// before the lobby owned its own version; those fall back to the
/// `protocol_version` window. Additive and optional, so an older broker
/// ignores it and an older client omits it — no `PROTOCOL_VERSION` bump
/// is required for either direction to keep parsing.
#[serde(default, skip_serializing_if = "Option::is_none")]
lobby_protocol_version: Option<u32>,
```

This is **byte-for-byte the serde shape D4 proposes**, on the same enum, carrying a doc comment that states
the identical both-directions-additive rationale this plan's probe P1 measures independently. `ServerHello`
carries the mirror field with the same attributes (`:762-763`). The new `request_id` field is therefore not a
new convention in this file — it is *the* convention this file already uses for exactly this situation, and
the new field's doc comment should be written to match its voice.

### 1.2 Secondary precedent — the correlation mechanism itself

**`crates/server-core/src/protocol.rs` — the canonical enum `lobby-broker`'s file is declared to be "the
lobby subset of", wire-compatible by construction — has carried request correlation for 27 protocol
versions.** Two instances, both structured identically:

```rust
// client → server                        // server → client (point replies, requester-only)
PreviewManaPayment { request_id: u64, .. } ManaPaymentPreview         { request_id: u64, source_ids: .. }
                                           ManaPaymentPreviewRejected { request_id: u64, rejection: .. }
                                           ManaPaymentPreviewFailed   { request_id: u64, message: .. }

ResolveAll { request_id: u64, .. }         ResolveAllResult   { request_id: u64, .. }
                                           ResolveAllRejected { request_id: u64, rejection: .. }
                                           ResolveAllFailed   { request_id: u64, message: .. }
```

And `PROTOCOL_VERSION`'s own changelog names the pattern by the maintainer's word:

> **29** — Added *requester-correlated* `ResolveAllRejected` response frames.
> **41** — Operational failure responses are *correlated to their pending action*.

This is not an analogy. It is the same protocol family, the same `#[serde(tag="type", content="data")]`
shape, the same problem (a reply that must be told apart from ambient traffic on a shared socket), solved
the same way. Per CLAUDE.md's **extend, don't hack** and **compose from building blocks**: the fix is to
carry this pattern into the lobby surface, not to invent a parallel one.

**Analogous trace (Step 2 hard gate).** Traced `PreviewManaPayment` end-to-end:
`crates/server-core/src/protocol.rs` (`ClientMessage::PreviewManaPayment { request_id }`
→ `ServerMessage::ManaPaymentPreview / ManaPaymentPreviewRejected / ManaPaymentPreviewFailed`)
→ that file's round-trip tests (pinning `request_id: 7` through the adjacently-tagged frame)
→ its wire-literal test (`{"type":"ManaPaymentPreviewFailed","data":{"request_id":7,"message":"…"}}`).

Three properties of that design carry over verbatim, and each answers a design question below:
1. The correlator is **client-minted** (the client picks the number; the server only echoes it).
2. Success and failure are **separate dedicated point-reply variants**, never a field bolted onto a
   broadcast.
3. Correlated replies are **requester-only** (`ToSelf`), never fanned out.

---

## 2. Architectural decisions

### D1 — Scope: correlate the four gated tournament actions, not every lobby frame

**Decision: per-variant `request_id` on the four `ToSubscribers`-only tournament actions. No general
envelope.**

The "build for the class, not the card" question here is: *what is the class of RPCs that settle on a
broadcast?* I measured it rather than assuming.

**Measurement.** The only other `LobbyClientMessage` variants whose broker handler returns
`ToSubscribers`-only are `UpdateLobbyMetadata` and `UnregisterLobby`. Both client call sites are in
`client/src/services/brokerClient.ts` and both are **fire-and-forget**:

```ts
const updateMetadata = (…): void => { … ws.send(JSON.stringify({ type: "UpdateLobbyMetadata", … })); };
const unregister = async (…): Promise<void> => { … ws.send(JSON.stringify({ type: "UnregisterLobby", … })); };
```

`updateMetadata` returns `void`. `unregister` is `async` but awaits nothing and its own comment says *"Callers
already treat unregister as fire-and-forget."* Neither awaits a reply, so neither can be mis-settled.

**Therefore the class of affected RPCs is exactly the four**, today and structurally: a fire-and-forget send
has nothing to correlate. A general envelope-level correlator would add a field to all sixteen
`LobbyClientMessage` variants for zero present consumers — and would contradict the very precedent it claims
to generalize, since `server_core::ClientMessage` has **no** envelope either: `PreviewManaPayment` and
`ResolveAll` each carry their own field while `Action`, `Interaction` and `Reconnect` carry none.

Where "parameterize, don't proliferate" *does* bind is the **reply** side — see D3.

### D2 — Reply shape: two new variants, generic over which action they answer

**Decision:**
```rust
/// Requester-only acknowledgement of one gated tournament action. Carries the
/// correlator the caller minted, so a caller can tell its own outcome from an
/// ambient `TournamentUpdate` for the same tournament.
TournamentActionAck {
    request_id: TournamentRequestId,
    code: String,
    view: TournamentView,
},
/// Requester-only refusal of one gated tournament action.
TournamentActionRejected {
    request_id: TournamentRequestId,
    message: String,
},
```

**Rejected alternative A — add `request_id` to `TournamentUpdate`.** Fails on two counts. (i) That frame is
emitted `Outbound::ToSubscribers(msg)` — *one* payload fanned to *every* subscriber; a correlator on it would
either be broadcast to everyone (meaningless) or force a second, differently-shaped `TournamentUpdate` sent
`ToSelf`, which would make `subscribeTournamentsOver`'s handler fire **twice** per action for the acting
client. (ii) It re-entrenches the exact tag-conflation that caused the bug: one tag meaning both "your reply"
and "ambient broadcast" is the defect, and the next reader would walk into it again.

**Rejected alternative B — four sibling ack variants** (`StartTournamentRoundAck`, `ReportMatchResultAck`, …).
This is CLAUDE.md's textbook **sibling-cluster smell**: four variants sharing a name root and differing only
in a context label. The action's identity is already carried by the `request_id` the caller minted — the
client knows which request `#7` was. Adding the action kind to the frame would be data the display layer
must not need.

**Why two variants and not three** (the full-game trio is result/rejected/failed): that split exists because
`server_core` distinguishes an engine `ActionRejection` DTO from an operational failure string. The lobby has
no such distinction — every refusal in `broker.rs` goes through one `fn error(message: &str) -> Outbound`
producing prose. Importing a distinction the lobby does not have would be proliferation.

**Why the ack carries `view`.** Precedent in the same file: `handle_join_tournament` already emits
`ToSelf(TournamentJoined { view })` *and* `ToSubscribers(TournamentUpdate { view })` with the same view. It
also fixes module-header part 3 as a genuine bonus — an **unsubscribed** caller currently never observes
success at all and settles `"timeout"`; with the ack it gets a real point reply. And it keeps the four
helpers' resolved value shape unchanged for `multiplayerStore.ts`.

### D3 — Correlator type: `TournamentRequestId`, a `#[serde(transparent)]` newtype

**Decision:**
```rust
/// Client-minted correlator for one gated tournament action. Opaque to the
/// broker: minted by the caller, echoed on the reply, never stored.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(transparent)]
pub struct TournamentRequestId(pub u64);
```

The sibling precedent is a bare `request_id: u64`, and a newtype needs to earn its keep. It does, concretely:
`handle_report_match_result` already takes `pairing_id: PairingId`, and `PairingId` is a bare `u32` type alias
(`tournament.rs`). Adding a second bare integer parameter to that same signature is precisely the confusion
the newtype idiom exists to prevent. There is newtype precedent in the same protocol family
(`TerminalCredential(pub String)` in `server-core/src/protocol.rs`), and `#[serde(transparent)]` makes it
**wire-identical** to a bare `u64`, so it costs nothing on the wire.

### D4 — `Option<TournamentRequestId>` on the request, not a required field

**Decision:** each of the four `LobbyClientMessage` variants gains
```rust
#[serde(default, skip_serializing_if = "Option::is_none")]
request_id: Option<TournamentRequestId>,
```

Typed absence, not a sentinel (`0` must not mean "uncorrelated"). `None` means *this client predates
correlation*, and the broker answers it exactly as it does today — broadcast only, no ack. That is what keeps
the change additive in both directions. This is the shape §1.1's `ClientHello.lobby_protocol_version` already
establishes in this enum; the new field's doc comment should mirror that one's voice.

**Probe P1 — measured, not asserted.** A standalone `serde`/`serde_json` program replicating the exact shapes
(`#[serde(tag="type", content="data")]` enum, plus `protocol.rs`'s two-stage `Envelope`/`RawValue`
reconstruct):

| # | Case | Result |
|---|---|---|
| A1 | old frame (no `request_id`) → **new** enum | `Ok(StartTournamentRound { …, request_id: None })` |
| A2 | new frame (with `request_id`) → **old** enum | `Ok(StartTournamentRound { … })` — unknown field ignored |
| A3 | new frame → new enum | `Ok(… request_id: Some(42))` |
| A4 | `request_id: None` serialization | `{"type":"EndTournament","data":{"code":"T","organizer_token":"k"}}` — **byte-identical** to today |
| A5 | **positive control**: old frame → enum with a *required* `request_id` | `Err("missing field \`request_id\` at line 1 column 79")` |

A5 is the reach-guard: A1 passes *because of* `#[serde(default)]`, not because the probe is insensitive. A2
confirms neither enum sets `deny_unknown_fields` — so a v5 client's frame reaches a v4 broker without error.

**Round 1 independently reproduced all five cases in its own scratch crate** (not trusting this plan's
narrative) and added two reach-guard controls this plan had not run, both of which passed:
- **A4b** — byte-identical serialization is attributable specifically to `skip_serializing_if`, not to the
  field happening to be absent.
- **A6** — a `deny_unknown_fields` variant of the old enum *does* reject the new frame, proving the absence
  of that attribute is load-bearing rather than incidental.

Probe source retained at `<scratchpad>/serdeprobe/src/main.rs`. Regenerate with `cargo run` in that
directory; it depends only on `serde`/`serde_json` and never touches the repo target dir.

### D5 — Broker: one settlement authority, enforced by the type system

The four handlers currently exit through **exactly 14** separate `return vec![error(&reason)]` statements
(census: `handle_start_tournament_round` 3, `handle_report_match_result` 5, `handle_drop_from_tournament` 3,
`handle_end_tournament` 3 — round 1 independently confirmed this total). Threading a correlator through them
by convention would mean any future edit can add an uncorrelated exit and nothing catches it. CLAUDE.md's
**single authority** and **idiomatic Rust / let the compiler catch it** principles both point the same way:

**Decision: the four handlers change their return type to `Result<GatedEffect, String>`.** A bare
`return vec![error(…)]` then becomes a **compile error**, not a review finding.

```rust
/// Whether a gated action moved any `TournamentSummary` field, and therefore
/// whether the list broadcast is warranted. A typed axis rather than a bool:
/// the distinction is a real property of the action (only a result report
/// leaves every summary field untouched), and today it survives only as a
/// comment each handler has to remember.
enum ListRowEffect { Changed, Unchanged }

/// What a successful gated action produced. Handlers describe the outcome;
/// they never assemble outbounds themselves.
struct GatedEffect {
    code: String,
    view: TournamentView,
    list_row: ListRowEffect,
}
```

and the single authority:

```rust
/// The correlated settlement for one gated tournament action. Success and
/// refusal are two halves of one signal, so both are minted here and nowhere
/// else. `request_id: None` reproduces the pre-correlation behavior exactly.
fn settle_gated(
    &self,
    request_id: Option<TournamentRequestId>,
    outcome: Result<GatedEffect, String>,
) -> Vec<Outbound>
```

**Ordering.** `Outbound` order is documented as significant. On `Ok`, emit
`[ack?, ToSubscribers(TournamentUpdate), list_update?]` — `ToSelf` before `ToSubscribers`. This is not a new
convention: `handle_join_tournament` already emits its `ToSelf(TournamentJoined)` ahead of its
`ToSubscribers(TournamentUpdate)` in one `Vec`, and round 1 independently confirmed that convention
generalizes cleanly to `settle_gated`. On `Err`, `[TournamentActionRejected]` when correlated, else the
existing bare `Error` — byte-identical to today for an uncorrelated caller.

**What this removes, stated correctly (round 1, m2).** Revision 1 said "four duplicated
`vec![ToSubscribers(TournamentUpdate), tournament_list_update()]` constructions." Measured, it is **three
identical two-element tails** (`handle_start_tournament_round`, `handle_drop_from_tournament`,
`handle_end_tournament`) **plus one distinct one-element tail** (`handle_report_match_result`, which emits
`vec![Outbound::ToSubscribers(…)]` alone — precisely the `ListRowEffect::Unchanged` asymmetry `GatedEffect`
types). So the refactor collapses 3 duplicates and folds the 4th's divergence into a typed field rather than
a comment. Still a net simplification; the framing is just accurate now.

**Decision status.** Revision 1 flagged this as an open judgment call against a smaller alternative (thread
`request_id` and swap `error()` for `reject()` at each of the 14 sites). **Round 1 endorsed the `Result`
form**, on two grounds this plan adopts: the `handle_join_tournament` ordering convention above generalizes
without invention, and the "this is frozen PR2 code" objection is weak because the maintainer has already
reopened this exact code through review. It is no longer an open call — see §8.

### D6 — Correlate `guard_inbound`'s refusal too; be honest about the one path that cannot be

`Broker::handle` runs `guard_inbound(&msg)` **before** the dispatch match and returns a bare `error(&reason)`.
For a correlated request that would be an uncorrelated refusal the client is designed to ignore — a hang
until timeout.

**Decision:** extract the correlator before the guard, via an exhaustive accessor on the message:

```rust
impl LobbyClientMessage {
    /// This frame's gated-action correlator, if it carries one. Exhaustive by
    /// construction, so a future gated variant that forgets a correlator is
    /// visible here rather than silently uncorrelated.
    pub fn tournament_request_id(&self) -> Option<TournamentRequestId> { … }
}
```
```rust
let request_id = msg.tournament_request_id();
if let Err(reason) = crate::inbound_guard::guard_inbound(&msg) {
    return vec![settle_rejection(request_id, &reason)];
}
```

**The one path that genuinely cannot be correlated — and it is a regression, not merely an unimproved path
(round 1, m4).** The Cloudflare shell validates through `parse_lobby_client_message`, where
`validate_lobby_message` runs *inside* the parser and a bounds failure becomes `ParsedFrame::Malformed(String)`
— a variant that discards the message and therefore the correlator.

Revision 1 disclosed this as a gap but under-framed it. The honest framing is that it **trades away a
deliberately-designed property**. `lobby-worker/broker-wasm/src/lib.rs`'s `reject_reply` carries its own doc
comment saying so explicitly (`:84-88`):

```rust
/// Single `Error` reply for a frame rejected at the parse/validation boundary.
/// Sent to the originating socket so the client's pending RPC fails fast rather
/// than waiting out its timeout. Malformed/unknown frames never reach
/// `Broker::handle`, so this boundary crate is the only place that can answer
/// them.
```

That function exists *precisely* to make a client's pending RPC fail fast instead of timing out. Under D7 a
correlated request ignores bare `Error` frames, so for the four gated actions this fast-fail no longer
reaches the caller: **the change trades a designed fast-fail for a timeout on this path.**

Reachability is the mitigating fact, and round 1 confirmed the characterization is fair: reaching it requires
a field-bounds violation (over-long code or token) on one of these four variants, and those payloads are
machine-generated by the store from broker-minted values, so it is near-unreachable from the real UI.
Restructuring `ParsedFrame` to carry the parsed message through a validation failure is a wider change than
this fix warrants. The trade is stated in the module header (Phase B, §3B.2) in these terms — as a property
given up, not as a path left alone.

### D7 — Client: mint the correlator inside the module; helper signatures unchanged

The four helpers keep their exact current signatures. The correlator is minted **inside**
`tournamentClient.ts` by a module-private counter and never appears in a parameter.

This is load-bearing for scope: `multiplayerStore.ts`'s `runGatedTournamentRpc` types its `send` parameter as
`(socket, token, signal) => Promise<TournamentRpcResult<T>>`. Because the signatures do not move, **phase 2's
frozen store needs no functional change** for the correlation itself. (It does take one doc-comment
correction — see D8's ripple analysis.)

Client-minted rather than server-assigned, following `PreviewManaPayment`: a server-assigned id would need
its own round trip to deliver, which is the problem being solved. Per-socket uniqueness is all that is
required; a module-scoped monotonic counter is strictly stronger and survives reconnects. JS numbers are
exact to 2^53 and the wire type is `u64`; at one increment per organizer action the ceiling is unreachable.

New matcher, alongside — not replacing — `matchReply`:

```ts
/**
 * The reply filter for a correlated gated action. Unlike {@link matchReply},
 * whose conjuncts are tag + tournament code, this one binds on the correlator
 * the caller minted, so an ambient `TournamentUpdate` for the same tournament
 * — from another participant, from this caller's own concurrent
 * `getTournamentOver`, or from the reaper — cannot match it at all.
 */
function matchAck(requestId: number): ReplyMatcher<TournamentUpdateReply>
```

`requestOver` gains an optional correlated-rejection matcher so that, for a correlated request:
- `TournamentActionAck` with **our** id → `{ok:true}`
- `TournamentActionRejected` with **our** id → `{ok:false, reason:"rejected"}`
- a bare `Error` → **ignored**, and here is why that is right rather than merely convenient: an uncorrelated
  `Error` provably belongs to *some* request on this socket but not provably to ours. Settling on it is the
  exact mirror image of the bug being fixed — a false *negative* in place of a false positive. With D6 in
  place the only remaining producer of a bare `Error` for a correlated frame is a parse failure, and a frame
  that never parsed never carried our id, so no correlated answer can exist and timeout is the honest
  settlement. (This is the same decision that produces D6's disclosed fast-fail trade; the two are one
  choice seen from two sides, and the module header must say so.)

**The three uncorrelated helpers keep `matchReply` and today's `Error` behavior unchanged**
(`createTournamentOver`, `joinTournamentOver`, `getTournamentOver`).

**Correction (round 1, m1).** Revision 1 said these three "were never exposed to B6." That is wrong for
`getTournamentOver`, and revision 1 contradicted itself on the point in its own §0.1. `getTournamentOver`
settles on the same `TournamentUpdate` tag the broadcast uses, so it **is** exposed to a racing same-code
frame — the exposure is simply **benign**, because the question it asks is `ToSelf`-shaped: "what is this
tournament's current view?" A foreign broadcast for the same code answers that question correctly. The
source already states this accurately, in `getTournamentOver`'s own doc comment:

> *This is the one helper whose reply is genuinely `ToSelf`, so a racing same-code broadcast still answers
> the question actually asked.*

The mandated header rewrite (§3B.2) must **preserve that comment's accuracy** — the correct wording is
"exposed but benign," not "never exposed." Writing the stronger claim into the header would regress a comment
that is currently right.

### D8 — Fail closed against a pre-correlation broker, with `"unsupported"` on the wire union

`PhaseSocket` already carries `serverInfo` (`openPhaseSocket.ts`), and `ServerInfo` already carries
`lobbyProtocolVersion` (`client/src/adapter/ws-adapter.ts:465`, doc comment at `:462-465`), populated from the
broker's `ServerHello`. **No new plumbing.**

The skew window is real, not theoretical: `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL = 2` means a v5 client accepts
a v4 broker, and client bundles deploy separately from the Worker (a cached tab is enough).

**Decision: send the frame, then settle a new typed reason `"unsupported"` without waiting.** Three options
were weighed:

- **(a) refuse to send** — safest against false success, but breaks a working feature during skew: an
  organizer simply cannot start a round.
- **(b) send, settle `"unsupported"` immediately** — the action *is* performed server-side; we simply cannot
  confirm it, and we say so.
- **(c) send and fall back to the tag+code matcher** — **rejected outright.** The fallback path *is* the bug.
  A version-gated reintroduction of a false-success path is not a compatibility measure.

**(b) is adopted, no longer merely recommended.** Round 1 probed the strongest counterargument against it —
that a user retrying after an unconfirmed action could double-submit a non-idempotent mutation — and found
**every affected action already carries its own independent server-side idempotency guard**: round generation
has its own status / round-ceiling / unresolved-pairing checks, `complete_tournament` has a terminal-state
guard, and drop is by-design non-idempotent in a way a repeat cannot corrupt. There is no data-integrity
hazard, so (b)'s only cost is a lost confirmation, which is exactly what it reports.

**Risk framing, corrected (round 1).** Revision 1 implied the skew window is broad. It is narrower than that
for the hosted deployment: `.github/workflows/deploy.yml`'s protocol-version gate greps the constant from the
tree and compares it to the deployed `/health`, which **requires the Worker to be redeployed before the client
deploy proceeds** — mostly closing the hosted exposure window. The real residual is **self-hosted
`phase-server` binaries running older releases**, which no deploy ordering can constrain. That population is
exactly the one for which (a) refuse-to-send would break the feature outright with no recourse, so the
corrected risk picture **strengthens** the case for (b) rather than weakening it.

#### D8.1 — Layer: `"unsupported"` is a **wire** member. Answering the documented boundary rule.

Round 1's M1 correctly flagged that revision 1 never engaged an existing, already-documented rule that
appears to argue the other way. `client/src/stores/multiplayerStore.ts` documents, for a
previously-considered-and-rejected fifth wire member (`TournamentNotAuthorized`, `:374-390`):

> *Deliberately not `reason: "rejected"`. `TournamentRpcFailureReason` is the WIRE vocabulary — each of its
> four members documents something the transport or the broker did … A local refusal contacted no broker and
> carries client-authored copy, so filing it under `"rejected"` would both falsify that contract and leave a
> consumer no way to tell the two apart except by matching English message text. … It lives here rather than
> as a fifth `TournamentRpcFailureReason` member because `tournamentClient.ts` is the wire layer and this is
> a store-level fact — and because that file is frozen by the time this store is written.*

**Decision: `"unsupported"` is a fifth `TournamentRpcFailureReason` member (option (a) of the two the review
offered).** This is argued, not asserted — the rule states four grounds, and each is tested against
`"unsupported"` on measured evidence:

**Ground 1 — "a local refusal contacted no broker."** Under D8(b), **the frame is sent.** This is the
decisive difference. `runGatedTournamentRpc`'s own doc draws the contrast in exactly these terms:
`not_authorized` is *"decided HERE, from this store's own map, with certainty. **Nothing was sent.**"* and the
store *"refuses locally … before any socket is opened, so a call with no credential costs nothing and puts
nothing on the wire."* An `"unsupported"` request opens a socket, puts a real frame on the wire, and the
server performs the action. It fails the defining property of the category the rule was written for.

**Ground 2 — "carries client-authored copy."** Measured against the union's existing membership, this cannot
be the discriminator: **three of the four incumbent members are minted client-side inside
`tournamentClient.ts` with hardcoded English copy** — `connection_lost` (`"Lobby connection dropped, please
try again"`), `aborted` (`"Tournament request aborted"` / `"…before start"`), and `timeout`
(`"No response from the tournament server within {n}ms"`). Only `rejected` carries broker text. Client-authored
copy is the *norm* in this union, not an exclusion criterion.

**Ground 3 — "`tournamentClient.ts` is the wire layer and this is a store-level fact."** This is the real
axis, and it points *toward* the wire union here. `lobbyProtocolVersion` is not a store-owned fact: it is a
field on `PhaseSocket.serverInfo`, populated from the broker's own `ServerHello` frame
(`protocol.rs:759-763` → `ws-adapter.ts:465`). It is a **server-observed fact received over the wire**. What
makes `not_authorized` a store fact is that its sole input — `tournamentCredentials` — is a map the store
itself owns and mutates; the version check has **no store-owned input at all**. The store could physically
read `socket.serverInfo`, so (b) is feasible; it would just mean the store reaching across a layer boundary
to re-derive a wire property that the wire layer already holds.

The distinction the union actually draws, once all four incumbents are examined, is not *who evaluated the
predicate* — the client evaluates three of four — but *whose fact the predicate reads*. `timeout` (a client
timer over server silence), `aborted` (a client signal), and `connection_lost` (a client `readyState` read)
are all client-**evaluated** readings of transport-level facts. `"unsupported"` is the same shape: a
client-evaluated reading of a **broker-advertised** fact. `not_authorized` is the one that reads a fact the
client itself authored, which is why it sits outside.

**Ground 4 — "that file is frozen by the time this store is written."** This ground is explicitly
time-bound and is now **void**: the maintainer's CHANGES_REQUESTED reopened `tournamentClient.ts`, and this
plan modifies it substantially. The doc comment should be updated to record that the freeze no longer holds
(see the ripple below), so the next reader does not apply a lapsed premise.

**Copy, and the i18n boundary.** The new reason's `message` is frontend-authored user-facing chrome, and per
this codebase's i18n-boundary rule it **must** render through `t()` — see D12. The wire-layer `message` string
on the result object remains a non-rendered fallback, exactly as the other four client-minted members' strings
already are (the page renders `t(failure.key)`, never `failure.message`, except for `errors.serverRejected`
which interpolates the broker's verbatim text).

**Ripple analysis (both directions worked through):**

- **`tournamentPageState.ts` enters scope either way.** Its `failureLabel` doc comment states the gate
  catches *"a sixth failure member anywhere (**a fifth `TournamentRpcFailureReason`, or a second store-level
  refusal**)"*. Both branches of the M1 choice trip the same `never` binding, so D12's wiring is required
  regardless of which layer wins — the choice changes *what* the new member looks like, not *whether*
  `failureLabel` and the seven locale catalogs must be updated.
- **`multiplayerStore.ts` enters scope for one doc-comment correction, and revision 1's "zero changes" claim
  is retracted to that extent.** No code changes: `GatedTournamentRpcResult<T> = TournamentRpcResult<T> |
  TournamentNotAuthorized`, so widening `TournamentRpcFailureReason` widens the gated result type
  automatically through the existing alias. But the `TournamentNotAuthorized` doc says *"each of its **four**
  members"* and the "frozen file" ground is now false. Leaving a stale count and a lapsed premise in the one
  comment that documents this boundary is precisely the kind of drift this plan is correcting elsewhere. The
  edit is: the count, plus one sentence recording that `"unsupported"` was added to the wire union on the
  *was-anything-sent* axis and why `not_authorized` still is not.
- **The two page components need no change.** `TournamentPage.tsx` renders
  `{"message" in failure ? t(failure.key, { message: failure.message }) : t(failure.key)}` — a **structural**
  test, not a per-key switch — so a new no-interpolation member routes through the existing branch untouched.
  Same for `TournamentLandingPage.tsx`, which consumes `failureLabel`'s result identically. Verified by
  reading both call sites; they are **not** scope paths.

**`MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL` and `MIN_SUPPORTED_LOBBY_PROTOCOL` must NOT move.** Per that
constant's own documented policy the floor moves only when a peer cannot *parse* a frame it routinely
exchanges — and probe A2 proves a v5 frame parses fine on a v4 broker. Raising the floor would evict every
lobby session (hosting, browsing, joining) over a tournament capability most users never touch. This is the
same asymmetry `LOBBY_PROTOCOL_VERSION` entry 4 already argues for itself.

#### D8.2 — The capability floor is a **named frozen constant**, never the current version (round 2, M4)

Revision 2 specified the gate as the bare expression `lobbyProtocolVersion === undefined || < 5`. That
literal `5` is a **sixth protocol-version pin** — absent from D9's census, absent from
`scripts/check-protocol-version.mjs`'s regex set, and therefore free to drift silently. Worse, it sits one
paragraph away from D14's instruction that a *neighbouring* literal "should be written as a reference to the
client's own `LOBBY_PROTOCOL_VERSION` export rather than a bare number." An executor generalising that
instinct writes `lobbyProtocolVersion < LOBBY_PROTOCOL_VERSION`, and **that is a real latent bug**: at the
next lobby bump to 6, every correctly-functioning v5 broker — which *does* mint `TournamentActionAck` —
would be refused as unsupported, silently disabling all four organizer actions against fully-compatible
servers. The two literals are semantically opposite. D14's is "what this client speaks *now*" and must
track. This one is **a floor frozen at the version that introduced the capability** and must never move.

**Decision: name it, freeze it, pin it, and say so in its own doc comment.**

```ts
/**
 * Lowest broker `LOBBY_PROTOCOL_VERSION` that can answer a gated tournament
 * action with a `TournamentActionAck` / `TournamentActionRejected` frame.
 *
 * This is a FLOOR frozen at the version that introduced correlated tournament
 * settlement, not a moving target. It must NOT be bumped when
 * `LOBBY_PROTOCOL_VERSION` moves: a v6 or v7 broker still answers the ack, and
 * raising this to match the current version would refuse every one of them and
 * silently disable organizer actions against servers that work perfectly.
 * Like {@link MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL} there is deliberately NO
 * ceiling. It moves only if a future version REMOVES the ack, which would be a
 * breaking change requiring its own floor decision.
 */
export const MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK = 5;
```

**Placement: `client/src/adapter/ws-adapter.ts`, immediately after `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL`.**
Verified as the right home rather than assumed: that file already owns `LOBBY_PROTOCOL_VERSION` (`:442`),
`MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL` (`:454`, whose own doc comment is the established in-repo statement of
exactly this "frozen floor, deliberately no ceiling" shape) and the `ServerInfo.lobbyProtocolVersion` field
the gate reads (`:465`). It is already a Phase A scope path for the version bump, and
`check-protocol-version.mjs` already reads it, so pinning the new constant costs one regex against a source
the harness loads anyway. A value import of it into `tournamentClient.ts` is precedented, not novel:
`services/openPhaseSocket.ts` and `stores/multiplayerStore.ts` both value-import from `ws-adapter.ts` today
(`serverProtocolRejection`), and `tournamentClient.ts`'s existing type-only `openPhaseSocket` import — pinned
verbatim by a section-F assertion — is untouched by adding a second import line.

**The constant lands in Phase A**, with the version bump and its `check-protocol-version.mjs` pin (V21); its
**consumer** — the gate itself — is `DEFERRED(Phase B)`. An exported-but-unconsumed constant is inert for one
phase and is not lint-visible; the alternative (defining it in Phase B) would split a version pin from the
version bump it is pinned against, which is exactly the drift D9's census exists to prevent.

#### D8.3 — The `undefined` default, and a deliberate divergence from `ws-adapter.ts`

The gate treats `lobbyProtocolVersion === undefined` **or** `< MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` as
unsupported. This **diverges** from how the codebase treats `undefined` elsewhere, and the divergence is a
considered choice, stated rather than silent:

`ws-adapter.ts`'s compatibility check **tolerates** `undefined` — `if (onLobbySurface &&
info.lobbyProtocolVersion !== undefined)` (`:517`) skips the version comparison entirely when the peer never
advertised one. That is correct **for the question it asks**: session admission. Refusing a whole lobby
session because a broker predates lobby-version advertisement would evict hosting, browsing and joining —
the exact asymmetry `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL` exists to prevent.

The correlation gate asks a different question: *can this specific peer mint a `TournamentActionAck`?* A peer
that never advertised a lobby version is strictly older than the version that introduced the ack, so the
answer is no. Tolerating `undefined` here would send a correlated frame to a broker that cannot answer it and
then wait — either hanging to timeout or, worse, tempting a fallback to the tag+code matcher, which is
option (c) and is rejected. **Different question, different default.** Both behaviors are correct for their
own gate; the plan records the divergence so the next reader does not "harmonize" them into a bug.

This choice is what makes D14's harness fix (§D14) mandatory rather than cosmetic.

**Do not conflate the four lobby constants.** They answer four different questions and only one of them
tracks the current version. All four are pinned by `scripts/check-protocol-version.mjs`, each by its own
regex, so a drift in any of them is caught mechanically:

| Constant | Side | Question | Moves when? |
|---|---|---|---|
| `LOBBY_PROTOCOL_VERSION` | both (`ws-adapter.ts:442`, `protocol.rs`) | what does this client speak? | **every** lobby wire change (→ 5 here) |
| `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL` | TS (`ws-adapter.ts:454`) | may this client hold a lobby session at all? | only when a peer cannot *parse* a routine frame (**not** here — probe A2) |
| **`MIN_SUPPORTED_LOBBY_PROTOCOL`** | **Rust (`crates/lobby-broker/src/protocol.rs:377`, `= 2`)** | **may this *broker* keep a client's session at all?** — the server-side mirror of the row above, and the fourth confusable | **stays at 2.** Version 5 is purely additive (probe A2), so a v2 client parses every frame it already understood. Pinned by `check-protocol-version.mjs:145`; asserted by `lobby_protocol_version_is_independent_of_the_full_game_one`, whose "purely additive" comment §3A.7's m6 item updates |
| `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` | TS (`ws-adapter.ts`, new) | can this peer answer a gated tournament action? | only if the ack is ever **removed** (frozen at 5) |

*(Round 3, m5: revision 3's table listed three and omitted the Rust-side floor — the one most easily
confused with `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL`, since the two differ by a single word in the name, sit
on opposite sides of the wire, and both hold the value 2. The table exists precisely to stop that
conflation, so its omission was the omission that mattered most.)*

### D9 — Version: `LOBBY_PROTOCOL_VERSION` 4 → 5. `PROTOCOL_VERSION` stays at 55.

A `LobbyServerMessage` **variant is added**, which is trigger #1 of that constant's own four-trigger policy.
The bump is mandatory.

`PROTOCOL_VERSION` does **not** move, and this is not a judgment call — it is the precedent set by PR2 of this
same engagement, verified empirically:

```
$ git show a4d569d86 -- crates/lobby-broker/src/protocol.rs | grep -E "^[-+]pub const .*PROTOCOL"
-pub const LOBBY_PROTOCOL_VERSION: u32 = 3;
+pub const LOBBY_PROTOCOL_VERSION: u32 = 4;
```

Commit `a4d569d86` ("tournament organizer protocol + native server wiring (PR 2/4)", #8258) added **7 client
and 5 server variants** across `lobby-broker`, `server-core` *and* `phase-server` — including mirrored
variants on the canonical `ClientMessage`/`ServerMessage` — and moved **only** `LOBBY_PROTOCOL_VERSION`.
`PROTOCOL_VERSION` and `MIN_SUPPORTED_LOBBY_PROTOCOL` did not move. This change is the same shape and follows
the same rule: no lobby variant carries `GameState` or `GameAction`, so the lobby number is the one that
governs. Round 1 re-ran this `git show` independently and confirmed it.

**Every site that pins the number** (census, not sample).

**Symbol-identity correction (round 2, M3).** Revision 2's census named a test
`lobby_protocol_version_is_current`. **That symbol does not exist anywhere in the repository** — re-verified
here by a repo-wide search returning zero hits. Revision 2 then named the *real* test under its correct name
elsewhere in the same section, so one object was carried as two. A fabricated symbol is worse than a stale
line number precisely because it reads as verified: an executor greps for it, finds nothing, and either skips
the pin or distrusts the whole census. The two real tests, read at source, are:

- **`lobby_protocol_version_is_independent_of_the_full_game_one`** (`protocol.rs`, the `assert_eq!` at
  `:986`) — holds `assert_eq!(LOBBY_PROTOCOL_VERSION, 4)`, `assert_eq!(MIN_SUPPORTED_LOBBY_PROTOCOL, 2)`, an
  `assert_ne!` against `PROTOCOL_VERSION`, and a `const { assert!(floor <= current) }` block. This is the
  test revision 2 meant in both places.
- **`tournament_lobby_version_follows_the_format_config_bump`** (`protocol.rs:1129-1133`) — holds
  `const PRE_TOURNAMENT_LOBBY_VERSION: u32 = 3;` and `assert_eq!(LOBBY_PROTOCOL_VERSION, PRE_TOURNAMENT_LOBBY_VERSION + 1)`.

| Site | What it holds | Action |
|---|---|---|
| `crates/lobby-broker/src/protocol.rs` — `LOBBY_PROTOCOL_VERSION` | `pub const … : u32 = 4;` | → `5`, **plus a new changelog entry 5** above it |
| `crates/lobby-broker/src/protocol.rs` — `lobby_protocol_version_is_independent_of_the_full_game_one` | `assert_eq!(LOBBY_PROTOCOL_VERSION, 4)`; `assert_eq!(MIN_SUPPORTED_LOBBY_PROTOCOL, 2)`; the `assert_ne!` and the `const` floor block | the first `assert_eq!` → `5`. The `MIN_SUPPORTED_LOBBY_PROTOCOL` assertion, the `assert_ne!` and the `const` block **do not move**. Its inline "purely additive" comment does — see m6 in §3A.7 |
| `crates/lobby-broker/src/protocol.rs` — `tournament_lobby_version_follows_the_format_config_bump` | `assert_eq!(…, PRE_TOURNAMENT_LOBBY_VERSION + 1)` | this test's *premise* no longer holds at 5 — see §3A.7 |
| `client/src/adapter/ws-adapter.ts:442` | `export const LOBBY_PROTOCOL_VERSION = 4;` | → `5` + changelog prose |
| `scripts/check-protocol-version.mjs:10` | `EXPECTED_LOBBY_PROTOCOL_VERSION = 4` | → `5` |
| **`client/src/adapter/ws-adapter.ts` — `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK`** *(new, D8.2)* | `export const … = 5;` | **added** at 5 and **frozen there forever** — it must NOT track future bumps |
| **`scripts/check-protocol-version.mjs` — the ack-floor pin** *(new, D8.2)* | — | **added**: an `EXPECTED_MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK = 5` constant, an `extractVersion` regex requiring a **bare integer literal** (`/export\s+const\s+MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK\s*=\s*(\d+)\s*;/`, the same structural device the four existing lobby regexes use so re-deriving it from another constant fails to match), and an equality check whose error message says *why* it is frozen |
| `crates/server-core/src/protocol.rs` | `= lobby_broker::LOBBY_PROTOCOL_VERSION` | **derived — no change** |
| `lobby-worker/broker-wasm/src/lib.rs` | returns `lobby_broker::LOBBY_PROTOCOL_VERSION` | **derived — no change** |
| `lobby-worker/src/lobby-do.ts` | `lobby_protocol_version()` from WASM | **derived — no change** |
| `.github/workflows/deploy.yml` | greps the constant from the tree, compares to the deployed `/health` | **no source change**; it will *require the Worker to be redeployed* before the client deploy proceeds (this is the ordering constraint D8 credits with closing the hosted skew window) |

**Probe P2:** `node scripts/check-protocol-version.mjs` → exit 0 at HEAD. Baseline green; the gate is live and
the reading above is correct.

### D10 — CR annotations: N/A, checked explicitly

Checked per the mandatory gate rather than waved off. This change is WebSocket RPC correlation across a
lobby broker, a Cloudflare Durable Object shell and a React client. It implements **no** MTG game rule: it
does not touch turn structure, priority, the stack, state-based actions, zones, or any object property.
`crates/engine/` is not modified.

`docs/MagicCompRules.txt` is **absent from this worktree** (gitignored; `./scripts/fetch-comp-rules.sh` was
never run here) — which independently forbids writing any CR annotation, since CLAUDE.md requires every CR
number be grep-verified against that file before it enters the code and says explicitly: *if you cannot find
the rule number, do NOT write the annotation.* **Zero CR annotations may be added by this change.** This
matches every prior phase of this engagement.

### D11 — `add-engine-variant` gate: does not apply mechanically; principle applied by hand

The brief asked me to run the variant-discoverability gate. I checked its actual scope rather than assuming:
`crates/engine-inventory-gen/src/main.rs:111` declares

```rust
const TARGET_DIRS: &[&str] = &["crates/engine/src"];
```

(Re-verified in this revision at `:111` — the citation is current; the loop consuming it is at `:123`.)

`LobbyServerMessage` lives in `crates/lobby-broker/src/protocol.rs`, **structurally outside** what
`cargo engine-inventory` walks, and the enums the `add-engine-variant` skill gates (`QuantityRef`, `Effect`,
`TargetFilter`, `Keyword`, …) are engine AST types. `data/engine-inventory.json` therefore cannot answer an
existence or sibling-cluster question about a wire enum, and running it would be theater.

The **principle** was applied manually and is the substance of D2: the four-sibling-ack shape was identified
as a name-root sibling cluster and rejected in favor of one parameterized ack + one parameterized rejection.
Existence check done by exhaustive read of both enums — no `TournamentAction*` variant and no correlator
field exists today.

### D12 — The `"unsupported"` failure reason's full frontend wiring (round 1, B1)

Revision 1 added a fifth `TournamentRpcFailureReason` member and scoped **none** of what that member is
compile-gated by. The gate is not incidental: it was built for this case, and it names it.

**`client/src/pages/tournamentPageState.ts`** — `failureLabel` ends in `const unreachable: never =
failure.reason;` with **no `default:` arm**, and its own doc comment says why:

> *Terminates in a `const unreachable: never` binding and has no `default:` arm, so a sixth failure member
> anywhere (a fifth `TournamentRpcFailureReason`, or a second store-level refusal) fails the build here
> rather than rendering a blank alert.*

So D8 as written in revision 1 **does not compile.** Required, and all in the same commit:

1. **`FailureLabel` gains a member.** The union is a catalog key plus the interpolation variables that key
   needs (`{ readonly key: "errors.unsupported" }` — **no vars**, which is what keeps the two page components
   out of scope per D8's ripple analysis).
2. **`failureLabel` gains an arm** before the terminal:
   `if (failure.reason === "unsupported") return { key: "errors.unsupported" };`
3. **Every stale ordinal in `failureLabel`'s own doc comment, and one in its test (round 2, m1).** Revision 2
   scheduled two of these and missed two more. All four are in the blast radius of adding one member, and
   this engagement has now hit this exact drift class three times — so where the surrounding prose allows it
   **the repair is to state the durable form, not to refresh the arithmetic**. Read at source:

   | Site | Current text | Repair |
   |---|---|---|
   | `tournamentPageState.ts:509-511` | *"a **sixth** failure member anywhere (**a fifth `TournamentRpcFailureReason`**, or a second store-level refusal)"* | *"**any new** failure member (**another `TournamentRpcFailureReason` member**, or a second store-level refusal)"* — durable form; the sentence loses nothing, since what it documents is the gate, not the arity |
   | `tournamentPageState.ts:516` | *"a **four-member** union *inside one object type*"* | *"a **string-literal** union *inside one object type*"* — the load-bearing fact is that it is a property union, not its size |
   | `tournamentPageState.ts:519` | *"still that member after **all four arms**"* | *"still that member after **every arm**"* |
   | `tournamentPageState.test.ts:450` | *"total over all **six** failure shapes"* | *"total over **every** failure shape"* — the `it.each` table below it is the actual enumeration and grows by one row (V16) |

   The narrowing explanation itself — *why* the terminal binds `failure.reason` rather than `failure` —
   remains exactly correct and must be preserved verbatim; only the counts move.

   **Do NOT touch `tournamentPageState.ts:25`** (*"so a fifth wire arm fails the build in every place"*).
   Read in full: that sentence is about `outcomeLabelKey` / `isReportable` / `decisiveGameWins` walking
   `PairingOutcome` and `tiebreakCells` walking `Tiebreaks` — four wire unions this change does not touch.
   It is a true statement about a different union, and "fixing" it would introduce an error.
4. **All seven locale catalogs gain `errors.unsupported`**, in the same commit:
   `client/src/i18n/locales/en/tournament.json`, `…/de/tournament.json`, `…/es/tournament.json`,
   `…/fr/tournament.json`, `…/it/tournament.json`, `…/pl/tournament.json`, `…/pt/tournament.json`. This is
   not optional and not deferrable, and the **mechanism matters** (round 2, m5 — revision 2 named the wrong
   one). Read at source, `client/src/i18n/__tests__/localeParity.test.ts` runs two independent per-namespace
   checks:
   - **`"%s has exactly the English key set"`** (`:282-290`) — bidirectional key parity with `en` pinned as
     `SOURCE`, asserting both `keys(source) \ keys(target)` and `keys(target) \ keys(source)` are empty. It
     is **unconditional and never consults `KNOWN_PLACEHOLDER_GAPS`.** *This* is what fails an English-only
     key, and it would fail one even if that exemption list were non-empty.
   - **`"%s interpolates the same placeholders"`** (`:292-308`) — the only check that calls `isKnownGap`, and
     therefore the only one `KNOWN_PLACEHOLDER_GAPS` can exempt. Irrelevant here: the new key introduces no
     placeholder.

   Revision 2's conclusion (an English-only key fails the suite) was right; its stated reason ("because the
   exemption list is empty") was not. A **second, independent** gate also catches it: V16's own assertion in
   `tournamentPageState.test.ts` that every key `failureLabel` can produce satisfies
   `i18n.exists("tournament:<key>")` — the pattern already used at `:73`, `:180-181`, `:204-205` and `:509`.
   Verified: the `errors` block currently holds `notOrganizer`, `notEntered`, `serverRejected`, `timedOut`,
   `connectionLost`, `aborted`, `notFound` in each of the seven.
5. **`client/src/pages/__tests__/tournamentPageState.test.ts`** gains coverage for the new arm (V16).

**i18n boundary, stated explicitly.** The copy this member renders is **frontend-authored user-facing chrome**
— there is no broker text to pass through, because the broker was never asked. Per this codebase's
i18n-boundary rule it therefore goes through `t()` with a catalog key, never a hardcoded string in a
component and never the wire `message` field. English source copy should say what actually happened and what
it does *not* claim — the action was sent, and this server cannot confirm it — rather than implying failure.
The wire-level `message` on the result object stays as a non-rendered fallback, matching how the other three
client-minted reasons' strings already behave.

### D13 — `types.ts` reply declarations

`client/src/adapter/types.ts` gains `TournamentActionAckReply` and `TournamentActionRejectedReply` beside the
existing three tournament reply interfaces, each citing its Rust source symbol. These are the client's view
of the two new wire variants and are consumed only by `matchAck` and the correlated-rejection branch, which is
why they land in Phase B with their consumer rather than in Phase A with the Rust contract.

### D14 — The test harness default must move (round 1, M3)

`client/src/services/__tests__/tournamentClient.test.ts`'s `makePhaseSocket` helper builds its `serverInfo`
from a literal that supplies `version`, `buildCommit`, `protocolVersion` and `mode` — and **no
`lobbyProtocolVersion` at all**, so the field defaults to `undefined` across all **24** call sites in that
file (both counts verified in this revision).

Under D8.3's gate, `undefined` takes the unsupported path. Left alone, that would mean **every existing gated
helper test in the file silently settles `{ok:false, reason:"unsupported"}` immediately** — which does not
merely fail loudly, it fails *quietly in the wrong direction*:

- **V6 and V7 would be gutted.** Both assert a request stays genuinely **pending** after a foreign frame.
  A request that short-circuits at the gate is trivially not pending; the assertions would go vacuous while
  still passing or failing for reasons unrelated to correlation.
- **V8's `undefined` reach-guard would pass for the wrong reason.** Asserting "undefined behaves like
  too-old" is meaningless when *every* test in the file already takes that path by default — the guard would
  be measuring the harness, not the gate.

**Decision: `makePhaseSocket`'s default `serverInfo` gains `lobbyProtocolVersion: 5`.** Existing tests then
keep exercising the real gated-request behavior they were written for, and the old-version path is reached
only by tests that ask for it explicitly through the helper's existing `Partial<ServerInfo>` override
(`makePhaseSocket(ws, { lobbyProtocolVersion: 4 })`, `{ lobbyProtocolVersion: undefined }`). The override
mechanism already exists and needs no change — only the default moves.

The default should be written as a reference to the client's own `LOBBY_PROTOCOL_VERSION` export rather than
a bare `5`, so the harness tracks the constant instead of drifting from it at the next bump.

---

## 3. Implementation — two sequential phases

Round 1 recomputed sizing with D12's and D14's omissions folded in, and the phase-fit conjunction
(T1: units ≥ 2 **and** T2: scope-paths ≥ 13) **fires**. See §6 for the counting under both conventions.

The seam below is the one revision 1 had already identified in its own fit assessment; round 1 independently
endorsed it as the resolution and confirmed no re-planning is required. Phase A is the wire contract alone;
Phase B is broker settlement plus client consumption, kept together.

**Why B is not split further.** U2 (broker) and U3 (client) are the two halves of one behavior: the
maintainer asked for a multi-client regression test, and its broker half (V5) and client half (V6) prove the
same property from two ends. Splitting them would strand the maintainer's own requested regression as
`DEFERRED` across a phase boundary for no compile-order benefit — each half already compiles against
Phase A's contract. Revision 1 argued this and round 1 confirmed the reasoning sound.

**Phase discipline.** Phase A must land green — compiling, with every existing test passing — before Phase B
begins, and Phase B is planned against Phase A's landed commit as its `PHASE_BASE_SHA`. This is the same
discipline this engagement's 5-phase charter used throughout.

---

## 3A. Phase A — The correlated wire contract

**Goal.** Put the correlator and the two reply variants on the wire, in every crate that mirrors the wire,
absorb the field at every site the compiler forces, and move the version pins. **No behavior changes.** The
two new server variants are constructed nowhere, the four new fields are `None` on every path, `settle_gated`
does not exist yet, and the client still uses `matchReply`.

**Standalone completability (the green-tree property).** Because nothing constructs the new variants and
every new field is optional-with-default, this phase is a pure additive contract change: once the mechanical
absorption sites of §3A.6 and §3A.8 are included it compiles alone, and every existing Rust and TypeScript
test passes unchanged. Its own new tests are **V1, V2, V3, V4, V13, V14, V19, V20, V21, V23** — ten rows, all
fully writable and runnable within the phase, none `DEFERRED`. (V23 adds **no new test**: it is a one-token
fixture change that makes an existing `main.rs` test non-vacuous — see §3A.5.)

**The single authoritative list of Phase A's tests is §3A.10's Sizing table** (round 2, m2 — revision 2
carried three different lists across four sections, and the Sizing table is the one the orchestrator's
phase-fit gate re-adjudicates against, so it is the one every other section is now written to match). §4's
Phase A block and §6's deferral list state the same ten and must be kept in step with it, not with each
other.

### 3A.1 `crates/lobby-broker/src/protocol.rs`

- Add `TournamentRequestId` (D3) near `ServerErrorCode`.
- Add `#[serde(default, skip_serializing_if = "Option::is_none")] request_id: Option<TournamentRequestId>`
  to `StartTournamentRound`, `ReportMatchResult`, `DropFromTournament`, `EndTournament`. Doc-comment each in
  the voice of `ClientHello.lobby_protocol_version` (§1.1), which is the same shape in the same enum.
- Add `TournamentActionAck` and `TournamentActionRejected` to `LobbyServerMessage` (D2), in the tournament
  block, with doc comments stating they are requester-only and carry no token.
- Add `LobbyClientMessage::tournament_request_id()` (D6) — exhaustive match, no wildcard. It is **added** in
  this phase (it is part of the contract and is unit-testable here); its **call site** in `Broker::handle`
  lands in Phase B.
- `LOBBY_PROTOCOL_VERSION` → `5` with a new changelog entry documenting: two added server variants (trigger
  #1); the four additive optional client fields; why `MIN_SUPPORTED_LOBBY_PROTOCOL` stays at 2 (probe A2);
  and why `PROTOCOL_VERSION` does not move (the `a4d569d86` precedent).
- **`is_known_lobby_tag` needs no change** — the four client tags already exist and no client tag is added.
  Note in passing: that gate is not compile-checked, but it is unaffected here.
- **Four construction sites in this file's own inline `#[cfg(test)]` module** (round 3, B1 — missed by every
  prior revision). `tournament_client_variants_round_trip_through_serde` (`:1198`) builds each gated variant
  as a full brace literal — `:1215`, `:1219`, `:1225`, `:1229` — and each is an `E0063` the moment
  `request_id` exists. Each gains `request_id: None`. That value is also what the test *means*: it asserts an
  old-shape frame round-trips, and §D4's probe A1 is the reason an uncorrelated literal is the honest fixture.
  These coordinates are compiler-derived (§3A.9); regenerate rather than trust them.

### 3A.2 `crates/server-core/src/protocol.rs`

Mirror `TournamentActionAck`/`TournamentActionRejected` onto `ServerMessage` and the `request_id` field onto
the four `ClientMessage` tournament variants, keeping field names and serde attributes byte-identical (the
wire-compatibility-by-construction contract). Re-export `TournamentRequestId` beside the existing
`TournamentView` re-export.

### 3A.3 `crates/lobby-broker/src/validation.rs`

`validate_lobby_message`'s tournament arms take `request_id: _` — the correlator is opaque and needs no
bounds check.

**Correction to revision 1's stated mechanism (round 1, m3).** Revision 1 claimed the compiler forces every
one of these arms to be updated. Measured, that holds for **three of four**:

| Arm | Pattern today | Compiler forces an update? |
|---|---|---|
| `M::StartTournamentRound { code, organizer_token }` | exhaustive | **Yes** |
| `M::DropFromTournament { code, player_token }` (`:477`) | exhaustive | **Yes** |
| `M::EndTournament { code, organizer_token }` | exhaustive | **Yes** |
| `M::ReportMatchResult { code, player_token, outcome, .. }` (`..` at `:469`) | **already has a rest pattern** | **No** — it silently absorbs `request_id` |

The functional outcome is identical either way (the field needs no validation, so absorbing it is harmless),
but the executor must not rely on a compile error to be reminded of the fourth arm. Add `request_id: _`
explicitly to `ReportMatchResult` anyway, for symmetry and so the next reader sees the correlator was
considered rather than overlooked.

**Seven construction sites in this file's inline `#[cfg(test)]` module (round 3, B1).** Revision 3 scoped
only the match arms above and stopped; the compiler says this file has ten sites, not three. The seven
`E0063`s, each gaining `request_id: None`:

| Owner | Sites | Note |
|---|---|---|
| **`fn report_with` (`:774`)** — shared test builder | `:775` | **One edit, many callers fixed.** This helper mints the `M::ReportMatchResult` that four separate tests use. The executor edits **the builder only** — its call sites (`:819`, `:823`, `:897`, and the `report_match_result_rejects_*` tests) pass `&str`/`PodOutcome` arguments and are untouched by construction. Do not go hunting through the callers |
| `tournament_messages_accept_valid` (`:804`) | `:811`, `:821`, `:825` | `StartTournamentRound`, `DropFromTournament`, `EndTournament` literals (its `ReportMatchResult` comes from `report_with`) |
| `organizer_gated_messages_reject_oversized_organizer_token` (`:876`) | `:879`, `:883` | the two organizer-gated variants |
| `player_gated_messages_reject_oversized_player_token` (`:893`) | `:897` | `DropFromTournament` only (its `ReportMatchResult` comes from `report_with`) |

`None` is the right value everywhere here: these tests assert **field-bounds** verdicts, and D4 makes the
correlator opaque to validation — a correlated frame is validated identically, which is exactly what V20's
unmoved-assertions evidence claims. Coordinates are compiler-derived (§3A.9); regenerate, do not trust.

### 3A.4 `crates/server-core/src/client_message_wire_guard.rs`

Same treatment on its two tournament match blocks and its test fixtures. Its `ServerMessage::error(reason)`
fan-in is the native shell's bounds-rejection path and stays as-is; see D6's disclosed trade.

**Enumerated, not gestured at (round 3).** Revision 3's scope *language* covered this file, but it was the
only in-scope file whose sites were never listed — asymmetric against §3A.6's fully transcribed `broker.rs`
coordinates, and exactly the shape of asymmetry that hid three other files. Fifteen sites, compiler-derived:

| Kind | Owner | Sites | Edit |
|---|---|---|---|
| `E0027` pattern | `guard_client_message_before_dispatch` (`:52`) | `:202`, `:219`, `:222` | `request_id: _` |
| `E0027` pattern | `guard_broker_projection_inbound` (`:353`) | `:441`, `:458`, `:461` | `request_id: _` |
| `E0063` literal | `fn oversized_tournament_frames` (`:738`) | `:768`, `:775`, `:784`, `:791` | `request_id: None` |
| `E0063` literal | `fn valid_tournament_frames` (`:799`) | `:816`, `:820`, `:826`, `:830` | `request_id: None` |
| `E0063` literal | `broker_projection_rejects_an_oversized_game_wins_map_before_clone` (`:886`) | `:890` | `request_id: None` |

Note the same 3-of-4 asymmetry §3A.3 found: **both** guard blocks already carry a `..` rest pattern on
`ReportMatchResult`, so only three arms per block are compile-forced. Add `request_id: _` to the
`ReportMatchResult` arms anyway, for the same reason as §3A.3. The two `*_tournament_frames` helpers are
shared fixture builders consumed by `both_inbound_guards_agree_on_every_tournament_variant` (`:843`) and
`both_inbound_guards_accept_valid_tournament_frames` (`:863`) — as with `report_with`, editing the builder is
the whole edit; the consuming tests need nothing. Coordinates are compiler-derived (§3A.9); regenerate them.

### 3A.5 `crates/phase-server/src/main.rs`

`to_server_message` is **wildcard-free**, so the two new variants are compile errors until arms are added.

**Correction (round 3): this file's exposure is compile-time, not runtime.** Revision 3 wrote that
`to_lobby_client_message` "must forward `request_id` — or the existing serialized-equality assertion … fails
at runtime rather than at compile time." That is wrong, and wrong in the direction that costs an executor a
debugging session: the compiler produced **twelve** errors here. `to_lobby_client_message` (`:3699`)
destructures the *`server-core`* variant and constructs the *`lobby-broker`* one on the same arm, so each of
the four arms breaks twice — once as `E0027`, once as `E0063`:

| Owner | Sites | Edit |
|---|---|---|
| `to_lobby_client_message` (`:3699`) — `ClientMessage` destructure | `:3822`, `:3829`, `:3840`, `:3844` | bind `request_id` **by name** |
| `to_lobby_client_message` — `L::…` construction | `:3825`, `:3834`, `:3840`, `:3847` | forward `request_id: *request_id` |
| **`fn tournament_client_frames` (`:12850`)** — shared test-fixture builder | `:12871`, `:12882`, `:12886` | `request_id: None` |
| — its `StartTournamentRound` literal (`:12867`) | one site | **`request_id: Some(TournamentRequestId(7))`** — see the non-vacuity note below. This is the one fixture in Phase A that is deliberately *not* `None` |

`:3840` (`DropFromTournament`) carries both the pattern and the construction on one line and produces two
errors at two columns — the one site an executor scanning error *lines* would undercount.

Three things follow. First, **this is the one place in Phase A where the correlator is forwarded rather than
discarded**: `to_lobby_client_message` is the native shell's projection of the wire into the broker's enum,
and dropping the field here would silently uncorrelate every request from a native `phase-server` client
while the Worker path worked. Binding by name is compiler-forced (`E0027`); *forwarding the bound value* is
not — `request_id: _` on the pattern plus `request_id: None` on the construction compiles cleanly and is
exactly the bug. Forwarding is behavior-neutral in Phase A (nothing reads it yet) and is what makes Phase B's
client work on both transports.

**Second — non-vacuity: the guard for that bug already exists, and revision 4 mis-stated it (round 4, M2).** Revision 4
wrote that this divergence is *"a divergence no test in this phase would catch."* That is wrong, and wrong in
a way that cost the plan a free regression guard. `main.rs`'s existing
**`tournament_variants_survive_the_canonical_lobby_roundtrip`** already walks every frame from
`tournament_client_frames()`, projects it through `to_lobby_client_message`, and asserts
`serde_json::to_string` equality between the projection and the canonical frame, failing with *"field dropped
or renamed across the projection"*. It is a precise detector for forward-vs-discard — **but only if a fixture
carries a value that survives or does not survive**. Under `request_id: None` everywhere it cannot
discriminate at all: `skip_serializing_if = "Option::is_none"` (D4) means `None` emits **no key**, so a
correctly-forwarded `None` and a silently-discarded `None` serialize to byte-identical strings and the
assertion passes either way. That is the missing-positive-reach-guard pattern this plan's own review criteria
warn about, landing on the plan's own fixture choice.

The fix costs one token: **the `StartTournamentRound` literal takes `Some(TournamentRequestId(7))`**, which
makes the existing test red the moment that arm stops forwarding. New Verification Matrix row **V23** records
it. Two consequences the executor must carry:

- **Field position now matters.** The test compares serialized *strings*, and serde emits struct-variant
  fields in **declaration order**. So `request_id` must be added at the **same relative field position** in
  both wire mirrors — `LobbyClientMessage` (§3A.1) and `ClientMessage` (§3A.2) — or the two strings differ by
  field order and the test reds for a reason that has nothing to do with a dropped field. Under the old
  `None`-everywhere fixture a position slip was **invisible**; under `Some(..)` it is caught immediately.
  This is a second reason the §3A.2 "byte-identical field names and serde attributes" contract is
  load-bearing, and it now has a test behind it.
- **Residual, stated plainly.** One correlated fixture guards the **`StartTournamentRound` arm's** forward by
  value. The other three arms are guarded at the *binding* level by `E0027` and by V20's green compile, not at
  the value level. Giving each gated frame a distinct id would extend the same zero-new-test guard to all
  four arms at no cost; revision 5 changes exactly one site (the measured minimum) and names the gap rather
  than leaving it unstated.

Third, `tournament_client_frames` is a shared fixture builder like `report_with`, `started_event` and the two
`*_tournament_frames` helpers: **edit the builder, not its callers** (`interaction_is_full_only`,
`interaction_is_never_projected_into_the_lobby_broker`, and the round-trip tests below it consume the `Vec`,
not the literals).

`Outbound` dispatch matches on `Outbound`'s kind alone — **no change**. The four `{ .. }` arms at `:1196`,
`:1397`, `:5310` and `:9764` absorb the field silently and correctly (verified by their absence from the
compiler's output, which is a stronger statement than reading them). Coordinates are compiler-derived
(§3A.9); regenerate them.

### 3A.6 `crates/lobby-broker/src/broker.rs` — mechanical only (round 2, B1)

**Revision 2 omitted this file from Phase A entirely and the phase therefore did not compile.** Adding a
field to a struct-variant of `LobbyClientMessage` breaks every exhaustive destructure and every construction
site of that variant, and `broker.rs` holds both. Re-measured at source in this revision:

- **Four dispatch arms in `Broker::handle`**, at `:445`, `:450`, `:457` and `:461`, each destructuring its
  variant exhaustively with **no rest pattern** (`StartTournamentRound { code, organizer_token }`,
  `ReportMatchResult { code, pairing_id, player_token, outcome }`,
  `DropFromTournament { code, player_token }`, `EndTournament { code, organizer_token }`). Each is a compile
  error the moment `request_id` exists.
- **26 construction sites in the same file's inline `#[cfg(test)]` module** (which begins at `:1393`), every
  one a full brace literal with no `..`: `:2424`, `:2598`, `:2602`, `:2623`, `:2648`, `:2670`, `:2685`,
  `:2723`, `:2750`, `:2779`, `:2862`, `:2878`, `:2900`, `:2919`, `:2949`, `:2993`, `:3009`, `:3043`, `:3053`,
  `:3071`, `:3087`, `:3127`, `:3139`, `:3418`, `:3555`, `:3606`. (The figure and the coordinates are the
  information here, which is why they are transcribed. **Regenerate them with §3A.9's compiler recipe**, not
  with `rg` — every coordinate above came from `rustc` and round 3 confirmed all 30 exact, whereas the `rg`
  form this plan previously named is the file-level instrument §3A.9 explains cannot answer a site-level
  question. `rg -n '(StartTournamentRound|ReportMatchResult|DropFromTournament|EndTournament)\s*\{' crates/lobby-broker/src/broker.rs`
  remains useful only as a cross-check that the two agree.)
- **One of those 26 is inside a shared test-fixture builder: `fn started_event`** (round 4, m1 — the
  builder list previously named four and this is the fifth). It runs a full head-to-head event up to
  "round 1 paired" and is called by **8 distinct tests** in the same module. Its single
  `LobbyClientMessage::StartTournamentRound` construction is already one of the 26 coordinates above
  (`:2424` in the snapshot), so **the blanket instruction already covers it correctly and it needs no
  separate treatment** — this bullet exists only so the builder census is complete, not because anything
  changes. Its 8 callers pass `(conn, broker, env)` and pass **no variant literals of their own**, so the
  usual warning applies with extra force here: **edit the builder, do not sweep its callers.**

**Phase A's edit, and its strict limit:**

- The four dispatch arms bind the new field as **`request_id: _`** and pass nothing on. Phase A changes no
  behavior: the handlers keep their current signatures and the correlator is discarded. **Actually consuming
  it** — the `settle_gated` plumbing and the `handle()`-level `guard_inbound` correlation — remains
  `DEFERRED(Phase B)`, where those same four arms are rewritten to destructure it by name. Binding to `_` in
  A and to a name in B is not churn: it is the minimum edit that keeps the tree green under an additive
  contract, and it makes B's diff read as "start using what A put here."
- The 26 test sites each gain **`request_id: None`**. This is not stylistic and there is no shortcut:
  Rust enum struct-variants support neither `#[derive(Default)]` nor functional-update (`..Default::default()`)
  syntax, so every field must be named at every literal. `None` is the correct value — these tests assert
  broker behavior that is by construction identical for correlated and uncorrelated callers (V11 is the row
  that pins that identity), so an uncorrelated fixture is what they mean.
- **`fn error`, the four handlers' bodies, and every non-tournament path are untouched in Phase A.**

### 3A.7 Version pins

`client/src/adapter/ws-adapter.ts:442` → `5` (plus changelog prose in the surrounding doc block);
`scripts/check-protocol-version.mjs:10` → `5`; the `assert_eq!(LOBBY_PROTOCOL_VERSION, 4)` inside
`protocol.rs`'s **`lobby_protocol_version_is_independent_of_the_full_game_one`** (`:986`) → `5`. Plus the two
**new** pins from D8.2: `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK = 5` in `ws-adapter.ts` beside
`MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL`, and its bare-integer regex + expected-value check in
`check-protocol-version.mjs`.

**Same test, one more sentence, and it is load-bearing (round 2, m6).** Directly under that `assert_eq!`,
`:987-989` reads:

```rust
// Deliberately still 2, not 4: lobby versions 3 and 4 are purely
// additive, so a version-2 client parses every frame it already
// understood and is not evicted. See the constant's own changelog.
assert_eq!(MIN_SUPPORTED_LOBBY_PROTOCOL, 2);
```

Version 5 is purely additive too — that is exactly what probe A2 measured — so the enumeration must read
**"lobby versions 3, 4 and 5 are purely additive"** and the "not 4" must become **"not 5"**. This is not
cosmetic: this comment is the *in-source* statement of the very argument §D8.1 relies on to justify leaving
`MIN_SUPPORTED_LOBBY_PROTOCOL` and `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL` at 2. Letting it go stale undermines
the plan's own cited justification for a separate decision, in the one place a future reader would look.

`tournament_lobby_version_follows_the_format_config_bump` (`:1129-1133`) asserts the *tournament set* sits
exactly one bump past the `FormatConfig` bump — a premise that stops being true once correlation takes 5.
**Do not just retarget the number**: rename it to pin what it now means (the tournament surface spans lobby
versions 4 and 5) or retire it and let `lobby_protocol_version_is_independent_of_the_full_game_one` carry the
pin. A test whose name states a relationship it no longer checks is worse than no test.

### 3A.8 `lobby-worker/broker-wasm/src/lib.rs` — one test, and only that test (round 2, B1)

Revision 2's §3A.7 (as then numbered) **cleared this file as needing no change, which was wrong and actively harmful** — it
steered the executor away from a real compile break. Read at source in this revision, the file splits cleanly:

| Site | Shape | Needs the field? |
|---|---|---|
| `mutates_lobby` (`:99-116`) — the four gated arms at `:113-116` | already `LobbyClientMessage::StartTournamentRound { .. }` etc. | **No** — the rest pattern absorbs it, and the classification is unaffected (all four still write) |
| `OutboundDto` + `impl From<Outbound>` (`:60-81`) | matches `Outbound` *kinds*, never the `LobbyServerMessage` carried | **No** — the two new server variants ride through as payload |
| **`tournament_variants_are_classified_by_whether_they_write`** (`:308`) — the `mutating` array at `:309-340` | **full brace literals**, four gated variants at `:322`, `:326`, `:332`, `:336` | **YES — compile error.** Each gains `request_id: None` |

The test's own doc comment (`:302-306`) explains why it is written that way: *"Every variant is enumerated
explicitly rather than sampled, because there is no runtime symptom to catch a missed one."* That deliberate
exhaustiveness is precisely what makes it a compile dependency of this change.

**Everything else in the file genuinely does not change**, and that finding — revision 2's, independently
re-confirmed by round 2's own sweep and again here — stands.

#### 3A.8.1 How to actually check this crate — the command, third time (round 4, M1)

**This recipe has now been wrong in three different ways across three revisions**, each time in the same
class the plan itself names twice: *an instrument that reports clean because it never reached the input.*
Revision 2 cleared the file as needing no change at all. Revision 3 named `-p broker-wasm`, a package id that
matches nothing (the crate is workspace-`exclude`d). Revision 4 replaced it with a `--manifest-path` form
that round 4 **measured** as failing for **two independent reasons**. Both are properties of *how cargo
resolves context*, not of the code:

1. **Workspace resolution is by ancestor directory, and from a nested worktree it escapes the checkout.**
   Cargo walks up from the crate looking for a `[workspace]` root. `<worktree>/Cargo.toml` has one, and its
   `exclude = [… "lobby-worker/broker-wasm"]` excludes the crate — so cargo keeps walking, past
   `.claude/worktrees/`, and lands on the **outer** checkout's `C:\git\phase\Cargo.toml`, whose `exclude`
   paths resolve relative to *that* root and therefore do **not** cover the worktree's copy. Result, measured
   verbatim with `cargo locate-project --workspace`, before any type-checking happens:

   ```
   error: current package believes it's in a workspace when it's not:
   current:   C:\git\phase\.claude\worktrees\…\lobby-worker\broker-wasm\Cargo.toml
   workspace: C:\git\phase\Cargo.toml
   ```

   From a **top-level** checkout the same probe returns the crate's own manifest as the root and there is no
   error — so this failure is specific to running inside a nested worktree, which is exactly where this plan
   will be executed.
2. **`--manifest-path` does not pick up the crate's `.cargo/config.toml`, and that config is required.**
   `lobby-worker/broker-wasm/.cargo/config.toml` supplies
   `rustflags = ['--cfg', 'getrandom_backend="wasm_js"']` for `wasm32-unknown-unknown`. Cargo's config search
   is **cwd-based**, not manifest-based, so a `--manifest-path` invocation from the repo root silently drops
   it. This is not inference: the config file's own comment says *"Read only when cargo is invoked with this
   dir in its config search path (i.e. build from within `lobby-worker/broker-wasm/`)"*, and the crate's
   `Cargo.toml` flags the missing cfg as a hard failure on getrandom 0.3.2+. **`--manifest-path` is therefore
   wrong for this crate under every working directory**, nested worktree or not.

**Use this form. It works regardless of worktree nesting:**

```bash
cd lobby-worker/broker-wasm            # (1) cwd-based: picks up .cargo/config.toml's getrandom_backend cfg

cp Cargo.toml Cargo.toml.bak           # (2) stop cargo's ancestor search AT this crate.
printf '\n[workspace]\n' >> Cargo.toml #     Required in a nested worktree; harmless in a top-level checkout.

cargo check --target wasm32-unknown-unknown --all-targets   # (3) --all-targets reaches the inline test module

mv -f Cargo.toml.bak Cargo.toml        # (4) REVERT — non-negotiable. This file is not part of the change.
cd - && git status --porcelain         #     must show only the intended edits; `Cargo.toml` must NOT appear
```

Notes for the executor:

- **Step 2 is a temporary local edit and must never be committed.** An empty `[workspace]` table makes the
  crate its own workspace root, which is what stops the ancestor walk. Round 4 measured the effect directly:
  with it appended, `cargo locate-project --workspace` returns the crate's own manifest.
- **Step 4 is part of the recipe, not cleanup.** Verify with `git status --porcelain` before moving on.
- **Expected output, before the fix is applied:** exactly **four** `E0063` errors — one per gated variant in
  `tournament_variants_are_classified_by_whether_they_write` — and nothing else. Round 4 measured exactly
  that. Four-and-only-four is the reach-guard: it proves the command compiled the inline `#[cfg(test)]`
  module (an instrument that reported zero would be the same failure this section is about), and it matches
  §3A.8's site table site-for-site. After the fix, the command exits 0.
- **A `wasm32-unknown-unknown` target must be installed** (`rustup target add wasm32-unknown-unknown`).
  Use the same isolated `CARGO_TARGET_DIR` as §3A.9 — never the shared `C:/git/phase/target`.

### 3A.9 The completeness census — generated by the compiler, not by reading (round 3, B1)

**Why this section is now built differently.** Three consecutive review rounds found a blocking
compile-completeness gap of the identical class: a required consumer of the four modified
`LobbyClientMessage` variants missing from scope, in a file the plan's own prose had already listed as
covered or cleared. The defect was never carelessness in one pass — it was the instrument. A `rg` sweep and a
read-and-sample pass answer a **file**-level question ("which files mention these names?"), while the real
question is **site**-level ("which expressions stop compiling?"), and every missed file was already on the
plan's own in-scope list. A file-level instrument cannot close a site-level gap no matter how carefully it is
run. The only instrument that answers the actual question is `rustc`.

So this census was **generated by compiling**, not by reading. Method, reproducible verbatim:

```bash
# From the implementation worktree. NEVER the shared C:/git/phase/target.
export CARGO_TARGET_DIR="<scratchpad>/probe-target"

# 1. Add the field to the four gated variants in BOTH mirrors:
#      crates/lobby-broker/src/protocol.rs   (LobbyClientMessage)
#      crates/server-core/src/protocol.rs    (ClientMessage)
# 2. Let rustc enumerate every site:
cargo check --workspace --all-targets --message-format short 2>&1 | grep -E 'error\['
# 3. Absorb the *library*-level E0027 arms only, then re-run — a crate whose lib
#    fails to build hides its own test targets AND every downstream crate's sites.
# 4. Revert every temporary edit; confirm `git status --porcelain` is empty.
```

Step 3 is not optional and is the trap that makes a single run misleading: on the first pass `lobby-broker`'s
lib failed on four `broker.rs` arms and three `validation.rs` arms, and `server-core` and `phase-server`
therefore reported **zero** errors — a clean result that meant only "the dependency did not build."

**The completeness claim, stated in the durable form.** Not a file count, which goes stale the moment
anything moves:

> Phase A's scope covers **every construction and destructuring site of the four gated `LobbyClientMessage`
> variants and their `server-core` `ClientMessage` mirrors that exists in the cargo workspace**, as
> enumerated by `cargo check --workspace --all-targets` after the field is added (equivalently
> `cargo check -p lobby-broker -p server-core -p phase-server --all-targets`, which reaches the same set —
> see the reverse-dependency note below), plus the one workspace-**excluded** crate the check structurally
> cannot see (§3A.8).

That claim is re-verifiable at any commit by re-running the recipe. **The executor should re-run it rather
than trust the coordinates below**, which are a snapshot of one moment and will drift the instant another
agent edits a line above them.

**What the compiler returned — 71 sites in 5 workspace files:**

| File | `E0027` patterns | `E0063` constructions | Total | Section |
|---|---|---|---|---|
| `crates/lobby-broker/src/broker.rs` | 4 | 26 | **30** | §3A.6 |
| `crates/server-core/src/client_message_wire_guard.rs` | 6 | 9 | **15** | §3A.4 |
| `crates/phase-server/src/main.rs` | 4 | 8 | **12** | §3A.5 |
| `crates/lobby-broker/src/validation.rs` | 3 | 7 | **10** | §3A.3 |
| `crates/lobby-broker/src/protocol.rs` | 0 | 4 | **4** | §3A.1 |

Plus **4 sites in `lobby-worker/broker-wasm/src/lib.rs`** (§3A.8) which no workspace check reaches: that
crate is in the root `Cargo.toml`'s `exclude` list, so `-p broker-wasm` and `-p lobby-broker-wasm` both fail
with *"package ID specification … did not match any packages"* (measured — see the V20 correction). It is
checked **separately, by `cd`-ing into the crate** — **§3A.8.1 carries the exact command and is the single
authority for it**; a `--manifest-path` form does not work here for two independent measured reasons, so do
not substitute one. §3A.8's site table stands: it was independently confirmed correct by round 3.

**Reverse-dependency bound, so the per-crate recipe is provably not short.** Only three workspace crates
consume either enum: `lobby-broker` itself, `server-core` (its own mirror), and `phase-server`.
`manabrew-compat` matches a `grep` for these crate names only inside a comment; it was compiled and returned
clean, so the three-crate recipe and the `--workspace` recipe enumerate the same set. Every other workspace
crate is unreachable from these types.

**`DraftAction::ReportMatchResult` is a namesake, and the compiler settles it.** A `rg` sweep for
`(StartTournamentRound|ReportMatchResult|DropFromTournament|EndTournament)\s*\{` across `*.rs` returns 13
files. **Seven** are in scope (`lobby-broker/{protocol,validation,broker}.rs`,
`server-core/{protocol,client_message_wire_guard}.rs`, `phase-server/main.rs`, `broker-wasm/lib.rs`). The
other six — `crates/draft-core/src/{session,types,view}.rs`,
`crates/server-core/src/{harness,draft_session,draft_action_payload_guard}.rs` — are
`DraftAction::ReportMatchResult`, an unrelated enum that merely shares a name (7 + 6 = 13). This is no longer
a claim resting on reading the qualified paths: **none of those six files appears anywhere in the compiler's
output**, which is the strongest available evidence and the reason the `rg` census is now demoted to a
cross-check rather than the authority. (Round 3, m1: revision 3 said "nine" here while listing seven — the
total was right, the label was not.)

### 3A.9.1 Verified as needing NO change (measured, so the executor does not go looking)

`lobby-worker/src/lobby-do.ts` — `dispatchOutbound` switches on the `Outbound` kind alone and its own comment
says it is *"deliberately variant-agnostic … never on the `LobbyServerMessage` carried."* It is TypeScript,
so no Rust census could have covered it; it is read-verified and labelled as such.

`phase-server/main.rs`'s four `{ .. }` arms (`:1196`, `:1397`, `:5310`, `:9764`) and `broker-wasm`'s
`mutates_lobby` rest patterns absorb the field silently. Their all-clear is now **compiler-derived** (absence
from the error set) rather than read-derived — the one form of all-clear this plan is entitled to give after
§3A.8's history of a false one.

### 3A.10 Sizing — Phase A

**Units: 1** (U1, the correlated wire contract).

| Unit | Behavior | Registration surfaces | Discriminating test |
|---|---|---|---|
| **U1** Correlated wire contract | `TournamentRequestId`; `Option` field ×4; 2 server variants; server-core mirror; validation + wire-guard arms; native projection arms; `tournament_request_id()`; broker dispatch-arm + test-literal absorption; version bump + 3 moved pins + 2 new ack-floor pins | `protocol.rs` ×2, `validation.rs`, `client_message_wire_guard.rs`, `main.rs`, `broker.rs`, `ws-adapter.ts`, `check-protocol-version.mjs`, `broker-wasm/lib.rs` (test only) | **V1, V2, V3, V4, V13, V14, V19, V20, V21, V23** |

**Scope paths: 8** (test files and inline `#[cfg(test)]` modules excluded from the *count* per the counting
rule — but note the two caveats below, which matter to the executor):

```
crates/lobby-broker/src/protocol.rs                 crates/phase-server/src/main.rs
crates/lobby-broker/src/validation.rs               client/src/adapter/ws-adapter.ts
crates/lobby-broker/src/broker.rs                   scripts/check-protocol-version.mjs
crates/server-core/src/protocol.rs
crates/server-core/src/client_message_wire_guard.rs
```

**Round 3's B1 changed no path and no count.** All five files the compiler census named (§3A.9) were already
on this list; what was missing was *sites inside them*, not paths. Scope-paths stay at **8**, units at **1**,
and the two-phase split is untouched — stated explicitly so the orchestrator does not re-adjudicate.

**Three counting caveats, stated so the `SCOPE_PATHS` pathspec is not silently short:**
1. `crates/lobby-broker/src/broker.rs` is counted once. Both its non-test edit (four dispatch arms) and its
   inline `#[cfg(test)]` edit (26 literals) live in that one file.
2. **`lobby-worker/broker-wasm/src/lib.rs` is an in-scope Phase A path whose only edit is inside its
   `#[cfg(test)]` module** (§3A.8). It is therefore excluded from the count of 8 by the counting rule, but it
   **must still appear in `SCOPE_PATHS`** — the checkpoint pathspec is what the orchestrator commits, and a
   path missing from it is a change left behind, not a change not counted.
3. **Four of the eight counted files also carry inline `#[cfg(test)]` edits**, and none of them adds a path
   because each is already counted for its non-test edit: `protocol.rs` (4 literals, §3A.1), `validation.rs`
   (7, §3A.3), `client_message_wire_guard.rs` (9, §3A.4), `main.rs` (4, §3A.5) — plus `broker.rs`'s 26 from
   caveat 1. The count is unaffected; the **edit** is not, which is what §3A.9 exists to make un-missable.

**Phase-fit re-adjudication: does not fire, and not marginally.** T1 requires units ≥ 2 and Phase A is
**1 unit** — B1's correction adds mechanical absorption sites to U1's existing surface, not a second coherent
behavior (nothing in `broker.rs` or `broker-wasm/lib.rs` gains an independently-testable behavior in this
phase; V20 asserts *absence* of behavior change). T1 alone therefore fails the conjunction. T2 fails
independently as well at 8 < 13. **No further split.**

---

## 3B. Phase B — Broker settlement authority + client correlation

**Base.** Phase A's landed commit (`PHASE_BASE_SHA`), green.

**Goal.** Make the contract do something: mint correlated settlements in one broker authority, consume them
in the client, and land the maintainer's requested regression tests on both sides.

### 3B.1 `crates/lobby-broker/src/broker.rs` (U2)

- Add `ListRowEffect`, `GatedEffect`, `Broker::settle_gated` (D5).
- Convert `handle_start_tournament_round`, `handle_report_match_result`, `handle_drop_from_tournament`,
  `handle_end_tournament` to `Result<GatedEffect, String>`: each of the **14** `return vec![error(&reason)]`
  statements becomes `return Err(reason)`; each success tail becomes `Ok(GatedEffect { code, view, list_row })`.
- `list_row` is `ListRowEffect::Unchanged` **only** for `handle_report_match_result` — the one handler whose
  tail is today a one-element `vec![Outbound::ToSubscribers(…)]` (§D5/m2). Preserve its existing explanatory
  comment as that field's justification, since it now states a typed value rather than a convention.
- Dispatch arms destructure `request_id` and pipe through `settle_gated`.
- `handle()`'s `guard_inbound` call takes the correlated form (D6), consuming Phase A's
  `tournament_request_id()`.
- `fn error(&str)` is untouched — every non-tournament path keeps today's exact bytes.

### 3B.2 `client/src/services/tournamentClient.ts` (U3)

- Module-private `nextRequestId` counter (D7).
- `matchAck(requestId)`, and a correlated-rejection branch in `requestOver`.
- The four helpers send `request_id` and await the ack; the capability gate (D8/D8.2/D8.3) short-circuits to
  `"unsupported"` when `socket.serverInfo.lobbyProtocolVersion` is `undefined` **or**
  `< MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK`, imported as a value from `../adapter/ws-adapter`. **Never write
  the literal `5` here, and never write `< LOBBY_PROTOCOL_VERSION`** — D8.2 states why the second is a real
  latent bug rather than a style preference.
- `TournamentRpcFailureReason` gains `"unsupported"`, with a doc line matching the existing four members'
  form. Per D8.1 it is a wire member; the doc should record *why* — the frame is sent, and the version is a
  broker-advertised fact — so the boundary argument survives in the source rather than only in this plan.

#### 3B.2.1 Doc-comment scope: every stale cross-reference, enumerated (round 2, M2)

Revision 2 scheduled exactly two header edits and left the rest of the file's cross-references to go stale —
including the doc comments on the four functions the maintainer's review is actually about. Read at source,
`tournamentClient.ts` carries **eight** cross-references to its module-header parts, plus the header's own
five parts. Every one is classified below; the discipline is the one already established elsewhere in this
plan — **preserve what is still accurate, change only what this fix makes false.**

| Site | Text today | Verdict |
|---|---|---|
| Header **part 3** (`:46-54`) | *"Four of the seven RPCs get no point reply at all … an unsubscribed caller never observes success and will settle `"timeout"` instead."* | **EDIT — becomes false.** D2's ack *is* a `ToSelf` point reply for all four, and V10 is the row that tests exactly this. Revision 2's own D2 claimed this fix "incidentally repairs part 3" and never scheduled the edit. Rewrite: the four still produce no `TournamentUpdate` point reply, but a correlated caller now receives `TournamentActionAck` `ToSelf`, so subscription is no longer required to observe success; an **uncorrelated** caller (pre-correlation client, or `request_id: None`) still sees the old behavior |
| Header **part 4** (`:56-79`) | the provenance limitation; *"Every candidate client-side fix … would fabricate provenance the broker never sent"* | **REWRITE**, as revision 2 specified: describe the correlated mechanism, retain the historical reasoning as *why a client-only fix was refused* (it remains true and is why the fix is on the wire), and add D6's disclosed trade in D6's terms — the parse/validation boundary's designed fast-fail (`reject_reply`) no longer reaches a correlated caller, which settles by timeout instead. Also update its closing directive (`:77-79`: *"must not treat `{ok: false}` from a gated helper as a complete rejection detector"*), which is exactly the claim this fix falsifies for correlated callers |
| Header **part 5** (`:81-89`) | *"An `Error` frame therefore settles every RPC in flight on this socket"* | **NARROW** to the three uncorrelated helpers, where it stays exactly true. Per m1, describe `getTournamentOver` as **exposed but benign**, not "never exposed" |
| `:200` inline | *"// Unfiltered by design — see the module header, part 5."* | **EDIT — sits directly above the `if (msg.type === "Error")` block this fix makes conditional.** It must now say that the unfiltered `Error` path is the *uncorrelated* path, and that a correlated request deliberately ignores a bare `Error` (D7's reasoning: an uncorrelated `Error` provably belongs to *some* request but not provably ours, and settling on it is the mirror-image false negative) |
| `matchReply` doc `:268-271` | *"The `code` conjunct discriminates **tournaments, not requests** … see the module header, part 4"* | **PRESERVE, extend by one clause.** Still exactly true of `matchReply`, which the three uncorrelated helpers keep. Add a pointer to `matchAck` as the correlated sibling so the reference resolves to the rewritten part 4 correctly |
| `matchReply` doc `:278-281` | *"it cannot and does not address part 4's provenance limitation"* | **PRESERVE, extend by one clause.** Still true of `matchReply` itself; note that `matchAck` is what now addresses it |
| `startTournamentRoundOver` `:385-387` | *"No point reply exists: this settles on the `TournamentUpdate` broadcast, so it is subject to the same-code provenance limitation in the module header, part 4."* | **EDIT — false after this fix** |
| `reportMatchResultOver` `:407-409` | *"No point reply exists: settles on the `TournamentUpdate` broadcast, subject to the module header's part 4 limitation."* | **EDIT — false after this fix** |
| `dropFromTournamentOver` `:436-438` | same sentence | **EDIT — false after this fix** |
| `endTournamentOver` `:455-457` | same sentence | **EDIT — false after this fix** |
| `subscribeTournamentsOver` `:493` | *"See the module header, part 2 — the shared `SubscribeLobby` reference count is the socket owner's"* | **NO CHANGE.** Part 2 is untouched by this fix; verified by reading both |

The four helper docs take the same replacement shape, which should be written once and reused: a correlated
`TournamentActionAck` settles this call, so it is no longer subject to part 4's provenance limitation; against
a broker below `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` the frame is still sent and the call settles
`"unsupported"` (D8(b)), which is **not** a statement that the action failed.

The header preamble's *"Five properties of this module are deliberate and load-bearing"* (`:17`) **stays at
five** — no part is added or removed, three are rewritten in place.

- **Wording constraint carried forward from phase 1, re-verified at source in this revision:** the static
  source-assertion tests in section F of `tournamentClient.test.ts` (the `describe("tournamentClient
  source-level boundaries")` block at `:734`, running to the end of the file at `:785`) run against raw file
  text and are comment-unaware. New prose must not contain a literal `.close(`, `openPhaseSocket(`, or
  `send(…Subscribe/UnsubscribeLobby`. Two further pins in that same block that the rewrites must not break:
  the file must **still contain** the bare word `UnsubscribeLobby` somewhere (a positive control,
  `expect(SOURCE).toContain("UnsubscribeLobby")` at `:767` — re-verified accurate), and the exact line
  `import type { PhaseSocket } from "./openPhaseSocket";` must survive verbatim (the regex assertion that
  closes `it("never acquires a socket of its own")`, at **`:783`**) — so the new value import from
  `../adapter/ws-adapter` is added as a *separate* import statement and that line is left untouched.
  *(Round 3, m2: revision 3 cited `:786` and a `:734-789` range, both introduced while fixing round 2's M2;
  the file is 785 lines long, so `:789` did not exist. Keyed to the enclosing `it(...)` name here so the next
  edit above it cannot falsify the reference — the durable form §0.1 mandates.)*

### 3B.3 `client/src/adapter/types.ts` (U3)

Add `TournamentActionAckReply` / `TournamentActionRejectedReply` beside the existing tournament reply
interfaces, each citing its Rust source symbol (D13).

### 3B.4 `client/src/pages/tournamentPageState.ts` (U3, from B1)

Add the `FailureLabel` member, the `failureLabel` arm, and **all four ordinal repairs** — the three in
`failureLabel`'s own doc comment plus the one in `tournamentPageState.test.ts:450` — exactly as tabulated in
D12 items 1-3, including D12's explicit instruction **not** to touch `tournamentPageState.ts:25`.

### 3B.5 The seven locale catalogs (U3, from B1)

Add `errors.unsupported` to all seven catalogs, **in this same commit** (D12 item 4):

```
client/src/i18n/locales/en/tournament.json          client/src/i18n/locales/it/tournament.json
client/src/i18n/locales/de/tournament.json          client/src/i18n/locales/pl/tournament.json
client/src/i18n/locales/es/tournament.json          client/src/i18n/locales/pt/tournament.json
client/src/i18n/locales/fr/tournament.json
```

English is the source; the other six are translations of it. What forces all seven is the **unconditional
bidirectional key-parity check** at `localeParity.test.ts:282-290`, not the placeholder machinery — see
D12 item 4 for the corrected mechanism. No `KNOWN_PLACEHOLDER_GAPS` entry may be added: that list is a
register of known defects, not an exemption mechanism, it is consulted only by the *placeholder* check, and
this key introduces no placeholder to drop.

### 3B.6 `client/src/stores/multiplayerStore.ts` (U3, doc only)

**Still doc-only, and that is re-confirmed rather than assumed** — `GatedTournamentRpcResult<T> =
TournamentRpcResult<T> | TournamentNotAuthorized`, so widening `TournamentRpcFailureReason` widens the gated
result through the existing alias with no store code change; and the store's *behavior* (never mutating state
on a gated failure) is unchanged. But revision 2 scoped **one** comment where the file has **two**, and the
second is the more consequential (round 2, M1). Both, read at source:

**(a) `TournamentNotAuthorized`'s doc (`:374-390`)** — as revision 2 specified: the *"each of its **four**
members"* count at `:378`, and one sentence recording that `"unsupported"` joined the wire union on the
*was-anything-sent* axis while `not_authorized` still does not. The *"because that file is frozen by the time
this store is written"* ground at `:388-389` is now void (D8.1 ground 4) and should be recorded as lapsed
rather than left to be applied by a future reader as if it still held.

**(b) `runGatedTournamentRpc`'s doc (`:443-467`) — three claims this fix directly falsifies:**

| Line | Claim today | After this fix |
|---|---|---|
| `:458-460` | *"any `TournamentRpcFailureReason` — decided by the transport or the broker. Note in particular that `"rejected"` inherits the caution below and is **NOT a reliable "the server refused me" signal**."* | **False.** `"rejected"` is now minted *only* from a correlated `TournamentActionRejected` carrying this caller's own id (D7). It becomes exactly a reliable server-refusal signal — the single most consequential behavioral consequence of this whole change, and the store's own doc would go on denying it |
| `:462-464` | *"Caution for consumers (`services/tournamentClient.ts`, module header part 4): the four gated RPCs settle on a `TournamentUpdate` BROADCAST, which carries no request-vs-broadcast discriminator, so a wire-level `{ok:false}` here is not a reliable 'the server rejected me' signal."* | **False**, and its cross-reference points at a part 4 that §3B.2.1 rewrites. Both the claim and the pointer must be corrected together, or the store cites a header section that no longer says what the citation assumes |
| `:465-466` | *"Nothing in this store mutates state on a gated failure **for exactly that reason**."* | The behavior is **unchanged and correct**; only its stated *justification* dies. Keep the sentence, replace the "for exactly that reason" clause — the store still does not mutate on failure, now as a layering choice rather than as compensation for an unreliable signal |

**The replacement caution is not "delete the caution" — it is a different, real one.** The new
`"unsupported"` member means a gated `{ok:false}` can now say *"the frame was sent and the broker very likely
performed the action; this client just cannot confirm it"* (D8(b)). That is the residual thing a consumer must
not misread as failure, and it is what the corrected paragraph should warn about. The other four wire reasons
keep their existing meanings verbatim.

Round 2 additionally endorsed writing this plan's **reformulated boundary axis into the source** while these
comments are open: the discriminator the union actually draws is *whose fact the predicate reads*, not *who
evaluated it* (§D8.1 ground 3). One sentence in (a) is the right home for it.

### 3B.7 Test-harness fix (D14)

`client/src/services/__tests__/tournamentClient.test.ts`'s `makePhaseSocket` default `serverInfo` gains
`lobbyProtocolVersion` set from the client's `LOBBY_PROTOCOL_VERSION` export. This must land **with** the
gate, not after it, or the file's existing gated-helper tests change meaning silently.

**D14's "reference the constant, not a literal" instruction is scoped to THIS site and no other.** It is
correct here because the harness models *a current-generation broker*, which is by definition whatever the
client currently speaks. It is wrong at the capability gate, where the threshold is a frozen floor — see
D8.2. The two literals look identical today (both are 5) and diverge at the next bump; that is precisely why
each is written against a different constant.

### 3B.8 Sizing — Phase B

**Units: 2.**

| Unit | Behavior | Registration surfaces | Discriminating test |
|---|---|---|---|
| **U2** Broker settlement authority | `ListRowEffect` / `GatedEffect` / `settle_gated`; 4 handlers → `Result`; correlated `guard_inbound` | `broker.rs` | **V5**, V10, V11, V12 |
| **U3** Client correlation + capability gate + failure-reason wiring | mint id; `matchAck`; correlated rejection; `"unsupported"`; consume `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK`; `failureLabel` arm; 7 locale keys; the full §3B.2.1 doc-edit set; ordinal repairs; harness default | `tournamentClient.ts`, `types.ts`, `tournamentPageState.ts`, 7× `tournament.json`, `multiplayerStore.ts` (doc) | **V6**, V7, V8, V9, V15, V16, V17, V18, V22 |

**Dependency edge:** both depend on Phase A. U2 ∥ U3 (independent of each other; U3's end-to-end value
depends on U2, which is why they share a phase).

**Scope paths: 6 grouped / 12 ungrouped.** The counting rule groups translation mirrors with their authored
source as one path, so the six non-English catalogs group with `en/tournament.json`. Paths are enumerated
literally rather than in prose shorthand (round 2, m4) — this list is the `SCOPE_PATHS` the orchestrator's
pathspec machinery consumes, and *"(+6 mirrors)"* is not a path:

```
crates/lobby-broker/src/broker.rs
client/src/adapter/types.ts
client/src/services/tournamentClient.ts
client/src/pages/tournamentPageState.ts
client/src/stores/multiplayerStore.ts                (doc only)
client/src/i18n/locales/en/tournament.json           ┐
client/src/i18n/locales/de/tournament.json           │
client/src/i18n/locales/es/tournament.json           │ grouped as ONE path
client/src/i18n/locales/fr/tournament.json           │ (translation mirrors +
client/src/i18n/locales/it/tournament.json           │  their authored source)
client/src/i18n/locales/pl/tournament.json           │
client/src/i18n/locales/pt/tournament.json           ┘
```

*(+ `broker.rs`'s inline `#[cfg(test)]` module; `client/src/services/__tests__/tournamentClient.test.ts`;
`client/src/pages/__tests__/tournamentPageState.test.ts` — test files, excluded from the count.)*

**Phase-fit re-adjudication: does not fire.** T1 fires (2 units) but T2 requires ≥ 13 scope-paths; Phase B is
6 grouped, 12 even counting every catalog separately. The conjunction is not met. No further split.

**Verified as NOT in scope, measured:** `lobby-worker/src/lobby-do.ts` and
`lobby-worker/broker-wasm/src/lib.rs` (its non-test surface only — variant-agnostic outbound routing and `mutates_lobby`'s rest patterns, §3A.8/§3A.9; its one test IS in Phase A scope);
`client/src/pages/TournamentPage.tsx` and `client/src/pages/TournamentLandingPage.tsx` (both render
`FailureLabel` structurally via `"message" in failure`, never by key switch — D8.1 ripple analysis).

---

## 4. Verification Matrix

Every negative row names its paired positive reach-guard, per the mandatory rule.

**Deferral vocabulary, stated once so §4 and §6 cannot appear to disagree (round 2, m3).** Every row below is
filed under the phase that lands it, and **no row is deferred without a named landing phase** — the sense in
which this matrix has no open deferrals. Separately, §6's deferral list is the Phase-A-relative view of the
same fact: from Phase A's vantage the Phase B rows are `DEFERRED(Phase B)`, because they cannot be written
until the behavior they test exists. The two statements are the same partition read from two directions.
Concretely: **Phase A's ten rows (V1, V2, V3, V4, V13, V14, V19, V20, V21, V23) are writable and runnable inside
Phase A; Phase B's rows (V5-V12, V15-V18, V22) are `DEFERRED(Phase B)` from Phase A's perspective and land
there.**

### Phase A rows

| # | Claim | Seam | Test (file) | Revert-failing assertion | Hostile / negative | Reach-guard |
|---|---|---|---|---|---|---|
| V1 | Old frame → new broker parses, uncorrelated | `parse_lobby_client_message` | `protocol.rs` tests | v4-shaped `StartTournamentRound` JSON → `request_id: None` | required-field variant errors (probe A5 shape) | correlated frame in same test → `Some` |
| V2 | Correlated frame round-trips | serde | `protocol.rs` tests | all four variants + both new server variants round-trip byte-identically | `request_id: None` serializes **without** the key (A4) | `Some` case emits the key |
| V3 | Every client tag still known | `is_known_lobby_tag` | existing `every_client_variant_tag_is_known` | correlated representative frames parse to `Message` | existing `an_invented_tournament_tag_is_still_unknown` stays red-on-removal | — |
| V4 | Neither new variant can leak a token | `TournamentActionAck` | extend `broadcast_tournament_messages_never_carry_a_token` | serialized bytes contain no `*_SECRET` | ack built from the token-bearing `meta_fixture` | asserts the ack really carried `Alice`/`Friday Night` |
| V13 | Cross-language version pin | `check-protocol-version.mjs` | CI | `node scripts/check-protocol-version.mjs` exits 0 with all pins at 5 | flipping any one pin back to 4 exits 1 | baseline exit 0 measured at HEAD (probe P2) |
| V14 | Native ↔ lobby projection carries the correlator | `to_lobby_client_message` | `main.rs` tests | the serialized-equality assertion passes with `request_id` populated | the `messages.len()` count in `tournament_server_variants_survive_the_canonical_lobby_roundtrip` moves 5 → 7 | its "every new server variant is covered" assertion is what forces it |
| V19 | `tournament_request_id()` is total and correct | `LobbyClientMessage::tournament_request_id` | `protocol.rs` tests | each of the four gated variants returns its `Some(id)` | a non-gated variant (`SubscribeLobby`, `GetTournament`) returns `None` | the same test asserts a gated variant with `request_id: None` also returns `None`, so `None` is not a blanket answer |
| **V20** | **The mechanical absorption sites are complete and behavior-neutral (B1)** | `Broker::handle` dispatch; the **five** fixture builders (`report_with`, `started_event`, `oversized_tournament_frames`, `valid_tournament_frames`, `tournament_client_frames` — round 4, m1 added the second); `to_lobby_client_message`; `mutates_lobby` | existing `broker.rs` / `validation.rs` / `client_message_wire_guard.rs` / `protocol.rs` / `main.rs` tests + existing `tournament_variants_are_classified_by_whether_they_write` | **`cargo check --workspace --all-targets` exits 0** in the isolated target dir — this is the same command §3A.9 used to *generate* the site list, so a green run is a direct statement that the list was consumed completely. **`broker-wasm` is checked separately, by the `cd` + temporary-`[workspace]` recipe in §3A.8.1** — it is workspace-`exclude`d, so `-p broker-wasm` fails with *"did not match any packages"*, **and** a `--manifest-path` form fails too (nested-worktree ancestor resolution + a dropped `.cargo/config.toml` rustflags cfg), both measured in round 4. §3A.8.1 is the authority for the command; do not substitute a `--manifest-path` variant. **And** every pre-existing tournament test across all five files still passes **unchanged in its assertions** — only a `request_id` field was added to fixtures (`None` at every site but the one V23 names). Behavior neutrality is the claim; a green suite whose expectations did not move is the evidence | `--all-targets` is load-bearing: without it none of the five files' inline `#[cfg(test)]` modules compiles at all, and 46 of the 71 sites would be invisible again. Second reach-guard, and the one round 3 proved matters: a `--workspace` run whose *library* targets fail reports **zero** errors in every downstream crate, so "no errors in `server-core`" is only meaningful once `lobby-broker`'s lib is green (§3A.9 step 3) | `mutates_lobby` still returns `true` for all four gated variants after the field is added (the existing test's own assertion), so the rest pattern absorbed the field without changing the classification; and `to_lobby_client_message`'s round-trip test still passes with the correlator **forwarded**, which is the one non-`_` absorption in Phase A (§3A.5) |
| **V23** | **The native projection FORWARDS the correlator rather than discarding it — and the field sits at the same position in both mirrors (round 4, M2)** | `to_lobby_client_message`'s `StartTournamentRound` arm; the `request_id` field's declaration position in `LobbyClientMessage` (§3A.1) and `ClientMessage` (§3A.2) | **`tournament_variants_survive_the_canonical_lobby_roundtrip`** (`crates/phase-server/src/main.rs`) — **existing test, zero new tests**; the only change is one fixture literal in `tournament_client_frames`, which takes `request_id: Some(TournamentRequestId(7))` | **Revert the `request_id: *request_id` forward in that arm of `main.rs`'s projection — write `request_id: _` on the pattern and `request_id: None` on the construction (which compiles cleanly) — and this test reds** with its own *"field dropped or renamed across the projection"* message. **Second revert-check on the same row:** move `request_id` to a different relative field position in one mirror only; serde emits fields in declaration order, so the two serialized strings diverge and the test reds immediately. Under the old `None`-everywhere fixture **both** reverts passed silently | The other six frames in `tournament_client_frames()` stay uncorrelated: the three non-gated variants have no such field, and the three remaining gated frames keep `request_id: None`, so the test still proves an **uncorrelated** frame round-trips unchanged (D4/probe A1's honesty requirement) in the same pass that proves a correlated one does | The vacuity this row removes is the reach-guard argument itself: `skip_serializing_if = "Option::is_none"` means a `None` fixture serializes **identically** whether forwarded or discarded, so every assertion touching the field passed for the wrong reason. `Some(..)` is what makes the instrument fire at all. Companion positive: the test's own `assert_eq!(frames.len(), 7)` and its `unwrap_or_else` panic-on-`None` already prove every frame reached the projection |
| **V21** | **The ack floor is pinned and structurally cannot be re-derived** | `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK`; `check-protocol-version.mjs` | CI | `node scripts/check-protocol-version.mjs` exits 0 with the constant at 5 | rewriting it as `= LOBBY_PROTOCOL_VERSION` (or any expression) makes the bare-integer regex fail to match and the script throws *"Could not find protocol version"* rather than passing — the executor must confirm this once by making the edit, observing the failure, and reverting. This is the D8.2 latent bug's tripwire | changing the literal to `4` or `6` exits 1 with the frozen-floor message, proving the check reads *this* constant and not another |

### Phase B rows

| # | Claim | Seam | Test (file) | Revert-failing assertion | Hostile / negative | Reach-guard |
|---|---|---|---|---|---|---|
| **V5** | **THE MAINTAINER'S REGRESSION (broker, multi-client)** | `settle_gated` | `broker.rs` tests | Two `ConnState`s on one `Broker`. Alice reports pairing 1 (correlated) → her outbounds contain a `TournamentActionAck` with **her** id. Bob then sends a correlated `EndTournament` with a **bad organizer token** → Bob's outbounds contain `TournamentActionRejected` with **Bob's** id and **no** ack, while Alice's earlier ack id appears nowhere in them | a valid `StartTournamentRound` from the true organizer in the same fixture produces an ack, not a rejection | the fixture's rejection message is asserted non-empty and the tournament state is asserted **unchanged** after the refusal |
| **V6** | **THE MAINTAINER'S REGRESSION (client)** | `matchAck` | `tournamentClient.test.ts` — **invert** the existing `"a foreign same-code broadcast settles a gated helper (B6)"` group | For each of the four helpers: deliver a same-code `TournamentUpdate` with `FOREIGN_VIEW` → `settledOrPending` is `"pending"` **and** `listenerCount("message") === 1`; then deliver `TournamentActionRejected` with our id → `{ok:false, reason:"rejected"}` and `listenerCount === 0` | an ack carrying a **different** `request_id` also leaves it pending | deliver an ack with **our** id → `{ok:true}`, `listenerCount === 0` |
| V7 | A bare `Error` no longer settles a correlated request | `requestOver` | `tournamentClient.test.ts` | correlated helper + bare `Error` → still pending, listener still 1 | — | the same `Error` **does** still settle `getTournamentOver` (part 5 preserved for the three) |
| V8 | Pre-correlation broker fails closed | capability gate | `tournamentClient.test.ts` | `makePhaseSocket(ws, { lobbyProtocolVersion: 4 })` → `{ok:false, reason:"unsupported"}`, and a subsequent same-code `TournamentUpdate` does **not** flip it to `{ok:true}` | explicit `{ lobbyProtocolVersion: undefined }` override behaves identically (D8.3) | the file's **new default** (`lobbyProtocolVersion: LOBBY_PROTOCOL_VERSION`) on the same helper reaches the correlated path — this is what makes the `undefined` row non-vacuous (D14) |
| V9 | The frame still goes out under D8(b) | capability gate | `tournamentClient.test.ts` | `ws.send` called exactly once with the `StartTournamentRound` tag even at v4 | — | asserts the parsed sent payload, not just the call count |
| V10 | Unsubscribed caller now observes success | ack carries `view` | `broker.rs` tests | an organizer who never sent `SubscribeLobby` still receives the `ToSelf` ack | the `ToSubscribers` broadcast is still emitted alongside | the ack's `view` equals the broadcast's |
| V11 | Uncorrelated callers are bit-for-bit unchanged | `settle_gated(None, …)` | `broker.rs` tests | `request_id: None` on all four → outbound `Vec` **equal** to the pre-change shape (the three two-element tails, and report-result's single-element form) | the `Err` path yields a bare `Error`, not a rejection variant | the `Some` case in the same test yields three/two elements incl. the ack |
| V12 | `ListRowEffect` preserves the report-result asymmetry | `settle_gated` | `broker.rs` tests | report-result emits **no** `TournamentListUpdate`; the other three do | — | all four assert their `TournamentUpdate` **is** present |
| V15 | Static source boundaries survive the header rewrite | section F | `tournamentClient.test.ts` | all three regexes still find nothing in the rewritten file | their positive controls still match their sample strings | — |
| **V16** | **`failureLabel` covers the new reason (B1's compile gate)** | `failureLabel` | `tournamentPageState.test.ts` | `failureLabel({ok:false, reason:"unsupported", message:"…"})` → `{ key: "errors.unsupported" }` | **removing the new arm must fail the build** at `const unreachable: never = failure.reason` — a real compile-time revert-check, not a runtime one; the executor must confirm this by deleting the arm once and observing the type error before restoring it | the same test asserts an existing reason (`"timeout"` → `errors.timedOut`) still maps, so the harness is not merely accepting anything |
| **V17** | **Locale parity holds across all seven catalogs** | i18n catalogs | `localeParity.test.ts` (existing, no change) | suite green with `errors.unsupported` present in all seven | deleting the key from **any one** non-English catalog fails the suite (bidirectional parity, `KNOWN_PLACEHOLDER_GAPS` empty); adding it to `en` alone fails too | measured baseline: the suite is green at HEAD with the current seven-catalog `errors` block, so a failure after this change is attributable to this change |
| V18 | The harness default no longer masks the gate | `makePhaseSocket` | `tournamentClient.test.ts` | with the default at `LOBBY_PROTOCOL_VERSION`, the pre-existing gated-helper tests still exercise real pending-request behavior (they do not settle `"unsupported"`) | — | V8's explicit `{lobbyProtocolVersion: 4}` row still reaches the unsupported path from the same helper, proving the override survived the default change |
| **V22** | **The capability gate is a FLOOR, not an equality — it admits every version at or above the ack's introduction (D8.2/M4)** | the gate in `tournamentClient.ts` | `tournamentClient.test.ts` | Three fixtures on the same gated helper: `{lobbyProtocolVersion: 5}` **reaches the correlated path** (stays pending after send, then settles on a correlated ack) and `{lobbyProtocolVersion: 4}` does **not** (settles `"unsupported"`) | **The row that matters most: `{lobbyProtocolVersion: 6}` — a hypothetical future broker — must ALSO reach the correlated path.** This is the assertion that fails if the threshold is ever written as `< LOBBY_PROTOCOL_VERSION`, and it fails *today*, at the moment of the mistake, rather than silently at the next protocol bump. It is the whole point of the row | the `5` fixture's positive settle proves the correlated path is genuinely reachable in this harness, so the `4` negative is not measuring a broken instrument; and V21 independently pins the constant's value cross-language |

**Non-vacuity note on V6.** The existing B6 group is currently a *characterization* test asserting the bug
(`expect(result.ok).toBe(true)` on a foreign view). Inverting it is the strongest available revert-check: if
correlation regresses, the inverted assertions fail immediately. Extend the existing `it.each` from two
helpers to all four while inverting.

**Multi-actor fixture — compose, don't invent** (per "build from building blocks"):
- **Rust (V5)** is the true multi-client test, and the pattern already exists: `broker.rs` has
  `a_second_connection_never_sees_another_organizers_token` (`organizer` + `watcher` `ConnState`s on one
  `Broker`) and `join_tournament_rejects_duplicate_player_key` (`host`/`alice`/`impostor`), plus
  `make_tournament` / `join_tournament` / `view_of` / `error_reason` / `outbounds_contain` helpers. Extend
  that pattern; do not build a new harness.
- **TypeScript (V6)** needs no second socket, and this is worth stating because it looks like a gap:
  a browser client only ever holds **one** socket, so "another participant" manifests *precisely* as a
  foreign frame arriving on our own socket — which `MockWebSocket.deliver()` already models exactly.
  `makePhaseSocket(ws, Partial<ServerInfo>)` already supports the V8 version override, and
  `listenerCount("message")` already exists as the leak detector.

**Baselines measured before any edit** (probe P3):
`npx vitest run src/services/__tests__/tournamentClient.test.ts src/stores/__tests__/multiplayerStore.tournament.test.ts`
→ **2 files, 98 tests, all passing**. `node scripts/check-protocol-version.mjs` → exit 0. Phase B additionally
depends on `localeParity.test.ts` being green at its base, which it is at HEAD.

**Rust verification note.** Tilt is **not installed** in this environment (`tilt` is absent from PATH; the
`tilt get uiresource clippy` detection exits 127, i.e. *cannot answer*, **not** a build failure). A `rustc`
process holding ~11 GB was observed against the shared `C:/git/phase/target`, so the executor must use an
isolated `CARGO_TARGET_DIR` for `-p lobby-broker -p server-core` checks and must not compete for the shared
lock. Reuse one isolated target dir across both phases rather than recreating it. `cargo fmt --all` still runs
directly.

---

## 5. Identity / Provenance Contract

| Field | Value |
|---|---|
| **Source concept** | "the broker's answer to **this** request", as distinct from "a change to this tournament" |
| **Authority type / value** | `TournamentRequestId(u64)`, minted by the client, opaque to the broker |
| **Binding time** | At `ws.send()`, synchronously, before the listener could observe anything |
| **Live vs snapshotted** | **Snapshotted.** The id is captured in the request closure and never re-read from mutable state — an in-flight request cannot have its correlator changed underneath it |
| **Storage** | Client: the `requestOver` closure only. Broker: **nowhere** — read off the frame, echoed, discarded. It is deliberately not persisted into `TournamentMeta`, `ConnState`, or the DO snapshot, so it cannot become a second authority or a replay/idempotency key it was never designed to be |
| **Consumer** | `matchAck(requestId)` (client); `Broker::settle_gated` (broker) |
| **Invalidation** | On any terminal path in `requestOver` (`cleanup()`), and implicitly at socket close. A reconnect mints fresh ids; a late ack for a dead request matches no listener and is inertly dropped |
| **Multi-authority hostile fixture** | **V5** — two `ConnState`s acting on one tournament, each with its own correlator, where the second actor's refusal must carry *its* id and never the first actor's ack id. **V6** — a foreign same-code `TournamentUpdate` and a wrong-id ack, both of which must leave the promise pending |

**What the correlator deliberately does NOT confer.** It is not an idempotency token: replaying the same
`request_id` re-executes the action. The broker is stateless with respect to it, exactly like
`PreviewManaPayment`'s. Authority remains the `organizer_token`/`player_token` — the correlator identifies a
*request*, never a *requester*, and must never be read as permission. This belongs in the doc comment.

This is also why D8(b) is safe without the correlator doing idempotency work: as round 1 established, each of
the four actions already carries its own server-side guard against a repeat, so an unconfirmed retry is
handled by the action's own logic and not by the correlation layer. Two separate mechanisms, deliberately not
conflated.

---

## 6. Sizing (whole task, and the phase-fit adjudication)

**Units: 3** (U1 in Phase A; U2 and U3 in Phase B). A unit = one coherent behavior implementable by a single
skill-checklist pass, regardless of how many layers it touches in lockstep. Per-phase unit tables are in
§3A.10 and §3B.8.

**Scope-path count and why the conjunction fires.** Revision 1 reported 10 non-test paths and concluded the
T2 threshold (≥ 13) was not reached. That count omitted everything D12 and D14 add. Recounted:

| Counting convention | Phase A | Phase B | Total | T2 (≥13)? |
|---|---|---|---|---|
| Every locale catalog counted separately | **8** | 12 | **20** | **fires** |
| Translation mirrors grouped with their source, per the counting rule | **8** | 6 | **14** | **fires** |

Phase A gains one path over revision 2 (`crates/lobby-broker/src/broker.rs`, round 2's B1); its second B1
file, `lobby-worker/broker-wasm/src/lib.rs`, is test-only and excluded from the count while remaining in
`SCOPE_PATHS` (§3A.10). Round 1 reported 18 **by the ungrouped axis** — the row above where every locale
catalog is counted separately, now 20; the deltas since are the doc-only `multiplayerStore.ts` path
(revision 2) and `broker.rs` (revision 3), and 18 + 2 = 20 is the arithmetic that identifies which axis it
was. *(Round 3, m4: revision 3 labelled that 18 "grouped", where the corresponding figure would be 12.)*
**Both conventions fire T2**, and T1 fires at 3 units, so the conjunction holds under every reading. The
split is not a judgment call.

**Round 3's B1 does not move any number in this table.** All five files its compiler census named were
already scope paths; it added sites inside them, not paths. Phase A stays at 8, Phase B at 6/12, the totals
at 14/20, units at 3.

**Neither phase re-trips the conjunction** — Phase A is **1 unit** (T1 fails; it also fails T2 independently
at 8 < 13), Phase B is 6/12 paths (T2 fails). The recursion terminates at two phases, and round 2's B1
correction does not disturb that: it adds mechanical absorption sites to U1's existing surface rather than a
second coherent behavior.

**Deferral list (Phase A → Phase B), explicit.** Read with §4's deferral-vocabulary note: these are the
things Phase A intentionally omits, each attributed to the phase that lands it — none is deferred without a
named target.
- `settle_gated`, `GatedEffect`, `ListRowEffect`, and the four handler conversions — `DEFERRED(Phase B)`.
- The `tournament_request_id()` **call site** in `Broker::handle` — `DEFERRED(Phase B)`. The function itself
  lands in A and is tested there (V19). Phase A's four dispatch arms bind `request_id: _` and use nothing.
- The **consumer** of `MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` — `DEFERRED(Phase B)`. The constant and its
  cross-language pin land in A (V21).
- All client consumption: `matchAck`, the correlated-rejection branch, the capability gate, `"unsupported"`,
  the `failureLabel` arm, the seven locale keys, the §3B.2.1 doc-edit set, the `multiplayerStore.ts`
  doc corrections, the ordinal repairs, the harness default — `DEFERRED(Phase B)`.
- Verification rows **V5-V12, V15-V18 and V22** — `DEFERRED(Phase B)`.

Phase A's interim verification is therefore structural plus its own contract tests: green tree (built
`--all-targets`, per V20), all existing Rust and TypeScript suites passing with their assertions unmoved, and
**V1, V2, V3, V4, V13, V14, V19, V20, V21, V23** green — the same ten §3A.10's Sizing table names.

---

## 7. Answers to the remaining mandatory sections

**Pattern Coverage.** Not a card class — an RPC class. Measured (D1): the class of lobby RPCs that settle on a
broadcast rather than a point reply is exactly the four gated tournament actions, because the only other
`ToSubscribers`-only handlers have fire-and-forget clients that await nothing. The *reply* mechanism is built
generic over the four (one ack + one rejection, not four pairs), so a fifth gated tournament action —
`CancelTournament`, a round-timer extension, a manual pairing override — reuses it by adding a field to its
request variant and returning `Ok(GatedEffect)`. The `tournament_request_id()` accessor's exhaustive match is
the mechanism that makes a future gated variant *notice* it needs one.

**Building Blocks.** Reuses `Outbound::{ToSelf, ToSubscribers}`; `Broker::tournament_view` /
`tournament_list_update` / `tournament_summaries`; `authorize_organizer` / `authorize_player`;
`fn error(&str)` (untouched for all non-tournament paths); `parse_lobby_client_message`'s two-stage
`Envelope`; `requestOver`'s existing lifetime machinery (readyState guard, abort pre-guard, close listener,
timer, single `cleanup()`, listeners-before-send); `matchReply` retained unchanged for the three uncorrelated
helpers; `PhaseSocket.serverInfo.lobbyProtocolVersion`; the client's own `LOBBY_PROTOCOL_VERSION` export (for
D14's harness default, and **only** there); `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL`'s "frozen floor,
deliberately no ceiling" doc-comment shape as the template for the new capability constant (D8.2);
`check-protocol-version.mjs`'s existing `extractVersion` + bare-integer-regex device, reused rather than
reinvented for the new pin; the existing `FailureLabel` key+vars shape and `TournamentPage.tsx`'s structural
`"message" in failure` renderer (which is why no component changes); `localeParity.test.ts` as-is; test-side
`MockWebSocket.deliver` / `listenerCount` / `settledOrPending` / `makePhaseSocket`, and `broker.rs`'s
`make_tournament` / `join_tournament` / `view_of` / `error_reason` / `outbounds_contain`.
**New helpers, each justified:** `TournamentRequestId` (D3, prevents `PairingId` confusion at a shared call
site); `ListRowEffect` (D5, types an axis that is currently a comment); `GatedEffect` + `settle_gated` (D5,
the single authority that makes correlation compiler-enforced); `tournament_request_id()` (D6, exhaustive
extraction); `matchAck` (D7, the correlation-aware sibling of `matchReply`);
`MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` (D8.2 — not a new *pattern* but a new *constant*, justified because
the alternative is an unnamed literal that no census tracks and no harness gates, and because the one
plausible way to "improve" it is a latent bug).

**Logic Placement.** Correlation *policy* (which frames answer which request) is protocol-layer, in
`protocol.rs`. Correlation *emission* is broker-layer, in one authority. The client does **no** deriving,
inferring, or diffing — it compares two integers and reads server-sent fields, which keeps it a display layer.
The capability gate reads a value the server advertised; it computes nothing. The failure *reason* sits in the
wire layer (D8.1, argued against the documented boundary rule) and its *copy* sits in the i18n catalogs behind
`t()` (D12), which is the same split every other failure reason already uses. Nothing moves into or out of
`crates/engine/`.

**Rust Idioms.** Newtype over a bare integer where two integer parameters would otherwise share a signature.
`Option<T>` for typed absence rather than a `0` sentinel. A two-member typed enum (`ListRowEffect`) instead of
a bool, per CLAUDE.md's explicit prohibition. `Result<GatedEffect, String>` so an uncorrelated exit is a type
error, not a review finding. Exhaustive matches with no wildcard in `tournament_request_id()` and
`settle_gated`. `#[serde(transparent)]` so the newtype costs nothing on the wire.

**TypeScript Idioms** (the mirror concern, since this change is half frontend). The new failure reason is a
string-literal union member, not a boolean or a sentinel; `FailureLabel` keeps its key+vars-travel-together
shape so "key without its variable" stays unrepresentable; and the `never` terminal in `failureLabel` is
extended rather than defeated with a `default:` arm — the gate is the point.

**Nom Compliance.** **N/A** — no file under `crates/engine/src/parser/` is touched. No Oracle text, no
grammar, no dispatch-by-string. The one string comparison introduced (`msg.type !== replyType` in the new
matcher) is JSON tag dispatch in TypeScript, which is what the existing `matchReply` and
`subscribeTournamentsOver` already do; the nom mandate governs Rust Oracle parsing and does not reach here.

**Extension vs Creation.** **Extension**, twice over. The serde shape of the new request field is the shape
`ClientHello.lobby_protocol_version` already uses in the same enum (§1.1). The correlation mechanism, naming
convention, client-minted-id discipline and requester-only reply posture are lifted from `PreviewManaPayment`
/ `ResolveAll` in the same protocol family (§1.2). No new pattern is created; a pattern that already existed
on the full-game half of the protocol is carried onto the lobby half, where its absence was the defect.

**Analogous Trace.** `PreviewManaPayment`, traced in §1.2: `crates/server-core/src/protocol.rs`
(`ClientMessage::PreviewManaPayment { request_id }`) → same file
(`ServerMessage::ManaPaymentPreview` / `…Rejected` / `…Failed`) → same file's round-trip test pinning the
correlator → same file's wire-literal test. Secondary trace, for the *broker* half: `handle_join_tournament`
(`crates/lobby-broker/src/broker.rs`) — the one existing tournament handler that already emits a `ToSelf`
point reply **and** a `ToSubscribers` broadcast in one `Vec<Outbound>`, in that order, which is exactly the
shape `settle_gated` generalizes.

**Variant Discoverability.** See D11: `cargo engine-inventory` walks only `crates/engine/src`
(`crates/engine-inventory-gen/src/main.rs:111`), so it structurally cannot see `LobbyServerMessage`. The
sibling-cluster check was performed by hand and is the substance of D2.

---

## 8. Judgment calls — every one now closed

Revision 1 left two calls open; revision 2 opened and closed a third. **No call remains open**, and
none of the three has been re-opened by any later revision: round 2 re-adjudicated the third (D8.1's layering) independently on all
four of its own grounds and endorsed it, so only its documentation ripple moved (§3B.6). Each is recorded
below with its grounds so a later reader can see they were decided rather than defaulted.

1. **D8's fail-closed shape → (b) send-then-`"unsupported"`.** Adopted. Round 1 probed the strongest
   counterargument (a retry after an unconfirmed action causing a duplicate non-idempotent mutation) and found
   every affected action already carries an independent server-side idempotency guard, so no data-integrity
   hazard exists. The risk framing is also corrected: `deploy.yml`'s ordering constraint mostly closes the
   hosted-Worker exposure window, and the real residual is self-hosted `phase-server` binaries on older
   releases — the population for which (a) refuse-to-send would break the feature outright. (c) remains
   rejected: the fallback path *is* the bug.
2. **D5's `Result` refactor of four already-merged handlers.** Adopted over the ~14-site manual-threading
   alternative. Round 1 cited the already-established `ToSelf`-before-`ToSubscribers` ordering convention in
   `handle_join_tournament` as generalizing cleanly, and judged the "frozen PR2 code" objection weak because
   the maintainer has already reopened this exact code through review. The compile-time guarantee that no
   gated exit can be uncorrelated is the deciding property.

**One call opened and decided in revision 2, and re-adjudicated clean by round 2**, flagged at the time
because it overrides a documented in-source rule:

3. **D8.1's layering — `"unsupported"` as a wire member rather than a store-level sibling of
   `TournamentNotAuthorized`.** Decided in favor of the wire union, on four grounds tested individually
   against the rule's own text (§D8.1): the frame is sent (the rule's category is "nothing was sent");
   client-authored copy is the norm for three of the four incumbents, so it cannot be the discriminator;
   `lobbyProtocolVersion` is a broker-advertised fact with no store-owned input; and the rule's fourth ground
   ("that file is frozen") is time-bound and now void. **Round 2 verified all four grounds independently at
   source and endorsed the decision**, additionally endorsing the reformulated axis (*whose fact* the
   predicate reads, not *who* evaluates it) as a strictly better statement of the boundary worth writing into
   the source. The decision is closed and has not been re-opened by any later revision. Its cost is honest and scoped, and
   is what the fix for M1 (entry 59) accounts for: `multiplayerStore.ts` re-enters scope for **two** doc-comment
   corrections rather than one (§3B.6), and revision 1's "zero store changes" claim is retracted to exactly
   that extent — still no store code change.

---

## 9. Probe ledger — what was measured vs. what was read

**Measured (compiled and run):** serde additivity in both directions with a positive control (P1, five
cases), independently reproduced by round 1 in its own scratch crate with two additional reach-guard controls
(A4b, A6) — all passing; `node scripts/check-protocol-version.mjs` exit 0 at HEAD (P2); the 98-test frontend
baseline (P3); the PR2 version-bump precedent via `git show a4d569d86` (D9).

**Read at source and re-verified in this revision** (each citation below was opened and confirmed, not
carried forward on trust): `failureLabel`'s `never` terminal and its doc comment naming "a fifth
`TournamentRpcFailureReason`"; `multiplayerStore.ts`'s `TournamentNotAuthorized` boundary rationale and
`GatedTournamentRpcResult`'s alias shape; the four incumbent failure reasons' mint sites and their hardcoded
English copy; `makePhaseSocket`'s literal (no `lobbyProtocolVersion` key) and its **23** call sites (round 3,
m3 — "24" was asserted as verified in two consecutive revisions and was wrong both times: `grep -c
"makePhaseSocket("` returns 24, but one of those is the declaration `function makePhaseSocket(` at `:81`.
D14's fix is to the *default inside the declaration*, so the correct count changes nothing operationally —
it is recorded because a confidently-restated count is exactly the kind of claim this plan has now been
wrong about three times, and because "23 call sites, 1 declaration" is the form that stays checkable); the seven
locale catalogs' `errors` blocks and `localeParity.test.ts`'s `KNOWN_PLACEHOLDER_GAPS` (empty, **and**
consulted only by the placeholder check — see D12 item 4's corrected mechanism);
`TournamentPage.tsx`'s structural `"message" in failure` renderer; `validation.rs`'s four tournament arms
including `ReportMatchResult`'s `..` at `:469`; the 14 error exits and the 3+1 tail shapes across the four
broker handlers; `broker-wasm/src/lib.rs`'s `reject_reply` doc comment at `:84-88`;
`ClientHello.lobby_protocol_version` at `protocol.rs:620-621` and `ServerHello`'s mirror at `:762-763`;
`ws-adapter.ts`'s `lobbyProtocolVersion` field at `:465` and its `!== undefined` tolerance at `:517`;
`engine-inventory-gen/src/main.rs`'s `TARGET_DIRS` at `:111`; `getTournamentOver`'s "genuinely `ToSelf`" doc
comment.

**Compiled for revision 4 — the census probe (round 3's mandated methodology correction).** Revision 3 said
here that *"no Rust crate in this repo was compiled while writing this plan."* **That is now retracted: it
was the root cause of three consecutive blocking findings, and it no longer holds.** The `request_id` field
was added to the four gated variants in **both** mirrors (`lobby-broker`'s `LobbyClientMessage` and
`server-core`'s `ClientMessage`) in the implementation worktree, under an isolated `CARGO_TARGET_DIR` in the
scratchpad — the shared `C:/git/phase/target` was never touched — and `cargo check` was run per crate and
then `--workspace`, with `--all-targets` throughout. `rustc` produced the census in §3A.9: **71 sites across
5 files**, with per-file totals and every coordinate taken from the error stream rather than from reading.
Every temporary edit was reverted immediately afterwards and `git status --porcelain` confirmed empty at the
revision-3 tree state (`HEAD` unmoved at `3ce0f5c54`).

Three things the probe established that no amount of reading had:
- **Three files were genuinely unscoped at the site level** — `validation.rs` (7 test constructions),
  `protocol.rs` (4), `main.rs` (4 in `tournament_client_frames`) — all three already on the in-scope *path*
  list, which is exactly why a file-level sweep kept reporting clean.
- **`main.rs`'s exposure is compile-time, not runtime** (§3A.5), reversing revision 3's characterization.
- **A first `--workspace` run is actively misleading** until each library target is green (§3A.9 step 3):
  `server-core` and `phase-server` reported zero errors purely because `lobby-broker`'s lib had failed.
  This is the "instrument reports clean because it never reached the rest of the input" failure mode entry 60
  already recorded once in this run, met a second time in a different instrument.

Two negative results worth recording because they bound the claim rather than merely decorate it:
`manabrew-compat` — the only other workspace crate whose `Cargo.toml` mentions either crate name (in a
comment) — **compiles clean**, so the three-crate recipe is provably not short of the `--workspace` one; and
`-p broker-wasm` / `-p lobby-broker-wasm` both fail with *"did not match any packages"*, so V20's
revision-3 recipe named a target that could not have been checked (corrected in V20 and §3A.9).

**Read, not executed — labelled as such:** the variant-agnosticism of the Worker shell (read in `lobby-do.ts`
and stated in its own comment) — TypeScript, so no Rust census could reach it; and `broker-wasm/lib.rs`'s
four literals (§3A.8), which are workspace-`exclude`d and were confirmed by round 3's own compile probe
rather than by this one. The previously-listed unverified items — `to_server_message` /
`to_lobby_client_message`'s exhaustiveness and `client_message_wire_guard.rs`'s destructuring shape — have
**graduated from "read" to "measured"** by the census above.

**Round 2's own probe, recorded because it changes what is known rather than what is claimed:** round 2
compiled the D12 frontend fix in isolation — adding the new wire member alone reproduced exactly the predicted
`TS2322` at the predicted line, and adding D12 items 1-2 produced zero errors and zero collateral breakage.
That is a measured result, and it establishes that B1's *type-level* fix is exactly sufficient. It is also
precisely why round 2's own B1 matters: type-level sufficiency in one language said nothing about the Rust
workspace, where the same change does not compile at all until §3A.6 and §3A.8 land.

**Read at source and re-verified for revision 3 specifically** (round 2's findings were re-derived from the
files, not accepted on report): `broker.rs`'s four dispatch arms at `:445/:450/:457/:461` and their absent
rest patterns; the 26 test-module construction sites and their brace-literal shape (sampled at `:2424`,
`:2598-2610` and `:3555`, all full field lists); `broker-wasm/src/lib.rs`'s `mutates_lobby` rest patterns at
`:113-116`, its `OutboundDto` kind mapping at `:60-81`, and
`tournament_variants_are_classified_by_whether_they_write`'s four full literals at `:322/:326/:332/:336` with
its exhaustiveness rationale at `:302-306`; the workspace-wide `rg` sweep confirming `DraftAction` namesakes
in `draft-core`/`server-core` are the only other hits (§3A.9); the **zero** repository hits for
`lobby_protocol_version_is_current` and the two real pin tests at `protocol.rs:985-1005` and `:1129-1133`,
including the "purely additive" comment at `:987-989`; `ws-adapter.ts`'s `LOBBY_PROTOCOL_VERSION` at `:442`
and `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL`'s "deliberately NO ceiling" doc at `:444-454`;
`check-protocol-version.mjs`'s four lobby regexes and their bare-integer-literal rationale;
`multiplayerStore.ts`'s `runGatedTournamentRpc` doc at `:443-467` in full; all eight header cross-references
in `tournamentClient.ts` plus its five header parts; `tournamentPageState.ts`'s four ordinal sites and the
unrelated `:25` sentence that must not be touched; `localeParity.test.ts`'s two per-namespace checks at
`:282-290` and `:292-308` and which one calls `isKnownGap`; `tournamentClient.test.ts` section F's three
regexes and its two additional positive-control pins at `:767` and `:783` (the latter cited as `:786` in
revision 3 — round 3's m2, corrected in §3B.2.1); the existing value imports from
`ws-adapter.ts` in `openPhaseSocket.ts` and `multiplayerStore.ts` that make D8.2's placement precedented.

---

## 10. Revision ledger — round 1 findings → where they landed

| Finding | Severity | Resolution | Where |
|---|---|---|---|
| **B1** — new failure reason doesn't compile against `failureLabel`'s `never` gate; 7 locale keys unscoped | **BLOCKING** | `tournamentPageState.ts` (+ its test) and all seven `tournament.json` catalogs added as scope paths; i18n `t()` boundary stated explicitly; V16 (compile-time revert check) and V17 (parity gate) added | D12, §3B.4, §3B.5, V16, V17 |
| **M1** — the documented wire-vs-store boundary rule was never engaged | material | **Decided: wire member.** Argued against the rule's four grounds individually on measured evidence; `multiplayerStore.ts` re-enters scope for one doc correction and the "zero changes" claim is retracted | D8.1, §3B.6, §8 item 3 |
| **M2** — sizing recount fires the phase-fit conjunction | material | Restructured into two phases at the seam revision 1 identified and round 1 endorsed; per-phase Sizing sections; recursion shown to terminate | §3A, §3B, §3A.10, §3B.8, §6 |
| **M3** — `makePhaseSocket`'s `undefined` default would gut the new tests | material | Default moves to the client's `LOBBY_PROTOCOL_VERSION`; the divergence from `ws-adapter.ts`'s `undefined` tolerance is stated as a considered choice; V18 added | D14, D8.3, §3B.7, V18 |
| **m1** — `getTournamentOver` described as "never exposed" | minor | Corrected to "exposed but benign"; the accurate existing source comment is quoted and protected from the header rewrite | D7, §3B.2 |
| **m2** — "4 duplicated constructions" | minor | Corrected to 3 identical two-element tails + 1 distinct one-element tail (measured); the 14-error-exit total confirmed exact | D5, §3B.1 |
| **m3** — compile-forcing destructure claimed for all 4 handlers | minor | Corrected to 3 of 4; `ReportMatchResult`'s `..` at `validation.rs:469` absorbs the field silently; explicit `request_id: _` mandated anyway | §3A.3 |
| **m4** — residual gap framed as merely unimproved | minor | Reframed as a **regression of a designed property**, citing `reject_reply`'s own doc comment verbatim; reachability mitigation retained | D6, §3B.2 |
| **m5** — two line-number drifts | minor | `TARGET_DIRS` re-verified at `:111` (citation was already correct, retained); `ws-adapter.ts`'s `lobbyProtocolVersion` corrected to `:465` (field) with the doc block at `:462-465`. Line citations elsewhere replaced with symbol names per the durable-claim rule | D11, D8, §0.1 |
| **Rec 1** — endorse D8 option (b) | recommendation | Adopted and closed, with round 1's idempotency-guard evidence and the corrected hosted-vs-self-hosted risk framing | D8, §8 item 1 |
| **Rec 2** — endorse the `Result` refactor | recommendation | Adopted and closed, citing `handle_join_tournament`'s ordering convention and the reopened-code rebuttal | D5, §8 item 2 |
| **Rec 3** — closer serde precedent missed | recommendation | `ClientHello.lobby_protocol_version` promoted to **primary** precedent (same file, same enum, same attributes, same rationale); `PreviewManaPayment` retained as secondary for the correlation mechanism | §1.1, §1.2, D4 |

---

## 11. Revision ledger — round 2 findings → where they landed

| Finding | Severity | Resolution | Where |
|---|---|---|---|
| **B1** — Phase A as scoped does not compile: `broker.rs`'s four exhaustive dispatch arms + 26 test literals, and `broker-wasm/lib.rs`'s enumerating test, were unscoped (the latter actively cleared as needing no change) | **BLOCKING** | `crates/lobby-broker/src/broker.rs` added to Phase A scope with a mechanical-only edit (`request_id: _` in the four arms, `request_id: None` at all 26 literals) and the "actually consume it" work left explicitly `DEFERRED(Phase B)`; the false all-clear on `broker-wasm/lib.rs` replaced by a site-by-site table naming its one in-scope test while confirming `OutboundDto` and `mutates_lobby` genuinely need nothing; a workspace-wide sweep added, showing the `DraftAction` hits are namesakes. Sizing re-adjudicated: Phase A 7 → **8** non-test paths, still **1 unit**, so T1 fails and the two-phase split survives — stated explicitly, not assumed. New rows V20, V21 | §3A.6, §3A.8, §3A.9, §3A.10, §6, V20 |
| **M1** — the `multiplayerStore.ts` ripple is undercounted at "exactly one doc comment" | material | The **architectural decision is not re-opened** — round 2 independently verified all four grounds and endorsed it. Its documentation ripple is expanded to both comments, with a line-by-line table of the three claims `runGatedTournamentRpc`'s doc makes that this fix falsifies (`"rejected"` becoming a reliable refusal signal; the part-4 cross-reference; the "for exactly that reason" justification), the replacement caution (`"unsupported"` means sent-but-unconfirmable, not failed), and round 2's endorsement of writing the reformulated boundary axis into the source. Still doc-only, re-confirmed | §3B.6 |
| **M2** — `tournamentClient.ts`'s doc-edit scope is undercounted (2 of 8 cross-references scheduled) | material | New §3B.2.1 enumerates every cross-reference read at source and classifies each EDIT / PRESERVE-and-extend / NO CHANGE, adding header part 3 (which D2 already claimed this fix repairs and V10 already tests), the four gated helpers' own doc comments, and the `:200` inline comment sitting above the code this fix makes conditional. Section F's two additional positive-control pins added to the wording constraint | §3B.2.1, §3B.2 |
| **M3** — the census names a test symbol that does not exist, and separately names the real one, treating one object as two | material | `lobby_protocol_version_is_current` re-verified as **zero hits repo-wide** and removed. Both real tests named with their exact holdings: `lobby_protocol_version_is_independent_of_the_full_game_one` (the `assert_eq!` at `:986`, plus the three assertions that must NOT move) and `tournament_lobby_version_follows_the_format_config_bump` (`:1129-1133`). The consolidated census re-confirmed complete | D9, §3A.7 |
| **M4** — the capability gate's `< 5` is an unnamed 6th version pin, uncensused, ungated, and one misapplied instruction away from a real latent bug | material | Named as **`MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK = 5`** in `ws-adapter.ts` beside the established `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL` precedent, with a doc comment stating it is a **frozen floor that must NOT be bumped when `LOBBY_PROTOCOL_VERSION` moves**; added to D9's census as two rows (the constant and its new `check-protocol-version.mjs` bare-integer pin); a three-constant disambiguation table added (**extended to four** in revision 4 — round 3's m5 found the Rust-side `MIN_SUPPORTED_LOBBY_PROTOCOL` floor missing; see §D8.3); D14's "reference the constant" instruction explicitly scoped to the harness site and marked wrong at the gate; new rows V21 (the pin, with re-derivation as its revert-check) and **V22** (gate direction, including the `lobbyProtocolVersion: 6` fixture that fails *at the moment of the mistake* rather than at the next bump) | D8.2, D8.3, D9, §3B.2, V21, V22 |
| **m1** — ordinals in `failureLabel`'s doc and a matching test comment go stale by one | minor | All four sites tabulated and repaired in the **durable form** ("any new failure member", "every arm", "every failure shape") rather than by refreshing the arithmetic, since this drift class has now recurred three times in this engagement. `tournamentPageState.ts:25` read in full and explicitly excluded — it is about `PairingOutcome`/`Tiebreaks`, a different union | D12 item 3, §3B.4 |
| **m2** — Phase A's test list inconsistent across four sections | minor | §3A.10's Sizing table declared the single authority (it is what the phase-fit gate re-adjudicates against) and made complete at **nine** rows; §3A's opening paragraph, §4's Phase A block and §6's deferral list all restated to match it, with a sentence saying which one governs | §3A, §3A.10, §4, §6 |
| **m3** — §4 and §6 read as a flat contradiction on deferral | minor | Both reworded against one stated vocabulary: §4 means "no row is deferred *without a named landing phase*", §6 gives the Phase-A-relative view of the same partition. Each now says so explicitly and names the exact row sets | §4, §6 |
| **m4** — a scope-path list uses prose shorthand ("+6 mirrors") where the pathspec machinery needs literal paths | minor | Both Phase B's `SCOPE_PATHS` block and §3B.5 now enumerate all seven catalog paths literally, with the grouping shown as an annotation rather than smuggled into a path string | §3B.5, §3B.8 |
| **m5** — the wrong i18n mechanism is credited with catching an English-only key | minor | Corrected against source: the **unconditional bidirectional key-parity check** (`localeParity.test.ts:282-290`) is what fails it, and it never consults `KNOWN_PLACEHOLDER_GAPS`; only the placeholder check (`:292-308`) calls `isKnownGap`. Round 2's second independent gate (V16's own `i18n.exists` assertion) recorded too. The conclusion was already right; only the mechanism moved | D12 item 4, §3B.5, §9 |
| **m6** — a stale "purely additive" enumeration inside the very test whose `assert_eq!` is already being bumped | minor | Scheduled: `protocol.rs:987-989` becomes "lobby versions 3, 4 and 5 are purely additive" / "not 5", with a note that this comment is the **in-source statement of the argument** §D8.1 relies on to keep both minimum-supported floors at 2 — load-bearing, not cosmetic | §3A.7, D9 |

---

## 12. Revision ledger — round 3 findings → where they landed

Round 3's verdict was **1 blocking, 0 material, 5 minor** — and, decisively, the blocking finding was the
**third consecutive** one of an identical class: a required consumer of the four modified
`LobbyClientMessage` variants missing from scope, in a file this plan's own prose already listed as covered.
Round 3 diagnosed the cause precisely and it is not carelessness: **the census methodology was a file-level
instrument answering a site-level question.** Revision 4's principal change is therefore the *method*, not
the content — §3A.9 is now generated by `rustc` rather than by reading, and every per-file section points at
the regenerating command instead of at a transcription.

**Nothing else was reopened.** The architecture has now held stable and independently confirmed across three
full review rounds and is preserved verbatim: the two-variant wire design and its rejected alternatives (four
sibling acks; `request_id` on `TournamentUpdate`); the M1 decision that `"unsupported"` stays a wire-level
`TournamentRpcFailureReason` member, with all four of its grounds; the 2-phase split; the serde-additivity
probes and their reach-guards; the 7-site broadcast-emission census; the `ClientHello.lobby_protocol_version`
precedent; the `Result<GatedEffect, String>` broker refactor; and
`MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` with its fixture.

| Finding | Severity | Where it landed | Sections |
|---|---|---|---|
| **B1** — three more files carry real compile errors the plan's scope did not cover at the site level, and a fourth is covered but unenumerated; the read-and-sample census cannot close this class | **BLOCKING** | **Method replaced.** §3A.9 is rewritten as a compiler-generated census with the exact reproducible recipe (isolated `CARGO_TARGET_DIR`; add the field to **both** mirrors; `cargo check --workspace --all-targets`; absorb lib-level `E0027`s and re-run; revert). The completeness claim is restated in the **durable, re-verifiable form** — "every construction/destructuring site in the workspace as enumerated by `cargo check --all-targets` after the field is added" — not as a file count that goes stale. Result: **71 sites in 5 files**, each folded into its own section: `validation.rs`'s 7 test constructions incl. the shared builder `report_with` (§3A.3), `protocol.rs`'s 4 in `tournament_client_variants_round_trip_through_serde` (§3A.1), `main.rs`'s 4 in `tournament_client_frames` (§3A.5), and `client_message_wire_guard.rs`'s 15 brought up to `broker.rs`'s transcription standard (§3A.4). §3A.6's `rg` regenerator demoted to a cross-check. **Sizing unchanged** — all five files were already scope paths, so 8/6-12/14-20 and 1/2/3 units all stand and neither phase re-trips the conjunction | §3A.1, §3A.3, §3A.4, §3A.5, §3A.6, §3A.9, §3A.10, §6, §9, V20 |
| **B1 (a)** — `main.rs`'s exposure mischaracterized as *runtime* | (within B1) | Corrected to **compile-time**: 12 errors, 4 `E0027` + 8 `E0063`, with `:3840` producing two on one line. Also newly stated — this is the **one site in Phase A where the correlator is forwarded rather than discarded**, because dropping it here would silently uncorrelate every native-`phase-server` client while the Worker path worked, a divergence no Phase A test could catch — **superseded by round 4's M2**: such a test already exists (`tournament_variants_survive_the_canonical_lobby_roundtrip`); it was merely vacuous while every fixture used `None`. See §3A.5 and V23 | §3A.5 |
| **B1 (b)** — shared fixture builders | (within B1) | Three of them (`report_with`, `oversized_/valid_tournament_frames`, `tournament_client_frames`) explicitly flagged **edit the builder, not its callers**, so the executor does not sweep consuming tests that need nothing | §3A.3, §3A.4, §3A.5 |
| **B1 (c)** — `broker-wasm` unreachable by any workspace check | (within B1) | Measured: it is in the root `Cargo.toml`'s `exclude`, and both `-p broker-wasm` and `-p lobby-broker-wasm` fail with *"did not match any packages"* — so **V20's revision-3 recipe named a target that could not have run**. V20 now carries the separate `--manifest-path … --target wasm32-unknown-unknown` command, and §3A.9 states the exclusion as the one gap the workspace census structurally cannot see | §3A.9, V20 |
| **B1 (d)** — reverse-dependency bound | (within B1) | Added, so the shorter per-crate recipe is provably equivalent: only `lobby-broker`, `server-core` and `phase-server` consume either enum; `manabrew-compat`'s apparent dependency is a comment and it compiles clean (measured). Also recorded: a first `--workspace` run reports **zero** errors downstream while any library target is red — the same "clean because it never reached the input" failure mode entry 60 logged in a different instrument | §3A.9, §9 |
| **m1** — sizing sweep says "nine … already in scope" then lists seven (7 + 6 namesakes = 13) | minor | Corrected to **seven**. The paragraph is also demoted: the `rg` sweep is now a cross-check, and the `DraftAction` all-clear rests on those six files' **absence from the compiler's error set** rather than on reading qualified paths | §3A.9 |
| **m2** — a line citation introduced *while fixing round 2's M2* is off by three | minor | The verbatim import-line regex is at **`:783`**, not `:786`, and the section-F range ends at `:785` (the file's last line), not `:789`. Both corrected, and the citation re-keyed to its enclosing `it("never acquires a socket of its own")` so the next edit above it cannot falsify it. Companion pin `:767` re-verified **accurate** and left alone | §3B.2.1 |
| **m3** — `makePhaseSocket`'s "24 call sites", asserted as verified in two consecutive revisions | minor | Recounted: **23 call sites plus 1 declaration** (`function makePhaseSocket(` at `:81` is one of the 24 `grep` hits). Operationally inert — D14 edits the default inside the declaration — but recorded in the checkable "23 + 1" form, with a note that a confidently-restated count is precisely the claim class this engagement has now been wrong about repeatedly | §9 |
| **m4** — a sizing figure attributed to the wrong axis | minor | Round 1's **18** is the **ungrouped** figure (18 + 2 deltas = 20, the ungrouped total; the grouped counterpart would be 12). Label swapped and the arithmetic shown inline so the attribution is self-checking | §6 |
| **m5** — the confusable-constants table omits a fourth constant that exists | minor | **`MIN_SUPPORTED_LOBBY_PROTOCOL`** (`crates/lobby-broker/src/protocol.rs:377`, `= 2`, pinned by `check-protocol-version.mjs:145`) added as a row, with a **Side** column added so the Rust/TS split is visible. Noted as the omission that mattered most: it differs from `MIN_SUPPORTED_SERVER_LOBBY_PROTOCOL` by one word, sits on the opposite side of the wire, and holds the same value — the exact conflation the table exists to prevent | D8.3 |

---

## 13. Revision ledger — round 4 findings → where they landed

Round 4's verdict was **0 blocking**, 2 material, 2 minor. It also **closed the completeness question**: the
reviewer reproduced §3A.9's compiler-driven census from scratch in its own isolated target dir, matched it
coordinate for coordinate, then applied `request_id` at all 71 sites and ran
`cargo check --workspace --all-targets` to a clean exit 0 — a positive proof of exhaustiveness rather than the
negative "we found no more" of every earlier round. **Nothing architectural moves in revision 5.** The
two-variant wire design, the D8.1 `"unsupported"`-is-wire-level decision, the 2-phase split, the 71-site
census, the `ClientHello` precedent, the `Result<GatedEffect, String>` refactor and
`MIN_LOBBY_PROTOCOL_FOR_TOURNAMENT_ACK` are all carried forward untouched, as they have been for four rounds.

| Finding | Severity | Where it landed | Sections |
|---|---|---|---|
| **M1** — the plan's own corrected `broker-wasm` verification command does not execute, for **two independent** measured reasons: (a) from the nested `.claude/worktrees/…` implementation worktree, cargo's ancestor workspace search escapes the worktree and resolves to the **outer** checkout's `Cargo.toml`, whose `exclude` paths do not cover the worktree's copy — *"believes it's in a workspace when it's not"*, before any type-checking; (b) even in a top-level checkout, `--manifest-path` bypasses the **cwd-based** config search and silently drops `.cargo/config.toml`'s required `getrandom_backend` rustflag. Third consecutive revision to get this recipe wrong in a new way | material | **New §3A.8.1** is now the single authority for the command: `cd lobby-worker/broker-wasm` → append a temporary `[workspace]` table → `cargo check --target wasm32-unknown-unknown --all-targets` → **revert and verify with `git status --porcelain`**. Both failure mechanisms are written out with their measured evidence, including the accurate scoping: the `cd` is required **everywhere** (it is what picks up the rustflags cfg), while the temporary `[workspace]` table is required **only** under a nested worktree and is harmless in a top-level checkout — re-measured for revision 5 with `cargo locate-project --workspace` from both copies, which returns the outer-checkout error from the worktree and the crate's own manifest from the top-level checkout. Expected pre-fix output is pinned at **exactly four `E0063`s and nothing else**, which doubles as the reach-guard that the inline `#[cfg(test)]` module was actually compiled. V20 and §3A.9's `broker-wasm` paragraph now defer to §3A.8.1 and explicitly forbid substituting a `--manifest-path` form | §3A.8.1, §3A.9, V20 |
| **M2** — the plan's claim that *"no Phase A test could catch"* the forward-vs-discard bug in `main.rs` is true only because of the plan's **own fixture choice** (`request_id: None` everywhere), not because no such test exists. `tournament_variants_survive_the_canonical_lobby_roundtrip` already does serialized-string equality across the projection with a *"field dropped or renamed"* message — but under `skip_serializing_if = "Option::is_none"` a forwarded `None` and a discarded `None` serialize identically, so it passes **vacuously**: the exact missing-positive-reach-guard pattern this plan's own criteria warn about | material | **One fixture literal changes**: `tournament_client_frames`'s `StartTournamentRound` frame takes `request_id: Some(TournamentRequestId(7))`; the other three gated frames keep `None` so the uncorrelated round-trip stays proven in the same pass. **New Verification Matrix row V23**, keyed to that existing test by name, with *"revert the `request_id: *request_id` forward in that arm → this test reds"* as the revert-failing assertion (and the note that `request_id: _` + `request_id: None` **compiles**, which is why `E0027` alone is not a guard). §3A.5's false sentence is replaced with what is actually true. **Zero new tests.** The reviewer's second consequence is stated as a hard constraint: because the test compares serialized **strings** and serde emits fields in declaration order, `request_id` must sit at the **same relative field position** in both wire mirrors — invisible under the old fixture, caught immediately under the new one. The residual is named rather than hidden: one correlated fixture guards the `StartTournamentRound` arm by value; the other three are guarded at the binding level only | §3A.5, §3A.1, §3A.2, **V23**, §3A.10, §6 |
| **m1** — the shared-test-builder list names four builders; a fifth exists | minor | **`fn started_event`** (`crates/lobby-broker/src/broker.rs`, called by **8** distinct tests) added to §3A.6 and to V20's builder list. Confirmed **operationally inert**: its single `LobbyClientMessage::StartTournamentRound` construction is already one of §3A.6's 26 enumerated coordinates, so the blanket instruction covers it correctly, and its 8 callers pass `(conn, broker, env)` with no variant literals of their own — so nothing needs separate treatment and nothing must be over-edited. Documentation completeness only; no scope, sizing or unit change | §3A.6, V20 |
| **m2** — the front matter still identified the document as "Revision 3 … after plan review round 2" while the body was revision 4 answering round 3 | minor | Front matter rewritten to **"Revision 5 — supersedes revision 4 (phase-fit entry 66) after plan review round 4 (entry 67: 0 blocking, 2 material, 2 minor)"**, entry numbers verified against the phase-fit log rather than assumed, with the ledger pointers extended to §12 and §13. The later *"Where revision 3 does transcribe coordinates …"* reference is reworded to **"Where this plan does transcribe coordinates …"** — the durable form, since a hardcoded revision number is precisely the drifting figure §0.1's own discipline exists to avoid; that is called out inline so the next revision does not reintroduce one | front matter, §0.1 |

**Sizing after revision 5: unchanged.** V23 adds no scope path (`crates/phase-server/src/main.rs` was already
Phase A's), no new test file, and no unit — it is a one-token change to a fixture the plan already edits.
§3A.8.1 changes a *command*, not a scope path. `started_event` is inside a file already in scope. Phase A
remains **8 non-test paths / 1 unit**, the run remains **14 grouped / 20 ungrouped / 3 units**, and neither
phase re-trips the T1∧T2 phase-fit conjunction. The only counting change anywhere is Phase A's verification
rows: **nine → ten** (V23 added), reflected in §3A.10's Sizing table, §3A's standalone-completability
paragraph, §6 and the matrix's own partition sentence.
