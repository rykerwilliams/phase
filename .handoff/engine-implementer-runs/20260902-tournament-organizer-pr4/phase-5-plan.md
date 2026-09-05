# Phase 5 of 5 — Pages, routing, navigation (TERMINAL) — Implementation Plan

**Revision:** 3 — fixes round 2's M1 (a **documentation-completeness** finding, not a design decision: two doc comments still assert the pre-correction *organizer*-authority reading that §0.2 disproves, and neither was flagged — one is in-scope and is now amended by §5.1 item 7, the other is in a frozen file and is now flagged as follow-up in §7.4) plus m2–m5. Everything from revision 2 is preserved unchanged: sizing (4 units / 6 source scope-paths — revision 3 adds no code, only a doc-comment clause inside an already-counted file), the player-vs-organizer authority correction, revision 2's own M1 fix (`isActiveEntrant` + both `canPlayerAct` gates + V22/V22b + RC9/RC10), the icon-asset finding, the deferral audit, the run-level completeness check, the component contracts, and the rest of the verification matrix.

**Revision 2** fixed round 1's M1 (the plan's own authorization thesis was applied incompletely: the **`dropped`** conjunct was quoted in §0.2 and then dropped from the binding table and both §5.5 gates) plus m2–m7. See §8 for both change logs.
**Mode:** `/engine-planner` phase-plan mode (charter: `<run-root>/phase-charter`, phase 5 entry, lines 182–213; seams S1–S9).
**Run:** PR 4/4 of the tournament-organizer rollout, `phase-rs/phase#7718`.
**Worktree:** `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend` · branch `feat/tournament-organizer-pr4-frontend`.
**PHASE_BASE_SHA:** `b34de3f09ae0c65a5920eb28687ffa6bc0a152e7` (phase 4's accepted fix-round candidate). **Verified:** `git rev-parse HEAD` == `b34de3f09…`, `git status --porcelain` empty at plan time and again after every probe.

**This is the terminal phase.** Its deferral list is empty by construction. Everything phases 1–4 attributed to phase 5 is discharged below, or is explicitly declined with reasoning (§7.2), or is named as out-of-scope follow-up work for the PR body (§7.5). Nothing is deferred to a phase 6, because there is no phase 6.

---

## §0 — Step 0: premise verification

### 0.1 No card, no Oracle text, no CR rule is involved

Per this run's established convention (entries 14, 22, 28, 36 of the phase-fit log, all recording "zero CR annotations, N/A"): this phase touches **no Rust, no engine crate, no MTG game rules**. It is React routing and composition over a lobby-broker tournament surface. The `/engine-planner` Step-0 card gate ("fetch the card's real Oracle text from Scryfall") has no applicable subject.

The **substitute** gate — the one this run's phases have actually paid for repeatedly — is verifying **wire/broker behavior claims against real source**. Every phase of this run found a real correction there (phase 1: `TournamentUpdate` is both point-reply and broadcast; phase 2: the one-and-only `TournamentListUpdate` push; phase 3: the inert `react-i18next.d.ts` oracle; phase 4: the pairing-seat-count-not-arity gate). **Phase 5 found one too, and it is the most consequential of the five — see §0.2.**

### 0.2 PREMISE CORRECTION (blocking, found by probe) — reporting a result is **player**-authority and **seat**-scoped, not organizer-authority

The charter's phase-5 verification plan says (`phase-charter:204`):

> **Discharges phase 2's `DEFERRED(phase 5)` — organizer/player gating as rendered UI.** Controls appear only when the matching token is held for *that* code.

and the orchestrator's spawn brief paraphrases the deferral as "Organizer/player controls as rendered UI, gated on `viewerRoles(...).has("organizer")`". Taken literally — supplying `PairingsList`'s `onReport` when the viewer holds the **organizer** token — every report click would be **dead UI**, refused before it ever reached the wire.

**Verified against real source, three independent ways:**

1. **Store gate.** `multiplayerStore.ts`'s `reportMatchResult` calls `runGatedTournamentRpc(get, code, "player", …)` — role `"player"`, not `"organizer"`.
2. **Wire helper.** `services/tournamentClient.ts`'s `reportMatchResultOver` takes a `playerToken` and sends `player_token`, and its doc comment already says *"player-gated — the token must belong to a player seated in this pairing."*
3. **Broker.** `handle_report_match_result` (`crates/lobby-broker/src/broker.rs:1211-1247`) calls `authorize_player(&code, &player_token)` and then, separately, refuses a reporter **not seated in this pairing** (`"Player {reporter} is not seated in pairing {pairing_id}"`). Being *an* entrant is explicitly not enough.

**`authorize_player` enforces three conjuncts, not one — enumerated here because every one of them has to be mirrored by a UI gate or the affordance is dead.** Read verbatim from `crates/lobby-broker/src/broker.rs`'s `authorize_player` (its body is short; cited by symbol rather than line number so this claim survives the next edit above it):

| # | Broker conjunct | Refusal text | Client-side mirror |
|---|---|---|---|
| **C1** | the presented token resolves to an entrant of this code | `"Invalid player token for tournament {code}"` | `viewerRoles(credential).has("player")` — token *possession*, read off `tournamentCredentials[code]` |
| **C2** | **that entrant has not dropped** (`if player.dropped { return Err(…) }`) | `"Player has dropped from tournament {code}"` | **`isActiveEntrant(view, credential?.playerKey)` — new in §4.3, revision 2's M1 fix** |
| **C3** | *(report only, enforced by the caller not by `authorize_player`)* the entrant is seated in **this** pairing | `"Player {reporter} is not seated in pairing {pairing_id}"` | `myPairing(view, playerKey)` — phase 4's export; only its result is ever handed `onReport` |

`authorize_player`'s own doc comment names all three as *"[t]hree distinct `Err` shapes — missing tournament, unusable token, dropped entrant"*, and explains why C2 exists at all: *"there is a real, reachable window in which a dropped seat could settle a match it is no longer in."*

**Revision 1 quoted C2 and then failed to apply it.** Its binding table and both of §5.5's gates checked only `roles.has("player")` — i.e. C1 alone. That produces **two reachable dead affordances**, both confirmed against real Rust source:

**(a) The Drop button stays rendered after a successful drop.** `tournamentCredentials[code]` is cleared only on `TournamentRemoved` (`forgetTournamentCredential`), never on a successful drop, so `roles.has("player")` stays `true` forever afterwards. But a second drop is **deliberately and permanently refused** — `handle_drop_from_tournament`'s own comment (`broker.rs:1281-1290`) says so at length: re-running `drop_player` *"changes no player state and can settle no further pairing … while still bumping `last_activity_at` — i.e. its only observable effect is to push back the staleness reaper for an event this caller has left. Refusing is both the honest answer … and the one that does not hand a departed entrant a liveness lever."* So immediately after the single most common player action, revision 1's page kept showing a live Drop button whose only possible outcome is an `errors.notEntered` alert.

**(b) The Report button stays dead for a dropped player in a pod.** `TournamentManager::drop_player` (`crates/lobby-broker/src/tournament.rs`) scans the dropper's unresolved pairings and auto-forfeits **only** when exactly one active seat remains — the `if let (Some(survivor), None) = (active.next(), active.next())` guard. In a 4-seat pod with ≥2 active seats still remaining, that guard is false: the pairing keeps `outcome: null`, and the dropped player **stays in `pairing.players`**, because `validate_match_result`'s own comment states the rule — *"`pairing.players` keeps its original seat list (a drop does not retroactively rewrite history), so membership alone does not close this gap."* Consequently `myPairing` still matches (C3 passes), `isReportable(null)` is `true`, and revision 1 offered a Report button to a viewer that `authorize_player` refuses at C2 every time. `validate_match_result` independently refuses to credit a dropped winner, which confirms the broker treats the two as separate gates — but that is a *server-side* backstop, not a reason to render the button.

**Both are fixed by adding the C2 conjunct to both gates (§5.5 items 4 and 5), backed by `isActiveEntrant` (§4.3), the hostile fixture V22, and revert-checks RC9/RC10.** Nothing about this widens scope: `PlayerSummary.dropped` is already mirrored on the wire (`client/src/adapter/types.ts`'s `PlayerSummary`, `dropped: boolean`, carried on both `TournamentView.players` and per-seat on `TournamentPairingView.players`), `labels.dropped` already exists in all 7 catalogs **and is already rendered** by phase 4's `TournamentStandingsTable` as a per-row chip, and the fix lands inside `tournamentPageState.ts` + `TournamentPage.tsx`, both already counted in §4.11. **Zero new scope-paths, zero new catalog keys, zero new units.**

**Probe P4 (measured, not reasoned).** Scratch vitest file against the real store with only the `openPhaseSocket` transport faked (phase 2's harness shape), run and then deleted:

```
P4  report-as-organizer  => {"ok":false,"reason":"not_authorized","role":"player",
                             "message":"You are not entered in this tournament."}
P4  ReportMatchResult frames sent => 0
P4  reach-guard StartTournamentRound frames => 1     ← positive control: the SAME
                                                       organizer credential does
                                                       authorize a start, so the
                                                       instrument is not refusing
                                                       everything
P4b player-credential ReportMatchResult frames => 1
```

**Consequence for this phase's design (binding):**

| Action | Broker conjuncts it must satisfy | UI gate (all conjuncts, none elided) | Rendered where |
|---|---|---|---|
| `startTournamentRound` | `authorize_organizer` only | `roles.has("organizer")` | Organizer control block |
| `endTournament` | `authorize_organizer` only | `roles.has("organizer")` | Organizer control block |
| `dropFromTournament` | **C1 + C2** (`authorize_player`) | `roles.has("player") && isActiveEntrant(view, credential?.playerKey)` | Player control block |
| `reportMatchResult` | **C1 + C2 + C3** (`authorize_player`, then the seat check) | `roles.has("player") && isActiveEntrant(view, credential?.playerKey)`, and `onReport` supplied **only** to the `[myPairing(...)]` list | **Only on the viewer's own current-round pairing** |

`authorize_organizer` has no dropped-equivalent — an organizer is not an entrant and cannot drop — which is why the two organizer rows are single-conjunct and are correct as revision 1 wrote them. The three player-facing conjuncts map 1:1 onto three client-side authorities of three different provenances, and that is deliberate: **C1 is token possession** (the credential map), **C2 is server state** (the `TournamentView`), **C3 is server state narrowed by identity** (`myPairing`). They are kept as three conjuncts rather than fused into one predicate precisely so the mapping to the broker's own structure stays legible in the diff — a reviewer can point at each gate and name the `Err` shape it prevents. The seat conjunct is what `myPairing(view, playerKey)` (phase 4's export) already computes. Phase 5 therefore supplies `onReport` **only** to a `PairingsList` rendering the viewer's own pairing, and **never** to the full-history list. This is not a workaround — it is the only shape the broker accepts, and it uses phase 4's components exactly as their prop contracts were written (`PairingsList`'s `onReport` doc even says *"Presence alone does NOT make a row reportable"*).

**One caveat on that quotation, so this plan is not silently unaware of it (round 2's M1(b)).** Only the *second* sentence of that doc comment is quoted above, and only the second sentence is correct. Its **first** sentence — *"Supplied by phase 5 only for a viewer holding the organizer credential"* — is the pre-correction premise this very section disproves. `PairingsList.tsx` is frozen (§7.5 item 4) and this is the terminal phase, so it **cannot be corrected here**; it is carried as an explicit flagged follow-up row in **§7.4** and must reach the final PR body. This is the only site in this plan that quotes that doc comment, and the quotation is to its second sentence only; §5.5 item 5 relies on the arm gate's *behavior*, never on the comment's first sentence.

**No structural foreclosure.** `PairingsList.tsx` is not in phase 5's scope, and it does not need to be: the component takes `pairings: readonly TournamentPairingView[]`, so a one-element array is a legal argument and the arm gate (`isReportable`) still applies to it. Nothing about phase 4's frozen contract has to change.

### 0.3 Second premise check — the missing nav icon asset (real, silent in tests)

The charter lists `client/src/components/chrome/navIcons.tsx` in phase 5's scope but never says what the icon *is*. Every existing nav icon is `sectionIcon("<file>", …)` → `<img src="/icons/sections/<file>.png">`. **Measured:** `client/public/icons/sections/` contains exactly `coverage, decks, draft, home, metagame, online, play, resume, settings` — **there is no `tournament.png`**, and this repo's tests run under happy-dom, which never fetches an `<img src>`, so a dangling reference would be **invisible to every test and broken only in production**.

Resolution (§5.3): author `TournamentNavIcon` as an **inline SVG** in `navIcons.tsx`, following `components/chrome/SparkleIcon.tsx` — an existing SVG glyph already rendered side-by-side with the PNG icons in both `Rail.tsx` and `TabBar.tsx`, with the same `className` opacity treatment. `navIcons.tsx`'s own module doc licenses this: *"For larger, color-tintable contexts prefer an SVG glyph."* Reusing an unrelated PNG (`metagame.png`) was considered and rejected: it depicts a different concept and `metagame` is not referenced by any component today, so borrowing it would create a false association.

### 0.4 Premise re-checks carried forward and re-verified against current source

| Claim (from an earlier phase) | Re-verified how | Verdict |
|---|---|---|
| `TournamentUpdate` is both `ToSelf` (only `handle_get_tournament`) and a `ToSubscribers` broadcast, with no request-vs-broadcast discriminator | Read `broker.rs:1175-1183`; re-read `tournamentClient.ts` module header part 4 | Holds |
| Four gated RPCs settle on the *broadcast*; `{ok:false}` is **not** a reliable rejection detector | `tournamentClient.ts` header parts 3–5; store's `runGatedTournamentRpc` doc | Holds — binds §4.6 |
| `handle_get_tournament` emits **no** `tournament_list_update()` | `broker.rs:1175-1183`; the 6 `tournament_list_update()` sites are `:576, :1130, :1169, :1207, :1310, :1335` | Holds — makes §4.7's re-seed loop-free |
| `handle_report_match_result` emits **no** list update | same census — `:1268`'s handler is absent from the six sites | Holds |
| Missing i18n keys render **without** the namespace prefix (`"list.heading"`, not `"tournament.list.heading"`) | `components/tournament/__tests__/tournamentTestUtils.ts` already encodes this (`RAW_KEY_PATH`) | Holds |
| The charter's `(?:Un)?SubscribeLobby` regex is broken (phase 1's erratum) | Not used anywhere in this phase — frame assertions use phase 2's **exact parsed-tag equality** `tally()` helper | N/A by construction |
| `test-setup.ts` registers the real `tournament` catalog | `src/test-setup.ts:29` — `ns: [... "multiplayer", "tournament"]` | Holds |
| `common:actions.cancel` / `common:actions.closeNamed` (used by `ReportResultDialog`) resolve | `en/common.json:3,6`; `common` is in `test-setup.ts`'s `ns` | Holds |
| `nav.tournament` exists in `menu` | `en/menu.json:319` inside the `nav` block; phase 3 mirrored all 7 | Holds |
| `errors.serverRejected` carries `{{message}}` in all 7 catalogs | grep count == 1 in `es/fr/de/it/pt/pl` + `en`; `localeParity.test.ts`'s placeholder-parity case is green today | Holds |

---

## §1 — Step 1: applicable skills

| Skill | Applies? | How it is honoured |
|---|---|---|
| **`/add-frontend-component`** | **YES — its later checklist phases fire here for the first time in this run** | Routing registration (§5.2), page mounting (§5.4/§5.5), nav registration (§5.3), i18n routing through `t()` (§5.4/§5.5), test coverage (§6). Phases 1–4 exercised only its "build the component" half. |
| `/oracle-parser`, `/add-engine-effect`, `/add-keyword`, `/add-trigger`, `/add-static-ability`, `/add-replacement-effect`, `/add-interactive-effect`, `/casting-stack-conditions`, `/add-ai-feature-policy`, `/add-card-data-pipeline`, `/card-test` | No | No engine, parser, AI, card-data or cast-pipeline surface is touched. |
| `/add-engine-variant` | No — **but the lens is applied anyway** | No engine enum is added. The one new client type (`ViewerRelation`, §4.3) is run through the parameterization / sibling-cluster / categorical-boundary filter in §4.3. |
| `/validate-cr-annotations` | Gate runs, result is N/A | §4.9. |

**`/add-frontend-component` self-maintenance note.** That skill asks for its directory table to be updated when a new component directory appears. `components/tournament/` was created in phase 4, which flagged this and chose **report-don't-edit** (the skill file is outside every phase's chartered scope in this run). Phase 5 creates **no new component directory** and takes the same posture: no skill-file edit. Recorded here so the decision is not silently re-litigated.

**Deferred checklist steps.** None. Every `/add-frontend-component` step that this run defers to a later phase has arrived at its landing phase. There is nothing to write `DEFERRED(phase n)` against.

---

## §2 — Step 2: analogous trace (hard gate)

**Traced feature: `MultiplayerPage` — the closest existing "page that owns view state, subscribes through `multiplayerStore`, and renders a list/detail split."**

Full trace path, followed end to end:

```
client/src/App.tsx:28                      lazy() chunk declaration
client/src/App.tsx:119                     <Route path="/multiplayer" element={<DevStrict><MultiplayerPage/></DevStrict>}/>
  └─ inside the <Route element={<AppShell/>}> layout route (:116-127)
client/src/components/chrome/AppShell.tsx  layout route: Rail + TabBar + <Outlet/>; owns the scene once
   ├─ :52                                  showStatusBanner = pathname === "/" || pathname === "/multiplayer"
   ├─ :86  <Rail/>                         → components/chrome/Rail.tsx:49  NAV_ITEMS.map(...)
   └─ :181 <TabBar/>                       → components/chrome/TabBar.tsx:33 NAV_ITEMS.map(...)
        └─ both call activeNavKey(useLocation().pathname)  → components/chrome/navItems.tsx:31
client/src/pages/MultiplayerPage.tsx:62    the page component
   ├─ :63    useTranslation("multiplayer")
   ├─ :69    useInShell()                  → suppresses its own <MenuParticles/> when embedded
   ├─ :86    useState<MultiplayerView>     ← VIEW STATE IS THE PAGE'S, not the store's
   ├─ :77-79 useMultiplayerStore((s)=>s.startHosting) etc.   ← per-action selectors
   ├─ :699   <ScreenChrome/>               → returns null inside the shell (ScreenChrome.tsx:47)
   ├─ :714   <MenuShell eyebrow/title/description/layout/contentWidthClass>
   └─ :782   <LobbyView key={`${serverAddress}:${lobbyRetryKey}`} …/>
client/src/components/lobby/LobbyView.tsx:115-191   THE SUBSCRIPTION IDIOM
   ├─ :119   let cancelled = false; let lobbyDetach = null;
   ├─ :128   (async () => { const detach = await subscribeLobby(cb);
   │ :134-137               if (cancelled) { detach?.(); return; }  ← the S3-flagged idiom
   │                                                                  (S3 is the shared-
   │                                                                  refcount/subscription
   │                                                                  seam; S2 is the
   │                                                                  unrelated `PairingView`
   │                                                                  naming collision)
   │                 if (detach === null) { onServerOffline?.(); return; }
   │                 lobbyDetach = detach; … })();
   └─ return () => { cancelled = true; ambientDetach?.(); lobbyDetach?.(); };
client/src/stores/multiplayerStore.ts:2296 subscribeTournaments (the tournament twin of subscribeLobby)
   ├─ :2297 await ensureSubscriptionSocket(); null → return null
   ├─ :2299 tournamentSubscribers.add(handlers)
   ├─ :2305 acquireLobbySubscription(...)   → attachSharedSubscription (:269) → SubscribeLobby on the wire
   ├─ :2306 seeds from tournamentListSnapshot if a push already arrived
   └─ :2309 detach = () => { delete; releaseLobbySubscription(); }
client/src/pages/multiplayerPageState.ts   the page's PURE view-model module (types + one classifier)
client/src/pages/__tests__/DraftLandingPage.test.tsx   page-test conventions:
   RTL + MemoryRouter, explicit `cleanup` import (no vitest globals), vi.mock of ScreenChrome,
   vi.hoisted mock bag, vi.mock("react-router", …) for useNavigate
```

**Six things the trace establishes that this plan copies verbatim rather than reinventing:**

1. **Routes live inside the existing `<Route element={<AppShell/>}>` layout route**, wrapped in `DevStrict`, with a `lazy()` chunk declared at the top of `App.tsx` (S7).
2. **View state belongs to the page**, in `useState` — the store owns wire state only. `multiplayerPageState.ts` is the precedent for a page's pure derivations living in a sibling module (here: `tournamentPageState.ts`, which already exists).
3. **The subscription effect uses `LobbyView`'s `if (cancelled) { detach?.(); return; }` idiom** — the exact shape the charter names (`:203`) for discharging phase 2's unmount-during-in-flight-connect deferral.
4. **`detach === null` is the "server unreachable" branch** and must be rendered, not swallowed. Probe P5 confirms it fires (below).
5. **Chrome composition:** `<ScreenChrome/>` (self-nulling inside the shell) + `<MenuShell eyebrow/title/description layout="stacked">`; `useInShell()` gates the page's own `<MenuParticles/>`.
6. **Page tests** use RTL + `MemoryRouter`, an explicit `cleanup`, and mock `ScreenChrome` (it reaches `ChromeControls → AccountControl`, unrelated to anything under test).

---

## §3 — Step 3: files read in full

Read completely before writing a line of this plan (worktree-absolute paths under `C:\git\phase\.claude\worktrees\tournament-organizer-pr4-frontend\`):

- `client/src/adapter/types.ts` — the Tournament section (`:4501-4728`), all 16 identifiers.
- `client/src/services/tournamentClient.ts` — all 529 lines (module header parts 1–5, `requestOver`, `matchReply`, 7 helpers, `subscribeTournamentsOver`).
- `client/src/stores/multiplayerStore.ts` — the full tournament surface: `:150-364` (abort set, subscriber sets, `lobbySubscriptionRefCount`, `attachSharedSubscription`, `detach`/`acquire`/`releaseLobbySubscription`, `forgetTournamentCredential`), `:367-503` (`TournamentRole`, `TournamentNotAuthorized`, `GatedTournamentRpcResult`, `runTournamentRpc`, `runGatedTournamentRpc`), `:755-809` (the 8 action signatures), `:940-994` (`TournamentCredential`, `MAX_TOURNAMENT_CREDENTIALS`, `capTournamentCredentials` doc), `:2091-2140` (`ensureSubscriptionSocket`), `:2296-2382` (all 8 action implementations).
- `client/src/pages/tournamentPageState.ts` — all 425 lines / 10 function exports + 4 view-model types.
- `client/src/components/tournament/*.tsx` — all five, in full, for their exact prop interfaces (see §4.2).
- `client/src/components/tournament/__tests__/tournamentTestUtils.ts` — `expectNoRawKeyPaths` / `expectCatalogValuePresent`.
- `client/src/i18n/locales/en/tournament.json` — all 147 lines / 111 keys.
- `client/src/i18n/locales/en/menu.json` — the `nav` block.
- `client/src/App.tsx` — all 141 lines.
- `client/src/components/chrome/navItems.tsx`, `navIcons.tsx`, `SparkleIcon.tsx`, `Rail.tsx`, `TabBar.tsx`, `AppShell.tsx`.
- `client/src/components/chrome/__tests__/navItems.test.ts` — all 41 lines.
- `client/src/pages/MultiplayerPage.tsx` (1059 lines) and `client/src/pages/multiplayerPageState.ts`.
- `client/src/components/lobby/LobbyView.tsx:1-200` (the subscription effect and its cleanup).
- `client/src/pages/__tests__/DraftLandingPage.test.tsx:1-60` (page-test conventions).
- `client/src/pages/__tests__/tournamentPageState.test.ts:400-428` (the `import type`-only static source assertion — binds §5.1).
- `client/src/stores/__tests__/multiplayerStore.tournament.test.ts:1-230` (the fake-socket harness §6.1 copies).
- `crates/lobby-broker/src/broker.rs` — `authorize_organizer` (`:1006-1019`), `authorize_player` (`:1048-1065`), `handle_get_tournament` (`:1175-1183`), `handle_report_match_result` (`:1211-1260`), `handle_drop_from_tournament` (`:1272-…`), the `tournament_list_update()` census.
- `client/vitest.config.ts` (`environment: "happy-dom"`, `setupFiles: ["src/test-setup.ts"]`, **no `globals: true`**), `client/src/test-setup.ts:29-31`.

---

## §3.5 — Step 3.5: probes (measured, then reverted)

Every probe below was **compiled and run** in the worktree and then removed; `git status --porcelain` is empty and `HEAD` is `b34de3f09…` after the last one. Frontend only — **no cargo target lock was taken at any point** (S9: this worktree has no Tilt; `./scripts/tilt-wait.sh` here returns exit 3 = "cannot answer", which is never a build failure).

`client/node_modules` **is present** on this worktree (contrary to S9's measurement at charter time — S9 was measured before phases 1–4 ran their own verification here). No `pnpm install` was needed.

**Counting convention for this table (stated, not restated as a bare number — m2).** Probes are numbered `P1..P8`; a probe that needed a second measurement to be conclusive carries a lettered sibling under the same number (here, exactly one: `P1b`, the suite baseline that gives `P1`'s type-check baseline its test-count half). So this table is **8 numbered probes across 9 rows**. Any later addition must extend the numbering and leave this sentence intact rather than editing a total into it — the convention is what stays true across edits; a transcribed count is what drifts. The same convention governs §6's verification matrix.

| # | Probe | Command / mechanism | Measured result | What it decides |
|---|---|---|---|---|
| **P1** | Baseline is green | `pnpm run type-check` | **exit 0** (chains `protocol:check` → `check-protocol-version.mjs`, exit 0) | Any type error after this phase is mine (S8 re-confirmed). |
| **P1b** | Baseline suites | `pnpm exec vitest run` over `navItems.test.ts`, `tournamentPageState.test.ts`, `components/tournament/__tests__`, `i18n/__tests__`, `i18n/resources.test.ts` | **10 files / 311 tests passed** | The delta this phase adds is measured against 311, not guessed. |
| **P4** | **Report authority** (§0.2) | scratch store test, real store, only `openPhaseSocket` faked | organizer-only credential → `{ok:false,reason:"not_authorized",role:"player"}`, **0** `ReportMatchResult` frames; **positive reach-guard:** same credential → **1** `StartTournamentRound` frame; player credential → **1** `ReportMatchResult` frame | **Blocking premise correction.** Gating report on `organizer` is dead UI. |
| **P5** | Offline branch | same harness, `withReconnect` firing `"offline"` | `subscribeTournaments(...)` resolves **`null`** | The `detach === null` branch is real and must be rendered (§4.5). |
| **P6** | Ambient delivery + refcount + cleanup | same harness | first tournament subscriber → **`SubscribeLobby` tally = 1**; a `TournamentUpdate` delivered with **no RPC in flight** → `onTournamentUpdate` called **1** time; message listeners **2 → 0** across detach; **`UnsubscribeLobby` tally = 1** | The page's render source (ambient broadcast) works with zero RPCs; detach is observable; §6.3's listener census is a real instrument. |
| **P2** | **S6 blast radius** | temporarily appended a 6th `NAV_ITEM` (`key:"tournament"`, `match: p=>p.startsWith("/tournament")`), ran `navItems.test.ts`, then reverted with the inverse edit | **exactly 1 test reds**: `exposes exactly the five primary destinations` — `AssertionError: expected [ 'home','play','online',…(3) ] to deeply equal [ …(2) ]`. The other **4 pass**, including `returns null for routes with no primary nav item (e.g. coverage)` | S6 confirmed *and bounded*: one assertion + one test name to update, nothing else. |
| **P3** | Chrome-suite regression from the nav item | `vitest run src/components/chrome/__tests__` **with** the temp item, then **without** | with: **16 failed / 112**; without: **15 failed / 112**. Delta = **exactly the one P2 test**. The 15 are pre-existing (`ChromeControls.focus`, `HostControlTile`, `StatusBanner`) — the standing Node v25 `localStorage`/`--localstorage-file` environment issue recorded at **Entry 29 (phase 3's review-impl)** | Adding a nav item breaks nothing else. The 15-failure baseline must not be misread as a regression by the executor or reviewers. |
| **P7** | Nav icon asset | `ls client/public/icons/sections/` | `coverage, decks, draft, home, metagame, online, play, resume, settings` — **no `tournament.png`** | §0.3 / §5.3: inline SVG, not a dangling `<img src>`. |
| **P8** | `get_tournament` cannot loop | source census of `tournament_list_update()` in `broker.rs` | 6 sites: `:576, :1130, :1169, :1207, :1310, :1335`; `handle_get_tournament` (`:1175-1183`) and `handle_report_match_result` are **not** among them | §4.7's "re-seed the detail view on every `onListUpdate`" is provably non-recursive. |

**Assertions in this plan that were NOT probed, labelled honestly:**

- That React 19's render-phase `setState` in `ReportResultDialog` behaves identically when the dialog is mounted by a page rather than by a test harness. Phase 4's fix-round reviewer proved the pattern's termination and payload safety directly against the component (**Entry 39 — phase 4's fix-round review-impl**); phase 5 mounts it unchanged and re-asserts the observable outcome (V14), so this is re-measured at implementation, not assumed.
- That `DevStrict`'s double-effect-invoke in DEV is harmless here. Reasoned from phase 2's *stated and tested* idempotence (set-membership refcount: "a double-subscribe cannot inflate the count and a double-release cannot drive it negative") plus the `cancelled` idiom. **V15 tests it directly** rather than leaving it reasoned.
- Visual/layout outcome of a 6th tab in `TabBar` at <820px (7 flex-1 cells). Not measurable under happy-dom. Named as a cosmetic follow-up in §7.5.

---

## §4 — Step 4: architectural sections

### 4.1 Pattern Coverage

Assessed **against the charter's class attribution**, per phase-plan mode — an infrastructure phase covers zero cards by construction, and this phase covers zero cards under any reading (it is not card-facing at all).

The class this phase serves is **"every tournament the broker can host, reachable and operable from the browser."** Concretely, the two pages are total over the closed wire unions phase 3 keyed the catalog to and phase 4 built exhaustive walks for:

| Axis | Members | Covered by |
|---|---|---|
| `TournamentStatus` | Registration / InProgress / Completed / Abandoned | `t(\`status.${…}\`)` direct index (phase 4's licensed pattern) |
| `BracketShape` | Swiss / SingleElimination | `t(\`bracket.${…}\`)` + the create form's `<select>` |
| `MatchArity` | `2..=128` | `arityLabel`; no arity branch anywhere in phase 5 |
| `PairingOutcome` | Bye / Forfeit / Reported→Decisive / Reported→Draw / pending `null` | `outcomeLabelKey`, `isReportable`, `decisiveGameWins` — all phase 4's |
| `Tiebreaks` | HeadToHead / Multiplayer | `tiebreakCells` |
| `TournamentRpcFailureReason` + local refusal | rejected / aborted / timeout / connection_lost / **not_authorized** | **`failureLabel`, new here (§4.3)** — exhaustive, `never`-terminated |
| Viewer relation (display) | organizer / entered(player) / spectating | **`viewerRelation`, new here (§4.3)** |
| Viewer entrant status (authority) | active entrant / dropped entrant / not an entrant | **`isActiveEntrant`, new here (§4.3)** — kept separate from the display axis on purpose, since a *playing organizer who drops* is `"organizer"` on one axis and inactive on the other |
| The 7 RPCs | create, join, get, start, report, drop, end | **all seven reachable from the UI** (§7.4) |

"Would this work for 50 tournaments or just one?" — nothing in either page is keyed to a specific code, name, arity, bracket or locale. The one place a single tournament is named is the URL parameter.

### 4.2 Component contracts consumed (read from source, not from prose)

Phase 5 is the first phase to mount these. Their prop interfaces are **frozen inputs** — none may be edited.

| Component | Exact props | How phase 5 supplies them |
|---|---|---|
| `TournamentListItem` | `{ summary: TournamentSummary; onOpen: (code: string) => void }` | Landing page, one per `TournamentSummary` from `onListUpdate`. `onOpen` → `navigate('/tournament/' + code)`. **Takes `TournamentSummary`, never `TournamentView`** — the narrower type is the whole point (active-vs-total entrant count). |
| `CreateTournamentForm` | `{ onSubmit: (req: CreateTournamentRequest) => void; submitting?: boolean; initialArity?: MatchArity }` | Landing page. `onSubmit` → `store.createTournament(req)`. `initialArity` **left at its default (2)** — see §7.3 (F2 residual risk). |
| `TournamentStandingsTable` | `{ standings: readonly TournamentStanding[] }` | Detail page, `view.standings`, **in array order, never sorted**. |
| `PairingsList` | `{ pairings: readonly TournamentPairingView[]; onReport?: (p) => void }` | Detail page **twice**: (a) "Your Match" — `[myPairing]` **with** `onReport` when the viewer holds `player`; (b) full history — `view.pairings` **without** `onReport`. See §0.2. |
| `ReportResultDialog` | `{ isOpen; pairing: TournamentPairingView; onSubmit: (o: PodOutcome) => void; onCancel; submitting?; returnFocusRef? }` | Detail page, one instance, opened from (a). Its doc explicitly states a caller **need not** pass `key={pairing.id}` (phase 4's fix round made the reset structural) — so phase 5 does **not** pass one, and V14 pins that this remains safe when mounted. |

### 4.3 New derivations — placement, and the parameterization lens

**Three** pure derivations are needed: `viewerRelation` and `failureLabel` by **both** pages, and `isActiveEntrant` (revision 2's M1 fix) by the detail page's two player gates. All three belong in `client/src/pages/tournamentPageState.ts` — the module whose own header declares itself *"the single authority for every derivation the tournament components need."* Duplicating any of them across page files would install exactly the second-authority-that-can-disagree failure this run has corrected four times.

**(1) `ViewerRelation` + `viewerRelation(roles)`** — discharges the chartered "role badge" deferral.

```ts
/**
 * How this browser relates to one tournament, for display.
 *
 * Three members, 1:1 with the catalog keys `labels.organizer` /
 * `labels.entered` / `labels.spectating`, so `t(\`labels.${relation}\`)` is a
 * direct index — the same licensed pattern as `status.*` and `bracket.*`
 * (flat unions whose members ARE the key leaves), and NOT the forbidden
 * `outcome.*` pattern (whose keys are not 1:1 with wire tags).
 */
export type ViewerRelation = "organizer" | "entered" | "spectating";

export function viewerRelation(
  roles: ReadonlySet<TournamentRole>,
): ViewerRelation {
  if (roles.has("organizer")) return "organizer";   // precedence: see below
  if (roles.has("player")) return "entered";
  return "spectating";
}
```

*Why a precedence rather than a set of badges.* A playing organizer holds **both** tokens under one code — phase 2 documented this as the **normal** path (`CreateTournament` does not auto-join the creator). Two badges on one row is noise; the organizer relation is the stronger claim and subsumes the weaker for display. **This is a display precedence only** — it must never be read as an authority decision. Authority stays with `viewerRoles(...)` (a *set*, precisely because a boolean cannot express the both case) and, for acting, with `runGatedTournamentRpc` alone. Both consumers of `viewerRelation` in this phase use it for a badge and nothing else; V4 pins that an organizer-and-player credential still renders **both** control blocks.

*Parameterization / sibling-cluster lens (CLAUDE.md, applied even though this is not an engine enum).* `ViewerRelation` is not a sibling cluster: the three members share no name root, differ by no comparator/scope axis, and are not a leaf-parameterization of an existing variant. It is not a re-declaration of `TournamentRole` either — `TournamentRole` is the **authority** vocabulary (2 members, both grantable at once); `ViewerRelation` is the **display** vocabulary (3 members, mutually exclusive, includes the zero-authority case `TournamentRole` cannot express). Collapsing them would force `"spectating"` into an authority union, which is exactly the category error phase 2's M2 finding rejected when it refused to file a local refusal under the wire's `"rejected"`.

**(2) `FailureLabel` + `failureLabel(failure)`** — discharges the chartered server-rejection-copy deferral.

```ts
/**
 * A catalog key for a failed tournament action, carried with the
 * interpolation variable that key needs. Key and vars travel as one value so
 * "called a key without its variable" is unrepresentable — the same shape as
 * {@link OutcomeLabel} and {@link ArityLabel} in this module.
 */
export type FailureLabel =
  | { readonly key: "errors.notOrganizer" }
  | { readonly key: "errors.notEntered" }
  | { readonly key: "errors.timedOut" }
  | { readonly key: "errors.connectionLost" }
  | { readonly key: "errors.aborted" }
  | { readonly key: "errors.serverRejected"; readonly message: string };

/** The failure half of a gated action's result — also total over an ungated one. */
type TournamentFailure = Extract<
  GatedTournamentRpcResult<unknown>,
  { ok: false }
>;

export function failureLabel(failure: TournamentFailure): FailureLabel { … }
```

Mapping, each arm justified against the type that produced it:

| `failure.reason` | Key | Why |
|---|---|---|
| `"not_authorized"` + `role: "organizer"` | `errors.notOrganizer` | phase 2's F4-named key; the **typed** `role` field is read, never the English `message` |
| `"not_authorized"` + `role: "player"` | `errors.notEntered` | same |
| `"rejected"` | `errors.serverRejected` with `{ message }` | phase 1's contract: *"the broker answered `Error`; `message` is its text verbatim"* — **interpolated, never translated** |
| `"timeout"` | `errors.timedOut` | |
| `"connection_lost"` | `errors.connectionLost` | |
| `"aborted"` | `errors.aborted` | fires on the `reconnecting` transition / `closeSubscriptionSocket` (phase 2's abort wiring) |

Terminates in `const unreachable: never = failure;` — **no `default:` arm** — so a sixth failure member anywhere (a fifth `TournamentRpcFailureReason`, or a second store-level refusal) fails the build here. It is therefore **a further exhaustive walk, over the failure-reason union rather than a wire union**, strengthening §4.1's compile-enforcement claim rather than diluting it.

*Deliberately no ordinal is attached to that sentence, here or in §5.1 (m3).* Revision 1 called it "the fifth exhaustive walk," which was wrong twice over and in a way the plan's own rules already forbade. The module header's count (*"Three of the exports below … and `tiebreakCells` is a fourth"*) is explicitly scoped to **wire-union** walks; measured on the current file, `tournamentPageState.ts` actually contains **seven** `const unreachable*: never` terminals — `grep -c ": never" client/src/pages/tournamentPageState.ts` returns 8, of which one is the header's own prose mention — because `outcomeLabelKey` and `decisiveGameWins` each carry a nested `unreachablePod` terminal inside their `Reported` arm, and `formatTiebreakValue` walks a format union that is not a wire union at all. An ordinal computed against either count would be wrong, and either way it is a transcribed number that the next edit falsifies. State the kind of walk; never the position in a sequence.

*Why the `role` sub-discrimination is not a "special case."* Phase 2's review round 2 (M2) established that local refusals are **undecidable** from a wire `{ok:false, reason:"rejected"}` unless the store carries a typed discriminator — and then built one (`TournamentNotAuthorized.role`). `failureLabel` is the single consumer that discriminator was created for. Consuming it here is the discharge of that design, not an extension of it.

*`errors.notFound`* is **not** in this map: no wire reason produces it. It is rendered by the detail page when a `TournamentRemoved` arrives **for the code being viewed** — a client-known fact, not a wire message (§5.5). That is the whole key set of `errors.*` accounted for: 7 keys, 7 producers.

**(3) `isActiveEntrant(view, playerKey)`** — the client mirror of the broker's **C2** conjunct (§0.2), and revision 2's fix for M1.

```ts
/**
 * Whether `playerKey` names an entrant of `view` who has **not** dropped.
 *
 * This is the client-side mirror of the second conjunct `authorize_player`
 * enforces (`crates/lobby-broker/src/broker.rs`): a token that resolves to an
 * entrant is refused anyway once `player.dropped` is true
 * (`"Player has dropped from tournament {code}"`). Token possession —
 * {@link viewerRoles} — answers the *first* conjunct only, and the store
 * clears a credential on `TournamentRemoved` alone, never on a drop, so
 * `roles.has("player")` stays true forever after a drop. A gate written on
 * possession alone therefore renders an affordance the broker refuses every
 * time; both player affordances need this conjunct too.
 *
 * Positive polarity on purpose: callers write
 * `roles.has("player") && isActiveEntrant(...)`, a plain conjunction, so no
 * edit can silently lose a `!`.
 *
 * Fails closed in both directions. An absent `playerKey` (a spectator) is not
 * active. A `playerKey` absent from `view.players` is not active either —
 * and that is sound rather than merely cautious, because `players` is a full
 * history that keeps dropped entrants listed (`adapter/types.ts`'s
 * `TournamentView` doc: *"dropped players stay listed (their `dropped` flag
 * is the distinction to render)"*), so absence means "not an entrant of the
 * tournament this view describes" — a foreign or not-yet-seeded view — never
 * "an entrant whose row was filtered out". If the broker ever did start
 * filtering dropped entrants out of `players`, this still answers `false`,
 * which is still the correct gate.
 *
 * "Active entrant" is the wire's own vocabulary for exactly this predicate,
 * not a coinage: `TournamentSummary.player_count` is documented as
 * "**Active** entrants — `TournamentMeta::active_player_count`", i.e. the
 * count of entrants for which this function is true.
 */
export function isActiveEntrant(
  view: TournamentView,
  playerKey: string | undefined,
): boolean {
  if (playerKey === undefined) return false;
  const entrant = view.players.find((p) => p.player_key === playerKey);
  return entrant !== undefined && !entrant.dropped;
}
```

*Placement: why this is a `tournamentPageState.ts` export and not an inline conjunct in `TournamentPage.tsx`.* This is the design decision M1 forces, and it is decided on shape, not on consumer count. Four grounds, in descending weight:

1. **It is an identity join across two wire structures, which is precisely what this module already exists to own.** The function matches `TournamentCredential.playerKey` against `TournamentView.players[].player_key` — the *identical* join `myPairing(view, playerKey)` already performs in this same module, down to the `if (playerKey === undefined) return null` fail-closed guard and the `(view, playerKey)` parameter order. `myPairing` lives in this module rather than in the page for exactly the reason given in its own doc (*"which entrant am I in THIS event"* is a derivation, not a render step). An inline conjunct would put one half of "who am I in this tournament" in the module and the other half in a JSX expression, which is the split a future reader is most likely to get wrong.
2. **It is authority logic, and this module is already the single display-authority.** `viewerRoles`'s doc states the division of labour outright: *"`runGatedTournamentRpc` is the single authority for *acting*; this is the single authority for *displaying*, off the same map, so the two can never disagree."* C2 is a display-authority conjunct. Filing C1 in the module and C2 in a page component would create the second authority that doc exists to prevent — and it would be the *more* dangerous half, since C1 is stable while C2 flips underneath the page on every broadcast.
3. **It is testable without a DOM, and the revert-check is sharper for it.** `tournamentPageState.test.ts` can cover the four input shapes (active entrant / dropped entrant / unknown key / `undefined` key) as a pure `it.each` in milliseconds; V22's mounted hostile fixture then proves the *gates consume it*, rather than having to carry the whole truth table through React. An inline conjunct is reachable only through a mounted page, which makes each case a render and makes RC9/RC10 red at a vaguer place.
4. **Consumer count is real but is the weakest argument, and is stated honestly rather than inflated.** There are two consumers today, both on the detail page (§5.5 items 4 and 5). The landing page **cannot** consume it — it holds `TournamentSummary`, which carries `player_count` and no `players` array — so this is not a two-page derivation the way `viewerRelation` and `failureLabel` are. If consumer count were the criterion, this would be a close call. It is not the criterion: grounds 1–3 are about where the *shape* of the logic belongs, and they are what decide it.

*Why it is a `boolean` and not a typed union, given §4.8's "typed unions, never booleans" rule.* That rule targets booleans that **encode a category** (`isOrganizer: boolean` losing the playing-organizer case; `hasError: boolean` carrying a string beside it). This is a genuine two-valued predicate over a single wire `boolean` field, with no third state to lose — and it has direct precedent in this very module: `isReportable(outcome: PairingOutcome | null): boolean` collapses a five-member union to a decision and returns a bare `boolean`, deliberately. Introducing an `EntrantStanding = "active" | "dropped" | "not-an-entrant"` union would be the opposite error: it would invite call sites to discriminate a third case that both gates must treat identically to `"dropped"`, and CLAUDE.md's parameterization filter names exactly that (a sibling cluster differing only by a context label) as the smell to avoid.

*Why `dropped` is not folded into `ViewerRelation` as a fourth member, despite `labels.dropped` already existing in all 7 catalogs.* This was considered and **rejected**, and the reason is the same sentence that governs `viewerRelation` above: it is a **display precedence** and *"must never be read as an authority decision."* `ViewerRelation` resolves organizer-first, so a playing organizer who drops would still resolve to `"organizer"` — and a gate written as `relation !== "dropped"` would leave that viewer's Drop and Report buttons live, reintroducing M1 for precisely the credential shape phase 2 documented as the **normal** path. Authority conjuncts must not ride on a precedence chain. (`labels.dropped` needs no new consumer regardless: phase 4's `TournamentStandingsTable` already renders it as a per-row chip, so the detail page's standings table already *tells* the viewer they have dropped. M1 was never a missing-information bug; it was a missing-gate bug.)

### 4.4 Logic Placement

| Logic | Home | Justification |
|---|---|---|
| Wire framing, reply correlation, broadcast fan-out | `services/tournamentClient.ts` (phase 1) | **Frozen. Not touched.** |
| Socket lifetime, credentials, refcount, abort wiring, authority gating | `stores/multiplayerStore.ts` (phase 2) | **Frozen. Not touched.** §0.2's finding is a *consumer* correction, not a store change. |
| Catalog keys and 7-locale mirrors | `i18n/locales/*/tournament.json` (phase 3) | **Not touched — zero new keys (§7.1).** |
| Wire-union → catalog-key derivations; identity joins; purity guarantees | `pages/tournamentPageState.ts` (phase 4) | **Three additive exports only** (§4.3: `viewerRelation`, `failureLabel`, `isActiveEntrant`). No existing export is modified. Additions are `import type`-only, preserving the static source assertion at `tournamentPageState.test.ts:406-427`. |
| Rendering a `TournamentView`/`TournamentSummary` | `components/tournament/*.tsx` (phase 4) | **Frozen. Not touched.** Composed only. |
| **Page view state; effect lifecycle; which action a control dispatches; which credential a control is gated on; navigation** | **`pages/TournamentLandingPage.tsx`, `pages/TournamentPage.tsx` (new)** | The only genuinely new logic. It is composition + local UI state — not game logic, not derived game state. |
| **Route registration** | `App.tsx` | The single route table (S7). |
| **Nav registration** | `navItems.tsx` + `navIcons.tsx` | The single nav data table (S7). |

**Display-layer discipline (CLAUDE.md's #1 frontend rule), stated as five prohibitions the executor must be able to point at in the diff:** neither page may (1) sort or re-rank anything, (2) recompute any standings/tiebreak number, (3) filter `players` or `pairings`, (4) filter `tournamentListSnapshot` on `TournamentRemoved` — the store's own doc forbids it ("would invent a delta protocol the broker does not speak"), or (5) pre-reject any create/report payload the broker validates. Every one of these has a revert-check (§6.5).

### 4.5 The subscription lifecycle (both pages, identical shape)

```tsx
useEffect(() => {
  let cancelled = false;
  let detach: (() => void) | null = null;
  void (async () => {
    const d = await subscribeTournaments(handlersRef.current);
    if (cancelled) { d?.(); return; }        // ← LobbyView.tsx:134-137 idiom, verbatim
    if (d === null) { setOffline(true); return; }   // ← probe P5: this really happens
    detach = d;
  })();
  return () => { cancelled = true; detach?.(); };
}, [subscribeTournaments]);
```

Three properties, each load-bearing:

1. **Unmount before resolve detaches anyway** — `if (cancelled) { d?.(); return; }`. This is #4615's original bug; V15 reproduces and pins it.
2. **`detach === null` is rendered**, as `errors.connectionLost` (probe P5). Swallowing it produces a page that renders "Loading tournaments…" forever against an unreachable server.
3. **The handlers object is held in a ref**, not rebuilt per render. A new handlers identity per render would re-run the effect, and `tournamentSubscribers` is a `Set` keyed by object identity — churning it would thrash `acquire`/`release` and, in the worst ordering, send `UnsubscribeLobby` while another subscriber is live. The dependency array is therefore the **stable store action only** (zustand actions are stable across renders), and the ref's `.current` is reassigned on every render so the handlers always close over fresh state setters. This is the reason the effect is written with a ref rather than with `useCallback`-wrapped handlers: `useCallback` deps would leak page state into the subscription lifetime.

### 4.6 Identity / Provenance Contract

| Binding | Source phrase / concept | Authority type + id | Bound when | Live vs latched | Stored | Consumed by | Invalidation | Hostile fixture |
|---|---|---|---|---|---|---|---|---|
| **B1 — "this tournament"** | the `:code` route segment | `string` code from `useParams` | on navigation | **live** — remount on code change | React Router location | both pages, every RPC, the `onTournamentUpdate` filter | route change | V6: a broadcast for a **different** code must not touch this page's view |
| **B2 — "may I organize this"** | `organizer_token` for **this** code | `TournamentCredential.organizerToken` | at `CreateTournament` reply | **live** read per render | `tournamentCredentials[code]` (persisted) | `viewerRoles` → control visibility; `runGatedTournamentRpc` → the actual send | `TournamentRemoved` → `forgetTournamentCredential` | V4: credential for **A**, viewing **B** → no organizer controls |
| **B3 — "may I report/drop"** (C1 only) | `player_token` for this code | `TournamentCredential.playerToken` | at `JoinTournament` reply | live | same map | same two consumers | **only `TournamentRemoved`** — *not* a successful drop, which is why B7 is a separate binding | V4b: organizer-only credential → **no** report affordance anywhere (§0.2) |
| **B7 — "am I still an active entrant"** (C2) | `authorize_player`'s `if player.dropped` refusal | `PlayerSummary.dropped` for **my** `player_key`, read out of the **view**, never the credential | on every `TournamentUpdate` broadcast | **live, and deliberately so** — this is the one authority conjunct that flips *underneath* a mounted page, with no local action and no credential change | not stored; derived per render by `isActiveEntrant(view, credential?.playerKey)` | the Drop gate and the Report gate (§5.5 items 4, 5) | recomputed from the next broadcast; never latched, because latching it at mount would miss the viewer's own drop | **V22:** a dropped entrant seated in a still-`Pending` 4-seat pod renders **zero** Drop and **zero** Report buttons, while an active entrant in the **same fixture** renders exactly one of each |
| **B4 — "which entrant am I"** | `player_key` sent at join | `TournamentCredential.playerKey` | at join, **captured before the await** (store `:2337`) | latched, deliberately | same map | `myPairing(view, playerKey)` | `TournamentRemoved` | V5: two entrants, one browser's key → exactly one "Your Match" |
| **B5 — "this pairing"** | the row whose Report was clicked | `TournamentPairingView` object | on click | latched into page state | `useState<TournamentPairingView \| null>` | `ReportResultDialog.pairing`; `reportMatchResult(code, pairing.id, outcome)` | closed on submit/cancel; **and** re-derived from the fresh `view` on every broadcast so a stale object is never submitted | V14: a broadcast arriving while the dialog is open must not carry a stale seat list into the payload |
| **B6 — "did my action land"** | the `TournamentUpdate` broadcast | **the ambient subscription's view — never the RPC return value** | on broadcast | live | page `useState<TournamentView>` | every rendered field | replaced by the next broadcast | **V10 (the discharge of phase 1's deferral):** `Error` settles the RPC `{ok:false}` **and** a broadcast still arrives → the DOM shows the broadcast's state *and* the rejection alert |

**B6 is the phase's central provenance rule and follows directly from phase 1's finding.** The four gated RPCs settle on a broadcast that carries no request-vs-broadcast discriminator, so their `{ok:true}` may be *another actor's* view and their `{ok:false}` may arrive after a foreign frame already settled the promise. Therefore: **the page never calls `setView(result.value.view)`.** Not once, for any of the seven RPCs — including `getTournament`, whose reply *is* `ToSelf` and *would* be safe, because a single rule with no exception is the one a future reader cannot get wrong. Every view update in both pages flows through the `onTournamentUpdate` handler. V11 pins this by mutation (§6.5, RC4).

The RPC results are used for exactly two things: (a) the `code` of a freshly created/joined tournament (from `TournamentCreatedReply.code` / `TournamentJoinedReply.code`, the only authority for a broker-minted code), and (b) `failureLabel(...)` for a **best-effort** alert. §5.5 requires a comment saying the alert is best-effort and citing part 4 of `tournamentClient.ts`'s header, so nobody later "fixes" it into an authoritative signal.

### 4.7 Seeding and re-seeding the detail view

`TournamentUpdate` broadcasts fire only on **mutation**. A page mounted on a quiet tournament would render nothing forever. So:

- **On mount** (and on every `code` change): `getTournament(code)` — the one genuinely `ToSelf` helper. Its result is **not** written to state directly (B6); it is awaited only so a failure can be surfaced. The view arrives through the subscription handler, because the same frame reaches both. *(If the subscription has not attached yet, the frame is missed — which is exactly why the `getTournament` call is issued **after** `subscribeTournaments` resolves, not before. §5.5 sequences them.)*
- **On every `onListUpdate`**: re-issue `getTournament(code)`. This covers (a) reconnect — the store re-attaches and `SubscribeLobby`'s `ToSelf(TournamentListUpdate)` is the only signal a page gets that the socket came back, and (b) any other actor's list-visible mutation.
  **Provably non-recursive** (probe P8): `handle_get_tournament` emits `ToSelf(TournamentUpdate)` and **no** `tournament_list_update()`, so the re-seed cannot re-trigger itself. The six list-update sites are `broker.rs:576, :1130, :1169, :1207, :1310, :1335`.
  **Cost:** one extra frame per list push per open detail page. `handle_report_match_result` is *not* a list-update site, so the common in-round traffic does not trigger it at all.

Without the second bullet, a detail page open across a reconnect shows a stale view until someone mutates the tournament. Closing it "properly" (a store-level reconnect signal for subscribers) would require editing `multiplayerStore.ts`, which is not in this phase's scope; this in-scope mechanism closes it fully at negligible cost. V12 pins it.

### 4.8 Rust Idioms → TypeScript equivalents

Not Rust, but the same discipline, and the file this phase edits already enforces it:

- **Typed unions, never booleans.** `ViewerRelation` and `FailureLabel` are discriminated unions. No `isOrganizer: boolean`, no `hasError: boolean` carrying a string beside it. Page error state is `FailureLabel | null` — the label *is* the presence.
- **Exhaustive discrimination, `never`-terminated, no `default:`.** `failureLabel` and `viewerRelation` follow the four walks already in the module.
- **Key + vars as one value.** `FailureLabel` mirrors `OutcomeLabel`/`ArityLabel`: `"message" in label ? t(label.key, { message: label.message }) : t(label.key)`.
- **Reuse over re-declaration.** `TournamentRole`, `TournamentCredential`, `TournamentRpcFailureReason`, `GatedTournamentRpcResult`, `TournamentNotAuthorized`, `CreateTournamentRequest` are all imported, never re-spelled.
- **`import type` only** in `tournamentPageState.ts` — pinned by that module's own static source assertion, and the reason a `value` import there costs 925ms vs 14ms.

### 4.9 Nom compliance / CR annotations / variant discoverability

- **Nom:** N/A. No file under `crates/engine/src/parser/` is touched. No file under `crates/` at all.
- **CR annotations: N/A — checked, not assumed.** Three independent grounds: (1) this phase adds no Rust and no game logic; (2) tournament-organizer behavior is governed by the **MTR/MSTR**, not the Comprehensive Rules — `crates/lobby-broker/src/tournament.rs:36` itself draws that distinction, and phase 4's plan recorded it; (3) writing a `CR` citation for pairing or tiebreak policy would be precisely the fabricated-citation failure the CLAUDE.md gate exists to prevent. **Executor gate:** `git diff PHASE_BASE_SHA..HEAD | grep -cE "CR [0-9]{3}"` must print `0`. Phases 1–4 each ran and passed this identical check.
  **Exit-code caveat (m7): `grep -c` exits `1` when the count is zero — which here is the *correct, passing* outcome.** The gate's verdict is the **printed count**, never the exit status. Do **not** wrap this command in `set -e`, do not chain it with `&&`, and do not let a wrapper script treat its non-zero exit as a failure; every one of those would report a clean phase as broken. If a script must branch on it, capture the number first: `n=$(git diff PHASE_BASE_SHA..HEAD | grep -cE "CR [0-9]{3}" || true); [ "$n" = "0" ]`. The `|| true` is what makes the pipeline safe under `set -e` while leaving `$n` correct. Phases 1–4 each ran this interactively, where the exit code was never consulted, which is why the hazard has not fired in this run yet.
- **Variant discoverability:** N/A — no engine enum variant is proposed, so `cargo engine-inventory` and the `/add-engine-variant` checklist have no subject. The parameterization lens was nonetheless applied to `ViewerRelation` and `FailureLabel` in §4.3. `data/engine-inventory.json` was **not** generated, deliberately: it requires a cargo build and this phase must not take the target lock (S9).

### 4.10 Extension vs Creation

Everything extends an existing pattern:

| Thing | Extends |
|---|---|
| Two page components | `MultiplayerPage` / `DraftLandingPage` (§2 trace) |
| Two routes | the `App.tsx` route table inside `<AppShell>`, with `lazy()` + `DevStrict` |
| One nav item | the `NAV_ITEMS` data table |
| One SVG nav icon | `SparkleIcon` (already rail/tab-bar-resident) |
| Two page-state exports | `tournamentPageState.ts`'s existing key+vars / exhaustive-walk forms |
| The subscription effect | `LobbyView.tsx:115-191` verbatim |
| Page tests | `DraftLandingPage.test.tsx` conventions + `multiplayerStore.tournament.test.ts`'s fake-socket harness |

**Nothing new is invented.** The only "new" shape is the SVG nav icon, and it has an in-file-adjacent precedent rendered by the very same two components.

### 4.11 SIZING (mandatory)

**Units** — one unit = one coherent behavior implementable by a single skill-checklist pass, regardless of how many lockstep layers it touches.

| # | Unit | Registration surfaces | Discriminating test |
|---|---|---|---|
| **U1** | **Reachability** — two routes + one nav destination + its icon | `App.tsx` (2 `lazy()` + 2 `<Route>`), `navItems.tsx` (`NAV_ITEMS` + `activeNavKey`), `navIcons.tsx` (`TournamentNavIcon`), `navItems.test.ts` (array + test name, S6) | `activeNavKey("/tournament")` and `activeNavKey("/tournament/ABC123")` both `=== "tournament"`, and `activeNavKey("/coverage")` stays `null` (V1–V3) |
| **U2** | **Page-state derivations** — `viewerRelation`, `failureLabel`, `isActiveEntrant` | `tournamentPageState.ts` (3 exports), `tournamentPageState.test.ts` | Exhaustive `it.each` over all 3 relations, all 6 failure shapes and all 4 entrant shapes, + compile-time `never` deletion checks (V7–V9, V22) |
| **U3** | **`TournamentLandingPage`** — list + create + join, subscribed | `pages/TournamentLandingPage.tsx`, `pages/__tests__/TournamentLandingPage.test.tsx` | Mounted against a fake socket: list renders from `onListUpdate`; create/join navigate on the reply's `code`; offline branch renders; no raw key paths (V16–V21) |
| **U4** | **`TournamentPage`** — detail, gated controls, live socket | `pages/TournamentPage.tsx`, `pages/__tests__/TournamentPage.test.tsx` | The B6 discharge (V10), gating hostile fixtures (V4/V4b), unmount race (V15), re-seed (V12), key completeness (V13) |

**T1 (units ≥ 2): 4 ≥ 2 → FIRES.**

The charter's own row for phase 5 said **3** units ("landing page; detail page; routing + nav"). This plan reports **4**, honestly: the two page-state derivations are independently tested behaviors with their own registration surface, and the charter's phase-4 precedent (where `isReportable` and `decisiveGameWins` were added *inside* an existing unit) does not apply, because those landed in a module the phase already owned as a unit — here `tournamentPageState.ts` is not otherwise part of this phase's work. Reporting 3 would violate `/review-engine-plan`'s consistency rule ("a plan whose body names N independently tested behaviors must not report fewer units").

**Source scope-paths**, under the charter's frozen counting rule (test fixtures and test files excluded outright; translation mirrors grouped with authored source; directory entries expanded):

| # | Path | New? |
|---|---|---|
| 1 | `client/src/pages/TournamentLandingPage.tsx` | new |
| 2 | `client/src/pages/TournamentPage.tsx` | new |
| 3 | `client/src/App.tsx` | edit |
| 4 | `client/src/components/chrome/navItems.tsx` | edit |
| 5 | `client/src/components/chrome/navIcons.tsx` | edit |
| 6 | `client/src/pages/tournamentPageState.ts` | edit (+3 exports) |

**Revision 2's M1 fix moves no count.** `isActiveEntrant` lands in scope-path 6 and its two consumers land in scope-path 2, both already listed; V22 lands in the two already-listed test files; no catalog file is touched. Units stay at **4** — `isActiveEntrant` is a third export of the same U2 unit (one coherent behavior, "derive what this browser may be shown about one tournament", implementable in a single `/add-frontend-component` pass), not a fifth unit, and it ships with U2's own test file. **4 units, 6 source scope-paths, unchanged from revision 1.**

**6 source scope-paths. T2 (≥ 13): 6 < 13 → DOES NOT FIRE. T1 ∧ T2 → does not fire. No further decomposition.**

**Delta from the charter's row (5, +1 conditional), reconciled explicitly:**

- **`AppShell.tsx` (the charter's conditional +1) is NOT taken.** §5.6 decides against widening `showStatusBanner`, with reasoning. −1 conditional.
- **`tournamentPageState.ts` is added.** Two derivations that both pages need; putting them anywhere else duplicates them. +1.
- **`localeParity.test.ts` is NOT touched.** Zero new catalog keys (§7.1), so there is no stem to register. It is a test file (T2-excluded) either way, so this moves no count — but the executor must know it is *not* expected in the diff. The 7 `tournament.json` catalogs are likewise untouched.

**Robustness under hostile counting conventions** (following phase 3's and phase 4's precedent of naming these rather than leaving them for rediscovery):

| Convention | Count | T2? |
|---|---|---|
| Charter's frozen rule (test files excluded) | **6** | no |
| Test files counted (+`TournamentLandingPage.test.tsx`, `TournamentPage.test.tsx`, `navItems.test.ts`, `tournamentPageState.test.ts`) | **10** | no |
| Test files counted **and** every hypothetical catalog file ungrouped | **10** (no catalog is touched, so grouping is moot) | no |

**T2 does not fire under any convention.** Unlike phase 4 (which had one convention combination reaching 19), this phase has no counting-convention exposure at all, because it authors no translation mirrors.

**Inter-unit dependency edges:** U2 → U3, U2 → U4 (both pages consume `failureLabel`; both consume `viewerRelation`). U1 is independent of U2/U3/U4 in code but must land with them so the routes it declares resolve. Implementation order in §5 is U2 → U1 → U3 → U4, so every intermediate state compiles.

### 4.12 Building Blocks

Composed, not rewritten:

| Block | Source | Use |
|---|---|---|
| `viewerRoles`, `myPairing`, `arityLabel`, `outcomeLabelKey`, `isReportable`, `decisiveGameWins`, `gameWinsEntries`, `tiebreakCells`, `formatTiebreakValue`, `defaultScoringForArity` | `pages/tournamentPageState.ts` (phase 4) | all consumed; none reimplemented |
| The 5 tournament components | `components/tournament/` (phase 4) | composed; none edited |
| `subscribeTournaments`, `createTournament`, `joinTournament`, `getTournament`, `startTournamentRound`, `endTournament`, `reportMatchResult`, `dropFromTournament`, `tournamentCredentials` | `stores/multiplayerStore.ts` (phase 2) | the page's only wire access |
| `MenuShell`, `MenuPanel`, `menuButtonClass`, `ScreenChrome`, `useInShell`, `MenuParticles` | `components/menu/`, `components/chrome/` | page chrome, exactly as `MultiplayerPage` composes them |
| `NAV_ITEMS`, `activeNavKey` | `components/chrome/navItems.tsx` | extended by one row |
| `expectNoRawKeyPaths`, `expectCatalogValuePresent` | `components/tournament/__tests__/tournamentTestUtils.ts` | the key-completeness discharge (V13/V21) — **already exists; do not author a second detector** |
| the fake-socket harness (`makeFakeSocket`, `primeSocket`, `tally`, `deliver`, `listenerCount`, `flush`) | `stores/__tests__/multiplayerStore.tournament.test.ts:66-165` | copied into the two page test files (§6.1) |

**New helpers justified:** none beyond U2's three exports, whose justification is in §4.3. In particular, `isActiveEntrant` is *not* a re-implementation of anything above — `viewerRoles` reads the credential map and never a `TournamentView`, and no existing export reads `PlayerSummary.dropped` at all (phase 4's `TournamentStandingsTable` reads `TournamentStanding.dropped` inline, for a chip, and exposes no predicate).

---

## §5 — Step 5: step-by-step implementation

Order is U2 → U1 → U3 → U4. Every intermediate commit-point compiles.

### 5.1 `client/src/pages/tournamentPageState.ts` — append three exports (U2)

**Surgical append only.** Do not reorder, reformat or modify any existing export's *code*. Re-read the file before editing (multi-agent safety).

**Two documented exceptions, both comment-only, both enumerated here so no third one is improvised:** item 5 (one sentence added to the module header) and item 7 (one clause corrected inside `isReportable`'s existing doc comment — round 2's M1). Neither touches a function body, a signature, or an export list. Everything else in this file is append-only.

1. Extend the existing `import type { … } from "../stores/multiplayerStore";` block with `GatedTournamentRpcResult` and keep `TournamentRole` (already imported). **It must remain `import type`** — `__tests__/tournamentPageState.test.ts:406-427` reads this file from disk and asserts every `multiplayerStore` import carries `type `. Adding a value import there reds that test.
2. Add `import type { … }` for anything needed from `../services/tournamentClient` — likewise type-only, for the same architectural reason (that module has runtime exports).
3. Append `ViewerRelation` + `viewerRelation`, `FailureLabel` + `failureLabel`, and `isActiveEntrant` exactly as specified in §4.3, each with the doc comment prose given there. Four paragraphs are load-bearing and must ship verbatim in substance: the precedence-is-display-only paragraph, the `errors.notFound`-is-not-here paragraph, `isActiveEntrant`'s fails-closed-in-both-directions paragraph, and its citation of `authorize_player`'s C2 refusal.
4. `failureLabel` ends `const unreachable: never = failure; return unreachable;` — **no `default:` arm**. `isActiveEntrant` has no union to walk and therefore no `never` terminal; do not invent one.
5. Add one sentence to the module header naming `failureLabel` as **a further exhaustive walk, over the failure-reason union rather than a wire union**. **Attach no ordinal to it, and do not restate a total export or walk count anywhere** — state the convention, not the number. (Phase 4 burned two review rounds on a drifting export count; revision 1 of *this* plan then broke the same rule two sentences after writing it, by calling `failureLabel` "the fifth exhaustive walk" — see §4.3's m3 note for why any ordinal there is wrong on both available counts.) The header's existing wire-union sentence is accurate as written and must not be renumbered.
6. `isActiveEntrant` needs `PlayerSummary`… **already imported** — `tournamentPageState.ts`'s existing `import type { … } from "../adapter/types"` block lists `PlayerSummary` and `TournamentView` today (both are used by `gameWinsEntries`/`myPairing`). Verify before adding; `noUnusedLocals` bites on a duplicate, and a needless edit to that import block is churn in a file another agent may hold.

7. **Correct the stale third-authority count in `isReportable`'s own doc comment (round 2's M1(a)).** This is the *one* permitted edit to already-shipped prose in this file, and it is a **one-sentence replacement, not a rewrite** — the rest of that doc comment (the `Bye`/`Forfeit` arm analysis, the re-reportable `Reported` reasoning, the predicate-form rationale) is correct and must be left byte-identical.

   **Why it is wrong today:** the comment's closing sentence enumerates the authorization guard as **one** authority and asserts *"both are required"* — a count written in phase 4, before this plan's §0.2 established that the broker's `authorize_player` enforces **three** conjuncts. After this phase there are **three** client-side authorities gating a report click, exactly mirroring C1/C2/C3: `viewerRoles` (C1 — is this viewer a player at all), `isActiveEntrant` (C2 — has that player not dropped; the export item 3 adds), and `myPairing` (C3 — is that player seated in *this* pairing; §5.5 item 5 supplies `onReport` only to `[myPairing(...)]`). Leaving the comment at one/"both" would make the very file this phase edits contradict the correction this phase exists to apply — and, unlike the frozen `PairingsList.tsx` case (§7.4), it is in scope and costs one sentence.

   **Current text, verbatim** (the last paragraph of the doc comment immediately above `export function isReportable`):
   ```
    * This answers "can this pairing be reported by anyone", NOT "may this viewer
    * report it". Authorization is a separate, orthogonal guard on the caller's
    * side ({@link viewerRoles}); both are required.
   ```
   **Replace that paragraph — and only that paragraph — with:**
   ```
    * This answers "can this pairing be reported by anyone", NOT "may this viewer
    * report it". Authorization is a separate, orthogonal guard on the caller's
    * side, and it is *three* conjuncts, mirroring the broker's own three
    * refusals for a report — `authorize_player`'s token and dropped checks
    * plus `handle_report_match_result`'s seat check
    * (`crates/lobby-broker/src/broker.rs`): {@link viewerRoles} — is this viewer
    * a player at all; {@link isActiveEntrant} — has that player not dropped; and
    * {@link myPairing} — is that player seated in THIS pairing. This arm gate
    * plus all three are required; none of the four is sufficient alone.
   ```
   **Executor notes.** Re-read the file immediately before this edit and match the existing text exactly (it is prose another agent may have touched). Keep the file's ` * ` comment prefix and wrap width. Do **not** renumber, re-word, or "harmonise" any other doc comment in the file while here. `{@link isActiveEntrant}` resolves because item 3 adds that export to this same module. No test asserts on this comment's text, so this edit changes no test outcome — it is a correctness-of-documentation fix, and V-matrix coverage is unaffected.

### 5.2 `client/src/App.tsx` — two routes (U1)

1. After the existing `ReplayPage` lazy declaration (`:38`), add, matching the surrounding one-line style:
   ```tsx
   const TournamentLandingPage = lazy(() => import("./pages/TournamentLandingPage").then((m) => ({ default: m.TournamentLandingPage })));
   const TournamentPage = lazy(() => import("./pages/TournamentPage").then((m) => ({ default: m.TournamentPage })));
   ```
2. Inside the existing `<Route element={<AppShell />}>` block (`:116-127`), after the `/draft/quick` line and before `/draft-pod`, add:
   ```tsx
   <Route path="/tournament" element={<DevStrict><TournamentLandingPage /></DevStrict>} />
   <Route path="/tournament/:code" element={<DevStrict><TournamentPage /></DevStrict>} />
   ```
   **Both inside the layout route** (S7) so the rail/tab bar/scene are present. **Both `DevStrict`-wrapped**, matching the **8 of the 10** existing routes inside that layout route that are wrapped (`/`, `/setup`, `/multiplayer`, `/my-decks`, `/deck-builder`, `/coverage`, `/draft`, `/draft/quick`) — the two that are **deliberately not** wrapped, `/draft-pod` (`:125`) and `/draft-spectator` (`:126`), are other, shipped work and must not be touched or "made consistent". The double-effect-invoke `DevStrict` causes in DEV is exactly what V15 tests, which is why the two new routes take the wrapped form.
3. Touch nothing else in this file. Do not reorder existing routes.

### 5.3 `client/src/components/chrome/navIcons.tsx` + `navItems.tsx` + `navItems.test.ts` (U1)

1. **`navIcons.tsx`** — append an inline SVG component after the five `sectionIcon(...)` consts, following `SparkleIcon.tsx`'s exact shape (`viewBox="0 0 24 24"`, `fill="currentColor"`, `aria-hidden="true"`, `className` passthrough). A trophy glyph. Add a short comment stating why this one is an SVG and not `sectionIcon("tournament", …)`: **there is no `/icons/sections/tournament.png`**, and a dangling `<img src>` is invisible to happy-dom and broken only in production (probe P7). Name it `TournamentNavIcon` to match the file's `…NavIcon` convention.
2. **`navItems.tsx`** — import `TournamentNavIcon` and append one row to `NAV_ITEMS`:
   ```tsx
   { key: "tournament", path: "/tournament", labelKey: "nav.tournament", Icon: TournamentNavIcon, match: (p) => p.startsWith("/tournament") },
   ```
   `labelKey` resolves in the **`menu`** namespace (`en/menu.json`'s `nav` block), which is what `Rail`/`TabBar` call `t()` with — **not** the `tournament` namespace. `nav.tournament` already exists in all 7 `menu.json` files (phase 3).
3. **`navItems.test.ts` (S6)** — in the same commit: rename `"exposes exactly the five primary destinations"` → `"exposes exactly the six primary destinations"` and append `"tournament"` to the expected array. Add two assertions to the existing `"lights the primary destinations on their own routes"` and `"keeps sub-routes under their section"` cases: `expect(activeNavKey("/tournament")).toBe("tournament")` and `expect(activeNavKey("/tournament/ABC123")).toBe("tournament")`. **Probe P2 measured that exactly one existing assertion reds and the other four stay green** — if anything else reds, stop and report.

### 5.4 `client/src/pages/TournamentLandingPage.tsx` — new (U3)

Composition, mirroring `MultiplayerPage`'s chrome exactly:

```tsx
export function TournamentLandingPage() {
  const { t } = useTranslation("tournament");
  const navigate = useNavigate();
  const embedded = useInShell();
  …
}
```

**State:** `tournaments: TournamentSummary[] | null` (`null` = loading), `offline: boolean`, `failure: FailureLabel | null`, `busy: "create" | "join" | null`, `joinCode: string`, `joinName: string`.

**Store selectors (one per action, as `MultiplayerPage` does):** `subscribeTournaments`, `createTournament`, `joinTournament`, and `tournamentCredentials` (for the role badge).

**Subscription effect:** §4.5 verbatim. Handlers: `onListUpdate: (list) => setTournaments(list)`. **`onTournamentRemoved` is deliberately NOT handled here** — the store's `tournamentListSnapshot` doc forbids filtering the list client-side, and the next `TournamentListUpdate` replaces it wholesale. Write that reason as a comment; a future reader will otherwise "fix" it.

**Render:**

- `{!embedded && <MenuParticles />}`, `<ScreenChrome onBack={() => navigate("/")} … />`, then `<MenuShell eyebrow={t("page.eyebrow")} title={t("page.landingTitle")} description={t("page.landingDescription")} layout="stacked" contentWidthClass="max-w-3xl">`.
- **Failure region** (`role="alert"`) when `failure !== null`: `"message" in failure ? t(failure.key, { message: failure.message }) : t(failure.key)`. When `offline`, render `t("errors.connectionLost")` in the same region.
- **List section:** `<h2>{t("list.heading")}</h2>`; `tournaments === null` → `t("list.loading")`; `[]` → `t("list.empty")`; else a `<ul>` where each `<li>` renders the page-owned **role badge** — `{relation !== "spectating" && <span …>{t(\`labels.${relation}\`)}</span>}` where `relation = viewerRelation(viewerRoles(tournamentCredentials[s.code]))` — beside `<TournamentListItem summary={s} onOpen={(code) => navigate(\`/tournament/${code}\`)} />`. **The badge lives in the page's `<li>`, not inside the component**, because `TournamentListItem`'s props are frozen and phase 5 must not edit it. The `!== "spectating"` suppression is a legible domain predicate, not key-string sniffing: a 20-row list all reading "Spectating" is noise, while "Organizer"/"Entered" is exactly the at-a-glance fact the badge exists for.
- **Create section:** `<CreateTournamentForm submitting={busy === "create"} onSubmit={handleCreate} />`. `initialArity` is left at its default — see §7.3.
- **Join section:** `<h2>{t("join.heading")}</h2>`, a code input (`join.codeLabel`/`join.codePlaceholder`), a display-name input (`join.displayNameLabel`/`join.displayNamePlaceholder`), and a submit button (`join.submit` / `join.submitting`).

**Handlers:**

```
handleCreate(req):  setBusy("create"); setFailure(null);
                    const r = await createTournament(req);
                    setBusy(null);
                    if (!r.ok) { setFailure(failureLabel(r)); return; }
                    navigate(`/tournament/${r.value.code}`);   // the broker-minted code:
                                                               // the reply is the ONLY authority
handleJoin():       same shape via joinTournament(joinCode, joinName), navigating on r.value.code
```

Both are ungated RPCs, so `failureLabel` here only ever produces the four wire arms — but it is called through the same function, so a future gated action added to this page needs no new mapping.

**No `setTournaments` from any RPC return value** (B6).

### 5.5 `client/src/pages/TournamentPage.tsx` — new (U4)

```tsx
export function TournamentPage() {
  const { code = "" } = useParams<{ code: string }>();
  const { t } = useTranslation("tournament");
  …
}
```

**State:** `view: TournamentView | null`, `offline: boolean`, `failure: FailureLabel | null`, `removed: boolean`, `busy: "start" | "end" | "drop" | "report" | null`, `reporting: TournamentPairingView | null`.

**Authority (three conjuncts, mirroring the broker's own three report-refusals — `authorize_player`'s token/dropped checks plus `handle_report_match_result`'s seat check — §0.2):**
```ts
// C1 — token possession. From the store's credential map, never from the view.
const credential = useMultiplayerStore((s) => s.tournamentCredentials[code]);
const roles = viewerRoles(credential);
const relation = viewerRelation(roles);          // display badge only, never a gate

// C2 — server state. From the view, never from the credential: a successful
// drop clears no credential (the store forgets one only on TournamentRemoved),
// so `roles.has("player")` alone renders affordances the broker refuses every
// time. See §0.2(a)/(b). `view === null` is the loading branch, which renders
// no controls at all, so short-circuiting here is not a third policy.
const canPlayerAct =
  view !== null &&
  roles.has("player") &&
  isActiveEntrant(view, credential?.playerKey);

// C3 — the seat conjunct, for reporting only: `myPairing` below.
```
`canPlayerAct` is computed **once** and used by both player affordances, so the two gates cannot drift apart. It is deliberately **not** widened to cover the organizer controls: `authorize_organizer` has no dropped-equivalent, and a playing organizer who drops must keep Start Round and End Tournament (§0.2's table).

**Subscription effect** (§4.5), handlers:
- `onTournamentUpdate: (c, v) => { if (c === code) setView(v); }` — **the code conjunct is B1 and is load-bearing** (V6).
- `onTournamentRemoved: (c) => { if (c === code) setRemoved(true); }` → renders `t("errors.notFound")`. This is the sole producer of that key (§4.3).
- `onListUpdate: () => { void seed(); }` — the re-seed of §4.7.

**Seeding**, sequenced **after** the subscription resolves (so the `ToSelf` reply cannot arrive before a listener exists — the same ordering invariant phase 2's F2 made structural in the store):
```
const d = await subscribeTournaments(handlersRef.current);
if (cancelled) { d?.(); return; }
if (d === null) { setOffline(true); return; }
detach = d;
void seed();                               // getTournament(code)
```
`seed()` awaits `getTournament(code)` and, on `!ok`, `setFailure(failureLabel(r))`. **It never calls `setView`** (B6) — the view arrives through `onTournamentUpdate`, which sees the same frame.

**Render** (all through `t()` in the `tournament` namespace):

1. `removed` → `t("errors.notFound")` and nothing else. `offline` → `t("errors.connectionLost")`. `view === null` → `t("detail.loading")`.
2. **Header:** `<MenuShell eyebrow={t("page.eyebrow")} title={view.summary.name} description={t("page.detailDescription", { code })}>`; a back affordance to `/tournament` labelled `t("page.backToList")`; the code badge `t("labels.code", { code })`; `t(\`status.${view.summary.status}\`)`; `t(\`bracket.${view.summary.bracket}\`)`; the arity label via `arityLabel`; `view.summary.current_round > 0 && t("labels.roundOf", {…})` (matching `TournamentListItem`'s own suppression of the Registration case); and the **role badge** `t(\`labels.${relation}\`)` — here rendered **always**, including "Spectating", because on a single-tournament page the viewer's relation to *this* event is exactly the thing worth stating.
3. **Organizer controls** — `roles.has("organizer") && (…)`: a block titled `t("detail.organizerControls")` with **Start Round** (`detail.startRound` / `detail.startRoundBusy`) and **End Tournament** (`detail.endTournament` / `detail.endTournamentBusy`, confirmed via `window.confirm(t("detail.endTournamentConfirm"))` — the same `window.confirm`/`window.prompt` posture `MultiplayerPage` already uses).
4. **Player controls** — **`canPlayerAct && (…)`**, *not* `roles.has("player")`: **Drop** (`detail.drop` / `detail.dropBusy`, confirmed via `t("detail.dropConfirm")`). The `canPlayerAct` conjunct is what makes the button disappear the moment the viewer's own drop comes back on the `TournamentUpdate` broadcast — the broker permanently refuses a second drop by design (§0.2(a)), so a still-rendered button here can only ever produce an alert. RC9 reds if the conjunct is weakened back to `roles.has("player")`.
5. **Your Match** — `<h2>{t("detail.yourPairing")}</h2>`; `const mine = myPairing(view, credential?.playerKey);`
   ```tsx
   {mine === null
     ? <p>{t("detail.noPairing")}</p>
     : <PairingsList
         pairings={[mine]}
         onReport={canPlayerAct ? setReporting : undefined}
       />}
   ```
   **This is the only place `onReport` is ever supplied** (§0.2). `PairingsList`'s own `isReportable` arm gate then decides whether the button renders for a bye/forfeit — phase 5 adds no second gate and duplicates no arm logic.

   **`canPlayerAct`, not `roles.has("player")`, and the arm gate does not cover this** (§0.2(b), RC10). A dropped entrant in a ≥3-seat pod keeps a live pairing: `drop_player` auto-forfeits only when exactly one active seat remains, so with ≥2 active seats left the pairing stays `outcome: null` and the dropped player stays in `pairing.players` (*"a drop does not retroactively rewrite history"*). `myPairing` therefore still matches (C3 passes) and `isReportable(null)` is `true` (the arm gate passes) — C2 is the **only** conjunct that refuses, so it must be present here or the Report button is dead. Note the asymmetry with item 4: the Drop button is dead for a *self-evident* reason (you just dropped), while this one is dead for a reason the viewer cannot see at all, which is why the fixture in V22 uses the pod shape rather than the head-to-head one.
6. **Standings** — `<h2>{t("standings.heading")}</h2>` + `<TournamentStandingsTable standings={view.standings} />`.
7. **Pairings (full history)** — `<h2>{t("pairings.heading")}</h2>` + `<PairingsList pairings={view.pairings} />` — **no `onReport`**.
8. **Dialog** — rendered when `reporting !== null`:
   ```tsx
   <ReportResultDialog
     isOpen
     pairing={freshPairing}
     submitting={busy === "report"}
     onSubmit={handleReport}
     onCancel={() => setReporting(null)}
   />
   ```
   `freshPairing` is `view.pairings.find(p => p.id === reporting.id) ?? reporting` — re-derived from the live view on every render so a broadcast arriving while the dialog is open cannot leave a stale seat list in the payload (B5). No `key={pairing.id}` is passed; phase 4's fix round made the reset structural and its prop doc says so explicitly.

**Handlers** — all four share one shape, and **none writes `view`**:
```
async function run(kind, action) {
  setBusy(kind); setFailure(null);
  const r = await action();
  setBusy(null);
  if (!r.ok) setFailure(failureLabel(r));
  // NOTE: no setView here, ever — see the comment below.
}
```
Above `run`, a comment that must ship verbatim in substance:

> The result is used for the failure alert only. It is **never** written to `view`. The four gated RPCs settle on a `TournamentUpdate` **broadcast** that carries no request-vs-broadcast discriminator (`services/tournamentClient.ts`, module header part 4), so `{ok:true}` may be another actor's view and `{ok:false}` may arrive after a foreign frame already settled the promise. The alert is therefore **best-effort**, and the rendered state is always the ambient subscription's. Do not "fix" this into an authoritative signal.

`handleReport(outcome)` calls `reportMatchResult(code, reporting.id, outcome)` and clears `reporting` on `ok`.

### 5.6 `AppShell.tsx` — DECIDED: not touched

The charter offers `AppShell.tsx` conditionally, "only if the tournament pages want the status banner." **They do not.** Reasons, recorded so this is not silently re-decided:

1. The gate's own comment (`AppShell.tsx:45-50`) says it is deliberately narrow — the banner's fetch **and poll** start only on the gated routes, and the gate is "also load-bearing for layout … so widening it is not free."
2. The operator status banner is about **server/lobby health**, which the landing page already surfaces contextually via `errors.connectionLost` on the `detach === null` branch — more specific, and rendered exactly where the user is.
3. It is the only shared-chrome file this phase could touch beyond the nav table (S7 asks for surgical additions); declining it keeps the shared-file blast radius to `App.tsx` + the two nav files.

Net: the charter's "+1 conditional" scope-path is **not** taken (§4.11).

---

## §6 — Verification Matrix

**Counting convention (stated once, as a convention rather than as a total, so it cannot drift — m2).** Claims are numbered `V1..Vn`. A claim that needs two rows because it is proven at two different levels — once as a pure unit assertion and once through a mounted page — carries a **lettered sibling** under the same number rather than a new number, so the claim count and the row count differ by exactly the number of lettered siblings. There are two such pairs: **V4/V4b** (organizer gating, pure vs. rendered) and **V22/V22b** (revision 2's dropped conjunct, pure vs. rendered). So this matrix is **22 numbered claims across 24 rows**. Revert-checks are `RC1..RCn` in §6.5, one row each, currently ending at **RC10**. Every negative names its **paired positive reach-guard** — a bare negative that an upstream short-circuit could satisfy vacuously is not a test. Test files are excluded from T2 counting but are listed in §4.11's hostile-convention table. **Anyone extending this matrix appends a number (or a lettered sibling) and leaves these sentences alone; do not edit a fresh total into the prose.**

### 6.1 Harness

Both page test files copy the fake-socket harness from `stores/__tests__/multiplayerStore.tournament.test.ts:66-165` — `makeFakeSocket()` (with `send`, `deliver`, `listenerCount`, `tally`, `frame`), `primeSocket()`, `flush()`. **Copied, not imported:** it is defined inside a test file today, and extracting it to a shared module would edit phase 2's committed test file, which is out of scope. `tally()` compares **exact parsed frame tags**, sidestepping the charter's broken `(?:Un)?SubscribeLobby` regex entirely (phase 1's erratum).

**Mocked:** only `../../services/openPhaseSocket` (the transport seam) and `../../components/chrome/ScreenChrome` (it reaches `ChromeControls → AccountControl`). **Not mocked, deliberately:** `multiplayerStore`, `tournamentClient`, `brokerClient` — mocking any of them would make every frame assertion vacuous (phase 2's own justification, and `multiplayerStore.visualAvatars.test.ts` is the precedent that the real import graph resolves under vitest).

**`localStorage`:** the `vi.hoisted` shim from `multiplayerStore.tournament.test.ts:3-25` is copied, because the store's persist middleware touches it and this worktree's Node build has the standing `--localstorage-file` issue.

**RTL cleanup:** this repo's vitest config has **no `globals: true`**, so RTL's auto-cleanup never registers. Both files must `import { cleanup } from "@testing-library/react"` and call it in an `afterEach` — the same scoped fix phase 4 applied to its five component test files. Do **not** edit `test-setup.ts`.

**Render helper:**
```tsx
render(
  <MemoryRouter initialEntries={["/tournament/TOUR01"]}>
    <Routes><Route path="/tournament/:code" element={<TournamentPage />} /></Routes>
  </MemoryRouter>,
);
```

**Fixture caution:** `expectNoRawKeyPaths`'s `RAW_KEY_PATH` is `/^[a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+$/`. Fixture `display_name`s must not be lowercase-dotted (`"alice.smith"` would false-positive). Use `"Alice"`, `"Bob"`, `"Cara"`, `"Dana"`. Tournament codes like `"TOUR01"` start uppercase and are safe.

**Query caution — the detail page renders `PairingsList` twice (m5).** §5.5 mounts it once for "Your Match" (`[mine]`) and once for the full round-by-round history (`view.pairings`), and the viewer's own pairing is in **both**. Every string `PairingsList` emits per row — `t("pairings.round", …)`, `t("pairings.table", …)`, `t("pairings.versus")`, `t("pairings.pending")`, `t("detail.reportResult")`, and each seat's `display_name` — therefore appears **at least twice** in the detail page's DOM. A bare `getByText("Round 1")` throws *"Found multiple elements"* — a confusing failure that looks like a production bug and is not one. Two remedies, and every row below that queries pairing text must use one of them explicitly:

- **`within(...)` scoping** where the assertion is about *one* of the two lists. Scope by heading: `const mySection = screen.getByRole("heading", { name: t("detail.yourPairing") }).closest("section")!;` then `within(mySection).getByText(...)`. Use this for **V5** (whose whole claim is that the "Your Match" section narrows while the full list does not) and for **V14** (the dialog is opened from the "Your Match" list specifically).
- **`getAllByText` / `queryAllByText` with an explicit expected length** where the assertion is about *how many* of something exist page-wide. Use this for **V22b** and **V4b** (both count Report buttons across the whole page — which is the point: a stray `onReport` on the history list must be caught, and RC5 depends on exactly that), and anywhere V13's rich fixture asserts presence.

Never assert a pairing-derived string with a bare `getByText` on the detail page. `TournamentLandingPage.test.tsx` is unaffected — it renders no `PairingsList` at all. Confirmed non-issue for accessibility identity: `PairingsList` emits no `id` or `aria-labelledby`, so the double render creates no duplicate-id collision, only duplicate text nodes.

### 6.2 U1 — Reachability

| # | Claim | Changed seam | Production entry | Test | Revert-failing assertion | Negative / hostile | Reach-guard |
|---|---|---|---|---|---|---|---|
| **V1** | `/tournament` lights the nav item | `NAV_ITEMS` | `activeNavKey` (Rail :24, TabBar :21) | `navItems.test.ts` | `expect(activeNavKey("/tournament")).toBe("tournament")` | `expect(activeNavKey("/coverage")).toBeNull()` (existing case, must stay green — **measured green under the added item in P2**) | V2 |
| **V2** | The detail sub-route lights the same item | same | same | same | `expect(activeNavKey("/tournament/ABC123")).toBe("tournament")` | `activeNavKey("/multiplayer")` still `"online"` | V1 |
| **V3** | S6's exact-array test is updated, not deleted | `navItems.test.ts` | — | same | array equals the **six** keys in order, test renamed to "six" | Deleting the case entirely would pass vacuously — the case must exist and name six | the four other cases stay green (P2/P3 measured: delta is exactly one test) |

**S6 status:** expected red → updated in the same commit. **Not** a regression.

### 6.3 U2 — Page-state derivations

| # | Claim | Test | Revert-failing assertion | Negative / hostile | Reach-guard |
|---|---|---|---|---|---|
| **V7** | `viewerRelation` is total and organizer-dominant | `tournamentPageState.test.ts`, `it.each` over 4 credential shapes | `{organizerToken}`→`"organizer"`; `{playerToken}`→`"entered"`; `undefined`→`"spectating"`; **`{organizerToken, playerToken}`→`"organizer"`** (the playing-organizer case phase 2 called normal) | `{}` with neither token → `"spectating"`, not a throw | assert all four distinct outputs actually occurred (a function returning `"spectating"` always would fail three of four) |
| **V8** | `failureLabel` is total over all six failure shapes | `it.each` over 6 inputs | each maps to its key; `"rejected"` carries `message` **verbatim, untranslated** (feed `"Tournament not found: X"` and assert the label's `message` is byte-identical) | the two `not_authorized` roles map to **different** keys — a mapping keyed on `reason` alone would collapse them | assert `"message" in label` is `true` for exactly the `rejected` case and `false` for the other five |
| **V9** | The `never` terminal is load-bearing | compile-time mutation (RC1) | deleting the `"timeout"` arm produces a real `TS2322` on the `never` binding | — | the unmutated file type-checks clean first |
| **V22** | `isActiveEntrant` is the C2 conjunct, and fails closed both ways | `tournamentPageState.test.ts`, `it.each` over 4 shapes against one fixture `view` | active entrant → `true`; **dropped entrant → `false`**; `playerKey` absent from `view.players` → `false`; `playerKey === undefined` → `false` | a function that only read `dropped` (ignoring the identity join) would answer `true` for a **foreign** key, so the unknown-key case is the sibling that discriminates the join from the flag; and a function that only performed the join would answer `true` for the dropped case | assert all four outputs occur and that **exactly one** of the four inputs yields `true` — a constant `false` (the trivial way to pass a matrix of three falses) fails the active case |

### 6.4 U3 / U4 — Mounted pages

| # | Claim | Changed seam | Production entry | Test | Revert-failing assertion | Negative / hostile fixture | Reach-guard |
|---|---|---|---|---|---|---|---|
| **V10** | **Discharges phase 1's `DEFERRED(phase 5)` — `ToSubscribers`-only delivery.** State comes from the ambient broadcast, never the RPC return | `TournamentPage` handlers | click Start Round / Report / Drop / End | `TournamentPage.test.tsx`, `it.each` over the 4 gated actions, on a **real store-owned, subscribed** fake socket mounted through the page | For each: click → deliver an **`Error`** frame (settles the RPC `{ok:false}`) → deliver a `TournamentUpdate` carrying the new state → **assert the DOM shows the new state AND the `errors.serverRejected` alert**. A page that rendered from the RPC return could never show the new state on this path | (a) deliver only the `Error`, no broadcast → DOM unchanged; (b) deliver a `TournamentUpdate` with **no RPC in flight** → DOM still updates (probe P6 proves the mechanism) | `expect(fake.tally("StartTournamentRound")).toBe(1)` etc. — the request frame really went out, so a silently no-op page cannot satisfy the assertion vacuously |
| **V11** | No page ever writes a view from an RPC result | both pages | — | source-level assertion in `TournamentPage.test.tsx`: `readFileSync` of `TournamentPage.tsx`, assert `/setView\s*\(\s*[a-z]\w*\.value/` finds **nothing** | — | positive control: the same regex **must** match the fixture string `setView(result.value.view)` (else it could pass vacuously) — the identical control shape phase 1 used for its static assertion |
| **V12** | The detail view re-seeds on `onListUpdate` (reconnect recovery, §4.7) | seed effect | any list push | `TournamentPage.test.tsx` | after mount settles, clear `send`; `fake.deliver("TournamentListUpdate", {tournaments: []})`; assert `fake.tally("GetTournament") === 1` | delivering a `TournamentUpdate` (not a list update) must **not** issue a `GetTournament` — otherwise it would be a refetch-on-everything loop | the initial mount's own `GetTournament` is asserted first (tally goes 0→1 before the clear) |
| **V13** | **Discharges phase 3's `DEFERRED(phase 5)` — key-set completeness across mounted pages.** Claim, scoped exactly to what the helper can see: **no raw key path leaks into a rendered *text node*** | both pages | — | both page test files | `expectNoRawKeyPaths(container)` on a **rich** fixture: `InProgress`, 4 standings rows (both `Tiebreaks` arms exercised across two renders), pairings covering bye + head-to-head + a 4-seat pod × all four outcome arms + a pending `null`, one dropped entrant, organizer+player credential, dialog open. Use `getAllByText`/`within` for any pairing-derived assertion (§6.1's query caution) | render the same page with the credential **absent** and assert no raw key paths either (the spectator branch renders different copy) | `expectCatalogValuePresent(container, "Standings")` — a page that rendered nothing cannot satisfy the negative |
| **V14** | The report dialog submits the pairing it is showing | `ReportResultDialog` mounted by the page | open dialog → deliver a broadcast → submit | `TournamentPage.test.tsx` | open the dialog on pairing `id=1`, enter a winner, then deliver a `TournamentUpdate` whose `pairings[0]` for `id=1` has a **changed seat list**; submit; assert the emitted `ReportMatchResult` frame's `pairing_id === 1` and its `winner` is a seat present in the **fresh** list | a payload naming a seat only in the stale list must be impossible | assert the frame was sent at all (`tally("ReportMatchResult") === 1`) |
| **V15** | **Discharges phase 2's `DEFERRED(phase 5)` — unmount during in-flight connect** (#4615) | subscription effect | mount → unmount | both page test files | prime `openPhaseSocket` with a **deferred** promise; render; `unmount()`; resolve; `await flush()`; assert `fake.listenerCount("message") === 0` **and** `fake.tally("UnsubscribeLobby") === 1` | remove the `if (cancelled) { d?.(); return; }` line and this reds (RC2) | the same flow **without** unmounting leaves `listenerCount("message") >= 1` and delivers a broadcast to the page (probe P6 measured 2→0 across a normal detach, so the instrument is real) |
| **V4** | **Discharges phase 2's `DEFERRED(phase 5)` — organizer gating as rendered UI** | `roles.has("organizer")` | detail page render | `TournamentPage.test.tsx` | credential for **`TOURA`** only, page mounted on **`TOURB`** → `queryByText(t("detail.startRound"))` is `null`, ditto End Tournament | with the credential for `TOURB`, both controls render | the positive case asserts both control labels **present**, so a page rendering nothing cannot satisfy the negative |
| **V4b** | **The §0.2 correction, as rendered UI** — C1 is what refuses here (no player token at all), which is why this row and V22b are distinct claims rather than one | `canPlayerAct`'s `roles.has("player")` conjunct, on the report affordance | detail page | same | organizer-**only** credential viewing **its own** tournament, with the viewer seated in no pairing → **zero** Report buttons anywhere; organizer controls **do** render | player credential + own current-round pairing → **exactly one** Report button, and it is inside the "Your Match" section | assert `getAllByText(t("detail.reportResult")).length === 1` in the positive case — proving the detector fires |
| **V22b** | **The C2 conjunct as rendered UI — revision 2's M1 discharge.** A dropped entrant is offered neither player affordance | `canPlayerAct` (both gates, §5.5 items 4 and 5) | detail page render | `TournamentPage.test.tsx`, **one shared hostile fixture, two viewers** | **Fixture (every clause below is load-bearing; the three marked ★ are the ones that stop this fixture from passing *vacuously*, i.e. for a reason other than C2):** `status: "InProgress"`, `current_round: 1`; one **4-seat pod** pairing with ★ **`round: 1`, i.e. exactly equal to `summary.current_round`** — `myPairing` conjoins a round match, so a pairing on any other round makes C3 fail closed and Alice's "zero buttons" assertion passes for the wrong reason, proving nothing about the dropped conjunct; ★ **`outcome: null`** (a genuinely `Pending` pairing, so `isReportable` passes and cannot be what refuses); seats `Alice, Bob, Cara, Dana` as `pairing.players` with ★ **`Alice.dropped === true` on her `PlayerSummary`** — both on `view.players` (which is what `isActiveEntrant` reads) **and** on her per-seat entry in `pairing.players` — and the other three active. Additionally, and separately from `PlayerSummary`: **Alice's `TournamentStanding.dropped` must also be `true`** on her row in `view.standings`. That is a *different field on a different part of the wire shape*, and it is the one the third assertion below actually reads — phase 4's `TournamentStandingsTable` renders its `labels.dropped` chip off `TournamentStanding.dropped`, never off `PlayerSummary.dropped`, so setting only the latter would leave the chip absent and the third assertion would fail for a fixture reason rather than a product reason. This is the exact shape `drop_player` leaves behind, since ≥2 active seats remain and the `(Some(survivor), None)` forfeit guard does not fire. **Viewer 1 = Alice** (holds a valid `playerToken` + `playerKey: "alice"` for this code): assert `queryAllByText(t("detail.reportResult")).length === 0` **and** `queryByText(t("detail.drop")) === null`. Weakening either gate to `roles.has("player")` reds this (RC9/RC10) | **Paired positive reach-guard, same fixture, same render helper, viewer 2 = Bob** (active, `playerKey: "bob"`, same credential shape): assert **exactly one** Report button (`getAllByText(t("detail.reportResult")).length === 1`) **and exactly one** Drop button. This is what forbids the vacuous pass — a page that rendered neither button for anybody, or that failed to render at all, satisfies Alice's case trivially and fails Bob's. **Third case, to prove C2 is what refuses and not C1 or C3:** Alice's own row must still be visible in the "Your Match" section (`myPairing` matched — C3 passed) and her `labels.dropped` chip must render in the standings (phase 4's `TournamentStandingsTable`), so the page is demonstrably *showing* her the pairing while *withholding* the action | `expectCatalogValuePresent(container, …)` on the "Your Match" heading in **both** viewers' renders, so neither assertion can be satisfied by an unrendered section |
| **V5** | Only the viewer's own pairing is offered | `myPairing` | detail page | same | a 4-entrant, 2-pairing round where the viewer is seated in pairing `id=2` → the "Your Match" section renders pairing 2's seats and the full list still renders both | a viewer with **no** `playerKey` → `t("detail.noPairing")` and zero Report buttons | the full pairings list renders both pairings in both cases (so the "Your Match" filter is doing the narrowing, not a broken view) |
| **V6** | A foreign-code broadcast cannot touch this page | `if (c === code)` | detail page | same | deliver `TournamentUpdate` for `"OTHER"` with a different `name`; assert the heading is unchanged | deleting the code conjunct reds this (RC3) | delivering the **same** code with the new name **does** change the heading |
| **V16** | The list renders from `onListUpdate` | landing subscription | `/tournament` | `TournamentLandingPage.test.tsx` | deliver `TournamentListUpdate` with 2 summaries → 2 rows, **in the array order given** | deliver a 2-row list whose `player_count` order is non-monotonic and assert DOM order still equals array order (no client sort) | `expect(fake.tally("SubscribeLobby")).toBe(1)` |
| **V17** | The list is never filtered on `TournamentRemoved` | landing handlers | — | same | deliver a 2-row list, then `TournamentRemoved` for row 1 → **still 2 rows** (the store's stated contract) | a page that filtered would show 1 | after a subsequent `TournamentListUpdate` with 1 row, the DOM shows 1 — proving the list does track the server |
| **V18** | Create navigates on the **reply's** code | `handleCreate` | submit the form | same | submit; deliver `TournamentCreated` with `code: "NEWC01"`; assert `navigate` called with `/tournament/NEWC01` | deliver a reply with a **different** code than anything typed and assert the navigation follows the **reply** (the broker mints it; nothing client-side can) | assert `fake.tally("CreateTournament") === 1` and that the sent frame's `data.arity`/`data.scoring` match what the form held |
| **V19** | Join navigates and sends the typed code | `handleJoin` | submit | same | assert the `JoinTournament` frame's `data.code` is the typed code and `data.display_name` the typed name; navigate on `TournamentJoined.code` | empty display name still sends (the store falls back to `displayName`/`"Player"`); **no client-side pre-rejection** | `tally("JoinTournament") === 1` |
| **V20** | Failures render translated copy, not raw English | `failureLabel` + the alert region | any failure | both files | `it.each` over the six failure shapes forced through a create/start action: assert the rendered text equals the **English catalog value** for the mapped key (and for `rejected`, that the raw server message appears **inside** it) | assert the raw store fallback string `"You are not the organizer of this tournament."`… **careful:** that English string is *also* `errors.notOrganizer`'s catalog value, so instead assert the alert for a `rejected` failure contains the server's message wrapped in the `serverRejected` template (`"The server rejected that: …"`), which the store never produces | assert at least one alert rendered at all |
| **V21** | The offline branch renders | `detach === null` | server unreachable | `TournamentLandingPage.test.tsx` | prime the transport to fire `"offline"` → assert `t("errors.connectionLost")` renders (probe P5 measured `subscribeTournaments` → `null`) | with a working socket the same text must be **absent** | the working-socket case renders `t("list.heading")` |

**V13's coverage boundary, stated honestly rather than papered over (m4).** `expectNoRawKeyPaths` (`components/tournament/__tests__/tournamentTestUtils.ts`) walks **text nodes only**. A raw key path leaking into an HTML *attribute* — `title`, `aria-label`, `placeholder`, `alt` — is invisible to it. That surface is real and already populated by phase 4's shipped components: `TournamentStandingsTable` uses `title={t("standings.matchPointsTitle")}`, `title={t("standings.matchesPlayedTitle")}`, `title={t("standings.byesTitle")}` and `title={t(cell.titleKey)}`; `CreateTournamentForm` uses `placeholder={t("create.namePlaceholder")}` and `placeholder={t("create.totalRoundsAuto")}`; `ReportResultDialog` uses `aria-label={t("common:actions.closeNamed", { name: title })}`. **There is no live defect** — every one of those keys resolves in the catalog today (independently re-verified), and the four `cell.titleKey` values come from `tiebreakCells`, itself a `never`-terminated exhaustive walk, so the dynamic half is compile-enforced as well. The gap is in the *test*, not the product: nothing here would catch a future attribute-only leak. **Not closed in this phase**, deliberately — attribute coverage means editing `tournamentTestUtils.ts`, phase 4's committed shared test helper, which is outside this phase's scope, for a surface with no known defect and a compile-enforced dynamic half. Recorded as a follow-up in §7.4 so it is a known boundary rather than an overstated claim. **V13's claim is worded "no raw key path leaks into a rendered text node"; do not restate it as "the DOM".**

### 6.5 Revert-checks (run before commit; each must break its named test)

| # | Mutation | Must red |
|---|---|---|
| **RC1** | Delete `failureLabel`'s `"timeout"` arm | `type-check` (TS2322 on the `never`), **not** vitest — the same type-check-vs-vitest distinction phase 1 recorded |
| **RC2** | Remove `if (cancelled) { d?.(); return; }` from either page's effect | V15 |
| **RC3** | Remove `if (c === code)` from `onTournamentUpdate` | V6 |
| **RC4** | Add `setView(r.value.view)` to any handler | V11 (source assertion) — and, deliberately, **not** V10, which is why V11 exists as a separate row |
| **RC5** | Supply `onReport` to the full-history `PairingsList` | V4b (Report button count > 1) |
| **RC6** | Change `canPlayerAct`'s role conjunct from `roles.has("player")` to `roles.has("organizer")` | V4b's organizer-only-credential case |
| **RC7** | Sort `view.standings` before passing it to the table | V13's rich fixture ordering / a dedicated order assertion in V16's shape |
| **RC8** | Filter `tournaments` on `TournamentRemoved` | V17 |
| **RC9** | Weaken the **Drop** gate (§5.5 item 4) from `canPlayerAct` back to `roles.has("player")` | **V22b**, at Alice's `queryByText(t("detail.drop")) === null` assertion. Bob's positive case must stay **green** under this mutation — that is what proves V22b reds on the *dropped* conjunct specifically, and not because the whole player block vanished |
| **RC10** | Weaken the **Report** gate (§5.5 item 5) from `canPlayerAct` back to `roles.has("player")` | **V22b**, at Alice's `queryAllByText(t("detail.reportResult")).length === 0` assertion. Bob's exactly-one assertion must stay green. Note this mutation leaves `myPairing` and `isReportable` untouched and still reds — which is the whole point of §0.2(b): in a ≥3-seat pod with ≥2 active seats, C2 is the **only** conjunct that refuses |

RC9 and RC10 must be run **separately**. Mutating both at once still reds V22b, but at whichever assertion vitest reaches first, which would leave the other gate unproven — the two gates are independent lines of code and each needs its own discriminating evidence. As a third check, mutate `isActiveEntrant` itself to `return true` and confirm **both** V22b assertions red while V22's pure truth table also reds — proving the page really consumes the derivation rather than duplicating the check inline.

Each must be reverted immediately. Because vitest aborts at the first failed assertion, **run each revert-check singly** and confirm it breaks at the *named* assertion — phase 2's executor's practice, adopted here.

### 6.6 Commands (S9 — Tilt does not watch this worktree; exit 3 ≠ failure)

```bash
cd C:/git/phase/.claude/worktrees/tournament-organizer-pr4-frontend/client
pnpm run type-check          # chains protocol:check → check-protocol-version.mjs; MUST be exit 0 (S8)
pnpm run lint                # expect 0 errors; 44 pre-existing warnings, none in touched files
pnpm exec vitest run \
  src/components/chrome/__tests__/navItems.test.ts \
  src/pages/__tests__/tournamentPageState.test.ts \
  src/pages/__tests__/TournamentLandingPage.test.tsx \
  src/pages/__tests__/TournamentPage.test.tsx \
  src/components/tournament/__tests__ \
  src/i18n/__tests__ src/i18n/resources.test.ts
```

**Baselines the executor must not misread (measured, §3.5):** the targeted set above is **311 passing** at `PHASE_BASE_SHA`; the i18n gates are **199** of those and must stay **exactly 199** (zero catalog delta). `src/components/chrome/__tests__` has **15 pre-existing failures** on this machine (Node v25 `--localstorage-file`), unrelated to this phase; with the nav item added the count must be **15**, not 16 (the 16th is the S6 test, fixed in the same commit). `cargo fmt`/`clippy`/`test-engine` are **N/A** — no Rust changes, and no cargo target lock may be taken.

---

## §7 — Deferral discharge, decisions, and findings

### 7.1 Every phase-1..4 deferral attributed to phase 5, audited against the actual log

| # | Deferral | Attributed by | Discharged how |
|---|---|---|---|
| 1 | **`ToSubscribers`-only delivery proven on a real, store-owned, *subscribed*, page-mounted socket** | phase 1 (charter `:63`, `:69`; entries 3–4, retargeted from phase 2 at review round 1) | **V10** — the named fulfilment, with the `Error`-plus-broadcast fixture that makes it genuinely discriminating, plus the frame-tally reach-guard |
| 2 | **Component-level unmount-during-in-flight-connect (#4615)** | phase 2 (charter `:93`) | **V15**, using `LobbyView`'s idiom verbatim |
| 3 | **Organizer-only controls gated on a held token, as rendered UI** | phase 2 (charter `:94`, `:204`) | **V4** (+ **V4b**, which corrects the deferral's own premise — §0.2 — and **V22/V22b**, which apply the correction's *own* second conjunct, `dropped`, to both player affordances; revision 2's M1) |
| 4 | **Key-set completeness across mounted pages** — scoped exactly as §6.4's boundary note scopes it: **no raw key path leaks into a rendered *text node***. Not "reaches the DOM": `expectNoRawKeyPaths` walks text nodes only, so attribute surfaces (`title`/`aria-label`/`placeholder`/`alt`) are outside the claim and are carried as a §7.4 follow-up row instead. Do not restate this discharge with the broader phrasing anywhere | phase 3 (charter `:139`, `:206`) | **V13**, via phase 4's existing `expectNoRawKeyPaths` + `expectCatalogValuePresent` — see **§6.4's V13 coverage-boundary note** for why the narrower wording is the honest one |
| 5 | **Mounting, routing, nav, store wiring, unmount races, live socket behavior** | phase 4 (charter `:178`) | §5.2–§5.5 in full; V1–V3, V10, V12, V15–V21 |
| 6 | **Server-rejection copy wiring** — `errors.serverRejected`/`notOrganizer`/`notEntered`/`timedOut`/`connectionLost`/`aborted`/`notFound` | phase 2's F4 + phase 3's catalog + phase 4's list of 7 deferrals (**Entry 36 — phase 4's implementation checkpoint**) | **`failureLabel`** (§4.3) covers six; `errors.notFound` is produced by the `TournamentRemoved`-for-this-code branch (§5.5). **All 7 `errors.*` keys have exactly one producer.** V8, V20 |
| 7 | **Role badge on a list row** (`labels.organizer`/`entered`/`spectating`) | phase 4 (**Entry 36 — phase 4's implementation checkpoint**) | **`viewerRelation`** + the page-owned `<li>` badge (§5.4) and the detail header badge (§5.5). All three `labels.*` keys now render. Not by editing `TournamentListItem` — its props are frozen |
| 8 | **Abort-on-reconnect** | phase 1 `DEFERRED(phase 2)` (charter `:64`) | **Closed in phase 2** (charter `:91`; entries 22–23 verified `pendingJoinRpcAborts` registration, the `reconnecting` transition, and the `finally`). **No phase-5 residual.** Phase 5's only relationship to it is consuming its output: an aborted RPC surfaces as `errors.aborted` (V8/V20) |
| 9 | **Explanatory copy for a suppressed report action** (optional) | phase 4 (**Entry 36 — phase 4's implementation checkpoint**) | **DECLINED — see §7.2** |
| 10 | **`CreateTournamentForm`'s scoring-prefill provenance (F2 residual risk)** | phase 4 (**Entry 30 — phase 4's plan production**) | **Not a phase-5 obligation** — see §7.3 |

**Audit note:** the orchestrator's brief listed these from memory and asked for verification. The list checks out against the log with **two corrections**: item 8 (abort-on-reconnect) is fully closed in phase 2 and leaves **no** phase-5 residual, contrary to the brief's "check if phase 2 fully closed this"; and item 3's stated gate (`viewerRoles(...).has("organizer")`) is **wrong for reporting** (§0.2).

**Zero new catalog keys — and the consumption claim, restated accurately (m6).** Revision 1 said "all 111 authored `tournament` keys … are consumed by the design above," which is false as written: the design above is not what consumes most of them. Measured against `client/src/i18n/locales/en/tournament.json` (111 leaf keys) and the phase-4 components this phase mounts:

| Consumer | Keys | Notes |
|---|---|---|
| **This phase's own `t()` calls** (§5.4 + §5.5 + `failureLabel`'s six arms + `errors.notFound`) | **49** | Counting each member of a template-indexed family separately, because each is separately reachable: `status.*` ×4, `bracket.*` ×2, `arity.*` ×2 (via `arityLabel`), `labels.organizer`/`entered`/`spectating` ×3 (via `viewerRelation`) |
| **Phase-4 components this phase merely mounts** (`TournamentListItem`, `CreateTournamentForm`, `TournamentStandingsTable`, `PairingsList`, `ReportResultDialog`) — the **remaining** keys, i.e. those the design above never names | **60** | The three buckets partition the 111 exactly (49 + 60 + 2). Some keys are consumed by *both* the design and a component (`status.*`, `bracket.*`, `labels.code`, `labels.roundOf`); those are attributed to the first bucket, so this row is a remainder, not a component total. Includes the 4-member `list.entrants_one/few/many/other` plural family, reached through a single `t("list.entrants", { count })` in `TournamentListItem`, and `labels.dropped`, already rendered as a standings chip |
| **Authored but reached by nothing** | **2** | `join.joined`, `report.cancel` — see below |

So: **109 of 111 keys are consumed once this phase lands**, 49 by this phase's own design and 60 by the components it mounts. Regenerate with `grep -rhoE 't\(\s*"[a-z][A-Za-z0-9.]+"' client/src/pages/Tournament*.tsx client/src/components/tournament/*.tsx | sort -u` plus the template-indexed and plural families listed above; the runtime proof is **V13**, not this arithmetic.

**The two orphans are a finding, not an omission, and are left alone deliberately.** `report.cancel` is superseded: `ReportResultDialog.tsx:264` renders `t("common:actions.cancel")` instead, phase 4's deliberate reuse of the shared action verb (`ReportResultDialog.tsx:168` does the same for `common:actions.closeNamed`). `join.joined` has no site: §5.4 navigates to `/tournament/{code}` the instant a join reply lands, so there is no surface left on which to render a "joined" confirmation, and inventing one — a toast, or cross-page state — is new UX in a terminal phase. **Neither is consumed and neither is deleted:** removing a key touches all 7 catalogs and re-engages S4's three-part contract for zero user-visible benefit, in the phase with no successor to review the change. Named in §7.4 as follow-up. This does not disturb the `errors.*` accounting (7 keys, 7 producers, all reached) or the i18n gates, which assert **parity across locales**, not reachability from code — an orphaned key is present in all 7 catalogs and stays parity-green.

Consequence, unchanged: the 7 `tournament.json` catalogs and `localeParity.test.ts` are **not in this phase's diff**, S4's three-part contract has nothing to satisfy, and the i18n gates must remain at exactly 199 tests.

### 7.2 Decision: decline the "suppressed report action" explanatory copy

Phase 4 left this optional. **Declining**, because:

1. A pairing where `isReportable` is false is a **bye** or a **forfeit**, and `PairingsList` already renders that row's outcome label — `"Bye"` or `"Forfeit — Alice"`. A second string beside it saying "byes cannot be reported" restates what the row already says.
2. Adding it costs a new key in **all 7** catalogs under S4's full three-part contract, for copy that appears only next to a row that is already self-explanatory.
3. It would be **new user-visible copy authored by a terminal phase with no successor to review its translations** — the least favourable moment to add translated strings.

This is a decision, not a deferral: no phase 6 is implied.

### 7.3 Noted, not fixed: `CreateTournamentForm`'s scoring-prefill provenance (phase 4's F2 residual)

`defaultScoringForArity` mirrors the broker's `ScoringPolicy::default_for_arity` (`tournament.rs:217-227`) because `CreateTournament.scoring` is wire-mandatory with no serde default and **no RPC exposes the broker's own default**. Phase 4 disclosed the drift risk and bounded it (prefill only; user-editable; broker-validated). **Phase 5 does not touch it** and does not pass `initialArity`, so the form opens on head-to-head with the matching 3/1/0 prefill. The durable fix is a broker-side default exposed on the wire — named in §7.5 as follow-up, not absorbed here (it would require a Rust protocol change, which is outside this PR entirely).

### 7.4 Run-level completeness check (terminal-phase obligation)

Every wire capability the PR's design surface exposes now has a UI path:

| Broker capability | Reachable from |
|---|---|
| `CreateTournament` | landing page form → navigates to the new code |
| `JoinTournament` | landing page join-by-code |
| `GetTournament` | detail page mount + re-seed |
| `StartTournamentRound` | detail page organizer controls |
| `ReportMatchResult` | detail page "Your Match" (player, own pairing) |
| `DropFromTournament` | detail page player controls |
| `EndTournament` | detail page organizer controls |
| `TournamentListUpdate` | landing list |
| `TournamentUpdate` | detail view (the sole render source) |
| `TournamentRemoved` | credential cleanup (store) + `errors.notFound` on the viewed code |

**Gaps found, and their disposition** (flagged, per the brief, rather than silently absorbed):

| Gap | Absorb here? | Why |
|---|---|---|
| **Stale detail view after a reconnect with no subsequent mutation** | **YES — absorbed** (§4.7, V12). Cheap, in-scope, provably loop-free (P8) | Leaving it would have required a store change (out of scope) or shipping a known-stale surface |
| **No `/icons/sections/tournament.png`** | **YES — absorbed** (§0.3, §5.3) as an inline SVG | A dangling `<img src>` is invisible to every test and broken only in production |
| **No "copy tournament code / invite link" affordance** | **No** — future work | Needs a new catalog key in 7 locales (see §7.2's reasoning about terminal-phase copy) and a clipboard permission path `HostControlTile` already solves elsewhere. The code is displayed and selectable today |
| **No entry point to a tournament from the multiplayer lobby page** | **No** — future work | `MultiplayerPage.tsx` is not in this phase's scope; the nav destination makes tournaments reachable, which is what the charter's acceptance criterion asks for |
| **Broker default `ScoringPolicy` is not exposed on the wire** (§7.3) | **No** — future work | A Rust protocol change, outside this PR |
| **6 nav items + What's New = 7 flex cells in `TabBar` below 820px** | **No** — cosmetic follow-up | Not measurable under happy-dom; a design call, not a correctness one |
| **`expectNoRawKeyPaths` walks text nodes only — attribute leaks (`title`/`aria-label`/`placeholder`) are uncovered** (m4) | **No** — test-coverage follow-up | No live defect: every attribute key resolves today and the dynamic half (`cell.titleKey`) is `never`-enforced. Closing it means editing `tournamentTestUtils.ts`, phase 4's committed shared helper, which is outside this phase's scope. See the m4 note under §6.4 |
| **`PairingsList.tsx`'s `onReport` prop doc asserts the disproved organizer-authority premise** (round 2's M1(b)) — **`client/src/components/tournament/PairingsList.tsx:14-18`**, the JSDoc on the `onReport?` member of `PairingsListProps`. Its **first sentence** reads *"Supplied by phase 5 only for a viewer holding the organizer credential."* That is **exactly the false premise §0.2 disproves**: `onReport` is supplied for a viewer holding the **player** credential, who is additionally **not dropped** (C2) and **seated in that pairing** (C3). Its second sentence (*"Presence alone does NOT make a row reportable — see the arm gate below"*) is correct, is unaffected, and is what §0.2 and §5.5 item 5 quote approvingly | **No** — **cannot be fixed in this phase; must be flagged, not shipped silently** | `PairingsList.tsx` is **frozen**: phase 4 shipped it, §7.5 item 4 forbids touching the five phase-4 components, and phase 5 mounts it unmodified. **This is the terminal phase — there is no phase 6 to catch this later**, which is precisely why it is written down here rather than left for a successor. The comment is misleading but **inert**: it documents a *caller's* obligation, and this phase's actual caller (§5.5 item 5) satisfies the real, correct contract, so no behavior is wrong and no test is affected. **Disposition: name it explicitly in the final PR body's follow-up section and correct the first sentence in a follow-up PR** (a one-line doc edit, e.g. *"Supplied by phase 5 only for a viewer who is an active entrant seated in this pairing — see `tournamentPageState.isActiveEntrant`/`myPairing`"*). An executor who notices the mismatch mid-implementation must **report it, not fix it** — editing a frozen file would put the diff outside this phase's scope-path set |
| **Two authored-but-unconsumed catalog keys: `join.joined`, `report.cancel`** (m6) | **No** — follow-up | Deleting a key touches all 7 catalogs and re-engages S4's three-part contract, in the phase with no successor to review it. `report.cancel` is superseded by `common:actions.cancel`; `join.joined` has no surface, because a successful join navigates away immediately. Neither is a defect — an unreached key is parity-green and renders nothing |

None of these blocks the PR's acceptance criteria. **Every row marked "No" belongs in the final PR body's follow-up section** — stated as a rule rather than as a count, so a row added later is carried automatically instead of silently falling outside a stale total.

### 7.5 Explicit decisions this phase makes (so none is re-litigated silently)

1. `AppShell.tsx` is **not** touched (§5.6).
2. `/add-frontend-component`'s self-maintenance directory table is **not** edited (§1), matching phase 4.
3. `test-setup.ts` is **not** touched — RTL cleanup stays file-local (§6.1), matching phase 4.
4. The five phase-4 components, `tournamentClient.ts`, `multiplayerStore.ts`, the 7 catalogs and `localeParity.test.ts` are **not** touched.
5. The `replay`-namespace drift (S5) is **not** repaired.
6. `components/draft/StandingsTable.tsx` — the display-layer counter-example phase 4 found and reported — is **not** touched.
7. No new catalog key is authored (§7.1, §7.2).
8. `isReportable`'s doc comment **is** corrected in place (§5.1 item 7) — a deliberate, enumerated comment-only exception to this file's append-only rule, taken because the stale count is in a file this phase already edits.
9. `PairingsList.tsx`'s stale `onReport` doc comment is **not** corrected (frozen file, terminal phase) but **is** explicitly flagged for the PR body (§7.4). "Found but out of scope" is recorded, never silently dropped.

### 7.6 Executor environment facts

- `client/node_modules` **is present**; no `pnpm install` needed (S9's "absent" measurement predates phases 1–4).
- Tilt does not watch this worktree: `tilt get uiresource clippy` fails, `./scripts/tilt-wait.sh` returns **exit 3 = "cannot answer"**, which must **never** be reported as a build failure.
- **No cargo command may be run** — no Rust changes, and the target lock must not be taken.
- `src/components/chrome/__tests__` carries **15 pre-existing failures** on this machine (Node v25 `--localstorage-file`). Do not attempt to fix them; do not treat them as a regression.
- RC1's failure surfaces under `type-check`, **not** vitest.
- `tsconfig.app.json`'s `noUnusedLocals` + `verbatimModuleSyntax` bite immediately on a stray import or a value-vs-type import slip.
- Avoid writing the literal string `"@ts-expect-error"` anywhere in a comment near a mutation check — phase 4 measured that even a prefixed variant suppresses the next line's real compiler error and produces a spurious pass.

---

## §8 — Summary for the reviewer

**What changed in revision 3** (round 2: 1 material + 4 minor). Revision 3 is **documentation-only** — it adds no export, no test, no gate, no catalog key, and no scope-path. **Sizing is untouched: 4 units, 6 source scope-paths.**

- **M1 — the two stale doc comments that still assert the disproved organizer-authority reading, now both handled and neither silent.**
  - **(a) In scope, fixed.** `tournamentPageState.ts`'s own `isReportable` doc closed with *"Authorization is a separate, orthogonal guard on the caller's side ({@link viewerRoles}); both are required"* — a **two**-authority count written in phase 4, before §0.2 established that `authorize_player` enforces **three** conjuncts. After this phase the gate is three authorities: `viewerRoles` (C1), **`isActiveEntrant` (C2 — the export revision 2 added)**, and `myPairing` (C3). **§5.1 item 7** now prescribes the exact one-paragraph replacement, verbatim in and verbatim out, with the rest of that doc comment left byte-identical. This was M1's own incompleteness restated inside the very file this phase edits, so leaving it would have shipped a file documenting the premise its own diff disproves. §5.1's header now enumerates its **two** permitted comment-only exceptions (items 5 and 7) so a third is not improvised.
  - **(b) Out of scope, flagged.** The **frozen** `PairingsList.tsx:14-18` `onReport` doc opens *"Supplied by phase 5 only for a viewer holding the organizer credential"* — the exact false premise §0.2 disproves. Revision 2 quoted that comment's *second* sentence approvingly without noticing the first was wrong. It **cannot** be fixed here (phase-4 component, §7.5 item 4, and this is the terminal phase — no successor exists to catch it), so it is now a **named row in §7.4's gap table** with its exact location, the reason it can't be fixed here, a suggested replacement sentence, and the instruction that it reach the **final PR body's follow-up section**; §0.2's quotation site carries a caveat pointing at that row, and an executor who spots the mismatch is told to **report, not fix**. The comment is misleading but inert — it documents a caller obligation this phase's caller satisfies correctly — so no behavior or test changes.
- **m2** — revision 2's own V13 rescoping ("rendered **text node**", not "the DOM") had not propagated to §7.1's deferral table, which still restated the discharge in the forbidden broader form. That row now states the text-node scoping, names the attribute surfaces as explicitly outside the claim, cross-references **§6.4's V13 coverage-boundary note**, and instructs that the broader phrasing not be reintroduced. Checked document-wide: the remaining "the DOM" occurrences are unrelated (they describe *rendered output* in V10/V17, not the key-path-leak instrument's reach) and are correct as written.
- **m3** — four phase-fit citations were transcribed **line offsets**, not entry numbers, and were unresolvable in a log with far fewer entries. Each was re-derived by reading the log and locating the entry that actually contains the cited content, then rewritten in the durable "Entry N + subject" form so a future line-number shift cannot re-break them: *entry 235* → **Entry 39** (phase 4's fix-round review-impl), *entry 220* → **Entry 36** (phase 4's implementation checkpoint, 3 sites), *entry 175* → **Entry 30** (phase 4's plan production), *entry 170* → **Entry 29** (phase 3's review-impl — the standing Node v25 `--localstorage-file` note; the companion "29" in that citation was already correct, so the pair collapses to one entry).
- **m4** — four citation/prose inaccuracies, each re-verified against current source rather than accepted from the review: `LobbyView.tsx`'s unmount-safety idiom is at **`:134-137`** (the plan said `:138`, which is the *next* branch, `if (detach === null)`); the subscription/cleanup seam is **S3**, not S2 (S2 is the charter's unrelated `PairingView` naming collision — confirmed by reading both seam entries); "matching **every other** shell route" was an overclaim — **8 of the 10** routes inside the layout route are `DevStrict`-wrapped and `/draft-pod`/`/draft-spectator` are deliberately not, so the text now names the count and warns the executor not to "make them consistent"; and §4.3's decorative *"eight lines away"* distance claim — already contradicted by §5.1, which appends `isActiveEntrant` at the end of the file after two other new exports — is removed in favour of "already performs in this same module", which is the load-bearing part of that argument anyway.
- **m5** — V22b's hostile fixture is now fully specified rather than relying on its third assertion to catch a vacuous build. Two clauses added, both verified against real source: **`pairing.round` must equal `summary.current_round`** (confirmed — `myPairing` conjoins `pairing.round === view.summary.current_round`, so a mismatched round makes C3 fail closed and Alice's "zero buttons" assertion pass for entirely the wrong reason), and **Alice's `TournamentStanding.dropped` must *also* be `true`**, separately from `PlayerSummary.dropped` (confirmed — `TournamentStandingsTable` renders its `labels.dropped` chip off the standing row's `dropped`, never off `PlayerSummary`, and that chip is what the third assertion reads). The three vacuity-blocking clauses are now marked ★ in the fixture text.

**What changed in revision 2** (round 1: 1 material + 6 minor):

- **M1 — the authorization thesis, applied completely.** Revision 1 quoted `authorize_player`'s dropped conjunct in §0.2 and then omitted it from the binding table and from both §5.5 player gates, which checked only `roles.has("player")`. Both resulting dead affordances were re-confirmed against real Rust source here: the Drop button survives a successful drop (credentials clear only on `TournamentRemoved`, while `handle_drop_from_tournament` permanently refuses a second drop by design), and the Report button survives a drop inside a ≥3-seat pod (`drop_player` auto-forfeits only at exactly one surviving active seat, and `pairing.players` keeps its original seat list). Fixed with **`isActiveEntrant(view, playerKey)`** in `tournamentPageState.ts` — placed there, rather than inlined in the page, because it is the same identity join as `myPairing`, because that module is already the declared single display-authority, and because the pure truth table (V22) sharpens the revert-checks; the argument is in §4.3, including why folding `dropped` into `ViewerRelation` is *rejected* (it would ride an authority conjunct on a display precedence and re-break the playing-organizer case). §0.2 now enumerates the broker's three conjuncts C1/C2/C3 and maps each to its UI gate. New: **V22** (pure), **V22b** (hostile 4-seat pod fixture: dropped Alice → zero of each button; active Bob, *same fixture* → exactly one of each), **RC9/RC10** (each gate weakened separately). **Sizing unchanged: 4 units, 6 source scope-paths, zero new catalog keys.**
- **m2** — §3.5 and §6 now state a lettered-sibling counting *convention* instead of a total: 8 probes across 9 rows (P1b), 22 claims across 24 rows (V4b, V22b).
- **m3** — `failureLabel` is described as "a further exhaustive walk, over the failure-reason union rather than a wire union," with **no ordinal anywhere**. Revision 1's "fifth" was wrong on both available counts (the header's count is wire-union-scoped; the file actually holds seven `never` terminals, since `outcomeLabelKey` and `decisiveGameWins` each nest an `unreachablePod` and `formatTiebreakValue` walks a non-wire union).
- **m4** — V13's claim is scoped to "no raw key path leaks into a rendered **text node**", with the attribute-surface gap named honestly (six real `title`/`placeholder`/`aria-label` sites in phase-4 components, no live defect) and listed as follow-up rather than absorbed.
- **m5** — the detail page renders `PairingsList` twice, so every pairing string appears ≥2×; §6.1 now prescribes `within(...)` scoping (V5, V14) or `getAllByText` with an explicit count (V4b, V13, V22b), and forbids a bare `getByText` on pairing-derived text.
- **m6** — the key-consumption claim is corrected and measured: **49** keys are named by this phase's own design, **60** by the phase-4 components it mounts, and **2 are reached by nothing** (`join.joined`, `report.cancel` — a real new finding, dispositioned as follow-up rather than deleted).
- **m7** — the CR gate now warns that `grep -c` exits `1` on the correct zero result, with a `|| true` capture form for any `set -e` wrapper.

**Preserved from revision 1 through revisions 2 and 3, unchanged** (revision 3 touched none of the following — it changed prose and citations only):

- **1 blocking premise correction, probe-proven:** reporting a match result is **player**-authority and **seat**-scoped, not organizer-authority (P4: 0 frames sent, `role:"player"` refusal, with a positive reach-guard proving the same credential does authorize a round start). The charter's and the brief's `has("organizer")` phrasing would have shipped dead UI. Resolved without touching any frozen file, by supplying `onReport` only to a `PairingsList` rendering the viewer's own pairing.
- **1 asset gap found:** no `/icons/sections/tournament.png`; resolved with an inline SVG following `SparkleIcon`, since happy-dom would never have caught a dangling `<img src>`.
- **8 probes across 9 rows, run and reverted**, tree pristine at `b34de3f09…` — baseline 311 tests / type-check exit 0; S6's blast radius bounded to exactly one assertion; the 15-failure chrome baseline distinguished from any real regression; the ambient-broadcast render path, the offline branch, and the loop-freedom of the re-seed all measured rather than reasoned.
- **10 deferrals audited** against the real 39-entry log; all discharged, one declined with reasoning, one (abort-on-reconnect) found already closed in phase 2 contrary to the brief's expectation.
- **Zero new catalog keys** → the 7 catalogs and `localeParity.test.ts` are out of the diff and the i18n gates stay at exactly 199. M1's fix needed none: `PlayerSummary.dropped` was already on the wire and `labels.dropped` was already rendered by phase 4's standings table.
- **Sizing: 4 units, 6 source scope-paths** — **unchanged by revision 2**, since `isActiveEntrant` is a third export of the existing U2 unit in an already-counted file and its consumers are in an already-counted file. T1 fires, **T2 does not** (6 < 13, and 10 < 13 under every hostile convention). The conjunction does not fire; the terminal phase does **not** need to split.
- **CR annotations: N/A**, checked on three grounds, with a `grep -c "CR [0-9]{3}"` == 0 gate for the executor — read the **printed count**, not the exit status (§4.9, m7). Nom compliance: N/A. Engine variants: N/A.
- **Deferral list: empty.** Four items are named as explicit out-of-scope follow-up work for the PR body (§7.4), none of which blocks the PR's acceptance criteria.
