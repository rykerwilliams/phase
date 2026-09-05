# Phase 1 Implementation Plan — Wire layer: type mirrors + the `requestOver` primitive (revision 2)

## What this revision changed, and nothing else

| Finding | Fix applied | Where |
|---|---|---|
| **G1 (blocking)** — the provenance contract omits the multi-authority case that actually bites: `TournamentUpdate` is both the `GetTournament` point reply **and** a broadcast, so a foreign actor's action on the same tournament settles a gated helper `{ok:true}` ahead of the caller's own outcome, foreclosing the `Error` arm. | (1) New **B6** in the Identity/Provenance Contract, modelled on B3 — names the wire limitation with all six citations (`handle_join_tournament:1168`, `handle_start_tournament_round:1206`, `handle_report_match_result:1268`, `handle_drop_from_tournament:1309`, `handle_end_tournament:1334`, `reap_expired`'s `Abandoned` arm `:550-555`; `ToSelf` only at `handle_get_tournament:1177`), states live-vs-latched, states the user-visible consequence, and takes B3's posture (document the wire, do not fabricate a correlator). (2) Required in `tournamentClient.ts`'s module header (§5.2), beside the B3 note. (3) New **matrix row 12a** + its test in §5.7 part C, with a paired reach-guard, requiring a new `listenerCount()` tally on the copied `MockWebSocket` (confined to this test file). (4) One added paragraph on the `DEFERRED(phase 5)` row naming phase 5's ambient-broadcast design as B6's mitigation and warning phase 5 off treating `{ok:false}` as a reliable rejection detector. | §0.3 (cross-ref), Identity/Provenance Contract, Verification Matrix row 12a, `DEFERRED(phase 5)`, §5.2, §5.4, §5.7 |
| **Note 1** — the `.close(` regex is comment-unaware and the natural doc-comment phrasing trips it. | §5.2 gains an explicit **wording constraint** (write "does not close the borrowed socket", never the literal `.close(`), §5.4's prose reworded so it cannot be copied verbatim into a comment, §5.7F + matrix row 9 gain the comment-awareness caveat next to the regex. | §5.2, §5.4, §5.7F, matrix row 9 |
| **Note 2** — `boundary-guardrails.test.ts` citations wrong. | Corrected: regex-scoped assertions are `:69`, `:84`, `:93` (three); bare `toContain` at `:70` (negative) and `:96` (positive) — two, not one. Substantive claim (regex-scoping dominant, 3 vs 2, not universal) kept. | §0.7, Building Blocks |
| **Note 3** — "thirteen names" vs §5.1's 16. | Count corrected to **sixteen** (13 mirrors + 3 reply wrappers: `TournamentCreatedReply`/`TournamentJoinedReply`/`TournamentUpdateReply`), composition spelled out, reviewer's zero-collision re-sweep recorded. | §0.6 |
| **Note 4** — two executor clarifications. | New **"Executor environment facts"** block in §5.8: (a) matrix row 2 fails under `type-check`, not `vitest`; (b) `noUnusedLocals`/`verbatimModuleSyntax` implications spelled out with the `searchControlWireTypes.test.ts:88-91` precedent. | §5.8, cross-referenced from §5.6 |

Everything else — all wire-type shapes, all 7 frame literals, the `ToSubscribers`-only routing table, findings 0.9 A and B, S2 collision handling, the Sizing section (3 units / 2 source scope-paths), deferral compliance and scope-path fidelity — is carried forward **verbatim** from revision 1.

---

**Run:** PR 4/4 tournament-organizer rollout (phase-rs/phase#7718) · **Mode:** phase-plan · **Phase 1 of 5**
**Worktree:** `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend` · branch `feat/tournament-organizer-pr4-frontend` · `PHASE_BASE_SHA 765c4ebda16a7ba17bb83c5b57d6ce1c6cf7e2be`.

---

## Step 0 — Premise verification (phase-1-scoped)

### 0.1 Wire types — read directly from source (measured)

| Rust item | File:line | Serde shape | Consequence for the mirror |
|---|---|---|---|
| `MatchArity(u8)` | `tournament.rs:83-85` | `#[serde(try_from="u8", into="u8")]` | **bare number**, not `{...}` |
| `ScoringPolicy` | `tournament.rs:153-159` | `#[serde(try_from/into = "RawScoringPolicy")]`, all `u8` | **flat** 3-field object |
| `TournamentStatus` | `tournament.rs:265-295` | plain externally-tagged unit enum | `"Registration"\|"InProgress"\|"Completed"\|"Abandoned"` |
| `BracketShape` | `tournament.rs:316-320` | ditto | `"Swiss"\|"SingleElimination"` |
| `PairingId` | `tournament.rs:330` | `pub type PairingId = u32` | `number` |
| `PodOutcome` | `tournament.rs:336-348` | externally tagged | `{Decisive:{winner,game_wins}} \| "Draw"` |
| `PairingOutcome` | `tournament.rs:355-367` | externally tagged, **newtype** `Reported(PodOutcome)` | `"Bye" \| {Forfeit:{winner}} \| {Reported: PodOutcome}` — `{"Reported":{"Decisive":{…}}}` |
| `Tiebreaks` | `tournament.rs:714-726` | externally tagged struct variants, `f64` fields | `{HeadToHead:{…}} \| {Multiplayer:{…}}` |
| `TournamentStanding` | `tournament.rs:756-768` | plain struct | 7 fields incl. nested `tiebreaks` |
| `PlayerSummary` | `protocol.rs:473-478` | plain struct | `player_key/display_name/dropped` |
| `PairingView` | `protocol.rs:496-503` | `outcome: Option<PairingOutcome>`, **no `skip_serializing_if`** | emits `"outcome":null` |
| `TournamentSummary` | `protocol.rs:507-528` | plain struct, 9 fields | `player_count` is **active** entrants (`active_player_count()`, `:538`) |
| `TournamentView` | `protocol.rs:556-562` | plain struct | `summary/players/pairings/standings` |

### 0.2 Client→server frame literals — measured, verbatim

`protocol.rs:1143-1172` (`every_client_variant_tag_is_known`) holds one literal per client variant. Frame builders reproduce these verbatim. `CreateTournament.total_rounds` is `Option<u32>`, `#[serde(default)]`, no `skip_serializing_if` (`:696-697`) → serializes `null` for `None`.

### 0.3 The `ToSubscribers`-only finding — confirmed, per-RPC routing table

| RPC | `ToSelf` on success | `ToSubscribers` on success | handler |
|---|---|---|---|
| `CreateTournament` | `TournamentCreated{code,organizer_token,view}` | `TournamentListUpdate` | `:1124-1131` |
| `JoinTournament` | `TournamentJoined{code,player_token,view}` | `TournamentUpdate` + `TournamentListUpdate` | `:1162-1170` |
| `GetTournament` | `TournamentUpdate{code,view}` | — | `:1177-1180` |
| `StartTournamentRound` | **none** | `TournamentUpdate` + `TournamentListUpdate` | `:1205-1208` |
| `ReportMatchResult` | **none** | `TournamentUpdate` **only** | `:1267-1269` |
| `DropFromTournament` | **none** | `TournamentUpdate` + `TournamentListUpdate` | `:1308-1311` |
| `EndTournament` | **none** | `TournamentUpdate` + `TournamentListUpdate` | `:1333-1336` |

Four of seven RPCs produce no point reply at all. This table is also the measured evidence for **B6**: `TournamentUpdate` appears once as `ToSelf` (`GetTournament`) and five times as `ToSubscribers`, plus a sixth broadcast site outside this table (`reap_expired`'s `Abandoned` arm, `:550-555`), and the wire gives no way to tell them apart beyond `code`.

### 0.4 S3's broker facts — confirmed

`SubscribeLobby` → `[AddSubscriber, ToSelf(LobbyUpdate), ToSelf(TournamentListUpdate), SendPlayerCountToSelf]` (`broker.rs:317-337`); `UnsubscribeLobby` → `[RemoveSubscriber]` (`:339-343`).

### 0.5 `subscribeLobbyOver` precedent — confirmed line-exact

`brokerClient.ts:597` def; `SubscribeLobby` sent at `:650`; `UnsubscribeLobby` sent from the detach at `:656`; explanatory doc comment naming `UnsubscribeLobby` at `:595`.

### 0.6 S2 collision — confirmed, full sweep of sixteen names

`draft-adapter.ts:306` exports an incompatible `PairingView`, imported by `EliminationBracket.tsx`, `multiplayerDraftStore.ts`, `p2p-draft-host.ts`, `draftPodHostAdapter.ts` and three adapter tests. Full `export type|interface|const|enum` sweep across `client/src` for all **sixteen** type-level names to add — the 13 wire-type mirrors in §0.1 **plus** `TournamentCreatedReply`/`TournamentJoinedReply`/`TournamentUpdateReply` (also new exports per §5.1) — plus every new value-level identifier (7 helper names, `requestOver`, `subscribeTournamentsOver`). **`PairingView` is the only collision.** `TournamentPairingView` is free.

### 0.7 Residual note 3 — confirmed, citations corrected

`boundary-guardrails.test.ts` mixes both styles. **Regex-scoped:** `:69`, `:84`, `:93` (three). **Bare `toContain`:** `:70` (negative), `:96` (positive) — two. Regex-scoping is the *dominant* convention (3 vs 2), not exclusive — phase 1 cites it as dominant convention, not universal rule.

### 0.8 S9 environment — measured on this worktree

`client/node_modules` **absent**. `node scripts/check-protocol-version.mjs` → **exit 0**. `LOBBY_PROTOCOL_VERSION = 4` at `ws-adapter.ts:442`. `type-check` = `protocol:check && tsc -b --noEmit`; `lint` = `eslint .`; `test` = `vitest`.

### 0.9 — Two findings that correct charter shorthand (design intent unchanged)

**(A) `TournamentRemoved` never requires client-side list reduction.** `reap_expired` (`broker.rs:526-579`) emits per-tournament `TournamentRemoved`/`TournamentUpdate` and then **exactly one trailing `tournament_list_update()`** when anything changed (`:575-577`); `tournament_summaries()` (`:261-269`) returns the **whole sorted list**. No `TournamentAdded`/`TournamentUpdated` deltas exist anywhere. Consequence: `subscribeTournamentsOver` must be a **pure pass-through with zero derived state**, unlike `subscribeLobbyOver`'s upsert/removal reducer (`brokerClient.ts:602-644`).

**(B) The charter's static-assertion shorthand would fail on the file's own necessary import.** `tournamentClient.ts` must write `import type { PhaseSocket } from "./openPhaseSocket"` — the module path contains the string "openPhaseSocket". A bare `not.toContain("openPhaseSocket")` cannot pass. Both `openPhaseSocket` and `.close(` are re-scoped to **call sites**, each with a positive control.

**(C) The `Error` frame carries no correlator.** `LobbyServerMessage::Error{message, code?}` (`protocol.rs:769-773`) has no tournament code. `resolveGuestOver` has the identical property (`brokerClient.ts:389-393`). Phase 1 matches the precedent and documents it. See Identity/Provenance Contract, B3.

**Unprobed and labelled as such:** no Rust probe was compiled to dump serialized bytes (disk: 1.9T used/18G free — an isolated `CARGO_TARGET_DIR` would cost a full engine dependency rebuild the box cannot absorb, and S9 forbids the cargo lock regardless). Server→client shapes are derived from serde derive semantics plus committed round-trip tests (`protocol.rs:1252-1416`), not a byte dump. Client→server shapes ARE literal-measured. Mitigation: Step 5.4's fixture is typed `TournamentView` and round-tripped, so a shape error is a compile error at the fixture.

---

## Step 1 — Applicable skills

| Skill | Verdict |
|---|---|
| `/add-frontend-component` | **N/A.** No component, no JSX — phase 4. |
| `/add-engine-effect`, `/add-keyword`, `/add-trigger`, `/add-static-ability`, `/add-replacement-effect`, `/add-interactive-effect`, `/casting-stack-conditions`, `/add-ai-feature-policy`, `/add-card-data-pipeline` | **N/A.** Zero Rust changes. |
| `/add-engine-variant` | **N/A.** Mirrors of already-shipped Rust enums, not new engine surface. |
| `/card-test` | **N/A.** No cast-pipeline test. |
| `/oracle-parser` | **N/A.** No `crates/engine/src/parser/` change. |
| `/project-reference` | **Applies** — S9 verification recipe. |

No checklist governs this phase — a data-mirroring + client-library task, governed by CLAUDE.md's frontend-layering rule and the house wire-mirror test convention.

---

## Step 2 — Analogous trace

**Traced feature: `resolveGuestOver`, the P2P guest-join RPC over a borrowed `PhaseSocket`.**

```
crates/lobby-broker/src/protocol.rs:648-655   LobbyClientMessage::JoinGameWithPassword
  → crates/lobby-broker/src/broker.rs                Broker::handle_* → Vec<Outbound>{ToSelf|ToSubscribers}
  → crates/lobby-broker/src/protocol.rs:809-820      LobbyServerMessage::PeerInfo
  → client/src/adapter/types.ts:409-417              interface PeerInfo
  → client/src/services/openPhaseSocket.ts:17-46     PhaseSocketTransport / PhaseSocket
  → client/src/services/brokerClient.ts:310-457      resolveGuestOver
  → client/src/services/brokerClient.ts:83-95        ResolveResult
  → client/src/services/brokerClient.ts:597-659      subscribeLobbyOver
  → client/src/services/__tests__/brokerClient.test.ts:12-45   MockWebSocket + makePhaseSocket
  → client/src/services/__tests__/brokerClient.test.ts:109-189 the five-path RPC suite
  → client/src/stores/multiplayerStore.ts:1665-1699  pendingJoinRpcAborts (phase 2's template)
```

`resolveGuestOver`'s body is the exact structure `requestOver` generalizes: `readyState` guard (`:349`) → `signal?.aborted` pre-guard (`:357`) → message listener with correlator filter (`:366-394`) → close listener (`:396`) → abort listener (`:405`) → timeout timer (`:416`) → single `cleanup()` (`:428`) → attach-then-send (`:435-455`).

**Secondary trace — the wire-mirror test convention:** `client/src/adapter/__tests__/searchControlWireTypes.test.ts` — typed fixture, `JSON.parse(JSON.stringify(x))` round-trip, `@ts-expect-error` blocks (`:75-92`), discharged for `noUnusedLocals` at `:90-91`.

---

## Step 3 — Files read

**Modify/create (4 scope paths):** `client/src/adapter/types.ts`; `client/src/services/tournamentClient.ts` (new); `client/src/adapter/__tests__/tournamentTypes.test.ts` (new); `client/src/services/__tests__/tournamentClient.test.ts` (new).

**Read for pattern, not modified:** `client/src/services/brokerClient.ts` (all); `client/src/services/openPhaseSocket.ts:1-120`; `client/src/services/__tests__/brokerClient.test.ts:1-330`; `client/src/adapter/__tests__/boundary-guardrails.test.ts` (all); `client/src/adapter/__tests__/rustEnumVariants.ts` (all); `client/src/adapter/__tests__/searchControlWireTypes.test.ts` (all); `client/src/adapter/draft-adapter.ts:300-331`; `client/tsconfig.app.json`; `crates/lobby-broker/src/protocol.rs:440-903, 1060-1431`; `crates/lobby-broker/src/tournament.rs:70-395, 685-770`; `crates/lobby-broker/src/broker.rs:120-160, 255-290, 310-345, 522-580, 1060-1345`; `client/src/adapter/ws-adapter.ts`; `client/src/stores/multiplayerStore.ts` (phase-2 context only).

---

## Step 4 — Architectural sections

### Pattern Coverage

Assessed against the charter's class attribution — phase 1 is the infrastructure phase (edges 1→2, 1→4, 1→5). Mirrors cover the **entire** tournament wire surface (13 types, all 7 client + 5 server variants). `requestOver` covers **all seven** RPCs by construction — one primitive, not seven bespoke bodies. `subscribeTournamentsOver` covers all three broadcast variants exhaustively via `switch`.

**Extra generality earned:** `requestOver` is not tournament-specific in its body; `resolveGuestOver`/`lookupJoinTargetOver` are latent future callers (not refactored onto it here — out of scope-path).

### Sizing

**3 units**, matching the charter's phase-1 row exactly:

| # | Unit | Registration surfaces | Discriminating test | Depends on |
|---|---|---|---|---|
| U1 | Tournament wire type mirrors (16 exported types) | `client/src/adapter/types.ts` | Probed-bytes fixture type-checks + round-trips; flattened `PairingOutcome` fails to compile | — |
| U2 | `requestOver` + 7 RPC helpers + `TournamentRpcResult` | `client/src/services/tournamentClient.ts` | `it.each` 7×5 paths, distinct discriminants; frame bytes match Rust literals; socket never closed | U1 |
| U3 | `subscribeTournamentsOver` | same file | Zero-send attach→inbound→detach cycle, paired positive delivery reach-guard | U1 |

**Source scope-paths: 2** (`types.ts`, `tournamentClient.ts`). Test files excluded per counting rule.

**Phase-fit re-adjudication:** T1 fires (3 units ≥ 2). T2 does not fire (2 < 13). Conjunction does not fire — unchanged from the charter's table. G1's fix adds one matrix row and one test inside the already-listed `tournamentClient.test.ts`, plus header prose — no new unit, no new scope path.

**Dependency edges:** U1 → U2, U1 → U3. Implementation order: U1, U2, U3.

### Building Blocks

| Block | Location | Use |
|---|---|---|
| `PhaseSocket` / `PhaseSocketTransport` | `openPhaseSocket.ts:17-46` | Borrowed socket type, type-only import. Already declares exactly the members `requestOver` needs. |
| `resolveGuestOver`'s five-path structure | `brokerClient.ts:310-457` | The shape `requestOver` generalizes (not imported — generalized). |
| `ResolveResult` discriminated union | `brokerClient.ts:83-95` | The result-union convention. `TournamentRpcResult<T>` follows it, generic in payload. Not extended — reason set is P2P-join-specific. |
| `MockWebSocket` + `makePhaseSocket` | `brokerClient.test.ts:12-45` | Fake-socket harness, **reused by copy** (file-local, unexported; house convention is per-test-file harnesses). This phase's copy gains one local extension: a `listenerCount(type)` tally (see §5.7), confined to this file. |
| `repoRoot()` | `adapter/__tests__/rustEnumVariants.ts:6-8` | Imported, not copied. |
| `JSON.parse(JSON.stringify(x))` + `@ts-expect-error` | `searchControlWireTypes.test.ts:45-92` | Wire-mirror test idiom, adopted verbatim including the `toBeDefined()` discharge (`:90-91`). |
| Argument/marker-scoped `expect(source)` regexes | `boundary-guardrails.test.ts:69,84,93` | Static-source-assertion convention — dominant (3 regex-scoped vs 2 bare `toContain`), not exclusive. |

**New helpers:** `requestOver` (the phase's purpose); a private `matchReply<T>(replyType, code)` matcher factory (not exported — six of seven helpers share its filter, one needs tag-only; its doc comment records B6 for the `"TournamentUpdate"` case). **Rejected:** `rustEnumVariants`-based drift guards over the 5 small enums — a new cross-language test category the charter did not scope into phase 1; the charter's actual discriminating property (fixture-compiles/flattened-fails) is what this plan delivers instead.

### Logic Placement

| Concern | Placement | Justification |
|---|---|---|
| Tournament wire type shapes | `adapter/types.ts` | S1 — where every other wire mirror lives. |
| Frame construction + reply correlation + transport lifecycle | `services/tournamentClient.ts` | Mirrors `brokerClient.ts`'s role. |
| Socket acquisition, closing, credentials | **Not here — phase 2** | Charter goal item 1. Helpers take a borrowed socket. |
| `SubscribeLobby`/`UnsubscribeLobby` frames | **Not here — phase 2** | Seam S3 — non-negotiable, see B6/S3 discussion. |
| List reduction / upsert / removal | **Nowhere** — broker sends the whole list | Finding 0.9(A). |
| Standings sorting / ranking | **Nowhere in the client** | Server-provided, pre-ordered. Phase 1 adds no comparator. |
| Arity/bracket legality | **Nowhere in the client** | Broker is the sole authority; `MatchArity` mirrors as a bare number with no client validation. |
| Distinguishing "my reply" from "someone else's broadcast" on `TournamentUpdate` | **Nowhere — the wire carries no discriminator** | B6. Any client-side guess (sequence counter, timing heuristic, view-diffing) would be inventing provenance the broker never sent — strictly worse than a documented limitation because it would be silently wrong. |
| Error-message classification | `tournamentClient.ts`, transport-vs-server split only | Deliberately not `classifyError`'s substring-matching (`brokerClient.ts:572-586`) — that would be re-interpreting engine data. Raw `message` passed through; phase 5 renders via `t("errors.serverRejected", {message})`. |

### Rust Idioms

- **Discriminated unions**, never flag bags — `PairingOutcome` is `"Bye" | {Forfeit:…} | {Reported:…}`, mirroring the Rust doc's own reasoning (`tournament.rs:350-354`).
- **`TournamentRpcResult<T>`** generic in payload, one union, one `ok` discriminant, one `reason` enum.
- **`reason`** is a closed 4-member string-literal union: `"rejected"|"aborted"|"timeout"|"connection_lost"` — a strict superset of `ResolveResult`'s 3-way collapse, chosen so each of the 5 test paths asserts a distinct discriminant and phase 3 can key distinct copy without a phase-1 revision.
- **Exhaustive `switch`, no `default`**, over the 3 inbound tags in `subscribeTournamentsOver` and over `reason` at consumers.
- **`type X = number`** aliases for `MatchArity`/`PairingId`, matching `types.ts:10-12`'s convention — documentation-only, stated as such.
- **`import type`** for every type-only import — `verbatimModuleSyntax: true` makes this mandatory for compilation, not stylistic (§5.8).
- **Snake_case field names preserved verbatim** — no camelCase translation layer.

### Nom Compliance

**N/A.** No `crates/engine/src/parser/` file touched; zero Rust changes. No parsing dispatch — only `switch(msg.type)` over a closed wire-tag set.

### Extension vs Creation

**Predominantly extension.** U1 extends `types.ts`'s wire-mirror pattern (append-only banner). U2 extends the `services/*Over(socket,…)` borrowed-socket RPC pattern and the `ResolveResult` convention; the one new thing (`requestOver`) is a generalization of an already-duplicated pattern, not a new one. U3 **deliberately departs** from `subscribeLobbyOver` in two documented, tested ways: sends no frames (S3) and holds no derived state (0.9(A)).

### Analogous Trace

See Step 2, re-verified line-exact.

### Variant Discoverability

**N/A.** No engine enum variant added; these are mirrors of Rust enums already shipped in PRs 1-3.

### Identity / Provenance Contract

Six bindings.

**B1 — Reply correlation for the six code-bearing RPCs.** Latched at invocation, closes over `code`, compared via `data.code === code`. Cleanup on any of 5 terminal paths. **Multi-authority hostile fixture:** two in-flight tournaments, wrong-code frame must not settle; paired positive: right-code frame settles `{ok:true}`. **Known limitation:** discriminates tournaments, not requests — see B6.

**B2 — `TournamentCreated` is the sole tag-only exception.** Code is broker-minted (`env.new_game_code()`, `broker.rs:1096`) — no value to correlate on at send time. Documented limitation: two concurrent `createTournament` calls cannot be distinguished. Hostile fixture: `TournamentJoined` delivered first must not settle; paired positive: subsequent `TournamentCreated` does.

**B3 — The `Error` reply is un-correlatable, by wire design.** `code?: Option<ServerErrorCode>` is an error *class*, not a tournament code, and usually absent (`skip_serializing_if`). Matches `resolveGuestOver`'s identical, identical-reason behavior. Hostile fixture: two in-flight RPCs, one `Error` → both settle `rejected` with the same message (positive, not vacuous).

**B4 — Token authority is per-code and never ambient.** `organizerToken`/`playerToken` required positional params, never module state. Makes phase 2's credential hostile fixture decidable at the store level — phase 1 provides no place for a wrong token to originate.

**B5 — `TournamentSummary.player_count` is active entrants.** `active_player_count()` (`protocol.rs:538`), not `players.len()`, pinned by `summary_counts_active_players_while_the_view_keeps_dropped_ones` (`:1341-1351`). Doc comment carries the distinction — load-bearing for phase 4's hostile fixture.

**B6 — `TournamentUpdate` is both a point reply and a broadcast, and carries no request-vs-broadcast discriminator.** *(New this revision.)*

- **Emission sites, measured, not inferred.** `ToSelf` exactly once: `handle_get_tournament` (`:1177`). `ToSubscribers` from five handlers plus the reaper: `handle_join_tournament` (`:1168`) — a different player joining; `handle_start_tournament_round` (`:1206`); `handle_report_match_result` (`:1268`) — a different player reporting their own pod; `handle_drop_from_tournament` (`:1309`) — a different player dropping; `handle_end_tournament` (`:1334`); `reap_expired`'s `Abandoned` arm (`:550-555`) — the server itself, no client action at all.
- **The limitation, precisely.** While any of the four gated helpers (`startTournamentRoundOver`, `reportMatchResultOver`, `dropFromTournamentOver`, `endTournamentOver`) is in flight, any other actor's unrelated action on the same tournament broadcasts a `TournamentUpdate` with our `code`, settling our promise `{ok:true}` with *that actor's* view — ahead of our own outcome. Since `cleanup()` has already run, a subsequent real `Error` for our actually-rejected request has no listener and is silently dropped. Not exotic — routine traffic in a live multi-entrant event.
- **Scope.** Only the four gated helpers are exposed. `getTournamentOver` is safe: it receives a genuine `ToSelf` reply, so even a racing foreign broadcast still carries a current view of the tournament the caller asked about. `joinTournamentOver`/`createTournamentOver` correlate on tags (`TournamentJoined`/`TournamentCreated`) no broadcast site emits.
- **Decision: match the wire's actual behavior and document it — same posture as B3.** Every candidate client-side workaround (sequence counter the broker doesn't echo, timing heuristics, view-diffing) is fabricating provenance the broker never sent, and would be *silently* wrong rather than *documented* as a known limitation.
- **Multi-authority hostile fixture:** Verification Matrix row 12a.
- **Mitigation lives in phase 5**, by design already present there — see the expanded `DEFERRED(phase 5)` row.

### Verification Matrix

| # | Claim | Seam / entry point | Test | Revert-failing assertion | Hostile fixture → first production branch | Positive reach-guard |
|---|---|---|---|---|---|---|
| 1 | Probed bytes type-check and round-trip | `types.ts` / `TournamentView` | `tournamentTypes.test.ts` → round-trip test | `expect(JSON.parse(JSON.stringify(view))).toEqual(view)` | Fixture carries every shape at once | Non-empty length assertions at each level |
| 2 | **Flattened `PairingOutcome` fails to compile** | `PairingOutcome` union | `tournamentTypes.test.ts`. **Surfaces under `type-check`, not `vitest`** | `@ts-expect-error` on a flattened literal | Sibling negatives: missing `game_wins`, string-not-object `Forfeit`, near-miss `"Drawn"` literal | 4 well-formed positive assignments, each fixture discharged via `toBeDefined()` (`noUnusedLocals`) |
| 3 | Both `Tiebreaks` arms representable | `Tiebreaks` union | `tournamentTypes.test.ts` | Round-trip both arms; `@ts-expect-error` cross-arm | Cross-arm field bleed | `"HeadToHead" in standings[0].tiebreaks` |
| 4 | 7 request frames byte-match Rust literals | 7 helpers' `ws.send` | `tournamentClient.test.ts` `it.each` | Exact string match to `protocol.rs:1143-1172` literals | `totalRounds:null`; `outcome:"Draw"` | `ws.send` called exactly once per helper |
| 5 | **Socket never closed, any helper, any path** | all 7 helpers + subscription | `tournamentClient.test.ts` `it.each` 7×5 | `ws.close` not called | All 5 paths incl. socket-drop, timeout | Paired settled-discriminant assertion per cell |
| 6 | Each of 5 paths settles with a distinct discriminant | `requestOver` | same `it.each` | Exact `{ok,reason}` per cell | Fake timers, real `AbortController`, `ws.fireClose()` | Success cell asserts payload shape too |
| 7 | **Subscription sends nothing across a full cycle** | `subscribeTournamentsOver` | `tournamentClient.test.ts` | `ws.send` called 0 times at 3 checkpoints (attach/inbound/detach) | Detach while `OPEN` — exactly where `subscribeLobbyOver` DOES send | Same test asserts all 3 handlers actually fire on delivery |
| 8 | No handler fires after detach | detach fn | `tournamentClient.test.ts` | Post-detach delivery leaves counter unchanged | Double-detach | Pre-detach increment (proves counter is live) |
| 9 | **Static: no socket ownership, no subscription frames** | source text | `tournamentClient.test.ts`. **Comment-unaware regexes — see §5.2's wording constraint** | 3 scoped-`null` regexes | Call-site scoping keeps the required doc comment legal | 3 positive controls + import-line positive control |
| 10 | Wrong-code reply does not settle | `matchReply` | `tournamentClient.test.ts` | Still-pending assertion via `Promise.race` | Two live tournaments | Right-code frame settles afterward |
| 11 | `TournamentCreated` tag-only, filter still real | matcher | `tournamentClient.test.ts` | `TournamentJoined` first must not settle | — | Subsequent `TournamentCreated` settles |
| 12 | Uncorrelated `Error` settles every in-flight RPC | `requestOver`'s `Error` arm | `tournamentClient.test.ts` | Both settle `rejected`, same message | Two codes in flight | Both are positive settlements |
| **12a** | **Foreign same-code broadcast settles a gated helper; later `Error` cannot re-settle** *(new — B6)* | `matchReply("TournamentUpdate", code)` under the 4 gated helpers | `tournamentClient.test.ts` part C | `endTournamentOver` in flight; deliver foreign `TournamentUpdate{code:"AAA111", view:FOREIGN_VIEW}` → settles `{ok:true, value.view:FOREIGN_VIEW}`; subsequent `Error` does NOT re-settle (value unchanged) AND `ws.listenerCount("message")===0` | Byte-identical shape to caller's own would-be reply — `data.code===code` matches it, can't discriminate. Sibling: same fixture with `reportMatchResultOver`. Adjacent negative: foreign frame with `code:"BBB222"` must not settle | Identical fixture **without** the foreign frame: settles `{ok:true, value.view:OWN_VIEW}` on the real reply — proves a real settlement path is observed, not just "nothing ever settles" |
| 13 | Malformed JSON ignored, not thrown | listener `try/catch` | `tournamentClient.test.ts` | No throw; valid frame after still settles | No-`data` frame | Valid frame settling |
| 14 | Protocol version unmoved | script | command | exit 0 | — | Already run: exit 0 |
| 15 | Tree compiles and lints | whole phase | `type-check`, `lint` | Both exit 0 | — | — |

**`DEFERRED(phase 5)` — `ToSubscribers`-only delivery on a real subscribed socket.** Structurally impossible here (§0.3: 4 RPCs emit no `ToSelf`; no mounted/subscribed socket exists until phase 5). Discharged by phase 5's explicitly-labelled row. Interim verification: rows 4-6, 10-13, 12a, plus green `tsc -b --noEmit`.

**B6's mitigation is that same phase-5 row, and phase 5 must read it that way.** Phase 5's plan already requires rendered state come from the ambient subscription broadcast, never the RPC return value — exactly the mitigation for B6 (a foreign broadcast that settles a gated promise early carries a *newer, real* view, so ambient rendering is correct regardless of which frame settled the promise). **Consequence phase 5 must not overlook:** its server-rejection-alert verification cannot treat the four gated RPCs' `{ok:false}` as a complete rejection detector — some rejections are masked by a same-code foreign broadcast racing the `Error` frame. Phase 5 must either (a) surface rejections from the ambient view alone, or (b) explicitly accept this known gap in its own plan. Silently assuming `{ok:false}` catches every rejection would ship a quietly lossy alert path under exactly the multi-entrant traffic a real event produces.

**`DEFERRED(phase 2)` — abort-on-reconnect.** `requestOver` accepts `AbortSignal`, row 6 proves `"aborted"` settles correctly. Registration in `pendingJoinRpcAborts` is the store's job. Discharges into phase 2's existing bullet.

---

## Step 5 — Step-by-step implementation

### 5.0 — Environment (once)

```bash
cd C:/git/phase/.claude/worktrees/tournament-organizer-pr4-frontend/client
pnpm install --frozen-lockfile
```

### 5.1 — `client/src/adapter/types.ts` (U1) — append-only

S1 discipline: re-read the tail before editing (4499-line high-collision file). `Edit` with unique `old_string`, never `Write`. Append one banner section at EOF.

Sixteen exported types: `MatchArity`, `PairingId`, `ScoringPolicy`, `TournamentStatus`, `BracketShape`, `PodOutcome`, `PairingOutcome`, `Tiebreaks`, `TournamentStanding`, `PlayerSummary`, `TournamentPairingView` (named to avoid the S2 collision), `TournamentSummary` (with B5's active-vs-total doc comment), `TournamentView`, `TournamentCreatedReply`, `TournamentJoinedReply`, `TournamentUpdateReply`. Every doc comment cites the Rust source location it mirrors.

### 5.2 — `client/src/services/tournamentClient.ts` (new) — module header

Must state, in the file's own words:

1. This module owns no socket — every function takes a borrowed `PhaseSocket`; `openPhaseSocket` imported for its type only.
2. This module owns no subscription — `subscribeTournamentsOver` sends neither `SubscribeLobby` nor `UnsubscribeLobby`, a deliberate departure from `subscribeLobbyOver`, with the S3 refcount reasoning inline.
3. Four of seven RPCs produce no point reply at all on success — only `ToSubscribers` (§0.3).
4. **(New, B6)** `TournamentUpdate` is both the `GetTournament` point reply and a broadcast, with no request-vs-broadcast discriminator beyond `code`. Emitted as `ToSubscribers` by `handle_join_tournament` (`:1168`), `handle_start_tournament_round` (`:1206`), `handle_report_match_result` (`:1268`), `handle_drop_from_tournament` (`:1309`), `handle_end_tournament` (`:1334`), `reap_expired`'s `Abandoned` arm (`:550-555`); `ToSelf` only from `handle_get_tournament` (`:1177`). Consequence: another actor's action on the same tournament can settle a gated helper `{ok:true}` before this caller's own outcome arrives. Stated, not worked around — the wire carries no correlator to work around it with. Callers needing to know whether their own mutation landed should read the ambient subscription's view, not this promise.
5. The `Error` frame carries no correlator (B3), citing `protocol.rs:769-773`.

**Wording constraint — mandatory.** The header and every comment in this file must express the socket-ownership property without ever writing the literal substring `.close(`. Write "does not close the borrowed socket — its owner does," never "never calls `.close()`." The static assertion's third regex (§5.7F / matrix row 9) is comment-unaware; the natural phrasing would trip the guard against the very file it guards.

### 5.3 — Result union and options

`TournamentRpcFailure` (4-member closed union), `TournamentRpcResult<T>`, `TournamentRequestOptions` (`{signal?, timeoutMs?}`, default 10_000, `Infinity` supported), minimal `InboundFrame`, `DEFAULT_TIMEOUT_MS = 10_000`.

### 5.4 — `requestOver` (the primitive)

`requestOver<T>(socket, frame, match, opts = {}): Promise<TournamentRpcResult<T>>`. Body follows `resolveGuestOver`'s shape exactly: readyState guard → abort pre-guard → message listener (trust-boundary parse, `match(msg)`, unfiltered `Error` arm) → close listener → abort listener → timeout timer → single `cleanup()` → listeners attach before send → `ws.send`.

**Never closes the borrowed socket on any path — the owner does.** (Phrased this way deliberately; do not restate using the literal `.close(`.) `cleanup()` runs exactly once on every terminal path and removes all registrations — matrix row 12a asserts this directly via the harness's listener tally, since a settled promise cannot visibly re-settle.

### 5.5 — Matcher factory, the seven helpers, and the subscription

`matchReply<T extends {code:string}>(replyType, code)` — filters `msg.type === replyType && (code === null || data.code === code)`. `code === null` only for `TournamentCreated` (B2). Doc comment records B6 for the `"TournamentUpdate"` case: the `code` conjunct discriminates tournaments, not requests.

Seven helpers as before (§5.5's frame literals per §0.2/§0.3), each of the four gated ones (`startTournamentRoundOver`, `reportMatchResultOver`, `dropFromTournamentOver`, `endTournamentOver`) carrying a one-line doc comment pointing at the module header's B6 paragraph.

`subscribeTournamentsOver(socket, handlers): () => void` — attaches a message listener, exhaustive `switch(msg.type)` over the 3 broadcast tags, each arm null-guarding `msg.data`. Sends nothing, ever. Holds no derived list state. Detach only removes the listener — never sends, never closes.

### 5.6 — `client/src/adapter/__tests__/tournamentTypes.test.ts` (new)

Modelled on `searchControlWireTypes.test.ts`. Read §5.8's "Executor environment facts" first. `PROBED_VIEW` fixture carrying every shape at once; round-trip test; flattened-`PairingOutcome`-fails-to-compile test (4 positives + 4 `@ts-expect-error` negatives, each discharged with `toBeDefined()`); both-`Tiebreaks`-arms test; S2 collision-pinning test (`TournamentPairingView` vs `draft-adapter.ts`'s `PairingView`, cross-assignment `@ts-expect-error` both directions); bare-number `MatchArity`/`PairingId` test.

### 5.7 — `client/src/services/__tests__/tournamentClient.test.ts` (new)

Copy `MockWebSocket` + `makePhaseSocket` from `brokerClient.test.ts:12-58` verbatim, **plus one local extension**: override `addEventListener`/`removeEventListener` to maintain a per-type tally, exposing `listenerCount(type): number` (delegating to `super`). Required by row 12a — a leaked listener after settlement is otherwise undetectable. Confined to this file's copy; `brokerClient.test.ts` untouched.

**A.** Frame bytes (`RUST_FRAMES` literals verbatim from `protocol.rs:1143-1172`), `it.each` over 7 helpers.

**B.** 5 paths × 7 helpers × socket-stays-open (`it.each`).

**C.** Correlation: wrong-code non-settlement; `TournamentCreated` tag-only; uncorrelated-`Error`-settles-both; **and row 12a**: two distinguishable fixture views (`OWN_VIEW`: `status:"Completed"`, `players.length:2`; `FOREIGN_VIEW`: `status:"InProgress"`, `players.length:3`). (1) Positive reach-guard: `endTournamentOver` + `OWN_VIEW` delivered → settles `{ok:true, value.view:OWN_VIEW}`. (2) Fresh socket, `endTournamentOver` + `FOREIGN_VIEW` delivered → settles `{ok:true, value.view:FOREIGN_VIEW}`. (3) Then `Error` delivered → value still `{ok:true, view:FOREIGN_VIEW}`, `listenerCount("message")===0`, no unhandled rejection. (4) Sibling: repeat (2) with `reportMatchResultOver`. (5) Adjacent negative: foreign frame with `code:"BBB222"` must not settle a pending `endTournamentOver(…,"AAA111",…)`.

**D.** Malformed frames.

**E.** Subscription zero-sends (3-checkpoint), post-detach no-op.

**F.** Static source assertion — `readFileSync` via `repoRoot()` (imported, not new); three call-scoped regexes with positive controls each, plus a positive control on the real `import type {...PhaseSocket...}` line.

**Comment-awareness caveat**, written beside the regexes: these three run against raw file text and are comment-unaware — `.close(`-matching prose in a doc comment would trip a genuine-looking S3 violation. §5.2's wording constraint is what keeps the header legal. Deliberately not fixed by comment-stripping first — no `stripComments`-style helper exists anywhere under `client/src`, and inventing one is out of scope.

### 5.8 — Verification (S9: direct `pnpm`, never Tilt, never cargo)

```bash
cd C:/git/phase/.claude/worktrees/tournament-organizer-pr4-frontend
node scripts/check-protocol-version.mjs
pnpm --dir client exec vitest run \
  src/adapter/__tests__/tournamentTypes.test.ts \
  src/services/__tests__/tournamentClient.test.ts
pnpm --dir client exec vitest run src/services/__tests__/brokerClient.test.ts   # untouched sibling stays green
pnpm --dir client run type-check
pnpm --dir client run lint
```

`./scripts/tilt-wait.sh` returns exit 3 here ("cannot answer") — never report as a build failure. `cargo fmt`/`clippy`/`test-engine` N/A.

**Executor environment facts** (measured from `client/tsconfig.app.json`):
- **Matrix row 2 fails at compile time, not runtime.** `@ts-expect-error` is compile-time; an unused directive is reported by `tsc`, not vitest. Revert-check (a) below surfaces under `pnpm --dir client run type-check` — vitest alone stays green.
- **`noUnusedLocals: true`, `noUnusedParameters: true`** (`:17-18`). Every `@ts-expect-error` fixture const must be referenced at runtime — precedent: `searchControlWireTypes.test.ts:88-91` discharges via `toBeDefined()`.
- **`verbatimModuleSyntax: true`** (`:12`). `import type` for `PhaseSocket` is mandatory for compilation, not stylistic.

**Revert-check before commit:** (a) flatten `PairingOutcome` → `type-check` must fail (vitest alone will not catch this); (b) add a `SubscribeLobby` send to `subscribeTournamentsOver`'s attach → both the zero-send test and the static assertion must fail; (c) delete the `data.code !== code` guard in `matchReply` → row 10 **and** row 12a's adjacent negative must both fail. Revert all three.

---

## Deferral compliance

| Deferred item | Landing phase | Where phase 1 stops |
|---|---|---|
| Store actions, credentials, socket acquisition | 2 | Every helper takes a borrowed socket; tokens are required per-call params; no module state. |
| All `SubscribeLobby`/`UnsubscribeLobby` frame-sending | 2 | Sent zero times; guarded by runtime test + static assertion. Load-bearing for S3. |
| `pendingJoinRpcAborts` registration | 2 | `requestOver` accepts `AbortSignal`; registration is the store's. |
| End-to-end `ToSubscribers`-only delivery on a real subscribed socket | 5 | Fake socket proves the matcher only. |
| **Mitigation of B6** | 5 | Phase 1 documents (B6) and pins the behavior (row 12a); builds no client-side correlator. Phase 5's ambient-broadcast design is the mitigation. |
| i18n for user-visible error copy | 3 | `message` passed through raw, no `t()`. |
| Rendering of any mirrored type | 4 | No `.tsx`, no JSX. |
| Route/nav reachability | 5 | No `App.tsx`, no `navItems.tsx`. |

**Files touched: exactly the 4 scope paths.** All others read-only. `types.ts` append-only per S1. Protocol version untouched per S8.
