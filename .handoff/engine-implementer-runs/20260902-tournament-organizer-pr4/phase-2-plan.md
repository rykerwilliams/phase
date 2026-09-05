# Phase 2 Implementation Plan — Store integration: credentials, unified subscription refcount, abort wiring (revision 3)

## What changed in this revision

| Finding | Fix applied | Where |
|---|---|---|
| **M1 (material)** — R11's eviction fixtures did not discriminate the behavior they were added to prove. Traced against the real comparator `(a,b) => map[a].updatedAt - map[b].updatedAt \|\| (a<b?-1:a>b?1:0)`: under a frozen clock the `updatedAt` term is a total tie, so the victim is simply the lexicographically-smallest non-protected code. Both named fixtures put the just-written/protected code at the lexicographic **maximum**, so revert-check #6 (drop `protect`) picked the *same* victim either way and stayed green with the bug present. Separately, no R11 case used distinct `updatedAt` values at all, so an implementation that dropped the `updatedAt` term entirely and sorted by code alone passed every case. | **(1)** Frozen-clock fixture inverted: hold `"T02"`…`"T33"` (32 codes), then write and protect **`"T01"`**, which sorts lexicographically *before* all of them. Keeping `protect` evicts `"T02"`; dropping it makes `"T01"` the lexicographic minimum of all 33 and evicts `"T01"` itself — **both halves of the assertion flip**, so revert-check #6 is now real. **(2)** New **R11b** row and new named test `evicts by write time even when the tournament codes sort the other way`: distinct, non-frozen `updatedAt` values assigned in the *reverse* of code order, so the oldest entry is the lexicographically-largest code. New revert-check **#8** (drop the `updatedAt` term) breaks it. **(3)** *(carried, same defect class — flagged, not silent)* the all-digit ordering fixture had the identical problem: `"0001"` is **not** a canonical array index (`ToString(ToUint32("0001")) === "1" ≠ "0001"`), so it enumerates in insertion order and an unsorted implementation picked the same victim as a sorted one. Replaced with unpadded canonical-index codes `"9"`…`"40"` protecting `"8"`, where numeric enumeration order (`"9"` first) and lexicographic order (`"10"` first) genuinely disagree; new revert-check **#10** (delete the `.sort(...)`) breaks it. | Verification Matrix R11 + new R11b; §5.1 doc comment; §5.7 suite A + revert-checks #8/#10 |
| **M2 (material)** — the two i18n keys named by revision 2's F4 were undecidable by their consumer. `TournamentRpcFailureReason` has exactly four members (`tournamentClient.ts:105-109`, re-verified), and a **local** refusal from `runGatedTournamentRpc` settled through the same `{ok:false, reason:"rejected", message}` shape as a genuine broker `Error`. Phase 5 had no typed signal to branch on — only the English message text, which is the exact string-matching anti-pattern F4's own reasoning rejected. | **Option A chosen** (justification in §5.5 and Rust Idioms). `MultiplayerActions` declares the four gated actions as returning a store-local `GatedTournamentRpcResult<T> = TournamentRpcResult<T> \| TournamentNotAuthorized`, where `TournamentNotAuthorized = { ok: false; reason: "not_authorized"; role: TournamentRole; message: string }`. `runGatedTournamentRpc`'s local-refusal branch returns that shape instead of `{reason:"rejected"}`. New matrix row **R18** proves the discriminator appears on the local path and *never* on a genuine server rejection, plus revert-check **#9**. This is a deliberate, named departure from the charter's literal `reason:"rejected"` wording — recorded in Extension vs Creation. | §5.5, `MultiplayerActions`, §0.5, Sizing U3, Matrix R7/R9/R18, Rust Idioms, Extension vs Creation, deferral table |
| **m1 (minor)** — F5's stated justification was factually wrong: the plan said (in three places) that `isRecord` "is outside this phase's scope path". `isRecord` is at `multiplayerStore.ts:541`, which **is** phase 2's one and only source scope path. | Re-verified on disk: `isRecord` has **five** other call sites — `:591` (`normalizeRememberedHostConfig`), `:659`, `:662` (`formatConfig`/`deck_size` projection), `:709` (`loopDetection`), `:719` (seat validation). The real reason is now stated: narrowing `isRecord` for `normalizeTournamentCredentials`'s benefit alone would be an **unscoped behavior change to five unrelated callers** in the remembered-host-config and migration paths. Corrected in all three places, not just the two named (leaving a known-false claim in the third would be worse). | §5.1 doc comment; deferral table; Building Blocks row; "Rejected" bullet |
| **m2 (minor)** — R6's primary claim (`tournamentListSnapshot` is verbatim, never merged/filtered) had no named test. Both R6-labelled tests were really about credential fan-out (F3's reach-guard, F6's no-write path). | New named test in §5.7 suite A: `seeds a late tournament subscriber with the pre-removal list after a TournamentRemoved`. Delivers a `TournamentListUpdate`, then a `TournamentRemoved` for one of its entries, then attaches a *late* subscriber and asserts the seeded array still contains the removed entry (identity-equal to the delivered array). R6's Test column now names it. | Verification Matrix R6; §5.7 suite A |
| **cosmetic** — `:1584` (`get().showToast`, inside `openPhaseSocket().catch()`) was cited as evidence that `get`/`set` are in scope in the `"open"` branch. | Now leads with `set({ serverInfo })` at **`:1599`**, which is inside the `"open"` branch itself; `:1584` is kept only as the narrower citation for `get` specifically. Verified on disk. | §5.4(c), §5.6 |
| **cosmetic** — `§0.3` cited the `SubscribeLobby` outbound vec as `broker.rs:317-332`. | Measured: the arm head is `:317`, the `vec![…]` literal is **`:331-336`**, the arm closes at `:337`. `UnsubscribeLobby`'s arm is `:339-343` with `vec![Outbound::RemoveSubscriber]` on **`:342`**. Corrected, and recorded as charter drift (the charter's S3 carries the same `:317-332` / `:339-342` citations). | §0.3 |

Everything else — F2 (the attach-order swap), F3 (R6/R9 reach-guards), F6 (the `get`-threading, verified consistent across every call site), F7 (the `:1033` citation), the core S3 unified-refcount design, both predicates and their reconnect-window justification, the two-optional-token `TournamentCredential` design, the `capTournamentCredentials` *algorithm* (only its fixtures changed), the cast-free `runGatedTournamentRpc` composition, the persistence lifecycle, all Step 0/1/2/3 content, the Sizing verdict (4 units / 1 source scope-path), and matrix rows R1–R5, R8, R10, R12–R17 — is carried forward **verbatim**.

---

**Run:** PR 4/4 tournament-organizer rollout (phase-rs/phase#7718) · **Mode:** phase-plan · **Phase 2 of 5**
**Worktree:** `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend` · branch `feat/tournament-organizer-pr4-frontend` · `PHASE_BASE_SHA 973d6932c5b4c956846bccb89fc4901e3b5d2a37` (= phase 1's accepted candidate, already in this branch's history).

**Scope paths (exactly two, from the charter):**
```
client/src/stores/multiplayerStore.ts
client/src/stores/__tests__/multiplayerStore.tournament.test.ts   (new)
```

---

## Step 0 — Premise verification (phase-2-scoped)

### 0.1 `multiplayerStore.ts` — measured current shape (1810 lines)

| Item | Current line(s) | Measured behavior |
|---|---|---|
| `pendingJoinRpcAborts: Set<AbortController>` | `:142` (doc `:135-141`) | Module-level. Doc names only `resolveGuest` / `lookupJoinTarget`. |
| `lobbySubscribers: Set<(games: LobbyGame[]) => void>` | `:153` (doc `:144-152`) | Module-level. Doc already names the ref-counting bug this structure fixed *for lobby subscribers only*. |
| `lobbySnapshot: LobbyGame[] \| null` | `:155` | Last `LobbyUpdate`; seeds late subscribers; read by `findLobbyGameByCode` (`:158-161`). |
| `lobbyAttachDetach: (() => void) \| null` | `:164` (doc `:162-163`) | The single per-socket detach returned by `subscribeLobbyOver`. |
| `subscribeLobby` action | `:1719-1747` | `wasEmpty = lobbySubscribers.size === 0` → `subscribeLobbyOver(...)`; else seed from `lobbySnapshot`. Returned unsubscribe: `delete`, then `if (lobbySubscribers.size === 0) { lobbyAttachDetach?.(); lobbyAttachDetach = null; lobbySnapshot = null; }`. |
| `onStateChange` | `:1595-1631` | `"open"` → `set({serverInfo})` (**`:1599`**) + `if (lobbySubscribers.size > 0) lobbyAttachDetach = subscribeLobbyOver(...)` (`:1605-1606`) + `settle(socket)`. `"reconnecting"` → drain `pendingJoinRpcAborts`, `lobbyAttachDetach = null` (**dropped, not called**). `"offline"` → drain aborts, `settle(null)`. |
| `closeSubscriptionSocket` | `:1641-1650` | drain aborts → `lobbyAttachDetach?.()` → `null` → `lobbySubscribers.clear()` → `lobbySnapshot = null` → `subscriptionReconnect?.close()` → `null`. |
| `resolveGuest` (the template) | `:1652-1678` | `await ensureSubscriptionSocket()` → `if (!socket) return {ok:false, reason:"connection_lost", message:"Lobby connection unavailable. Check your server address."}` → `const ac = new AbortController(); pendingJoinRpcAborts.add(ac);` → `try { return await …Over(socket, …, { signal: ac.signal, … }); } finally { pendingJoinRpcAborts.delete(ac); }`. **Never closes a socket.** |
| `lookupJoinTarget` | `:1680-1701` | Same template verbatim — two instances, so the template is established, not incidental. |
| `MultiplayerState` | `:270-…`; `playerId: string` at `:271` | `playerId` is `crypto.randomUUID()` (`:996`), persisted (`:1791`). |
| initial state object | `:996-1022` | Plain literal inside `create(...)(persist((set, get) => ({…})))`. |
| `partialize` | `:1790-1795` | Persists exactly `playerId`, `displayName`, `serverAddress`, `lastHostConfig`. **Every persisted value is JSON-safe; no `Map`/`Set` is persisted anywhere.** |
| `merge` | `:1780-1789` | `{...current, ...saved, lastHostConfig: normalizeRememberedHostConfig(saved.lastHostConfig)}`. Header comment: *"Persisted state is external input… hydrate current-version blobs through the same normalizer."* |
| `migratePersistedMultiplayerState` | `:776-795` | Mutates and returns **the same record**; no key whitelist. `version: 5` at `:1751`. |
| `isRecord` | `:541-543` | File-local `(value: unknown) => value is Record<string, unknown>`. Reusable. Implemented as `value !== null && typeof value === "object"` — **an array satisfies it**; see §5.1's documented edge case. **Five other call sites measured on disk: `:591`, `:659`, `:662`, `:709`, `:719`.** Not modified by this phase — see §5.1 and the deferral table for the reason (m1). |
| `MultiplayerSet` / `MultiplayerGet` | `:797-802` | Exported-shape type aliases; the file's convention for module-level helpers is `fn(set, …)` / `fn(get, …)` (`resetServerHostSession(set)` `:804`, `savePregameHostSession(get, data)` `:815`). `MultiplayerGet` is declared at `:802` and already consumed at `:816`, `:847`, `:905`, `:962`. |
| `lobbySubscribers` / `lobbySnapshot` / `lobbyAttachDetach` | `:153-164` | The exact structure `tournamentSubscribers` / `tournamentListSnapshot` / `tournamentAttachDetach` mirrors. |
| `setServerAddress` | `:1026-1036` | Calls `closeSubscriptionSocket()` on address change at **`:1033`** (`:1032` is the guarding `if`) — a second teardown path my changes must stay correct under. |

**Charter drift found and corrected (1 of 2):** the charter/S3 cites `brokerClient.ts:650` / `:656` for the two frames; measured they are at **`:650`** (`SubscribeLobby`) and **`:656`** (`UnsubscribeLobby`) — exact. `subscribeLobbyOver` itself is `:597-659` and its doc comment naming `UnsubscribeLobby` spans `:594-595`. No material drift.

### 0.2 `subscribeLobbyOver` is the sole frame authority, and it couples frames to listener attachment

`client/src/services/brokerClient.ts:597-659`:

```ts
ws.addEventListener("message", listener);
if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "SubscribeLobby" }));   // :649-651
return () => {
  ws.removeEventListener("message", listener);
  if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "UnsubscribeLobby" })); // :653-658
};
```

**This is the single most load-bearing measured fact for the whole phase.** `brokerClient.ts` is **not** in phase 2's scope paths, so the frames cannot be moved. Therefore the unification cannot be "extract the frames into a store-owned acquire/release pair" — it must be **"the combined refcount decides when `subscribeLobbyOver` is invoked and when its returned detach is invoked."** `subscribeLobbyOver`'s call/detach *is* the acquire/release primitive; phase 2 only replaces the predicate that gates it. See Extension vs Creation.

Both frames are guarded by `readyState === WebSocket.OPEN`, so a release against a dead socket is a silent no-op — which is why `"reconnecting"` can drop `lobbyAttachDetach` without calling it.

**Consequence for §5.3's statement ordering (F2):** because the `SubscribeLobby` frame is emitted *inside* `subscribeLobbyOver`, the statement that binds `lobbyAttachDetach` is also the statement that provokes the broker's reply. Any listener that must catch that reply has to be bound before it.

### 0.3 Broker side — `SubscribeLobby` is the only path to the tournament list (verified in source)

`crates/lobby-broker/src/broker.rs`, `LobbyClientMessage::SubscribeLobby` arm — arm head at **`:317`**, arm closes at **`:337`**, and the outbound `vec![…]` literal itself is **`:331-336`**:

```rust
vec![
    Outbound::AddSubscriber,
    Outbound::ToSelf(LobbyServerMessage::LobbyUpdate { games }),
    Outbound::ToSelf(LobbyServerMessage::TournamentListUpdate { tournaments }),
    Outbound::SendPlayerCountToSelf,
]
```
with the source's own comment (`:322-328`): *"The tournament list rides the same initial push as the game list… Emitted unconditionally — an empty list is a meaningful answer ('no events')."* The `UnsubscribeLobby` arm is **`:339-343`**, whose body is `vec![Outbound::RemoveSubscriber]` on **`:342`**.

**Charter drift found and corrected (2 of 2):** the charter's S3 and its revision-3 note 2 both cite `broker.rs:317-332` for the add and `:339-342` for the remove. `:317` is the arm head, not the start of the vec; the vec literal is `:331-336`. The remove citation `:339-342` spans the arm head through the vec but stops one line short of the arm's close (`:343`). Neither drift is material — the `Outbound` variants and their ordering are exactly as the charter describes — but the corrected ranges are used throughout this plan.

**Two consequences that shape the design, and the second one is new to this plan:**

1. `AddSubscriber` is the only insertion into the delivery set (S3's premise — confirmed).
2. **`ToSelf(TournamentListUpdate)` fires exactly once per `SubscribeLobby`, and there is no `GetTournamentList` RPC** — phase 1 shipped seven helpers and none of them fetches the list. So the *only* ways a client ever learns the tournament list are (a) that one `ToSelf` push, or (b) a subsequent `TournamentListUpdate` broadcast caused by someone else's mutation. **If the store attaches the tournament listener only when a tournament subscriber exists, then the lobby-subscriber-first ordering loses that one push forever and the tournament page renders an empty list until an unrelated actor mutates a tournament.** This is the exact "renders but never updates" failure S3 exists to prevent, arriving through the ordering S3's own bullets do not enumerate. It is why the design below attaches the tournament listener at *acquisition* time rather than at *first-tournament-subscriber* time, and caches a `tournamentListSnapshot` to seed later subscribers. See Verification Matrix row **R5**.

### 0.4 Wire tags — the corrected regex

`LobbyClientMessage::UnsubscribeLobby` (lowercase `s`), sent by `brokerClient.ts:656` as `{"type":"UnsubscribeLobby"}`. The charter's illustrative `(?:Un)?SubscribeLobby` does **not** match it — confirmed twice already in phase 1's implementation and review. This plan uses `(?:Subscribe|Unsubscribe)Lobby` wherever a pattern over both tags is needed, and prefers exact parsed-tag equality over regex entirely where possible (see §5.7's `tally` helper).

### 0.5 Phase 1's shipped exports — read from the real files, not the plan

`client/src/services/tournamentClient.ts` (529 lines) exports: `TournamentRpcFailureReason`, `TournamentRpcResult<T>`, `TournamentRequestOptions`, `requestOver`, `CreateTournamentRequest`, `createTournamentOver`, `joinTournamentOver`, `getTournamentOver`, `startTournamentRoundOver`, `reportMatchResultOver`, `dropFromTournamentOver`, `endTournamentOver`, `TournamentSubscriptionHandlers`, `subscribeTournamentsOver`.

`TournamentRpcResult<T> = { ok: true; value: T } | { ok: false; reason: TournamentRpcFailureReason; message: string }` (`:111-113`), with `TournamentRpcFailureReason` at **`:105-109`** having exactly four members — **re-verified on disk this revision**:

```ts
export type TournamentRpcFailureReason =
  | "rejected"
  | "aborted"
  | "timeout"
  | "connection_lost";
```

Its doc comment (`:95-104`) defines each member by *what the transport or the broker did*, and `rejected` specifically as *"the broker answered `Error`; `message` is its text verbatim."*

**Revision-3 correction (M2).** Revision 2 asserted "phase 2 adds no new reason — the missing-token failure reuses the existing `"rejected"` member." That is now **rejected as wrong on two counts**, and phase 2 introduces exactly one store-local failure shape instead:

1. It contradicts phase 1's own documented contract. A local refusal never contacts the broker, the broker never answered `Error`, and `message` is client-authored English rather than "its text verbatim." Filing it under `"rejected"` makes the type comment a lie.
2. It is undecidable by the consumer. Both a local refusal and a genuine broker rejection settle as `{ok:false, reason:"rejected", message}`, so phase 5 could only tell them apart by matching on the English message string — the exact anti-pattern revision 2's own F4 reasoning rejected when it refused to route client copy through `errors.serverRejected`.

`tournamentClient.ts` is phase 1's frozen file and is outside phase 2's scope paths, so the new member cannot be added to `TournamentRpcFailureReason`. It is added as a **store-local union widening** in `multiplayerStore.ts` — phase 2's sole source scope path — see §5.5 and Extension vs Creation.

Confirmed by reading `subscribeTournamentsOver` (`:485-529`): it calls **only** `ws.addEventListener` / `ws.removeEventListener`; there is no `ws.send` anywhere in its body or its detach. S3's constraint on phase 1 held. Its handlers are three optional callbacks (`onListUpdate(tournaments)`, `onTournamentUpdate(code, view)`, `onTournamentRemoved(code)`), each null-guarded on `msg.data` before dispatch.

`requestOver` bails `{ok:false, reason:"connection_lost"}` when `ws.readyState !== WebSocket.OPEN` and pre-guards `signal?.aborted` — so a controller aborted by an earlier `reconnecting` transition still produces a clean `"aborted"` rather than a hang.

`client/src/adapter/types.ts:4501-4728` carries the 16 mirrors; phase 2 imports `TournamentSummary`, `TournamentView`, `PairingId`, `PodOutcome`, `MatchArity`, `ScoringPolicy`, `BracketShape`, and the three `*Reply` types.

### 0.6 Test-harness facts (measured)

- `client/src/stores/__tests__/` holds 15 suites. **`multiplayerStore.visualAvatars.test.ts` contains zero `vi.mock` calls** and loads the real store — so the store's whole import graph resolves cleanly under vitest with nothing stubbed.
- `multiplayerStore.test.ts` mocks `../../services/brokerClient` wholesale (`:111-113`, exposing only `openBrokerClient`) — **my new file must not do that**, or `subscribeLobbyOver` becomes a stub and every frame assertion in this phase becomes vacuous.
- Its `openPhaseSocket` mock (`:115-139`) supplies exactly `{ HandshakeError, openPhaseSocket, withReconnect }` — the three value imports the store and `brokerClient` take from that module. Copyable shape.
- Its `withReconnect` driver (`:262-272`) is the pattern for firing `onStateChange`: return `{ current: () => current, close: vi.fn() }` and notify from an async continuation *after* the handle is returned, because the store reads `subscriptionReconnect?.current()` inside the `"open"` branch (`:1597`).
- `localStorage` is stubbed via `vi.hoisted` (`:4-26`) — required, since `persist` writes on every `set`.
- Its fake socket at `:251-261` already uses `ws: { readyState: 1, addEventListener, removeEventListener, send }`, proving `WebSocket.OPEN` resolves in this environment.

### 0.7 `client/tsconfig.app.json` (measured)

`strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true`, `verbatimModuleSyntax: true`, `noFallthroughCasesInSwitch: true`. **Absent:** `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`. Consequences: `import type` is mandatory for every type-only import; `record[key]` is typed non-`undefined` (so a presence test needs an explicit `in` / `?.` check).

### 0.8 S9 environment — re-measured on this worktree

`client/node_modules` **absent**. `tilt get uiresource clippy` fails → exit 3 ("cannot answer") — never a build failure. Phase 2 changes no Rust; cargo N/A, no cargo lock.

### 0.9 What is not probed, labelled as such

No live broker was run, no browser session driven. Every broker claim is read from `broker.rs` source; every store claim is read from `multiplayerStore.ts` at HEAD. Runtime claims (frame counts, listener counts, abort propagation, rehydrate survival) are discharged by the vitest suite in §5.7 against a fake socket with real spies. The one thing the fake socket cannot prove is that a real broker honours `AddSubscriber` for tournament frames — that is `DEFERRED(phase 5)`.

**Labelled-unprobed, added in revision 2 (F2):** the fake socket's `send` is a bare `vi.fn()` and never echoes a reply, synchronously or otherwise. No test in §5.7 can therefore observe an ordering violation between the two statements in `attachSharedSubscription`. The fix for that is not a new test that would have to simulate a transport this codebase does not have — it is to make the ordering structurally correct, which §5.3 now does.

**Probed by hand-trace, not by execution, this revision (M1):** `capTournamentCredentials`'s comparator was traced symbolically against each proposed fixture, in both the "keep `protect`" and "drop `protect`" directions, and (for R11b) in both the "keep the `updatedAt` term" and "sort by code alone" directions. The traces are written out inline in §5.7 suite A's fixture notes so a reviewer can re-check them without running anything, and each is bound to a numbered revert-check that must be executed for real before commit.

---

## Step 1 — Applicable skills

| Skill | Verdict |
|---|---|
| `/add-frontend-component` | **N/A here, `DEFERRED(phase 4/5)`.** |
| `/add-engine-effect` etc. (all engine skills) | **N/A.** Zero Rust changes. |
| `/add-engine-variant` | **N/A.** No engine enum variant. `TournamentRole` and `TournamentNotAuthorized`'s `reason` are client-side TS unions in a store file, not engine enums; the gate governs `crates/engine` types. |
| `/card-test` | **N/A.** |
| `/oracle-parser` | **N/A.** |
| `/project-reference` | **Applies** — S9 verification recipe. |

No skill checklist governs this phase. Governed by CLAUDE.md's frontend-layering rule, the multi-agent surgical-edit rule (1810-line shared file), and the store's own established conventions.

---

## Step 2 — Analogous trace

**Primary traced feature: the `resolveGuest` action template and the `subscribeLobby` multiplexed-refcount mechanism, end to end.**

```
crates/lobby-broker/src/protocol.rs        LobbyClientMessage::{SubscribeLobby, UnsubscribeLobby, JoinGameWithPassword}
  → crates/lobby-broker/src/broker.rs      SubscribeLobby arm :317-337 (vec :331-336) → [AddSubscriber,
                                             ToSelf(LobbyUpdate), ToSelf(TournamentListUpdate),
                                             SendPlayerCountToSelf]
                                           UnsubscribeLobby arm :339-343 (vec :342) → [RemoveSubscriber]
  → client/src/services/openPhaseSocket.ts:17-46          PhaseSocket / PhaseSocketTransport / withReconnect
  → client/src/services/brokerClient.ts:310-457           resolveGuestOver  (the RPC body requestOver generalizes)
  → client/src/services/brokerClient.ts:597-659           subscribeLobbyOver (sends BOTH frames; :650, :656)
  → client/src/stores/multiplayerStore.ts:142             pendingJoinRpcAborts
  → client/src/stores/multiplayerStore.ts:153-164         lobbySubscribers / lobbySnapshot / lobbyAttachDetach
  → client/src/stores/multiplayerStore.ts:1546-1639       ensureSubscriptionSocket + onStateChange
  → client/src/stores/multiplayerStore.ts:1641-1650       closeSubscriptionSocket
  → client/src/stores/multiplayerStore.ts:1652-1678       resolveGuest              ← the action template
  → client/src/stores/multiplayerStore.ts:1719-1747       subscribeLobby            ← the refcount mechanism
  → client/src/stores/multiplayerStore.ts:1790-1795       partialize                ← the persistence partition
  → client/src/components/lobby/LobbyView.tsx:115-191     the `cancelled` consumer idiom (phase 5's copy target)
  → client/src/stores/__tests__/multiplayerStore.test.ts:111-139, 250-285   the mock/driver harness
```

**Secondary trace — the persisted-field lifecycle**, followed because `tournamentCredentials` is the first new persisted key added since v5:

```
multiplayerStore.ts:993-995   create(persist((set,get)=>({…}), {…}))
  → :996-1022                 initial state literal            (default value lives here)
  → :270-…                    interface MultiplayerState       (type lives here)
  → :541-543                  isRecord                          (external-input guard helper; 5 other callers)
  → :588-600                  normalizeRememberedHostConfig     (the normalizer convention)
  → :776-795                  migratePersistedMultiplayerState  (mutate-in-place, no whitelist)
  → :1780-1789                merge                             (normalizer applied on every hydrate)
  → :1790-1795                partialize                        (the persistence partition)
```

That trace settles three things without guessing: a new key needs **no version bump** (migrate has no whitelist and `merge` spreads `current` first, so an old blob simply keeps the default); it **must be JSON-safe** (a `Map` would persist as `{}` — every currently-persisted value is a plain string or plain object, and both `playerNames` and `toasts`, which *are* `Map`s, are deliberately excluded from `partialize`); and it **must be normalized on hydrate**, because the file's own `merge` comment declares persisted state to be external input.

**Tertiary trace — the consumer idiom phase 5 will copy** (`LobbyView.tsx:115-191`): `let cancelled = false` → `const detach = await subscribeLobby(cb)` → `if (cancelled) { detach?.(); return; }` → `if (detach === null) { onServerOffline?.(); return; }` → cleanup calls `lobbyDetach?.()`.

---

## Step 3 — Files read

**Modify (1 source scope path):** `client/src/stores/multiplayerStore.ts` — read `:1-200`, `:260-305`, `:355-431`, `:535-600`, `:650-730`, `:765-830`, `:985-1045`, `:1540-1810` in full before editing. (`:650-730` added this revision to re-verify `isRecord`'s five other call sites for m1.)

**Create (1 test path, excluded from T2 counting):** `client/src/stores/__tests__/multiplayerStore.tournament.test.ts`.

**Read for pattern and dependency, not modified:** `client/src/services/tournamentClient.ts` (all 529 lines; `:95-113` re-read this revision for M2); `client/src/adapter/types.ts:4501-4728`; `client/src/services/brokerClient.ts:1-20, 588-659`; `client/src/stores/__tests__/multiplayerStore.test.ts:1-164, 240-295`; `client/src/stores/__tests__/multiplayerStore.visualAvatars.test.ts`; `client/src/components/lobby/LobbyView.tsx:112-196`; `client/tsconfig.app.json`; `crates/lobby-broker/src/broker.rs:310-350` (re-read this revision for the §0.3 line-range correction).

---

## Step 4 — Architectural sections

### Pattern Coverage

Assessed against the charter's class attribution. Phase 2 is the store-integration phase on dependency edges 1→2 and 2→5; renders nothing by construction.

- **All seven** tournament RPCs get their socket through **one** acquisition path and **one** abort-registration path.
- **Both** token-gated authorities (organizer, player) route through **one** gated runner parameterized by `TournamentRole` — the rejected shape was `runOrganizerRpc` + `runPlayerRpc`, a two-member sibling cluster.
- **Every** subscriber of the shared lobby connection is counted by **one** refcount, expressed as a function over set membership so adding a third stream is "add its set to the sum."
- Credential storage is keyed by tournament code and holds *n* concurrent events with bounded eviction, not one "current tournament."
- **Every** locally-refused gated action produces **one** typed discriminator (`reason: "not_authorized"` + `role`), so a consumer distinguishes "this browser holds no authority" from "the server said no" without ever reading a message string — for both roles today and any third authority later.

### Sizing

**4 units**, matching the charter's phase-2 row exactly.

| # | Unit | Registration surfaces | Discriminating test | Depends on |
|---|---|---|---|---|
| U1 | Persisted `tournamentCredentials` map | `TournamentCredential`; `MultiplayerState.tournamentCredentials`; initial-state literal; `normalizeTournamentCredentials`; `rememberTournamentCredential` + `capTournamentCredentials`; `merge`; `partialize` | Rehydrate survival + merge-not-replace + eviction cap (protect **and** primary-key directions) + `TournamentRemoved` deletion | — |
| U2 | Unified `SubscribeLobby` refcount | `tournamentSubscribers`, `tournamentListSnapshot`, `tournamentAttachDetach`, `lobbySubscriptionRefCount`, `attachSharedSubscription`, `detachSharedSubscription`, `acquireLobbySubscription`, `releaseLobbySubscription`; rewritten `subscribeLobby`; new `subscribeTournaments` | Attach direction (1st subscriber sends exactly 1 `SubscribeLobby`, 2nd sends none) **and** detach direction (last-of-either-kind sends `UnsubscribeLobby`) | U1 (fan-out deletion) |
| U3 | Seven store actions | `TournamentRole`, `TournamentNotAuthorized`, `GatedTournamentRpcResult`, `runTournamentRpc`, `runGatedTournamentRpc`, 7 public actions | Two-tournament hostile fixture: matching code's token on the wire; missing token → `{ok:false, reason:"not_authorized", role}` with zero send, and a genuine server `Error` on the same action → `reason:"rejected"`, never `"not_authorized"` | U1, U2 |
| U4 | Abort + reconnect wiring | `pendingJoinRpcAborts` doc widened; `onStateChange` `"open"`/`"reconnecting"`; `closeSubscriptionSocket` | In-flight RPC settles `"aborted"` on reconnect; reconnect re-sends `SubscribeLobby` | U2, U3 |

**Source scope-paths: 1** (`multiplayerStore.ts`). Test file excluded.

**Phase-fit re-adjudication:** T1 fires (4 ≥ 2). T2 does not fire (1 < 13). Conjunction does not fire — matches charter row exactly. **This revision changes no unit count and no scope-path count:** M1 is a fixture and matrix change inside U1's already-named surfaces; M2 adds two type declarations to U3's already-named `runGatedTournamentRpc` surface (a return-type widening, not a new mechanic — the gate itself is unchanged and still single-authority); m1 is a comment correction; m2 is a test name; the cosmetics are citations.

**Dependency edges:** U1→U2, U1→U3, U2→U3, U2→U4, U3→U4. **Implementation order: U1, U2, U3, U4.**

### Building Blocks

| Block | Location | Use |
|---|---|---|
| `resolveGuest` / `lookupJoinTarget` body | `:1652-1701` | The action template, followed verbatim. |
| `pendingJoinRpcAborts` | `:142` | Reused, not duplicated — no new drain sites needed. |
| `subscribeLobbyOver` | `brokerClient.ts:597-659` | Unchanged; phase 2 changes only *when* it's called/detached. |
| `subscribeTournamentsOver` | `tournamentClient.ts:485-529` | Attached once per socket alongside `subscribeLobbyOver`, fanned out. |
| The seven `*Over` helpers | `tournamentClient.ts:304-454` | Called by the seven actions. |
| `TournamentRpcResult<T>` | `tournamentClient.ts:111-113` | Reused unchanged as the *wire* result. `GatedTournamentRpcResult<T>` widens it store-side rather than redefining it (M2). |
| `isRecord` | `:541-543` | Reused in `normalizeTournamentCredentials`. **Not modified** — it has five other callers (`:591`, `:659`, `:662`, `:709`, `:719`) whose current behavior, array-acceptance included, is load-bearing for the remembered-host-config and migration paths; narrowing it for one new caller's benefit would be an unscoped behavior change to all five (m1). Its array-acceptance is documented at the new call site instead. |
| `normalizeRememberedHostConfig` + `merge` | `:588-600`, `:1780-1789` | The normalizer-on-hydrate convention copied. |
| `MultiplayerSet` / `MultiplayerGet` | `:797-802` | Signatures for new module-level helpers. `MultiplayerGet` is already consumed at `:816/847/905/962`, so threading it into `attachSharedSubscription` / `acquireLobbySubscription` / `forgetTournamentCredential` (F6) follows the file's own convention rather than introducing one. |
| `lobbySubscribers`/`lobbySnapshot`/`lobbyAttachDetach` | `:153-164` | Structure `tournamentSubscribers`/`tournamentListSnapshot`/`tournamentAttachDetach` mirrors. |
| `MockWebSocket`-style fake + `withReconnect` driver | `multiplayerStore.test.ts:115-139, 251-272` | Copied, minus the `brokerClient` mock. |

**New helpers:** `lobbySubscriptionRefCount()`; `attachSharedSubscription`/`detachSharedSubscription` (bind both listener attachments + frame pair as one operation); `acquireLobbySubscription`/`releaseLobbySubscription` (the two predicates, kept separate — see Rust Idioms); `rememberTournamentCredential`/`capTournamentCredentials`/`normalizeTournamentCredentials` (pure, unit-testable); `runTournamentRpc`/`runGatedTournamentRpc`.

**New types:** `TournamentCredential`; `TournamentRole`; `TournamentNotAuthorized` + `GatedTournamentRpcResult<T>` (M2 — see §5.5 for why a store-local widening rather than a fifth `TournamentRpcFailureReason` member).

**Rejected:** a separate `tournamentAborts` set (parallel drains for no gain); a per-code `TournamentView` cache in the store (phase 5's pages own view state); an integer `sharedSubscriptionCount` (see Rust Idioms); an `Array.isArray` rejection inside `normalizeTournamentCredentials` or a change to `isRecord` (m1 — `isRecord` is in this phase's scope path, but it has five other callers whose behavior is not phase 2's to change, and the per-entry validation already makes the array case inert); reusing `"rejected"` for local refusals (M2 — see §0.5); and Option B for M2, i.e. having phase 5 re-read `tournamentCredentials` to decide the copy (see §5.5's decision record).

### Logic Placement

| Concern | Placement | Justification |
|---|---|---|
| Frame construction, reply correlation | `tournamentClient.ts` — untouched | Phase 1's frozen file. |
| `SubscribeLobby`/`UnsubscribeLobby` emission | `brokerClient.ts:650/656` — untouched, gated by the store | Frames cannot move; the store owns *when*, `subscribeLobbyOver` owns *how*. |
| The one shared refcount | `multiplayerStore.ts`, module scope | Both subscriber sets already live at module scope beside the socket they govern. |
| Credential storage | `multiplayerStore.ts` persisted state | Tokens are per-browser authority, exactly like `serverAddress`/`playerId`. |
| Token → RPC argument resolution | `runGatedTournamentRpc` | Single authority; a call site reading the map itself is the "inspecting cost structure at a call site" anti-pattern. |
| **Local-refusal classification** (`"not_authorized"` + `role`) | `runGatedTournamentRpc`, returned as data | The gate is the only place that knows *why* it refused, and it knows at refusal time. Encoding it as a typed field is the store answering the question once; the alternative makes every consumer re-derive it, either from message text (string matching) or by re-reading the credential map (a second, racy authority). The frontend must not re-interpret store data — CLAUDE.md's display-layer rule. |
| Credential deletion on `TournamentRemoved` | Inside the fan-out | The one place every such frame arrives, attached for the whole subscription lifetime. Because it is attached for the whole lifetime, the no-op path must be genuinely free of writes — see F6. |
| Which tournaments exist | Nowhere derived — verbatim cache | Broker always sends the whole list (phase 1 finding 0.9(A)). |
| Standings/pairing order, active-vs-total, arity legality | Nowhere in the client | Server authority. |
| `isOrganizer`/`myPairing`/labelling | `DEFERRED(phase 4)` | Presentation logic over a `TournamentView`. |
| Error copy/keys | `DEFERRED(phase 3/5)` | `message` passed through verbatim; the two client-authored strings are pre-named as `errors.notOrganizer` / `errors.notEntered`, **selected by `result.role` on a `reason: "not_authorized"` result** (M2), never by message text. |
| Unmount race, gating as rendered UI | `DEFERRED(phase 5)` | No component exists; store-level primitives + R15 land here. |

### Rust Idioms

*(TypeScript file; the section's intent — typed unions over booleans, exhaustive matching, reuse over invention, correct abstraction layering — applies unchanged.)*

- **The refcount is derived from set membership, never an incremented integer.** `lobbySubscriptionRefCount() = lobbySubscribers.size + tournamentSubscribers.size`. `add`/`delete` are idempotent, so double-subscribe/double-release cannot miscount — which is what makes phase 5's `if (cancelled) { detach?.(); return; }` safe alongside a React cleanup that may run the same detach twice.
- **Two predicates, not one, because they ask different questions.** Attach asks "is the subscription currently bound?" (`lobbyAttachDetach === null`). Release asks "does anyone still want it?" (`refCount() === 0`). Collapsing into `refCount()===1`/`===0` is wrong across the reconnect window, where the count is legitimately > 0 while the handle is `null`.
- **`TournamentRole = "organizer" | "player"`** is a closed union naming a domain concept, not a boolean, not a field name.
- **Exhaustive `switch`, no `default`**, on `TournamentRole` (`noFallthroughCasesInSwitch: true` already on).
- **The local refusal is a typed union member carrying `role`, not a `"rejected"` with special English (M2).** A refusal decided locally and a refusal decided by the broker are different events with different consumers, so they get different `reason` members — and the local one carries the `TournamentRole` it refused on, so a consumer needs neither a message match nor a second read of the credential map to pick its copy. This is the "typed enum, never a bool, never a string sniff" rule applied one layer up, and it is also an **abstraction-layer separation**: `TournamentRpcFailureReason` is a *wire* vocabulary (each member documents what the transport or broker did); "this browser holds no token" belongs one level up, in the store's own vocabulary. Hence `GatedTournamentRpcResult<T> = TournamentRpcResult<T> | TournamentNotAuthorized` — a widening at the store boundary — rather than a fifth member inside phase 1's frozen wire union.
- **Reuse over new types:** the three ungated actions return phase 1's `TournamentRpcResult<T>` completely unchanged, and the four gated ones return it widened by exactly one member. No wire type is redefined, no result shape is re-invented, and every failure member keeps the same `{ ok:false; reason; message }` skeleton so `if (!result.ok) …` narrowing works uniformly.
- **Read-before-write for no-op detection** (F6). `forgetTournamentCredential` checks `code in get().tournamentCredentials` *before* entering `set`. Returning `{}` from a zustand updater leaves the state reference unchanged, so consumers don't re-render — but the `set` call still runs, and `persist` still writes to `localStorage`. Since the `TournamentRemoved` fan-out is attached for the whole life of the shared subscription, the no-credential case is the common case, and it must cost nothing.
- **Plain `Record<string, TournamentCredential>`, not `Map`** — forced by persistence (a persisted `Map` serializes to `{}`, silent total data loss).
- **Deterministic eviction ordering** by `(updatedAt, code)`, not object key order. `updatedAt` is the *primary* key and carries the actual LRU semantics; `code` is a pure tiebreak that exists only so a frozen or coarse clock cannot make eviction depend on `Object.keys` enumeration, which orders canonical array-index keys (`"9"`, `"40"`) numerically ahead of the insertion-ordered rest. **Both halves are separately tested** — R11 pins the tiebreak and the `protect` exemption, R11b pins the primary key (M1).
- **`import type`** for every type-only import (mandatory under `verbatimModuleSyntax`).

### Nom Compliance

**N/A.** No `crates/engine/src/parser/` file touched; zero Rust changes.

### Extension vs Creation

**Overwhelmingly extension, with one deliberate, tested generalization.** U1 extends the persisted-state pattern exactly as `lastHostConfig`'s lifecycle. U2 **generalizes an existing mechanism** — the store already multiplexes one `subscribeLobbyOver` attachment across subscribers and documents the ref-counting bug that structure fixed; phase 2 widens the *domain* of that refcount from one set to two. The rejected alternative (a second independent gate re-invoking `subscribeLobbyOver`) reintroduces the exact bug the existing doc comment says it fixed, one connection-level up. U3 extends the twice-instantiated `resolveGuest` template to seven more instances via one runner. U4 is pure reuse of `pendingJoinRpcAborts`.

**Departure 1 from the charter's literal text — the tournament listener attaches at *acquisition* time**, not at *first-tournament-subscriber* time, with a `tournamentListSnapshot` seeding late subscribers — because §0.3 shows the lobby-first ordering silently loses the one-and-only `ToSelf(TournamentListUpdate)` push. Carries its own matrix row (**R5**) rather than being asserted as opinion. **Within that acquisition, the tournament listener is bound before the frame is sent** (F2) — the statement order is part of the design, not an implementation detail.

**Departure 2 from the charter's literal text — the local-refusal `reason` (M2).** The charter's phase-2 verification plan says a gated action with no token *"must return `{ok:false, reason:"rejected"}` without hitting the wire."* This plan returns `{ok:false, reason:"not_authorized", role, message}` instead. Stated plainly so it is adjudicated, not smuggled:

- **The charter's substantive requirement is preserved exactly.** The action still returns a failure result, still refuses before `ensureSubscriptionSocket`, still puts zero frames on the wire, and still mutates no state. R7's hostile fixture and revert-check #4 are unchanged in substance — only the asserted `reason` literal moves.
- **The literal wording could not be honoured without breaking phase 1's contract.** `tournamentClient.ts:100` documents `rejected` as *"the broker answered `Error`; `message` is its text verbatim"*. A local refusal satisfies neither clause. The charter wrote `"rejected"` at a time when the only vocabulary in view was phase 1's four-member wire union; it did not adjudicate the store-local widening, because the ambiguity it creates for phase 5 was not yet visible.
- **It is entirely inside phase 2's scope.** The widening lives in `multiplayerStore.ts` and touches no frozen file; `TournamentRpcFailureReason` gains no member and `tournamentClient.ts` is not opened.
- **It removes a consumer-side anti-pattern rather than adding one.** Without it, phase 5's only route to the two i18n keys the charter's own deferral chain requires is matching on English message text.

**Rejected alternative for departure 2 (Option B): "phase 5 re-reads `tournamentCredentials` itself."** Rejected on three counts. (i) It creates a second authority for a question `runGatedTournamentRpc` already answered — the exact "call site inspects the cost structure" anti-pattern this plan's Logic Placement table forbids one row above. (ii) It is racy: the credential map can change between the action's gate check and the consumer's read (a `TournamentRemoved` fan-out deletes entries asynchronously), so the two authorities can disagree about the same result. (iii) It does not actually decide the ambiguous case — a genuine server rejection while a credential *is* held still arrives as bare `{reason:"rejected"}` with client-indistinguishable provenance, so the hole M2 identified would remain open, merely made rarer.

### Analogous Trace

See Step 2.

### Variant Discoverability

**N/A.** No engine enum variant added. `TournamentRole`, `TournamentNotAuthorized`, `GatedTournamentRpcResult` and every other new exported identifier are swept for name collisions across `client/src` (§5.0 step 2) — expect zero hits outside `tournamentClient.ts`'s own `*Over` names.

### Identity / Provenance Contract

**B1 — Organizer authority is bound per tournament code, at creation, never ambient.** Source: `TournamentCreated.organizer_token`, minted by the broker, delivered only as a point reply. Keyed under the *reply's* code (phase 1's `TournamentCreated` is tag-only correlated — B6 below). Binding time: on `result.ok` inside `createTournament`. Latched, not live. Storage: `tournamentCredentials[code].organizerToken`, persisted. Consumer: `runGatedTournamentRpc(..., "organizer", ...)` only. Invalidation: `TournamentRemoved` deletion; LRU eviction; malformed-entry drop on hydrate. Hostile fixture: **R7** — credentials for two codes; the matching code's token goes on the wire; a third code with no credential returns `{ok:false, reason:"not_authorized", role:"organizer"}` with zero send.

**B2 — Player authority is bound per code, at join, together with the `player_key` it was minted for.** The `playerKey` written is the one actually sent on the join frame, captured before the await (not re-read from `get().playerId` afterward). Consumer: `runGatedTournamentRpc(..., "player", ...)`. Hostile fixture: **R8** — a code holding only an `organizerToken` must fail `reportMatchResult` with `reason:"not_authorized", role:"player"` and zero sends; the same code with a `playerToken` added reaches the wire.

**B1 ∧ B2 coexistence — the merge contract.** Because `CreateTournament` does not auto-join the creator, both authorities on one code arise from two separate replies at two separate times. The write path must therefore accumulate, never replace: a join after a create must not erase `organizerToken`, and a create after a join must not erase `playerToken`/`playerKey`. Fixture: **R11** (merge half).

**B3 — The shared `SubscribeLobby` subscription is owned by the socket, counted across both subscriber kinds, re-established per socket generation.** Authority: `lobbyAttachDetach`; count is `lobbySubscribers.size + tournamentSubscribers.size`. Binding time: first subscriber of either kind, and again on each `"open"` while count > 0. Live per socket generation, not latched — the handle is dropped (not invoked) on `"reconnecting"`. Storage: module scope, deliberately outside store state. Multi-authority hostile fixture: **R3/R4** — one of each subscriber kind, releasing in both orders; only the second release may emit `UnsubscribeLobby`, and exactly one `SubscribeLobby` was emitted across the episode.

**B4 — `tournamentListSnapshot` is a verbatim cache with no derived content and a per-socket lifetime.** Bound on every `onListUpdate`; cleared in `detachSharedSubscription` so a reconnect cannot serve a stale list as current. Hostile fixture: **R5/R6** — `TournamentRemoved` without a trailing list push leaves the snapshot unchanged (proved by the late-seeded subscriber still receiving the removed entry, m2); a late subscriber is seeded from the cache.

**B5 — (from phase 1, consumed here) `TournamentUpdate` carries no request-vs-broadcast discriminator.** Phase 2's obligation: no store state is set from a gated action's `{ok:false}`, no credential deleted, no toast raised on gated failure. Fixture: **R9** — a gated failure of either kind must leave `tournamentCredentials` byte-identical. Note this is precisely why the *store-local* discriminator (M2) is safe and the *wire* one is not: `"not_authorized"` is decided by this store's own read of its own map before any frame exists, so it carries no server-provenance claim at all, whereas `"rejected"` inherits B5's ambiguity in full.

**B6 — (from phase 1) `TournamentCreated` is correlated by tag only.** `createTournament` keys the credential by **the code in the reply**, never by a code the caller assumed. Fixture: **R10**.

**B7 — (from phase 1) an `Error` frame settles every in-flight RPC on the socket.** Same no-mutation-on-failure posture as B5, covered by R9. Its interaction with M2 is pinned by **R18**: an `Error` reply must settle as `reason:"rejected"`, never as `"not_authorized"`.

### Verification Matrix

| # | Claim | Changed seam | Test | Revert-failing assertion | Hostile fixture → first production branch | Paired positive reach-guard |
|---|---|---|---|---|---|---|
| R1 | Credentials survive rehydrate | `partialize`+`merge`+normalizer | persistence round-trip test | write 2 credentials → read persisted JSON → feed back through `merge` → both survive | Remove from `partialize` → key absent → red. Pre-phase-2 blob (no key) → `{}` default, not `undefined` | Other persisted keys (`playerId`) still present in same blob |
| R2 | Persisted credentials normalized, cap holds on hydrate | `normalizeTournamentCredentials` | malformed-blob test | mixed valid/invalid entries → only valid survive | Delete normalizer from `merge` → invalid entries leak → red | `AAA.organizerToken === "t"` — a normalizer returning `{}` unconditionally fails this |
| R3 | **Unified refcount, attach direction (S3)** | `acquireLobbySubscription` via `subscribeTournaments` | attach test | 0 lobby subs, 1st tournament sub → `SubscribeLobby` tally exactly 1 | 2nd tournament sub while 1st live → tally still 1. Revert: gate on `tournamentSubscribers.size===1` and re-send per subscriber → tally 2 → red | Deliver `TournamentListUpdate`, both subscribers' `onListUpdate` fired |
| R4 | **Unified refcount, detach direction (S3)** | `releaseLobbySubscription` | detach test, both orders | 1 lobby + 1 tournament sub; release lobby first → `UnsubscribeLobby` tally 0; release tournament → tally 1 | Symmetric order too. Revert: restore per-set gate in `subscribeLobby`'s unsubscribe → first release emits frame → red. Double-release same detach → still 1 | After non-emitting release, subscription still delivers |
| R5 | Tournament listener attached at acquisition, not first-tournament-subscriber | `attachSharedSubscription` | late-seed test (`seeds a late tournament subscriber from the cached list push`) | lobby subscriber acquires first, `TournamentListUpdate` push arrives, THEN tournament subscriber attaches → seeded from cache, not waiting on a new push | Revert: gate tournament listener attach on `tournamentSubscribers.size` → push lost → red | The late subscriber's `onListUpdate` fired with the exact cached array (identity + content), so a subscriber that attached but was never seeded fails |
| R6 | `tournamentListSnapshot` is verbatim, never merged/filtered | fan-out (`onTournamentRemoved`) | **(m2)** `seeds a late tournament subscriber with the pre-removal list after a TournamentRemoved` — the named test for this row's own claim. Credential-fan-out behavior keeps its two separate tests (`forgets credentials when the broker removes the tournament`, `leaves credentials untouched for a TournamentRemoved it holds nothing for`), which belong to F3/F6, not to the snapshot claim | Deliver `TournamentListUpdate` with `["AAA","BBB"]`; deliver `TournamentRemoved("BBB")` with **no** trailing list push; attach a *late* tournament subscriber → its seed still contains `BBB`, and is identity-equal (`toBe`) to the delivered array | Revert: fold the removal into the cached list inside `onTournamentRemoved` (`tournamentListSnapshot = tournamentListSnapshot.filter(...)`) → the late-seeded list is short by one, and identity-equality also breaks → red. Only a subsequent `TournamentListUpdate` may change the snapshot — assert that too by pushing a second list and re-seeding a third subscriber | **(F3)** In the same test assert the frame was genuinely delivered and processed: the *already-registered* subscriber's `onTournamentRemoved` fired with that exact code, **and** the credential held for that code was dropped. Without this the "unchanged" assertion passes vacuously for a frame that never reached the fan-out at all |
| R7 | Organizer token routed per-code | `runGatedTournamentRpc` | 2-tournament fixture | matching code's token on wire; missing-credential code → `{ok:false, reason:"not_authorized", role:"organizer"}`, zero send | Third code with no credential at all → first production branch is `token === undefined` in `runGatedTournamentRpc`, before `ensureSubscriptionSocket`. Revert-check #4 moves the check after socket acquisition → red | The *matching* code's action in the same test reaches the wire and the sent frame's token equals that code's stored `organizerToken` — so a runner that refused everything cannot pass |
| R8 | Player token routed per-code, organizer≠player | same | cross-role fixture | organizer-only credential fails `reportMatchResult` with `reason:"not_authorized", role:"player"`; adding `playerToken` succeeds | Same code, both roles exercised — proves the `switch` arm, not the map lookup. The `role` field must read `"player"` even though an `organizerToken` *is* held for that code, which is what distinguishes an arm-correct switch from a map-presence check | The post-add call reaches the wire with the `playerToken`, never the `organizerToken` |
| R9 | No state mutation on gated failure (B5/B7) | all 4 gated actions | no-mutation test | any gated `{ok:false}` → `tournamentCredentials` byte-identical (deep-equal against a `structuredClone` taken before the call) | True by construction — none of the four gated actions contains a `set()` call on the failure path | **(F3)** Two variants, each with its own guard. **(a) Local refusal** (no credential): R7's own zero-send assertion is the guard — it proves the failure was produced by the gate rather than by an unreached code path. **(b) Server rejection** (credential present, RPC reaches the wire, broker replies `Error`): additionally assert the request frame *did* go out on the socket, so the "no mutation" claim is about a real completed round-trip and not an early return |
| R10 | `TournamentCreated` filed under reply's code | `createTournament` | tag-only-correlation fixture | reply code differs from any code caller assumed → credential filed under reply's code | Caller-assumed code must hold nothing afterwards | The reply's code holds an entry whose `organizerToken` equals the reply's token |
| **R11** | **Credential writes merge rather than replace; eviction never claims the protected entry, and its tiebreak is `code`, not `Object.keys` order** | `rememberTournamentCredential` + `capTournamentCredentials` | suite A: `merges a later join into an existing organizer credential for the same code`; `evicts the least-recently-written credential and never the newest`; `orders eviction deterministically for all-digit tournament codes` | **Merge:** create-then-join on one code → the single entry carries BOTH `organizerToken` and `playerToken` (plus `playerKey`), neither overwriting the other; a replace-semantics implementation loses one and goes red. **Protect (M1-corrected fixture):** hold `"T02"`…`"T33"` (32 codes) all sharing one frozen `updatedAt`, then `rememberTournamentCredential(existing, "T01", …, FROZEN)`. Assert `result["T01"]` **present** and `!("T02" in result)`. Traced: with `protect`, victims are `T02…T33`, all tied on `updatedAt`, lexicographic min `"T02"` → evicted. Revert-check **#6** (drop `protect`) makes `"T01"` eligible; `"T01"` is the lexicographic minimum of all 33, so it evicts itself and `"T02"` survives — **both asserted halves flip**, which is what revision 2's fixture failed to do. **Tiebreak (M1-corrected fixture):** hold canonical-array-index codes `"9"`…`"40"` (32 codes) under a frozen clock, write and protect `"8"`. `Object.keys` enumerates canonical indices numerically (`"8","9","10",…,"40"`), so an implementation trusting key order evicts `"9"`; the `(updatedAt, code)` sort evicts the lexicographic min `"10"`. Assert `!("10" in result)` **and** `"9" in result` | **Frozen clock** drives the first production branch `codes.filter(code => code !== protect)`: with the `updatedAt` term a total tie, `protect` is the *only* thing standing between the just-written entry and eviction, and the fixture is now arranged so the newest code is also the lexicographic minimum — the single arrangement in which dropping `protect` changes the outcome. **All-digit codes** use *unpadded* canonical indices deliberately: `"0001"` is **not** a canonical array index (`ToString(ToUint32("0001")) === "1" ≠ "0001"`), so it enumerates in insertion order and cannot exhibit the numeric-ordering hazard the doc comment describes — revision 2's fixture was inert for that reason. Revert-check **#10** deletes the `.sort(...)` entirely | **Not a bare `Object.keys(result).length === 32`** — that passes for any 32-element result including a wrong one. Assert positively that `result[protectedCode]` is present **and** deep-equals what was just written, **and** that the specific expected victim (named literally in the test) is absent via `!(victimCode in result)`, **and** that a named *survivor* the buggy implementation would have taken is still present. Only then assert the size. Under merge, additionally assert both token fields on the merged entry are the exact strings written, so an implementation that merged into an empty object cannot pass |
| **R11b** | **(M1, new) `updatedAt` is the *primary* eviction key — the `code` term is only a tiebreak** | `capTournamentCredentials`'s comparator | suite A: `evicts by write time even when the tournament codes sort the other way` | Build 32 held entries `"T01"`…`"T32"` whose `updatedAt` runs **counter** to code order — `"TNN"` gets `BASE + (33 − NN)`, so `"T01"` is the *newest* (`BASE+32`) and `"T32"` the *oldest* (`BASE+1`). Then `rememberTournamentCredential(existing, "T99", …, BASE + 100)`. Assert `!("T32" in result)` **and** `result["T01"]` present. Traced: with the `updatedAt` term, victims sort oldest-first → `"T32"`. Revert-check **#8** (drop the `updatedAt` term; sort by code alone) makes `"T01"` the minimum → `"T01"` is evicted and `"T32"` survives, so **both asserted halves flip** | Distinct, non-frozen timestamps are the point: every other R11 case freezes the clock, so before this row the primary sort key was never exercised at all and a code-only comparator passed the whole suite. First production branch reached is the comparator's `map[a].updatedAt - map[b].updatedAt` term itself, evaluated on a non-zero difference. `protect` is deliberately *not* discriminating here (`"T99"` is both newest and lexicographically largest, so it survives either way) — that direction is R11's job, and keeping the two rows single-purpose is what makes each revert-check unambiguous | Assert `result["T99"]` present and deep-equal to what was written (the write actually landed), `result["T01"]` present (the newest non-protected entry was not taken), and only then `Object.keys(result).length === MAX_TOURNAMENT_CREDENTIALS` |
| R12 | Abort on reconnect, fresh controller after | `runTournamentRpc` + `"reconnecting"` | abort test | in-flight RPC settles `"aborted"` on reconnect | 2nd RPC started after transition uses fresh controller, unaffected, settles normally; `ws.close` never called | 2nd RPC settling `{ok:true}` proves abort was scoped |
| R13 | `closeSubscriptionSocket` full teardown | teardown | teardown test | both listeners removed, both sets cleared, both snapshots null, in-flight RPC aborted | Called twice → no throw, no double frame. `setServerAddress` drives same teardown (`:1033`) | Fresh `subscribeTournaments` after teardown sends `SubscribeLobby` again |
| R14 | Reconnect re-binds both listeners, re-sends `SubscribeLobby` | `"open"` branch | reconnect test | tournament-only subscriber (0 lobby subs) → `"reconnecting"` then `"open"` w/ new socket → `SubscribeLobby` tally 1 on new socket | Revert: `if (lobbySubscribers.size>0)` gate → tournament-only never re-bound → red | Lobby fan-out also works on new socket if a lobby subscriber exists |
| R15 | Late-resolving subscribe leaves nothing attached (interim for phase 5) | `subscribeTournaments` detach | cancelled-race test | `cancelled=true` set before await resolves → `detach?.()` → refcount 0, `UnsubscribeLobby` tally 1, no frame reaches handler | Double-detach → still 1, no throw. `ensureSubscriptionSocket` resolving null → detach a safe no-op | Handler reachable before detach (delivered frame arrives) |
| R16 | Existing lobby behavior unchanged | `subscribeLobby` | existing suite stays green + lobby-only cycle test | full existing suite green; lobby-only cycle emits exactly 1 `SubscribeLobby`+1 `UnsubscribeLobby` | 2 lobby subscribers, release 1 → no `UnsubscribeLobby` | `findLobbyGameByCode` still resolves from `lobbySnapshot` |
| R17 | Tree compiles, lints, protocol version unmoved | whole phase | `type-check`, `lint`, protocol script | all exit 0 | — | — |
| **R18** | **(M2, new) The local-refusal discriminator appears on the local path and NEVER on a wire path** | `runGatedTournamentRpc`'s refusal branch + `GatedTournamentRpcResult` | suite C: `classifies a local refusal as not_authorized and a server rejection as rejected` | **(a)** Gated action for a code holding no matching token → `result.ok === false`, `result.reason === "not_authorized"`, `result.role` equals the action's required role, and `tally(...) === 0` for every tag (nothing on the wire). **(b)** Same action, credential now held, broker replies `Error` → `result.reason === "rejected"` and `result.reason !== "not_authorized"`, with `result.message` equal to the broker's text verbatim. Revert-check **#9** (return `{reason:"rejected"}` from the refusal branch) makes (a) red while leaving (b) green — the two halves are independently falsifiable | Hostile fixture is (b) itself: a genuine server `Error` on a fully-credentialed call is the one path that could plausibly be mislabelled. **It is additionally unfalsifiable by construction, and that is worth stating:** `runGatedTournamentRpc`'s `send` parameter is typed `=> Promise<TournamentRpcResult<T>>` — the narrow four-member wire union — so no value flowing back from `runTournamentRpc`, `requestOver`, or any phase-1 helper can carry `reason:"not_authorized"` without a compile error. The test pins the runtime behavior; the type pins the impossibility. Run both (a) and (b) for one organizer-gated and one player-gated action, so the `role` field is exercised on both `switch` arms | Both halves are positive assertions on a settled result, not absences. (a)'s guard against a vacuous pass is `role` equality — a refusal branch that hardcoded one role passes a bare `reason` check and fails this. (b)'s guard is the request-frame assertion shared with R9(b): the frame went out, so the `"rejected"` classification describes a real round-trip |

**`DEFERRED(phase 5)` — component-level unmount-during-in-flight-connect.** Interim: **R15**.
**`DEFERRED(phase 5)` — organizer/player gating as rendered UI.** Decidable primitive landed (R7/R8/R18); nothing renders it.
**`DEFERRED(phase 5)` — `ToSubscribers`-only delivery on a real subscribed socket.** Fake socket proves frame accounting only.
**`DEFERRED(phase 3)` — i18n.** Two raw English literals authored; phase 3 keys them as `tournament:errors.notOrganizer` / `tournament:errors.notEntered`, phase 5 routes them, selecting between them on `result.role` (M2).
**Not tested, by design (F2):** the statement ordering inside `attachSharedSubscription` is not observable against a fake socket whose `send` never produces a reply. It is made structurally correct instead, and the reasoning is recorded in the function's own doc comment.

---

## Step 5 — Step-by-step implementation

### 5.0 — Environment and pre-flight (once)

```bash
cd C:/git/phase/.claude/worktrees/tournament-organizer-pr4-frontend/client
pnpm install --frozen-lockfile
```

1. Re-read `multiplayerStore.ts` immediately before the first edit. Every change uses `Edit` with a unique anchor; never `Write`.
2. Collision sweep: grep `client/src` for `TournamentCredential|TournamentRole|TournamentNotAuthorized|GatedTournamentRpcResult|MAX_TOURNAMENT_CREDENTIALS|rememberTournamentCredential|capTournamentCredentials|normalizeTournamentCredentials` and the seven action names as store members. Expect zero hits outside `tournamentClient.ts`'s `*Over` names.
3. `node scripts/check-protocol-version.mjs` → exit 0 baseline before any edit.

### 5.1 — U1a: credential type, constants, pure helpers

**Anchor:** insert immediately after `isRecord` (`:541-543`).

```ts
/**
 * Per-tournament bearer credentials this browser holds.
 *
 * The two token fields are independently optional on purpose, and this is NOT
 * a discriminated union waiting to be tidied into one: an organizer may also
 * join their own event, so one code can legitimately carry BOTH authorities at
 * once. This is the normal path, not an exotic one — `CreateTournament` does
 * not auto-join the creator, so an organizer who also wants to play issues a
 * separate `JoinTournament` on the same code. Each token is minted by the
 * broker in a point reply (`TournamentCreated.organizer_token`,
 * `TournamentJoined.player_token`) and is never broadcast — losing it is
 * unrecoverable, which is why this map is persisted rather than held in memory.
 */
export interface TournamentCredential {
  /** Organizer authority for this code. Present iff this browser created it. */
  organizerToken?: string;
  /** Entrant authority for this code. Present iff this browser joined it. */
  playerToken?: string;
  /**
   * The `player_key` this browser joined under — the identity every later
   * `TournamentView` keys on (`PlayerSummary.player_key`). Stored beside the
   * token rather than re-derived from `playerId` at read time so "which entrant
   * am I in THIS event" stays answerable even if the ambient id ever changes.
   */
  playerKey?: string;
  /** ms epoch of the last write. The eviction key; never rendered. */
  updatedAt: number;
}

/**
 * Cap on retained tournament credentials. Bounded because this map is
 * persisted and grows once per event the player touches, with no natural
 * shrink other than `TournamentRemoved` (which only fires while subscribed).
 */
export const MAX_TOURNAMENT_CREDENTIALS = 32;

/**
 * Trims the credential map to {@link MAX_TOURNAMENT_CREDENTIALS}, evicting
 * least-recently-written first.
 *
 * `protect` is never evicted — without it a write made under a frozen or
 * coarse clock (every entry sharing one `updatedAt`) could evict the very
 * entry that caused the overflow, whenever that entry also happens to sort
 * first by `code`.
 *
 * Ordering is `(updatedAt, code)`. `updatedAt` is the real key and carries the
 * LRU semantics; `code` is a pure tiebreak, present so that a clock tie cannot
 * hand the decision to `Object.keys`. Key order is not a safe fallback: JS
 * enumerates *canonical array-index* string keys ("9", "40" — strings that
 * round-trip through `ToString(ToUint32(k))`) in ascending numeric order ahead
 * of every other key's insertion order, so an all-digit tournament code would
 * otherwise make eviction depend on how the code happens to spell a number.
 * Note this hazard applies only to unpadded codes: "0001" does not round-trip
 * and is therefore insertion-ordered like any other string.
 */
function capTournamentCredentials(
  map: Record<string, TournamentCredential>,
  protect?: string,
): Record<string, TournamentCredential> {
  const codes = Object.keys(map);
  const overflow = codes.length - MAX_TOURNAMENT_CREDENTIALS;
  if (overflow <= 0) return map;

  const victims = codes
    .filter((code) => code !== protect)
    .sort(
      (a, b) =>
        map[a].updatedAt - map[b].updatedAt || (a < b ? -1 : a > b ? 1 : 0),
    )
    .slice(0, overflow);

  const next = { ...map };
  for (const victim of victims) delete next[victim];
  return next;
}

/**
 * Returns a new credential map with `patch` merged into `code`'s entry.
 *
 * Merging, not replacing: create-then-join on the same code accumulates both
 * authorities (see {@link TournamentCredential}). `now` is injectable so the
 * eviction tests are deterministic.
 */
export function rememberTournamentCredential(
  existing: Readonly<Record<string, TournamentCredential>>,
  code: string,
  patch: Omit<Partial<TournamentCredential>, "updatedAt">,
  now: number = Date.now(),
): Record<string, TournamentCredential> {
  const merged: Record<string, TournamentCredential> = {
    ...existing,
    [code]: { ...existing[code], ...patch, updatedAt: now },
  };
  return capTournamentCredentials(merged, code);
}

/**
 * Rehydration guard. Persisted state is external input (see this store's
 * `merge`), so a blob may be hand-edited, truncated, or written by a build
 * whose shape or cap differed. Entries carrying no authority at all are
 * dropped: a credential with neither token is not a credential.
 *
 * Accepted edge case, stated rather than guarded: an array also satisfies the
 * object check `isRecord` performs, so `normalizeTournamentCredentials([...])`
 * clears the top-level guard and enumerates numeric indices as if they were
 * tournament codes. Each such "entry" would still have to be an object
 * carrying a string `organizerToken` or `playerToken` to survive the per-entry
 * validation below, so the result is a narrow, harmless edge case rather than
 * a functional gap.
 *
 * `isRecord` is deliberately NOT narrowed to fix this. It is file-local and in
 * this phase's scope, but it has five other callers — `normalizeRememberedHostConfig`
 * (:591), the `formatConfig` / `deck_size` projection (:659, :662), the
 * `loopDetection` guard (:709) and the seat validation (:719) — whose current
 * behavior, array-acceptance included, is load-bearing for the remembered-host-config
 * and migration paths. Tightening a shared predicate for one new caller's
 * benefit is an unscoped behavior change to five unrelated call sites, which is
 * not something this phase should do as a side effect of adding a sixth.
 */
export function normalizeTournamentCredentials(
  persisted: unknown,
): Record<string, TournamentCredential> {
  if (!isRecord(persisted)) return {};
  const out: Record<string, TournamentCredential> = {};
  for (const [code, raw] of Object.entries(persisted)) {
    if (!isRecord(raw)) continue;
    const organizerToken =
      typeof raw.organizerToken === "string" ? raw.organizerToken : undefined;
    const playerToken =
      typeof raw.playerToken === "string" ? raw.playerToken : undefined;
    const playerKey =
      typeof raw.playerKey === "string" ? raw.playerKey : undefined;
    if (organizerToken === undefined && playerToken === undefined) continue;
    out[code] = {
      ...(organizerToken !== undefined ? { organizerToken } : {}),
      ...(playerToken !== undefined ? { playerToken } : {}),
      ...(playerKey !== undefined ? { playerKey } : {}),
      updatedAt:
        typeof raw.updatedAt === "number" && Number.isFinite(raw.updatedAt)
          ? raw.updatedAt
          : 0,
    };
  }
  return capTournamentCredentials(out);
}
```

Conditional spreads are used instead of `{ organizerToken }` with a possibly-`undefined` value so the file stays correct if `exactOptionalPropertyTypes` is ever enabled.

### 5.2 — U1b: state field, default, persistence partition, hydrate normalizer

Four surgical edits.

**(a) `MultiplayerState`** — anchor on the `lastHostConfig` declaration (`:281-283`), insert after:

```ts
  /**
   * Tournament code → bearer credentials this browser holds. Persisted:
   * `organizer_token` and `player_token` are minted once in a point reply and
   * never re-sent, so losing them is unrecoverable. A plain object, not a
   * `Map` — `partialize` runs through JSON, where a `Map` serializes to `{}`.
   * Bounded by {@link MAX_TOURNAMENT_CREDENTIALS}; entries are dropped on
   * `TournamentRemoved`.
   */
  tournamentCredentials: Record<string, TournamentCredential>;
```

**(b) initial state** — anchor `lastHostConfig: null,` (`:1004`), insert after:

```ts
      tournamentCredentials: {},
```

**(c) `partialize`** (`:1790-1795`) — add one line:

```ts
        tournamentCredentials: state.tournamentCredentials,
```

**(d) `merge`** (`:1780-1789`) — add the normalizer beside the existing one:

```ts
        return {
          ...current,
          ...saved,
          lastHostConfig: normalizeRememberedHostConfig(saved.lastHostConfig),
          tournamentCredentials: normalizeTournamentCredentials(
            saved.tournamentCredentials,
          ),
        };
```

**Do not bump `version` and do not touch `migratePersistedMultiplayerState`.** Measured §0.1: `migrate` has no whitelist and `merge` spreads `current` first, so a pre-phase-2 blob hydrates with the `{}` default.

### 5.3 — U2a: module-level tournament subscription state and the ONE refcount

**Anchor:** immediately after `lobbyAttachDetach` (`:162-164`).

First, widen two existing doc comments (prose only, zero behavior change):

- `pendingJoinRpcAborts` (`:135-141`): name the tournament RPCs too.
- `lobbySubscribers` (`:144-152`): append — *"The reference count that governs the shared `SubscribeLobby` frame spans this set **and** `tournamentSubscribers`; see {@link lobbySubscriptionRefCount}."*

Then insert:

```ts
/**
 * Registered tournament-broadcast subscribers. Handlers rather than one
 * callback because the three broadcast streams (`TournamentListUpdate`,
 * `TournamentUpdate`, `TournamentRemoved`) are independent and a caller
 * usually renders only one of them.
 *
 * This set is the SECOND half of the shared-subscription reference count —
 * see {@link lobbySubscriptionRefCount}.
 */
const tournamentSubscribers: Set<TournamentSubscriptionHandlers> = new Set();

/**
 * Most recent `TournamentListUpdate`, used to seed subscribers that attach
 * after the push has already arrived.
 *
 * A verbatim cache, never a reduction: the broker sends the whole sorted list
 * every time (`tournament_summaries()`) and there are no add/update/remove
 * delta frames, so folding anything in here would be inventing a delta
 * protocol the server does not speak. In particular `onTournamentRemoved` must
 * NOT filter this array — a removed tournament stays in the cached list until
 * the server's next `TournamentListUpdate` replaces it wholesale. Cleared
 * whenever the shared subscription is released, so a reconnect can never serve
 * a stale list.
 */
let tournamentListSnapshot: TournamentSummary[] | null = null;

/** Per-socket detach returned by `subscribeTournamentsOver`. Re-bound on
 *  reconnect; `null` when no socket is attached. Sends nothing by design —
 *  the frames belong to {@link detachSharedSubscription}. */
let tournamentAttachDetach: (() => void) | null = null;

/**
 * The single reference count governing the shared `SubscribeLobby` /
 * `UnsubscribeLobby` pair.
 *
 * Broker-side those frames are per-CONNECTION, not per-subscriber:
 * `SubscribeLobby` inserts this connection's sender into one delivery set
 * (`AddSubscriber`) and `UnsubscribeLobby` removes it (`RemoveSubscriber`),
 * so a single removal silences every stream riding this socket regardless of
 * how many subscribes preceded it. Lobby and tournament subscribers therefore
 * cannot each keep their own count — the last subscriber of EITHER kind is the
 * one that may release.
 *
 * Derived from set membership rather than an incremented integer on purpose:
 * `add`/`delete` are idempotent, so a double-subscribe cannot inflate the
 * count and a double-release cannot drive it negative and strand the
 * subscription. Callers (including React cleanups that may run twice) need no
 * discipline for that to hold.
 */
function lobbySubscriptionRefCount(): number {
  return lobbySubscribers.size + tournamentSubscribers.size;
}

/**
 * Binds both listeners to `socket` and puts `SubscribeLobby` on the wire.
 *
 * The frame is emitted as a side effect of `subscribeLobbyOver`, which owns
 * both frames (`services/brokerClient.ts`). Attaching the TOURNAMENT listener
 * here — rather than when the first tournament subscriber appears — is
 * load-bearing, not tidiness: `SubscribeLobby` triggers exactly one
 * `ToSelf(TournamentListUpdate)`, there is no request that re-fetches the
 * list, and the next list push only happens when some other actor mutates a
 * tournament. A store that attached the tournament listener later would
 * silently drop that one push whenever a lobby subscriber acquired the
 * subscription first, and the tournament page would render an empty list
 * indefinitely.
 *
 * For the same reason the two statements below are in this order and must
 * stay in it: the tournament listener is registered BEFORE the statement that
 * provokes the reply it needs to catch, because `subscribeLobbyOver`'s own
 * `ws.send` is what puts `SubscribeLobby` on the wire. Binding it afterwards
 * would happen to work only by relying on an unwritten, untested fact — that
 * a `send` cannot deliver its reply within the same synchronous execution
 * block — which a future refactor (an async `subscribeTournamentsOver`, a
 * transport that dispatches on a microtask) could quietly invalidate. This
 * ordering makes the invariant structural instead.
 */
function attachSharedSubscription(
  socket: PhaseSocket,
  set: MultiplayerSet,
  get: MultiplayerGet,
): void {
  tournamentAttachDetach = subscribeTournamentsOver(socket, {
    onListUpdate: (tournaments) => {
      tournamentListSnapshot = tournaments;
      for (const h of tournamentSubscribers) h.onListUpdate?.(tournaments);
    },
    onTournamentUpdate: (code, view) => {
      for (const h of tournamentSubscribers) h.onTournamentUpdate?.(code, view);
    },
    onTournamentRemoved: (code) => {
      // The tournament is gone server-side; its tokens can never authorize
      // anything again. Dropped here because this fan-out is the one place
      // every `TournamentRemoved` arrives, and it stays attached for the whole
      // life of the shared subscription — so the cleanup happens even when no
      // page is currently subscribed. That lifetime is also why the helper
      // must not write when it holds nothing for `code`.
      //
      // Deliberately does NOT touch `tournamentListSnapshot`: that cache is a
      // verbatim copy of the server's last list push, and filtering it here
      // would invent a delta protocol the broker does not speak.
      forgetTournamentCredential(set, get, code);
      for (const h of tournamentSubscribers) h.onTournamentRemoved?.(code);
    },
  });
  lobbyAttachDetach = subscribeLobbyOver(socket, (games) => {
    lobbySnapshot = games;
    for (const cb of lobbySubscribers) cb(games);
  });
}

/** Releases the shared subscription: detaches both listeners, sends
 *  `UnsubscribeLobby` (via `subscribeLobbyOver`'s detach, which no-ops on a
 *  socket that is no longer OPEN), and drops both cached snapshots. */
function detachSharedSubscription(): void {
  tournamentAttachDetach?.();
  tournamentAttachDetach = null;
  lobbyAttachDetach?.();
  lobbyAttachDetach = null;
  lobbySnapshot = null;
  tournamentListSnapshot = null;
}

/**
 * Acquires the shared subscription if it is not already bound to a socket.
 * Call AFTER adding the new subscriber to its set.
 *
 * The predicate is "is it attached?", not "is the count exactly 1": across a
 * reconnect the count is legitimately > 0 while the handle is null, and
 * `onStateChange`'s "open" branch re-acquires through this same function.
 */
function acquireLobbySubscription(
  socket: PhaseSocket,
  set: MultiplayerSet,
  get: MultiplayerGet,
): void {
  if (lobbyAttachDetach !== null) return;
  attachSharedSubscription(socket, set, get);
}

/**
 * Releases the shared subscription once no subscriber of EITHER kind remains.
 * Call AFTER removing the departing subscriber from its set.
 */
function releaseLobbySubscription(): void {
  if (lobbySubscriptionRefCount() > 0) return;
  detachSharedSubscription();
}

/**
 * Drops a tournament's credentials, and genuinely no-ops when nothing is held
 * for `code` — no `set` call, therefore no `persist` write.
 *
 * The presence test reads through `get` rather than being made inside the
 * updater. Returning `{}` from a zustand updater does leave the state
 * reference unchanged (so credential consumers do not re-render), but the
 * `set` still runs and `persist` still serializes the whole partition to
 * `localStorage`. This fan-out is attached for the entire life of the shared
 * subscription and fires for every `TournamentRemoved` on the server —
 * including the overwhelming majority this browser holds no credential for —
 * so the miss path has to be free.
 */
function forgetTournamentCredential(
  set: MultiplayerSet,
  get: MultiplayerGet,
  code: string,
): void {
  if (!(code in get().tournamentCredentials)) return;
  set((state) => {
    const next = { ...state.tournamentCredentials };
    delete next[code];
    return { tournamentCredentials: next };
  });
}
```

**Ordering note for the executor:** `MultiplayerSet`/`MultiplayerGet` are declared at `:797-802`, below this insertion point. Type aliases hoist for type positions, and `forgetTournamentCredential` is a function declaration (hoists too), so this compiles. If `tsc` objects for any reason, move this whole block to just after `MultiplayerSet`/`MultiplayerGet` (`:797-802`) rather than restructuring it. The same hoisting argument covers `TournamentRole` / `TournamentNotAuthorized` / `GatedTournamentRpcResult` (§5.5), which are referenced from `MultiplayerActions` at `:402` but declared later in the file — all three are type-only declarations used only in type positions.

**Imports to add** at the top of the file:

```ts
// extend the existing "../adapter/types" type-only import list:
  TournamentSummary,
  TournamentView,
  PairingId,
  PodOutcome,
  MatchArity,
  ScoringPolicy,
  BracketShape,
  TournamentCreatedReply,
  TournamentJoinedReply,
  TournamentUpdateReply,

// new value + type import block, placed after the brokerClient import (:37):
import {
  createTournamentOver,
  dropFromTournamentOver,
  endTournamentOver,
  getTournamentOver,
  joinTournamentOver,
  reportMatchResultOver,
  startTournamentRoundOver,
  subscribeTournamentsOver,
  type CreateTournamentRequest,
  type TournamentRpcResult,
  type TournamentSubscriptionHandlers,
} from "../services/tournamentClient";
```

`verbatimModuleSyntax: true` makes the inline `type` modifiers mandatory. Only import what is referenced — `noUnusedLocals` is on; drop `TournamentView`/`MatchArity`/`ScoringPolicy`/`BracketShape` if they end up unreferenced after 5.5.

### 5.4 — U2b: rewrite the two subscribe actions and the teardown/reconnect paths

**(a) `subscribeLobby` (`:1719-1747`)** — replace only the two gate expressions:

```ts
      subscribeLobby: async (onUpdate) => {
        const socket = await get().ensureSubscriptionSocket();
        if (!socket) return null;
        lobbySubscribers.add(onUpdate);
        // Acquire against the count that spans BOTH subscriber kinds: a
        // tournament subscriber may already hold the subscription, in which
        // case this must not re-send `SubscribeLobby`.
        acquireLobbySubscription(socket, set, get);
        if (lobbySnapshot) {
          // Immediate seed so a late subscriber renders without waiting for
          // the next server push.
          onUpdate(lobbySnapshot);
        }
        return () => {
          lobbySubscribers.delete(onUpdate);
          // Only the last subscriber of EITHER kind may release — see
          // `lobbySubscriptionRefCount`.
          releaseLobbySubscription();
        };
      },
```

Two behavioral notes the executor must not "simplify away":

- The seed changes from `else if (lobbySnapshot)` to an unconditional `if (lobbySnapshot)`. Under the unified count the very first *lobby* subscriber may arrive while a snapshot already exists (a tournament subscriber acquired first and the `LobbyUpdate` push has landed). The old `else` branch would starve it. When no snapshot exists — genuine cold start — the guard is false and behavior is identical to today.
- `wasEmpty` disappears; the acquire predicate is now `lobbyAttachDetach === null`, computed inside `acquireLobbySubscription`.

**(b) new `subscribeTournaments` action** — insert immediately after `subscribeLobby`:

```ts
      subscribeTournaments: async (handlers) => {
        const socket = await get().ensureSubscriptionSocket();
        if (!socket) return null;
        tournamentSubscribers.add(handlers);
        // First subscriber of EITHER kind puts `SubscribeLobby` on the wire.
        // That frame is not optional for tournaments: `AddSubscriber` is the
        // only path into the broker's delivery set, and its
        // `ToSelf(TournamentListUpdate)` is the only way this client ever
        // learns the list without waiting on someone else's mutation.
        acquireLobbySubscription(socket, set, get);
        if (tournamentListSnapshot) {
          handlers.onListUpdate?.(tournamentListSnapshot);
        }
        return () => {
          tournamentSubscribers.delete(handlers);
          releaseLobbySubscription();
        };
      },
```

**(c) `onStateChange` "open" branch (`:1596-1612`)**:

```ts
                if (state === "open") {
                  const socket = subscriptionReconnect?.current() ?? null;
                  if (socket) {
                    set({ serverInfo: socket.serverInfo });
                    // Re-attach the shared subscription if anyone still wants
                    // it — a tournament subscriber alone is reason enough, and
                    // gating this on `lobbySubscribers` would leave a
                    // tournament-only page silently dead after a reconnect.
                    // The first snapshot from the server overwrites the caches;
                    // stale data is not authoritative across a reconnect.
                    if (lobbySubscriptionRefCount() > 0) {
                      acquireLobbySubscription(socket, set, get);
                    }
                  }
                  settle(socket);
                }
```

`set` and `get` are the store creator's own closure parameters and both already reach this closure — `set({ serverInfo: socket.serverInfo })` sits inside **this very `"open"` branch at `:1599`**, and (for `get` specifically) `get().showToast(err.message)` at `:1584` is the same closure's sibling error path. No signature or structural change is needed to thread either (F6).

**(d) `onStateChange` "reconnecting" branch (`:1613-1622`)**:

```ts
                } else if (state === "reconnecting") {
                  for (const ac of pendingJoinRpcAborts) ac.abort();
                  pendingJoinRpcAborts.clear();
                  // Drop the handles to the old socket's listeners; they are
                  // re-bound on the next "open". Not invoked: the old socket is
                  // gone, and `subscribeLobbyOver`'s detach is `readyState`-
                  // guarded, so calling it could only remove listeners from a
                  // socket that is being discarded anyway.
                  lobbyAttachDetach = null;
                  tournamentAttachDetach = null;
                  // Both caches are per-socket-generation; a reconnect must not
                  // seed a new subscriber from a pre-drop snapshot.
                  lobbySnapshot = null;
                  tournamentListSnapshot = null;
                }
```

Clearing `lobbySnapshot` here is a deliberate, named tightening of existing behavior: the current code leaves it set across a reconnect while its own comment at `:1602-1604` says "stale cached data is not authoritative across a reconnect." Under the unified design the snapshot is now also a *seed source* for newly-attaching subscribers, so leaving it would hand a fresh subscriber a pre-drop list. **Call this out in the commit body as an intentional consistency fix, not a drive-by.**

**(e) `closeSubscriptionSocket` (`:1641-1650`)**:

```ts
      closeSubscriptionSocket: () => {
        for (const ac of pendingJoinRpcAborts) ac.abort();
        pendingJoinRpcAborts.clear();
        // Unconditional teardown of the shared subscription, both kinds.
        detachSharedSubscription();
        lobbySubscribers.clear();
        tournamentSubscribers.clear();
        subscriptionReconnect?.close();
        subscriptionReconnect = null;
      },
```

`detachSharedSubscription()` already nulls both handles and both snapshots — do not leave a duplicate `lobbySnapshot = null` line. This path is also reached from `setServerAddress` (the `closeSubscriptionSocket()` call at **`:1033`**, guarded by the `if` at `:1032`), covered by R13's second hostile fixture.

### 5.5 — U3: the role/result types, the two runners, and the seven actions

**M2 decision record — Option A chosen, Option B rejected.**

The reviewer offered two ways to make the two i18n keys decidable by phase 5. This plan takes **Option A: widen the store action's return type with a typed local-refusal discriminator.** The justification, against this codebase's own patterns:

- **It is the only option that keeps a single authority.** `runGatedTournamentRpc` is already this store's single authority for "does this browser hold the required token for this code" — the Logic Placement table says so, and the plan's own doc comment tells call sites never to read `tournamentCredentials` themselves. Option B asks phase 5 to do exactly that, re-deriving an answer the gate already computed. That is the "inspecting the cost structure at a call site" anti-pattern CLAUDE.md names, and the frontend re-interpreting store data is the display-layer rule broken in the same move.
- **Option B is racy where Option A is not.** `forgetTournamentCredential` deletes entries asynchronously from the `TournamentRemoved` fan-out, so the map phase 5 re-reads is not guaranteed to be the map the gate read. Two authorities that can disagree about one result is a defect generator, not a design.
- **Option B does not actually close the hole.** Even with a proactive credential check, a real server rejection on a fully-credentialed call still arrives as `{reason:"rejected"}` with no way to tell it from anything else; the ambiguity is made rarer, not decidable. Option A makes the two cases structurally distinct.
- **Option A also repairs a contract violation that exists independently of phase 5.** Phase 1 documents `rejected` as *"the broker answered `Error`; `message` is its text verbatim"* (`tournamentClient.ts:100`). Filing a local refusal — no broker contacted, client-authored message — under that member is wrong on its own terms, before any consumer looks at it.
- **It stays inside phase 2's scope.** The widening is a store-local union in `multiplayerStore.ts`. `TournamentRpcFailureReason` is untouched and `tournamentClient.ts` is not opened, so phase 1's frozen file and its four-member wire union are preserved exactly.

The cost is one departure from the charter's literal `reason:"rejected"` wording, adjudicated in full under Extension vs Creation (departure 2). The charter's substantive requirements — refuse locally, before socket acquisition, with zero wire traffic and no state mutation — are unchanged.

**Types and runners** — insert after `forgetTournamentCredential`:

```ts
/**
 * Which authority a gated tournament RPC requires. A closed union naming the
 * domain concept, not the storage field: adding a third authority later is a
 * new member plus one compile error at the switch below, not a third runner.
 */
export type TournamentRole = "organizer" | "player";

/**
 * A gated action refused by THIS STORE, before any frame existed.
 *
 * Deliberately not `reason: "rejected"`. `TournamentRpcFailureReason` is the
 * WIRE vocabulary — each of its four members documents something the transport
 * or the broker did, and `"rejected"` specifically means "the broker answered
 * `Error`; `message` is its text verbatim" (`services/tournamentClient.ts`).
 * A local refusal contacted no broker and carries client-authored copy, so
 * filing it under `"rejected"` would both falsify that contract and leave a
 * consumer no way to tell the two apart except by matching English message
 * text. `role` is carried so a consumer can pick its copy (and later, its
 * i18n key) from a typed field rather than from the message.
 *
 * It lives here rather than as a fifth `TournamentRpcFailureReason` member
 * because `tournamentClient.ts` is the wire layer and this is a store-level
 * fact — and because that file is frozen by the time this store is written.
 */
export interface TournamentNotAuthorized {
  ok: false;
  reason: "not_authorized";
  /** The authority that was required and not held. */
  role: TournamentRole;
  /** Human-readable fallback. Phase 3/5 replace this with a `t()` lookup keyed
   *  off {@link TournamentNotAuthorized.role}; see the i18n boundary note. */
  message: string;
}

/**
 * What a token-gated tournament action resolves to: phase 1's wire result,
 * widened by exactly one locally-produced failure member. Every failure member
 * keeps the same `{ ok: false; reason; message }` skeleton, so `if (!r.ok)`
 * narrowing works uniformly and `r.reason === "not_authorized"` narrows
 * further to the member carrying `role`.
 */
export type GatedTournamentRpcResult<T> =
  | TournamentRpcResult<T>
  | TournamentNotAuthorized;

/**
 * Single authority for giving a tournament RPC its socket and its abort
 * registration. Follows `resolveGuest` exactly: acquire lazily, register an
 * `AbortController` so a `reconnecting` transition or a teardown cuts the wait
 * short, and remove it in `finally`. It never closes a socket — the socket
 * belongs to `ensureSubscriptionSocket` / `closeSubscriptionSocket`.
 */
async function runTournamentRpc<T>(
  get: MultiplayerGet,
  send: (socket: PhaseSocket, signal: AbortSignal) => Promise<TournamentRpcResult<T>>,
): Promise<TournamentRpcResult<T>> {
  const socket = await get().ensureSubscriptionSocket();
  if (!socket) {
    return {
      ok: false,
      reason: "connection_lost",
      message: "Lobby connection unavailable. Check your server address.",
    };
  }
  const ac = new AbortController();
  pendingJoinRpcAborts.add(ac);
  try {
    return await send(socket, ac.signal);
  } finally {
    pendingJoinRpcAborts.delete(ac);
  }
}

/**
 * Single authority for token-gated tournament RPCs. Resolves the required
 * authority for `code` and refuses locally when it is absent — before any
 * socket is opened, so a call with no credential costs nothing and puts
 * nothing on the wire.
 *
 * Call sites never read `tournamentCredentials` themselves: a caller that
 * inspects which token an action needs is one refactor away from sending the
 * wrong tournament's token, and a caller that re-reads the map to explain a
 * failure has become a second authority that can disagree with this one (the
 * fan-out deletes entries asynchronously).
 *
 * Two distinguishable failure shapes, deliberately:
 *  - `{reason: "not_authorized", role}` — decided HERE, from this store's own
 *    map, with certainty. Nothing was sent.
 *  - any `TournamentRpcFailureReason` — decided by the transport or the
 *    broker. Note in particular that `"rejected"` inherits the phase-1 caution
 *    below and is NOT a reliable "the server refused me" signal.
 *
 * Caution for consumers (`services/tournamentClient.ts`, module header part 4):
 * the four gated RPCs settle on a `TournamentUpdate` BROADCAST, which carries
 * no request-vs-broadcast discriminator, so a wire-level `{ok:false}` here is
 * not a reliable "the server rejected me" signal. Nothing in this store mutates
 * state on a gated failure for exactly that reason.
 */
async function runGatedTournamentRpc<T>(
  get: MultiplayerGet,
  code: string,
  role: TournamentRole,
  send: (
    socket: PhaseSocket,
    token: string,
    signal: AbortSignal,
  ) => Promise<TournamentRpcResult<T>>,
): Promise<GatedTournamentRpcResult<T>> {
  const held = get().tournamentCredentials[code];
  let token: string | undefined;
  switch (role) {
    case "organizer":
      token = held?.organizerToken;
      break;
    case "player":
      token = held?.playerToken;
      break;
  }
  if (token === undefined) {
    return {
      ok: false,
      reason: "not_authorized",
      role,
      message:
        role === "organizer"
          ? "You are not the organizer of this tournament."
          : "You are not entered in this tournament.",
    };
  }
  const heldToken = token;
  return runTournamentRpc(get, (socket, signal) =>
    send(socket, heldToken, signal),
  );
}
```

**The discriminator cannot leak onto a wire path, by type (R18).** `send` is typed `=> Promise<TournamentRpcResult<T>>` — the narrow four-member union — and `runTournamentRpc`'s return type is the same. So every value that reaches the caller through the wire branch is a `TournamentRpcResult<T>`, and `"not_authorized"` is producible only by the literal above. A server `Error` reply cannot be mislabelled without a compile error. R18 pins the runtime behavior on top of that.

**Compose without a cast** — `runTournamentRpc`'s `send` takes `(socket, signal)`; the gated wrapper's `send` takes `(socket, token, signal)`. The composition above (`(socket, signal) => send(socket, heldToken, signal)`) is the corrected, final form — no `as never`, no cast anywhere in this file. `runTournamentRpc`'s `Promise<TournamentRpcResult<T>>` is assignable to the declared `Promise<GatedTournamentRpcResult<T>>` by union widening, so the `return` needs no annotation either. Each action's own closure builds the `{ signal }` options object it passes to the phase-1 helper.

**The seven actions** — insert after `subscribeTournaments`:

```ts
      createTournament: async (req) =>
        runTournamentRpc(get, async (socket, signal) => {
          const result = await createTournamentOver(socket, req, { signal });
          if (result.ok) {
            // Keyed by the code in the REPLY: `CreateTournament` carries no
            // client-chosen code (the broker mints it), so the reply is the
            // only authority for which tournament this token opens.
            set((state) => ({
              tournamentCredentials: rememberTournamentCredential(
                state.tournamentCredentials,
                result.value.code,
                { organizerToken: result.value.organizer_token },
              ),
            }));
          }
          return result;
        }),

      joinTournament: async (code, displayName) =>
        runTournamentRpc(get, async (socket, signal) => {
          // Captured BEFORE the await so the credential records the key that
          // was actually sent, not whatever `playerId` reads as afterwards.
          const playerKey = get().playerId;
          const result = await joinTournamentOver(
            socket,
            code,
            playerKey,
            displayName || get().displayName || "Player",
            { signal },
          );
          if (result.ok) {
            set((state) => ({
              tournamentCredentials: rememberTournamentCredential(
                state.tournamentCredentials,
                result.value.code,
                { playerToken: result.value.player_token, playerKey },
              ),
            }));
          }
          return result;
        }),

      getTournament: async (code) =>
        runTournamentRpc(get, (socket, signal) =>
          getTournamentOver(socket, code, { signal }),
        ),

      startTournamentRound: async (code) =>
        runGatedTournamentRpc(get, code, "organizer", (socket, token, signal) =>
          startTournamentRoundOver(socket, code, token, { signal }),
        ),

      endTournament: async (code) =>
        runGatedTournamentRpc(get, code, "organizer", (socket, token, signal) =>
          endTournamentOver(socket, code, token, { signal }),
        ),

      reportMatchResult: async (code, pairingId, outcome) =>
        runGatedTournamentRpc(get, code, "player", (socket, token, signal) =>
          reportMatchResultOver(socket, code, pairingId, token, outcome, {
            signal,
          }),
        ),

      dropFromTournament: async (code) =>
        runGatedTournamentRpc(get, code, "player", (socket, token, signal) =>
          dropFromTournamentOver(socket, code, token, { signal }),
        ),
```

`displayName || get().displayName || "Player"` uses `||`, not `??` — `displayName` defaults to `""` (`:997`), which `??` would pass through unchanged. Matches `resolveGuest`'s same fallback (`:1669-1673`; the broker rejects a blank display name).

**`MultiplayerActions` interface additions** — insert after `subscribeLobby`'s declaration (`:402-411`):

```ts
  /**
   * Subscribe to tournament broadcasts over the shared subscription socket.
   * Returns a detach function, or `null` when the socket could not be opened.
   *
   * Shares ONE `SubscribeLobby` reference count with {@link subscribeLobby}:
   * the first subscriber of either kind sends the frame and only the last one
   * of either kind sends `UnsubscribeLobby`. Callers should not await the
   * result before their cleanup can run — follow `LobbyView.tsx`'s
   * `if (cancelled) { detach?.(); return; }` idiom.
   */
  subscribeTournaments: (
    handlers: TournamentSubscriptionHandlers,
  ) => Promise<(() => void) | null>;
  /** Create a tournament and remember its organizer token. */
  createTournament: (
    req: CreateTournamentRequest,
  ) => Promise<TournamentRpcResult<TournamentCreatedReply>>;
  /** Join a tournament and remember its player token and player key. */
  joinTournament: (
    code: string,
    displayName?: string,
  ) => Promise<TournamentRpcResult<TournamentJoinedReply>>;
  /** Fetch one tournament's current view. Ungated — codes are public. */
  getTournament: (
    code: string,
  ) => Promise<TournamentRpcResult<TournamentUpdateReply>>;
  /**
   * Organizer-gated. When no organizer token is held for `code` this resolves
   * `{ok:false, reason:"not_authorized", role:"organizer"}` locally, with no
   * wire traffic — a shape distinct from every
   * {@link TournamentRpcFailureReason}, so a consumer can pick "you are not the
   * organizer" copy without inspecting `message`.
   */
  startTournamentRound: (
    code: string,
  ) => Promise<GatedTournamentRpcResult<TournamentUpdateReply>>;
  /** Organizer-gated, same local-refusal contract. */
  endTournament: (
    code: string,
  ) => Promise<GatedTournamentRpcResult<TournamentUpdateReply>>;
  /** Player-gated; local refusal carries `role: "player"`. */
  reportMatchResult: (
    code: string,
    pairingId: PairingId,
    outcome: PodOutcome,
  ) => Promise<GatedTournamentRpcResult<TournamentUpdateReply>>;
  /** Player-gated, same local-refusal contract. */
  dropFromTournament: (
    code: string,
  ) => Promise<GatedTournamentRpcResult<TournamentUpdateReply>>;
```

**i18n boundary, stated so phase 3/5 can find it (F4 + M2):** the two local-refusal messages above are raw English literals. Phase 2 adds no `t()` and no catalog key (charter deferral: all i18n → phase 3). The keys they should become are **`tournament:errors.notOrganizer`** ("You are not the organizer of this tournament.") and **`tournament:errors.notEntered`** ("You are not entered in this tournament.").

**How phase 5 selects between them — decidable, no string matching (M2).** The result is a discriminated union, so:

```ts
if (!result.ok) {
  if (result.reason === "not_authorized") {
    // `result.role` is `TournamentRole`; the key is chosen from a typed field.
    show(t(result.role === "organizer" ? "errors.notOrganizer" : "errors.notEntered"));
  } else {
    show(t("errors.serverRejected", { message: result.message }));
  }
}
```

That branch was **not** decidable before this revision: a local refusal and a broker `Error` both arrived as `{reason:"rejected"}`, so the only available discriminator was the English `message` text. Phase 3 authors both keys in all 7 catalogs; phase 5 routes them alongside `t("errors.serverRejected", { message })`. **They must not be funnelled through `errors.serverRejected`** — that key exists to wrap an *untranslatable server* message and interpolates `{{message}}` verbatim; passing client-authored English into it would leave the copy permanently untranslated in all six non-English locales. Neither key is count-bearing or placeholder-bearing, so S4's placeholder-parity and four-form obligations do not apply to them.

### 5.6 — U4: verify the abort/reconnect wiring is complete

No further edits — the wiring is finished by 5.4(c)(d)(e) and 5.5's use of `pendingJoinRpcAborts`. Confirm by inspection:

1. Every one of the seven actions reaches the wire only through `runTournamentRpc`.
2. `"reconnecting"` and `"offline"` and `closeSubscriptionSocket` all already drain `pendingJoinRpcAborts` — no new drain sites.
3. `runTournamentRpc`'s `finally` removes the controller on every path and never calls `.close()`.
4. The `"open"` branch re-acquires the shared subscription whenever `lobbySubscriptionRefCount() > 0`, passing `set` and `get` — both already reach that closure, `set` inside the branch itself at `:1599` and `get` at `:1584`.
5. All three `acquireLobbySubscription` call sites pass three arguments; `forgetTournamentCredential` is called only from the `onTournamentRemoved` fan-out, with both `set` and `get`.
6. `runGatedTournamentRpc` is the only producer of `reason: "not_authorized"` in the file (`grep -n '"not_authorized"' client/src/stores/multiplayerStore.ts` returns exactly the one literal plus the two type declarations).

### 5.7 — `client/src/stores/__tests__/multiplayerStore.tournament.test.ts` (new)

**Harness.** Copy the `localStorage` `vi.hoisted` stub (`:4-26`) and the `openPhaseSocket` mock shape (`:115-139`), then diverge in two load-bearing ways:

- **Do NOT mock `../../services/brokerClient`.** The existing suite stubs it down to `openBrokerClient` only; under that stub `subscribeLobbyOver` would not exist and every frame assertion here becomes vacuous. Precedent that the real module loads fine: `multiplayerStore.visualAvatars.test.ts` has zero `vi.mock` calls. **Do NOT mock `../../services/tournamentClient`** either — the seven helpers and `subscribeTournamentsOver` must be real.
- Build a fake socket with real spy-backed listener bookkeeping:

```ts
function makeFakeSocket() {
  const listeners = new Map<string, Set<(e: unknown) => void>>();
  const send = vi.fn();
  const ws = {
    readyState: 1,                                   // WebSocket.OPEN
    send,
    close: vi.fn(),
    addEventListener: vi.fn((type: string, fn: (e: unknown) => void) => {
      (listeners.get(type) ?? listeners.set(type, new Set()).get(type)!).add(fn);
    }),
    removeEventListener: vi.fn((type: string, fn: (e: unknown) => void) => {
      listeners.get(type)?.delete(fn);
    }),
  };
  return {
    socket: { serverInfo: { mode: "Full" }, ws, close: vi.fn() },
    ws,
    send,
    listenerCount: (type = "message") => listeners.get(type)?.size ?? 0,
    deliver: (type: string, data?: unknown) => {
      for (const fn of [...(listeners.get("message") ?? [])]) {
        fn({ data: JSON.stringify({ type, data }) } as MessageEvent);
      }
    },
    /** Frame-tag tally over `send`, by EXACT PARSED TAG EQUALITY — not a
     *  regex. `UnsubscribeLobby` has a lowercase `s`, so a naive
     *  `(?:Un)?SubscribeLobby` pattern would miss it (confirmed twice in
     *  phase 1's review). Equality on the parsed `.type` cannot suffer that
     *  class of bug. */
    tally: (tag: string) =>
      send.mock.calls.filter(
        ([raw]) => (JSON.parse(raw as string) as { type: string }).type === tag,
      ).length,
  };
}
```

This `send` is a bare spy that never echoes a reply — which is exactly why §5.3's statement ordering is enforced structurally rather than by a test here (F2).

**`withReconnect` driver** — copy `:262-272`'s async-continuation shape, extended so a test can fire `"reconnecting"` and a second `"open"` with a second socket. Shape it to whatever is minimal for R14 (two sockets, `"reconnecting"` then `"open"`); keep it in this file, do not touch the existing suite's driver.

**Global hygiene per test:** `beforeEach` → `vi.clearAllMocks()`, `localStorageItems.clear()`, `useMultiplayerStore.setState({ tournamentCredentials: {} })`, and `useMultiplayerStore.getState().closeSubscriptionSocket()` so module-level subscription state cannot leak between cases (the sets and handles are module scope, not store scope). `afterEach` → `closeSubscriptionSocket()` again.

**Suite layout, one `describe` per matrix group:**

**A. `tournament credentials` (R1, R2, R6, R10, R11, R11b)**

The three eviction cases exercise the **pure functions directly** — `rememberTournamentCredential` / `capTournamentCredentials` are exported and take an injectable `now`, so no store, socket or fake transport is involved. That is the "test the building block, not the special case" convention, and it is what makes the traces below checkable by inspection.

- `persists tournament credentials across a rehydrate`  *(R1)*
- `hydrates a pre-phase-2 blob with an empty credential map`  *(R1)*
- `drops malformed persisted credentials and enforces the cap on hydrate`  *(R2)*
- `merges a later join into an existing organizer credential for the same code`  *(**R11**, merge half — run both orders: create-then-join and join-then-create; assert the single entry carries both tokens and the `playerKey`, each equal to the exact string written)*
- `evicts the least-recently-written credential and never the newest`  *(**R11**, protect half — **M1-corrected fixture**)*

  Fixture: 32 held codes `"T02"` … `"T33"`, every entry `updatedAt: FROZEN`. Write `rememberTournamentCredential(existing, "T01", { organizerToken: "org-T01" }, FROZEN)`.

  Trace, keep `protect` — `codes.length` 33, `overflow` 1; `victims` = `["T02"…"T33"]`; every `updatedAt` difference is 0, so the comparator falls to the `code` tiebreak; lexicographic minimum is `"T02"`; evicted `"T02"`.
  Trace, drop `protect` (revert-check **#6**) — `victims` = all 33; `"T01"` is now the lexicographic minimum of the whole set; evicted `"T01"`.

  Assertions, all four, in this order: `result["T01"]` is present and deep-equals `{ organizerToken: "org-T01", updatedAt: FROZEN }`; `"T02" in result` is **false**; `"T03" in result` is **true** (the named survivor — an implementation evicting more than `overflow` cannot pass); `Object.keys(result).length === MAX_TOURNAMENT_CREDENTIALS`. Under #6 the first and second both flip, which is what revision 2's fixture failed to achieve — it placed the protected code at the lexicographic *maximum*, where the same victim is chosen either way.
- `evicts by write time even when the tournament codes sort the other way`  *(**R11b**, new — the only case with distinct timestamps)*

  Fixture: 32 held codes `"T01"` … `"T32"` where `"TNN".updatedAt = BASE + (33 − NN)` — so `"T01"` is the **newest** (`BASE+32`) and `"T32"` the **oldest** (`BASE+1`), exactly inverting lexicographic order. Write `rememberTournamentCredential(existing, "T99", { organizerToken: "org-T99" }, BASE + 100)`.

  Trace, real comparator — `overflow` 1; `victims` = `["T01"…"T32"]` sorted by `updatedAt` ascending → `"T32"` (`BASE+1`) first; evicted `"T32"`.
  Trace, `updatedAt` term deleted (revert-check **#8**, sort by `code` alone) — minimum is `"T01"`; evicted `"T01"`.

  Assertions: `"T32" in result` is **false**; `result["T01"]` is present; `result["T99"]` is present and deep-equals what was written; size `=== MAX_TOURNAMENT_CREDENTIALS`. Under #8 the first two both flip. `protect` is deliberately not discriminating here (`"T99"` is both newest and lexicographically last, so it survives either way) — that direction belongs to the previous case, and keeping each case single-purpose is what makes #6 and #8 unambiguous.
- `orders eviction deterministically for all-digit tournament codes`  *(**R11**, tiebreak half — **M1-corrected fixture**)*

  Fixture: 32 held codes `"9"`, `"10"`, `"11"` … `"40"` (all *canonical array indices*), every entry `updatedAt: FROZEN`, inserted in that order. Write and protect `"8"` at `FROZEN`.

  Why unpadded: `Object.keys` orders a key numerically only when it round-trips `ToString(ToUint32(k))`. `"9"` and `"40"` do; `"0001"` does **not** (it maps to `"1"`), so revision 2's zero-padded fixture enumerated in insertion order and could not exhibit the hazard at all — an unsorted implementation picked the same victim as a sorted one, making the case inert.

  Trace, real implementation — enumeration order is `"8","9","10",…,"40"`; after `filter(≠"8")` the sort applies, all `updatedAt` tie, lexicographic minimum is `"10"` (since `"1" < "9"`); evicted `"10"`.
  Trace, `.sort(...)` deleted (revert-check **#10**, trusting key order) — first non-protected key is `"9"`; evicted `"9"`.

  Assertions: `"10" in result` is **false**; `"9" in result` is **true**; `result["8"]` present; size `=== MAX_TOURNAMENT_CREDENTIALS`. Under #10 the first two both flip.
- `seeds a late tournament subscriber with the pre-removal list after a TournamentRemoved`  *(**R6**, m2 — the named test for R6's own claim)*

  Subscribe tournament subscriber #1; hold a credential for `"BBB"`. Deliver `TournamentListUpdate` with summaries for `["AAA","BBB"]` (keep the delivered array by reference). Deliver `TournamentRemoved("BBB")` with **no** trailing list push. Then attach a *late* subscriber #2 and assert its `onListUpdate` was called exactly once with an array that (a) is `toBe`-identical to the delivered array and (b) still contains `"BBB"`. Reach-guards in the same test: subscriber #1's `onTournamentRemoved` fired with `"BBB"`, and `tournamentCredentials["BBB"]` is gone — so a `TournamentRemoved` that never reached the fan-out cannot satisfy the "snapshot unchanged" assertion vacuously. Finally push a second `TournamentListUpdate` with `["AAA"]` and seed a third subscriber, asserting it receives the *new* list — proving the snapshot is replaced wholesale by list pushes and by nothing else.
- `forgets credentials when the broker removes the tournament`  *(the F3 credential-fan-out case)*
- `leaves credentials untouched for a TournamentRemoved it holds nothing for`  *(the F6 no-write path: assert no additional `localStorage` write occurred for this frame, alongside the reference-equality assertion)*
- `files a created tournament's organizer token under the reply's code`  *(R10)*

**B. `unified SubscribeLobby refcount` (R3, R4, R5, R14, R16)**:
- `sends SubscribeLobby exactly once for the first tournament subscriber with no lobby subscribers`
- `does not send a second SubscribeLobby for a second tournament subscriber`
- `does not send UnsubscribeLobby while a tournament subscriber is still live`
- `does not send UnsubscribeLobby while a lobby subscriber is still live`
- `sends UnsubscribeLobby exactly once when the last subscriber of either kind leaves`
- `is idempotent when the same detach runs twice`
- `seeds a late tournament subscriber from the cached list push`
- `re-establishes the shared subscription for a tournament-only subscriber after a reconnect`
- `still sends exactly one SubscribeLobby / UnsubscribeLobby pair for a lobby-only cycle`

Every one of these asserts `tally("SubscribeLobby")` / `tally("UnsubscribeLobby")` **and** a delivery reach-guard.

**C. `tournament store actions` (R7, R8, R9, R12, R18)**:
- `sends the matching code's organizer token when two tournaments are held`
- `rejects a gated action with no held token without opening a socket or sending a frame`
- `does not let an organizer token authorize a player-gated action`
- `reaches the wire for a player-gated action once a player token is held`
- `classifies a local refusal as not_authorized and a server rejection as rejected` *(**R18**, new — both halves in one test, run once for `startTournamentRound` (organizer) and once for `reportMatchResult` (player) via `it.each`, so both `switch` arms set `role`. Half (a): no credential → `reason === "not_authorized"`, `role` equals the action's role, every `tally` is 0. Half (b): credential present, deliver an `Error` reply → `reason === "rejected"`, `reason !== "not_authorized"`, `message` equals the broker text verbatim, and the request frame is asserted to have gone out)*
- `leaves credentials untouched when a gated action is rejected` *(both R9 variants: the local-refusal case, and the server-`Error` case where the request frame is asserted to have gone out first)*
- `aborts an in-flight tournament RPC on the reconnecting transition`
- `uses a fresh controller for an RPC started after a reconnect`
- `never closes the borrowed socket on any action path`

**D. `subscription teardown` (R13, R15)**:
- `tears down both listeners, both subscriber sets and both snapshots on closeSubscriptionSocket`
- `tears down the shared subscription when the server address changes`
- `a caller that detaches a late-resolving subscription leaves nothing attached`
- `a null socket makes subscribeTournaments resolve null and its caller's detach a safe no-op`

**Revert-checks to run manually before commit** (each must go red, then be reverted):
1. Restore `if (lobbySubscribers.size === 0)` in `subscribeLobby`'s unsubscribe → suite B's `does not send UnsubscribeLobby while a tournament subscriber is still live` must fail.
2. Gate `subscribeTournamentsOver`'s attachment on `tournamentSubscribers.size` instead of on acquisition → `seeds a late tournament subscriber from the cached list push` must fail.
3. Restore `if (lobbySubscribers.size > 0)` in the `"open"` branch → `re-establishes the shared subscription for a tournament-only subscriber after a reconnect` must fail.
4. Move the credential check in `runGatedTournamentRpc` to after `ensureSubscriptionSocket` → `rejects a gated action ... without opening a socket` must fail.
5. Remove `tournamentCredentials` from `partialize` → `persists tournament credentials across a rehydrate` must fail.
6. Drop the `protect` argument in `capTournamentCredentials` → **R11's** `evicts the least-recently-written credential and never the newest` must fail on **both** its `result["T01"]`-present and its `!("T02" in result)` assertions. *(If only one of the two flips, the fixture has regressed to revision 2's non-discriminating shape — stop and re-check the codes.)*
7. *(F6)* Replace `forgetTournamentCredential`'s early return with the old `set((state) => { if (!(code in state.tournamentCredentials)) return {}; … })` shape → `leaves credentials untouched for a TournamentRemoved it holds nothing for` must fail on its no-additional-persist-write assertion (the reference-equality half stays green either way, which is precisely why the write assertion is the discriminating one).
8. *(M1, new)* Delete the `map[a].updatedAt - map[b].updatedAt ||` term from `capTournamentCredentials`'s comparator, leaving the `code` tiebreak alone → **R11b's** `evicts by write time even when the tournament codes sort the other way` must fail on both `!("T32" in result)` and `result["T01"]`-present.
9. *(M2, new)* Change `runGatedTournamentRpc`'s refusal branch back to `{ ok: false, reason: "rejected", message }` (dropping `role`) → **R18's** half (a) must fail, while half (b) stays green. *(Both going red would mean the two halves are not independent — re-check that (b) really drives a server `Error`.)*
10. *(M1, new)* Delete the `.sort(...)` call in `capTournamentCredentials`, leaving `filter(...).slice(0, overflow)` → `orders eviction deterministically for all-digit tournament codes` must fail on both `!("10" in result)` and `"9" in result`.

### 5.8 — Verification (S9: direct `pnpm`, never Tilt, never cargo)

```bash
cd C:/git/phase/.claude/worktrees/tournament-organizer-pr4-frontend
node scripts/check-protocol-version.mjs                                   # S8: exit 0
pnpm --dir client exec vitest run src/stores/__tests__/multiplayerStore.tournament.test.ts
pnpm --dir client exec vitest run src/stores/__tests__/multiplayerStore.test.ts \
                                 src/stores/__tests__/multiplayerStore.visualAvatars.test.ts
pnpm --dir client exec vitest run src/services/__tests__/tournamentClient.test.ts   # phase 1 stays green
pnpm --dir client run type-check
pnpm --dir client run lint
```

`./scripts/tilt-wait.sh` returns exit 3 ("cannot answer") in this worktree — never a build failure. `cargo fmt`/`clippy`/`test-engine` N/A; no cargo lock.

**Executor environment facts:**
- `verbatimModuleSyntax: true` — every type-only import needs `import type` / inline `type`.
- `noUnusedLocals`/`noUnusedParameters: true` — import only what is referenced.
- `noUncheckedIndexedAccess` is **off**, so `map[code]` is typed non-`undefined`. Presence must be tested with `code in map` or `map[code]?.field`, never truthiness of the index read alone — directly affects `runGatedTournamentRpc` and `forgetTournamentCredential`, both of which already use explicit `?.`/`in`. The R11/R11b assertions use `in`, not truthiness, for the same reason.
- `exactOptionalPropertyTypes` is **off**, but the conditional-spread style in `normalizeTournamentCredentials` is used anyway so the file survives that flag being turned on.
- The whole existing lobby suite is a regression gate for the refactor; if `multiplayerStore.test.ts` goes red, the refcount change broke lobby behavior — **fix the store, do not edit that test file.**

---

## Deferral compliance

| Deferred item | Landing phase | Where phase 2 stops |
|---|---|---|
| All rendering | 4, 5 | No `.tsx`, no JSX, no component. |
| All i18n | 3 | Two raw English literals in `runGatedTournamentRpc`; zero `t()` calls, zero catalog edits. **Named for phase 3: `tournament:errors.notOrganizer` and `tournament:errors.notEntered`.** These are client-authored copy and must be their own keys — routing them through `errors.serverRejected` (which interpolates raw, untranslatable server text) would leave them permanently English in six locales. **Phase 5 selects between them on the typed `result.role` field of a `reason: "not_authorized"` result (M2)** — never on message text, and never by re-reading `tournamentCredentials`. Naming the keys now is not a foreclosure of phase 3's own discovery — S4 explicitly permits later-phase key additions — it just spares phase 3 the rediscovery and spares phase 5 the full 7-catalog-parity cost of adding them late. Neither key is count-bearing or placeholder-bearing, so S4 parts 2 and 3 do not bind them. |
| All routing / nav | 5 | No `App.tsx`, no `navItems.tsx`. |
| Component-level unmount-during-in-flight-connect (#4615) | 5 | Store-level primitives landed (async subscribe resolving `null`, idempotent detach); **interim structural verification is R15**. |
| Organizer/player gating as rendered UI | 5 | Per-code credentials with independent authorities landed and tested (R7/R8/R11), and the refusal is now typed and role-labelled (R18); nothing renders them. |
| `ToSubscribers`-only delivery on a real subscribed socket | 5 | Fake socket proves the store's frame accounting only (phase 1's deferral, restated). |
| Mitigation of B5/B7 (`TournamentUpdate` has no request/broadcast discriminator) | 5 | Phase 2 respects it by mutating no state on any gated failure (R9); builds no client-side correlator. The new `"not_authorized"` member does **not** narrow B5 — it is decided locally, before any frame exists, and makes no claim about what the server did. |
| `isOrganizer`/`myPairing`/outcome + tiebreak labelling | 4 | `playerKey` is stored so phase 4's predicates are decidable; no predicate is written here. |
| `isRecord`'s array acceptance | never (accepted) | Documented in `normalizeTournamentCredentials`'s doc comment. **`isRecord` (`:541-543`) IS inside this phase's scope path** — the earlier "out of scope" justification was wrong (m1). The real reason it is not narrowed: it has five other callers (`:591`, `:659`, `:662`, `:709`, `:719`) in the remembered-host-config and migration paths whose current behavior, array-acceptance included, may be depended on. Tightening a shared predicate for one new caller's benefit would be an unscoped, unjustified behavior change to five unrelated call sites, which phase 2 should not make as a side effect of adding a sixth. The per-entry validation already makes the array case inert for the new caller. |
| `brokerClient.ts` frame relocation | never | Out of scope; frames stay at `:650`/`:656`, store gates *when* they fire. |
| A fifth `TournamentRpcFailureReason` member for local refusals | never (rejected) | `tournamentClient.ts` is phase 1's frozen file and outside phase 2's scope paths, and the concept belongs one abstraction layer up regardless: that union is the wire vocabulary. Phase 2 widens store-side with `GatedTournamentRpcResult<T>` instead (M2). |

**Files touched: exactly the 2 chartered scope paths.** `tournamentClient.ts`, `adapter/types.ts`, `brokerClient.ts`, `LobbyView.tsx`, and `multiplayerStore.test.ts` are all read-only in this phase. Protocol version untouched per S8. All edits to `multiplayerStore.ts` are `Edit`-anchored insertions and targeted replacements — no whole-file rewrite, per the multi-agent safety rule on a 1810-line shared file.
