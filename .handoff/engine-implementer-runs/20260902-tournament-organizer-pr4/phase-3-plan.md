# Phase 3 Plan — i18n `tournament` namespace registration (revision 2)

## Revision summary — what changed and why

| Finding | Status | Fix applied |
|---|---|---|
| **BLOCKING — V7 has no committed test; nothing else catches its absence** | Fixed | New committed test `client/src/i18n/__tests__/namespaceRegistration.test.ts` (§5.9), asserting through the **test-harness `i18next` singleton** that `test-setup.ts` configures, with the paired reach-guard. V7 promoted from "no new test" → **must run**; test-count delta recomputed **179 → 199** across **3** files. New refinement **R4** records the one thing the test provably does *not* catch, so V7 does not overclaim. |
| **NB-1 — §5.1 rule 4 opens a second, undisclosed escape hatch** | Fixed | One sentence added to §7.3 item 3 disclosing the placeholder-renaming escape hatch alongside the existing "must remember to register the stem" one. Design unchanged; `arity.pod`'s `{{seats}}` stands. |
| **NB-2 — stale `page.title` cross-reference** | Fixed | Every prose use of `page.title` as an example replaced with a key that exists in §5.2 (`page.landingTitle` where the value `"Tournaments."` is load-bearing, `list.heading` where a generic example reads better) — in §0.2 C3, §3.5, §6 V1, §7.1. A footnote records that the probe draft spelled the key `page.title`; the final catalog renames it `page.landingTitle` with the identical value, so every probe result transfers verbatim (reformulated, not refreshed). |
| **NB-3 — §5.2 design note overclaims for `outcome.*` / `standings.tiebreaks.*`** | Fixed | Design note split into two bullets: the direct-indexing claim now covers **only** `status.*`/`bracket.*` (independently re-verified: `adapter/types.ts:4546-4553` — both are flat string unions). `outcome.*`/`standings.tiebreaks.*` restated as one-key-per-member under the same *"mirror the union, don't invent a mapping table"* principle but consumed via phase 4's chartered exhaustive-switch helpers, because their wire shapes (`types.ts:4561-4599`) are externally-tagged objects, not flat strings. |

Everything else — the 136-error/66-file figure, ns-prefix stripping, all union spellings, the verbatim error strings, the 179 baseline, and the Sizing section (**2 units, 5 grouped source scope-paths**) — is carried forward verbatim.

**New measurements taken for this revision** (worktree at `f77ca3f4`, all probe files deleted, `git status --porcelain` empty afterward, HEAD unmoved, 179 baseline re-confirmed green):

| # | Probe | Measured result |
|---|---|---|
| 12 | `i18n.t()` through the harness singleton (`import i18n from "i18next"`), tree pristine | `multiplayer:page.deckRejected` → `"Deck was rejected by the host."` (positive control: the instance resolves); `tournament:list.heading` → **`"list.heading"`**; `replay:anything.here` → `"anything.here"`; `definitelyNotARealNamespace:someKey` → **`"someKey"`**; `definitelyNotARealNamespace:list.heading` → `"list.heading"` |
| 13 | `createInstance()` isolation of `test-setup.ts`'s two edits | `ns[]` entry only, `resources.en` absent → `"list.heading"` (**caught**). `resources.en` only, `ns[]` absent → `"Open Tournaments"` (**not** caught). Both → `"Open Tournaments"` |
| 14 | Prefix-free / `useTranslation`-style resolution | `getFixedT(null,"tournament")("list.heading")` and `t("list.heading",{ns:"tournament"})` both → `"Open Tournaments"` even with `ns[]` lacking the entry |
| 15 | Baseline re-confirmation | `pnpm exec vitest run src/i18n/__tests__/localeParity.test.ts src/i18n/resources.test.ts` → 2 files, **179** tests, green |

---

**Run:** PR 4/4 tournament-organizer rollout · phase 3 of 5
**Worktree:** `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend` · branch `feat/tournament-organizer-pr4-frontend`
**PHASE_BASE_SHA:** `f77ca3f4a7c56962e788b106cd239efdd7df2c65` (phase 2's accepted candidate)
**Mode:** phase-plan (charter §"Phase 3", seams S4 + S5 + S8 + S9)

---

## §0 — Step 0: Premise verification (scoped to phase 3's content)

No card is referenced; the Scryfall gate is N/A. Phase 3's premises are entirely about the current state of the i18n infrastructure, so every one was re-verified against real source at `f77ca3f4` and, where a *behavior* was claimed, measured (see §3.5).

### 0.1 Premises CONFIRMED

| # | Charter premise | Verified against | Verdict |
|---|---|---|---|
| P1 | `NAMESPACES` in `client/src/i18n/index.ts` holds 8 entries | `index.ts:10-19` — `common, menu, game, deck-builder, draft, settings, multiplayer, replay` | exactly 8 |
| P2 | `react-i18next.d.ts` carries a `resources` map with 8 `import type` lines | `react-i18next.d.ts:6-13`, `:18-27` | confirmed |
| P3 | `test-setup.ts` registers **7** namespaces — `replay` is missing (pre-existing drift, S5) | `test-setup.ts:28` (`ns` array) and `:30-40` (`resources.en`) — both omit `replay` | still there, still out of scope |
| P4 | `resources.test.ts` auto-discovers, no edit needed | `resources.test.ts:48-54` keys off the Vite glob; `:18-26` `readdirSync` for encoding; `:99-108` loops `SUPPORTED_LNGS` | measured — probe 1 flagged a new key in a brand-new namespace with zero test edits |
| P5 | `localeParity.test.ts` `namespaces`/`locales` are `readdirSync`-derived at `:61`/`:64` | verbatim match | confirmed |
| P6 | Key parity is exact in **both** directions at `:276`/`:279`; placeholder parity at `:282`; stale-gap policing at `:303` | verbatim | confirmed |
| P7 | `KNOWN_PLACEHOLDER_GAPS` (`:32-36`) is an allowlist — do not add tournament entries | currently **`[]`** (empty) | confirmed, stricter than the charter implies: any addition is the *first* entry |
| P8 | `FOUR_FORM_STEMS` (`:137-154`) is `readonly string[]` with **16** entries, **one** use site at `:202`, inside a loop whose `target` is `load(locale, "draft.json")` hardcoded at `:201` | verbatim; counted exactly 16 | charter finding A confirmed correct in every particular |
| P9 | `WORKSPACE_SHELL_KEYS` (`:69-135`, loaded at `:168`) and `resolves_polish_one_few_many_and_other_without_fallback` (`:210-269`) are separate draft-pinned surfaces, not in scope | verbatim | confirmed |
| P10 | Four-form-in-all-7 is existing house convention | `en/draft.json` `workspace.count.deck_{one,few,many,other}` all present, `_few`/`_many`/`_other` all = `"Deck ({{count}} cards)"`; `fr` mirrors identically | confirmed |
| P11 | Locale dirs are exactly `{en,es,fr,de,it,pt,pl}`, 8 catalogs each | `ls` | confirmed |
| P12 | Nav labels resolve in `menu`, not `tournament` | `navItems.tsx` `NavItem.labelKey` doc-comment says "i18n key under the `menu` namespace"; `Rail.tsx:22` and `TabBar.tsx:20` both `useTranslation("menu")`, both render `t(labelKey)`; `en/menu.json` has the `nav.*` group at `:312-323` | confirmed — `nav.tournament` belongs in `menu.json` |
| P13 | Phase 2's two client-authored English strings exist verbatim | `client/src/stores/multiplayerStore.ts:493-497` — `"You are not the organizer of this tournament."` / `"You are not entered in this tournament."`, selected on `role` inside `runGatedTournamentRpc`, with `TournamentNotAuthorized.role` doc-comment at `:396-398` explicitly saying "Phase 3/5 replace this with a `t()` lookup keyed off role" | verbatim confirmed — plan uses these exact strings |
| P14 | Protocol version pinned (S8) | untouched by this phase | confirmed |

### 0.2 Premises CORRECTED — three, all material

**C1 — S9's "`client/node_modules` is absent" is stale.** `node_modules` is present at `f77ca3f4` (phases 1-2 installed it). Consequence: the executor should not blindly re-run `pnpm install --frozen-lockfile`; run it only if a `pnpm exec vitest` invocation fails to resolve. Everything else in S9 holds — `tilt get uiresource clippy` still fails here, so `./scripts/tilt-wait.sh` returns exit 3 (cannot answer, never a build failure), and no phase-3 file is Rust, so `cargo fmt`/`clippy`/`test-engine` are N/A and the cargo target lock is never taken.

**C2 — the `react-i18next.d.ts` type oracle is INERT. `tsc` cannot prove "`t("tournament:…")` typing oracle wired."** This is the single largest premise correction and it is measured, not inferred (probes 9-11):

- `i18next@26.2.0` declares `CustomTypeOptions` in module `"i18next"` (`node_modules/i18next/typescript/options.d.ts:28`). `react-i18next@17.0.8` declares none of its own.
- The repo augments `declare module "react-i18next"` (`react-i18next.d.ts:15-29`), which therefore mints a fresh, unreferenced interface. Its own header comment — "so `t("bad.key")` is a compile error" — is false today.
- Measured: with `tournament` fully registered, `tsc -b --noEmit` exits 0 on `useTranslation("tournament"); t("page.doesNotExist")` and on `useTranslation("nosuchns")`.
- Confirming the mechanism: re-pointing the identical augmentation at `declare module "i18next"` makes the oracle fire instantly and hard.

Three consequences, all folded into this plan:
1. The charter's phase-3 verification bullet "`tsc -b --noEmit` proves `react-i18next.d.ts` registration compiles" is downgraded: `tsc` proves the new `import type` path resolves and the declaration file compiles. It proves nothing about key typing. §6 states the claim at its true strength.
2. The charter's phase-3 goal clause "so phases 4 and 5 can call `t()` without a type error" is, strictly, vacuous. The real, measured value of this phase is runtime: `NAMESPACES` + `resources` (app) and `test-setup.ts`'s `ns` + `resources` (tests) are what make `t("tournament:…")` return English copy instead of echoing a bare key path. As of this revision this is **committed** here as V7's new test (§5.9), not merely probed.
3. Repairing the drift is out of scope, and the cost is measured, not asserted. Re-pointing the augmentation at `"i18next"` with the full 9-namespace resources map produces 136 pre-existing type errors across 66 files (121 × TS2345, 14 × TS2322, 1 × TS2589 "type instantiation is excessively deep"). A three-figure, whole-frontend repair is a standalone PR, categorically not a drive-by inside a 5-path registration phase. It is treated exactly as S5 treats `replay`: do not silently repair, report it (§7.3).

**C3 — a missing key renders the key path WITHOUT its namespace prefix.** Measured: in a registered namespace, `t("tournament:page.doesNotExist")` returns `"page.doesNotExist"`, and `t("tournament:deeply.nested.missing")` returns `"deeply.nested.missing"`. The `ns:` prefix is stripped. Re-measured in this revision through an unregistered namespace as well (probe 12): `t("tournament:list.heading")` with `tournament` unregistered returns `"list.heading"`, and `t("definitelyNotARealNamespace:someKey")` returns `"someKey"` — the same stripping, whether the namespace is registered-but-missing-the-key or entirely absent. This does not change anything phase 3 builds, but it falsifies the literal wording of two deferral rows this phase hands forward — phase 4's and phase 5's "assert no rendered text node equals a raw `tournament.…` key path". Nothing would ever render `tournament.list.heading`; it renders `list.heading`. §7.1 restates both deferrals in a form that can actually fire. It is also what makes the missing-registration failure silent and plausible-looking rather than loud — the reason V7 now carries a committed test.

### 0.3 Premise refinements (non-blocking, hand to the executor)

- **R1 — the reach-guard fires as ONE failing test, not four.** `keeps_all_plural_families_complete_in_every_locale` is a single `it` with nested loops, so the first failing `expect` aborts it. Measured observable: 1 failed test, message `en:menu.json:entrants_one: expected undefined to deeply equal Any<String>`. V4 states it that way.
- **R2 — the assertion label must carry `ns` or the reach-guard is not self-identifying.** With two namespaces in the list, the existing label `` `${locale}:${stem}_${suffix}` `` cannot say which file was searched. §5.8 adds `${ns}` to the label. Deliberate deviation from the charter's "no assertion semantics" shorthand: it changes the message, never the assertion.
- **R3 — no unused-key gate exists.** `i18next-parser@9.4.0` is a devDependency, but `client/i18next-parser.config.js` is manual-only (`keepRemoved: true`), invoked by no `package.json` script, no workflow, and no Tilt resource. Authoring ~110 keys with zero consumers is therefore safe.
- **R4 (new this revision) — of `test-setup.ts`'s two edits, only the `resources.en` entry is observable at runtime; the `ns[]` array entry is not.** Measured with isolated `createInstance()`s (probes 13-14): `ns:[...,"tournament"]` with `resources.en` lacking `tournament` → `t("tournament:list.heading")` returns the bare `"list.heading"`; the mirror case — `resources.en.tournament` present, `ns[]` lacking the entry — resolves correctly to `"Open Tournaments"`, and so do the prefix-free `getFixedT(null,"tournament")(…)` and `t(…,{ns:"tournament"})` forms `useTranslation` is built on. The `ns[]` list governs preloading for async backends, which this synchronous, resources-supplied harness does not use. Consequence, stated so V7 does not overclaim: §5.9's test catches complete omission and the `resources.en` half — the half that actually decides whether copy renders — but a lone missing `ns[]` array entry would still pass it. That entry is still mandatory: `test-setup.ts:24`'s own comment says "Keep the namespace list in sync with `NAMESPACES`", and S5's whole existence is a live instance of that list drifting.

---

## §1 — Applicable skills

No skill in the `/engine-*` table applies: this phase touches no Rust, no Oracle text, no engine enum, no effect/keyword/trigger/static/replacement, no `GameAction` round-trip, and no card-data pipeline.

- `/add-frontend-component` — inspected, does not apply. Its checklist is scoped to components that dispatch `GameAction`s against `WaitingFor` states. Phase 3 authors zero components. Its consumers land in phases 4-5.
- `/card-test` — N/A, no cast-pipeline test.
- `/add-engine-variant` — N/A, no engine enum variant.

`DEFERRED(phase 4)` — `/add-frontend-component`'s checklist steps for the five tournament components.
`DEFERRED(phase 5)` — its route/mount/store-subscription steps for the two pages.

**CR annotations: N/A.** This phase implements no MTG Comprehensive Rule. It is display-layer string registration.

---

## §2 — Analogous trace (hard gate)

**Traced feature: the `replay` namespace**, the most recently added namespace and the closest structural analogue.

```
client/src/i18n/locales/en/replay.json          authored English catalog (the typing/parity oracle)
  → client/src/i18n/locales/{es,fr,de,it,pt,pl}/replay.json   6 mirrors, exact key parity
  → client/src/i18n/resources.ts:5-8              import.meta.glob("./locales/*/*.json") picks it up with NO edit
  → client/src/i18n/resources.ts:33-42            reshaped to { lng: { ns: tree } }
  → client/src/i18n/index.ts:10-19                NAMESPACES gains "replay"  <- registration surface 1
  → client/src/i18n/index.ts:37-48                i18n.init({ resources, ns: NAMESPACES })
  → client/src/i18n/react-i18next.d.ts:12, :26    import type + resources map entry  <- registration surface 2
  → client/src/test-setup.ts:25-44                ns[] + resources.en{}  <- registration surface 3  (replay MISSING here — S5 drift)
  → client/src/i18n/resources.test.ts:48-108      key parity, auto-discovered via the glob
  → client/src/i18n/__tests__/localeParity.test.ts:61-64, :271-299   key + placeholder parity, auto-discovered via readdirSync
```

What the trace establishes, and what phase 3 copies verbatim: the registration triple is `index.ts` + `react-i18next.d.ts` + `test-setup.ts`, both parity gates are free (no test edit), and the catalog file itself needs no wiring because the glob is pattern-driven. What the trace also establishes by counter-example: `replay` reached only two of the three surfaces and nothing caught it — which is precisely why S5 exists and why this phase must hit all three deliberately rather than assume a gate will notice. **This revision closes that loop rather than merely restating it:** §5.9's test is the gate that would have caught `replay`, and V7 is the matrix row that makes it mandatory.

**Second trace, for the `FOUR_FORM_STEMS` refactor: `WORKSPACE_SHELL_KEYS`.** Same file, same shape (a pinned key list iterated against a `load()`ed catalog at `:165-175`), and the reason the refactor must not touch it: it is separately pinned to `draft.json` at `:168` for a different purpose.

**Third trace, for §5.9's new test: `client/src/components/chrome/__tests__/DebugLibraryViewer.focus.test.tsx`.** This is the house precedent for reaching the test-harness i18n instance from a test. It does `import i18n from "i18next"` (`:2`) and then drives that same singleton — `i18n.addResourceBundle("de","game",deGame,true,true)` (`:95`), `await i18n.changeLanguage("de")` (`:97`), `await i18n.changeLanguage("en")` in `afterEach` (`:85`). That works because `test-setup.ts:25` calls `i18n.use(initReactI18next).init({...})` on the default `i18next` export rather than a `createInstance()`, and `vitest.config.ts`'s `setupFiles: ["src/test-setup.ts"]` runs it before every test file. So the default export is the configured harness instance. §5.9 follows this idiom exactly. (Contrast `localeParity.test.ts:4`, which imports `createInstance` and builds its own instance from disk — which is precisely why it cannot see `test-setup.ts` and why the deregistration experiment left it green.)

---

## §3 — Files read in full before proposing changes

`client/src/i18n/index.ts`; `client/src/i18n/react-i18next.d.ts`; `client/src/test-setup.ts`; `client/src/i18n/resources.ts`; `client/src/i18n/resources.test.ts`; `client/src/i18n/index.test.ts`; `client/src/i18n/__tests__/localeParity.test.ts`; `client/vitest.config.ts`; `client/src/components/chrome/__tests__/DebugLibraryViewer.focus.test.tsx`; `client/src/i18n/locales/en/menu.json`; `client/src/i18n/locales/en/multiplayer.json`; `client/src/i18n/locales/{en,fr,pl}/draft.json` (`workspace.count`); `client/src/i18n/locales/en/common.json`; `client/src/stores/multiplayerStore.ts` (`:355-503`, `:760-810`); `client/src/adapter/types.ts` (Tournament section, `:4546-4670`); `client/src/services/tournamentClient.ts` (`:95-135`, `:290-335`); `client/src/components/chrome/{navItems.tsx,Rail.tsx,TabBar.tsx}`; `client/i18next-parser.config.js`, `client/package.json`.

---

## §3.5 — Probe log (measured, not traced)

All probes ran in the worktree against real files, then were fully reverted; the tree was verified pristine afterward (`git status --porcelain` empty, HEAD unmoved at `f77ca3f4`, 179 tests green, `tsc` exit 0). No probe took the cargo target lock.

**Positive control / baseline.** `pnpm exec vitest run src/i18n/__tests__/localeParity.test.ts src/i18n/resources.test.ts` → 2 files, 179 tests, all green (re-confirmed at revision time, probe 15).

**Key-naming footnote (revision 2).** Probes 1 and 7 were run against a catalog draft that spelled the landing-page title key `page.title`. The final §5.2 catalog renames that key `page.landingTitle`, with the identical value `"Tournaments."`; there is no `page.title` key in the authored catalog. The rows below are stated under the final name.

| # | Probe | Measured result |
|---|---|---|
| 1 | Add `tournament.json` to all 7 locales, with `de` missing `page.landingTitle` and `pl` dropping `{{code}}` from `list.code` | 3 failures, zero test edits. `resources.test.ts` → `missing: ["tournament.page.landingTitle"]`; `localeParity` key parity → `["page.landingTitle"]`; `localeParity` placeholder parity → `["list.code: en=[code] pl=[]"]`. Count 179 → 198 (+19) |
| 2 | Repair both mirrors | 198 green |
| 3 | Apply the `FOUR_FORM_STEMS` parameterization | 114 green in `localeParity` alone; draft coverage unchanged |
| 4a | Hostile: flip the tournament entry's `ns` to `"menu.json"` | 1 failed test — `keeps_all_plural_families_complete_in_every_locale`, message `en:menu.json:entrants_one: expected undefined to deeply equal Any<String>` |
| 4b | Hostile: delete `entrants_few`/`entrants_many` from all 7 catalogs, stem registered | 1 failed test, `en:tournament.json:entrants_few` — while key parity stayed fully green (197 passed) |
| 4c | Control: same missing forms, stem not registered | 198 green |
| 6 | Register all three surfaces + a scratch consumer; `npx tsc -b --noEmit` | exit 0. `t("tournament:entrants",{count:3})` type-checks against a catalog carrying only `entrants_{one,few,many,other}` |
| 7 | Runtime, via `test-setup.ts` registration | `t("tournament:page.landingTitle")` → `"Tournaments."`; `t("tournament:list.entrants",{count:1})` → `"1 entrant"`; `{count:5}` → `"5 entrants"` |
| 8 | Missing key in a registered ns | → `"page.doesNotExist"` — ns prefix stripped (C3) |
| 9 | Type-oracle negative controls | `t("page.doesNotExist")` → tsc exit 0; `useTranslation("nosuchns")` → tsc exit 0 |
| 10 | Re-point the augmentation at `declare module "i18next"` | Errors immediately → mechanism confirmed |
| 11 | Full 9-ns augmentation at `"i18next"` | 136 errors / 66 files |
| **12** | **(new) Harness-singleton resolution on a pristine tree** — `import i18n from "i18next"`, no edits | Positive control: `t("multiplayer:page.deckRejected")` → `"Deck was rejected by the host."`. `t("tournament:list.heading")` → **`"list.heading"`**. `t("replay:anything.here")` → `"anything.here"`. `t("definitelyNotARealNamespace:someKey")` → **`"someKey"`**. `t("definitelyNotARealNamespace:list.heading")` → `"list.heading"` |
| **13** | **(new) Isolate `test-setup.ts`'s two edits** via three `createInstance()`s | `ns[]` entry present, `resources.en` absent → `"list.heading"` (§5.9 catches this). `resources.en` present, `ns[]` absent → `"Open Tournaments"` (§5.9 does not catch this). Both present → `"Open Tournaments"` |
| **14** | **(new) Prefix-free resolution**, the form `useTranslation` uses | With `resources.en.tournament` present but `ns[]` lacking it: `getFixedT(null,"tournament")("list.heading")` → `"Open Tournaments"`; `t("list.heading",{ns:"tournament"})` → `"Open Tournaments"` |
| **15** | **(new) Baseline re-confirmation** at revision time | 2 files, 179 tests green |

**Assertions NOT probed:** a `{{count}}` key authored without plural suffixes falling back cleanly to the base key (the §5.2 authoring rule is safe either way); `eslint` on the refactored/new test files (cheap, mandatory step V8); translation quality for the six non-English locales (nothing in this repo gates it structurally).

---

## §4 — Architectural sections

### 4.1 Pattern Coverage

Two classes, neither a special case:

1. **The namespace-registration class.** The registration triple + a 7-locale catalog group is the repeatable unit by which every UI domain enters this codebase — eight prior instances, and `tournament` is the ninth, built identically. §5.9's new test is written against this class, not against `tournament` specifically: its positive assertion names one namespace, but its shape (resolves through the harness instance / an unregistered namespace returns its bare path) is the invariant every one of the nine must satisfy, and the one `replay` silently violates today.
2. **The four-form enforcement class** — this is where the phase actually generalizes. Before this phase, `FOUR_FORM_STEMS` could enforce Polish plural completeness for exactly one namespace (`draft.json`). After parameterization it enforces the same invariant for any namespace × any stem, for all 7 catalogs including English.

The key set is designed by the same rule: every closed wire union gets exactly one key per member. This is what lets phase 4's `outcomeLabelKey`/`tiebreakColumns` be exhaustive switches with no `default` arm.

### 4.2 Sizing

**Units = 2** (unchanged from the charter's recursive table):

| Unit | Registration surfaces | Discriminating test |
|---|---|---|
| U1 — the `tournament` namespace | `i18n/index.ts` `NAMESPACES`; `react-i18next.d.ts`; `test-setup.ts`; 7 × `tournament.json`; `localeParity.test.ts` `FOUR_FORM_STEMS` + loop | `keeps_all_plural_families_complete_in_every_locale` red under probe 4b; **`resolves_the_tournament_namespace_through_the_test_harness_instance` (new, §5.9) red if `test-setup.ts`'s `resources.en` entry is omitted**; plus auto-discovered parity |
| U2 — the `menu` nav key | 7 × `menu.json` `nav.tournament` | auto-discovered key parity across all 7 `menu.json` |

The `FOUR_FORM_STEMS` parameterization is not a third unit — infrastructure inside U1. The new §5.9 test is likewise not a third unit: it is U1's discriminating test for the registration surface U1 already owns.

**Dependency edges:** U1 → U2 none. Outbound: 3→4, 3→5.

**Expected source scope-path count = 5** (grouped): 3 authored modules + 7-file `tournament.json` mirror group (1) + 7-file `menu.json` mirror group (1). `localeParity.test.ts` and the new `namespaceRegistration.test.ts` are test files, excluded from T2 counting outright. Ungrouped this would be 3 + 14 = 17.

**Phase-fit re-adjudication:** T1 fires (2). T2 does not (5). Conjunction does not fire. The blocking fix does not move either number.

### 4.3 Building Blocks

N/A engine table. Frontend blocks composed from, none new: the glob (`resources.ts:5-8`), the reshape reducer, `load(locale, ns)` (already parameterized — the refactor calls the existing signature correctly), `flatten`/`placeholders`, `menu.json`'s `nav.*` group, `en/multiplayer.json`'s `page.*` grouping convention, `common.json`'s `actions.*`, and **the harness i18n singleton reached via `import i18n from "i18next"` (house idiom) — §5.9 composes from it rather than constructing an instance.**

**One new construct, justified:** the `{ ns, stem }` object shape for `FOUR_FORM_STEMS`.

**No new test helper.** §5.9 deliberately introduces no fixture, factory, or shared utility.

### 4.4 Logic Placement

| Piece | Placed in | Justification |
|---|---|---|
| User-visible English copy | `locales/en/tournament.json` | catalogs are the sole authority for display strings |
| 6 translations | `locales/{es,fr,de,it,pt,pl}/tournament.json` | parity gated in both directions |
| Nav label | `locales/*/menu.json` `nav.tournament` | measured (P12): `Rail.tsx`/`TabBar.tsx` resolve `labelKey` in `menu` |
| App-runtime ns list | `i18n/index.ts` `NAMESPACES` | single source feeding `i18n.init({ ns })` |
| Type-oracle registration | `react-i18next.d.ts` | correct location even though currently inert (C2) |
| Test-runtime ns list | `test-setup.ts` | the load-bearing registration |
| **Assertion that the test-runtime registration took effect** | **`i18n/__tests__/namespaceRegistration.test.ts`** | **a test-harness invariant, asserted through the harness's own instance; cannot live inside `test-setup.ts`, which is a setup file with no test runner context** |
| Four-form enforcement | `localeParity.test.ts` `FOUR_FORM_STEMS` | test-side invariant over catalog data; no runtime consumer |
| `role` → error-key selection | NOT here — phase 5 | phase 3 mints keys; the switch on `role` is a consumer in `multiplayerStore.ts` |

Phase 3's diff contains no component, no store edit, no route, and no `t()` call in any source module — the only two `t()` calls in the diff are inside §5.9's test.

### 4.5 Rust Idioms — N/A (TypeScript equivalents)

Typed shape over parallel data (`ReadonlyArray<{ns,stem}>`); `readonly`+`as const` preserved; destructuring in the loop head; closed unions mirrored one-key-per-member; no `any`/non-null-assertion/type-only widening; `{{count}}` reserved as the plural selector.

### 4.6 Nom Compliance — N/A

No Rust file changes; JSON key lookup by exact string is data indexing, not parsing.

### 4.7 Extension vs Creation

Everything extends; nothing new is created. The one new file — §5.9's test — creates no new pattern: the third test file under the i18n tree, using the same `import i18n from "i18next"` idiom an existing component test already uses.

**Two rejected alternatives for the four-form problem:** (1) append the string to the old list — verified broken (28 guaranteed failures); (2) convention-only with no gate — measured to leave a live hole (probe 4c).

**Two rejected alternatives for V7's committed test (new this revision):**
1. Assert against the JSON catalogs (`expect(flatten(enTournament)).toHaveProperty(...)`) — rejected as a tautology that stays green through the deregistration experiment.
2. Assert the `test-setup.ts` source text (`expect(source).toContain("tournament")`) — rejected: asserts file shape not runtime behavior, doesn't distinguish the `resources.en` entry from the `ns[]` entry (probe 13 shows they're not equivalent).

### 4.8 Analogous Trace

See §2. Named features: the `replay` namespace; `WORKSPACE_SHELL_KEYS`; `DebugLibraryViewer.focus.test.tsx` (the harness-singleton idiom §5.9 copies).

### 4.9 Variant Discoverability — N/A

No engine enum variant proposed.

### 4.10 Identity / Provenance Contract

**B1 — which namespace a four-form stem is checked in.** Authority: the `ns` field of a `FOUR_FORM_STEMS` entry. Multi-authority hostile fixture: probe 4a (flipping the tournament entry's `ns` fails exactly one test, naming it).

**B2 — which of two refusal copies a local authorization failure selects.** Authority: `TournamentNotAuthorized.role`, never message text, never a re-read of credentials. Phase-3 obligation, discharged here: English values verbatim identical to the phase-2 strings — confirmed in P13.

**B3 — which catalog is the authority for the key set.** Authority: `locales/en/tournament.json`, live, re-read every test run. Multi-authority hostile fixture: probe 1.

**B4 — what a namespace registration actually binds (post-C2).** Authority: runtime, in two independent places — `NAMESPACES`+`resources` (app) and `resources.en`+`ns` (tests). Not the type layer (inert, C2). **Within the test harness, refined by R4: the sole resolution authority is `test-setup.ts`'s `resources.en` object; the `ns[]` array is a preload hint this synchronous configuration never consults.** Failure mode: an unregistered namespace does not throw — it renders the bare key path without the `ns:` prefix, silent and plausible-looking. **Multi-authority hostile fixture, now committed rather than merely probed:** §5.9 asserts a registered namespace resolves to something other than its bare path and, in the same test, that a namespace registered nowhere returns exactly its bare path — two authorities exercised against the same instance in the same assertion pair. The `replay` drift (S5) remains a live instance of the app-side and test-side registrations disagreeing, deliberately unrepaired.

### 4.11 Verification Matrix

Full matrix in §6. No Oracle text accepted, no parser branch changes, no coverage status moves — `cargo coverage`/`cargo semantic-audit` N/A.

---

## §5 — Step-by-step implementation

Order: English catalog first, then mirrors, then registration, then the refactor, then the registration test. Everything lands in **one commit**.

### 5.1 — Authoring rules the executor must hold throughout

1. Every key lands in all 7 catalogs in this commit.
2. Every `{{placeholder}}` set is identical across all 7.
3. Do not add anything to `KNOWN_PLACEHOLDER_GAPS` (currently `[]`).
4. `{{count}}` is the plural selector — any key using it needs all four suffixes in all 7 catalogs and registration in `FOUR_FORM_STEMS`. A key that merely displays a number uses a different placeholder name. This plan authors exactly one `{{count}}` family. *(The general limitation this rule creates is disclosed in §7.3 item 3.)*
5. Four forms in all 7 including English.
6. The seductive wrong fix: never delete Polish's `_few`/`_many` to fix an extra-key failure — add the missing forms to the other six.
7. UTF-8, no BOM, no `\uXXXX` escapes, no U+FFFD.
8. JSON style: 2-space indent, trailing newline; mirror English's key order.
9. Zero component files, zero store edits, and zero `t()` calls in any source module. The two `i18n.t(...)` calls in §5.9's test are the sole `t()` usage in this diff.

### 5.2 — Create `client/src/i18n/locales/en/tournament.json` (new file)

```json
{
  "page": {
    "eyebrow": "Tournaments",
    "landingTitle": "Tournaments.",
    "landingDescription": "Create a tournament, join with a code, or follow one already running.",
    "detailDescription": "Tournament {{code}}",
    "backToList": "All tournaments"
  },
  "labels": {
    "code": "Code {{code}}",
    "roundOf": "Round {{current}} of {{total}}",
    "created": "Created {{date}}",
    "organizer": "Organizer",
    "entered": "Entered",
    "spectating": "Spectating",
    "dropped": "Dropped"
  },
  "status": {
    "Registration": "Registration",
    "InProgress": "In Progress",
    "Completed": "Completed",
    "Abandoned": "Abandoned"
  },
  "bracket": {
    "Swiss": "Swiss",
    "SingleElimination": "Single Elimination"
  },
  "arity": {
    "headToHead": "Head-to-head",
    "pod": "{{seats}}-player pods"
  },
  "list": {
    "heading": "Open Tournaments",
    "empty": "No tournaments right now.",
    "loading": "Loading tournaments…",
    "view": "View",
    "entrants_one": "{{count}} entrant",
    "entrants_few": "{{count}} entrants",
    "entrants_many": "{{count}} entrants",
    "entrants_other": "{{count}} entrants"
  },
  "create": {
    "heading": "Create Tournament",
    "nameLabel": "Tournament name",
    "namePlaceholder": "Friday Night Magic",
    "arityLabel": "Players per match",
    "arityHint": "2 is head-to-head; 4 is a standard Commander pod.",
    "bracketLabel": "Bracket",
    "totalRoundsLabel": "Rounds",
    "totalRoundsAuto": "Automatic",
    "scoringLabel": "Match points",
    "winPointsLabel": "Win",
    "drawPointsLabel": "Draw",
    "lossPointsLabel": "Loss",
    "submit": "Create Tournament",
    "submitting": "Creating…"
  },
  "join": {
    "heading": "Join by Code",
    "codeLabel": "Tournament code",
    "codePlaceholder": "Enter tournament code",
    "displayNameLabel": "Display name",
    "displayNamePlaceholder": "Your name at the table",
    "submit": "Join",
    "submitting": "Joining…",
    "joined": "You are entered in this tournament."
  },
  "detail": {
    "loading": "Loading tournament…",
    "organizerControls": "Organizer controls",
    "startRound": "Start Round",
    "startRoundBusy": "Starting…",
    "endTournament": "End Tournament",
    "endTournamentBusy": "Ending…",
    "endTournamentConfirm": "End this tournament? Remaining rounds will not be played.",
    "drop": "Drop",
    "dropBusy": "Dropping…",
    "dropConfirm": "Drop from this tournament? You cannot rejoin.",
    "reportResult": "Report Result",
    "yourPairing": "Your Match",
    "noPairing": "You have no match this round."
  },
  "standings": {
    "heading": "Standings",
    "empty": "No standings yet.",
    "rank": "#",
    "player": "Player",
    "matchPoints": "Points",
    "matchPointsTitle": "Match points",
    "matchesPlayed": "Played",
    "matchesPlayedTitle": "Matches played, excluding byes",
    "byes": "Byes",
    "byesTitle": "Rounds received as a bye",
    "tiebreaks": {
      "headToHead": {
        "opponentsMatchWinPct": "OMW%",
        "opponentsMatchWinPctTitle": "Opponents' match-win percentage",
        "gameWinPct": "GW%",
        "gameWinPctTitle": "Game-win percentage",
        "opponentsGameWinPct": "OGW%",
        "opponentsGameWinPctTitle": "Opponents' game-win percentage"
      },
      "multiplayer": {
        "matchWinPct": "MW%",
        "matchWinPctTitle": "Match-win percentage",
        "opponentsAvgMatchPoints": "OAMP",
        "opponentsAvgMatchPointsTitle": "Opponents' average match points",
        "opponentsMatchWinPct": "OMW%",
        "opponentsMatchWinPctTitle": "Opponents' match-win percentage"
      }
    }
  },
  "pairings": {
    "heading": "Pairings",
    "empty": "No pairings yet.",
    "round": "Round {{round}}",
    "table": "Table {{id}}",
    "pending": "Pending",
    "versus": "vs"
  },
  "outcome": {
    "bye": "Bye",
    "forfeit": "Forfeit — {{winner}}",
    "decisive": "{{winner}} won",
    "draw": "Draw",
    "gameWins": "{{name}} {{wins}}"
  },
  "report": {
    "heading": "Report Result",
    "winnerLabel": "Winner",
    "drawOption": "Draw",
    "gameWinsLabel": "Game wins",
    "gameWinsFor": "Game wins for {{name}}",
    "submit": "Submit Result",
    "submitting": "Submitting…",
    "cancel": "Cancel"
  },
  "errors": {
    "notOrganizer": "You are not the organizer of this tournament.",
    "notEntered": "You are not entered in this tournament.",
    "serverRejected": "The server rejected that: {{message}}",
    "timedOut": "The server did not respond. Try again.",
    "connectionLost": "Lost connection to the lobby. Check your server address.",
    "aborted": "That request was cancelled.",
    "notFound": "No tournament with that code."
  }
}
```

**Design notes:**

- **`status.*` and `bracket.*` use the wire spellings verbatim, and those two groups alone support direct indexing.** `TournamentStatus` is a flat string union (`adapter/types.ts:4546-4550`); `BracketShape` is `"Swiss"|"SingleElimination"` (`:4553`). Phase 4 can write ``t(`status.${summary.status}`)``/``t(`bracket.${summary.bracket}`)`` directly. This claim is exact and does not extend beyond these two groups.
- **`outcome.*` and `standings.tiebreaks.{headToHead,multiplayer}.*` are keyed one-per-member under the same "mirror the union" principle, but they are NOT directly indexable.** `PairingOutcome` is `"Bye"|{Forfeit:{...}}|{Reported:PodOutcome}` (`types.ts:4561-4579`, doubly nested for a reported decisive result); `Tiebreaks` is `{HeadToHead:{...}}|{Multiplayer:{...}}` (`:4587-4600`). No flat string to interpolate. Consumed through phase 4's chartered `outcomeLabelKey`/`tiebreakColumns` exhaustive-switch helpers instead. Key segments are deliberately camelCase (not the wire's PascalCase) — the visible signal they were never designed for interpolation; the switch is the mapping, compiler-checked rather than stringly-typed.
- `errors.{notOrganizer,notEntered}` verbatim the phase-2 strings (B2).
- `errors.*` covers all four `TournamentRpcFailureReason` members plus both `TournamentRole` refusals plus `notFound`. Only `serverRejected` interpolates.
- `arity.pod` deliberately uses `{{seats}}`, not `{{count}}` (see §7.3 item 3).
- `labels.roundOf` defined once, shared by list item and detail header.
- Exactly one `{{count}}` family (`list.entrants`). `TournamentSummary.player_count` is active entrants, not `view.players.length` (`types.ts:4662-4669`) — phase 4's own hostile fixture covers the distinction.
- No `page.title` key; the landing-page title is `page.landingTitle`, detail subtitle is `page.detailDescription`.

### 5.3 — Create the six mirrors

`client/src/i18n/locales/{es,fr,de,it,pt,pl}/tournament.json` — same structure, same key order, same placeholder sets, all keys translated.

**Mandatory verbatim values — four-form family (`list.entrants_{one,few,many,other}`), all 7 catalogs:**

| locale | `_one` | `_few` | `_many` | `_other` |
|---|---|---|---|---|
| en | `{{count}} entrant` | `{{count}} entrants` | `{{count}} entrants` | `{{count}} entrants` |
| es | `{{count}} participante` | `{{count}} participantes` | `{{count}} participantes` | `{{count}} participantes` |
| fr | `{{count}} participant` | `{{count}} participants` | `{{count}} participants` | `{{count}} participants` |
| de | `{{count}} Teilnehmer` | `{{count}} Teilnehmer` | `{{count}} Teilnehmer` | `{{count}} Teilnehmer` |
| it | `{{count}} partecipante` | `{{count}} partecipanti` | `{{count}} partecipanti` | `{{count}} partecipanti` |
| pt | `{{count}} participante` | `{{count}} participantes` | `{{count}} participantes` | `{{count}} participantes` |
| pl | `{{count}} uczestnik` | `{{count}} uczestnicy` | `{{count}} uczestników` | `{{count}} uczestnika` |

**Placeholder-bearing keys — identical placeholder set required in every locale:**

| key | es | fr | de | it | pt | pl |
|---|---|---|---|---|---|---|
| `page.detailDescription` | `Torneo {{code}}` | `Tournoi {{code}}` | `Turnier {{code}}` | `Torneo {{code}}` | `Torneio {{code}}` | `Turniej {{code}}` |
| `labels.code` | `Código {{code}}` | `Code {{code}}` | `Code {{code}}` | `Codice {{code}}` | `Código {{code}}` | `Kod {{code}}` |
| `labels.roundOf` | `Ronda {{current}} de {{total}}` | `Ronde {{current}} sur {{total}}` | `Runde {{current}} von {{total}}` | `Turno {{current}} di {{total}}` | `Rodada {{current}} de {{total}}` | `Runda {{current}} z {{total}}` |
| `labels.created` | `Creado {{date}}` | `Créé {{date}}` | `Erstellt {{date}}` | `Creato {{date}}` | `Criado {{date}}` | `Utworzono {{date}}` |
| `arity.pod` | `Mesas de {{seats}} jugadores` | `Tables de {{seats}} joueurs` | `Tische mit {{seats}} Spielern` | `Tavoli da {{seats}} giocatori` | `Mesas de {{seats}} jogadores` | `Stoły po {{seats}} graczy` |
| `pairings.round` | `Ronda {{round}}` | `Ronde {{round}}` | `Runde {{round}}` | `Turno {{round}}` | `Rodada {{round}}` | `Runda {{round}}` |
| `pairings.table` | `Mesa {{id}}` | `Table {{id}}` | `Tisch {{id}}` | `Tavolo {{id}}` | `Mesa {{id}}` | `Stół {{id}}` |
| `outcome.forfeit` | `Incomparecencia — {{winner}}` | `Forfait — {{winner}}` | `Nichtantritt — {{winner}}` | `Forfait — {{winner}}` | `Ausência — {{winner}}` | `Walkower — {{winner}}` |
| `outcome.decisive` | `Ganó {{winner}}` | `{{winner}} a gagné` | `{{winner}} hat gewonnen` | `Ha vinto {{winner}}` | `{{winner}} venceu` | `Wygrał {{winner}}` |
| `outcome.gameWins` | `{{name}} {{wins}}` | `{{name}} {{wins}}` | `{{name}} {{wins}}` | `{{name}} {{wins}}` | `{{name}} {{wins}}` | `{{name}} {{wins}}` |
| `report.gameWinsFor` | `Partidas ganadas de {{name}}` | `Manches gagnées par {{name}}` | `Gewonnene Spiele von {{name}}` | `Partite vinte da {{name}}` | `Jogos vencidos por {{name}}` | `Wygrane gry gracza {{name}}` |
| `errors.serverRejected` | `El servidor lo rechazó: {{message}}` | `Le serveur a refusé : {{message}}` | `Der Server hat das abgelehnt: {{message}}` | `Il server ha rifiutato: {{message}}` | `O servidor recusou: {{message}}` | `Serwer odrzucił żądanie: {{message}}` |

**Terminology glossary for remaining free-prose keys:**

| en | es | fr | de | it | pt | pl |
|---|---|---|---|---|---|---|
| tournament | torneo | tournoi | Turnier | torneo | torneio | turniej |
| round | ronda | ronde | Runde | turno | rodada | runda |
| standings | clasificación | classement | Tabelle | classifica | classificação | klasyfikacja |
| pairing | emparejamiento | appariement | Paarung | accoppiamento | emparelhamento | parowanie |
| bye | bye | bye | Freilos | bye | bye | wolny los |
| drop | retirarse | se retirer | zurückziehen | ritirarsi | desistir | wycofać się |
| organizer | organizador | organisateur | Organisator | organizzatore | organizador | organizator |
| match points | puntos de partida | points de match | Matchpunkte | punti partita | pontos de partida | punkty meczowe |
| entrant | participante | participant | Teilnehmer | partecipante | participante | uczestnik |

Tiebreak abbreviations (`OMW%`, `GW%`, `OGW%`, `MW%`, `OAMP`) are not translated. The `*Title` tooltip keys are translated.

### 5.4 — Add `nav.tournament` to all 7 `client/src/i18n/locales/*/menu.json`

Surgical insertion into the existing `nav` group (`en/menu.json:312-323`), after `"decks"`:

| locale | value |
|---|---|
| en | `Tournaments` |
| es | `Torneos` |
| fr | `Tournois` |
| de | `Turniere` |
| it | `Tornei` |
| pt | `Torneios` |
| pl | `Turnieje` |

Inert until phase 5. Do not touch `navItems.tsx`.

### 5.5 — Registration surface 1: `client/src/i18n/index.ts`

```ts
export const NAMESPACES = [
  "common",
  "menu",
  "game",
  "deck-builder",
  "draft",
  "settings",
  "multiplayer",
  "replay",
  "tournament",
] as const;
```

### 5.6 — Registration surface 2: `client/src/i18n/react-i18next.d.ts`

```ts
import type settings from "./locales/en/settings.json";
import type tournament from "./locales/en/tournament.json";
```

and inside `CustomTypeOptions.resources`, after `replay`:

```ts
      replay: typeof replay;
      tournament: typeof tournament;
```

Do not change `declare module "react-i18next"` to `declare module "i18next"` — the C2 repair, out of scope.

### 5.7 — Registration surface 3: `client/src/test-setup.ts`

```ts
import multiplayer from "./i18n/locales/en/multiplayer.json";
import tournament from "./i18n/locales/en/tournament.json";
```

```ts
  ns: ["common", "menu", "game", "deck-builder", "draft", "settings", "multiplayer", "tournament"],
```

```ts
      multiplayer,
      tournament,
    },
```

**Both edits are mandatory, but not equally observable — do not conclude from a green suite that both landed.** Per R4, only the `resources.en` entry decides whether `t("tournament:…")` resolves; the `ns[]` array entry is a preload hint this synchronous harness never consults, so §5.9's test cannot catch its absence. Add it anyway.

**S5 decision point, resolved explicitly:** `test-setup.ts` will now register 8 namespaces while `NAMESPACES` holds 9 — `replay` still missing. Add `tournament` only; do not repair `replay`; do not add a "the two lists agree" assertion.

### 5.8 — The `FOUR_FORM_STEMS` namespace parameterization

**File:** `client/src/i18n/__tests__/localeParity.test.ts`.

**Edit 1 — retype the constant and convert all 16 entries (`:137-154`), then append the tournament entry:**

```ts
/**
 * Plural families that must carry all four Polish forms, paired with the
 * namespace file each stem lives in. Polish is the locale whose grammar needs
 * `_one`/`_few`/`_many`/`_other`, but i18next resolves plurals by looking up
 * SUFFIXED keys and the key-parity case below is exact in both directions — so
 * every catalog, English included, must carry all four. The loop runs over
 * `[SOURCE, ...locales]` precisely so English is pinned too: key parity is
 * English-driven and cannot catch an English family that was never authored.
 */
const FOUR_FORM_STEMS: ReadonlyArray<{ ns: string; stem: string }> = [
  { ns: "draft.json", stem: "intro.quantity.packsOpened" },
  { ns: "draft.json", stem: "intro.quantity.cardsContained" },
  { ns: "draft.json", stem: "intro.quantity.packSizeEntry" },
  { ns: "draft.json", stem: "intro.quantity.minimumDeckCards" },
  { ns: "draft.json", stem: "intro.packPassing" },
  { ns: "draft.json", stem: "sealedOpening.subtitle" },
  { ns: "draft.json", stem: "workspace.count.deck" },
  { ns: "draft.json", stem: "workspace.count.sideboard" },
  { ns: "draft.json", stem: "workspace.sideboard.expand" },
  { ns: "draft.json", stem: "workspace.pool.filter.combined" },
  { ns: "draft.json", stem: "workspace.pool.filter.deck" },
  { ns: "draft.json", stem: "workspace.pool.filter.sideboard" },
  { ns: "draft.json", stem: "workspace.headers.accessible" },
  { ns: "draft.json", stem: "limitedDeck.spellCount" },
  { ns: "draft.json", stem: "limitedDeck.landCount" },
  { ns: "draft.json", stem: "seat.activePackCount" },
  { ns: "tournament.json", stem: "list.entrants" },
] as const;
```

**Edit 2 — restructure the loop (`:199-208`) so `load` runs per entry:**

```ts
  it("keeps_all_plural_families_complete_in_every_locale", () => {
    for (const locale of [SOURCE, ...locales]) {
      for (const { ns, stem } of FOUR_FORM_STEMS) {
        const target = load(locale, ns);
        for (const suffix of ["one", "few", "many", "other"]) {
          expect(target[`${stem}_${suffix}`], `${locale}:${ns}:${stem}_${suffix}`).toEqual(expect.any(String));
        }
      }
    }
  });
```

**Explicitly NOT touched:** `WORKSPACE_SHELL_KEYS`, `keeps_workspace_keys_in_phase_after_pin_and_actions_removal`, `resolves_polish_one_few_many_and_other_without_fallback`, `KNOWN_PLACEHOLDER_GAPS`, the discovery guard, the two `describe.each` parity cases, the stale-gap case.

**Behavior preservation, measured:** probe 3 confirmed the test still passes with the refactor plus the tournament entry, whole file green at 114 tests. Measured cost: `load` now runs 17× per locale instead of 1×; measured test duration 34-38ms — memoizing declined.

### 5.9 — NEW: the committed registration test

**File:** `client/src/i18n/__tests__/namespaceRegistration.test.ts` (new file).

**Why this file must exist.** C2 concluded that with the type oracle inert, this phase's load-bearing deliverable is the runtime registration in `test-setup.ts`. The gap is real, demonstrated by direct experiment: deregistering the existing `multiplayer` namespace from `test-setup.ts` (both the `ns` array and the `resources.en` object) leaves 179/179 green across both of this phase's gates, because neither reaches that instance. `tsc` is inert per C2. An executor who forgot §5.7 would see every command in §6 report success, and the resulting failure would be silent (bare key path, `ns:` prefix stripped) — the same failure `replay` is living proof of.

**Placement.** Beside `localeParity.test.ts` in `client/src/i18n/__tests__/`.

**Mechanism.** `test-setup.ts:25` calls `i18n.use(initReactI18next).init({...})` on the default `i18next` export, not a `createInstance()`. So `import i18n from "i18next"` in a test file yields the very instance the harness configured — the house idiom established by `DebugLibraryViewer.focus.test.tsx:2`.

**Content:**

```ts
import i18n from "i18next";
import { describe, expect, it } from "vitest";

/**
 * Guards the one registration surface nothing else in this repo reaches.
 *
 * `resources.test.ts` and `localeParity.test.ts` both read the catalog files
 * off disk — the latter builds its own `createInstance()` — so neither observes
 * whether `test-setup.ts` actually registered a namespace. `react-i18next.d.ts`
 * cannot cover the gap either: i18next v26 declares `CustomTypeOptions` in
 * module "i18next" while this repo augments module "react-i18next", so that
 * oracle is inert and `tsc` proves nothing about key resolution. Measured:
 * deregistering an already-shipped namespace from `test-setup.ts` leaves all
 * three of those green, and the failure it lets through is silent — an
 * unregistered lookup renders its bare key path with the `ns:` prefix stripped,
 * which reads as plausible UI text. `replay` is the live instance.
 *
 * `test-setup.ts` initialises the DEFAULT `i18next` export (not a
 * `createInstance()`), so importing it here is importing the configured harness
 * instance — the same idiom as
 * `components/chrome/__tests__/DebugLibraryViewer.focus.test.tsx`.
 */
describe("test-harness i18n registration", () => {
  it("resolves_the_tournament_namespace_through_the_test_harness_instance", () => {
    // Reach-guard: prove the negative below is not vacuous. A namespace that is
    // registered nowhere resolves to its bare key path, `ns:` prefix stripped.
    expect(i18n.t("definitelyNotARealNamespace:someKey")).toBe("someKey");

    // The claim: `tournament` IS registered, so this is NOT the bare key path.
    expect(i18n.t("tournament:list.heading")).not.toBe("list.heading");
  });
});
```

**Both assertions are measured** (probe 12, pristine tree):

| assertion | value today (tournament unregistered) | value after §5.7 |
|---|---|---|
| `i18n.t("definitelyNotARealNamespace:someKey")` | `"someKey"` — passes | `"someKey"` — passes |
| `i18n.t("tournament:list.heading")` | `"list.heading"` — fails | `"Open Tournaments"` — passes |

**Authoring constraints:**
- Assert `.not.toBe("list.heading")`, not `.toBe("Open Tournaments")` — the equality would restate the catalog and stay green through the deregistration experiment.
- Keep both assertions in one `it`.
- Do not add `beforeEach`/`afterEach` — the test mutates nothing.
- Do not import any catalog JSON in this file.
- Honest scope, per R4: catches complete omission and a missing `resources.en` entry; does NOT catch a missing `ns[]` array entry alone.

### 5.10 — Do NOT do (scope fence)

No `t()` call outside §5.9's test; no edit to `multiplayerStore.ts`; no edit to `navItems.tsx`/`navIcons.tsx`/`navItems.test.ts`/`App.tsx`; no component or page file; no repair of the `replay` drift (including: do NOT generalize §5.9's test into a loop over `NAMESPACES`, which would go red on `replay`); no repair of the C2 type-oracle drift; no "the two ns lists agree" assertion; nothing added to `KNOWN_PLACEHOLDER_GAPS`; no touch to `LOBBY_PROTOCOL_VERSION`/`check-protocol-version.mjs`; no edit to `vitest.config.ts`; no `cargo` command.

---

## §6 — Verification Matrix

Environment (S9, corrected by C1): `node_modules` is present; run `pnpm install --frozen-lockfile` only if resolution fails. `./scripts/tilt-wait.sh` returns exit 3 — never a build failure.

| # | Claim | Test | Revert-failing assertion | Hostile fixture / reach-guard | Status |
|---|---|---|---|---|---|
| V1 | New namespace covered by `resources.test.ts`, no test edit | existing gates | drop a leaf from `de/tournament.json` → names it | Measured (probe 1): `de` missing `page.landingTitle` → named. Count rises 179→198 | auto |
| V2 | `localeParity.test.ts` key parity, exact both directions | existing case | remove/add a key → named | Measured (probe 1+4b): deleting `_few`/`_many` from all 7 keeps this green | auto |
| V3 | Placeholder parity | existing case | translate without `{{code}}` → names key+sets | Measured (probe 1) | auto |
| V4 | `FOUR_FORM_STEMS` consults each entry's own `ns`, pins English too | `keeps_all_plural_families_complete_in_every_locale` | flip `ns` → 1 test fails (R1) | Hostile (probe 4b): delete forms from all 7 → reds while key parity green. Control (4c): unregistered stem → 198 green | must run |
| V5 | Registration triple compiles; import resolves | `type-check` | delete `en/tournament.json` → import fails | Stated at true strength (C2): proves compilation only | must run |
| V6 | Draft four-form coverage bit-identical after refactor | whole file | all 16 draft entries retain `ns:"draft.json"` | Baseline 179→198 | must run |
| **V7** | **`test-setup.ts`'s registration makes `tournament` resolve through the test-runtime instance** | **NEW — `namespaceRegistration.test.ts`** | **remove `tournament` from `resources.en` → `"list.heading"`, test reds** | Paired reach-guard: fake ns → `"someKey"`. Positive control: `multiplayer:page.deckRejected` resolves. Stated non-coverage (R4): a lone missing `ns[]` entry still passes | **must run** |
| V8 | Refactored + new test file pass lint | `lint` | — | not probed, mandatory | must run |
| V9 | Protocol version unmoved | protocol script | — | — | must run |

**Commands, in order:**
```
cd client
pnpm exec vitest run src/i18n/__tests__/localeParity.test.ts src/i18n/resources.test.ts src/i18n/__tests__/namespaceRegistration.test.ts   # expect 3 files, 199 tests, green
pnpm run lint
pnpm run type-check
```

**Expected test-count delta: 179 → 199**, across 3 files. 198 from the two auto-discovering gates (+19: +12 locale/case combos, +7 encoding); +1 from the new file (one `it`, two `expect`s — nothing auto-discovers it into a larger count).

**Executor sanity check:** run the new file alone before applying §5.7 and confirm it fails; then apply §5.7 and confirm it passes. A test green in both states is not wired to the instance and must be fixed before the commit lands.

---

## §7 — Deferrals, seams, and reporting

### 7.1 Deferrals owned by this phase

**`DEFERRED(phase 4)` — `t()` routing.** Wording correction (C3): assert no rendered text node equals a bare dotted key path (e.g. `list.heading`, `page.landingTitle`) — not `tournament.list.heading`, which cannot occur.

**`DEFERRED(phase 5)` — key-set completeness across mounted pages.** Same correction. Also: the runtime mechanism it depends on is `test-setup.ts`'s registration, landed in §5.7 and now committed as a standing gate in §5.9 — if phase 5's page-level assertions ever go red across every string at once, `namespaceRegistration.test.ts` localizes the cause to registration rather than the pages.

Interim structural verification for both: green tree, both parity gates green at 198, `namespaceRegistration.test.ts` green (199 total), `tsc` exit 0, `eslint` clean.

### 7.2 Deferral allowlist honored (charter)

Every consumer of the namespace → phases 4 and 5. Catalog not frozen here (S4).

### 7.3 Findings to report — NOT to repair

1. **S5 — `replay` missing from `test-setup.ts`.** Pre-existing, deliberately unrepaired. §5.9's new test is the shape that would catch it — generalizing it to loop over `NAMESPACES` would red immediately on `replay`, which is exactly why §5.10 forbids doing so in this phase and exactly what a `replay` repair PR should do.
2. **C2 — the type oracle is inert.** Measured repair cost: 136 errors across 66 files. Recommend a standalone PR.
3. **The four-form gate has two escape hatches, both requiring author discipline, neither closed.** First (measured, probe 4c): parameterizing `FOUR_FORM_STEMS` closes the English hole only if the author remembers to register the stem. Second (disclosed here, opened by this plan's own §5.1 rule 4): because the gate keys off the reserved placeholder name `{{count}}`, an author can bypass the four-form requirement entirely by naming the placeholder something else — `{{seats}}`, `{{total}}`, `{{n}}` — regardless of whether the sentence is grammatically a count. `arity.pod` uses that hatch correctly and by design (it reads as a descriptive "N-player pods", not a countable-noun sentence), but nothing mechanical distinguishes that legitimate use from an author dodging 28 values. A fully auto-discovering variant would close hatch 1; hatch 2 is inherent to keying off the placeholder name and would need a different signal (e.g. reviewing count-bearing prose) to close.
4. **`client/i18next-parser.config.js` omits `pl`.** Harmless, noted in passing.
5. **S9's "`node_modules` absent" is stale** (C1).
6. **(new) Neither auto-discovering locale gate can observe `test-setup.ts`.** Demonstrated: deregistering an already-shipped namespace leaves 179/179 green. This phase closes that hole for `tournament` only; the other eight namespaces remain uncovered — the natural companion to finding 1's `replay` repair.

### 7.4 Seams touched

S4 fully discharged. S5 decision point resolved, drift left intact. S8 untouched, re-verified. S9 applied with C1's correction. S6/S7 not touched.

### 7.5 Commit

One commit, all files together.

```
feat(client): register the tournament i18n namespace (PR 4/5, phase 3)

Adds the `tournament` namespace across all three registration surfaces
(NAMESPACES, react-i18next.d.ts, test-setup.ts), authors the English
catalog and its six locale mirrors, and adds nav.tournament to menu.json
so phase 5's nav item has a label.

Parameterizes FOUR_FORM_STEMS in localeParity.test.ts by namespace
({ns, stem} pairs; all 16 existing entries keep ns: "draft.json", so
draft coverage is bit-identical) and registers list.entrants under it.
Without this the four-form Polish invariant could only be enforced for
draft.json: key parity is English-driven, so English authoring only
_one/_other passes green while Polish plurals break in production.
Measured: deleting _few/_many from all seven catalogs leaves key parity
green and reds only this case.

Adds i18n/__tests__/namespaceRegistration.test.ts, which asserts through
the test-harness i18next instance that `tournament` resolves, paired with
a reach-guard that an unregistered namespace returns its bare key path.
Nothing else in the repo covers that surface: both locale gates read the
catalogs off disk (localeParity builds its own createInstance), and the
key-typing oracle is inert (below) — measured, deregistering an existing
namespace from test-setup.ts leaves all of them green, and the resulting
failure is silent because an unregistered lookup renders the bare key
path with the `ns:` prefix stripped.

Known, deliberately unrepaired (reported, not fixed here):
- test-setup.ts still omits `replay` (pre-existing drift; adding
  `tournament` alone is the charter's explicit decision). The new test is
  deliberately scoped to `tournament` rather than looping NAMESPACES,
  which would red on that drift.
- react-i18next.d.ts augments module "react-i18next", but i18next v26
  declares CustomTypeOptions in module "i18next", so the key-typing
  oracle is inert. Repair measures at 136 errors across 66 files and
  belongs in its own PR.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DMa6DrxXyFHBdGxz3uLgvM
```

---

## §8 — Ready-for-review summary

| | |
|---|---|
| Units | 2 — T1 fires |
| Source scope-paths | 5 grouped (17 ungrouped) — T2 does not fire |
| Phase-fit | conjunction does not fire |
| New files | 7 (`locales/*/tournament.json`) + 1 test file (excluded from T2) |
| Modified files | 10 + 1 test file (excluded from T2) |
| New test files | 1 — `i18n/__tests__/namespaceRegistration.test.ts`, closing V7 |
| Expected test delta | 179 → 199 (198 auto-discovered, +1 new) |
| Rust touched | none |
| CR annotations | N/A |
| Premise corrections | C1 `node_modules` present; C2 type oracle inert; C3 missing/unregistered keys render without ns prefix |
| Refinements | R1 one test not four; R2 label needs `ns`; R3 no unused-key gate; R4 only `resources.en` is runtime-observable |
