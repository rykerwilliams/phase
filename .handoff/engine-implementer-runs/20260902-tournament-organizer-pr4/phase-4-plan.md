# Phase 4 Plan — Presentation primitives: pure page-state module + five dumb components

**Mode:** `/engine-planner` phase-plan mode. Phase 4 of 5, run `20260902-tournament-organizer-pr4` (PR 4/4, phase-rs/phase#7718).
**Revision:** 3 — fixes round 2's two material findings (M1: incomplete `role="dialog"` propagation; M2: §5.6's `PairingsList` code contradicts its own rule 8 and doesn't compile) and six minor findings (m1-m6). Everything else carried forward from revision 2 unchanged.
**Worktree:** `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend` · branch `feat/tournament-organizer-pr4-frontend`.
**PHASE_BASE_SHA:** `c7bde455acef08e9e5225fa4ac4b2f47fb52db74` — **verified**: `git rev-parse HEAD` matches, `git status --porcelain` empty before and after all probing.
**Authoritative scope statement:** the charter's phase 4 entry ("Presentation primitives: pure page-state module + five dumb components"), lines 148–178 of `phase-charter`.
**Input obligations (phase 3's deferral allowlist):** phase 3 deferred exactly two things to later phases — `DEFERRED(phase 4)` **`t()` routing** (discharged here, §6 V26) and `DEFERRED(phase 5)` **key-set completeness across mounted pages** (not this phase; no page is mounted here). Phase 3 also left the catalog explicitly **not frozen** (S4).

---

## §0 — Step 0: Premise verification

### 0.1 The Oracle-text gate — N/A, stated explicitly, not assumed

Step 0's hard gate ("fetch the card's real Oracle text from Scryfall") is **not applicable**: this phase references no card, no Oracle text, no ability, and no MTG rules primitive. It renders a tournament-organizer wire projection. The gate is recorded as checked-and-N/A rather than silently skipped, per the same discipline phases 1–3 applied.

The *analogue* of the premise gate that **does** apply here is "verify the wire shapes and broker behaviour you are building against, from Rust source, not from charter prose." That is §0.2–§0.4, and it produced three material corrections — plus, at revision 2, one further broker refusal the first revision had not read (§0.3, F4).

### 0.2 Premises CONFIRMED against real source (not prose)

| # | Premise | Evidence |
|---|---|---|
| C1 | All 16 wire types phase 1 minted exist and have the shapes the charter assumes | `client/src/adapter/types.ts:4501-4728`, read in full |
| C2 | The 7 store actions + `GatedTournamentRpcResult<T>` / `TournamentNotAuthorized` / `TournamentRole` / `TournamentCredential` are exported and typed as the charter describes | `client/src/stores/multiplayerStore.ts:366-503, 755-809, 943-970` |
| C3 | `en/tournament.json` carries 111 keys across the 12 groups phase 3 authored | full file read (147 lines) |
| C4 | `status.*` and `bracket.*` **are** directly indexable off wire PascalCase values | measured, probe P2: `t("status.InProgress") → "In Progress"`, `t("bracket.SingleElimination") → "Single Elimination"` |
| C5 | `outcome.*` / `standings.tiebreaks.*` are **not** indexable off wire tags | measured, probe P2: `i18n.exists("tournament:outcome.Bye") === false`, `i18n.exists("tournament:outcome.bye") === true`; `…tiebreaks.HeadToHead.… === false`, `…tiebreaks.headToHead.… === true` |
| C6 | `FOUR_FORM_STEMS` is `{ns, stem}` pairs with 17 entries, the 17th being `{ns:"tournament.json", stem:"list.entrants"}` | `client/src/i18n/__tests__/localeParity.test.ts:146-164`, use site `:211-216` |
| C7 | The broker rejects `SingleElimination` + arity ≠ 2 | `crates/lobby-broker/src/tournament.rs:1514-1523` (comment `:1514-1517`, guard `:1518-1523`) — **line range corrected at revision 2, m2** |
| C8 | Standings arrive pre-ranked; `standings()` binds **one** `tiebreak_order` and maps every row with it | `tournament.rs:905-935` — the arm is homogeneous per tournament **server-side** |
| C9 | `TournamentSummary.created_at` is unix **seconds** | `tournament.rs:1527` `let now = env.now_ms() / 1000;` → `created_at: now` (`:1546`) |
| C10 | The i18n typing oracle is inert (`tsc` does not catch a bad key) | measured, probe P3 + its positive control P3b |
| C11 | **`report_result` refuses `Bye` and `Forfeit` unconditionally, and permits re-reporting a `Reported` pairing** | `tournament.rs:1741-1753`, read in full at revision 2 — see F4 |

### 0.3 Premises CORRECTED — four material findings

These are **implementation-level precision corrections to charter shorthand**, in the same class as phase 1's §0.9(A)/(B) and phase 2's R5 finding. None changes the charter's design intent, none changes phase 4's unit or scope-path count, and none requires a charter re-review. All four are fixed inside this plan.

---

**F1 (material) — `ReportResultDialog`'s gate authority is the pairing's seat count, not the tournament's arity. The charter's shorthand is wrong at arity 3.**

The charter says: *"`game_wins` inputs appear only at arity 2 (pods are single-game per MSTR); at arity 4 the dialog submits `Decisive { winner, game_wins: {} }`."*

Verified against `validate_match_result` (`crates/lobby-broker/src/tournament.rs:967-1021` — the `pub fn` at `:967`, its doc comment at `:963-966`, its closing brace at `:1021`; **line range corrected at revision 3, reviewer's m2**): the broker branches on **`pairing.players.len() == 2`**, not on `MatchArity`:

```rust
if pairing.players.len() == 2 {
    // require exactly both keys AND a legal completed-Bo3 tally
    if game_wins.len() != 2 || !game_wins.contains_key(a) || !game_wins.contains_key(b) { … }
    if !matches!((wa, wb), (2, 0) | (2, 1) | (0, 2) | (1, 2)) { … }
} else if !game_wins.is_empty() {
    return Err("Pod results are single-game per MSTR - game_wins must be empty");
}
```

A **2-seat pairing in an arity-3 tournament is reachable in production**, not hypothetical:
- `MatchArity::new` accepts `2..=128` (`tournament.rs:96-113`), so arity 3 is legal.
- `MatchArity::short_pod_size()` is `arity - 1` (`tournament.rs:123-126`), so a short pod at arity 3 seats **2**.
- `partition_round` (`tournament.rs:1058-1095`) reaches it: at `n = 5`, `seats = 3`, `short_size = 2` → `short_pods = 1`, `remainder = 3`, `full_pods = 1`. One 3-seat pod plus one **2-seat** pairing.

Under the charter's literal instruction the dialog would gate on `summary.arity === 3 ≠ 2` and submit `game_wins: {}` for that 2-seat pairing — which the broker rejects **every time** with *"Head-to-head result must report game wins for exactly both players."* The failure would be invisible until phase 5, and even there it would surface only as a `{ok:false}` the module header's part-4 caution already tells phase 5 not to trust.

**Fix (in this plan):** the dialog gates on `pairing.players.length === 2`, and **does not take `arity` as a prop at all** — the wrong authority becomes unrepresentable rather than merely unused. Matrix row V22 carries the hostile fixture that fails under the charter's literal version.

---

**F2 (material) — `CreateTournament.scoring` is wire-mandatory with no client-side defaulting path; the charter never says where the form's initial policy comes from.**

Verified at `crates/lobby-broker/src/protocol.rs:689-698`:

```rust
CreateTournament {
    name: String,
    arity: MatchArity,
    scoring: ScoringPolicy,          // ← NO #[serde(default)]
    bracket: BracketShape,
    #[serde(default)]
    total_rounds: Option<u32>,       // ← defaulted; "Automatic" is expressible
},
```

So `total_rounds` has an "Automatic" affordance (and the catalog carries `create.totalRoundsAuto` for exactly that), but **`scoring` does not**. The client must author one, and there is no RPC among phase 1's seven helpers that asks the broker for its default. The broker's own default is arity-dependent — `ScoringPolicy::default_for_arity` (`tournament.rs:217-227`) = `win_points = 2n - 1`, `draw_points = 1`, `loss_points = 0` (arity 2 → 3/1/0; arity 4 → **7**/1/0).

Shipping a fixed 3/1/0 prefill would silently give every pod organizer MTR head-to-head scoring instead of MSTR pod scoring — a real defect against the charter's own "arity-polymorphic" goal.

**Fix (in this plan):** `tournamentPageState.ts` exports **one** `defaultScoringForArity(arity)` carrying an explicit source citation to `tournament.rs:217`, unit-tested at arity 2 / 4 / 128 (V12). The form uses it for the *prefill only*, re-prefilling when arity changes **until the organizer edits a scoring field** (a `scoringTouched` UI flag), after which the organizer's values are authoritative. This is a form-prefill mirror, not a rule duplication: the value is user-editable and the broker validates it (`ScoringPolicy::new` rejects `win_points == 0`), so drift degrades a default, never a correctness guarantee. Stakes and residual risk are stated in §7.3 rather than hidden.

---

**F3 (minor, but it would have cost the executor a round) — the charter's `t()`-routing assertion, as literally worded, can never fire.**

The charter's V-row says *"assert no rendered text node equals a raw `tournament.…` key path."* Measured (probe P2): a missing key renders **without its namespace prefix** —

```
t("standings.doesNotExist")  →  "standings.doesNotExist"        // NOT "tournament.standings.doesNotExist"
```

This reproduces phase 3's C3 correction independently, on this exact tree. Phase 3 already restated its own deferral in a form that can trigger; this plan restates **phase 4's discharging row** the same way. V26 asserts no rendered text node matches a *bare dotted key path* (`/^[a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+$/`), with a paired positive reach-guard.

---

**F4 (material, NEW at revision 2 — this is round 1's blocking finding B1) — `report_result` refuses two `PairingOutcome` arms *before* any validation runs, so the report affordance itself must be arm-gated, not merely prop-gated.**

Revision 1 applied F1's reasoning (*honour the broker's total contracts; never duplicate its conditional rules*) to the **game-wins inputs inside the dialog** — but not to the **report action in `PairingsList` that opens the dialog**. §5.6 let `onReport` render its affordance unconditionally whenever the prop was supplied. That is a real defect against this plan's own §4.4 principle.

Verified by reading `TournamentMeta::report_result` in full (`crates/lobby-broker/src/tournament.rs:1741-1753`) — **not from the charter, not from memory**:

```rust
match meta.pairings[index].outcome {
    Some(PairingOutcome::Bye) => {                                   // :1742
        return Err(format!(
            "Pairing {pairing_id} is a bye and has no result to report"   // :1744
        ))
    }
    Some(PairingOutcome::Forfeit { .. }) => {                        // :1747
        return Err(format!(
            "Pairing {pairing_id} was resolved by forfeit and cannot be reported"  // :1749
        ))
    }
    Some(PairingOutcome::Reported(_)) | None => {}                   // :1752 — BOTH permitted
}
validate_match_result(&meta.pairings[index], &outcome, &meta.players)?;   // :1754
```

Three facts this establishes, each load-bearing for the fix:

1. **The refusal is unconditional and total**, exactly like the `game_wins`-must-be-empty contract F1 honours. It is not a judgement about the *content* of a submission; it is a statement that for these two arms **no submission can ever succeed**. `validate_match_result` is never reached (`:1754` is after the `match`).
2. **Both refused arms are production-reachable**, so this is not a type-level-only guard:
   - **`Bye`** — set by normal round generation (`tournament.rs:1323`, `outcome: Some(PairingOutcome::Bye)`), reached through `partition_round`'s ordinary remainder handling whenever the entrant count does not divide evenly. Every odd-sized Swiss round at arity 2 produces one.
   - **`Forfeit`** — set by `drop_player`'s auto-settlement (`tournament.rs:1828`, `meta.pairings[index].outcome = Some(PairingOutcome::Forfeit { winner })`), whose own doc comment (`:1760-1775`) states the rule: *"Head-to-head: the remaining player is awarded `PairingOutcome::Forfeit` immediately"*, generalized to *"Pod reduced to exactly one active player: the same forfeit."* Any drop mid-round produces one.
3. **Re-reporting an already-`Reported` pairing IS legal** — `Some(PairingOutcome::Reported(_)) | None => {}` at `:1752` falls through to validation identically to a pending pairing, and `:1755` overwrites the outcome. So the correct guard is **arm-selective**, *not* "unresolved only." A guard written as `outcome === null` would wrongly hide a legal correction action for every already-reported match — the failure mode an organizer hits the moment they mistype a game count.

**Why this cannot be deferred to phase 5 (the reason it is blocking rather than a note).** The decision is **per-pairing** and must be made where the pairing row is rendered — inside `PairingsList.tsx`. That file is in **phase 4's** scope paths (charter `:158`) and is **absent from phase 5's** (charter `:186-199` lists only `TournamentLandingPage.tsx`, `TournamentPage.tsx`, `App.tsx`, the three `chrome/` files, two page test files and `localeParity.test.ts`, plus one conditional `AppShell.tsx`). Shipping an unguarded prop here would **structurally foreclose** the fix — the same class of seam failure the charter already learned once at **S3**, where phase 1 was given a deliberate zero-frame constraint precisely so that phase 2 could unify the refcount inside *its own* scope. A plan must not hand its successor a defect the successor is not permitted to touch.

**Also noted, honestly:** `onReport` is **this plan's own addition**, not charter shorthand — the charter's `PairingsList` row (`:171`) specifies only arity-polymorphic rendering and says nothing about a report affordance. Revision 1 introduced the prop because phase 5 needs it and cannot add it. That makes the guard this plan's responsibility twice over: the prop is ours, so its contract is ours.

**Fix (in this plan):** `tournamentPageState.ts` exports **`isReportable(outcome)`** — a second exhaustive `PairingOutcome` discrimination sitting alongside `outcomeLabelKey`, terminating in the same `const unreachable: never` form, carrying the `tournament.rs:1741-1753` citation and stating explicitly that the `Reported` arm is permitted. `PairingsList` renders its report action **iff `onReport` is supplied *and* `isReportable(pairing.outcome)`**. No arm test appears inline in the component. New matrix rows **V29** (unit, with compile-time exhaustiveness) and **V30** (component, hostile fixture + paired positive reach-guard), new revert-checks **RC10** (drop the guard) and **RC11** (narrow it to "unresolved only", which must red the `Reported` half). §5.2, §5.6, §4.3, §4.4, §4.11 and §6 are updated.

### 0.4 Premise refinements (non-blocking, hand to the executor)

- **R1 — the `add-frontend-component` skill's i18n instruction is measurably wrong for this repo.** The skill says *"you do **not** edit `es/fr/de/it/pt`."* Measured (probe P8): adding one key to `en/tournament.json` alone produces **12 failures** — 6 in `resources.test.ts` and 6 in `localeParity.test.ts`, one per non-English locale. The skill also omits `pl` entirely (7 locales exist). Charter seam **S4 is authoritative**; the skill bullet is stale. Phase 4 expects to add **zero** keys (§5.1), so this is a trap-avoidance note, not an obligation.
- **R2 — `types.ts` does not document `created_at`'s unit.** Measured seconds (C9). `TournamentSummary.created_at`'s doc comment is silent, unlike `LobbyGame`'s de-facto convention. **Report, do not repair** — `types.ts` is not in phase 4's chartered scope paths and is the high-collision shared file S1 warns about.
- **R3 — carried forward from entry 23 (phase 2's impl-review LOW).** A `let x: T | undefined` declared *before* a `switch` satisfies TS's definite-assignment analysis and therefore does **not** make the switch compile-time exhaustive. Every exhaustive discriminator in this phase uses an explicit `const unreachable: never = value; return unreachable;` terminal instead, which genuinely does. This is the concrete discharge of that finding's suggested remedy in the first module that needed it.
- **R4 — carried forward from entry 14.** The charter's static-assertion regex `(?:Un)?SubscribeLobby` is broken. Phase 4 authors no such assertion, so this is informational only; the one static source assertion this phase *does* author (V28) uses exact-substring/regex forms with a positive control, per the house convention in `client/src/adapter/__tests__/boundary-guardrails.test.ts`.

---

## §1 — Applicable skills

Per the skill table, exactly one applies: **`/add-frontend-component`** (loaded and read in full). `/add-engine-effect`, `/oracle-parser`, `/add-keyword`, `/add-trigger`, `/add-static-ability`, `/add-replacement-effect`, `/add-interactive-effect`, `/casting-stack-conditions`, `/add-ai-feature-policy`, `/add-card-data-pipeline`, `/add-engine-variant` and `/card-test` are all N/A — this phase touches no Rust, no engine enum, no parser, and no cast pipeline.

**Every checklist step, with its disposition** (phase-plan mode requires later-phase steps to appear as `DEFERRED(phase n)`, not to be omitted):

| Skill checklist step | Disposition in phase 4 |
|---|---|
| **Phase 1** — `WaitingFor` / `GameAction` / `GameEvent` / `GameObject` type additions | **N/A.** These are the *engine* game-session unions. The tournament wire mirrors were minted in phase 1 (`types.ts:4501-4728`) and are frozen. No union in this phase. |
| **Phase 2** — component implementation (Pattern A/B/C) | **APPLIES**, as **Pattern C (board element / non-overlay)** for all five: read-only, prop-driven, no `dispatch`. Patterns A and B are `WaitingFor`-routed game overlays and do not apply. §5.3–5.7. |
| **Phase 2.5** — internationalize all frontend-authored text | **APPLIES**, and is this phase's chartered deliverable. Namespace-by-source-directory resolves `components/tournament/*` → `"tournament"` — consistent, no conflict. §5.1 rule 1, discharged by V26. **Exception noted:** the step's "do not edit other locales" bullet is superseded by S4 (§0.4 R1). |
| **Phase 3** — `GamePage.tsx` `WaitingFor` routing | **`DEFERRED(phase 5)`.** Nothing mounts these components here; routing is `App.tsx` + the two pages, all phase 5. |
| **Phase 4** — animation integration (`eventNormalizer`, `AnimationOverlay`) | **N/A.** No `GameEvent` is produced or consumed; there is no animation pipeline on the lobby/tournament surface. |
| **Phase 5** — game log (`logFormatting.ts`, `LogEntry.tsx`) | **N/A.** Same reason. |
| **Phase 6** — multiplayer player gating (`waitingFor.data.player === playerId`) | **N/A in its literal form** (no `WaitingFor`). Its *substance* — "the wrong viewer must not see privileged controls" — is `DEFERRED(phase 5)` per the charter (organizer-only controls as rendered UI), and this phase lands its typed input: `viewerRoles` (§5.2, V11). **Phase 6's state-filtering bullet is already satisfied structurally:** every type this phase renders is a token-free broker projection; secrets (`organizer_token`, `player_token`) live only in the store's `tournamentCredentials` and never enter a component prop. |
| **Phase 7** — component tests | **APPLIES**, with **two deliberate, precedent-backed deviations** justified in §4.3: (a) the factory helpers `gameObjectFactory`/`gameStateFactory`/`waitingForFactory` are `GameState`-shaped and have no bearing on tournament wire fixtures — the applicable precedent is `GameListItem.test.tsx`'s inline typed `const baseGame: LobbyGame`; (b) "seed the store, don't mount providers" is inapplicable because these components read **no** store — that is the phase's defining property. All other Phase-7 bullets apply verbatim: colocated `__tests__/`, assert real English strings, semantic queries, and the interaction-contract assertion (here: the `onSubmit`/`onOpen`/`onReport` callback payload rather than a `GameAction`). |
| **Phase 7** — "Run via Tilt" | **Superseded by charter S9** (measured again this session: `tilt get uiresource clippy` exits non-zero — Tilt does not watch this worktree). Verify directly with `pnpm`. A `./scripts/tilt-wait.sh` exit `3` here means *cannot answer*, never *build failure*. |
| **Self-Maintenance** — "update the directory reference table if new component directories were added" | **Explicit decision point, §7.5.** `components/tournament/` is new. The skill file is not in phase 4's chartered scope paths. |

---

## §2 — Analogous trace (hard gate)

**Traced feature: the multiplayer lobby list surface** — the closest existing "pure page-state module + dumb presentational components for a broker-backed multiplayer feature" in the codebase, and the one whose file-naming this phase's charter mirrors exactly (`multiplayerPageState.ts` → `tournamentPageState.ts`).

**Full trace path, followed end-to-end:**

```
crates/lobby-broker/src/protocol.rs   (LobbyGame wire shape)
  → client/src/adapter/types.ts                              (LobbyGame mirror)
  → client/src/services/brokerClient.ts                      (subscribeLobbyOver — borrowed-socket helper)
  → client/src/stores/multiplayerStore.ts                    (subscribeLobby, refcount, lobbySnapshot)
  → client/src/pages/multiplayerPageState.ts                 (PURE module: MultiplayerView, LiveCheck, classifyCompatResult)
  → client/src/pages/__tests__/multiplayerPageState.test.ts  (pure unit tests, no render, no store)
  → client/src/pages/MultiplayerPage.tsx                     (1059 lines — owns view state, calls the store)
  → client/src/components/lobby/LobbyView.tsx                (subscribes; owns the `if (cancelled) { detach?.(); return; }` idiom)
  → client/src/components/lobby/GameListItem.tsx             (DUMB row: props only, useTranslation("multiplayer"), no store)
  → client/src/components/lobby/__tests__/GameListItem.test.tsx (renders with plain props; asserts real English; asserts the callback payload)
```

**What the trace establishes, and what it warns against:**

1. **The split is a real, shipped house pattern, not an invention.** `multiplayerPageState.ts` holds a discriminated `LiveCheck` union plus one pure classifier; `MultiplayerPage.tsx` holds state and store calls; `GameListItem.tsx` renders props. `tournamentPageState.ts` + five components + (phase 5) two pages is the same shape one layer larger.
2. **Dumb components take props and a callback, and read no store.** `GameListItem` takes `{game, onJoin, compatible?, hostGameCode?}` and calls `useTranslation("multiplayer")` and nothing else. This is the exact prop-shape template for `TournamentListItem`.
3. **Component tests need no provider and no store seeding.** `GameListItem.test.tsx` renders with a bare `render(<GameListItem …/>)` and asserts the literal English string `"You are hosting this game."`. Measured green this session (probe P1, 6/6). `test-setup.ts` registers the real English catalogs globally — including `tournament`, added by phase 3 at `:13`/`:29`/`:40`. This is the mechanism V26 depends on.
4. **Counter-example, and the single most important thing this trace produced.** The *nearest by name* component — `client/src/components/draft/StandingsTable.tsx` — is a **counter-example on the logic-placement axis and must not be copied.** It (a) subscribes to `useMultiplayerDraftStore` directly rather than taking props, (b) **re-sorts server data client-side** (`[...standings].sort((a,b) => b.match_wins - a.match_wins …)`, `:83-89`), and (c) **computes tiebreak values client-side** (`computeGwp`, `:11-15`, complete with a hand-rolled 1/3 WPN floor). Its test file (`components/draft/__tests__/StandingsTable.test.tsx`) is nine lines of `it.todo` stubs — no assertion exists that would notice. Every one of those three is exactly what the charter's `TournamentStandingsTable` row forbids and what CLAUDE.md's display-layer principle forbids. The executor will find this file when searching for "StandingsTable"; §5.5 names it and says do not copy it. Per multi-agent safety, phase 4 also does **not** touch or fix it — it is other, shipped work.
5. **`ConcedeDialog.tsx` is the dialog template** (`components/multiplayer/ConcedeDialog.tsx`): `FocusScope` render-prop + `AnimatePresence` + `role="alertdialog"` + `aria-modal` + `useId()`-linked `aria-labelledby`/`aria-describedby`, and it already reuses `t("common:actions.cancel")` and `t("common:actions.closeNamed", { name })`. `ReportResultDialog` composes the same primitives, with **one deliberate, named deviation on the `role` attribute** (§5.7).

---

## §3 — Files read in full before proposing changes

| File | Why |
|---|---|
| `.git/engine-implementer-runs/20260902-tournament-organizer-pr4/phase-charter` | scope authority (all **296** lines — re-counted at revision 3, reviewer's m6; revisions 1–2 said 297 — S1–S9); re-read at revision 2 to confirm phase 5's scope paths exclude `PairingsList.tsx` (F4) |
| `.git/…/phase-fit` | every entry through round 2's review of this plan — charter evolution and all three prior phase cycles |
| `client/src/adapter/types.ts:4501-4728` | every type this phase renders; `PairingOutcome`/`PodOutcome` re-read at revision 2 (`:4550-4582`) for the `isReportable` discrimination |
| `client/src/services/tournamentClient.ts` (529 lines, full) | `CreateTournamentRequest`, `TournamentRpcResult`, the module header's five load-bearing properties |
| `client/src/stores/multiplayerStore.ts:366-503, 755-809, 940-977` | `TournamentRole`, `TournamentCredential`, `TournamentNotAuthorized`, `GatedTournamentRpcResult`, all 7 action signatures |
| `client/src/i18n/locales/en/tournament.json` (full, 111 keys) | the catalog this phase consumes; `detail.reportResult` confirmed present at `:79` (zero-catalog-delta claim under F4's fix) |
| `client/src/i18n/__tests__/localeParity.test.ts:146-218` | `FOUR_FORM_STEMS` post-refactor shape and its use site |
| `client/src/test-setup.ts` (full) | the global English i18next instance V26 depends on |
| `client/src/pages/multiplayerPageState.ts` + its test | the pure-module precedent |
| `client/src/components/lobby/GameListItem.tsx` + its test | the dumb-component + prop-driven-test precedent |
| `client/src/components/draft/StandingsTable.tsx` + its test | the counter-example (§2.4) |
| `client/src/components/multiplayer/ConcedeDialog.tsx` | the dialog/FocusScope precedent, and the source of the `role="alertdialog"` value §5.7 deliberately departs from |
| `client/src/components/ui/FocusScope.tsx` (head) | render-prop API |
| `client/tsconfig.app.json`, `client/vitest.config.ts`, `client/eslint.config.js`, `client/package.json` | compiler/test/lint constraints |
| `crates/lobby-broker/src/tournament.rs` (§§ MatchArity, ScoringPolicy, Tiebreaks, standings, `validate_match_result` (`:967-1021`), `partition_round`, `create_tournament`, **`report_result`**, **`drop_player`**) | F1, F2, F4, C7, C8, C9, C11 |
| `crates/lobby-broker/src/protocol.rs:689-706` | F2 |

---

## §3.5 — Probe log (measured, then reverted; tree verified pristine)

**10 distinct probes (P1–P10) across 11 table rows** — P5 and P6 share one row, and four of the ten carry a paired control probe (P2b and P4b have their own rows; P3's control P3b and P7's control P7b are recorded inside their parents' rows). Revision 3 adds **P11** (with two paired controls, P11b/P11c) in its own block below the table, for **11 distinct probes in total**. This convention is stated here and matched verbatim in §8 (reviewer's m5: revision 2 said "nine" here and "10" in §8, and the table's row count was never reconciled with its P-number count). All run in the implementation worktree with `pnpm exec vitest` / `pnpm exec tsc` / `pnpm exec eslint` / `node`. **No cargo, no Tilt, no target lock taken** (S9). Every mutation was restored and `git status --porcelain` is empty at plan time.

| # | Question | Result | Reach-guard |
|---|---|---|---|
| **P1** | Do prop-driven component tests + the pure-module test pass at PHASE_BASE_SHA under this Node? | **6/6 green**, 2 files | positive by construction (they assert real English copy) |
| **P2** | Does `useTranslation("tournament")` resolve in a component render, and what does a *missing* key produce? | `known → "Standings"`; **`missing → "standings.doesNotExist"` (no ns prefix)**; `status.InProgress → "In Progress"`; `bracket.SingleElimination → "Single Elimination"`; `list.entrants` count 1→`"1 entrant"`, 5→`"5 entrants"`; `labels.roundOf{2,5} → "Round 2 of 5"`; `outcome.forfeit{winner} → "Forfeit — Ann"`; `common:actions.cancel → "Cancel"`; `menu:nav.tournament → "Tournaments"`; `i18n.options.ns` = the 8-entry list incl. `tournament` | the `known` value resolving proves the instrument fires; **F3** is the negative result it licenses |
| **P2b** | Is the `outcome.*` casing trap real? (entry 29's forward note to this planner) | **`i18n.exists("tournament:outcome.Bye") === false`**, `outcome.bye === true`; `…tiebreaks.HeadToHead.… === false`, `…tiebreaks.headToHead.… === true` | the lowercase forms returning `true` is the paired positive |
| **P3** | Does `tsc -b --noEmit` catch a nonexistent `t()` key? | **No — exit 0** with `t("standings.doesNotExist")` present. Reproduces phase 3's C2 independently. | **P3b (mandatory control):** injecting `const x: number = "s"` into the *same file* produces `error TS2322` — so `tsc` genuinely compiles `src/**/__tests__/*.tsx` (`tsconfig.app.json` `include: ["src"]`). The exit-0 is a real negative, not an unexamined file. |
| **P4** | What does eslint enforce? | `@typescript-eslint/no-unused-vars` **error** (`^_` ignore); `react-hooks` recommended; `react-refresh/only-export-components` **warn** | — |
| **P4b** | Does exporting a plain function from a `.tsx` warn? | **Yes** — `react-refresh/only-export-components`: *"Fast refresh only works when a file only exports components. Use a new file to share constants or functions between components."* | the same file with only a component export is clean |
| **P5/P6** | Broker facts behind F1/F2/C7–C9 | `validate_match_result` gates on `pairing.players.len() == 2`; `MatchArity` 2..=128; `short_pod_size = arity-1`; `partition_round(n=5, arity=3)` = 1 full + 1 **2-seat** pod; `scoring` wire-required; `default_for_arity` = `2n-1`/1/0; `standings()` binds one `order`; `created_at = now_ms()/1000` | line-exact reads, not greps alone |
| **P7** | Does `import type` from `multiplayerStore` drag the store's runtime into a pure-module test? | **No.** `import 14ms`, `transform 87ms`, no warning. | **P7b (mandatory control):** switching one symbol to a **value** import → `import 925ms`, `transform 792ms`, **and the `--localstorage-file` warning appears**. A 66× import-time delta plus the environment hazard materializing is an unambiguous positive control. This makes V28 worth pinning. |
| **P8** | Does an English-only key go red? | **12 failures** — 6 × `resources.test.ts` (`es/fr/de/it/pt/pl has exactly the same keys as en`) + 6 × `localeParity.test.ts` (`tournament.json has exactly the English key set`) | restored; 199 green again |
| **P9** | Pristine baseline of the i18n gates | **199/199 green, 3 files** — matches phase 3's measured `179 → 199` delta exactly | — |
| **P10** | JS object-key enumeration with digit-like keys (`game_wins` ordering) | `Object.keys(JSON.parse('{"12":2,"7":0,"alice":1}'))` → **`["7","12","alice"]`** | `{"bob":…,"alice":…}` → `["bob","alice"]` (insertion order preserved for non-integer keys) — the paired negative that isolates the integer-key hoisting |

**Revision-2 verification (read-only; no probe, no mutation, tree untouched — stated as such rather than dressed up as a measurement).** Every `tournament.rs` line citation this plan makes was re-derived by line-exact read at revision 2, not carried forward: `report_result`'s refusal block `:1741-1753` with its two `Err` strings at `:1744`/`:1749` and the permissive `Reported(_) | None` arm at `:1752` (F4/C11); the bye-generation site `:1323` and the forfeit auto-settlement site `:1828` with `drop_player`'s doc comment `:1760-1775` (F4's reachability); `create_tournament`'s `SingleElimination` guard `:1514-1523` and its `total_rounds == Some(0)` rejection at **`:1524`** (m2 — revision 1 cited `:1523`, which is the closing brace of the *preceding* guard); `validate_match_result` at `:967-1021` with its two error strings at `:996`/`:1015`. `git rev-parse HEAD` re-confirmed `c7bde455a` and `git status --porcelain` re-confirmed empty afterwards.

**Revision-3 verification (P11 — a real probe this time, with two paired positive controls; mutation made, measured, then deleted).** Round 2's M2 was that §5.6's prescribed `outcome.Reported.Decisive.game_wins` expression violates §5.1 rule 8 *and* does not compile. Both halves were re-measured here rather than taken on the reviewer's word, by writing a throwaway `client/src/__probe_m2.ts` and running `pnpm exec tsc -p tsconfig.app.json --noEmit` against the real `client/src/adapter/types.ts`:

| | Measured |
|---|---|
| **P11 — does the revision-3 replacement compile?** | **Yes, exit 0.** `decisiveGameWins` (§5.2 item 6) + the widened `gameWinsEntries` parameter + the §5.6 call site + V7's `{"12":2,"7":0}` fixture all type-check clean together |
| **P11b — positive control A: does the *old* expression really fail?** | **Yes, exit 2**, with exactly the two errors round 2 reported: `error TS18047: 'p.outcome' is possibly 'null'` and `error TS2339: Property 'Reported' does not exist on type 'PairingOutcome'. Property 'Reported' does not exist on type '{ Forfeit: { winner: string; }; }'` |
| **P11c — positive control B: is `decisiveGameWins`'s `never` terminal load-bearing?** | **Yes.** Deleting the `"Forfeit" in outcome` branch → `error TS2322: Type '{ Forfeit: { winner: string; }; }' is not assignable to type 'never'`. Deleting the inner `reported === "Draw"` branch → `error TS2322: Type '"Draw"' is not assignable to type 'never'` **plus** a second error at the `"Decisive" in reported` narrowing (`Type 'PodOutcome' is not assignable to type 'object'`), because the `in` operator cannot be applied to a union that still admits the string arm. Both `never` bindings therefore genuinely fail closed |

**Trap worth naming, because it silently voided the first run of P11b:** a comment beginning `// @ts-expect-error` suppresses the next line's errors even when the text continues into an unrecognised suffix (`// @ts-expect-error-NOT-USED: …` still suppresses). The first attempt at P11b returned exit 0 for that reason, not because the expression compiled. It was re-run without the directive and produced the two errors above. Any executor writing a "this must not compile" check must not put an `@ts-expect-error`-prefixed comment above it.

`client/src/__probe_m2.ts` was deleted; `git status --porcelain` is empty and `git rev-parse HEAD` is still `c7bde455a`.

**Not probed, labelled as such:** (a) that a 2-seat short pod at arity 3 *actually* reaches a client — derived from `partition_round`'s arithmetic and `MatchArity`'s bounds by reading, not by running the broker; the design is conservative either way (gating on seat count is correct even if the shape never occurs). (b) That a `Bye` or `Forfeit` pairing actually reaches a client — likewise derived from `partition_round`'s remainder handling and `drop_player`'s auto-settlement by reading; and likewise conservative, since the guard mirrors a *total* refusal that cannot become permissive without a broker change. (c) The rendered visual appearance of any component. (d) Full-suite regression at PHASE_BASE_SHA — deliberately skipped: entry 29 established that ~1300 tests/132 files fail at base for a Node v25.2.1 `--localstorage-file` environment reason unrelated to this work, so a full-suite number would be noise, not signal. §5.14 scopes verification to the files this phase touches plus the two i18n gates.

---

## §4 — Architectural sections

### 4.1 Pattern Coverage

Per phase-plan mode, assessed against the **charter's class attribution**, not this phase's own diff.

This phase covers **the entire tournament-organizer presentation surface**, arity-polymorphically. Concretely, one code path renders:

- **every `MatchArity` in `2..=128`** — a bye (1 seat), head-to-head (2), a short pod (`arity-1`), and a full pod (`arity`) all render through one `PairingsList` with no arity branch;
- **all 4 `PairingOutcome` shapes** (`Bye`, `Forfeit`, `Reported→Decisive`, `Reported→Draw`), exhaustively, compile-enforced — now through **three** independent exhaustive discriminations (`outcomeLabelKey` for the label, `isReportable` for the affordance, `decisiveGameWins` for the game-wins tally), each with its own `never` terminal, all three in the same module, so a future fifth arm breaks the build in all three places at once (measured: P11c);
- **both `Tiebreaks` arms** (MTR §3.1 head-to-head, MSTR multiplayer), exhaustively;
- **all 4 `TournamentStatus` and both `BracketShape` members**, by direct catalog indexing off the wire value (C4);
- **both `TournamentRole` authorities** and the both-at-once case phase 2 documented as the *normal* path for a playing organizer.

Card count is not the relevant metric (no cards are involved). The equivalent "is this a class or a special case?" test: **is there any tournament shape the broker can emit that these five components cannot render, or any pairing state whose available actions they misrepresent?** The answer is no, by exhaustive-union construction — and V16's `it.each` over {1,2,3,4} seats × 4 outcome shapes, plus V29/V30's coverage of all four arms' reportability, measure it rather than asserting it. The charter's stop-condition ("if the answer is 1, find the general pattern") is not triggered.

### 4.2 Sizing (mandatory)

**Units — 6.** One unit = one coherent behaviour implementable by a single skill-checklist pass. **Unchanged at revision 2:** F4's fix lands as one additional export *inside the existing U1 module* and one conditional *inside the existing U5 component* — it creates no new coherent mechanic, no new file, and no new registration surface. **Unchanged again at revision 3:** round 2's M2 fix (`decisiveGameWins`, §4.3) is likewise one additional export inside the existing U1 module and one `const` binding inside the existing U5 component. Sizing is 6/6 in all three revisions.

| # | Unit | Registration surfaces | Discriminating test |
|---|---|---|---|
| U1 | `tournamentPageState.ts` — the pure page-state module (**10 function exports**: `viewerRoles`, `outcomeLabelKey`, **`isReportable`**, `tiebreakCells`, `formatTiebreakValue`, **`decisiveGameWins`**, `gameWinsEntries`, `myPairing`, `arityLabel`, `defaultScoringForArity`) | none — a leaf module, imported by U2–U6 and (phase 5) the pages | V1–V13, **V29**, **V31** |
| U2 | `TournamentListItem` | none | V18 |
| U3 | `CreateTournamentForm` | none | V19 (no client-side pre-reject) |
| U4 | `TournamentStandingsTable` | none | V14 (server order preserved under a non-monotonic fixture) |
| U5 | `PairingsList` | none | V16 (`it.each` 4 arities × 4 outcomes, no arity branch), **V30** (arm-gated report affordance), **V32** (game-wins lines only on the `Decisive` arm) |
| U6 | `ReportResultDialog` | none | V22 (seat-count gate, hostile arity-3 short-pod fixture) |

> **Export-count convention, stated so it cannot drift again (m1).** The "10" above counts **function (value) exports**. `tournamentPageState.ts` additionally exports four **types** — `OutcomeLabel`, `TiebreakCell`, `GameWinEntry`, `ArityLabel` — which are not included in that number, exactly as in revisions 1 and 2. Revision 1's U1 row said "7" while §4.3/§5.2 listed and numbered 8; revision 2 corrected that to **9** (adding `isReportable`) and attached this convention; **revision 3 moves it to 10**, adding `decisiveGameWins` as round 2's M2 fix (§4.3). The type count is unchanged at four — `decisiveGameWins` returns a `Readonly<Record<string, number>>`, a projection of the wire's own field type, and mints no new view-model type. The ten are enumerated in the same order in §5.2, and this number appears in exactly three places — this row, §4.3's "New helpers" paragraph, and §5.2's list header — all three of which must move together.

**Inter-unit dependency edges:** U1 → U2, U1 → U4, U1 → U5, U1 → U6 (all consume its label/derivation helpers). U1 → U3 (`defaultScoringForArity`, `arityLabel`). U2…U6 are mutually independent and could be implemented in any order after U1. No unit depends on another component.

**Source scope-paths — 6** (test files excluded outright per the T2 counting rule; no generated artifacts, no translation mirrors expected — §5.1):

```
client/src/pages/tournamentPageState.ts
client/src/components/tournament/TournamentListItem.tsx
client/src/components/tournament/CreateTournamentForm.tsx
client/src/components/tournament/TournamentStandingsTable.tsx
client/src/components/tournament/PairingsList.tsx
client/src/components/tournament/ReportResultDialog.tsx
```

**Test paths (T2-excluded, listed so the executor knows they are in scope to author):**

```
client/src/pages/__tests__/tournamentPageState.test.ts
client/src/components/tournament/__tests__/TournamentListItem.test.tsx          ← ADDED, see below
client/src/components/tournament/__tests__/CreateTournamentForm.test.tsx        ← ADDED, see below
client/src/components/tournament/__tests__/TournamentStandingsTable.test.tsx
client/src/components/tournament/__tests__/PairingsList.test.tsx
client/src/components/tournament/__tests__/ReportResultDialog.test.tsx
client/src/i18n/__tests__/localeParity.test.ts                                  ← in scope, expected UNTOUCHED (§5.1)
```

> **Charter scope-path-hint gap, reported (zero sizing impact).** The charter's phase-4 hint block lists only three component test files, yet its verification plan carries discriminating rows for **`TournamentListItem`** (`player_count` labelled as *active* entrants) and **`CreateTournamentForm`** (must not pre-reject `SingleElimination` + arity ≠ 2). Those two rows are undischargeable without test files. The two files above are added. Both are **test files, excluded from T2 counting outright**, so this phase's unit count stays **6** and its source scope-path count stays **6** — identical to the charter's table row. No phase's fit verdict moves. This is a hint-block omission, not a design defect.

**Phase-fit re-adjudication for this phase, individually:**

- **T1** (units ≥ 2): 6 ≥ 2 → **FIRES**.
- **T2** (source scope-paths ≥ 13): 6 < 13 → **does not fire**.
- **Conjunction T1 ∧ T2: DOES NOT FIRE.** No decomposition required.

**Honest re-derivation, not a copy of the charter's number.** I counted independently from the scope and arrived at 6/6 — the same as the charter's row. I also checked the two ways this could have honestly differed and neither does: (a) if the two added test files counted, source paths would be 8 — still < 13, verdict unchanged; (b) if phase 4 discovered it needed catalog keys, the 7 `tournament.json` files group as **one** path with their authored English source *and are already counted under phase 3's mirror group*, so even that maximal case is 7 — still < 13.

> **The one counting combination that does reach the threshold, named explicitly rather than left for a future re-adjudicator to rediscover (m5), per the precedent phase 3's charter footnote set for its own 17-vs-5 gap.** Combining **both** relaxations at once — counting test files **and** treating the 7 `tournament.json` catalogs as ungrouped, in the maximal case where this phase discovers it needs a key — gives 6 source + 6 new test + 7 catalogs = **19**, which is ≥ 13 and would technically fire T2. **This is not the charter's frozen counting convention**, which excludes test files outright and groups translation mirrors with their authored source, and it is the same relaxation phase 3's footnote already adjudicated and rejected for phase 3's own row. Under the frozen convention this phase is 6 and T2 does not fire. **The verdict is unchanged and no charter revision is warranted** — this sentence exists so that a future reader who re-counts under a different convention finds the discrepancy already accounted for rather than mistaking it for a counting error.

**Under every counting convention available, T2 does not fire for this phase.** No charter revision is warranted.

### 4.3 Building Blocks

The CLAUDE.md helper table (`parser/oracle_nom/`, `game/filter.rs`, `game/quantity.rs`, …) is the **engine** inventory and is entirely N/A — this phase writes no Rust. The applicable frontend inventory, composed from rather than duplicated:

| Existing building block | Used for | Instead of |
|---|---|---|
| `client/src/adapter/types.ts` tournament mirrors (phase 1) | every prop type; `PairingOutcome`/`Tiebreaks`/`PodOutcome` drive the exhaustive discriminators | re-declaring wire shapes locally |
| `multiplayerStore.ts`'s `TournamentRole`, `TournamentCredential` (**`import type` only**, P7) | `viewerRoles`' domain vocabulary | minting a second role union that can drift from the store's |
| `services/tournamentClient.ts`'s `CreateTournamentRequest` | `CreateTournamentForm`'s `onSubmit` payload type | a hand-rolled form-shape interface that could drift from the wire builder |
| `react-i18next` `useTranslation("tournament")` | all frontend-authored copy | any raw JSX literal |
| `t("common:actions.cancel")`, `t("common:actions.closeNamed", { name })` (measured to resolve, P2) | dialog chrome | new `tournament`-namespace keys duplicating `common` |
| `components/ui/FocusScope` (render-prop `({ onKeyDown }) =>`, props `active`/`containerRef`/`ownerRef`/`initialFocusRef`/`returnFocusRef`/`onEscape`) | `ReportResultDialog` focus containment + Escape | a hand-rolled focus trap |
| `framer-motion` `AnimatePresence` + `motion.div` | dialog mount/unmount, per the skill's Common Mistakes table | instant appear/disappear |
| `components/lobby/GameListItem.tsx`'s row shape | `TournamentListItem`'s `<button>` + badge + truncated title + trailing code-chip layout | a novel row idiom |
| `components/multiplayer/ConcedeDialog.tsx`'s a11y wiring (`aria-modal`, `useId()`-linked `aria-labelledby`/`aria-describedby`, backdrop close-button labelling) | `ReportResultDialog` — **but not its `role` value**: `ConcedeDialog`'s `role="alertdialog"` is deliberately **not** carried over; `ReportResultDialog` uses `role="dialog"` (§5.7) | ad-hoc, unlabelled dialog markup |
| `client/src/test-setup.ts`'s global English i18next instance | every component test asserts real copy; V26's mechanism | mounting `I18nextProvider` per test |

**New helpers, each justified: the ten `tournamentPageState.ts` function exports.** Every one exists because **two or more consumers** need the same derivation and a second copy could disagree — `outcomeLabelKey` (`PairingsList` now, the detail page in phase 5), `tiebreakCells`/`formatTiebreakValue` (header and body of the same table, which is exactly where positional drift hides), `decisiveGameWins`/`gameWinsEntries` (`PairingsList` now, the detail page in phase 5, `ReportResultDialog`'s pre-fill later), `arityLabel` (`TournamentListItem` + `CreateTournamentForm`), `viewerRoles`/`myPairing`/`defaultScoringForArity` (chartered inputs for phase 5's gating and prefill). None is a one-call-site wrapper.

**`isReportable` (new at revision 2, F4) earns its place on the same test, and on two further grounds:**
- **Two consumers already.** `PairingsList` gates its report affordance on it *now*, and phase 5's detail page must gate the *same* affordance identically when it renders a single pairing — a second, inline copy in a file phase 5 owns is exactly the drift this module exists to prevent.
- **It belongs with its sibling discriminator.** It is the second exhaustive walk over `PairingOutcome`, sitting immediately beside `outcomeLabelKey`. Keeping both in one module means a future arm added to the wire union breaks the build in one file, at two `never` terminals, rather than in scattered components.
- **The alternative is the banned shape.** Inline `pairing.outcome !== "Bye" && !("Forfeit" in pairing.outcome)` in the component is unexhaustive (no `never` terminal), duplicated per call site, and puts a broker-contract citation inside JSX. §5.1 rule 4 forbids it.

**`decisiveGameWins` (new at revision 3, round 2's M2) — the design decision, argued rather than asserted.**

Round 2 found that revision 2's §5.6 prescribed, inside `PairingsList`'s own body:

```ts
gameWinsEntries(outcome.Reported.Decisive.game_wins, pairing.players)
```

which narrows `PairingOutcome | null` → `{Reported: …}` → `{Decisive: …}` **inline in a component**. That is precisely what §5.1 rule 8 forbids, and it does not compile: measured (P11b) as `TS18047: 'p.outcome' is possibly 'null'` plus `TS2339: Property 'Reported' does not exist on type 'PairingOutcome'`. This is honest reconstruction damage — rule 8 was *tightened* as part of revision 2's F4 fix without re-checking the pre-existing §5.6 line against it, and the line was a latent compile error in revision 1 as well.

Two remediations were available, and they are genuinely different architectures, not stylistic variants:

- **Option A (chosen) — a new single-purpose export.** `decisiveGameWins(outcome: PairingOutcome | null): Readonly<Record<string, number>> | null` does the narrowing exhaustively in `tournamentPageState.ts` and returns `null` when there is no tally to show. `gameWinsEntries` keeps its existing signature and semantics; the component composes the two.
- **Option B (rejected) — widen `gameWinsEntries` itself** to take `PairingOutcome | null` and do the narrowing in its own body, keeping the export count at 9.

**Why A.** Three reasons, in descending weight:

1. **Abstraction-layer separation** — CLAUDE.md's *"An enum variant must belong to exactly one semantic layer"*, in its function-level form (§4.5). `gameWinsEntries` is a **join**: it walks the broker's seat order and indexes a record, and its entire reason to exist is P10's integer-key hoisting hazard (B7). `decisiveGameWins` is a **discrimination**: it walks a closed wire union. Option B produces one function that does both, and — decisively — one that must answer *four structurally different questions* with the same empty array: "pod, so single-game per MSTR, legitimately no tally", "bye", "forfeit", "draw". Those are different facts, and collapsing them means no consumer can ever tell them apart again. Option A keeps `{}` ("decisive, but a pod") distinct from `null` ("no decisive result here at all") — a distinction phase 5's detail page plausibly wants and this phase must not destroy on its behalf.
2. **Consistency with the module's established shape.** Every other export here is a small named authority with one job (`outcomeLabelKey`, `isReportable`, `arityLabel`, `defaultScoringForArity`). `decisiveGameWins` is the **third** exhaustive walk over `PairingOutcome`, joining its two siblings in one file, so §4.1's compile-enforcement claim gets *stronger* (a fifth wire arm now breaks the build in three places, measured at P11c) rather than being diluted into a general-purpose function. It passes the same two-consumer test `isReportable` passed: `PairingsList` now, phase 5's detail page next (it renders a single pairing's game wins and cannot add this helper — `tournamentPageState.ts` is phase 4's file), and `ReportResultDialog`'s pre-fill after that.
3. **Zero ripple onto rows two review rounds already confirmed.** Option B changes `gameWinsEntries`'s parameter type, which forces V7's and V8's hostile fixtures — the `["12","7"]` integer-key case built specifically around P10, and the unattributable-key filter — to be re-expressed as full `{Reported:{Decisive:{winner, game_wins}}}` literals. That buries each row's discriminating property under wire-shape ceremony for no gain. Under Option A, V7 and V8 are untouched: `gameWinsEntries`'s parameter is only *widened* from `Record<string, number>` to `Readonly<Record<string, number>>` (rule 6), which every existing fixture already satisfies — measured clean at P11.

**Why not B, stated as its own claim rather than as A's shadow.** B's single advantage is that it holds the export count at 9. That count is a *convention* this plan states explicitly (§4.2), not a budget it is spending against, and trading a real layering property for a stable integer is the wrong trade. B also makes the surviving function's name a lie — `gameWinsEntries(outcome, seats)` reads as "the game-win entries of an outcome", but for three of five inputs the honest answer is "this outcome has no such concept", which an empty array states falsely rather than declining to answer.

**Precedent for a boolean-returning predicate, so this does not read as a violation of §4.5's "typed unions, never booleans."** That rule governs *data modelling* — a field or return that must distinguish cases carries a typed enum, never a bare flag (which is why `viewerRoles` returns `ReadonlySet<TournamentRole>` rather than `isOrganizer: boolean`). `isReportable` is not a case distinction; it is a **predicate**, the direct analogue of the broker's own `meta.status.is_terminal()` guard, called earlier in the very same function it mirrors (`tournament.rs:1730`, inside `report_result` which opens at `:1721`). *(Reviewer's m4: revisions 1–2 said "four lines above"; `:1730` is in fact eleven lines above the `:1741` refusal block. The citation was right, the distance claim was not — so the distance claim is dropped rather than re-derived, here and in §5.2's doc comment, which ships verbatim into source.)* A richer `{ reportable } | { notReportable, reason }` return was considered and **rejected**: no consumer in this phase renders a reason, no catalog key exists for one (§5.1 rule 2 expects a zero catalog delta), and minting an unconsumed axis is speculative generality. If phase 5 wants explanatory copy it can widen the return then, under the full S4 contract — that deferral is recorded in §6.

**Deliberate deviations from `/add-frontend-component` Phase 7, both precedent-backed:**
1. **No `gameStateFactory`/`gameObjectFactory`/`waitingForFactory`.** Those construct `GameState`/`GameObject`/`WaitingFor` — engine-session types with zero overlap with the tournament wire surface. The skill's underlying rule ("don't hand-roll literals that drift from the serde contract") is honoured a different way: fixtures are declared with an **explicit type annotation** (`const view: TournamentView = {…}`), so a wire-shape change is a compile error in every fixture. This is precisely `GameListItem.test.tsx:8`'s `const baseGame: LobbyGame = {…}`.
2. **No `setGameStoreForTest` seeding.** These components subscribe to no store. That is the phase's defining property, and V28 pins it.

### 4.4 Logic Placement

The governing rule is CLAUDE.md's *"The frontend is a display layer, not a logic layer… Formatting for display is acceptable; calculating, filtering, or inferring game state is not."* Each piece is placed and justified:

| Piece | Placement | Justification |
|---|---|---|
| Standings **order and rank** | **broker only** — rendered in array order, index+1 as the rank | `standings()` emits pre-ranked rows (C8). Re-sorting would be a second ranking authority. §2.4's counter-example is what this row exists to prevent. |
| Tiebreak **values** | **broker only** — rendered, never recomputed | `opponents_average`, `game_win_pct`, `match_win_pct` and the `tiebreak_floor` all live in `tournament.rs`. The draft table's `computeGwp` with its hand-rolled `1/3` floor is the failure mode. |
| Tiebreak **value → display string** | client, `formatTiebreakValue` | Pure display formatting of a server number. Explicitly permitted. |
| **Which** tiebreak columns exist | client, `tiebreakCells` | A projection of the `Tiebreaks` union the broker chose — reading the arm, not deciding it. |
| Outcome → **label key + winner name** | client, `outcomeLabelKey` | Choosing a translation key from a closed union, plus a `player_key → display_name` join across two arrays the **same frame** carried. A join is a lookup, not a derivation. |
| **Whether a pairing has a `game_wins` tally at all** | client, `decisiveGameWins` (U1) | A projection of the `PairingOutcome` union the broker chose — reading the arm, not deciding it, exactly as `tiebreakCells` does one row above. It exists so no component narrows the wire union in its own body (§5.1 rule 8); the alternative, inline `outcome.Reported.Decisive.game_wins`, is both the banned shape and a compile error (P11b). `null` (no decisive result) and `{}` (decisive, but a pod — single-game per MSTR) are deliberately kept distinct. |
| `game_wins` **display order** | **broker's seat order** — iterate `pairing.players`, index into `game_wins` | Not merely stylistic: `player_key` is client-supplied and opaque (`protocol.rs:699-702`), so an all-digit key reorders `Object.keys` (P10). Seat order is the only stable authority. `gameWinsEntries` owns this join and nothing else; `decisiveGameWins` feeds it. |
| **Which pairing is mine** | client, `myPairing` | Selection over server-provided arrays by a key the store already holds. No game state inferred. |
| **Whether I am the organizer** | client, `viewerRoles` — **from the store's credential map only** | Phase 2 made `runGatedTournamentRpc` the single authority for *acting*. `viewerRoles` is the single authority for *displaying*, reading the same map. It never re-derives authority from a `TournamentView`. |
| **Arity/bracket legality** | **broker only** | `SingleElimination` + arity ≠ 2 is refused at `tournament.rs:1514-1523`. The form must not pre-reject (V19). |
| **Bo3 tally legality** | **broker only** | `validate_match_result` owns `(2,0)|(2,1)|(0,2)|(1,2)` and the winner↔tally consistency check. The dialog submits what was entered (V25). |
| **Whether `game_wins` is expressible at all** | client, from `pairing.players.length` | Not a legality judgment — the *wire contract* (F1). At ≥3 seats the broker rejects any non-empty map unconditionally, so rendering inputs there would build a request that can never succeed. Honouring a total contract ≠ duplicating a conditional rule. |
| **Whether a pairing may be reported at all** | client, `isReportable` (U1) | F4. `report_result` refuses `Bye`/`Forfeit` unconditionally before validation ever runs (`tournament.rs:1741-1753`) — the same total-contract posture as the row above, applied one layer out at the affordance rather than the dialog's inputs. `Reported` stays reportable (re-reporting is legal), so the guard is arm-selective, never "unresolved only." |
| Scoring **prefill** | client, `defaultScoringForArity`, cited + tested | F2. The wire mandates a value and offers no defaulting path. Editable by the user, validated by the broker. Residual risk disclosed in §7.3. |
| `created_at` → date string | client, `toLocaleDateString(i18n.language)` | Display formatting. Uses the **app** language, not the browser's — the `i18n` handle from `useTranslation()`, no extra import. |
| Mounting, routing, subscribing, store calls, error copy | **`DEFERRED(phase 5)`** | Charter deferral list. |

### 4.5 Rust Idioms — N/A; the TypeScript equivalents, applied

No Rust changes. The transferable principles from CLAUDE.md are honoured in their TS forms:

- **Typed unions, never booleans.** `OutcomeLabel` and `ArityLabel` are discriminated unions, not `{key: string, vars?: object}`; `TiebreakCell.format` is `"percent" | "points"`, not `isPercent: boolean`; `viewerRoles` returns `ReadonlySet<TournamentRole>` reusing phase 2's union, not `{isOrganizer: boolean, isPlayer: boolean}` — which would also mis-model the both-at-once case phase 2 documented as normal.
- **Exhaustive discrimination, no `default`, no wildcard.** Every union walk terminates in `const unreachable: never = value; return unreachable;`. Per R3, this is the form that is *genuinely* compile-time exhaustive; the `let x: T | undefined` + `switch` shape is not, and is banned in this phase.
- **`??` never `||`.** A tiebreak value of `0` is legitimate (a player with no opponents yet). `cell?.value || "—"` would render `0.0%` as `—`. Pinned by V6.
- **Existing type reuse over new types.** `TournamentRole`, `TournamentCredential`, `CreateTournamentRequest`, `ScoringPolicy`, `PodOutcome` are all imported, never re-declared.
- **`readonly` on every array/set prop and return.** These components mutate nothing they are handed.
- **`import type` exclusively at the store boundary.** `verbatimModuleSyntax: true` makes erasure a compiler guarantee; P7/P7b measured what a value import would cost (925ms + the localStorage hazard).

### 4.6 Nom Compliance — N/A

Mandatory only if a file under `crates/engine/src/parser/` changes. **No file under `crates/` changes in this phase.** No text is parsed; the closest thing to "dispatch" is discrimination over closed TypeScript unions, which is done with `in` narrowing and literal comparison plus a `never` terminal — the TS analogue of an exhaustive `match`, not of `contains()`/`starts_with()`.

### 4.7 Extension vs Creation

**Extension in every case but one.**

- `tournamentPageState.ts` **extends** the `pages/*PageState.ts` pattern (`multiplayerPageState.ts`), same directory, same naming, same "typed unions + pure functions + colocated `__tests__` unit test, no render, no store" shape.
- All five components **extend** the `components/<feature>/` dumb-component pattern (`components/lobby/`, `components/multiplayer/`), with `useTranslation(<source-directory namespace>)` and props-only inputs.
- `ReportResultDialog` **extends** `ConcedeDialog`'s `FocusScope` + `AnimatePresence` + `aria-modal` + `useId()` composition. **The extension is that composition, not the `role` value** — `ReportResultDialog` uses `role="dialog"`, a deliberate WAI-ARIA deviation from `ConcedeDialog`'s `role="alertdialog"` argued in full at §5.7 and not to be "corrected" back.

**The one creation: the `client/src/components/tournament/` directory.** Justified and mandated — the charter's scope paths name it, and the skill's own namespace rule ("namespace = source directory") makes a `tournament/` directory the thing that makes `useTranslation("tournament")` correct rather than arbitrary. It sits beside `lobby/`, `multiplayer/` and `draft/`, which are the same kind of feature grouping.

**Why the pure module is a separate `.ts` file rather than helpers colocated in the components — measured, not stylistic.** P4b: exporting a plain function alongside a component from a `.tsx` produces `react-refresh/only-export-components` — *"Use a new file to share constants or functions between components."* The lint rule the repo already runs independently prescribes exactly the charter's split. That is the strongest possible form of "extend, don't invent."

### 4.8 Analogous Trace

**Traced feature:** the multiplayer lobby list surface.
**Full path:** `crates/lobby-broker/src/protocol.rs` → `client/src/adapter/types.ts` → `client/src/services/brokerClient.ts` → `client/src/stores/multiplayerStore.ts` → `client/src/pages/multiplayerPageState.ts` → `client/src/pages/__tests__/multiplayerPageState.test.ts` → `client/src/pages/MultiplayerPage.tsx` → `client/src/components/lobby/LobbyView.tsx` → `client/src/components/lobby/GameListItem.tsx` → `client/src/components/lobby/__tests__/GameListItem.test.tsx`.
**Secondary traces:** `client/src/components/multiplayer/ConcedeDialog.tsx` → `client/src/components/ui/FocusScope.tsx` (dialog composition); `client/src/components/draft/StandingsTable.tsx` → `client/src/components/draft/__tests__/StandingsTable.test.tsx` (**counter-example**, §2.4).

### 4.9 Variant Discoverability — N/A

No engine enum variant is added. `cargo engine-inventory` and the `/add-engine-variant` gate govern `QuantityRef`/`FilterProp`/`Effect`/`Keyword`/etc. in `crates/engine`; this phase adds only TypeScript view-model types local to one client module (`OutcomeLabel`, `ArityLabel`, `TiebreakCell`, `GameWinEntry`), each a projection of an already-frozen wire union rather than a new engine surface. `cargo engine-inventory` is deliberately **not** run — it would take the cargo target lock for zero information (S9).

### 4.10 CR annotations — N/A, gate checked explicitly

CLAUDE.md requires the CR gate be *checked*, not assumed, on every change. Checked, and **N/A**, for three independent reasons:

1. **No Rust changes.** The annotation requirement is scoped to code that implements or enforces an MTG rule; the whole diff is TypeScript/TSX under `client/src/`.
2. **No game logic.** These components render tournament administration data — pairings, standings, match points. Nothing touches the stack, priority, layers, state-based actions, or any object the CR governs.
3. **The rules involved are not the CR at all.** The tournament logic these views present is governed by the **MTR** and **MSTR** (Wizards' *Magic Tournament Rules* and its *Multiplayer Addendum*), which the broker itself distinguishes explicitly: `crates/lobby-broker/src/tournament.rs:36` — *"tiebreakers, byes, drops, retention) is **not CR-governed game logic**."* Writing a `CR ###` annotation here would be exactly the fabricated-citation failure the CLAUDE.md gate exists to prevent.

**Executor instruction:** add **zero** `CR ` annotations. Verify with a diff-wide `grep -c "CR [0-9]\{3\}"` returning `0`, and report that count — the same evidence phases 1–3 produced (entries 14, 22, 28). Do **not** run `./scripts/fetch-comp-rules.sh`; `docs/MagicCompRules.txt` is not needed.

### 4.11 Identity / Provenance Contract

Every binding where "this player", "that pairing", "the winner", "mine" or a chosen value appears:

| Binding | Source phrase / wire concept | Authority + id | Binding time | Live vs latched | Storage | Consumer | Invalidation | Hostile fixture |
|---|---|---|---|---|---|---|---|---|
| **B1 — "the winner"** in `Forfeit`/`Decisive` | `PairingOutcome::Forfeit{winner}` / `PodOutcome::Decisive{winner}` — a **`player_key`**, not a display name | the pairing's own `players: PlayerSummary[]` (`TournamentPairingView`, `types.ts:4645-4650`) | at render, per frame | **live** — re-resolved from the current `view` on every render; nothing latched | none (derived) | `outcomeLabelKey` | naturally, when a new `TournamentUpdate` replaces the view | a `Forfeit.winner` **not present** in `seats` must render the raw key, never blank/`undefined` (V3) |
| **B2 — "my pairing"** | the entrant identity this browser joined under | `TournamentCredential.playerKey` (`multiplayerStore.ts:961-967`), **stored beside the token precisely so "which entrant am I in THIS event" survives an ambient-id change** | phase 5 supplies it as a prop; phase 4 takes it as an argument | live | store (persisted, phase 2) | `myPairing` | credential dropped on `TournamentRemoved` (`multiplayerStore.ts:293`) | pairings exist only for **earlier** rounds → `null`, never the stale earlier pairing (V9) |
| **B3 — "the current round"** | `TournamentSummary.current_round` | broker (`tournament.rs`, `current_round: 0` at creation) | at render | live | none | `myPairing` | — | `current_round === 0` (Registration) → `null` (V10) |
| **B4 — "I am the organizer"** | holding the organizer bearer token for **this** code | `tournamentCredentials[code].organizerToken` — the *same map* `runGatedTournamentRpc` reads (`:478-487`), so display and action can never disagree | at render | live | store (persisted) | `viewerRoles` | `forgetTournamentCredential` on `TournamentRemoved` | credentials for tournament **A** while viewing **B** → empty role set (V11; the rendered-UI half is `DEFERRED(phase 5)`) |
| **B5 — "both authorities at once"** | an organizer who also joined their own event | both tokens under one code — phase 2 documents this as the **normal** path (`CreateTournament` does **not** auto-join the creator) | at render | live | store | `viewerRoles` | — | both tokens → `Set{"organizer","player"}`, size 2 — the case a `boolean` return could not express (V11) |
| **B6 — "this tiebreak number belongs under this header"** | the `Tiebreaks` arm that produced the row | **the row's own arm**, never the table's | at render, per row | live | none | `tiebreakCells` → `TiebreakStanding` join by **scheme-qualified `id`** | — | a `Multiplayer` row under a `HeadToHead` header renders three explicit `—`, never three plausible-looking misaligned numbers (V5). Note C8: the broker emits homogeneous arms, so this is a type-level possibility the wire permits and the design must not silently mishandle. |
| **B7 — "this game-win count belongs to this seat"** | `Decisive.game_wins: Record<player_key, u8>`, reached **only** through `decisiveGameWins` (never by inline narrowing — §5.1 rule 8) | the pairing's `players` array **order**, indexed into `game_wins` | at render | live | none | `decisiveGameWins` → `gameWinsEntries` | naturally, when a new `TournamentUpdate` replaces the view | all-digit `player_key`s must still render in seat order (V7 — `Object.keys` would reorder them, P10); a `game_wins` key matching **no** seat must not render (V8); a `Bye`, a `Forfeit` and a `{Reported:"Draw"}` pairing each yield **`null`**, not an empty tally, so "no result" is never rendered as "0–0" (V31), and none of them renders a game-wins line (V32) |
| **B8 — "the scoring policy this tournament will use"** | `CreateTournament.scoring`, wire-mandatory (F2) | the **organizer's** entry; prefilled once per arity from `defaultScoringForArity` | prefill at arity change; **latched** the moment any scoring field is edited (`scoringTouched`) | latched-on-touch by design — an organizer's explicit 4/1/0 must survive an arity change | component-local `useState` | `CreateTournamentForm` | unmount | edit `win` → change arity → the edited value **survives** (V20b); untouched → arity 2→4 re-prefills 3→**7** (V20a) |
| **B9 — "this pairing may be reported"** (F4, NEW at revision 2) | `report_result`'s unconditional refusal of `Bye`/`Forfeit` (`tournament.rs:1741-1753`), before `validate_match_result` ever runs | **the pairing's own `outcome` arm**, never `onReport`'s mere presence | at render, per pairing | live — re-resolved from the current `view`; nothing latched | none (derived) | `isReportable` → `PairingsList`'s report affordance (this phase) and phase 5's detail-page equivalent | naturally, when a new `TournamentUpdate` replaces the view | a `Bye` pairing and a `Forfeit` pairing, both with `onReport` supplied, must render **no** action; a pending (`outcome: null`) pairing and a `Reported` pairing, in the **same render**, must render it (V29 unit-level, V30 component-level) — the `Reported` case is what forecloses a resolution-based ("unresolved only") guard rather than an arm-selective one |

### 4.12 Verification Matrix

Every row names its changed seam, its production entry point, its test, its revert-failing assertion, and — for every negative — its **paired positive reach-guard**.

| # | Claim | Seam / entry point | Test | Revert-failing assertion | Paired positive reach-guard / hostile sibling |
|---|---|---|---|---|---|
| V1 | `outcomeLabelKey` maps all 4 outcome shapes to the right key + vars | `tournamentPageState.outcomeLabelKey` | `tournamentPageState.test.ts` | swap the `Bye`/`Draw` keys → red | asserts the **exact object** per shape (`{key:"outcome.forfeit", winner:"Ann"}`), not merely "truthy" |
| V2 | That mapping is **compile-time** exhaustive | the `const unreachable: never` terminals | type-level | delete the `Draw` branch → `TS2322: Type '"Draw"' is not assignable to type 'never'` | run `tsc` **before** the deletion and confirm exit 0, so the error is attributable |
| V3 | An unresolvable winner key renders the raw key, never blank | `displayNameFor` fallback | `tournamentPageState.test.ts` | `?? ""` instead of `?? playerKey` → red | same fixture with a **resolvable** key returns the display name — so the test cannot pass by always returning the key |
| V4 | `tiebreakCells` covers both arms with the right catalog keys | `tiebreakCells` | `tournamentPageState.test.ts` | point a `Multiplayer` cell at a `headToHead.*` key → red | asserts each `labelKey`/`titleKey` **resolves** via `i18n.exists`, so a typo'd key that "looks right" fails (C5's casing trap is exactly this) |
| V5 | Cell ids are scheme-qualified, so a foreign-arm row cannot render under the wrong header | `TiebreakCell.id` + the table's `Map` join | `TournamentStandingsTable.test.tsx` | drop the `headToHead.`/`multiplayer.` prefix → the mixed fixture renders a number under `OMW%` instead of `—` → red | **hostile fixture:** row 0 `HeadToHead`, row 1 `Multiplayer`; row 1's three tiebreak cells must all read `—`. Positive control: an all-`HeadToHead` fixture renders three real numbers, proving the cells render at all |
| V6 | `formatTiebreakValue` distinguishes percent from points, and `0` is a value not an absence | `formatTiebreakValue` + `?? "—"` | both | `\|\|` for `??` → a `0.0` OMW% renders `—` → red | a genuinely **absent** cell in the same test still renders `—`, so the row proves the distinction rather than just the presence |
| V7 | `game_wins` renders in **seat** order | `gameWinsEntries` | `tournamentPageState.test.ts` | iterate `Object.keys(gameWins)` → red | **hostile fixture:** seats `["12","7"]` with matching `game_wins`; expected order `["12","7"]`, which is the exact inverse of `Object.keys` (P10). Sibling: non-digit keys `["bob","alice"]` pass under both implementations — included so the digit case is visibly the discriminator |
| V8 | A `game_wins` key matching no seat is dropped | `gameWinsEntries` filter | `tournamentPageState.test.ts` | drop the filter → a 3rd entry appears → red | the same fixture's two **attributable** keys still render — so "drops everything" cannot pass |
| V9 | `myPairing` returns the **current** round's pairing | `myPairing` | `tournamentPageState.test.ts` | remove the `p.round === current_round` conjunct → returns the round-1 pairing → red | a fixture where the current round **does** contain me returns that pairing — so "always null" cannot pass |
| V10 | `myPairing` is `null` for a spectator and during Registration | same | same | `playerKey === undefined` unguarded → throws or matches wrongly | paired with V9's positive |
| V11 | `viewerRoles` expresses none / one / **both** authorities | `viewerRoles` | `tournamentPageState.test.ts` | return a `boolean` → cannot express B5 | `{organizerToken, playerToken}` → size 2; `{}` → size 0; each single token → the right single member |
| V12 | `defaultScoringForArity` mirrors `2n-1 / 1 / 0` | `defaultScoringForArity` | `tournamentPageState.test.ts` | hardcode 3/1/0 → arity-4 case red | arity 2→`{3,1,0}`, 4→`{7,1,0}`, 128→`{255,1,0}` (the `u8` boundary `MatchArity::new` caps at) |
| V13 | `arityLabel` picks head-to-head vs pod and carries `{{seats}}` | `arityLabel` | `tournamentPageState.test.ts` | invert the comparison → red | 2→`{key:"arity.headToHead"}`; 4→`{key:"arity.pod", seats:4}`; 3→`{key:"arity.pod", seats:3}` |
| V14 | Standings render in **server** order, never re-sorted or re-ranked | `TournamentStandingsTable` body | `TournamentStandingsTable.test.tsx` | add `[...standings].sort(…)` (i.e. copy §2.4's counter-example) → red | **hostile fixture:** `match_points` deliberately non-monotonic in array order (`[3, 9, 6]`); assert DOM row order === array order **and** that rank badges read 1,2,3 in that same order |
| V15 | Dropped entrants stay **listed and marked**, not filtered | same | same | add a `.filter(r => !r.dropped)` → red | fixture with one dropped row: assert the row is present **and** carries the `labels.dropped` copy — presence alone would pass with the marker missing |
| V16 | One code path renders every arity | `PairingsList` | `PairingsList.test.tsx` | add any `if (arity === 2)` branch → one `it.each` case red | `it.each` over **1 seat (bye) × 2 (head-to-head) × 3 (short pod) × 4 (full pod)** × all 4 outcome shapes = 16 cases, each asserting every seat's display name renders and the right outcome copy appears |
| V17 | A pending pairing (`outcome: null`) renders `pairings.pending` | same | same | treat `null` as `"Bye"` → red | the same fixture with a resolved outcome renders the outcome copy instead — so "always pending" cannot pass |
| V18 | The entrant count is `summary.player_count` (**active**), and `players.length` is unreachable | `TournamentListItem` props | `TournamentListItem.test.tsx` | widen the prop to `TournamentView` and read `players.length` → red | **hostile fixture** (the charter's probed payload): `player_count: 1` while a sibling `TournamentView` in the same test has `players.length === 2`; assert `"1 entrant"` renders and `"2 entrants"` does **not**. Structural half: the prop type is `TournamentSummary`, which has no `players` — the error is unrepresentable, and V18 pins the runtime half |
| V19 | The form does **not** client-side pre-reject an illegal bracket/arity combination | `CreateTournamentForm` submit | `CreateTournamentForm.test.tsx` | add a client-side guard → red | **positive reach-guard (charter-mandated):** assert `onSubmit` fired **with** `{bracket:"SingleElimination", arity:4}` — a form that never submitted anything cannot satisfy this |
| V20a | Untouched scoring re-prefills when arity changes | `scoringTouched` = false path | same | drop the re-prefill → win stays 3 at arity 4 → red | assert the **specific** value 7, not merely "changed" |
| V20b | Edited scoring survives an arity change | `scoringTouched` = true path | same | drop the flag → the organizer's 4 is overwritten by 7 → red | V20a is V20b's paired opposite; both must be present or one implementation satisfies the other vacuously |
| V21 | "Automatic" rounds submits `totalRounds: null` | same | same | submit `0` → red (and the broker rejects `Some(0)`, `tournament.rs:1524`) | an explicit round count submits that number — so "always null" cannot pass |
| V22 | Game-wins inputs appear **iff `pairing.players.length === 2`** | `ReportResultDialog` | `ReportResultDialog.test.tsx` | change the gate to `arity === 2` → **red on the hostile fixture** | **hostile fixture (F1):** a 2-seat short pod in an **arity-3** tournament must **still** show game-wins inputs. Paired sibling: a 3-seat pod shows **none**. The dialog takes no `arity` prop, so the wrong authority is also structurally unavailable |
| V23 | ≥3 seats submits `Decisive{winner, game_wins:{}}` | same | same | emit a non-empty map → the broker rejects (`tournament.rs:1011-1016`); test asserts `{}` → red | assert the **exact** payload object, and that `winner` is the selected seat's `player_key` (not its display name) |
| V24 | Draw submits the bare string `"Draw"` | same | same | emit `{Draw:{}}` → red | asserts `onSubmit` called with the primitive `"Draw"`, pinning the externally-tagged unit-variant encoding |
| V25 | No client-side pre-rejection of an inconsistent Bo3 tally | same | same | add a consistency guard → red | assert `onSubmit` fires with `winner: A` while `game_wins` is `{A:0, B:2}` — the broker's `expected` check (`tournament.rs:1006-1009`) is the sole authority. Mirrors V19's posture exactly |
| **V26** | **Discharges phase 3's `DEFERRED(phase 4)` — `t()` routing.** Every user-visible string in all five components resolves through the `tournament` (or `common`) namespace; no raw English literal and no unresolved key survives | all five components | one shared assertion helper used by all five component test files | inline a raw English literal, **or** reference a nonexistent key → red | Restated per **F3**: assert no rendered text node matches `/^[a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+$/` (a bare dotted key path — measured to be what a missing key produces, P2). **Paired positive reach-guard (charter-mandated):** in the same render, assert at least one **known catalog value** is present (e.g. `"Standings"`, `"Pairings"`, `"Report Result"`) — so a component that rendered nothing cannot satisfy the negative vacuously. **Scope note:** this row discharges the **`t()`-routing half only**; key-set completeness across mounted pages remains `DEFERRED(phase 5)` |
| V27 | The tree compiles, lints and the protocol pin has not moved | whole diff | `pnpm run type-check` (chains `protocol:check`), `pnpm run lint` | any TS error / new lint **error** | `check-protocol-version.mjs` exit 0 (S8); lint must show **0 errors** and no new warning in a touched file (baseline: 44 pre-existing warnings, none in these files) |
| V28 | `tournamentPageState.ts` imports **no store runtime** | the store import line | `tournamentPageState.test.ts`, static source assertion | change `import type {…} from "…multiplayerStore"` to a value import → red | House convention (`adapter/__tests__/boundary-guardrails.test.ts`): regex-scoped `expect(source)`. Assert every `from ".*multiplayerStore"` import statement begins `import type`. **Positive control:** a fixture string containing a value import **must** match the offending pattern, so a regex that matches nothing cannot pass. Grounded in P7/P7b (14ms vs 925ms + the `--localstorage-file` hazard) |
| **V29** | **(NEW, F4)** `isReportable` is **arm-selective** and exhaustive: `null` → `true`, `"Bye"` → `false`, `{Forfeit}` → `false`, `{Reported:{Decisive}}` → `true`, `{Reported:"Draw"}` → `true` | `tournamentPageState.isReportable` | `tournamentPageState.test.ts` **+ type-level** | **Runtime:** return `true` for `"Bye"` or for `{Forfeit}` → red; **narrow to "unresolved only"** (`outcome === null`) → the two `Reported` cases red. **Compile-time:** delete the `"Forfeit" in outcome` branch → `TS2322: … not assignable to type 'never'` at the `unreachable` binding (run `tsc` clean *before* the deletion so the error is attributable, exactly as V2 requires) | Asserts all **five** inputs in one table-driven `it.each`, so neither "always `false`" nor "always `true`" can pass, and the `Reported` pair is what makes the guard demonstrably arm-selective rather than resolution-based. The doc comment's claim that re-reporting is legal is pinned by the two `true` expectations, and is traceable to `tournament.rs:1752`'s `Some(PairingOutcome::Reported(_)) \| None => {}` |
| **V30** | **(NEW, F4 — the component-level half)** `PairingsList` renders the report affordance **iff `onReport` is supplied AND the outcome arm is reportable** | `PairingsList`'s report action | `PairingsList.test.tsx` | drop the `isReportable` conjunct (render on `onReport`'s presence alone) → **red on the hostile half**; narrow the guard to `outcome === null` → **red on the positive half** | **Hostile fixture:** one **bye** pairing and one **forfeited** pairing, `onReport` supplied for both — assert `queryAllByRole("button", { name: t("detail.reportResult") })` finds **zero** actions on those two rows. **Paired positive reach-guard, in the SAME render:** a **pending (`outcome: null`)** pairing and an already-**`Reported`** pairing each **do** render the action, and clicking one calls `onReport` with **that exact pairing object** — so "never renders the action" cannot pass vacuously, and the `Reported` row specifically forecloses a resolution-based guard. **Third control:** the same four-pairing fixture with `onReport` **omitted** renders zero actions anywhere, pinning that the prop is still required |
| **V31** | **(NEW, revision 3 — round 2's M2)** `decisiveGameWins` is exhaustive and returns `null` for every arm that has no tally: `null` → `null`, `"Bye"` → `null`, `{Forfeit}` → `null`, `{Reported:"Draw"}` → `null`, `{Reported:{Decisive:{game_wins}}}` → **that exact record** (including a legitimately **empty** one at ≥3 seats) | `tournamentPageState.decisiveGameWins` | `tournamentPageState.test.ts` **+ type-level** | **Runtime:** return `{}` instead of `null` for `"Bye"`/`{Forfeit}`/`Draw` → red (the three `null` cases assert `toBeNull()`, not `toEqual({})`, so the two are distinguishable). **Compile-time:** delete the `"Forfeit" in outcome` branch → `TS2322: Type '{ Forfeit: { winner: string; }; }' is not assignable to type 'never'`; delete the inner `reported === "Draw"` branch → `TS2322: Type '"Draw"' is not assignable to type 'never'` **plus** a second error at the `"Decisive" in reported` narrowing. Both measured verbatim at **P11c**; run `tsc` clean *before* each deletion so the error is attributable, exactly as V2 and V29 require | Asserts all **five** inputs in one table-driven `it.each`, so neither "always `null`" nor "always the record" can pass. **Hostile sibling, and the row's real point:** a **6th** case — `{Reported:{Decisive:{winner:"a", game_wins:{}}}}` from a 4-seat pod — must return **`{}`**, *not* `null`, in the same `it.each`. That pins `{}` ≠ `null` as different facts (§4.4), which is exactly what the rejected Option B could not express |
| **V32** | **(NEW, revision 3 — the component-level half of M2)** `PairingsList` renders game-wins lines **only** on the `Decisive` arm, and reaches them **only** through `decisiveGameWins` | `PairingsList`'s game-wins block | `PairingsList.test.tsx` | Restore revision 2's inline `outcome.Reported.Decisive.game_wins` → **`type-check` red** (P11b's two errors), before any test runs; render game-wins lines unconditionally → red on the hostile half | **Hostile fixture, one render, four pairings:** a `Bye`, a `Forfeit`, a `{Reported:"Draw"}` and a 3-seat `Decisive` pod each render **zero** `outcome.gameWins` lines. **Paired positive reach-guard, in the SAME render:** a 2-seat `Decisive` pairing renders **exactly two** lines, in **seat** order, one per seat — so "never renders game wins" cannot pass vacuously. Note the pod row is the subtle one: it is `Decisive` *and* renders nothing, because its record is empty — with **no arity check anywhere in the component** (V16's invariant) |

**Coverage-status impact:** none. This phase changes no Rust, no card data, and no `Effect::Unimplemented`/strict-failure surface. `cargo coverage` is neither run nor affected. No Oracle text is accepted-with-deferred-semantics, because no Oracle text is parsed.

**Revert-checks to run before committing** (each must break its named row; run the *positive* direction first so a green-both-ways implementation is impossible):

| # | Mutation | Must break |
|---|---|---|
| RC1 | Delete `outcomeLabelKey`'s `Draw` branch | V2 (`tsc`, **not** vitest) |
| RC2 | Add `[...standings].sort((a,b) => b.match_points - a.match_points)` to the table | V14 |
| RC3 | Change `ReportResultDialog`'s game-wins gate from `pairing.players.length === 2` to the **tournament arity**. **Executor note (m3): this mutation is not executable against the shipped prop shape, by design — §5.7 deliberately removes `arity` from `ReportResultDialogProps` so the wrong authority is unrepresentable.** To run it, *temporarily* re-add `arity: MatchArity` to the props interface, pass `3` from the V22 hostile fixture, and gate on `arity === 2`. This is a **mutation-test scaffold only** — restore both the prop removal and the gate immediately afterwards. It is **not** a design change and must not survive into the diff; §5.14's final `git diff --stat` (12 files, or 13 with the optional shared test helper) and V22's structural half both catch it if it does | V22 |
| RC4 | Iterate `Object.keys(gameWins)` in `gameWinsEntries` | V7 |
| RC5 | Replace `?? "—"` with `\|\| "—"` | V6 |
| RC6 | Drop the scheme prefix from `TiebreakCell.id` | V5 |
| RC7 | Inline one raw English literal in one component | V26 |
| RC8 | Change the store import to a value import | V28 (and observe the `--localstorage-file` warning appear — a second, independent signal) |
| RC9 | Add a `if (bracket === "SingleElimination" && arity !== 2) return;` guard to the form | V19 |
| **RC10** | **(NEW, F4)** Drop the `isReportable` conjunct from `PairingsList` — render the action whenever `onReport` is supplied | **V30's hostile half** (the bye row and the forfeit row each grow a report action) |
| **RC11** | **(NEW, F4)** Narrow `isReportable` to "unresolved only" — `return outcome === null;` | **V30's positive half** (the `Reported` row loses its action) **and V29** (both `Reported` cases). This is the arm-selectivity check: RC10 and RC11 fail in **opposite directions**, so no single implementation can be green under both, which is what proves the guard is arm-shaped rather than either always-on or resolution-based |
| **RC12** | **(NEW, revision 3)** Make `decisiveGameWins` return `{}` instead of `null` for the `{Reported:"Draw"}` arm | **V31's `Draw` case** (`toBeNull()` fails against `{}`). Paired with V31's 6th case — a 4-seat pod's `Decisive` arm, which must stay **`{}`** and must *not* become `null` — this is the `{}`-vs-`null` distinction check: RC12 and that case pull in **opposite** directions, so an implementation that collapses "no decisive result" into "decisive with an empty tally" (the rejected Option B's semantics, §4.3) cannot be green under both |

> **Executor environment fact, carried forward from entry 12 and re-measured this session (P3/P3b):** RC1's failure — and V29's and V31's compile-time halves — surface under **`type-check`**, never under `vitest` — vitest's esbuild transform strips types without checking them. Run `pnpm run type-check` for those, not the test suite.

---

## §5 — Step-by-step implementation

### 5.0 Environment (once)

`client/node_modules` is **present** in this worktree (measured — unlike the state S9 recorded at charter time). Run `pnpm install --frozen-lockfile` in `client/` **only** if a module-resolution error appears. Tilt does not watch this worktree (re-measured); `./scripts/tilt-wait.sh` here returns exit **3 = cannot answer**, which must never be reported as a build failure. **Take no cargo target lock at any point** — this phase touches no Rust.

### 5.1 Authoring rules the executor must hold throughout

1. **Every frontend-authored string goes through `t()`** in `useTranslation("tournament")`, or `t("common:…")` for shared chrome. No raw English in JSX. Engine/broker pass-through — tournament `name`, `code`, `display_name`, `player_key`, numeric values — stays **raw**.
2. **Expected catalog delta: ZERO keys.** I enumerated every string the five components need against the 111-key catalog and found **no gap**: `page.*`/`labels.*`/`status.*`/`bracket.*`/`arity.*`/`list.*` cover `TournamentListItem`; `create.*` covers the form (including the four scoring labels — which is itself evidence phase 3 anticipated an explicit scoring editor, cf. F2); `standings.*` incl. both `tiebreaks.*` sub-trees cover the table; `pairings.*` + `outcome.*` + `detail.reportResult` (present at `en/tournament.json:79`, re-confirmed at revision 2) cover the list; `report.*` + `common:actions.cancel`/`closeNamed` cover the dialog. **F4's guard authors no copy** — a non-reportable pairing simply renders no action — so the zero-delta expectation survives revision 2 unchanged. **Therefore `localeParity.test.ts` is expected to be left UNTOUCHED and no `tournament.json` is expected to change.**
3. **If — and only if — a genuine gap appears**, the **full three-part S4 contract** applies *in the same commit*: (a) the key in **all 7** `tournament.json` files, English included (P8: an English-only key = 12 failures); (b) identical `{{placeholder}}` sets in every locale (`KNOWN_PLACEHOLDER_GAPS` is **off-limits** — `localeParity.test.ts:303` fails on an unnecessary entry); (c) if count-bearing, **all four** `_one`/`_few`/`_many`/`_other` suffixes in all 7 catalogs **plus** `{ ns: "tournament.json", stem: "<stem>" }` appended to `FOUR_FORM_STEMS` (`:146-164`). **Ignore `/add-frontend-component`'s "do not edit es/fr/de/it/pt" bullet — it is stale (§0.4 R1).**
4. **Exhaustive union walks end in `const unreachable: never = value; return unreachable;`.** Never a `default:`, never a wildcard, and never a `let x: T | undefined` declared before a `switch` (R3 — that shape defeats the exhaustiveness it appears to provide). This binds all **four** exported walks — `outcomeLabelKey`, `isReportable`, `decisiveGameWins`, `tiebreakCells` — **including the nested `PodOutcome` level inside the first and third**, which needs its own `never` terminal (`unreachablePod`), not just the outer `PairingOutcome` one. P11c measured that the nested terminal genuinely fires.
5. **`??` not `||`** wherever a legitimate `0` or `""` can occur.
6. **`readonly` on every array/set in a prop or return type.** `import type` for every type-only import; `verbatimModuleSyntax` enforces it and P7 measured why it matters at the store boundary.
7. **No component reads a store, a route, a socket, or `Date.now()`-dependent logic beyond simple display formatting.** Everything arrives as a prop.
8. **No component discriminates a wire union inline.** Every `PairingOutcome` / `Tiebreaks` arm test lives in `tournamentPageState.ts` behind a named export. A component may call `isReportable(...)`, `outcomeLabelKey(...)` or `decisiveGameWins(...)`; it may not write `outcome === "Bye"`, `"Forfeit" in outcome`, **or `outcome.Reported.Decisive.game_wins`** in its own body. **Reaching into a union's nested payload is the same violation as testing its tag** — that is what makes the third example a rule-8 breach and not merely a property access, and it is additionally a hard compile error (P11b). A component *may* null-check a helper's **return** (`const gw = decisiveGameWins(...); gw && …`) — that is a plain `T | null` test, not a union discrimination. (This is the authoring rule both F4's fix and revision 3's M2 fix depend on; RC10 and RC12 are its revert-checks. Revision 2 tightened this rule without re-checking §5.6 against it, which is exactly how round 2's M2 survived — so an executor finding *any* remaining `outcome.` member access inside a component should treat it as a plan defect and stop.)
9. **Re-read a file before editing it** if it changed since your last read (multi-agent safety). `types.ts`, `multiplayerStore.ts` and `tournamentClient.ts` are **read-only** in this phase.

### 5.2 `client/src/pages/tournamentPageState.ts` (new) — U1

Module header: state that this is the single authority for every tournament view-model derivation; that it is pure (no React, no store runtime, no I/O); that its store imports are **type-only by design** (naming P7's measurement and V28's guard); and that it renders nothing and formats only.

Imports — **all `import type`**:

```ts
import type {
  MatchArity, PairingOutcome, PlayerSummary, PodOutcome, ScoringPolicy,
  Tiebreaks, TournamentPairingView, TournamentView,
} from "../adapter/types";
import type { TournamentCredential, TournamentRole } from "../stores/multiplayerStore";
```

**Exports, in order** (**ten** functions; the four view-model *types* below are exported too and are not counted in that ten — §4.2's convention note):

1. **`viewerRoles(credential: TournamentCredential | undefined): ReadonlySet<TournamentRole>`** — adds `"organizer"` iff `organizerToken !== undefined`, `"player"` iff `playerToken !== undefined`.
   *Disclosed deviation from the charter's `isOrganizer`.* The charter names the capability; this is its signature. Reasons, all three load-bearing: (a) it **reuses** phase 2's `TournamentRole` union instead of minting a parallel vocabulary — CLAUDE.md's "use an existing typed enum, never a raw bool"; (b) a `boolean` cannot express B5, the both-authorities case phase 2 documented as the **normal** path for a playing organizer; (c) it avoids the sibling-cluster smell of `isOrganizer` + `isEntered` + `isSpectating`. `isOrganizer(c)` becomes `viewerRoles(c).has("organizer")` at every call site. **Phase 4 has no consumer** — its consumers are phase 5's organizer/player gating (charter edge 4→5); it is chartered, unit-tested here (V11), and that is the whole reason the charter placed it in this phase.
2. **`OutcomeLabel`** (discriminated union) and **`outcomeLabelKey(outcome, seats): OutcomeLabel`**:
   ```ts
   export type OutcomeLabel =
     | { readonly key: "outcome.bye" }
     | { readonly key: "outcome.draw" }
     | { readonly key: "outcome.forfeit"; readonly winner: string }
     | { readonly key: "outcome.decisive"; readonly winner: string };
   ```
   Consumers narrow with `"winner" in label`. Return the key **and its vars together**, because two of the four keys interpolate `{{winner}}` and pairing them makes "called a key without its variable" unrepresentable. Implementation: `outcome === "Bye"` → bye; `"Forfeit" in outcome` → forfeit; else unwrap `outcome.Reported`, `=== "Draw"` → draw, `"Decisive" in pod` → decisive; each level terminates in a `never` binding. Winner names go through the private `displayNameFor(seats, key)` (§B1: falls back to the raw `player_key`, never blank).
   **Trap, named explicitly for the executor** (entry 29's forward note, re-measured as P2b): the catalog keys are `outcome.bye`/`outcome.draw` — *lowercase* — while the wire tags are `"Bye"`/`"Draw"`. `t(\`outcome.${tag.toLowerCase()}\`)` **appears** to work for those two and silently breaks for forfeit and decisive, which are not 1:1 with wire tags at all (`Reported` wraps `Decisive`/`Draw` at a second level). **Never construct a catalog key from a wire tag.** The exhaustive switch is the whole point.
3. **`isReportable(outcome: PairingOutcome | null): boolean`** — **NEW at revision 2 (F4 / round 1's B1).** The single authority for "may a result be submitted for this pairing at all". Sits immediately beside `outcomeLabelKey` because it is the second exhaustive walk over the same union.

   ```ts
   /**
    * Whether the broker will accept a `ReportMatchResult` for this pairing at
    * all — a *total* contract, not a validity judgement about a submission's
    * contents (which is `validate_match_result`'s alone, and is never
    * duplicated here).
    *
    * `TournamentMeta::report_result`
    * (`crates/lobby-broker/src/tournament.rs:1741-1753`) matches the pairing's
    * existing outcome and returns `Err` for two arms *before*
    * `validate_match_result` is ever reached (`:1754`):
    *   - `Bye`     (`:1742-1746`) — "is a bye and has no result to report"
    *   - `Forfeit` (`:1747-1751`) — "was resolved by forfeit and cannot be reported"
    * Both are production-reachable: byes come from `partition_round`'s ordinary
    * remainder handling (`:1323`) and forfeits from `drop_player`'s
    * auto-settlement of a pairing left with one active player (`:1828`).
    *
    * `Some(PairingOutcome::Reported(_)) | None => {}` (`:1752`) means an
    * ALREADY-REPORTED pairing may be reported AGAIN — a reported result is
    * overwritten at `:1755`, and correcting a mistyped tally is a legitimate
    * organizer action. This guard is therefore **arm-selective, not
    * "unresolved only"**: narrowing it to `outcome === null` would wrongly hide
    * a legal affordance. V29/V30 and RC11 pin exactly that.
    *
    * Predicate form (rather than a typed result) mirrors the broker's own
    * `TournamentStatus::is_terminal()` guard, called earlier in this same
    * function (`:1730`; `report_result` opens at `:1721`). See the plan's §4.3
    * for why a `{reason}` variant was rejected.
    */
   export function isReportable(outcome: PairingOutcome | null): boolean {
     if (outcome === null) return true;         // pending — the broker's `None` arm
     if (outcome === "Bye") return false;       // tournament.rs:1742-1746
     if ("Forfeit" in outcome) return false;    // tournament.rs:1747-1751
     if ("Reported" in outcome) return true;    // tournament.rs:1752 — re-reporting is legal
     const unreachable: never = outcome;
     return unreachable;
   }
   ```
   The `never` terminal is load-bearing, not decorative: a fifth `PairingOutcome` arm added to the wire mirror fails the build here, forcing an explicit reportability decision rather than defaulting silently in either direction.
4. **`TiebreakCell`** + **`tiebreakCells(tiebreaks: Tiebreaks): readonly TiebreakCell[]`**:
   ```ts
   export interface TiebreakCell {
     readonly id: string;          // scheme-qualified, e.g. "headToHead.gameWinPct"
     readonly labelKey: string;    // "standings.tiebreaks.headToHead.gameWinPct"
     readonly titleKey: string;    // …"gameWinPctTitle"
     readonly value: number;       // server-computed; never re-derived
     readonly format: "percent" | "points";
   }
   ```
   Three cells per arm, in the order they rank. **`format`:** every H2H axis and both Multiplayer percentages are `"percent"`; `opponents_avg_match_points` is `"points"`. **`id` is scheme-qualified deliberately** (B6): both arms carry an `opponentsMatchWinPct`, and an unqualified id would silently render a `Multiplayer` row's value under a `HeadToHead` header — asserting an equivalence the client is not the authority to assert. Terminates in a `never` binding.
5. **`formatTiebreakValue(cell: TiebreakCell): string`** — `"percent"` → `${(value * 100).toFixed(1)}%`; `"points"` → `value.toFixed(2)`. Precedent for a formatted percentage string: `components/draft/StandingsTable.tsx:17-21`. One decimal place is enough to break visible ties without implying precision the `f64` does not carry meaningfully — stated as a display decision, not a rules claim.
6. **`decisiveGameWins(outcome: PairingOutcome | null): Readonly<Record<string, number>> | null`** — **NEW at revision 3 (round 2's M2).** The single authority for reaching `PairingOutcome`'s doubly-nested `Reported → Decisive → game_wins` payload, so no component ever narrows the wire union in its own body (§5.1 rule 8). It is the **third** exhaustive walk over `PairingOutcome`, and its inner `PodOutcome` level carries its own `never` terminal. The design choice — this export vs. widening `gameWinsEntries` — is argued in §4.3.

   ```ts
   /**
    * The game-wins tally carried by a pairing's outcome, or `null` when the
    * outcome carries none. The single place that reaches into
    * `PairingOutcome`'s nested `Reported -> Decisive` shape: components call
    * this and null-check the result, and never narrow the union themselves.
    *
    * Four of the five reachable states have no tally, each for its own reason
    * and none of them an error:
    *   - `null`               pending; nothing reported yet
    *   - `"Bye"`              server-assigned (tournament.rs:1323), never played
    *   - `{Forfeit}`          server-assigned by `drop_player` (:1828)
    *   - `{Reported:"Draw"}`  MSTR: all seated players draw; no per-seat wins
    *
    * Only `{Reported:{Decisive:{game_wins}}}` yields a record — and that record
    * is legitimately EMPTY at three or more seats, because pods are
    * single-game per MSTR and `validate_match_result`
    * (`crates/lobby-broker/src/tournament.rs:967-1021`) rejects any non-empty
    * map there ("Pod results are single-game per MSTR - game_wins must be
    * empty", `:1015`).
    *
    * `{}` and `null` are therefore DIFFERENT FACTS and must never be collapsed:
    * `{}` means "a decisive result with no per-game tally to show"; `null`
    * means "there is no decisive result here at all". V31 and RC12 pin exactly
    * that distinction.
    */
   export function decisiveGameWins(
     outcome: PairingOutcome | null,
   ): Readonly<Record<string, number>> | null {
     if (outcome === null) return null;        // pending
     if (outcome === "Bye") return null;       // tournament.rs:1323
     if ("Forfeit" in outcome) return null;    // tournament.rs:1828
     if ("Reported" in outcome) {
       const reported = outcome.Reported;
       if (reported === "Draw") return null;   // MSTR: no per-seat tally
       if ("Decisive" in reported) return reported.Decisive.game_wins;
       const unreachablePod: never = reported;
       return unreachablePod;
     }
     const unreachable: never = outcome;
     return unreachable;
   }
   ```
   **Measured, not asserted (P11/P11b/P11c, §3.5):** this exact body compiles clean against the real `client/src/adapter/types.ts`; the expression it replaces does not (`TS18047` + `TS2339`); and deleting either the outer `Forfeit` branch or the inner `Draw` branch produces the predicted `TS2322` at the corresponding `never` binding. Both terminals are load-bearing — the inner one is not decoration.
7. **`GameWinEntry`** + **`gameWinsEntries(gameWins: Readonly<Record<string, number>>, seats): readonly GameWinEntry[]`** — iterate **`seats`**, filter to seats present in `gameWins`, map to `{playerKey, name: seat.display_name, wins}`. **Signature note (revision 3):** the first parameter is only *widened* from `Record<string, number>` to `Readonly<Record<string, number>>` — rule 6, and it matches export 6's return type. Every existing fixture already satisfies it, so V7's and V8's hostile fixtures are **untouched** (verified at P11). The function's contract is otherwise **unchanged**: it is a seat-order join over a record it is handed, and it discriminates no union — that is export 6's job, and keeping the two separate is the whole point of §4.3's Option-A argument. The comment must carry P10's measurement (`Object.keys({"12":…,"7":…,"alice":…}) === ["7","12","alice"]`) and the reason it matters (`player_key` is client-supplied and opaque, `protocol.rs:699-702`). Unattributable keys are dropped — they cannot be placed in seat order, and the broker rejects such payloads at write time (`game_wins.len() != 2 || !contains_key(a) || !contains_key(b)`).
8. **`myPairing(view: TournamentView, playerKey: string | undefined): TournamentPairingView | null`** — `undefined` → `null`; otherwise the first pairing whose `round === view.summary.current_round` **and** whose `players` contain `playerKey`; `?? null`.
9. **`ArityLabel`** + **`arityLabel(arity: MatchArity): ArityLabel`** — `2` → `{key:"arity.headToHead"}`, otherwise `{key:"arity.pod", seats: arity}`.
10. **`defaultScoringForArity(arity: MatchArity): ScoringPolicy`** — `{win_points: 2 * arity - 1, draw_points: 1, loss_points: 0}`. Doc comment must state plainly: *"Prefill only. Mirrors `ScoringPolicy::default_for_arity` (`crates/lobby-broker/src/tournament.rs:217-227`) because `CreateTournament.scoring` is wire-mandatory and has no `#[serde(default)]` (`protocol.rs:692`) and no RPC exposes the broker's default. The organizer may edit the result and the broker validates it (`ScoringPolicy::new` rejects `win_points == 0`), so drift here degrades a default, never a guarantee."*

Private (not exported — used by export 2 (`outcomeLabelKey`), so `noUnusedLocals` is satisfied; its behaviour is pinned through V3): `displayNameFor(seats, playerKey): string`.

### 5.3 `client/src/components/tournament/TournamentListItem.tsx` (new) — U2

```ts
interface TournamentListItemProps {
  summary: TournamentSummary;                 // NOT TournamentView — see V18
  onOpen: (code: string) => void;
}
```
`useTranslation("tournament")`. A `<button type="button" onClick={() => onOpen(summary.code)}>` following `GameListItem`'s layout: a `bracket.*` badge, a `status.*` badge (indexed **directly** off the wire value, C4), the truncated `summary.name` as the title, and a secondary line carrying `t("list.entrants", { count: summary.player_count })`, `t("labels.roundOf", { current: summary.current_round, total: summary.total_rounds })`, the `arityLabel` copy, and `t("labels.created", { date: new Date(summary.created_at * 1000).toLocaleDateString(i18n.language) })`. Trailing: the `list.view` action chip and a monospace `labels.code` chip.

**`created_at` is unix seconds — multiply by 1000** (C9; `types.ts` does not document this, §0.4 R2). Use `i18n.language` from `useTranslation()`, not the browser default. **Never render `players.length`** — the prop type makes it unavailable, which is the real fix; V18 pins the runtime half.

### 5.4 `client/src/components/tournament/CreateTournamentForm.tsx` (new) — U3

```ts
interface CreateTournamentFormProps {
  onSubmit: (req: CreateTournamentRequest) => void;   // imported from services/tournamentClient
  submitting?: boolean;
  initialArity?: MatchArity;                          // default 2
}
```
Local `useState`: `name`, `arity`, `bracket`, `totalRounds: number | null`, `scoring: ScoringPolicy`, `scoringTouched: boolean`. `scoring` initialises to `defaultScoringForArity(initialArity)`. Changing arity re-prefills `scoring` **only while `!scoringTouched`**; any edit to a scoring input sets `scoringTouched` (B8, V20a/V20b).

Fields, all labelled from `create.*`: name (`nameLabel`/`namePlaceholder`); arity (numeric input or select — `arityLabel`/`arityHint`; the hint copy already reads *"2 is head-to-head; 4 is a standard Commander pod"*); bracket (both `bracket.*` options); rounds (`totalRoundsLabel`, with an "Automatic" option submitting **`null`** — `totalRoundsAuto`; note the broker rejects an explicit `0` at **`tournament.rs:1524`**, *"total_rounds override must be at least 1"*); scoring (`scoringLabel` + `winPointsLabel`/`drawPointsLabel`/`lossPointsLabel`). Submit button: `create.submit`, or `create.submitting` while `submitting`.

**Submit exactly what was chosen.** No client-side legality check of any kind — in particular `SingleElimination` + arity ≠ 2 must reach `onSubmit` (V19). The broker is the sole authority (**`tournament.rs:1514-1523`** — the `// v1 ships single elimination for head-to-head only` comment at `:1514-1517` plus the guard at `:1518-1523`) and the doc comment on `CreateTournamentRequest` (`tournamentClient.ts:286-294`) already says so. Server error copy is `DEFERRED(phase 5)` (`errors.serverRejected`).

> **Citation-precision note (m2).** Revision 1 cited `tournament.rs:1523` for the `total_rounds == Some(0)` rejection and `:1514-1521` for the `SingleElimination` guard. Both were off by one at the boundary: `:1523` is the *closing brace* of the `SingleElimination` guard, `:1524` is the `if req.total_rounds == Some(0)`, and the guard's block ends at `:1523` not `:1521`. Corrected here, in §0.2 C7, in §4.4, and in V21. The behaviour described was correct in both revisions; only the line numbers moved.

### 5.5 `client/src/components/tournament/TournamentStandingsTable.tsx` (new) — U4

```ts
interface TournamentStandingsTableProps {
  standings: readonly TournamentStanding[];
}
```
Empty → `standings.empty`. Header row: `standings.rank`/`player`/`matchPoints`/`matchesPlayed`/`byes` (each with its `*Title` as the `title` attribute where one exists), then one `<th>` per cell of `tiebreakCells(standings[0].tiebreaks)`, using `labelKey` and `titleKey`.

Body: **`standings.map((row, i) => …)` in array order**, rank badge `i + 1`, `key={row.player_key}`. Per row, build `new Map(tiebreakCells(row.tiebreaks).map(c => [c.id, c]))` and render one `<td>` **per header cell id**, `const c = cells.get(header.id); c ? formatTiebreakValue(c) : "—"`. Dropped rows stay listed and carry the `labels.dropped` marker (V15).

> **Do not copy `client/src/components/draft/StandingsTable.tsx`.** It subscribes to a store, re-sorts (`:83-89`) and recomputes tiebreaks (`:11-15`) — all three forbidden here, and its own test file is `it.todo` stubs, so nothing there would catch a regression. Per multi-agent safety, **do not modify it either**; it is other, shipped work.

### 5.6 `client/src/components/tournament/PairingsList.tsx` (new) — U5

```ts
interface PairingsListProps {
  pairings: readonly TournamentPairingView[];
  /**
   * Supplied by phase 5 only for a viewer holding the organizer credential.
   * Presence alone does NOT make a row reportable — see the arm gate below.
   */
  onReport?: (pairing: TournamentPairingView) => void;
}
```
Empty → `pairings.empty`. Group by `round` in array order (byes generation-ordered); heading `t("pairings.round", { round })`. Per pairing: `t("pairings.table", { id: pairing.id })`; seat names joined by `t("pairings.versus")` — **rendered from `pairing.players` with no arity branch whatsoever** (V16). Outcome: `null` → `t("pairings.pending")`; otherwise `outcomeLabelKey(pairing.outcome, pairing.players)` and `"winner" in label ? t(label.key, { winner: label.winner }) : t(label.key)`.

**The game-wins lines go through `decisiveGameWins`, never through an inline narrowing (revision 3 — round 2's M2).** Per pairing:

```tsx
const gameWins = decisiveGameWins(pairing.outcome);
…
{gameWins &&
  gameWinsEntries(gameWins, pairing.players).map((e) => (
    <span key={e.playerKey}>
      {t("outcome.gameWins", { name: e.name, wins: e.wins })}
    </span>
  ))}
```

Three things this gets right that revision 2's version did not:

- **It obeys §5.1 rule 8.** Revision 2 prescribed `gameWinsEntries(outcome.Reported.Decisive.game_wins, pairing.players)` **inside this component's body** — a two-level narrowing of `PairingOutcome`, which is exactly the shape rule 8 forbids. The `gameWins &&` above is a null-check on a **helper's return**, not a union discrimination, and is permitted.
- **It compiles.** Revision 2's expression does not: measured (P11b) as `TS18047: 'p.outcome' is possibly 'null'` and `TS2339: Property 'Reported' does not exist on type 'PairingOutcome'`. The replacement was compiled against the real `types.ts` and is clean (P11).
- **It keeps "no result" and "no tally" distinct without an arity check.** A bye, a forfeit and a draw yield `null` (nothing renders); a **pod's** `Decisive` yields `{}` (`gameWinsEntries` returns `[]`, so nothing renders); a head-to-head `Decisive` yields two entries in **seat** order. **There is still no arity branch anywhere in this file** — V16's invariant is preserved, and V32 pins all four cases in one render.

**The report affordance is arm-gated, not merely prop-gated (F4 / round 1's B1).** Render the `detail.reportResult` action **iff `onReport` is supplied *and* `isReportable(pairing.outcome)`**:

```tsx
{onReport && isReportable(pairing.outcome) && (
  <button type="button" onClick={() => onReport(pairing)}>
    {t("detail.reportResult")}
  </button>
)}
```

Four points the executor must not soften:

- **Never render on `onReport`'s presence alone.** `report_result` refuses `Bye` and `Forfeit` unconditionally, before any validation (`tournament.rs:1741-1753`), so offering the action on those rows builds a request that is guaranteed to fail — the same class of defect F1 fixed inside the dialog, one layer out. RC10 is its revert-check.
- **Never write the arm test inline** (§5.1 rule 8). `isReportable` is U1's export (§5.2 item 3); `pairing.outcome === "Bye"` must not appear in this file. The exhaustiveness, the citation and the single authority all live in the module.
- **Never narrow the guard to "unresolved only."** A `Reported` pairing IS reportable again (`tournament.rs:1752`, overwritten at `:1755`); hiding the action there would remove the organizer's only way to correct a mistyped tally. RC11 is its revert-check, and it fails in the **opposite** direction from RC10.
- **Author no copy for the suppressed case.** A non-reportable pairing simply renders no action. Explanatory "this pairing cannot be reported" copy would require new keys under the full three-part S4 contract and belongs with phase 5's error-copy surface — it is `DEFERRED(phase 5)` (§6). This is what keeps §5.1 rule 2's zero-catalog-delta expectation intact.

> **Provenance of this prop, stated plainly.** `onReport` is **not** charter shorthand — the charter's `PairingsList` row (`phase-charter:171`) specifies only arity-polymorphic rendering. The prop is this plan's own addition, made because phase 5 needs a report affordance on a pairing row and **`PairingsList.tsx` is not in phase 5's scope paths** (`phase-charter:186-199`). Adding the prop is therefore correct; adding it *unguarded* would have foreclosed the guard permanently, since the successor phase cannot edit this file. Compare seam **S3**, where phase 1 was given a deliberate constraint precisely so phase 2 could fix a shared refcount inside its own scope.

### 5.7 `client/src/components/tournament/ReportResultDialog.tsx` (new) — U6

```ts
interface ReportResultDialogProps {
  isOpen: boolean;
  pairing: TournamentPairingView;   // NOT arity — see F1/V22
  onSubmit: (outcome: PodOutcome) => void;
  onCancel: () => void;
  submitting?: boolean;
  returnFocusRef?: RefObject<HTMLElement | SVGElement | null>;
}
```
Composed from the **same primitives** as `ConcedeDialog`: `FocusScope` render-prop, `AnimatePresence`, `motion.div` with `aria-modal="true"`, `useId()`-linked `aria-labelledby`, backdrop button labelled `t("common:actions.closeNamed", { name: title })`, cancel button `t("common:actions.cancel")` (a `report.cancel` key also exists — prefer `common:` for shared chrome, matching `ConcedeDialog`).

> **One deliberate, correct deviation from `ConcedeDialog` — do NOT "fix" it back (m4).** `ConcedeDialog` uses **`role="alertdialog"`**; `ReportResultDialog` must use **`role="dialog"`**. This is intentional and is the accessible choice, not an oversight: per WAI-ARIA, `alertdialog` is for an urgent interruption conveying an alert that demands immediate acknowledgement (conceding a game — a destructive, irreversible confirmation), and assistive technology announces it accordingly. `ReportResultDialog` is a **result-entry form** with radios and numeric inputs, opened deliberately by an organizer; announcing it as an alert would be wrong and noisy. Revision 1 described the composition as "exactly like `ConcedeDialog`" while prescribing the different role — accurate on the primitives, misleading on the role, and round 1 flagged the risk that an executor would "correct" the prescription to match the template. **The prescription is `role="dialog"`. The word "exactly" applies to the `FocusScope`/`AnimatePresence`/`aria-modal`/`useId()` composition, not to the role value.**

Controls: `report.heading`; `report.winnerLabel` — one radio per seat from `pairing.players`, valued by `player_key`, labelled by `display_name`; plus a `report.drawOption` radio.

**`const isHeadToHead = pairing.players.length === 2;`** — the sole gate (F1). When true, render `report.gameWinsLabel` and one numeric input per seat labelled `t("report.gameWinsFor", { name })`. When false, render none.

Submit (`report.submit` / `report.submitting`):
- Draw selected → `onSubmit("Draw")` — the **bare string** (V24).
- Otherwise `onSubmit({ Decisive: { winner: <selected player_key>, game_wins: isHeadToHead ? { [aKey]: aWins, [bKey]: bWins } : {} } })` (V23).

**No client-side validation of the tally, and no derivation of `winner` from it** (V25). The broker owns Bo3 legality and the winner↔tally consistency check (`tournament.rs:990-1009`); duplicating it would be a second, drifting copy — the same posture as V19.

**This dialog does not re-check reportability.** `PairingsList` (and, in phase 5, the detail page) gate the affordance that opens it via `isReportable`; the dialog renders whatever pairing it is handed. Keeping the check at the affordance is what makes `isReportable` a single authority rather than two.

### 5.8–5.13 Test files

Author the six files listed in §4.2. Conventions throughout: `render(<C … />)` with **no provider and no store seeding** (`GameListItem.test.tsx` precedent, measured green as P1); fixtures declared as `const x: TournamentView = {…}` so a wire-shape change is a compile error; semantic queries (`getByRole`, `getByText`); `userEvent` for interaction (`GameListItem.test.tsx` precedent) or `fireEvent` where the suite prefers it; assert the **exact** callback payload object at every interaction seam.

V30's fixture is the one to build deliberately: **one render containing four pairings** — a `Bye`, a `Forfeit`, a pending (`outcome: null`), and a `Reported` — with `onReport` supplied once for the whole list. Assert exactly two report actions exist and that they belong to the pending and `Reported` rows (query within each row's container, not globally), then click one and assert `onReport` received **that pairing object**. Re-render the same fixture with `onReport` omitted and assert zero actions. Built that way, RC10 and RC11 each red a different half, which is the property that proves the guard is arm-shaped.

**V32's fixture is the second one to build deliberately, and it is a different fixture from V30's** — do not try to overload one. It needs **five** pairings in one render: a `Bye`, a `Forfeit`, a `{Reported:"Draw"}`, a **3-seat pod** `{Reported:{Decisive:{winner, game_wins:{}}}}`, and a **2-seat** `{Reported:{Decisive:{winner, game_wins:{a:2,b:1}}}}`. Assert the first four render **zero** `outcome.gameWins` lines and the fifth renders **exactly two**, in seat order (query within each row's container). The pod row is the one that carries the row's real weight: it is `Decisive` and still renders nothing, which is only correct because its record is empty — not because anything checked the arity.

Put V26's shared assertion in a small local helper (e.g. `expectNoRawKeyPaths(container)` + `expectCatalogValuePresent(...)`) used by all five component test files — one authority for the regex and its positive control. It may live in one of the test files and be imported by the others, or be duplicated with a comment; prefer a single export from `__tests__/tournamentTestUtils.ts` if that reads cleaner, since a `__tests__` helper is still a test file and is T2-excluded either way. **If that separate helper file is created, the diff is 13 files, not 12** — §5.14's final count carries the matching carve-out (reviewer's m3).

### 5.14 Verification (S9 — direct `pnpm`, never Tilt, never cargo)

Run from the repo root, in order:

```
pnpm --dir client run type-check          # chains protocol:check (S8) — expect exit 0
pnpm --dir client run lint                # expect 0 errors; 44 pre-existing warnings, none in touched files
pnpm --dir client exec vitest run \
  src/pages/__tests__/tournamentPageState.test.ts \
  src/components/tournament/__tests__ \
  src/i18n/__tests__/localeParity.test.ts \
  src/i18n/resources.test.ts \
  src/i18n/__tests__/namespaceRegistration.test.ts
```

Expected: all new tests green, and the three i18n gates **still 199/199** (measured pristine baseline, P9) — unchanged, because §5.1 rule 2 expects zero catalog edits. A different i18n number means the catalog was touched and the full S4 contract must be satisfied.

Regression sweep (evidence, not a gate): re-run `src/components/lobby/__tests__/GameListItem.test.tsx` and `src/pages/__tests__/multiplayerPageState.test.ts` (baseline 6/6, P1). **Do not run the full client suite as a pass/fail gate** — entry 29 established ~1300 tests/132 files fail at PHASE_BASE_SHA for a Node v25.2.1 `--localstorage-file` reason unrelated to this work. If a broader sweep is run, compare *failing-file sets* at base vs candidate rather than absolute counts, exactly as entry 29's reviewer did.

Then run **RC1–RC12** (§4.12), each restoring the file immediately afterwards. **RC1 and V29's and V31's compile-time halves are checked with `type-check`, not `vitest`.** **RC3 requires temporarily re-adding the `arity` prop** — see its row; confirm it is gone again afterwards. Because vitest aborts a test at its first failed assertion, verify **both directions** of any "flip" claim (RC3, RC6, RC8, the RC10/RC11 pair, and RC12 against V31's pod case in particular) with separate runs — the diligence phase 2's executor added and that caught real fixture bugs.

Finally: `git diff --stat` must show **exactly 12 files** (6 source + 6 test) — **or exactly 13, if and only if the shared V26 assertion helper was created as its own `__tests__/tournamentTestUtils.ts` file** (§5.13's optional split; reviewer's m3). No other count is acceptable. All new, none outside `client/src/pages/`, `client/src/components/tournament/`. This count is unchanged by revisions 2 and 3 — F4's fix adds one export to an existing file and one conditional to another, and revision 3's M2 fix adds one export to that same file and one `const` to another; neither creates a file. `grep -c "CR [0-9]\{3\}"` over the diff must return **0** (§4.10).

### 5.15 Scope fence — do NOT do

- Do **not** edit `client/src/adapter/types.ts`, `client/src/services/tournamentClient.ts`, or `client/src/stores/multiplayerStore.ts`. All three are frozen; S1 in particular warns that `types.ts` is a 4728-line high-collision shared file.
- Do **not** edit `client/src/components/draft/StandingsTable.tsx` (or anything under `components/draft/`) — other agents' shipped work.
- Do **not** create a route, a page, a nav entry, or any store call. All `DEFERRED(phase 5)`.
- Do **not** touch `client/src/i18n/index.ts`, `react-i18next.d.ts` or `test-setup.ts` — phase 3 completed all three registration surfaces.
- Do **not** add catalog keys for the non-reportable case (§5.6). Suppression is silent in phase 4 by design.
- Do **not** leave RC3's temporary `arity` prop in `ReportResultDialogProps`. It is mutation scaffolding only.
- Do **not** repair the `replay` drift in `test-setup.ts` (S5), the inert `react-i18next` augmentation (phase 3's C2 — repairing it was measured at 136 errors across 66 files), the `FOUR_FORM_STEMS` inert `as const` (entry 29 finding 1), or `getTournamentOver`'s over-stated doc comment (entry 15's LOW). All are **report, do not repair**.
- Do **not** run `cargo` anything, `tilt` anything, or `./scripts/fetch-comp-rules.sh`.

---

## §6 — Deferrals owned by this phase

| Deferred item | Lands in | Interim structural verification here |
|---|---|---|
| Mounting, routing, nav, store wiring, unmount-during-in-flight-connect, live socket behaviour | phase 5 | green `tsc -b --noEmit`, green `eslint`, and the fixture-driven suites in §4.12, which are fully discriminating without a route |
| Organizer/player controls **as rendered UI** (phase 2's deferral) | phase 5 | `viewerRoles` landed and unit-tested here (V11) — the typed input phase 5 gates on |
| Key-set completeness across mounted pages (phase 3's `DEFERRED(phase 5)`) | phase 5 | this phase discharges only the **component-level `t()`-routing half** (V26); no page is mounted here |
| Server-rejection copy (`errors.serverRejected`, `errors.notOrganizer`, `errors.notEntered`, `errors.timedOut`, `errors.connectionLost`, `errors.aborted`, `errors.notFound`) | phase 5 | catalog keys already exist (phase 3); no component in this phase renders an error, so none is wired |
| **Explanatory copy for a suppressed report action** ("this pairing is a bye / was resolved by forfeit"), if wanted (F4) | phase 5, with the rest of the error-copy surface, under the full S4 contract | phase 4 suppresses the action **silently and correctly**; `isReportable` already carries the arm distinction, so phase 5 can widen its return to a `{reason}` union without changing a single call site's placement. Deliberately not authored here — it would break §5.1 rule 2's zero-catalog-delta expectation for cosmetic gain |
| Where `CreateTournamentForm`'s scoring prefill should ultimately come from (F2's residual) | phase 5 or a follow-up PR | `defaultScoringForArity` is the single, cited, tested client authority; §7.3 records the residual risk |
| The role badge on a list row (`labels.organizer`/`entered`/`spectating`) | phase 5 | keys exist; `viewerRoles` exists; deliberately not rendered here to avoid expanding the charter's `TournamentListItem` row |

**Deferral allowlist honoured.** Phase 3 deferred exactly two items. `t()` routing is discharged (V26). Key-set completeness is correctly passed on to phase 5 and is **not** silently claimed here.

---

## §7 — Findings, seams, decision points, and reporting

### 7.1 Findings to REPORT, not repair

1. **Charter phase-4 scope-path-hint omission** — no test files for `TournamentListItem` or `CreateTournamentForm`, despite both carrying verification rows. Two added; **zero sizing impact** (§4.2).
2. **`types.ts` does not document `TournamentSummary.created_at`'s unit** (measured: unix seconds). A one-line doc addition would be correct but is outside this phase's scope paths and inside S1's high-collision file.
3. **`/add-frontend-component`'s i18n bullet is stale** — "you do not edit `es/fr/de/it/pt`" is measurably false here (P8: 12 failures), and it omits `pl`. Worth a follow-up skill edit.
4. **The `add-frontend-component` skill's directory table lacks `components/tournament/`** — see the decision point in §7.5.
5. **`components/draft/StandingsTable.tsx` violates the display-layer principle three ways** and its test file is `it.todo` stubs. Pre-existing, out of scope, not touched. Worth a separate issue.
6. **Standing environment note (entry 29), re-confirmed:** the client suite is not fully green at PHASE_BASE_SHA under Node v25.2.1 for `--localstorage-file` reasons unrelated to this work. Newly measured this session: this hazard is reached **only** by modules that execute the store (P7b) — prop-driven component tests and type-only-importing pure-module tests are unaffected (P1, P7). Phase 4's entire test surface therefore sits on the clean side of it.
7. **The charter's `PairingsList` row specifies no report affordance at all** (`phase-charter:171`), yet phase 5's organizer-gating deliverable requires one and cannot add it (`PairingsList.tsx` is absent from `phase-charter:186-199`). This plan supplies `onReport` **with its arm guard** rather than deferring. Reported so the charter's own row is known to be narrower than the phase it feeds; **no charter revision is requested** — the gap is fully closed inside phase 4's existing scope paths and changes no sizing.

### 7.2 Seams touched

- **S4 (shared locale catalogs)** — in scope, **expected untouched** (§5.1 rule 2), and F4's fix is specifically designed to keep it that way. If touched, the full three-part contract applies.
- **S8 (protocol version pinned)** — `check-protocol-version.mjs` exit 0, chained by `type-check`.
- **S9 (verification environment)** — direct `pnpm`; Tilt exit 3 is *cannot answer*; no cargo lock.
- **S2 (`PairingView` collision)** — honoured by construction: every reference is to `TournamentPairingView`. The draft-side `PairingView` (`adapter/draft-adapter.ts`, consumed by `EliminationBracket.tsx` and six other call sites) is never imported, renamed, or touched.
- **S3 (structural-foreclosure precedent)** — not modified, but explicitly *applied*: F4's reasoning about `onReport` is the same "a later phase cannot fix what an earlier phase froze outside its scope" argument S3 records for the `SubscribeLobby` refcount.
- **S1, S5, S6, S7** — not reached by this phase.

### 7.3 Residual risks, disclosed rather than hidden

1. **`defaultScoringForArity` is a client-side mirror of a Rust formula with no cross-language test.** Bounded: it prefills a user-editable field the broker validates; drift degrades a default, not a guarantee. The alternatives are worse — a fixed 3/1/0 is wrong for every pod, and there is no RPC to ask. A fully-closed version needs a broker-supplied default in the wire (a follow-up PR, out of scope here).
2. **V26 detects an *unresolved* key and an obvious raw literal, but cannot detect a string that is both hardcoded English *and* happens to equal a catalog value.** Bounded by review of a 12-file diff, and by the fact that a hardcoded string only escapes detection if it duplicates copy that already exists — i.e. the worst case is a maintenance smell, not a broken locale. Phase 3 disclosed a structurally identical limit (R4, the `ns[]` half) and the reviewer accepted the honest statement over an overclaim.
3. **The mixed-arm tiebreak fixture (V5) exercises a shape the broker never emits** (C8: `standings()` binds one `order`). It is retained because the TypeScript type permits it, the charter mandates it, and the failure it guards against — three plausible-looking numbers under the wrong headers — is silent. Labelled as a type-level guard, not a production scenario.
4. **The 2-seat-short-pod-at-arity-3 shape (V22) is derived from `partition_round`'s arithmetic and `MatchArity`'s bounds by reading, not by running the broker.** The design is conservative either way: gating on seat count is correct whether or not the shape occurs, and matches the broker's own gate exactly. (Round 1's reviewer independently found further reachable instances at `n = 2` and `n = 4`, which strengthens rather than changes this.)
5. **`isReportable` is a client-side mirror of a broker refusal, and could in principle drift (F4).** Bounded in a way F2's mirror is not, on three counts: (a) it mirrors a **total** refusal, not a conditional rule — there is no content to get subtly wrong, only an arm list; (b) the safe direction is the likely one — if the broker ever became *more* permissive, the client would merely hide an action that is now legal, a visible usability bug, never an invalid request or a wrong result; (c) the doc comment pins exact line numbers and quoted error strings, so the next reader of `report_result` has a grep target. It cannot degrade into duplicating `validate_match_result`, because that function is deliberately not consulted here and the split is stated in the doc comment. Residual: no cross-language test binds the two — the same structural gap as risk 1, and closable the same way (a broker-supplied "reportable" flag on `TournamentPairingView`) in a follow-up PR, out of scope here.
6. **The report affordance's *authorization* is still phase 5's** — `isReportable` answers "can this pairing be reported by anyone", not "may this viewer report it". Phase 4 renders the action whenever `onReport` is supplied, and only phase 5 decides to supply it (gated on `viewerRoles(...).has("organizer")`, charter `:204`). Stated so the two guards are not confused for each other: they are orthogonal, and both are required.

### 7.4 Commit

One commit, **12 new files (or 13 if §5.13's optional shared test helper is split into its own file)**. Body must name: the four §0.3 corrections (F1 seat-count-not-arity with its `tournament.rs:967-1021` citation; F2 wire-mandatory scoring with `protocol.rs:692` + `tournament.rs:217`; F3 the ns-prefix-stripping restatement of the `t()`-routing assertion; **F4 the arm-selective `isReportable` guard with its `tournament.rs:1741-1753` citation, including that the `Reported` arm is deliberately permitted**); the disclosed `isOrganizer` → `viewerRoles` signature deviation and its three reasons; the deliberate `role="dialog"` deviation from `ConcedeDialog`'s `alertdialog`; **`decisiveGameWins` as the single authority for `PairingOutcome`'s nested `game_wins` payload, with the reason `gameWinsEntries` was deliberately *not* widened instead (§4.3) and the `{}` ≠ `null` distinction that choice preserves**; the zero-catalog-delta outcome; and the zero-CR-annotation result. Trailer per this session's attribution instruction.

### 7.5 Explicit decision point — do not resolve silently

**`client/src/components/tournament/` is a new component directory, and `/add-frontend-component`'s Self-Maintenance section instructs "update the directory reference table if new component directories were added."** That file (`.claude/skills/add-frontend-component/SKILL.md`) is **not** in phase 4's chartered scope paths, and no phase in this charter has it in scope.

**Recommended resolution: do NOT edit the skill file.** Report it (§7.1 item 4) and name it in the commit body as a known follow-up. Reasons: this run's culture has been strictly scope-fenced (phase 3 was explicitly told not to silently repair the `replay` drift under S5); the skill file is a shared, cross-agent artifact; and the update is cosmetic. If the executor disagrees and edits it, that must be called out in the commit body as a separate, named drive-by — never folded in silently. **Adding nothing, and reporting, is the default and is correct.**

---

## §8 — Ready-for-review summary

- **Revision 3 fixes exactly round 2's findings and nothing else.** **M1** (incomplete `role="dialog"` propagation) → the two sections revision 2's surgical reconstruction missed are corrected: §4.3's building-blocks row no longer lists `role="alertdialog"` among what `ReportResultDialog` composes from and now points at §5.7, and §4.7's "extends … composition" sentence now names `FocusScope`/`AnimatePresence`/`aria-modal`/`useId()` and explicitly excludes the role value. Every surviving `alertdialog` mention in the document now either describes `ConcedeDialog` itself or flags the deviation. **M2** (§5.6's `PairingsList` code violated the plan's own rule 8 and did not compile) → a **new U1 export `decisiveGameWins`** (Option A), chosen over widening `gameWinsEntries` (Option B) for three argued reasons — abstraction-layer separation, consistency with the module's single-purpose-export shape, and zero ripple onto V7/V8 — with the rejection of B stated as its own claim (§4.3). Export count **9 → 10**, propagated through §4.2's U1 row and convention note, §4.3, §5.2's numbered list (new item 6, old 6–9 renumbered 7–10, `displayNameFor`'s "exports 2 and 6" → "2 and 7"), §5.6, §7.4 and this section. New rows **V31**/**V32**, new revert-check **RC12**, new probe **P11** with controls **P11b**/**P11c**. Six minor findings fixed: **m1** "All three" → "All four" (§0.3); **m2** `validate_match_result` now cited as `:967-1021` in all three places, re-derived by direct read (`pub fn` `:967`, closing brace `:1021`); **m3** §5.14's file gate now reads "12, or 13 with the optional shared V26 helper file"; **m4** the wrong "four lines above" distance claim dropped from both §4.3 and §5.2's shipping doc comment, citation `:1730` kept (it is correct — `report_result` opens at `:1721`); **m5** probe count reconciled to one stated convention in §3.5 and §8; **m6** matrix-row convention stated explicitly, and the charter's line count corrected 297 → **296**.
- **Revision 2 fixed exactly round 1's findings and nothing else.** B1 → **F4**: the arm-selective `isReportable` guard (§0.3 F4, §4.3, §4.4, §4.11 B9, §5.1 rule 8, §5.2 item 3, §5.6, §6, §7.3 items 5–6), with new rows **V29**/**V30** and new revert-checks **RC10**/**RC11** that fail in opposite directions. m1 → export count corrected to **9 function exports** with its counting convention stated (§4.2) — *revision 3 raises it to **10**, per the bullet above*. m2 → `tournament.rs:1523` → **`:1524`**, and `:1514-1521` → **`:1514-1523`**, corrected in C7, §4.4, §5.4 and V21, each re-derived by line-exact read. m3 → RC3 now states it requires temporarily re-adding the `arity` prop, is scaffolding only, and must be removed. m4 → §5.7 states the `role="dialog"` deviation from `ConcedeDialog`'s `alertdialog` is deliberate and correct, with the WAI-ARIA reasoning, and must not be "fixed" back. m5 → §4.2 names the one counting combination (test files counted **and** catalogs ungrouped, maximal case = 19) that would technically fire T2, why it is not the frozen convention, and that the verdict is unchanged — following phase 3's precedent. **Everything round 1 confirmed correct is carried forward verbatim.**
- **Sizing: 6 units, 6 source scope-paths — unchanged by revisions 2 and 3**, independently re-derived, matching the charter's phase-4 row. **T1 fires, T2 does not, the conjunction does not fire.** Checked under every available counting convention, with the sole threshold-reaching combination named explicitly (§4.2) rather than left unstated. No charter revision warranted.
- **Step 0 Oracle-text gate: checked, N/A** (no card, no Oracle text). Its analogue — verify the wire and broker behaviour from Rust source — was run and produced **four material corrections** (F1, F2, F3, F4).
- **CR annotations: gate checked, N/A** on three independent grounds, including that the governing rules here are MTR/MSTR, which `tournament.rs:36` explicitly distinguishes from CR-governed game logic. `isReportable`'s doc comment cites `tournament.rs` line numbers, never a CR rule. Executor must produce a zero-match `grep` as evidence.
- **Nom compliance: N/A** — no `crates/engine/src/parser/` file changes.
- **Step 2 analogous trace: satisfied**, full path recorded, plus a **counter-example trace** (`components/draft/StandingsTable.tsx`) that is the single most likely way this phase could have gone wrong, plus a broker-side backwards trace from `report_result` to both refused arms' producers (F4).
- **Step 3.5 probing: 11 distinct probes (P1–P11)** — P1–P10 across 11 table rows (P5 and P6 share a row), plus revision 3's **P11** in its own block; **the convention is stated identically in §3.5 and here (reviewer's m5)**. Every negative result carries a paired positive control (P3/P3b, P4/P4b, P7/P7b, P10's non-digit sibling, P8's restore-to-199, and P11's two controls P11b/P11c). Revision 2's read-only line-exact re-verification of every `tournament.rs` citation is labelled as a read rather than a measurement; revision 3's P11 is a real measurement and is labelled as one. Tree verified pristine after every probe; `HEAD` still `c7bde455a`.
- **32 verification claims across 33 matrix rows** — the two counts differ because **V20 splits into V20a/V20b, which share one V-number** (reviewer's m6; revision 2 said "30 rows" while the table held 31 rows / 30 numbers). Every negative is paired with a reach-guard. **12 revert-checks**, two of which (`RC1`, and V29's and V31's compile-time halves) are explicitly flagged as surfacing under `type-check` rather than `vitest`, and one of which (`RC3`) is explicitly flagged as requiring temporary scaffolding. Two checks are deliberately *opposed* so no single implementation can be green under both: the RC10/RC11 pair (arm-selectivity), and RC12 against V31's pod case (`{}` ≠ `null`).
- **Charter deferral discipline:** phase 3's `DEFERRED(phase 4)` is discharged by an explicitly-labelled row (V26); phase 3's `DEFERRED(phase 5)` is passed on, not absorbed; seven of this phase's own deferrals are attributed to phase 5, and none of them is a structural foreclosure — F4's fix is precisely the removal of the one that would have been.
- **Two disclosed deviations** from charter/template shorthand, each argued from principle rather than asserted: `isOrganizer` → `viewerRoles` (three independent reasons, same posture as phase 1's §0.9 and phase 2's M2), and `ConcedeDialog`'s `alertdialog` → `dialog` (WAI-ARIA semantics; a result-entry form is not an urgent interruption).
