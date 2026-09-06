# Backlog

Personal backlog for `rykerwilliams/phase`. Lives only on this fork's `main` —
it is a divergent file and must never appear in a PR to `phase-rs/phase`.
Every feature/fix branch is cut fresh from `origin/main` (upstream), never
from this fork's `main`, so this file is automatically excluded from PR
diffs — no extra tooling required.

## Format

Each item is written so it can be pasted with little or no editing as the
opening instruction to the next pipeline step (usually `/engine-implementer`
for a bug fix, or a plain investigation prompt for research/infra work).

- **Title**
- **Type** — `bug-fix` | `feature` | `infra` | `research`
- **Status** — `open` | `in-progress` | `done`
- **Source** — where this came from
- **Prompt** — ready-to-paste instruction for the next agent/skill invocation

Move an item to the bottom "Done" section (don't delete it) once it ships,
so there's a record of what's already been resolved.

---

## Open

### [bug-fix] Transform / flip / morph silently drop a carried resolution shield (CR 611.2a)

- **Status:** open
- **Source:** 2026-09-05, `/review-impl` MED finding on the issue #8485 fix.
- **Context:** #8485 made resolution-created replacements (prevention shields,
  regeneration shields, damage redirects) survive the CR 613.1 layer reset. Their
  documented removal paths are an expiry prune (`turns.rs`: cleanup,
  end-of-combat teardown, untap step) and a zone change (CR 400.7). Three
  in-place FACE rewrites also drop them, because each wholesale-assigns the live
  replacement store from a face snapshot:
  `printed_cards::apply_back_face_to_object` (transform / specialize),
  `flip.rs` (CR 710.1b), and `morph.rs` (turn face down, CR 708.2a).
- **Why it is wrong:** CR 611.2a — a continuous effect from the resolution of a
  spell or ability "lasts as long as stated by the spell or ability creating it".
  None of transform, flip, or turning face down is a zone change (CR 400.7) and
  none is a stated duration, so a regenerated or shielded creature that transforms
  should keep its shield. Today it silently loses it.
- **Deliberately not fixed in #8485:** `flip.rs` and `morph.rs` were outside that
  change's frozen scope, and the `printed_cards.rs` seam was filtered to fix a
  worse HIGH (a transform round-trip was seeding `base_replacement_definitions`
  with a `Resolution` def, which made the CR 613.1 carry-over duplicate the shield
  once per layer pass without bound). Shield LOSS was the correct trade against
  unbounded shield DUPLICATION, but it is still wrong.
- **Prompt:** Make a resolution-created replacement survive transform, flip, and
  turning face down. The three seams that wholesale-assign the live replacement
  store from a face snapshot are `printed_cards::apply_back_face_to_object`,
  `flip.rs`, and `morph.rs`. The shape that works is the one
  `layers::seed_live_characteristics_from_base` already uses: rebuild from the
  face/base baseline while carrying forward the `Resolution`-origin members of the
  live store, via `game_object::reseed_replacements_carrying_resolution_effects`.
  CRITICAL: whatever you do, a `Resolution`-origin def must NEVER end up in
  `base_replacement_definitions` — that breaks the carry-over's idempotency
  precondition and duplicates the shield every pass. `snapshot_object_face`
  filters them out for exactly that reason; keep that filter and carry the live
  members across separately. Regression-test a transform round-trip, a flip, and a
  morph over a live shield, asserting the shield survives AND that the count does
  not grow across two `evaluate_layers` passes.

### [infra] `add_target_replacement`'s two registry pushes bypass the floating-install authority

- **Status:** open
- **Source:** 2026-09-05, `/review-impl` MED finding on the issue #8485 fix.
- **Context:** #8485 introduced
  `game::effects::install_floating_damage_replacement` as the single authority for
  installing a source-scoped damage shield into
  `state.pending_damage_replacements`, latching `source_controller` (CR 113.8 /
  CR 109.5: the controller of an activated ability is the player who activated it)
  and, where applicable, the CR 113.7a `source_object` host anchor.
  `effects/add_target_replacement.rs` still pushes raw at two sites — its
  `TargetFilter::None` global arm and its `TargetRef::Player` arm — and neither
  latches `source_controller`.
- **Consequence:** for definitions installed through those two arms, a
  controller-relative gate in the pending scan resolves against
  `state.active_player` instead of the installer, so it can answer the wrong player
  when the installer is not the active player. Pre-existing behavior, not a
  regression from #8485.
- **Deliberately not fixed in #8485:** latching the controller there is a behavior
  change to a population that change did not otherwise touch, and it was too late
  in that work to take it without measurement.
- **Prompt:** Route `effects/add_target_replacement.rs`'s two
  `state.pending_damage_replacements.push(...)` sites (the `TargetFilter::None`
  global arm and the `TargetRef::Player` arm) through
  `game::effects::install_floating_damage_replacement`. Pass `anchor_zones: &[]`
  unless you can argue a host anchor is correct for that arm, since anchoring a
  population that is already registry-hosted is over-matching. Expect the
  `source_controller` latch to CHANGE behavior for controller-relative gates on
  those definitions — from `state.active_player` to the installer — which CR 113.8
  and CR 109.5 say is correct; find or write a fixture where the installer is not
  the active player and pin the new reading. Then delete the "scope of that claim"
  caveat from `install_floating_damage_replacement`'s doc comment.

### [infra] Two independent copies of the CR 510.1c/702.19b combat-damage division in the integration tests

- **Status:** open
- **Source:** 2026-09-05, `/review-impl` LOW finding on the issue #8485 fix.
  Deliberately not fixed there: sharing the logic properly means extracting a
  helper in `crates/engine/tests/integration/rules.rs`, which was outside that
  change's frozen scope.
- **Context:** the combat-damage division — assign each blocker its
  `lethal_minimum` in order, then give the remainder to the defending player as
  trample damage (CR 702.19b) or dump it on the last blocker so the assignment
  totals the attacker's power (CR 510.1c) — now exists **twice**:
  `rules.rs::run_combat_with_blocker_divisions` and the `WaitingFor::
  AssignCombatDamage` arm of
  `issue_8485_maze_of_ith_defender.rs::run_mazed_combat_with_maze_removal`. The
  second copy was added because the first lives inside a whole-combat driver that
  cannot host the Maze-activation timing the #8485 tests need.
- **Why it matters:** this is RULES-BEARING logic, not boilerplate. CR 510.1c's
  lethal-damage ordering and CR 702.19b's trample remainder are exactly the kind
  of thing that gets corrected once and then silently disagrees between copies —
  and a test helper that divides damage wrongly produces tests that pass while
  asserting the wrong thing. The #8485 work already demonstrated the failure mode
  it protects against: two tests in that file were passing vacuously for months
  because no division was performed at all.
- **Prompt:** Extract the CR 510.1c/702.19b combat-damage division out of
  `crates/engine/tests/integration/rules.rs::run_combat_with_blocker_divisions`
  into a standalone `pub` helper in `rules.rs` that takes the
  `WaitingFor::AssignCombatDamage` payload and returns the `(assignments,
  trample_damage)` pair (or submits the `GameAction` directly). Then repoint both
  callers at it: `run_combat_with_blocker_divisions` itself and the
  `AssignCombatDamage` arm in
  `crates/engine/tests/integration/issue_8485_maze_of_ith_defender.rs`. Keep the
  CR annotations on the extracted helper. Verify with
  `cargo test -p phase-engine --test integration` — the Maze file's 14 tests and
  every banding/menace/trample fixture that uses the shared driver must stay green.

### [bug-fix] Unbounded-expiry resolution riders stay layer-fragile — the one subclass issue #8485 deliberately did not fix

- **Status:** open
- **Source:** 2026-09-05, `/review-impl` LOW finding on the issue #8485 fix
  (Maze of Ith / CR 611.2c resolution-shield durability). Recorded here rather
  than fixed in that PR, and recorded here rather than left only in a doc
  comment, because it is a real hole in that change's stated class.
- **Context:** #8485's stated class is "every continuous replacement/prevention
  effect created by the RESOLUTION of a spell or ability and hosted on a
  battlefield permanent survives the CR 613.1 layer reset". One subclass is
  excluded: `GameObject::install_resolution_replacement`
  (`crates/engine/src/game/game_object.rs`) refuses to stamp
  `ReplacementOrigin::Resolution` on a definition whose `expiry` is `None`, and
  installs it live-only instead — i.e. exactly the pre-#8485 behavior, still
  wiped by the next layer pass.
- **Why the fail-closed arm is CORRECT and must not simply be removed:** all
  three prunes that can remove a carried definition — `turns::execute_cleanup`,
  `turns::complete_end_combat_teardown`, and the untap-step prune — key on
  `expiry` ALONE. A `Resolution`-stamped definition is carried across every
  CR 613.1 reset, so its only removal paths are an expiry prune and a zone
  change. Carrying one with `expiry: None` would therefore make it **immortal**,
  which is strictly worse than layer-fragile. A bare `debug_assert!` is also the
  wrong instrument: it would fire in debug builds on a legitimate path.
- **The reachable population:** `effects::add_target_replacement`'s
  unstated-duration NON-shield rider.
  `ReplacementDefinition::with_resolution_shield_expiry` is gated on
  `shield_kind.is_shield()` precisely so durable non-shield riders keep
  `expiry: None` (the CR 611.2b `ControllerControlsSource` lock and the
  CR 702.84a `UntilHostLeavesPlay` rider are the audited members, and those are
  base-resident by design and correctly excluded). `prevent_damage`,
  `create_damage_replacement` and `regenerate` all stamp an expiry
  unconditionally, so none of them can reach the arm.
- **What a real fix needs (CR 611.2a):** a lifetime the engine can actually
  END for the unstated-duration rider class — either a representable `expiry`,
  or an applicability gate on the same footing as
  `add_target_replacement::stamp_for_as_long_as_controlled_gate`'s
  `ReplacementCondition::ControllerControlsSource`, or a demotion at parse time
  the way `parser::oracle::demote_unenforceable_replacement_lifetimes` already
  demotes refused prevention windows to `Effect::Unimplemented`. Whichever is
  chosen, the invariant to preserve is: a definition is `Resolution`-stamped
  **iff** some prune can end it.
- **Prompt:** Investigate the unstated-duration (`expiry: None`) non-shield
  rider class produced by `Effect::AddTargetReplacement`. Determine, from the
  parsed corpus, which printings actually reach
  `GameObject::install_resolution_replacement`'s fail-closed arm
  (`def.expiry.is_none()`) and what window their Oracle text states. Then decide
  per CR 611.2a whether each wants a representable `RestrictionExpiry`, a
  runtime applicability gate, or a parse-time demotion to
  `Effect::Unimplemented`. Do NOT simply remove the fail-closed arm: carrying an
  unbounded definition across the CR 613.1 reset makes it immortal, because all
  three `turns.rs` prunes read `expiry` alone. Preserve the invariant that a
  definition is stamped `Resolution` if and only if some prune can end it.

### [feature] Connive N (N>1) + multi-draw-replacement interaction — follow-up from the Dredge/Bazaar fix

- **Status:** open
- **Source:** 2026-07-08, explicitly descoped from PR
  [phase-rs/phase#5360](https://github.com/phase-rs/phase/pull/5360) (the
  CR 121.6b multi-card-draw-replacement fix) during a 6-round adversarial
  plan review.
- **Context:** #5360 fixes `Effect::Draw{count: N>1}` (the general draw
  path used by Ancestral Vision, Concentrate-class spells, etc.) so each
  unit of a multi-card draw offers Dredge/Notion Thief/Hullbreacher-style
  replacement independently, instead of one unit's replacement zeroing the
  whole count. Connive N (N>1, CR 701.50d) draws through its own,
  independent, non-delegating implementation in `connive.rs` and has the
  IDENTICAL bug — but was deliberately NOT touched by #5360.
- **Why deferred, not just missed:** `connive.rs:1389-1424` documents a
  **previously shipped and fixed bug**: routing Connive's "you draw a
  card, THEN that creature connives" (CR 701.50a) ordering through a
  shared, generic mid-draw continuation mechanism caused the connive's
  `ConniveDiscard` state to be silently clobbered by an unrelated epilogue
  reset. The dedicated `pending_connive_reentry` slot exists specifically
  to avoid that collision. #5360's `pending_multi_draw` continuation is
  drained at the exact same `handle_replacement_choice` call site as
  `pending_connive_reentry` — reusing it for Connive N risked reintroducing
  that exact failure mode, and the review process didn't have enough
  evidence to certify the two compose safely.
- **Before designing anything:** trace `pending_connive_reentry`'s
  original fix (git history/PR that introduced it, likely referencing
  issue-like context similar to #4886) to understand exactly what broke
  and why the dedicated slot was the chosen fix, so any new design doesn't
  reintroduce a variant of the same problem.
- **Prompt:**
  > Fix Connive N (N>1, CR 701.50d) so a multi-count connive draw offers
  > Dredge/Notion-Thief/Hullbreacher-style replacement independently per
  > unit, matching the fix already shipped for the general draw path in
  > phase-rs/phase#5360. Start by tracing `pending_connive_reentry`'s
  > original introduction (git log on `crates/engine/src/game/effects/connive.rs`
  > and `crates/engine/src/game/engine_replacement.rs`) to understand the
  > prior collision this dedicated slot was built to avoid — the fix must
  > not reuse `resume_multi_draw`/`pending_multi_draw` naively at the same
  > resume site without first proving it doesn't reintroduce that
  > collision (e.g. a per-unit-paused connive draw whose leading unit is
  > ALSO the CR 701.50a "leading draw" needing deferred connive-linking).
  > Use `/engine-planner` + `/review-engine-plan` given the delicacy shown
  > by #5360's own 6-round review cycle on the adjacent, simpler case.

### [research] Automated era-by-era card correctness sweep — start with Old School (93/94), move forward chronologically

- **Status:** open
- **Source:** 2026-07-08. Motivated directly by user frustration: manually
  playing games and stumbling onto broken cards (Scourglass, the
  Serum-Powder-deployment-lag false alarm, the Dredge/Bazaar report) is
  tedious and not how bugs should get found. The goal of this item is to
  **replace manual play-testing-as-bug-discovery with an automated sweep**,
  not to produce another one-off manual audit.
- **Scoping decision (explicit, from this session):** start with Old
  School (93/94)-legal cards, then move forward through eras (Old School →
  Premodern → Legacy/Vintage-legal older cards → ...), rather than a flat
  whole-format sweep. Older/simpler cards are cheaper to verify and more
  likely to reveal foundational bugs (like the Scourglass exception-clause
  gap or the cast-controller-vs-owner bug found earlier this session) that
  also affect newer cards sharing the same building blocks — fixing those
  early has outsized leverage on later eras.
- **Key finding this session, must inform the design:** Old School/93-94
  is **not** a tracked format in the engine's own coverage system.
  `LegalityFormat` (`crates/engine/src/database/legality.rs`) only goes
  back to Premodern — no Old School entry exists, so `cargo coverage`'s
  `coverage_by_format` cannot filter to it directly. The card-legality
  list for Old School has to come from an external authoritative source:
  reuse the Eternal Central 93/94 set list already referenced in the
  "Custom/'design your own' format engine" backlog item above
  (https://github.com/northern-information/lordsofthepit.com/blob/main/src/pages/formats.md),
  or the underlying LEA/LEB/2ED/ARN/ATQ/3ED/LEG/DRK/FEM set-code list —
  verify against that source, don't hardcode a remembered set list.
  Premodern, Legacy, and Vintage ARE tracked (`LegalityFormat::Premodern`
  /`::Legacy`/`::Vintage`), so later eras of this sweep can use
  `cargo coverage`'s existing `coverage_by_format` output directly.
- **Two-layer methodology (both required — this session proved layer 1
  alone is not enough):**
  1. **Structural gaps (cheap, fully automated):** `cargo coverage`'s
     `cards[]` list where `supported == false`, filtered to the era's
     legal-card set, gives a mechanical "definitely not implemented" list
     with `gap_details` pinpointing the exact missing clause/effect.
  2. **Supported-but-silently-wrong spot checks (the layer that actually
     catches bugs like Scourglass):** `supported: true` only means the
     parser produced a non-`Unimplemented` effect for every clause — it
     does NOT mean the effect is runtime-correct. Scourglass showed
     `supported: true` the entire time its exception clause was being
     silently dropped. This layer needs real runtime verification (the
     `/card-test` GameScenario/GameRunner recipe), prioritized toward
     cards with irregular Oracle grammar most likely to hide silent bugs:
     exception/"except for" clauses, replacement effects, multi-part
     "then" sequences, cards whose effect interacts with another
     mid-resolution player choice (Dredge-style replacements included).
- **Automate the discovery, not just the fix:** the actual ask here is to
  stop relying on the user hitting bugs live. Options to evaluate (don't
  commit to one without checking feasibility first): (a) a `Workflow`-
  based sweep that fans out one verification agent per era-legal card,
  each doing the full session-established pipeline (verify Oracle text →
  check existing coverage/tests → write or run a targeted runtime test →
  report pass/fail), reporting back a structured pass/fail list instead of
  requiring a human to play a game and notice something's off; (b)
  AI-vs-AI self-play sessions (the engine already has an AI opponent) that
  log anomalies (unexpected effect outcomes, panics, stuck WaitingFor
  states) automatically across many simulated games — investigate whether
  hooks for this already exist before building new ones. Whichever
  approach, the deliverable is a system the user can point at an era and
  get a bug list back, not a document someone has to maintain by hand.
- **Prompt:**
  > Design (don't yet implement) an automated card-correctness sweep,
  > starting with Old School (93/94)-legal cards. Step 1: get the
  > authoritative Old School card/set list (fetch the Eternal Central
  > source linked above, or MTGJSON set codes for LEA/LEB/2ED/ARN/ATQ/3ED/
  > LEG/DRK/FEM — verify, don't assume). Step 2: run `cargo coverage` and
  > cross-reference its `cards[]` `supported: false` entries against that
  > list for the mechanical gap list. Step 3: propose a concrete mechanism
  > (Workflow fan-out, AI-self-play anomaly logging, or another approach)
  > for automating layer-2 (supported-but-wrong) verification at scale
  > without requiring the user to manually play games, and get sign-off
  > on the approach before building it. Once Old School is swept and any
  > real bugs are fixed, repeat for Premodern (tracked format, use
  > `coverage_by_format` directly), then Legacy/Vintage-legal older cards.

### [infra] Follow up on PR #5236 and PR #5304 (mulligan bottoming fix)

- **Status:** open
- **Source:** 2026-07-07, this session's Serum Powder / CR 103.5 mulligan
  bottoming fix.
- **Context:** As of 2026-07-07, PR [phase-rs/phase#5236](https://github.com/phase-rs/phase/pull/5236)
  (the core mulligan-declare-point-bottoming fix) is CI-green and
  **approved** by `matthewevans`, but not yet confirmed merged. PR
  [phase-rs/phase#5304](https://github.com/phase-rs/phase/pull/5304) (the
  isolated `.claude/skills/add-interactive-effect/SKILL.md` doc fix, split
  out of #5236 because `.claude/skills/**` is a hard-stop path for the
  automated PR review loop per `.agents/pr-review-policy.toml`) is
  CI-green but still shows `CHANGES_REQUESTED` from the same reviewer —
  expected and permanent by design, since skill-file PRs are excluded
  from that automated loop entirely. #5304 needs a human to merge it
  directly; it will never clear the bot review on its own.
- **Follow up around 2026-07-14 (about a week out)** if neither has moved:
  check whether #5236 actually got merged despite approval, and whether
  #5304 has been merged manually or needs a nudge.
- **Prompt:**
  > Check the current status of phase-rs/phase PR #5236 and PR #5304
  > (`gh pr view 5236 --repo phase-rs/phase`, `gh pr view 5304 --repo
  > phase-rs/phase`). If either is still open with no new activity, post a
  > polite follow-up comment or ping asking for merge. If #5236 has
  > drifted out of sync with `origin/main` (check `mergeStateStatus`),
  > sync it from a fresh worktree before pinging. If both have already
  > merged, mark this backlog item done.

### [feature] Custom/"design your own" format engine, instance-configurable — first presets: Eternal Central retro formats (93-94, 95, Middle School, Classic Magic)

- **Status:** open
- **Source:** 2026-07-07 planning discussion. Authoritative EC ruleset
  source (user-provided): https://github.com/northern-information/lordsofthepit.com/blob/main/src/pages/formats.md
  — fetched and confirmed this session, quoted below. Re-fetch before
  implementing in case the source has been updated since.
- **Reframed scope (2026-07-07, mid-discussion):** this item started as
  "add 4 hardcoded EC formats" and was deliberately widened to a more
  general capability once the user raised it — **don't build the narrow
  version.** The real ask has three layers, broadest first:
  1. A **general custom/"design your own format" engine**: players
     and/or instance operators can define a format (legal card pool,
     restricted/banned lists, deck-size rules, sideboard policy, starting
     life, mulligan variant, etc.) as *data*, without a phase.rs code
     change or rebuild.
  2. That data-driven format definition also needs an **independently
     toggleable "legacy/alternate rules" flag set** — see below, this is
     NOT the same axis as card-pool/banned-list restriction.
  3. The four EC formats (plus, as a stretch goal, LotP's "Eternal Chaos"
     variant) become the **first bundled presets** built on top of (1)
     and (2), proving the general system works, rather than a parallel
     hardcoded implementation that the custom-format engine would later
     have to duplicate or reconcile with.
  - This ordering matters: per CLAUDE.md's "build for the class, not the
    card," if a general custom-format system is the real target, building
    it first and expressing the four EC formats *through* it (as data) is
    the aligned design — not the other way around. Don't let "just ship 4
    formats fast" pull the implementation back to the narrow, hardcoded
    version once work starts.
- **Legacy/alternate rules — a separate, independently-toggleable axis
  from deck legality (confirmed this session via the EC source data):**
  Mana burn applies to **all four** EC formats (93-94, 95, Middle School,
  *and* Classic Magic). "Damage Uses the Stack" and pre-M10 Wish
  templating apply **only** to Middle School and Classic Magic — NOT
  93-94 or 95. Because these don't travel together, they must be modeled
  as independent flags (e.g. `LegacyRules { mana_burn: bool,
  damage_uses_stack: bool, pre_m10_wish_templating: bool, ... }`) that the
  core engine's rules logic checks generically wherever each applies —
  never as a per-format hardcoded check (`if format == MiddleSchool`).
  This flag set is itself part of what "design your own format" needs to
  expose, since real old-format communities disagree on which legacy
  rules to combine.
  - **These two legacy rules are NOT the same size of engine change —
    investigate both independently, don't assume parity:**
    - **Mana burn** was removed from the modern Comprehensive Rules
      entirely by the 2010 "M10" update (not present in current CR at
      all) — re-adding it as an optional flag is likely a well-contained
      addition IF the engine already tracks unspent mana when a pool
      empties at a step/phase boundary (probably does, since pool-emptying
      is itself required for any ruleset) — investigate that hook point
      specifically as the likely small, tractable piece.
    - **"Damage Uses the Stack"** is a deeper, pre-6th-edition combat
      resolution difference (damage was itself a stacked, response-able
      event rather than the current immediate-effect model) — likely
      touches core combat-damage-resolution ordering, not just a
      step-boundary check. Investigate whether the current engine has
      *any* hook-point for this before assuming it's comparable in size
      to mana burn. If it's genuinely large, ship deck-legality +
      mana-burn support first, with damage-on-the-stack as an explicitly
      separate, clearly-labeled follow-on — don't let it block everything
      else.
  - Neither of us knows yet how deep this goes in the current engine —
    that uncertainty is exactly what the research phase needs to resolve,
    not something to guess a size for now.
- **Instance-configurability and the design-interface question — genuinely
  open, don't assume an answer:** "instance customizable via configs" and
  "design your own format" could mean either (or both, feeding the same
  underlying schema): (a) a **player-facing UI** where someone builds a
  format interactively in the client and it's saved/shareable, or (b) an
  **operator-facing config file** a self-hosted phase-server instance
  loads at startup/build time to enable house-rule formats for that
  deployment only (the closest existing precedent for *that* half is
  `GATED_SETS` in `crates/engine/src/database/set_gating.rs` — an
  env-var-driven, generation-time config knob, though it's a narrow
  pre-release-embargo tool, not a general format-definition mechanism).
  Resolve which (or both) is wanted, and if both, confirm they share one
  underlying data schema rather than becoming two divergent
  implementations, before designing either.
- **The four EC-attributed formats (content confirmed, architecture is
  the open question above) — not two, "all EC variants" expands the
  original "93/94 + Middle School" ask to all four on the source page:**
  1. **Old School 93-94** — Alpha, Beta, Unlimited, Arabian Nights,
     Antiquities, Revised, Legends, The Dark, Fallen Empires. Reprints
     allowed only with original frame/art. Restricted (1 copy): Ancestral
     Recall, Balance, Black Lotus, Braingeyser, Chaos Orb, Channel,
     Demonic Tutor, Library of Alexandria, Mana Drain, Mind Twist, all
     five Moxes, Recall, Regrowth, Sol Ring, Time Vault, Time Walk,
     Timetwister, Wheel of Fortune. Banned: Bronze Tablet, Contract from
     Below, Darkpact, Demonic Attorney, Jeweled Bird, Rebirth, Tempest
     Efreet. Legacy rules: mana burn only. "No Draws" rule (tied matches
     after 50 minutes settled by Chaos Orb flip, not a draw).
  2. **Old School 95** — 93-94's pool plus Fourth Edition, Ice Age,
     Chronicles, Renaissance, Homelands. Restricted list = 93-94's plus
     Demonic Consultation and Mana Crypt. Banned list = 93-94's plus
     Amulet of Quoz and Timmerian Fiends. Legacy rules: mana burn only
     (same as 93-94).
  3. **Middle School** — 1995-2003 (Fourth Edition through Scourge).
     Reprints allowed (Collector's Edition/International Collector's
     Edition, World Championship, artist proofs; even modern-bordered
     reprints "begrudgingly" allowed). **No restricted list** — 25 named
     cards fully banned instead (Amulet of Quoz, Balance, Brainstorm,
     Bronze Tablet, Channel, Dark Ritual, Demonic Consultation, Flash,
     Goblin Recruiter, Imperial Seal, Jeweled Bird, Mana Crypt, Mana
     Vault, Memory Jar, Mind's Desire, Mind Twist, Rebirth, Strip Mine,
     Tempest Efreet, Timmerian Fiends, Tolarian Academy, Vampiric Tutor,
     Windfall, Yawgmoth's Bargain, Yawgmoth's Will). Legacy rules: mana
     burn AND damage-uses-the-stack AND pre-M10 Wish templating (all
     three).
  4. **Classic Magic** — full 1993-2003 pool (Alpha through Scourge), no
     new-border reprints of any kind (proxy or not). Its own restricted
     list (37 cards, mostly a superset spanning both eras — Ancestral
     Recall, Black Lotus, Necropotence, Vampiric Tutor, Yawgmoth's
     Bargain/Will, etc.) and banned list (11 cards). Legacy rules: mana
     burn AND damage-uses-the-stack AND wish-cycle restoration (same set
     as Middle School). Banlist updates twice yearly in the real world
     (Jan 1 / Jul 1) — likely irrelevant for a single-operator fork, but
     worth noting if this ever needs periodic re-sync.
  - **Stretch goal, not core scope:** "Eternal Chaos" on the same page is
    a Lords-of-the-Pit-specific variant built on top of EC 93-94 (adds
    booster-pack tutoring during matches, a dynamically-built sideboard
    from opened packs instead of a pre-built one, and a "Gentleman's
    Agreement" pre-match ban option) — it's NOT itself an EC-defined
    format, it's LotP's own house rule layered on 93-94. Confirmed wanted
    (2026-07-07), but explicitly sequenced after the four core EC formats
    (and the general custom-format engine they're built on) ship — it
    depends on 93-94 already existing and adds a genuinely new mechanic
    (in-match pack-opening + dynamic sideboard), not just a rules-flag
    combination.
  - **Stub — Type 4's core rules as a possible future variant, NOT
    researched or designed, just flagged for later consideration
    (2026-07-07).** While cross-checking Dandan (`#5169`, a shared-library
    format proposal — see below) against this design, confirmed via
    WebSearch that **Type 4** (a real, decades-old casual format:
    unlimited mana at all times, no lands, one spell per turn, chaos
    targeting, last-player-standing) has a documented "all players use the
    pool as a shared library" variant — the same zone-sharing shape as
    Dandan. Type 4's shared-library variant is a candidate future preset
    for the general custom-format engine's `SharedZones` building block
    (see below), and its *other* core rules (infinite mana, no lands,
    one-spell-per-turn, chaos targeting) are a candidate future
    `LegacyRuleSet`-style axis in the same framework — each independently
    toggleable, the same way mana-burn/damage-on-stack are for the EC
    formats. **None of this has been investigated for engine feasibility**
    (no idea yet how large "unlimited mana"/"no lands"/"one spell per
    turn" are as engine changes) — this is a bare stub for a future
    research pass, not a scoped ask. See
    `.planning/phases/58-custom-format-engine/CONTEXT.md`'s Dandan
    cross-reference for the verified sourcing.
- **Architecture context already confirmed this session (applies whether
  the general custom-format engine turns out to be built on top of
  `GameFormat` or alongside it):**
  - `GameFormat`/`FormatConfig`/`FormatMetadata` (`crates/engine/src/types/format.rs`)
    is a real, well-established, self-documenting pattern for *built-in*
    formats (see `GameFormat::Premodern`: one enum variant, one
    `FormatConfig::premodern()` builder inheriting from `standard()`, one
    `FormatMetadata` registry entry, one `LegalityFormat` mapping) — but
    it's a closed, compile-time Rust enum, which is the right shape for a
    fixed official-format list and the *wrong* shape for player/operator-
    authored custom formats. The custom-format engine likely needs an
    additive, data-driven layer alongside this (e.g. a
    `GameFormat::Custom(CustomFormatId)` variant or an entirely separate
    format-identity concept), not a wholesale rewrite of `GameFormat`
    into stringly-typed data.
  - **Real prior art for a new-format planning cycle in this exact repo**:
    `GameFormat::Limited` — see `.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`,
    committed at `80404a98b` (`.planning/` is gitignored and was later
    stripped from tracking entirely — commit "Remove planning docs" — so
    it no longer exists in a fresh checkout; retrieve it via `git show
    80404a98b:.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`).
  - `Premodern`'s (and every built-in format's) per-card legality comes
    from an *externally-sourced* per-card `legalities` field ingested
    into `CardLegalities` (`crates/engine/src/database/legality.rs` +
    `card_db.rs`'s `normalize_legalities(&entry.legalities)`) — this
    mirrors Scryfall/MTGJSON's own bulk-data legality keys (`"standard"`,
    `"premodern"`, `"pioneer"`, etc.). **None of the four EC formats are
    expected to have that external per-card legality signal already
    populated** — confirm directly (check an actual card's raw ingested
    legality data for an `"oldschool"`/`"middleschool"`/`"classic"` key)
    rather than assuming, but if absent as expected, this is exactly the
    kind of thing the general custom-format engine needs to support
    natively: a locally-defined legal-set-code + restricted/banned-name
    list, evaluated directly against each card's set code and name,
    independent of the `CardLegalities` pipeline. `set_gating.rs` was
    checked as a candidate for this and does NOT fit (pre-release
    embargo tool only).
  - **`DeckCopyLimit::UpTo(n)`** (already exists in `format.rs`, currently
    used for per-card overrides like Relentless Rats/Nazgûl/Commander
    singleton) may directly be the right building block for "restricted
    to 1 copy" in a custom format's restricted list — check reuse before
    inventing a second, parallel "restricted list" concept.
  - **Parameterize, don't proliferate** (per CLAUDE.md) applies twice
    here: once at the "custom format schema vs. four separate EC formats"
    level (the four EC presets should be four instances of one schema,
    not four hardcoded blocks), and again within any built-in-format
    fallback path if one still exists after the custom engine is built.
  - **Design/research output belongs in `.planning/phases/<NN>-<slug>/`**
    (CONTEXT/RESEARCH/PLAN/SUMMARY/VERIFICATION docs per CLAUDE.md's own
    "Planning" section) — gitignored, stays local, decoupled from any PR,
    matching how the `GameFormat::Limited` cycle above was actually run.
    Research/design can happen well before implementation and by a
    different session/agent; don't conflate the two phases.
- **Prompt:**
  > Research and produce a plan (don't implement yet, write it to
  > `.planning/phases/<NN>-custom-format-engine/`) for a general,
  > data-driven "design your own format" engine in phase.rs, with the
  > four Eternal Central retro formats (Old School 93-94, Old School 95,
  > Middle School, Classic Magic) as the first bundled presets exercising
  > it. Do NOT scope this narrowly as "hardcode 4 GameFormat variants" —
  > the actual ask is the general engine first, formats as data on top of
  > it. Re-fetch https://github.com/northern-information/lordsofthepit.com/blob/main/src/pages/formats.md
  > to confirm the exact card pools/restricted/banned lists quoted in this
  > backlog item (as of 2026-07-07) haven't changed. First read
  > `crates/engine/src/types/format.rs` in full (trace `GameFormat::Premodern`
  > end-to-end) and `.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`
  > (retrieve via `git show 80404a98b:.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`
  > since `.planning/` is gitignored) as prior art for how a new-format
  > planning cycle has actually been scoped in this repo. Design: (1) a
  > data-driven custom-format definition schema (legal-set list,
  > restricted/banned name lists, deck-size/sideboard rules, and an
  > independently-toggleable `LegacyRules` flag set covering at minimum
  > mana burn and damage-uses-the-stack — confirmed NOT to travel together,
  > since 93-94/95 use only mana burn while Middle School/Classic Magic
  > use both, so they must be separate flags, not one "old rules" bool);
  > (2) how that schema relates to the existing closed `GameFormat` enum
  > (additive `Custom` variant vs. parallel concept — the existing enum
  > should stay closed/typed for official formats, this needs to be a
  > separate additive layer, not a rewrite into stringly-typed data); (3)
  > resolve whether "design your own format" means a player-facing UI, an
  > operator-facing per-instance config file (nearest existing precedent:
  > `GATED_SETS` in `crates/engine/src/database/set_gating.rs`, though it
  > doesn't fit as a mechanism, only as a rough shape of "env/config-driven
  > deployment customization"), or both sharing one schema — don't assume
  > an answer. Confirm directly whether the card-data pipeline's
  > `CardLegalities`/`LegalityFormat` mechanism already carries any signal
  > for these EC formats (expected: no) before designing the new
  > locally-defined legal-set/banned-list mechanism the custom-format
  > engine will need regardless. Separately and independently investigate
  > mana burn (likely small — check whether the engine already tracks
  > unspent mana at pool-emptying boundaries) versus "damage uses the
  > stack" (likely much larger — a pre-6th-edition combat-resolution
  > difference, not a deck-legality filter; report whether the engine has
  > any hook for this at all) — do not assume they're the same size of
  > change. If damage-on-the-stack is large, propose shipping
  > deck-legality + mana-burn support for all four EC formats first, with
  > damage-on-the-stack as a clearly separate, non-blocking follow-on. The
  > LotP-specific "Eternal Chaos" variant (booster-pack tutoring built on
  > 93-94, not itself an EC-defined format) is a confirmed stretch goal —
  > sequence it after the core engine and four EC presets ship; note it in
  > the plan but don't block on it.

### [research] Audit the AWS host before hosting phase.rs there

- **Status:** open
- **Source:** 2026-07-06 planning discussion
- **Why this is its own item:** read-only investigation, no changes to the
  live host — cleanly separable from, and a hard prerequisite for, the
  "Host my fork at phase.teamserio.us" item below. Do this first; it'll
  likely change details in that item's plan.
- **What's already confirmed** (don't re-ask): nginx is the reverse proxy;
  its config lives only on the host, not in any repo; `teamserio.us`
  itself deploys via GitHub Actions → SSH wipe + SCP copy to `/prod-www/`
  (secrets `DEPLOY_HOST`, `DEPLOY_USERNAME`, `DEPLOY_SSH_KEY`,
  `DEPLOY_HOST_PORT`, currently only on the `teamserio.us` repo). **TLS
  terminates at the reverse proxy itself** (confirmed by the user) — not
  an AWS-layer component (ALB/CloudFront) in front of it, so a
  `phase.teamserio.us` cert needs to be issued for nginx directly, not
  requested through an AWS console/ACM flow.
- **What's genuinely unconfirmed:**
  1. **Exact TLS mechanism on the box** — likely certbot/Let's Encrypt
     given nginx terminates TLS itself, but not confirmed which ACME
     client or whether renewal is a cron job/systemd timer — check
     `which certbot`, `systemctl list-timers`, and `/etc/letsencrypt/`
     (or equivalent) before assuming certbot specifically.
  2. **nginx config layout** — single `nginx.conf`, or
     `sites-available`/`sites-enabled` per-site convention? Pull the
     existing `teamserio.us` server block as the literal template to copy
     for `phase.teamserio.us`.
  3. **OS/distro and package manager** on the host (`/etc/os-release`) —
     needed to know how to install/verify Docker.
  4. **Is Docker already installed and in use** on this host for anything?
     `docker --version`, `docker ps`. phase-server's documented self-host
     path (README "Dedicated Server") is Docker-based; if Docker isn't
     already there, that's a real setup step, not a given.
  5. **DNS management for `teamserio.us`** — Route53, the registrar
     directly, Cloudflare, something else? Needed to add the `phase` A/CNAME
     record. (This one may not need host SSH at all — could be checked from
     wherever the domain's DNS is actually managed.)
  6. **Host capacity** — `free -h`, `df -h`, `nproc`. Confirm there's room
     for another Docker container + static site alongside the existing
     sites before assuming it'll just fit.
  7. **Firewall/security group** — confirm only 80/443 (or whatever's
     already open) is exposed, and that phase-server binding to
     `127.0.0.1` behind nginx (per README's own reverse-proxy guidance)
     doesn't need any new inbound rule.
  8. **Deploy secrets are per-GitHub-repo, not shared** — `DEPLOY_HOST`
     etc. exist on the `teamserio.us` repo's GitHub settings only; the
     fork (`rykerwilliams/phase`) will need its own copies added, or a
     dedicated SSH key/user scoped just to the phase deploy path (worth
     considering over reusing the exact same key as `teamserio.us`, to
     keep blast radius contained if either pipeline were ever compromised).
- **Prompt:**
  > SSH into the AWS host that serves `teamserio.us` and audit it,
  > read-only — do not change anything. TLS is confirmed to terminate at
  > the nginx reverse proxy itself (not an AWS-layer ALB/CloudFront), so
  > just confirm (1) the exact mechanism (`which certbot`, look for a
  > renewal cron/systemd timer, check `/etc/letsencrypt/` or equivalent);
  > (2) the nginx config layout and the literal existing server block for
  > `teamserio.us` as a template; (3) OS/distro and package manager; (4)
  > whether Docker is already installed/in use; (5) where `teamserio.us`'s
  > DNS is managed; (6) available CPU/RAM/disk headroom; (7) current
  > firewall/security-group rules. Also separately note whether
  > `DEPLOY_HOST`/`DEPLOY_USERNAME`/`DEPLOY_SSH_KEY`/`DEPLOY_HOST_PORT` are
  > only configured as secrets on the `teamserio.us` GitHub repo (expected)
  > and whether a dedicated, more narrowly-scoped SSH credential for the
  > phase deploy path is worth setting up instead of reusing the existing
  > one. Feed the findings back into the "Host my fork at
  > phase.teamserio.us" backlog item's plan — don't implement anything yet.

### [infra] Host my fork of phase.rs at phase.teamserio.us

- **Status:** open (blocked on the host-audit item above)
- **Source:** 2026-07-06 planning discussion
- **Context (verified, not assumed):**
  - Target: run my fork at `phase.teamserio.us`, on the same AWS host that
    already serves `teamserio.us` and other sites behind a single **nginx**
    reverse proxy.
  - nginx config lives **only on the host** (SSH-edited, not tracked in any
    repo) — no config-as-code to read/PR against; changes have to be made
    live over SSH and `nginx -t && systemctl reload nginx` (or equivalent).
  - Known-working deploy pattern, copied from `teamserio.us`
    (`/mnt/c/git/teamserio.us/.github/workflows/jekyll-build-and-deploy-prod.yml`):
    GitHub Actions builds the static site, then `appleboy/ssh-action` wipes
    the target directory and `appleboy/scp-action` copies the fresh build
    over SSH to a directory on the host (teamserio.us uses `/prod-www/`).
    Secrets: `DEPLOY_HOST`, `DEPLOY_USERNAME`, `DEPLOY_SSH_KEY`,
    `DEPLOY_HOST_PORT`. Phase.rs's client build is a static bundle too
    (`pnpm build` in `client/`), so the same SSH/SCP pattern applies
    directly — just to a new directory (e.g. `/phase-www/`) and a new
    nginx server block for `phase.teamserio.us`.
  - Unlike the Jekyll blog, phase.rs also needs a **running backend**:
    `phase-server` (WebSocket, `/ws`, plus `/health`) per README's
    "Dedicated Server" Docker instructions. That needs to run persistently
    on the same host (`docker run -d --restart unless-stopped`, bound to
    `127.0.0.1:9374` per README's own guidance for the reverse-proxy case),
    with nginx adding a `location /ws { proxy_pass ...; proxy_set_header
    Upgrade ...; }` block for `phase.teamserio.us` alongside the static
    file block.
  - Card data must be generated **from this fork**
    (`scripts/gen-card-data.sh`), not pulled from upstream's published
    data, or fork-only fixes (e.g. Hollow One) silently won't show up in
    play. The upstream `phase-server` Docker image
    (`ghcr.io/phase-rs/phase-server`) is built from upstream too — the
    fork needs its own image (root `Dockerfile`) built and either pushed
    to `ghcr.io/rykerwilliams/phase-server` or built directly on the host.
  - TLS for the new subdomain: unconfirmed whether the host already uses
    certbot/Let's Encrypt for its other sites — check on the host before
    assuming a mechanism.
  - Project is a **non-commercial fan project** under the WotC Fan Content
    Policy — hosting must stay within that (no monetization, etc.).
- **Prompt:**
  > Produce a concrete, step-by-step plan to host my phase.rs fork
  > (`rykerwilliams/phase`) at `phase.teamserio.us`, on the same AWS host
  > that already serves teamserio.us behind nginx (config is host-only,
  > SSH-edited, not in any repo). Mirror teamserio.us's own deploy pattern
  > (`.github/workflows/jekyll-build-and-deploy-prod.yml` in
  > `/mnt/c/git/teamserio.us`) for the static client: GitHub Actions builds
  > `client/` with `pnpm build` against card data generated from *this
  > fork* (not upstream's), then `appleboy/ssh-action` + `scp-action` ships
  > it to a new directory on the host (e.g. `/phase-www/`). Additionally
  > plan: (1) the phase-server Docker container running persistently on
  > the host bound to localhost only, built from the fork's own
  > `Dockerfile`; (2) the exact nginx server block for
  > `phase.teamserio.us` — static file serving plus a `/ws` WebSocket
  > proxy to phase-server, and how it should get a TLS cert (check what
  > the host already uses for its other sites before assuming certbot);
  > (3) whether GitHub Actions should also build+push the fork's
  > `phase-server` image, or whether it's simpler to `git pull` + rebuild
  > directly on the host when the fork's engine changes. Confirm the nginx
  > software/config approach and get my explicit go-ahead on the exact SSH
  > commands and nginx block before touching the live host — it's serving
  > my real blog and other sites, so nothing here should run unattended.

### [feature] Configurable, non-copyrighted card back art

- **Status:** open
- **Source:** 2026-07-06 planning discussion
- **Context (verified against the repo, not assumed):**
  - Card back art is currently hardcoded: `CARD_BACK_URL` in
    `client/src/services/scryfall.ts:33-34`, hotlinked from Scryfall's
    generic-back CDN asset, deliberately non-configurable to avoid bundling
    WotC-copyrighted art. No config/env override exists today.
  - There's an almost-exact architectural precedent already upstream to
    mirror: **board background** is a real, pluggable preference —
    `boardBackground` (`"auto-wubrg" | "random" | "none" | "custom" |
    string`) plus `customBackgroundUrl` in the preferences store, resolved
    in `client/src/components/board/BattlefieldBackground.tsx:20-54`
    (curated art, plain colors, deck-color auto-match, or a user-supplied
    custom image URL), surfaced in `PreferencesModal.tsx:97-106+` and
    `BoardContextMenu.tsx:71`.
  - The audio theme system (`client/src/audio/themeRegistry.ts`) is a
    second precedent for "load user-supplied asset by URL, validate,
    cache" if a richer manifest (e.g. a full back-art *set* rather than one
    URL) ends up being wanted instead of a single image URL.
  - This is generically useful (not fork-specific) and follows an existing,
    already-accepted pattern closely enough that it's a real candidate for
    an upstream PR to `phase-rs/phase`, not just a personal fork
    customization — worth floating to the maintainer/Discord before
    building, in case there's already a reason it wasn't done (e.g. a
    licensing concern specific to *any* non-default back art, even
    non-copyrighted).
- **Prompt:**
  > Add a configurable card-back-art preference to phase.rs, mirroring the
  > existing `boardBackground`/`customBackgroundUrl` pattern
  > (`client/src/components/board/BattlefieldBackground.tsx`,
  > preferences store). Default stays the current hardcoded Scryfall
  > generic back (`client/src/services/scryfall.ts` `CARD_BACK_URL`) so
  > behavior is unchanged out of the box; add a preference (e.g.
  > `cardBackUrl: "default" | string`) that lets a user supply their own
  > non-copyrighted image URL, surfaced in the same preferences modal /
  > context-menu pattern board background uses. This is a frontend-only,
  > display-layer change per CLAUDE.md's engine/frontend split — no engine
  > involvement expected. Use the `/add-frontend-component` skill for the
  > UI piece. Before implementing, check whether this is better proposed
  > upstream to `phase-rs/phase` (it mirrors an already-accepted pattern
  > and isn't fork-specific) rather than kept as a fork-only customization
  > — flag that choice back to me rather than assuming either way.

### [bug-fix] Ad Nauseam's repeat loop never adds revealed cards to hand (GitHub #1032)

- **Status:** in-progress — fixed, tested, PR open awaiting CI/review:
  [phase-rs/phase#5315](https://github.com/phase-rs/phase/pull/5315)
- **Source:** GitHub issue [phase-rs/phase#1032](https://github.com/phase-rs/phase/issues/1032),
  surfaced via the same Vintage-relevance sweep as the Underworld Breach
  item above.
- **Verified Oracle text** (Scryfall, not from memory): "Reveal the top
  card of your library and put that card into your hand. You lose life
  equal to its mana value. You may repeat this process any number of
  times." ({3}{B}{B})
- **Confirmed real bug (2026-07-07)**, reproduced from scratch via parsed
  Oracle text in an isolated worktree, through two rounds of
  `/engine-planner` + `/review-engine-plan` (round 1 had a factual error
  in its root-cause model — claimed `pending_continuation` was
  last-write-wins/clobbering, when it actually accumulates via
  `append_to_sub_chain` — which would have produced a non-discriminating
  test; round 2 corrected this) and one clean `/review-impl` pass.
- **Root cause:** `engine_resolution_choices.rs`'s `RepeatDecision`
  accept-handler re-entered `resolve_ability_chain` without resetting
  `state.waiting_for` away from the just-answered `RepeatDecision`
  prompt, which fooled `waits_for_resolution_choice` into deferring each
  iteration's `ChangeZone`(hand)/`LoseLife` sub-chain into
  `pending_continuation` instead of running it immediately — deferred
  pairs accumulated and all drained in one batch on decline, matching the
  reported symptom exactly.
- **Fix:** one-line `set_priority(state, player)` reset, mirroring the
  sibling `decline` branch and the analogous `OptionalEffectChoice`
  resume handler, both of which already do this. Class-level fix — covers
  every `RepeatContinuation::ControllerChoice` card with a multi-step
  body, not just Ad Nauseam. CR 107.1c + CR 608.2c verified against
  `docs/MagicCompRules.txt`.
- **Verification:** new discriminating integration test (asserts hand/life
  *between* accepts, not just final aggregate — final totals are
  identical whether the bug is present or not) confirmed to fail on the
  unfixed code and pass on the fixed code; 9/9 sibling repeat-mechanism
  tests and 3/3 existing lib unit tests unaffected; `cargo fmt`/`clippy
  -D warnings` clean.

### [bug-fix] Relic of Progenitus's first ability doesn't respect the targeted player (GitHub #1077)

- **Status:** open — narrowed from the original two-part report
- **Source:** GitHub issue [phase-rs/phase#1077](https://github.com/phase-rs/phase/issues/1077);
  standard Vintage sideboard graveyard hate against Dredge (a current
  top-3 Vintage archetype) — no open PR.
- **Verified Oracle text:** "{T}: Target player exiles a card from their
  graveyard. {1}, Exile this artifact: Exile all graveyards. Draw a
  card." ({1})
- **Investigated 2026-07-07:** traced against current `main` before
  implementing. The *second* ability ("exile all graveyards, draw a
  card") uses only well-tested primitives (exile-self cost,
  `ChangeZoneAll`, `Draw`) and multi-activated-ability parsing is
  foundational engine-wide — no evidence this is actually broken as the
  original report claimed. Narrowing this item to the first ability only.
- **Reported bug (first ability, still real):** `inject_subject_target`
  (`oracle_effect/mod.rs`) rewrites the subject for `Discard`, `Draw`,
  `Scry`, `Token`, `ChangeZoneAll`, `Shuffle`, etc., but **not**
  `Effect::ChangeZone` — the single-card exile this ability needs. The
  generic exile fallback (`oracle_effect/imperative.rs`) only has a
  hardcoded `attach_controller_if_absent(ControllerRef::You)` arm for
  "...from your hand"; there's no possessive-pronoun-to-target-player
  binding for "...from their graveyard." This matches the reported
  symptom (shows activator's own graveyard instead of the targeted
  player's).
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Relic of Progenitus's first ability (GitHub phase-rs/phase#1077):
  > "Target player exiles a card from their graveyard" must bind the
  > exile's subject/controller to the *targeted player*, not the
  > activator. Verify Oracle text against Scryfall first. `ChangeZone`
  > is missing from `inject_subject_target`'s handled-effect list
  > (`oracle_effect/mod.rs`) alongside `Discard`/`Draw`/`Scry`/`Token`/
  > `ChangeZoneAll`/`Shuffle` — this is a possessive-pronoun-to-target
  > binding gap in a shared building block, not a Relic-specific fix, so
  > check whether other "target player discards/exiles/puts a card from
  > their [zone]" effects share the same gap before scoping the fix to
  > just `ChangeZone`. Do NOT touch the second ability ("exile all
  > graveyards, draw a card") — investigation confirmed it already works
  > correctly; the original issue's claim about it not working appears to
  > be false.

### [feature] Licid cycle "becomes an Aura, attach, revert" mechanic is entirely unimplemented (GitHub #605, #604)

- **Status:** open — investigated 2026-07-07, upgraded from "bug-fix" to
  "feature": this is a genuinely new mechanic, not a small bug, so it's
  a bigger lift than the original backlog framing assumed. Deferred this
  session in favor of other candidates given the low real-world priority
  (see below) and the size of the actual build.
- **Source:** GitHub issues [phase-rs/phase#605](https://github.com/phase-rs/phase/issues/605)
  and [phase-rs/phase#604](https://github.com/phase-rs/phase/issues/604);
  Homelands (1995) — Homelands commons are notoriously weak and this was
  never actually a played card, even casually. Low conviction, tracked
  anyway per instruction.
- **Verified: this is a real 12-card cycle**, not just Calming Licid —
  fetched all 12 directly from Scryfall's search API this session
  (`type:Licid`), not from memory: Calming, Convulsing, Corrupting,
  Dominating, Enraging, Gliding, Leeching, Nurturing, Quickening,
  Stinging, Tempting, and Transmogrifying Licid. All 12 share the
  **identical** shape — "**[cost], {T}: This creature loses this ability
  and becomes an Aura enchantment with enchant creature. Attach it to
  target creature. You may pay [cost] to end this effect.**" — differing
  only in activation/end cost and the granted ability while attached
  (can't attack, can't block, fear, control-steal, haste, flying,
  regenerate, first strike, drain-on-tap, force-block, or
  artifact+pump). Any fix must be parameterized across all 12, not
  hardcoded to Calming Licid's "can't attack" grant.
- **Investigated 2026-07-07 — #605 confirmed genuinely unimplemented,
  #604 unconfirmed / possibly not a real independent bug:**
  1. **(#605, real)** Exhaustive grep for "becomes an aura"/"become an
     aura" across `crates/engine/src/parser/` returns zero non-test
     hits for this shape. The only related machinery,
     `Effect::ReturnAsAura` (`types/ability.rs:10236`), is NOT reusable
     as-is — it's a **replacement effect fired during a zone change**
     (a card entering the battlefield FROM THE GRAVEYARD as an Aura;
     class members Old-Growth Troll, Bronzehide Lion, Harold and Bob),
     structurally different from a Licid's activated ability
     transforming an **already-battlefield** permanent in place. The
     only other Licid-specific code in the repo
     (`parser/clause_shell.rs:483`,
     `is_you_may_pay_to_end_effect_phrase`) only covers the "you may
     pay to end this effect" clause not making the whole activation an
     optional yes/no prompt (a prior, narrower fix for issue #4000) —
     it does not touch the transform/attach itself, which is a no-op
     regardless of target.
  2. **(#604, unconfirmed)** `has_summoning_sickness`
     (`game/combat.rs:3171`) and the turn-start clear
     (`game/turns.rs:1006-1015`) are fully generic with no Licid/
     type-change special-casing anywhere. Since the transform in #605
     never executes today, there's no existing code path that could
     have produced whatever #604 originally observed — **re-verify #604
     in isolation** (an untouched Licid across a turn boundary, no
     ability activation involved) before assuming it's a real,
     independent bug; it may describe confusion stemming from #605, or
     may not reproduce at all.
- **Design questions an implementation plan needs to resolve** (not yet
  answered — this needs a fresh `/engine-planner` pass, not just this
  research):
  1. New `Effect` variant vs. composing existing building blocks (some
     existing type-changing CDA pattern + `Attach` + a revert
     mechanism)? `ReturnAsAura`'s shape (`enchant_filter: TargetFilter`,
     `grants: Vec<ContinuousModification>`) is the closest analog to
     trace even though it's not directly reusable.
  2. How does "You may pay [cost] to end this effect" work as a
     **revert** — a permanent gaining a new activated ability as part
     of the transform, where activating it turns the Aura back into a
     creature? What characteristics does it revert to (its original
     printed characteristics, per CR 400.7's "new object" semantics —
     verify the exact number against `docs/MagicCompRules.txt`)?
  3. What happens if the enchanted creature leaves the battlefield —
     does the Licid-as-Aura fall off/die per the standard "Aura with no
     legal attachment" SBA (verify the exact CR number), or revert to a
     creature? Trace how existing (non-Licid) Auras already handle this
     — that building block should already exist and just needs to
     apply correctly here, not be reinvented.
  4. Targeting: "Attach it to target creature" is targeted at
     **activation** time (CR 601.2c-style, verify against the activated-
     ability equivalent), not chosen later — confirm this doesn't
     conflict with "it" (the Licid itself) being a self-reference within
     the same activated ability's resolution, not a new spell.
- **Prompt:**
  > Implement the Licid cycle's "becomes an Aura, attach, revert"
  > mechanic (GitHub phase-rs/phase#605), covering all 12 real cards
  > (Calming, Convulsing, Corrupting, Dominating, Enraging, Gliding,
  > Leeching, Nurturing, Quickening, Stinging, Tempting, Transmogrifying
  > Licid — verify each against Scryfall, don't assume from this note).
  > This is a genuinely new mechanic, not a small fix — `Effect::ReturnAsAura`
  > is the closest existing analog but is NOT directly reusable (it's a
  > graveyard-entry replacement effect, not an activated-ability
  > self-transform of an already-battlefield permanent). Resolve the 4
  > design questions above in the plan before writing any code. Treat
  > #604 (summoning sickness) as a separate, lower-priority follow-up —
  > re-verify it reproduces in isolation before planning any fix for it,
  > since no Licid-specific summoning-sickness defect was found and the
  > transform never executing today means there's nothing that could
  > have produced whatever #604 originally observed. Use
  > `/add-static-ability` and/or `/add-replacement-effect` as applicable
  > once the design in question 1 is resolved.

### [done] Molten Echoes gives haste to the wrong object and skips its end-step exile (GitHub #4709, #4708)

- **Status:** done — already fixed on `main`, verified with a new targeted
  test, no production code change needed.
- **Source:** GitHub issues [phase-rs/phase#4709](https://github.com/phase-rs/phase/issues/4709)
  and [phase-rs/phase#4708](https://github.com/phase-rs/phase/issues/4708);
  Middle-School-era (Torment) — obscure even in its own era, low
  conviction, tracked anyway per instruction.
- **Verified Oracle text** (note: differs from both issues' "expected
  behavior" — the real card says *exile*, not sacrifice, and grants haste
  to the *token*, matching #4709 but contradicting #4708's assumption):
  "As this enchantment enters, choose a creature type. Whenever a
  nontoken creature you control of the chosen type enters, create a token
  that's a copy of that creature. That token gains haste. Exile it at the
  beginning of the next end step." ({2}{R}{R})
- **Investigation:** both reported bugs are already fixed by the existing
  "that token"/"it" anaphor-rewriting building block in
  `oracle_effect/lower.rs` (`rewrite_parent_target_to_last_created` and
  the sibling "that token" rewrite), the same infrastructure already
  proven for Flameshadow Conjuring and Inalla, Archmage Ritualist. The one
  genuinely untested piece was whether Molten Echoes' extra "of the chosen
  type" filter on the trigger condition (`FilterProp::IsChosenCreatureType`)
  interferes with that rewrite — it doesn't. Added
  `molten_echoes_chosen_type_filter_preserves_last_created_anaphors`
  (`crates/engine/src/parser/oracle_trigger_tests.rs`) confirming the
  `CopyTokenOf` source stays `TriggeringSource` and the delayed exile
  target binds `TargetFilter::LastCreated`. Full `oracle_trigger::tests`
  module re-run clean: 964 passed, 0 failed, 0 regressions.
- **PR:** [phase-rs/phase#5352](https://github.com/phase-rs/phase/pull/5352)
  (test-only, verified fresh off `origin/main` post-#5349).
- **Evidence posted:** comments on both
  [#4709](https://github.com/phase-rs/phase/issues/4709#issuecomment-4910503767)
  and [#4708](https://github.com/phase-rs/phase/issues/4708#issuecomment-4910503855)
  (can't close directly — no repo permissions).

### [feature] Theme Pack system (bundled, per-deployment branding)

- **Status:** open
- **Source:** 2026-07-06 planning discussion
- **Motivation:** not just cosmetic options for one player — the real goal
  is per-deployment branding. If I end up hosting this at multiple
  subdomains (e.g. `phase.teamserio.us` vs. a hypothetical
  clevelandrocs-flavored instance), each deployment should be able to ship
  a different **default look** as one bundled unit, while individual
  players can still override pieces for themselves. This depends on the
  card-back-art item above as one of its building blocks — do that one
  first, then build the pack registry on top of it plus the two systems
  that already exist.
- **Context (verified against the repo, not assumed):**
  - **Two real precedents to generalize from, don't invent a third
    pattern:** the audio theme registry
    (`client/src/audio/themeRegistry.ts` — `BUILT_IN_THEMES`, validated
    JSON manifest, load-by-URL, IndexedDB cache) and the board-background
    preference (`boardBackground`/`customBackgroundUrl`,
    `BattlefieldBackground.tsx:20-54`). A "theme pack" is naturally a
    manifest that bundles: a palette (see below), a card back URL (once
    the item above ships), a board-skin selection, and an audio theme
    reference — i.e. compose the two existing per-facet systems plus two
    new facets into one selectable unit, rather than building a
    from-scratch bundling mechanism.
  - **Curated background art is currently a single global, hardcoded
    list**, not scoped per anything: `BATTLEFIELDS` in
    `client/src/components/board/battlefields.ts` (flat array, one fixed
    set for every player/deployment). "Set the curated art for
    backgrounds" (per pack) means this list needs to become
    pack-scoped/overridable rather than a single module-level constant —
    same shape of change as making `CARD_BACK_URL` configurable.
  - **Color palette has no runtime system at all today** — single static
    `@theme` block in `client/src/index.css:20-96` (Tailwind v4's
    CSS-native config; there is no `tailwind.config.*` to layer variants
    onto). Making the palette swappable is the one facet with no existing
    precedent to mirror — likely needs its own small registry (CSS custom
    properties swapped via a `data-theme-pack` attribute on `<html>`,
    analogous to how the existing dark/light `data-theme` toggle already
    works per the artifact-design conventions used elsewhere) rather than
    literally copying the audio/board pattern.
  - **Card frame / card face style is UNINVESTIGATED** — no research done
    yet on how individual card rendering works or whether it's realistically
    swappable. Do not assume it's a small change; investigate the actual
    card-rendering component(s) first as step 1 of implementing this, and
    report back what's actually involved before committing to scope.
  - Per-deployment default selection likely wants a build-time or
    server-config mechanism (env var read at build, or a config JSON
    served alongside `card-data.json`) rather than requiring every new
    visitor to manually pick a pack — but confirm this against how
    `client/public/*` config/meta files are already loaded before
    designing a new one.
- **Prompt:**
  > Design (don't implement yet) a Theme Pack system for phase.rs that
  > bundles: color palette, board-skin (background image + a pack-scoped
  > curated art list, generalizing the current global `BATTLEFIELDS` in
  > `client/src/components/board/battlefields.ts`), card back art (once
  > the separate card-back-art backlog item ships), and an audio theme
  > reference (`client/src/audio/themeRegistry.ts`) into one selectable
  > unit. Goal: a given deployment (e.g. `phase.teamserio.us`) can ship
  > with its own default pack while individual players can still override
  > any single facet via existing per-facet preferences. Explicitly
  > investigate and report on card frame/face rendering (how individual
  > cards are drawn today, whether style is realistically swappable)
  > before scoping that facet in or out — this hasn't been researched yet.
  > For the color palette facet, propose a mechanism analogous to the
  > existing dark/light theme toggle (a root attribute swapping CSS custom
  > properties) rather than a new one-off system. Reuse the audio-theme
  > registry's manifest/validation/caching pattern for the pack manifest
  > itself rather than inventing new loading/caching logic. Produce a plan
  > with the mandatory `/engine-planner`-style architectural sections
  > (though this is frontend-only, no engine involvement) — pattern
  > coverage, building-block reuse, logic placement — then stop for review
  > before writing code, since this touches several existing preference
  > systems and a wrong seam here is expensive to unwind later.

### [feature] Add a Premodern metagame decks feed

- **Status:** open
- **Source:** 2026-07-07 request
- **Context (verified against the repo, not assumed):** phase.rs already has
  a per-format metagame-decks feed system, distinct from the Commander-only
  "precon" system (`useDecks.ts`, `PreconDeckModal.tsx`) — don't confuse the
  two. The relevant one is `client/src/data/feedRegistry.ts:12-74`, which
  lists a bundled feed JSON per format (`mtggoldfish-standard.json`,
  `-modern`, `-pioneer`, `-commander`, `-legacy`, `-vintage`, `-pauper`) at
  `client/public/feeds/*.json`, in the shape `{id, name, description, icon,
  format, version, updated, source, decks: [{name, author, colors, tags,
  main:[{count,name}], sideboard, commander?}]}`. **No
  `mtggoldfish-premodern.json` exists yet** — that's the gap. `Premodern` is
  already a fully supported engine format
  (`crates/engine/src/types/format.rs:42` `GameFormat::Premodern`,
  `client/src/data/formatRegistry.ts:76-84`), so this is purely a
  missing-feed gap, not a missing-format gap.
  - Feed generation already has an external-source pipeline to extend:
    `crates/feed-scraper/src/scrape.rs` scrapes
    `https://www.mtggoldfish.com/metagame/{format}` (URL built at
    `scrape.rs:16`) via a `--format` CLI arg (`main.rs:19-21`, comma-separated
    list), writing feed JSON into `client/public/feeds/`. MTGGoldfish does
    have a `/metagame/premodern` page, so `--format premodern` should work
    with no scraper changes — just needs to be added to the invocation.
    `.github/workflows/refresh-feeds.yml:34` (daily cron) currently only
    passes `--format standard,modern,pioneer,commander`; add `premodern` to
    that list so it refreshes automatically going forward (existing
    legacy/vintage/pauper feeds exist but appear to have been generated
    manually/separately, not via the cron — check whether they should also
    be added to the cron list while touching this, or leave that as a
    separate decision).
  - Minor: `config_format_tag()` in `scrape.rs:283-302` has a hardcoded
    format-name list used only for a title-matching fallback tag; it doesn't
    include `"premodern"` today. Not blocking (falls back to a generic
    `"metagame"` tag, cosmetic only) but worth adding while in this file.
  - **tcdecks.net has no existing precedent anywhere in this repo** — if
    MTGGoldfish's `/metagame/premodern` page turns out to be thin/stale
    (Premodern has a much smaller competitive scene than the formats
    `feed-scraper` currently targets), tcdecks.net would be a second,
    net-new source requiring its own scraper — confirm MTGGoldfish coverage
    is adequate first before building a second source for one format.
- **Prompt:**
  > Add a Premodern feed to phase.rs's metagame-decks system (not the
  > Commander-only precon system — those are separate; this is
  > `client/src/data/feedRegistry.ts` + `client/public/feeds/*.json`).
  > `Premodern` is already a supported engine format
  > (`crates/engine/src/types/format.rs`); the gap is purely the missing
  > `mtggoldfish-premodern.json` feed. Extend `crates/feed-scraper` (already
  > scrapes `mtggoldfish.com/metagame/{format}`, see `scrape.rs`) with
  > `--format premodern` and add it to the `.github/workflows/refresh-feeds.yml`
  > cron's `--format` list so it refreshes automatically. Check MTGGoldfish's
  > actual `/metagame/premodern` page first to confirm it has real deck data
  > worth scraping (Premodern's competitive scene is much smaller than
  > Standard/Modern/Pioneer) — only reach for tcdecks.net as a second source
  > if MTGGoldfish's Premodern coverage turns out inadequate, since
  > tcdecks.net has zero existing scraper precedent in this repo and would be
  > net-new work. Register the new feed in `feedRegistry.ts` following the
  > existing per-format entries exactly. Also add `"premodern"` to the
  > format-name list in `config_format_tag()` (`scrape.rs`) for a correct
  > fallback tag.

### [feature] Deck builder silently drops the printing/set a player picked or imported, instead of tracking it

- **Status:** open
- **Source:** 2026-08-24. Surfaced while resolving discussion #5312's
  custom-format-engine proposal (PR #7703, round 11) — the question there
  was whether Old School 93-94/95 needed printing-level LEGALITY
  enforcement, resolved as no (confirmed `legal_sets` membership is the
  same oracle-card-level legality model every format including Premodern
  already uses — no format anywhere in this engine checks printing/frame/
  foil for legality, `LegalityFormat::Premodern`,
  `crates/engine/src/types/format.rs:243`). This item is a genuinely
  separate, real, general idea that came up along the way and is worth its
  own backlog entry rather than being bundled into that PR.
- **Context (verified against the repo this session, not assumed):**
  - The deck builder already has the UI shape for this — it isn't a
    from-scratch feature. `PrintingPickerModal.tsx`
    (`client/src/components/deck-builder/PrintingPickerModal.tsx:142-203`)
    lets a player browse every printing of a card (art/set/collector-number
    grid) and pick one. But selecting a printing only calls
    `setArtOverride(oracleId, {...})` (`PrintingPickerModal.tsx:52-62`),
    which writes into `usePreferencesStore`'s `artOverrides` — a
    client-local, oracle-id-keyed cosmetic preference used purely to
    resolve art (`useCardImage.ts`), never persisted to a saved deck and
    never sent to the engine. It's also only reachable from the deck
    list's context menu (`useDeckBuilder.ts:106-132`), not the add-card
    flow itself.
  - Import parsing already captures the data, then throws it away.
    `DeckEntry.sourcePrinting` (`client/src/services/deckParser.ts:5-9`,
    type at `useCardImage.ts:25-28`) is populated when importing decklists
    in formats that embed set codes (Forge/MTGA/Archidekt, regexes at
    `deckParser.ts:101,186`) — but it's explicitly discarded at the
    `expandParsedDeck`/`expandEntries` boundary (`deckParser.ts:45-73`,
    which only pushes `entry.name`) before producing `ExpandedDeck`
    (`main_deck`/etc. are plain `string[]` of names). It's used downstream
    only for hover-preview art (`CardEntryRow.tsx:120`, `DeckStack.tsx`)
    and never reaches `deckCatalog.ts`'s saved-deck shape (no matches
    there) — so importing a decklist that names specific printings loses
    that detail permanently the moment it's saved.
  - The engine has no field to receive it even if the frontend kept it.
    `PrintedCardRef { oracle_id, face_name }`
    (`crates/engine/src/types/card.rs:89-92`) and the deck-submission
    struct `PlayerDeckList` (`crates/engine/src/game/deck_loading.rs:120-147`
    — `main_deck`/`sideboard`/`commander`/etc. are all `Vec<String>` of
    names) have no set-code field anywhere. Card resolution is name-only
    (`CardDatabase::get_face_by_name`, `crates/engine/src/game/printed_cards.rs:1049`).
  - **Explicitly NOT a legality feature.** This is about recording/
    preserving a player's chosen printing (so importing a decklist that
    names one doesn't silently lose it, and a deliberate in-app choice
    persists across saves) — not about validating it against anything.
    No format in this engine enforces printing-level legality today and
    this item doesn't propose changing that.
  - **Related but genuinely separate — don't conflate:** making the
    frontend's `ArtChainEntry` `{type: "oldest"}` display-default
    legal-set-aware (so "show me the oldest printing" respects a format's
    declared `legal_sets` instead of picking a promo/non-tournament
    printing) is a different feature — a display-default fix, independent
    of whether a player's chosen printing is ever persisted. File that as
    its own item if pursued.
- **Prompt:**
  > Spec out (research/plan only, no implementation yet) how phase.rs's
  > deck builder should track which specific printing (set code) a player
  > picked or imported for a card, instead of silently discarding it.
  > Today: `PrintingPickerModal.tsx` already lets a player pick a printing
  > but only writes to `usePreferencesStore`'s local `artOverrides`
  > (cosmetic-only, never persisted or sent to the engine). Import parsing
  > (`deckParser.ts`'s `DeckEntry.sourcePrinting`) already captures set +
  > collector-number when importing Forge/MTGA/Archidekt decklists, but
  > discards it at the `expandParsedDeck`/`expandEntries` boundary before
  > producing `ExpandedDeck` (plain `string[]` of names). The engine's
  > `PrintedCardRef`/`PlayerDeckList` have no set-code field at all. Scope
  > as: (1) stop dropping `sourcePrinting` at the `expandParsedDeck`
  > boundary and persist it through `deckCatalog.ts`'s saved-deck shape;
  > (2) wire `PrintingPickerModal` into the add-card flow itself, not just
  > the post-add context menu; (3) decide whether/how the chosen printing
  > should cross the wire to the engine (`PlayerDeckList` gaining a
  > parallel per-card set-code field) for round-tripping, NOT for legality
  > enforcement — no format in this engine checks printing for legality
  > (confirmed against `LegalityFormat::Premodern`), and this spec should
  > not propose changing that. Treat "make `ArtChainEntry`'s oldest-printing
  > display default legal-set-aware" as a separate, unrelated backlog item
  > — don't fold display-default logic into this spec.

---

## Done

### [bug-fix] ~~Solitary Confinement prevents damage to all players instead of just its controller~~ — already fixed (GitHub #1062)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1062](https://github.com/phase-rs/phase/issues/1062)
- **Investigated 2026-07-07.** Parser (`oracle_replacement.rs`) already
  maps "dealt to you" to `damage_target_controller()`, and an existing
  test named for this exact card
  (`replacement_prevent_all_damage_to_you_without_duration`) asserts
  it. Fix commit `a46cf1002` ("Scope damage prevention to controller",
  2026-05-27) confirmed as an ancestor of current `main` — a generic
  fix across 9 call sites (Hallow, Safe Passage, Solitary Confinement,
  redirection shields), not card-specific. Reporter's build
  (`v0.1.36 1e14782`, 2026-05-25) predates the fix by two days — real
  bug when filed, simply never closed out. Runtime match
  (`player_scope_matches`) is an exhaustive typed-enum match, already
  tested for controller-vs-opponent scoping. Confirmed the parser logic
  and test assertion directly from source myself; the compiled test run
  itself hit the same incremental-build corruption already logged as
  standing lesson 10 (heavy concurrent load from other active
  worktrees), not a real blocker.
- **Action taken:** commented on the GitHub issue with this evidence;
  no PR needed. **Update:** re-ran the exact named test successfully
  once machine load eased (`replacement_prevent_all_damage_to_you_without_duration`
  passes) — comment updated to cite an executed run, not just a source
  read. See `PIPELINE-LOG.md` standing lesson 11 for why this
  re-verification pass happened at all.

### [bug-fix] ~~Violent Urge grants delirium bonus to all creatures, not just the target~~ — already fixed (GitHub #1272)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1272](https://github.com/phase-rs/phase/issues/1272)
- **Investigated 2026-07-07.** Verified against Scryfall's exact
  verbatim text (including the real embedded newline between the base
  clause and the Delirium clause). Parser AST dump confirmed both
  clauses carry `affected: TargetFilter::ParentTarget` — "that creature"
  correctly anaphors to the single cast-time target. Runtime test (3
  creatures: target, same-controller bystander, opponent's creature)
  confirmed only the target gains double strike.
- **Root cause of why it's already fixed:** same "target X gets A.
  [condition] — that X also gets B" template as Mu Yanling, Sky
  Dignitary's +2 (issue #2922, "broadcasts to every matching permanent
  instead of the parent target"), generically fixed by
  `24afeefbb` ("fix: ParentTarget GenericEffect binding for targeted
  pump/debuff abilities", #2999) — which landed after this issue was
  filed. Violent Urge just never got a follow-up regression test or
  issue closure.
- **Action taken:** commented on the GitHub issue; **update:** the
  original comment cited a deleted scratch test the investigating agent
  didn't persist — re-verified by writing a real, permanent test
  (`violent_urge_delirium_scopes_to_parent_target_not_all_creatures`),
  ran it locally (pass), and shipped it as
  [phase-rs/phase#5348](https://github.com/phase-rs/phase/pull/5348).
  Comment updated to cite the executed test instead. See
  `PIPELINE-LOG.md` standing lesson 11.

### [bug-fix] Underworld Breach's own escape grant applying to itself off-battlefield (GitHub #1033) — real bug, fixed via #5350 + #5381

- **Status:** done — real bug, fixed and merged (#5350 + #5381, not "already fixed" as originally concluded)
- **Source:** GitHub issue [phase-rs/phase#1033](https://github.com/phase-rs/phase/issues/1033),
  surfaced via a Vintage-relevance sweep of unclaimed `[Card Bug]` issues.
- **Point 1** ("exile 0/0, cast goes through anyway") confirmed already
  fixed by `aa4ee3455` — no action needed, verified via
  `cargo test -p engine --lib escape` (31/31 pass).
- **Point 2 ("Breach re-escapes itself from the graveyard") — full saga:**
  1. **2026-07-07, initial investigation:** concluded "not a bug" via
     CR 604.2 source-tracing only (no executed test).
  2. **Same night, re-verification:** wrote and ran a real discriminating
     test (`escape_grant_from_graveyard_source_does_not_apply_to_itself`)
     to back the claim with execution, not just source-reading — the
     test **failed**, revealing point 2 was a real, live bug after all.
     Root cause: `active_continuous_effects_from_static_definitions`
     (`layers.rs`) skipped its zone-of-function gate entirely whenever a
     static's `active_zones` was empty (the documented battlefield-only
     default), so Breach's own grant kept applying after it left the
     battlefield.
  3. Full plan → review → implement → review pipeline (4 blockers found
     across 3 planning rounds; 2 more unmigrated sibling functions with
     the identical bug found across 2 implementation-review rounds)
     produced a 6-function fix. Before it could be pushed, the maintainer
     (`matthewevans`) independently pushed their own 3-commit fix
     directly to the PR branch, scoped narrowly to just the one call path
     Underworld Breach hits (a caller-side pre-filter on
     `active_continuous_effects_from_base_static_source`) — merged as
     [phase-rs/phase#5350](https://github.com/phase-rs/phase/pull/5350).
     Per explicit user instruction ("use his always"), deferred to the
     maintainer's version rather than pushing a competing commit; the
     broader fix was preserved on `archive/underworld-breach-broader-zone-gate-fix`
     rather than discarded.
  4. **Follow-up PR** [phase-rs/phase#5381](https://github.com/phase-rs/phase/pull/5381)
     reconciled the two: verified which of the original 6 sibling fixes
     still applied after #5350 merged (5 of 6 — only the one function
     #5350 already fixed was dropped), confirmed the existing off-zone
     test fixtures still pass unmodified under #5350's approach (no
     `.active_zones()` additions needed after all), and shipped the
     remaining 5 migrations plus a deleted redundant duplicate
     (`graveyard_permission_functions_in_zone`) as a clean, non-competing
     follow-up — including a discussion point (not a demanded fix) about
     a possible CR 113.6b gap in #5350's own admission rule.
- **Lesson:** "verify locally" cuts both ways — the same discipline that
  catches a false "already fixed" claim can also *reveal* a real bug
  behind one. See `PIPELINE-LOG.md` standing lessons 11–13.
- **#5381 CI/review saga after initial push:**
  1. `matthewevans` CHANGES_REQUESTED (commit `ad7ec9c22`): `compute_combat_tax`'s
     outer command-zone gate was emblem-only (`!source_obj.is_emblem`),
     silently dropping legitimate non-emblem command-zone opt-in sources
     (planes/schemes/conspiracies). Fixed by swapping in
     `object_sources_static_from_command_zone` (commit `e865c5444`),
     matching the admission rule every other command-zone gather already
     used; added a positive+negative test pair, live-revert-proven.
  2. Same review round, `matthewevans` also pushed `ad7ec9c22` directly to
     the PR branch — a fix to the `phase-ai` regression I'd caused (CR
     113.6g Stack-only gate broke `spell_can_be_countered`'s predictive
     check on hand-resident spells). That commit called
     `Definitions::iter_all`, which is `pub(crate)` in the `engine` crate
     and not visible from `phase-ai` — broke the workspace build (E0624),
     failing Rust lint, both test shards, WASM compile, and the
     Decision-cost perf gate simultaneously (the tell that it was a
     compile error, not a real test failure). Fixed by swapping to the
     existing public `iter_unchecked` (identical semantics, intended for
     exactly this classification/prediction use outside the engine
     crate) — commit `d62d02d80`. Verified locally with `cargo check`/
     `cargo clippy -D warnings` on the affected crates before pushing
     (Tilt wasn't running in this worktree).
  3. All CI green after `d62d02d80`; `matthewevans` approved against that
     commit and merged. **#5381 merged 2026-07-08.**

### [bug-fix] ~~Pact of Negation doesn't lose the game on unpaid deferred cost~~ — already fixed (GitHub #1058)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1058](https://github.com/phase-rs/phase/issues/1058)
- **Investigated 2026-07-07.** Round 1 planning misdiagnosed this as a
  parser AST-misattachment bug, but that diagnosis was built on a
  **paraphrased single-line version** of the Oracle text instead of the
  verbatim two-line text (`"Counter target spell.\nAt the beginning of
  your next upkeep..."` — the parser dispatches per-line via
  `split('\n')`, so joining the sentences routes to a different code
  path than the real card hits). Caught by independent plan review
  before any code was written — see `PIPELINE-LOG.md` standing lesson 8.
- **Round 2, using the correct verbatim text:** confirmed the parser
  already produces a correctly-nested AST (`LoseTheGame` properly nested
  inside `PayCost`'s `sub_ability`, via
  `try_parse_at_next_phase_delayed_trigger`, which already explicitly
  handles the Pact cycle by name). Pivoted to a full runtime
  `GameRunner` simulation (unpaid case → game-loss; paid case → no
  loss) and confirmed both directions already work correctly on
  current `main`. Found an existing regression test
  (`crates/engine/tests/integration/issue_3871_summoners_pact.rs`)
  covering the identical rider wording for Summoner's Pact, confirming
  this is a known, already-fixed parser class, not specific to Pact of
  Negation. No AI-specific gap found either — mana payment for a
  resolution-time cost is fully automatic (no interactive prompt either
  player could get stuck on).
- **Action taken:** commented on the GitHub issue. **Update:** the
  runtime claim (unpaid → lose, paid → no-lose) wasn't independently
  re-run at first, only the Summoner's Pact parser test was cited (which
  doesn't actually assert the rider nesting in dispute here) — closed
  that gap by writing and running two real `GameRunner` tests
  (`pact_of_negation_loses_the_game_when_upkeep_cost_goes_unpaid`,
  `pact_of_negation_does_not_lose_the_game_when_upkeep_cost_is_paid`,
  both pass), shipped as
  [phase-rs/phase#5351](https://github.com/phase-rs/phase/pull/5351).
  Comment updated accordingly. See `PIPELINE-LOG.md` standing lesson 11.

### [infra] Follow up on PR #5342 (verify-card-premise docs fix)

- **Status:** open
- **Source:** 2026-07-07, discovered while investigating Pact of
  Negation — the CLAUDE.md "Verify the card, not just the rule"
  principle and its matching `engine-planner` Step 0 hard gate had been
  committed to this fork's `main` only (commit `4f5c2e0c7`, explicitly
  marked "local-only, not for upstream PR" at the time), never to
  `origin/main`. Every fix worktree is cut fresh from `origin/main`, so
  that rule silently never reached any actual fix work, including
  tonight's — Pact of Negation round 1 planning paraphrased the Oracle
  text specifically because it never saw the hard gate's "verbatim,
  never a paraphrase" language.
- **Fix:** cherry-picked the doc-only commit onto a fresh branch off
  `origin/main` and opened
  [phase-rs/phase#5342](https://github.com/phase-rs/phase/pull/5342).
  Touches `.claude/skills/engine-planner/SKILL.md`, which per
  `.agents/pr-review-policy.toml` is excluded from the automated
  review/merge loop (same as #5304) — will need a maintainer to merge
  directly, will never auto-clear bot review.
- **Prompt:**
  > Check the status of phase-rs/phase PR #5342
  > (`gh pr view 5342 --repo phase-rs/phase`). If merged, mark this item
  > done. If still open with no activity after a week or so, post a
  > polite follow-up asking for a manual merge (same situation as #5304
  > above).

### [bug-fix] ~~Karn, the Great Creator's static doesn't stop opponents' artifact activations~~ — already fixed (GitHub #1080)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1080](https://github.com/phase-rs/phase/issues/1080);
  Karn is the centerpiece of Karn Shops, one of Vintage's current top
  archetypes.
- **Investigated 2026-07-07** by tracing the actual code on current `main`
  before touching anything, per this repo's "verify the card, not just the
  rule" policy — no worktree code changes were needed.
- **Findings:**
  1. `is_blocked_by_cant_be_activated` (`game/casting.rs`) evaluates
     `StaticMode::CantBeActivated`'s `TypeFilter::Artifact` against
     **live** `obj.card_types.core_types` at activation time, not a
     cached/ETB-time snapshot.
  2. `ContinuousModification::AddType` (`game/layers.rs:4861`) — the
     mechanism Liquimetal Coating uses to turn a permanent into an
     artifact — pushes directly into that same `core_types` field during
     the continuous-effects layer pass. A land turned into an artifact
     *after* Karn is already on the battlefield therefore feeds the
     identical live field Karn's static checks against — exactly the
     scenario this issue describes.
  3. This was generalized in `d1c99a805` ("prohibitions: widen
     CantBeActivated…"), which explicitly lists "Karn, the Great Creator
     (first static)" as one of the cards it unlocked, and is already an
     ancestor of current `main` (confirmed via `git merge-base
     --is-ancestor`).
  4. Two dedicated tests already cover this exact mechanism:
     `karn_blocks_opponent_artifact_activation` and
     `karn_permits_own_artifact_activation` in `game/casting_tests.rs`.
- **Action taken:** could not close the issue directly (insufficient
  GitHub permissions on `phase-rs/phase`); posted evidence as a comment
  instead ([issuecomment-4908412649](https://github.com/phase-rs/phase/issues/1080#issuecomment-4908412649))
  asking a maintainer to confirm and close. No PR needed for this item.

### [bug-fix] ~~Cityscape Leveler's Powerstone token is delayed and goes to the wrong controller~~ — already fixed (GitHub #1079)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1079](https://github.com/phase-rs/phase/issues/1079);
  sideboard/maindeck payoff in Vintage Karn Shops.
- **Investigated 2026-07-07** by tracing current `main` before touching
  anything.
- **Findings:** the generic "[verb] target permanent. Its controller
  creates a token" shape is a tested, general pattern, not per-card
  logic. `oracle_effect/tests.rs`
  (`effect_its_controller_creates_tokens_sets_parent_target_controller_owner`)
  confirms "Its controller creates two Map tokens" lowers
  `owner: TargetFilter::ParentTargetController` — the destroyed/exiled
  object's controller, not the source's. Immediacy is proven by a
  full-pipeline test on a structurally identical real card, Fractured
  Identity (`oracle_pipeline_snapshot_tests.rs`,
  `fractured_identity_each_player_other_than_controller_copies_exiled_permanent`):
  its second sentence becomes a `sub_ability`
  (`AbilityDefinition::sub_ability`, `types/ability.rs`) — a
  same-resolution continuation, never a new/delayed trigger. No
  card-specific code exists for Cityscape Leveler; it rides this
  already-correct general path.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.

### [bug-fix] ~~Expressive Iteration sends cards to the wrong zones~~ — already fixed (GitHub #1271)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1271](https://github.com/phase-rs/phase/issues/1271);
  played in Vintage Izzet fast-mana shells.
- **Investigated 2026-07-07.** `game/effects/mod.rs` contains a dedicated
  regression test, `expressive_iteration_dig_chain_reaches_library_bottom_and_exile`
  (citing issue #1162), using the exact card text, that drives the real
  parser + real resolver and asserts: card kept → Hand, card chosen for
  bottom → Library back, and the third, unchosen card → Exile with
  `CastingPermission::PlayFromExile` — precisely the correct (non-swapped)
  zone assignment. Source-level evidence directly contradicts the
  reported swap; a full `cargo test -p engine` run could not be completed
  in-session to get a live green confirmation, but the assertions are
  unambiguous.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.

### [bug-fix] ~~Endurance's ETB fizzles if killed in response~~ — already fixed (GitHub #1059)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1059](https://github.com/phase-rs/phase/issues/1059);
  free pitch-elemental graveyard hate/blocker played across
  Legacy/Vintage.
- **Investigated 2026-07-07.** The general CR 608.2a/b class ("a trigger
  whose source leaves the battlefield before it resolves must still
  resolve") is explicitly tested:
  `fabricate_e2e_source_gone_servo_branch_still_creates_tokens`
  (`database/synthesis.rs`) bounces the trigger's source mid-resolution
  and asserts the trigger is NOT removed. `resolve_ability_chain`
  (`game/effects/mod.rs`) has no source-existence gate. Endurance's
  simple "up to one target player" ETB rides this same generic path.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.

### [bug-fix] ~~Mother of Runes doesn't let you choose the protection color~~ — already fixed (GitHub #624)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#624](https://github.com/phase-rs/phase/issues/624);
  Middle-School/Premodern-era (Urza's Legacy) white-aggro staple, still
  played across Legacy/Premodern/Canadian-Highlander today.
- **Investigated 2026-07-07.** `crates/engine/tests/fixtures/integration_cards.json`
  and the golden `mother_of_runes_ir.snap` both show a real
  `Choose { choice_type: Color, persist: true }` step feeding
  `Protection: ChosenColor`. `game/effects/choose.rs` sets
  `WaitingFor::NamedChoice` for `ChoiceType::Color` — a genuine
  interactive prompt, not a fixed/random pick.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.

### [bug-fix] ~~Cards counting lands (Archaeomancer's Map, Land Tax, Knight of the White Orchid, Claim Jumper, Weathered Wayfarer)~~ — already fixed, stale duplicate (GitHub #1127)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1127](https://github.com/phase-rs/phase/issues/1127),
  surfaced via a fresh-issue sweep. Land Tax is old-border-era (Legends,
  1994); the rest are Vintage/Legacy legal.
- **Verified Oracle text** (Scryfall, all 5 cards): the shared clause is
  "if an opponent controls more lands than you" (Land Tax, Knight of the
  White Orchid, Claim Jumper — twice, for its repeat-gate too —
  Weathered Wayfarer's activation restriction) or "if that player
  controls more lands than you" (Archaeomancer's Map, event-scoped to
  the specific opponent whose land just entered).
- **Investigated 2026-07-07.** #1127 (filed 2026-05-26) is a stale,
  never-deduped duplicate of three separate, more specific issues, all
  since fixed and closed:
  1. **#2908** ("Weathered Wayfarer: activation restriction dropped,
     parser emits `condition:null`") — fixed by `e93dccdb3` (#3002,
     2026-06-11).
  2. **#1304** ("Keeper of the Accord not working — 'that player controls
     more creatures than you'") — fixed by `92feb876a` (#1432,
     2026-05-29), which wired the `ScopedPlayer`/trigger-condition path
     Archaeomancer's Map also needs.
  3. **Claim Jumper's "repeat this process once" clause** — fixed by
     `405151475` (#4030, 2026-06-21).
  All three commits are confirmed ancestors of current `main` (`git
  merge-base --is-ancestor`). Live-tested 7 regression tests covering
  all 5 cards' actual mechanisms — all pass:
  `test_opponent_controls_more_lands_than_you`,
  `claim_jumper_parses_repeat_once_while_opponent_lands`,
  `parses_activate_only_if_opponent_controls_more_lands_than_you`,
  `keeper_of_the_accord_creature_intervening_if_true_when_opponent_ahead`/
  `_false_when_tied` (the `ScopedPlayer` mechanism Archaeomancer's Map
  shares), plus 2 supporting parser tests.
- **Residual gap (not blocking, noted for future work):** no test
  currently pins `TriggerDefinition.condition` end-to-end for the
  *leading* "if an opponent/that player controls more X than you"
  ETB/phase-trigger form specifically (only the embedded repeat-gate and
  the activation-restriction form are directly covered) — a worthwhile
  test-coverage-only follow-up, not a functional gap.
- **Action taken:** posted evidence as a comment linking the 3 actual
  fixing PRs (no permission to close directly). No PR needed.

### [done] Land Grant's reveal-hand alternative cost — already fixed (GitHub #1098)

- **Status:** done — verified already fixed, no code change needed.
- **Source:** GitHub issue [phase-rs/phase#1098](https://github.com/phase-rs/phase/issues/1098)
  ("Alternative cost - show hand with no land cards - doesn't work"),
  surfaced via a fresh-issue sweep.
- **Verified Oracle text** (Scryfall): "If you have no land cards in hand,
  you may reveal your hand rather than pay this spell's mana cost. Search
  your library for a Forest card, reveal that card, put it into your hand,
  then shuffle." ({1}{G})
- **Investigated 2026-07-07.** Traced the full production chain: the
  parser already emits an `EffectCost(RevealHand)` casting option gated by
  a `Not(ZoneCoreTypeCardCountAtLeast{Hand, Land, 1})` condition (existing
  parser test `land_grant_reveal_hand_alternative_cost_option`), and
  `payable_spell_alternative_cost_details` → `restrictions::evaluate_condition`
  already handles that exact condition shape correctly (existing unit test
  `zone_core_type_card_count_condition_checks_hand_card_types`). The same
  mechanism class (conditional-gate alternative cost via
  `payable_spell_alternative_cost_details`) already has full runtime
  coverage for Ravenous Trap in `casting_tests.rs`. The one genuine gap was
  a runtime test for Land Grant's specific condition+cost combination.
  Added `land_grant_alt_cost_offered_with_no_lands_in_hand` and
  `land_grant_alt_cost_not_offered_with_land_in_hand`, driving the real
  `payable_spell_alternative_cost_details`/`can_cast_object_now`
  production seam. Full `game::casting::tests` module re-run clean: 655
  passed, 0 failed, 0 regressions.
- **PR:** [phase-rs/phase#5354](https://github.com/phase-rs/phase/pull/5354)
  (test-only, verified fresh off `origin/main` post-#5349).
- **Evidence posted:** comment on
  [#1098](https://github.com/phase-rs/phase/issues/1098#issuecomment-4910583632)
  (can't close directly — no repo permissions).

### [bug-fix] Scourglass's "except for artifacts and lands" exclusion was silently dropped — fix opened (GitHub #4710)

- **Status:** in progress — real fix implemented and PR opened, awaiting
  review/CI/merge.
- **Source:** GitHub issue [phase-rs/phase#4710](https://github.com/phase-rs/phase/issues/4710)
  ("[Card Bug] Scourglass" — actual: destroys all permanents; expected: any
  permanent except for artifacts and lands).
- **Verified Oracle text** (Scryfall): "{T}, Sacrifice this artifact: Destroy
  all permanents except for artifacts and lands. Activate only during your
  upkeep." ({3}{W}{W}, Artifact)
- **Root cause confirmed 2026-07-07** via a live scratch parse of the exact
  text: `parse_type_phrase_with_ctx` had no suffix grammar for "except for
  `<type-list>`" — only the predicate-based "except those that
  `<relative-clause>`" exclusion was recognized. The clause was silently
  dropped with zero parse warning, so `Effect::DestroyAll` resolved against
  the unfiltered `Permanent` population — an exact match for the report.
- **General class, not a one-card patch:** a live Scryfall search
  (`o:"except for" o:"destroy all"`) surfaced Elspeth Tirel's −5 ability
  ("Destroy all other permanents except for lands and tokens") sharing the
  identical grammar, with a heterogeneous type/property split (lands →
  `TypeFilter::Non`, tokens → `FilterProp::NonToken`). Both fixed by the
  same change. Mageta the Lion ("except for Mageta") and Slash the Ranks
  ("except for commanders") are explicitly out of scope — their exceptions
  name a specific permanent / a Commander-format designation, not a card
  type, and the fix includes a hostile-fixture guard proving it declines
  rather than mis-fires on those shapes.
- **Fix:** new `parse_except_for_type_list_suffix` in `oracle_target.rs`,
  reusing the existing `classify_negation` (already used by the
  "nonartifact, nonland" prefix-negation loop) and the existing
  Oxford-comma-tolerant `match_mass_union_separator` — no new
  `TargetFilter`/`TypeFilter`/`FilterProp` variant, no runtime change
  (`game/filter.rs`'s `TypeFilter::Non` already correctly treats artifact
  creatures as satisfying "artifact" per CR 205.2b). 6 new tests (parser
  suffix shape ×3 including the Mageta hostile fixture, full-ability-line
  parse ×2, runtime artifact-creature-exclusion ×1). Full engine test suite
  re-run clean: 15692 passed, 0 failed, 0 regressions.
- **PR:** [phase-rs/phase#5356](https://github.com/phase-rs/phase/pull/5356).
- **Evidence posted:** comment on
  [#4710](https://github.com/phase-rs/phase/issues/4710#issuecomment-4910984069).

### [bug-fix] Multi-card draws didn't offer Dredge (or any draw-replacement) independently per unit — fix opened

- **Status:** in progress — real fix implemented and PR opened, awaiting
  review/CI/merge.
- **Source:** reported directly by the user (not a GitHub issue): "Multiple
  times I tried to dredge the stinkweed imp. The time with bazaar drew no
  cards. Activated bazaar to dredge, [word unclear], and then it just
  asked me to discard three."
- **Verified Oracle text** (Scryfall): Bazaar of Baghdad "{T}: Draw two
  cards, then discard three cards." Stinkweed Imp "...Dredge 5 (If you
  would draw a card, you may mill five cards instead. If you do, return
  this card from your graveyard to your hand.)"
- **Root cause confirmed 2026-07-08**, CR 121.6b: "If an effect replaces a
  draw within a sequence of card draws, the replacement effect is
  completed before resuming the sequence." The engine treated a
  `Effect::Draw{count: N>1}` as ONE atomic replaceable event — accepting
  Dredge on a `count: 2` draw zeroed the entire count (both cards' worth),
  not just the one unit it replaced, yielding zero net cards drawn instead
  of one dredged + one normal. Matches the report exactly (Bazaar of
  Baghdad isn't in phase.rs's real Oracle-driven card set yet — only in
  the dormant, out-of-scope `mtgish-import` data — but the underlying
  engine bug is independent of that card's presence and is proven against
  Ancestral Vision, a real shipped `count: 3` draw card).
- **General class, not a one-card patch:** affects the cross-product of
  every multi-card-draw effect (Ancestral Vision, Concentrate-class
  spells, Windfall, Bazaar-class abilities once added) and every
  `ReplacementEvent::Draw` producer (Dredge — an entire card class across
  Vintage/Legacy, Notion Thief, Hullbreacher, and a count-doubling class
  like Teferi's Ageless Insight/Brainsurge).
- **Fix:** new `resume_multi_draw` in `game/effects/draw.rs`, looping one
  unit at a time through the existing replacement primitives instead of
  proposing the whole count as one event. A new `PendingMultiDraw{player,
  remaining, accumulated}` continuation (mirroring the zone-move batch
  machinery's proven re-pause contract) survives an arbitrary number of
  sequential per-unit pauses. `apply_draw_after_replacement` now returns
  the per-unit drawn count instead of writing `state.last_effect_count`
  directly, so a chained "discard that many" sees the TRUE total across
  the whole instruction (CR 609.3), not just the last unit processed. The
  new continuation is torn down via `replacement::abandon_post_replacement_continuation`
  (the single authority already used for `pending_connive_reentry` etc.,
  CR 800.4a) on player departure.
- **Explicitly out of scope, filed as a separate item above:** Connive N
  (N>1) — has a documented history of a previously-fixed collision
  between a shared generic mid-draw continuation and its own ordering
  requirements; reusing the new mechanism there risked reintroducing it.
- **Process note:** this fix went through 6 rounds of adversarial
  `/review-engine-plan`, each surfacing a real, previously-hidden issue
  (incomplete caller enumeration, an unaddressed count-doubling
  replacement class, a hand-waved resume function signature,
  `last_effect_count` corruption across loop iterations, the Connive
  collision risk, and the elimination-cleanup fix's correct location).
  During implementation, the first test run caught a genuine off-by-one in
  the remaining-count bookkeeping, fixed before commit — a reminder that
  even a heavily-reviewed plan still needs a real test run, not just
  compile success, before trusting it.
- **PR:** [phase-rs/phase#5360](https://github.com/phase-rs/phase/pull/5360)
  (15698 passed, 0 failed, 0 regressions; clippy clean).

### [bug-fix] Animate Dead / Dance of the Dead reanimation (GitHub #4767) — real bug, two compounding root causes, fixed

- **Status:** done — PR open, CI in progress
- **Source:** GitHub issue [phase-rs/phase#4767](https://github.com/phase-rs/phase/issues/4767),
  surfaced via the Scryfall-sets ∩ open-issues sweep for 1993-95-era cards.
- **Two compounding bugs, not one:** (1) the ETB reanimation effect text
  was never recognized by the parser at all (fell to `Unimplemented`/
  absorbed into the wrong clause); (2) a separate, previously-undiscovered
  prerequisite — the Aura could never successfully attach to its own
  graveyard-zone cast-time target in the first place, because two
  resolution-path checks (`ability_utils.rs::validate_targets_in_chain`'s
  generic fallback, `stack.rs`'s CR-annotated Aura-attach block) hardcoded
  "target must be on the battlefield" instead of consulting the Aura's own
  zone-scoped `Enchant` filter. Fixing only the parser bug would have
  changed nothing observable — the spell fizzled to the graveyard before
  the ETB trigger ever got a chance to exist.
- **Fix, three layers:** (1) runtime — new `TargetFilter::OriginalSource`
  variant (an ability's pre-`forward_result`-rebind source identity,
  concretized eagerly in-place at the one point pre-rebind `source_id` and
  the about-to-mutate sub-ability clone coexist), a companion
  `Keyword::Enchant(ParentTarget)`→`SpecificObject` concretization, a
  Sacrifice controller-scope fix so "that creature's controller sacrifices
  it" uses the creature's *current* controller, and a `parent_target_snapshot`
  fix (delayed-trigger infra) so the delayed sacrifice snapshots the
  reanimated creature, not the departing Aura; (2) parser — a new
  whole-body, fail-closed recognizer building the
  `ChangeZone→GenericEffect→Attach→CreateDelayedTrigger` chain directly,
  generalized over the class's verb/destination axis (Animate Dead's
  "return...to the battlefield" / Dance of the Dead's "put...onto the
  battlefield tapped"); (3) the initial-attach prerequisite, fixed
  generically (not just for this card) by routing both checks through the
  Aura's own `Enchant` filter via existing authorities
  (`aura_enchant_filter`, `sba::is_valid_attachment_target`) — this also
  fixes every other zone-scoped Enchant Aura (e.g. Spellweaver Volute).
- **Process note:** this went through an extraordinarily long
  plan→review loop (6 rounds on the runtime/`OriginalSource` architecture
  alone, then 4 more rounds on the parser composition after the runtime
  work was already implemented) — multiple rounds independently "confirmed
  correct" an `Attach{attachment: OriginalSource}` design nested directly
  under `ChangeZone` before a later round found, by direct hand-trace (not
  agent-reported), a dramatically simpler architecture: nesting the
  keyword-swap `GenericEffect` as `ChangeZone`'s direct sub-ability (where
  it legitimately needs `OriginalSource`) and leaving `Attach` one level
  deeper (as `GenericEffect`'s sub), where it's never rebound at all and
  plain `SelfRef`/`ParentTarget` just work — eliminating an entire class of
  runtime fixes the earlier rounds had converged on. The initial-attach
  prerequisite bug was found only because the implementation-executor
  insisted on driving the *real* cast pipeline rather than trusting the
  parser/runtime fixes' unit tests alone — a second reminder (after
  Underworld Breach) that "verify locally" via the real production path,
  not just isolated unit tests, is what actually catches compounding bugs.
- **PR:** [phase-rs/phase#5449](https://github.com/phase-rs/phase/pull/5449).

### [investigate] Necromancy — same reanimator-Aura family, different effect shape, NOT fixed by #5449

- **Status:** open, not started
- **Source:** GitHub issue [phase-rs/phase#640](https://github.com/phase-rs/phase/issues/640)
  ("Necromancy aura does nothing"), raised by the user while #4767 was in
  flight, asking whether the Animate Dead fix would cover it.
- **Confirmed it does not.** Necromancy's Oracle text is structurally
  different from Animate Dead/Dance of the Dead: it's cast as a plain
  Enchantment (no `Enchant` keyword, no pre-ETB Aura-ness), and its ETB
  trigger makes it *become* an Aura ("it becomes an Aura with 'enchant
  creature put onto the battlefield with Necromancy.'"), targeting a
  creature card as an ordinary spell target rather than via
  Enchant-keyword-restricted casting. This is the `Effect::ReturnAsAura`
  shape already built for Old-Growth Troll/Bronzehide Lion/Harold and Bob
  — a different building block than the `ChangeZone→GenericEffect→Attach→
  CreateDelayedTrigger` chain #5449 built.
- **Next step:** a separately-scoped fix reusing `Effect::ReturnAsAura` +
  the existing "becomes an Aura with quoted text" recognizer family
  (`oracle_nom/return_as_aura.rs`). Not started.

### [investigate] "Enchantment Auras are not going to graveyard if the permanent they were attached to is exiled" — could not reproduce with a minimal repro

- **Status:** investigated, inconclusive — needs a real repro
- **Source:** user-reported (recent bug report, not yet a filed GitHub
  issue as of this investigation — searched open issues, Discord-sourced
  issues, and closed issues for "aura"/"exile"/"graveyard" combinations,
  found nothing matching).
- **Investigated 2026-07-09:** wrote a direct unit test (Pacifism-shape
  Aura attached to a creature, creature moved to `Zone::Exile` via
  `zones::move_to_zone`, then `check_state_based_actions` called
  explicitly) mirroring the existing, passing
  `sba_aura_still_goes_to_graveyard_when_target_leaves` test (which covers
  the "creature dies" case). The exile case **passed** — the Aura
  correctly detached and went to its owner's graveyard (CR 704.5m) for
  this minimal scenario. `move_to_zone` is a single unified function for
  every zone destination (not separate graveyard-only vs exile-only
  plumbing), so there's no structural reason to expect exile specifically
  to behave differently from destroy/bounce — confirmed by this test.
- **Conclusion:** the reported symptom could not be reproduced at the SBA
  layer with a direct, minimal test. If real, the bug is likely
  scenario-specific (a particular card, a particular exile-triggering
  effect that doesn't route through the normal SBA-check cadence, a
  replacement effect interaction, or a UI-only display bug rather than a
  true engine-state bug) rather than a blanket "exile never triggers Aura
  cleanup" defect. **Needs a concrete repro (specific cards, steps) before
  further engine-side investigation is worthwhile** — do not assume this
  is fixed; also do not assume it's real without a repro.

### [feature] Tournament format shapes — multi-stage brackets (Swiss→cut, group→playoff, monthly async) + the cheap "Swiss + N rounds" affordance

- **Source:** 2026-09-05 design discussion while landing the tournament
  organizer (PR #8325 + protocol v6). Captured here so it survives past the
  session. Nothing implemented; this is scoping for when we loop back.
- **What the engine does TODAY** (verified in
  `crates/lobby-broker/src/tournament.rs`): `BracketShape` is `{ Swiss,
  SingleElimination }`, chosen **standalone** — they do NOT chain. A Swiss
  event runs auto-derived rounds (`default_total_rounds`: H2H Swiss = smallest
  `r` with `2^r ≥ max(players, 8)`) and ends on **final standings**, no
  playoff. An SE event is a standalone bracket (Appendix E 4–8 field, plus the
  degenerate 2/3-player finals). The word "cut" in the code only means the SE
  player-count range, not a Swiss→SE transition. The combined form was a
  deliberate v1 scope-out.

- **Already supported, do NOT build (only a UX shortcut is missing): "Swiss +
  N more full rounds"** (the community "Swiss plus one" — play the auto rounds
  plus one/more FULL rounds, champion by final standings, no cut). `total_rounds`
  is an override that "wins outright" and is **deliberately unbounded** at
  create-validation (`validation.rs`), so an organizer sets
  `CreateTournament.total_rounds` = (auto default) + N and the engine pairs that
  many full Swiss rounds. It fits the existing single-stage Swiss model.
  **Cheap frontend follow-up (do this one first, it's tiny):** an "Automatic +
  N" affordance — a control (or an optional `plus_rounds` wire field) that
  tracks the live default and adds N, so the organizer doesn't have to know the
  default and type an absolute number.

- **Deferred multi-stage work (the real feature), easiest → hardest:**
  1. **Swiss → cut to Top-X (single-elim).** ~1.5× one tournament PR. Fully
     SYNCHRONOUS — reuses the round state machine and BOTH pairing builders
     (`build_swiss_round`, `build_single_elimination_round`) unchanged. New:
     (a) single-stage → two-stage meta (`current_stage`, pairings tagged by
     stage), (b) the cut + SE seeding (freeze Swiss standings → top X → seed
     1v8/2v7…). "Swiss plus one" as a top-2 SE final is just X=2 here.
  2. **Group (round-robin) → SE playoff, synchronous.** Adds a `RoundRobin`
     builder + group partitioning; still synchronous.
  3. **Monthly async groups → playoff.** ~2–3×. The group stage is
     ASYNC/time-windowed (all group matches open at once, ~3-week deadline,
     report in any order, continuous standings) — a NEW progression mode the
     round-synchronized engine lacks — plus multi-week persistence. Rides the
     protocol-v6 expiring/rotating credentials directly (tokens survive/renew
     across the window). Do NOT fake round-robin as N−1 synchronized rounds —
     that breaks the "play your matches whenever in 3 weeks" UX; model it as a
     flat open match pool with a deadline.

- **Recommended architecture:** model a tournament as ordered stages, each
  declaring TWO axes — *progression mode* (`SynchronizedRounds |
  OpenPoolWithDeadline`) and *bracket* (`RoundRobin | Swiss |
  SingleElimination`) — with a cut rule between stages. One primitive covers
  Swiss→Top8, groups→knockout, and the monthly async format (build-for-the-
  class, avoids per-format special cases). Each stage transition / cut is a
  broker-owned state change and fits the v6 `open_actions` / `report_gate`
  affordance model already added.
- **Suggested order when we return:** the "Automatic + N rounds" affordance
  first (tiny, frontend-only), then Swiss→cut-to-Top-X as the next tournament
  PR, then the group/async shapes.
