# ROUND-5 REVISED Implementation Plan: `TriggerMode::Blocks` silently drops "or becomes blocked by [filter]"

**Worktree for implementation:** `C:\git\phase\.claude\worktrees\card-blocks-or-becomes-blocked-by-filter` (branch `worktree-card-blocks-or-becomes-blocked-by-filter`, cut from `origin/main` @ `b0fa2d3a4`)

All file:line citations below were re-verified directly against that worktree's current source during this round (not carried forward blindly from prior rounds). Where a citation matches a prior round's number, it is confirmed unchanged; where it drifted, the corrected number is used.

---

## Step 0 — Card-text verification (hard gate)

Fetched live from Scryfall (`api.scryfall.com/cards/named?exact=...`) this round, via curl with a descriptive User-Agent (Scryfall 403s bare WebFetch):

| Card | Verified Oracle text |
|---|---|
| **High-Rise Sawjack** | "Reach (This creature can block creatures with flying.)\nWhenever **this creature** blocks a creature with flying, this creature gets **+2/+0** until end of turn." |
| **Goblin Cadets** | "Whenever this creature blocks or becomes blocked, target opponent gains control of it. (This removes this creature from combat.)" |
| **Nascent Metamorph** | "Whenever this creature attacks or blocks, target opponent reveals cards from the top of their library until they reveal a creature card. …" |
| **Vraska's Conquistador** | "Whenever this creature attacks or blocks, if you control a Vraska planeswalker, target opponent loses 2 life and you gain 2 life." |
| **Karn, Silver Golem** | "Whenever Karn blocks or becomes blocked, it gets **-4/+4** until end of turn.\n{1}: Target noncreature artifact becomes an artifact creature…" |
| **Quagmire Lamprey** | "Whenever this creature becomes blocked by a creature, put a -1/-1 counter on that creature." |
| **Mammoth Harness** | "Enchant creature\nEnchanted creature loses flying.\nWhenever enchanted creature blocks or becomes blocked by a creature, the other creature gains first strike until end of turn." |
| **Venom** | "Enchant creature\nWhenever enchanted creature blocks or becomes blocked by a non-Wall creature, destroy the other creature at end of combat." |
| **She-Hulk, Wallbreaker** | "Trample\nOther Heroes you control have trample.\nWhenever a Hero you control becomes blocked, put a +1/+1 counter on that Hero for each creature blocking it." |

**Correction locked in (finding #1):** High-Rise Sawjack is **"this creature"** (self-referential, not the card's own name) and **+2/+0** (not +3/+0). Every reference and test body below uses the corrected text. Card-database storage note: the game's own card DB substitutes the literal card name for "this creature" in self-referential subjects (confirmed by the existing Karn test using "Karn, Silver Golem" verbatim for "Karn"), so `parse_trigger_line` test bodies below use the same convention as existing tests in the file (literal name substituted for "this/that creature").

**She-Hulk, Wallbreaker note:** its trigger is the **bare** `BecomesBlocked` form (no "by a creature" qualifier — `valid_target` stays `None`), so it is unaffected by every per-blocker code path this plan touches. It is not in scope for any behavior change; it is cited only as a safety-net check for finding #3 below.

---

## Step 1 — Applicable skills

- `/add-trigger` — new `TriggerMode` variant, matcher registry, event key indexing.
- `/oracle-parser` — nom combinator dispatch fix at the root-cause site; new filter-capture helper.
- `/add-engine-variant` — gate for `TriggerMode::BlocksOrBecomesBlocked` and `GameEvent::AttackerBecameBlockedByFilteredBlocker`.
- `/card-test` — the Venom `apply()`-level integration test.

`cargo engine-inventory` grep performed (manually, via direct source grep since the generated inventory file is gitignored and not present in this fresh worktree) — confirmed no existing `TriggerMode`/`GameEvent` variant already covers this compound-trigger-with-disambiguated-blocker shape; the sibling-cluster check (`Blocks`/`BecomesBlocked`/`AttacksOrBlocks` already exist as parameterized compound siblings, e.g. `AttacksOrBlocks` unifies `Attacks`+`Blocks`) confirms `BlocksOrBecomesBlocked` is the correct, minimal extension of an *already-established* parameterization axis (2-way compound trigger modes), not a new axis.

---

## Step 2 — Analogous trace (hard gate)

Traced `TriggerMode::AttacksOrBlocks` end-to-end as the closest existing compound-trigger sibling:

1. **Parser dispatch** — `crates/engine/src/parser/oracle_trigger.rs:8322-8331`: `tag("attacks or blocks").parse(rest).is_ok()` → `def.mode = TriggerMode::AttacksOrBlocks`.
2. **Type definition** — `crates/engine/src/types/triggers.rs:542`: `AttacksOrBlocks` variant in the "Compound triggers" section (line 538-546); `FromStr` arm at line 651; `Display` derives automatically; string list entry at line 884.
3. **Matcher definition** — `crates/engine/src/game/trigger_matchers.rs:1786-1797` (`match_attacks_or_blocks`, dispatches `AttackersDeclared → match_attacks`, `BlockersDeclared → match_blocks`).
4. **Matcher registration (two sites)** — `trigger_matcher()` function definition at `game/trigger_matchers.rs:18` (arm at line 142: `TriggerMode::AttacksOrBlocks => match_attacks_or_blocks`) and `build_trigger_registry()` at `game/trigger_matchers.rs:225` (insert at line 424).
5. **Per-instance event dispatch** — `crates/engine/src/game/triggers.rs:768` (the **call site**: `if let Some(matcher) = trigger_matcher(trig_def.mode.clone())`) and the batch-construction `else if` chain at `triggers.rs:825-875`, where `AttacksOrBlocks` deliberately takes **no** narrowing arm (falls to the generic `vec![vec![event.clone()]]` at line 873-874) because its shipping cards (Nascent Metamorph, Vraska's Conquistador) never reference "that creature"/"the other creature."
6. **Exhaustive TriggerMode matches** — `analysis/ability_graph.rs::trigger_axis` (line 1039, `AttacksOrBlocks` grouped into the giant `None` arm at line 1218/1227) and `game/trigger_index.rs::keys_from_trigger_def` (line 106, `AttacksOrBlocks` gets its **own** dedicated arm at line 424-427 pushing **two** keys: `Attacks` and `Blocks`, because its underlying events span two different axes).

**Why `BlocksOrBecomesBlocked` diverges from this trace at step 5:** unlike `AttacksOrBlocks`, its shipping cards (Venom, Mammoth Harness) **do** reference a per-firing antecedent ("the other creature"), so it needs the same per-instance narrowing arm that `Blocks` (`triggers.rs:844-848`) and `BecomesBlocked` (`triggers.rs:849-855`) already have — confirmed by tracing those two arms directly (see Step 5 detail below). This is not extra complexity invented for this plan; it is required because the class of cards using the compound mode is a superset of the classes using the two atomic modes.

---

## Step 3 — Files read in full before proposing changes

`crates/engine/src/parser/oracle_trigger.rs` (root-cause site, `AttacksOrBlocks`/`Blocks`/`BecomesBlocked` parsing, `parse_becomes_blocked_by_filter`, `lower_trigger_ir`, `mode_carries_event_source_object`/lift pass), `crates/engine/src/types/triggers.rs` (full `TriggerMode` enum + `FromStr` + tests), `crates/engine/src/game/trigger_matchers.rs` (`matching_block_events`, `matching_becomes_blocked_events`, `match_attacks_or_blocks`, `trigger_matcher()`, `build_trigger_registry()`), `crates/engine/src/game/triggers.rs` (lines 768-890, the per-instance dispatch), `crates/engine/src/game/targeting.rs` (`blocked_attacker_from_event`, `extract_source_from_event`, `resolve_event_context_target_for_event_or_state`'s `ParentTarget`/`TriggeringSource` arms), `crates/engine/src/parser/oracle_target.rs` (`parse_target_with_syntax`'s definite-anaphor block, `parse_event_context_ref`, `parse_type_phrase`/`parse_type_phrase_with_ctx`), `crates/engine/src/parser/oracle_effect/subject.rs` (`parse_subject_application`'s "that "/pronoun handling), `crates/engine/src/parser/oracle_effect/counter.rs` (`resolve_counter_target`, `resolve_that_creature_in_trigger`), `crates/engine/src/types/events.rs` (`AttackerBecameBlockedByEffect` definition), `crates/engine/src/game/log.rs`, `crates/engine/src/game/public_state.rs`, `crates/engine/src/game/trigger_index.rs`, `crates/engine/src/analysis/ability_graph.rs`, `crates/engine/src/database/synthesis.rs` (Flanking's synthesized `BecomesBlocked` trigger), `crates/engine/src/parser/oracle_trigger_tests.rs` (Quagmire/Karn/Acolyte-adjacent tests), `crates/engine/tests/integration/rules/combat.rs`, `crates/engine/tests/integration/std_longtail_b_delayed_effects.rs`, `crates/engine/tests/dazzling_beauty_become_blocked.rs`.

Additionally, **two targeted `cargo test -p engine` runs were executed in this isolated worktree** (its own `target/`, no shared `CARGO_TARGET_DIR`, no Tilt watching this path — confirmed via `.cargo/config.toml` and `git worktree list`) to empirically ground design decision #3, since the premise carried across 4 rounds needed independent verification per this project's "verify the card, not just the rule" doctrine extended to "verify the runtime claim, not just the trace":

- `trigger_becomes_blocked_by_a_creature_sets_blocker_filter` (parser-only) — **passes today**, confirms the parser already captures Quagmire Lamprey's blocker filter correctly.
- `rules::combat::becomes_blocked_by_creature_fires_for_each_blocker` (Acolyte of the Inferno, full `apply()`-level integration test using `DealDamage` to "that creature") — **passes today**.

That second result initially looked like it *refuted* the premise (if Acolyte's `DealDamage`-to-"that creature" already resolves correctly, does Quagmire's `PutCounter`-to-"that creature" also already work?). Tracing why resolved the discrepancy exactly — see Step 4 / finding #3 below. This is the single most important correction this round makes over rounds 1-4.

---

## Step 4 — Architectural questions

### Pattern Coverage

- **Root-cause fix** (compound trigger mode): the ~2-card `BlocksOrBecomesBlocked`-with-filter class (Venom, Mammoth Harness) plus the no-filter class already partially working via `Blocks` misclassification (Karn Silver Golem, Goblin Cadets) — Karn's own test already exists, proving this is a real, previously-miscategorized-but-parsing class, not a 1-card fix.
- **`parse_blocks_a_filter` fix** (plain `Blocks` mode filter capture): every "`~` blocks a `<filter>` creature" card (High-Rise Sawjack is one; Wall of Frost's "blocks a creature" is filter-less so unaffected; this covers the general "blocks a `<type/quality>` creature" grammatical class, mirroring the ~29-card class the existing `parse_becomes_blocked_by_filter` regression-guard comment already documents for the `BecomesBlocked` side).
- **`TargetFilter::Player`-exclusion guard**: applies to every card whose trigger body is lowered via `lower_trigger_ir` (the general IR-lowering path) AND contains a bare bodiless "target opponent"/"target player" reference AND uses `Blocks`/`BecomesBlocked`/`AttacksOrBlocks`/`BlocksOrBecomesBlocked` as its mode — confirmed as a real, general collision (not a one-card patch) by tracing the exact assignment site (`oracle_trigger.rs:1429-1446`, generic across all modes) against 4 independently-found real cards (Goblin Cadets, Nascent Metamorph, Vraska's Conquistador, plus the general Flanking/Quagmire-class check below).
- **Decision-#3 fix** (`blocked_attacker_from_event`'s ParentTarget resolution for per-blocker events): applies specifically to the class of cards whose per-blocker `Blocks`/`BecomesBlocked`/`BlocksOrBecomesBlocked` effect body resolves its "that creature"/"the other creature" subject through **`ParentTarget`** rather than `TriggeringSource` — see the precise sub-class identification below (this is *narrower* than round 4 assumed, and the correction matters).

### Building Blocks

- `parse_type_phrase` (`oracle_target.rs:1841`, delegating to `parse_type_phrase_with_ctx`) — reused by the new `parse_blocks_a_filter` helper, mirroring `parse_becomes_blocked_by_filter` (`oracle_trigger.rs:9164-9170`) exactly.
- `target_filter_matches_object(state, object_id, filter, source_id)` — already used by `matching_becomes_blocked_events`'s blocker-side check (`trigger_matchers.rs:3384`); reused unchanged for `matching_block_events`'s new attacker-side check.
- `TriggerDefinition` builder methods (`.valid_card()`, `.valid_target()`, `.execute()`) — used identically to how `database/synthesis.rs`'s Flanking trigger is built, for citation/consistency, not for new construction (Flanking is not modified by this plan).
- `DelayedTriggerCondition::AtNextPhase { phase: Phase::EndCombat }` — the exact existing building block Venom's "destroy … at end of combat" clause composes onto, proven live and tested via `fortune_schedules_end_of_combat_delayed_trigger` (`crates/engine/tests/integration/std_longtail_b_delayed_effects.rs:126-167`).
- `Effect::Destroy { target: TargetFilter, cant_regenerate: bool }` (`types/ability.rs:9157-9163`) — reused unchanged for Venom.
- `ContinuousModification::AddKeyword { keyword }` (the "gets +N/+M and has flying"-family building block CLAUDE.md's table documents) — reused unchanged for Mammoth Harness's first-strike grant.

### Logic Placement

| Concern | Layer | Justification |
|---|---|---|
| "blocks or becomes blocked" dispatch (root cause) | Parser (`oracle_trigger.rs`) | Grammar recognition — belongs with every other trigger-mode dispatch arm. |
| "blocks a `<filter>`" capture | Parser (`oracle_trigger.rs`, new `parse_blocks_a_filter`) | Mirrors the existing `BecomesBlocked`-side filter capture; same layer. |
| Blocker/attacker disambiguation for "that creature"/"the other creature" | Runtime (`game/targeting.rs`) | This is CR 608.2c anaphora resolution against *live game state* (which object is currently the blocker vs. attacker for *this* firing) — cannot be resolved at parse time. |
| New `GameEvent` variant + its narrowing | Runtime (`game/trigger_matchers.rs`, `types/events.rs`) | Event-shape disambiguation is inherently a runtime/event-system concern. |
| `Player`-exclusion guard | Runtime matchers (`matching_block_events`, `matching_becomes_blocked_events`) | The collision is a runtime field-reuse artifact of `lower_trigger_ir`, not a parse-time concept; guarding at the consumption site is the single-authority fix (no parser change needed — `lower_trigger_ir`'s behavior is correct and general-purpose for its own concern, effect-target surfacing; it doesn't know a filter check runs against the same field for a different mode). |
| "the other creature" anaphor | Parser, two sites (generic object-position `parse_target_with_syntax`, and generic subject-position `parse_subject_application`) | Both are the existing, single, generic dispatch points every other definite-anaphor phrase ("the creature", "that creature", "it") already uses — extending them, not adding a third parallel path. |

### Rust Idioms

- `GameEvent::AttackerBecameBlockedByFilteredBlocker { attacker: ObjectId, blocker: ObjectId }` — a struct-variant carrying **both** ids explicitly, eliminating the ambiguous-inference problem `blocked_attacker_from_event`'s current fallback branch has (inferring orientation from assignment shape). This is more idiomatic than patching the inference logic: the event becomes unambiguous *by construction*, and every consumer becomes a trivial one-line match arm instead of conditional logic.
- `TriggerMode::BlocksOrBecomesBlocked` slots into the existing "Compound triggers" enum section (`types/triggers.rs:538-546`) alongside `AttacksOrBlocks`/`EntersOrAttacks`/`EntersOrHauntedCreatureDies` — extending an established parameterization axis, not creating a new one (passes `/add-engine-variant`'s sibling-cluster check because it *is* the established 2-way-compound-trigger pattern, applied to the one remaining un-compounded pair CR 509 defines).
- Exhaustive matches (`trigger_axis`, `keys_from_trigger_def`, `TriggerMode::from_str`, `trigger_matcher()`, `build_trigger_registry()`) all get explicit new arms — no wildcards introduced anywhere.

### Nom Compliance

Root-cause fix replaces the bare `tag("blocks").parse(rest).is_ok()` (which discards `rest`) with a proper `alt()` dispatch that **consumes and inspects the remainder**: first try `tag("blocks or becomes blocked")` (compound — this is the *existing* pattern already used for `AttacksOrBlocks` at line 8322-8331, applied here), THEN fall back to bare `tag("blocks")` **plus** run the new `parse_blocks_a_filter` combinator against whatever remainder follows, storing it into `def.valid_target`. No `contains`/`starts_with`/`find` introduced. `parse_blocks_a_filter` is a direct structural mirror of `parse_becomes_blocked_by_filter` (`oracle_trigger.rs:9164-9170`), itself pure nom (`alt((tag(" by a "), tag(" by an ")))` → `parse_type_phrase`).

"the other creature" is added as two new `value(TargetFilter::ParentTarget, tag("the other creature"))` nom arms (see Building Blocks/anaphor section below) — no string matching.

### Extension vs Creation

Every change extends an existing, already-established pattern:
- `BlocksOrBecomesBlocked` extends the compound-trigger-mode pattern (`AttacksOrBlocks` sibling).
- `AttackerBecameBlockedByFilteredBlocker` extends the "synthetic narrowed combat event" pattern (`AttackerBecameBlockedByEffect` sibling).
- `parse_blocks_a_filter` extends the filter-capture pattern (`parse_becomes_blocked_by_filter` sibling).
- The Player-exclusion guard extends existing filter-presence checks (`trigger.valid_target.is_some()`) with one additional exclusion condition, not a new mechanism.
- "the other creature" extends the existing definite-anaphor `alt()` blocks in `oracle_target.rs` and `subject.rs` with two new sibling arms.

No new architecture is introduced anywhere in this plan.

### Variant Discoverability

Manual grep-based inventory check performed (see Step 1) in lieu of `cargo engine-inventory` (gitignored, not present, and per CLAUDE.md must be regenerated locally — out of scope to run inside a planning-only task; the implementer must run `cargo engine-inventory` and re-confirm before implementation per the `/add-engine-variant` gate). No existing `TriggerMode` or `GameEvent` variant duplicates or should-be-parameterized-instead-of this proposal.

---

## Design Decision #3 — RESOLVED: (b), with a corrected and narrower scope than round 4 assumed

**Decision: remove the mode-gate. Gate the new event's emission on `per_blocker` (filter presence) alone, and add Quagmire Lamprey to explicit in-scope with its own regression test.**

**But the justification is more precise than round 4's, because of the empirical test run in Step 3.** Tracing the full resolution path for "that creature" reveals **two independent, inconsistent resolvers** for the exact same CR 608.2c anaphor, at two different call sites:

1. **`oracle_effect/subject.rs::parse_subject_application`** (lines 2540-2576) — used by `Effect::DealDamage` (and most other effect subject positions). Its gate is `if ctx.subject.is_some()` — **no SelfRef exclusion** — so for a self-referential subject ("Whenever `~` becomes blocked by a creature…"), it *still* returns `TargetFilter::TriggeringSource`. `TriggeringSource` resolves via `extract_source_from_event` (`targeting.rs:1284`), whose `BlockersDeclared` arm (~line 1330) returns the **first blocker** in the (already narrowed, single-assignment) event unconditionally. **This is already correct today** — which is exactly why the empirical test (`becomes_blocked_by_creature_fires_for_each_blocker`, Acolyte of the Inferno, a `DealDamage`-shaped effect) passes on `origin/main` right now.

2. **`oracle_effect/counter.rs::resolve_counter_target`** (lines 920-935), via `resolve_that_creature_in_trigger` (lines 945-955) — used specifically by `PutCounter`/counter-placement effects. Its gate is `Some(subject) if !matches!(subject, SelfRef | Any)` — **SelfRef is explicitly excluded**. For a self-referential subject, this returns `None`, so `resolve_counter_target` falls through to the generic `parse_target(text)`, which (per the documented lift-pass gating at `oracle_trigger.rs:1525-1598`, whose `mode_carries_event_source_object` list at lines 1568-1587 does **not** include `Blocks`/`BecomesBlocked`) yields `TargetFilter::ParentTarget`, uncorrected. `ParentTarget` resolves via `blocked_attacker_from_event` (`targeting.rs:1160-1190`), whose **second branch** (the `BecomesBlocked`-orientation fallback, lines 1181-1189) returns the sole **attacker** in the narrowed single-assignment event — which, for a per-blocker `BecomesBlocked` trigger, **is the trigger's own source**. **This is the real, confirmed, currently-shipping bug**, and it hits *exactly* Quagmire Lamprey and every other card in the documented "~29 plain 'by a creature' cards" regression class (`oracle_trigger_tests.rs:6546-6551` names Quagmire Lamprey, Order of the Alabaster Host, Cave Tiger) **whose effect is specifically a counter-placement** ("put a -1/-1 counter on that creature" / "+1/+1 counter" etc.) — not the whole class unconditionally, since cards in that class using `DealDamage`/`Pump`/other effect shapes already resolve correctly via path (1).

**Why fix it in `targeting.rs` rather than reconciling `counter.rs`'s gate with `subject.rs`'s:** `blocked_attacker_from_event`'s ParentTarget path is reached by *any* future or existing effect-subject parser that keeps the (arguably more conservative) SelfRef-exclusive gate — reconciling only `counter.rs` would leave the same landmine for the next effect-specific resolver copy. Fixing the shared runtime resolution function fixes it for every current and future caller of `ParentTarget` in this shape, with **strictly less code** than patching N per-effect parser gates, and with **zero regression risk to path (1)** since path (1) never touches `ParentTarget`/`blocked_attacker_from_event` for this trigger shape at all — the two resolution paths are structurally disjoint today (SelfRef gate presence/absence), so fixing one cannot regress the other.

**Safety-net re-verification for extending scope to all `per_blocker=true` firings regardless of mode:**
- She-Hulk, Wallbreaker (the only other named "observer, per-blocker-shaped-sounding" card checked this round) is **bare** `BecomesBlocked` (`per_blocker = false` — no "by a creature" qualifier at all), so it is structurally untouched by this fix regardless of mode-gating. Confirmed by its verified Oracle text in Step 0.
- Flanking's synthesized trigger (`database/synthesis.rs:5197-5209`) is built directly via `TriggerDefinition::new(...).execute(...)` with an explicit `target: TargetFilter::TriggeringSource` (`is_flanking_trigger`'s check at line 5227) — it **never** goes through the `ParentTarget` path this fix touches, so it is unaffected.
- No other currently-shipping card's parse path was found routing a per-blocker filtered `BecomesBlocked`/`Blocks` effect through `ParentTarget` other than the counter-effect class already named in the existing regression-guard comment.

**Net effect of decision (b):** removing the mode-gate and fixing `blocked_attacker_from_event` directly (see Step 5, "New leading arm") is *safe*, fixes the ~29-card counter-effect class (Quagmire Lamprey representative) as a documented, in-scope regression fix, and requires no additional gating code beyond what the compound-mode work already needs.

---

## Step 4b — Design Decision #4 — Complete `GameEvent::AttackerBecameBlockedByFilteredBlocker` consumption footprint

Grepped `AttackerBecameBlockedByEffect`'s **complete** real usage (not a guessed subset) across the whole crate. Its footprint, and the corresponding required treatment for the new variant:

| Site | `AttackerBecameBlockedByEffect`'s treatment | New variant's required treatment |
|---|---|---|
| `types/events.rs:545-547` (definition) | struct variant `{ attacker: ObjectId }` | **New sibling definition**: `AttackerBecameBlockedByFilteredBlocker { attacker: ObjectId, blocker: ObjectId }`, placed adjacent, CR 509.3d doc comment. |
| `game/trigger_matchers.rs:927` (a wildcard-free "no trigger subject" grouping, comment: "Mirrors BlockersDeclared: the 'becomes blocked' trigger uses the dedicated matcher, not this generic per-object count helper") | grouped, no-op | **Add to the same group** — this new event is likewise handled by the dedicated `matching_becomes_blocked_events`/`matching_blocks_or_becomes_blocked_events` matchers, not this generic helper. |
| `game/trigger_matchers.rs:3343` (`matching_becomes_blocked_events`'s own first match arm) | own arm, effect-driven-block handling | **N/A — this is the arm that emits the OLD effect-driven event; unrelated to the new event**, which is emitted from the *second* (per-blocker `BlockersDeclared`) branch of the same function. No change to this specific arm. |
| `game/trigger_matchers.rs:4690` (unit test) | test fixture | New unit test(s) constructing the new event directly (see Verification Matrix). |
| `game/trigger_index.rs:599` (`GameEvent::AttackerBecameBlockedByEffect { .. } => push(TriggerEventKey::Blocks)`) | pushes `Blocks` key | **New sibling arm**: `GameEvent::AttackerBecameBlockedByFilteredBlocker { .. } => push(TriggerEventKey::Blocks)`. |
| `game/targeting.rs:1166` (`blocked_attacker_from_event`'s first arm) | returns `attacker` | **New leading arm, inserted before this one**: `GameEvent::AttackerBecameBlockedByFilteredBlocker { blocker, .. } => return Some(*blocker)` — this is the actual bug fix (see below). |
| `game/targeting.rs:1337` (`extract_source_from_event`'s arm) | returns `attacker` | **New arm — this is the site round 4 missed entirely.** Add: `GameEvent::AttackerBecameBlockedByFilteredBlocker { blocker, .. } => Some(*blocker)`. Required because the per-blocker branch of `matching_becomes_blocked_events` currently emits generic `BlockersDeclared{assignments:[(blocker,attacker)]}`, which `extract_source_from_event`'s existing generic `BlockersDeclared` arm (~line 1330) *already* resolves correctly (returns first blocker) for any `TriggeringSource`-routed "that creature"/"it" reference (path (1) above, e.g. Acolyte-of-the-Inferno-shaped cards). **Once the per-blocker branch is changed to emit the new event type instead of `BlockersDeclared`, that existing generic arm no longer sees these events at all** — without a new `extract_source_from_event` arm, every currently-working `TriggeringSource`-routed per-blocker `BecomesBlocked`/`Blocks` card (i.e., every non-counter-effect card in the "~29-card" class, such as Acolyte of the Inferno) would **regress**. This is a hard correctness requirement of switching the event type, not an optional nice-to-have. |
| `game/public_state.rs:421` (wildcard-free "no display-field impact" group, lines 401-439) | grouped, no-op | **Add to the same group** — the new event changes no `derive_display_state`-computed field (same reasoning as its sibling). |
| `game/log.rs:116` (`categorize`, Combat group, lines 114-119) | grouped under `LogCategory::Combat` | **Add to the same group.** |
| `game/log.rs:604-606` (`format_segments`) | `vec![card_seg(state, *attacker), text(" becomes blocked")]` | **New sibling arm**: `GameEvent::AttackerBecameBlockedByFilteredBlocker { attacker, blocker } => vec![card_seg(state, *blocker), text(" blocks "), card_seg(state, *attacker)]` (mirrors `BlockersDeclared`'s per-assignment phrasing at lines 592-598, since this event *is* a disambiguated single blocker/attacker pair). |
| `game/log.rs:26-40` (`should_exclude_event`) | **absent** (wildcard `_ => false`) | **No change** — confirmed `AttackerBecameBlockedByEffect` is not listed here either; the new variant correctly falls through the same wildcard to "not excluded," which is the desired default (log it, don't hide it). |
| `game/effects/become_blocked.rs` | doc-comment cross-references and its own unit tests for the *effect-driven* block path | **No change** — this file implements `Effect::BecomeBlocked` (Dazzling Beauty's mechanic), which emits `AttackerBecameBlockedByEffect`, not the new event. Unrelated. |

**`targeting.rs:1160-1190` (`blocked_attacker_from_event`) — the actual fix, spelled out:**

```rust
fn blocked_attacker_from_event(
    event: &crate::types::events::GameEvent,
    source_id: ObjectId,
) -> Option<ObjectId> {
    // CR 509.3d: a per-blocker `BecomesBlocked`/`Blocks`/`BlocksOrBecomesBlocked`
    // firing carries an unambiguous (attacker, blocker) pair — no orientation
    // inference needed or possible to get wrong.
    if let crate::types::events::GameEvent::AttackerBecameBlockedByFilteredBlocker { blocker, .. } = event {
        return Some(*blocker);
    }
    // CR 509.3c: an effect-driven "becomes blocked" carries only the attacker...
    if let crate::types::events::GameEvent::AttackerBecameBlockedByEffect { attacker } = event {
        return Some(*attacker);
    }
    // ...(existing BlockersDeclared branches UNCHANGED below — still correct for
    // Blocks-mode's blocker-side firing, and remain as a fallback for any
    // residual bare/multi-assignment BlockersDeclared case that never routes
    // through the new event type)
    ...
}
```

**Round-2's "no in-scope card uses 'it' on a filtered BecomesBlocked trigger" — re-verified, still holds, scope now explicit:** Quagmire Lamprey's verified text (Step 0) uses "that creature," not "it." No card added to scope by this round's plan uses "it" on a filtered `BecomesBlocked`/`BlocksOrBecomesBlocked` trigger. (Karn Silver Golem's "it" refers to itself on a **filter-less** compound trigger — routed via the ordinary `SelfRef`-subject bare-pronoun path, untouched by this plan.)

---

## Step 4c — `TargetFilter::Player`-exclusion guard: root cause, confirmed by direct trace

`oracle_trigger.rs::lower_trigger_ir`, lines 1429-1446:

```rust
// CR 109.4 + CR 603.7c: Surface TargetFilter::Player when execute
// references ControllerRef::TargetPlayer, when the effect text names a
// target opponent/player ...
if def.valid_target.is_none() {
    let effect_lower = modifiers.effect_lower.as_str();
    if scan_contains(effect_lower, "target opponent") || scan_contains(effect_lower, "target player") {
        def.valid_target = Some(TargetFilter::Player);
    } else if ... { def.valid_target = Some(TargetFilter::Player); }
}
```

This runs for **every** trigger mode lowered through the general IR path whenever `valid_target` is still `None` and the effect body mentions "target opponent"/"target player" — it is not specific to combat modes. For **Goblin Cadets** ("blocks or becomes blocked, **target opponent** gains control of it" — bare compound, no CR 509 blocker qualifier at all), this sets `def.valid_target = Some(TargetFilter::Player)`, purely because the *effect* targets an opponent — completely unrelated to any CR 509.3d blocker filter. The same mechanism fires for **Nascent Metamorph** and **Vraska's Conquistador** (`AttacksOrBlocks` mode, "target opponent …") through the exact same code path, and both of those share `matching_block_events` with the plain `Blocks` mode (traced in Step 2).

**Fix:** every place this plan adds a check of the shape `trigger.valid_target.is_some()` (or reads `trigger.valid_target.as_ref()`) to mean "there is a genuine CR 509 blocker/attacker filter" must first exclude the bare `TargetFilter::Player` case:

```rust
fn combat_filter(trigger: &TriggerDefinition) -> Option<&TargetFilter> {
    trigger.valid_target.as_ref().filter(|f| !matches!(f, TargetFilter::Player))
}
```
Applied at (five sites):
- `matching_becomes_blocked_events`'s **existing** effect-driven-block early-return check (`trigger_matchers.rs:3343-3350`, currently `if trigger.valid_target.is_some() { return Vec::new(); }` inside the `GameEvent::AttackerBecameBlockedByEffect` arm) — currently unguarded, must be retrofitted. Concrete failure scenario if left unfixed: Goblin Cadets (bare `BlocksOrBecomesBlocked`, "target opponent gains control of it") gets `valid_target = Some(TargetFilter::Player)` via this same effect-text fallback (the Player-collision described above). If Goblin Cadets is ever made to become blocked via an effect (`GameEvent::AttackerBecameBlockedByEffect`, the `Effect::BecomeBlocked`/Dazzling-Beauty-class mechanic) rather than via declared blockers, this unguarded check sees `valid_target.is_some() == true` — a false positive from the Player-collision, not a real blocker filter — and incorrectly suppresses the trigger, violating CR 509.3c (the bare "becomes blocked" form must still fire from an effect-driven block).
- `matching_becomes_blocked_events`'s **existing** blocker-side filter check (`trigger_matchers.rs:3382-3387`) — currently unguarded, must be retrofitted.
- `matching_becomes_blocked_events`'s **existing** `per_blocker` computation (`trigger_matchers.rs:3369`, currently `trigger.valid_target.is_some()`) — must become `combat_filter(trigger).is_some()`.
- `matching_block_events`'s **new** attacker-side filter check (Step 5).
- The new `matching_blocks_or_becomes_blocked_events`'s per-blocker computation (shares the same helper).

`TargetFilter::Player` is never a legitimate CR 509 blocker/attacker filter (a blocker/attacker is always an object, never a player), so this exclusion is a pure safety guard with no legitimate-case regression risk.

---

## Step 4d — "the other creature" anaphor: TWO insertion sites required (correction to round 4)

Semantic analysis: "the other creature" is **not** equivalent to "that creature." "That creature" (CR 608.2k, `TriggeringSource`) binds to a *fixed* triggering-event object regardless of the ability's own subject's role. "The other creature" is *relative to whichever role the ability's own subject played in this specific firing* — for the "blocks" half of a compound firing the antecedent is the attacker; for the "becomes blocked" half it's the blocker. This is exactly `ParentTarget`/`blocked_attacker_from_event`'s existing dual-branch semantics (branch 1: source is blocker → return attacker; new leading arm/branch 2: source is attacker → return blocker, now fixed). So "the other creature" must **always** map to `ParentTarget`, **unconditionally** — never gated on `ctx.subject`, unlike "that creature."

Traced both grammatical positions Mammoth Harness/Venom actually use:

1. **Object position** ("destroy **the other creature**", Venom) — resolved via the generic `parse_target_with_syntax` dispatcher's definite-anaphor `alt()` block. **Insertion site confirmed at `oracle_target.rs:1117`**, immediately alongside the existing `value(TargetFilter::ParentTarget, tag("the creature"))`:
   ```rust
   value(TargetFilter::ParentTarget, tag("the other creature")),
   value(TargetFilter::ParentTarget, tag("the creature")),
   ```

2. **Subject position** ("**the other creature** gains first strike…", Mammoth Harness) — resolved via `oracle_effect/subject.rs::parse_subject_application`, which does **not** fall back to `parse_target_with_syntax` — its fallback for unrecognized subjects is the narrower `parse_type_phrase`/`parse_type_phrase_with_ctx` (`oracle_target.rs:1841-1930+`), which strips only `"a "`/`"an "` articles and has **no** anaphor recognition at all (confirmed by reading its body — it is a pure typed-noun-phrase parser). Because "the other creature" doesn't start with a type word, this fallback would fail to consume "the other" and the whole clause would degrade to `Effect::Unimplemented`. **A second, unconditional arm must be added directly in `subject.rs::parse_subject_application`**, structured like the existing "that " handler (lines 2540-2576) but *without* that handler's `ctx.subject.is_some()` conditional branch — always returning `ParentTarget`:
   ```rust
   // CR 608.2c + CR 509.1/509.3d: "the other creature" — the creature on the
   // opposite side of a compound blocks-or-becomes-blocked pairing (Mammoth
   // Harness, Venom). Unconditionally ParentTarget (unlike "that creature"):
   // the antecedent flips per-firing-orientation, which `blocked_attacker_from_event`
   // already disambiguates from the resolved event shape, regardless of ctx.subject.
   if let Ok((rest_subject, _)) = tag::<_, _, OracleError<'_>>("the other ").parse(lower.as_str()) {
       let consumed = lower.len() - rest_subject.len();
       let original_rest = &subject[consumed..];
       let (filter, rem) = parse_type_phrase(original_rest);
       if rem.trim().is_empty() && !matches!(filter, TargetFilter::Any) {
           return Some(SubjectApplication {
               affected: TargetFilter::ParentTarget,
               target: Some(TargetFilter::ParentTarget),
               multi_target: None,
               inherits_parent: true,
               is_optional: false,
           });
       }
   }
   ```
   Placed before the existing "that " block (line 2540) for a stable, longest-match-first-consistent position (no prefix collision with "that " either way, but grouping definite-anaphor arms together matches file convention).

This two-site requirement is why finding is flagged as a correction to round 4, which cited only `oracle_target.rs:1117`.

---

## Step 5 — Implementation steps

**5.1 — `types/events.rs`** (near line 545): add
```rust
/// CR 509.3d: A per-blocker `Blocks`/`BecomesBlocked`/`BlocksOrBecomesBlocked`
/// firing with an explicit blocker/attacker qualifier — carries both ids so
/// "that creature"/"the other creature" resolution never has to infer
/// orientation from event shape.
AttackerBecameBlockedByFilteredBlocker {
    attacker: ObjectId,
    blocker: ObjectId,
},
```

**5.2 — `types/triggers.rs`**: add `BlocksOrBecomesBlocked` to the "Compound triggers" section (after line 542's `AttacksOrBlocks`), doc comment: `/// CR 509.1h + CR 509.3d: "~ blocks or becomes blocked" — fires on either the blocker-declaration event or the becomes-blocked event, with per-firing blocker/attacker disambiguation available to the effect body.` Add `FromStr` arm (`"BlocksOrBecomesBlocked" => TriggerMode::BlocksOrBecomesBlocked`, alphabetically near line 606's `"Blocks"`). Add to the string-count test list (near line 895's `"Blocks"`).

**5.3 — `oracle_trigger.rs` root-cause fix** (replacing lines ~8660-8666): dispatch `"blocks or becomes blocked"` (compound, no filter — Karn/Goblin-Cadets shape) before the bare `"blocks"` check; extend the bare `"blocks"` arm to also try the new `parse_blocks_a_filter` against the remainder and populate `def.valid_target`. The compound arm must ALSO try `parse_becomes_blocked_by_filter` against ITS remainder (the text after "blocks or becomes blocked"), following the exact same "try the filter-suffix parse against the remainder" structure as the bare-`"blocks"` arm — so Venom/Mammoth Harness (which use the compound form WITH a filter) get `TriggerMode::BlocksOrBecomesBlocked` with `valid_target` populated, and Karn/Goblin Cadets (compound WITHOUT a filter) get `valid_target = None`. Concretely:
```rust
// "blocks or becomes blocked [by a <filter>]" — Karn (bare), Goblin Cadets
// (bare), Venom/Mammoth Harness (filtered).
if let Ok((after_compound, _)) =
    tag::<_, _, OracleError<'_>>("blocks or becomes blocked").parse(rest)
{
    let mut def = make_base();
    def.mode = TriggerMode::BlocksOrBecomesBlocked;
    def.valid_card = Some(subject.clone());
    def.valid_target = parse_becomes_blocked_by_filter(after_compound);
    return Some((TriggerMode::BlocksOrBecomesBlocked, def));
}
// "blocks [a <filter>]" — Wall of Frost (bare), High-Rise Sawjack (filtered).
if let Ok((after_blocks, _)) = tag::<_, _, OracleError<'_>>("blocks").parse(rest) {
    let mut def = make_base();
    def.mode = TriggerMode::Blocks;
    def.valid_card = Some(subject.clone());
    def.valid_target = parse_blocks_a_filter(after_blocks);
    return Some((TriggerMode::Blocks, def));
}
```
This is the fully-resolved, non-dead-code version of the dispatch — no fragment is left "to be folded in by the implementer"; both arms are structurally parallel and self-contained.

New helper (near `parse_becomes_blocked_by_filter`, `oracle_trigger.rs:9164`):
```rust
/// CR 509.1h: "blocks a <filter>" carries a target-side (attacker) qualifier —
/// mirrors `parse_becomes_blocked_by_filter`'s blocker-side qualifier exactly.
fn parse_blocks_a_filter(input: &str) -> Option<TargetFilter> {
    let (type_phrase, _) = alt((tag::<_, _, OracleError<'_>>(" a "), tag(" an "))).parse(input).ok()?;
    let (filter, rest) = parse_type_phrase(type_phrase);
    rest.trim().is_empty().then_some(filter)
}
```

**5.4 — `oracle_target.rs:1117`**: add `value(TargetFilter::ParentTarget, tag("the other creature"))` sibling arm (Step 4d).

**5.5 — `oracle_effect/subject.rs`** (before line 2540's "that " block): add the unconditional "the other `<type>`" → `ParentTarget` arm (Step 4d, full code given above).

**5.6 — `game/targeting.rs`**:
- `blocked_attacker_from_event` (line 1160): new leading arm returning `blocker` directly (Step 4b).
- `extract_source_from_event` (line 1284, arm near 1337): new arm `GameEvent::AttackerBecameBlockedByFilteredBlocker { blocker, .. } => Some(*blocker)` (Step 4b — mandatory, not optional).

**5.7 — `game/trigger_matchers.rs`**:
- Add `combat_filter(trigger: &TriggerDefinition) -> Option<&TargetFilter>` private helper (Step 4c).
- `matching_becomes_blocked_events` (line 3337): change the effect-driven-block early-return check inside the `GameEvent::AttackerBecameBlockedByEffect` arm (line 3348, currently `if trigger.valid_target.is_some() { return Vec::new(); }`) to `if combat_filter(trigger).is_some() { return Vec::new(); }`; change `per_blocker` (line 3369) to `combat_filter(trigger).is_some()`; change the blocker-filter check (lines 3382-3387) to consult `combat_filter(trigger)` instead of `&trigger.valid_target`; change the per-blocker emission (currently `Some(GameEvent::BlockersDeclared { assignments: vec![(*blocker, *attacker)] })` at line 3398-3400) to `Some(GameEvent::AttackerBecameBlockedByFilteredBlocker { attacker: *attacker, blocker: *blocker })` **only on the `per_blocker` branch** (the bare once-per-combat branch keeps emitting `BlockersDeclared` unchanged, since it has no single unambiguous blocker to carry). This applies regardless of `trigger.mode` (Decision #3, resolved as (b) — no mode-gate).
- `matching_block_events` (line 1817): add the new attacker-side filter check, guarded by `combat_filter`:
  ```rust
  pub(super) fn matching_block_events(...) -> Vec<GameEvent> {
      if let GameEvent::BlockersDeclared { assignments } = event {
          assignments.iter().filter_map(|(blocker, attacker)| {
              let blocker_matches = if trigger.valid_card.is_some() {
                  valid_card_matches(trigger, state, *blocker, source_id)
              } else {
                  *blocker == source_id
              };
              if !blocker_matches { return None; }
              let attacker_matches = match combat_filter(trigger) {
                  Some(filter) => target_filter_matches_object(state, *attacker, filter, source_id),
                  None => true,
              };
              attacker_matches.then_some(GameEvent::BlockersDeclared { assignments: vec![(*blocker, *attacker)] })
          }).collect()
      } else { Vec::new() }
  }
  ```
  (Kept as `BlockersDeclared`, not the new event type — the `Blocks`-mode source is already the blocker, so `blocked_attacker_from_event`'s *existing, unmodified* first branch already resolves "that creature"/"the other creature" correctly for this side; no ambiguity to eliminate here.)
- New union matcher:
  ```rust
  pub(super) fn match_blocks_or_becomes_blocked(event: &GameEvent, trigger: &TriggerDefinition, source_id: ObjectId, state: &GameState) -> bool {
      !matching_blocks_or_becomes_blocked_events(event, trigger, source_id, state).is_empty()
  }
  pub(super) fn matching_blocks_or_becomes_blocked_events(event: &GameEvent, trigger: &TriggerDefinition, source_id: ObjectId, state: &GameState) -> Vec<GameEvent> {
      matching_block_events(event, trigger, source_id, state)
          .into_iter()
          .chain(matching_becomes_blocked_events(event, trigger, source_id, state))
          .collect()
  }
  ```
- `trigger_matcher()` (line 18): add arm near line 54: `TriggerMode::BlocksOrBecomesBlocked => match_blocks_or_becomes_blocked,`
- `build_trigger_registry()` (line 225): add near line 253: `r.insert(TriggerMode::BlocksOrBecomesBlocked, match_blocks_or_becomes_blocked);`
- Group `AttackerBecameBlockedByFilteredBlocker` into the wildcard-free "no trigger subject" list at line 927 alongside `AttackerBecameBlockedByEffect`.

**5.8 — `game/triggers.rs`**: **call site** confirmed unchanged at `triggers.rs:768` (`if let Some(matcher) = trigger_matcher(...)`, distinct from the `trigger_matcher()` **definition** at `trigger_matchers.rs:18` — finding #6, both correct, now stated unambiguously). New per-instance narrowing arm inserted after the existing `BecomesBlocked` arm (currently lines 849-855):
```rust
} else if matches!(trig_def.mode, TriggerMode::BlocksOrBecomesBlocked) {
    super::trigger_matchers::matching_blocks_or_becomes_blocked_events(event, trig_def, obj_id, state)
        .into_iter()
        .map(|trigger_event| vec![trigger_event])
        .collect()
}
```

**5.9 — `analysis/ability_graph.rs::trigger_axis`** (line 1039): add `TriggerMode::BlocksOrBecomesBlocked` into the giant `None`-returning group, next to `TriggerMode::AttacksOrBlocks` (line 1218).

**5.10 — `game/trigger_index.rs::keys_from_trigger_def`** (line 106): add `TriggerMode::BlocksOrBecomesBlocked` to the group at lines 199-207 (pushes `TriggerEventKey::Blocks`, same as `Blocks`/`BlockersDeclared`/`BecomesBlocked`). Add `GameEvent::AttackerBecameBlockedByFilteredBlocker { .. } => push(TriggerEventKey::Blocks)` next to line 599's `AttackerBecameBlockedByEffect` arm.

**5.11 — `game/log.rs`**:
- `categorize` (Combat group, lines 114-119): add `| GameEvent::AttackerBecameBlockedByFilteredBlocker { .. }`.
- `format_segments` (near lines 604-606): add sibling arm (Step 4b table, exact code given).
- `should_exclude_event`: no change (confirmed, Step 4b).

**5.12 — `game/public_state.rs`** (wildcard-free group, lines 401-439): add `| GameEvent::AttackerBecameBlockedByFilteredBlocker { .. }` next to line 421's `AttackerBecameBlockedByEffect`.

**5.13 — Test update — `oracle_trigger_tests.rs:11436-11445`** (Karn Silver Golem; confirmed still correct and present at this exact location, carried forward from round 4 unchanged per finding #7):
```rust
#[test]
fn trigger_blocks_or_becomes_blocked() {
    let def = parse_trigger_line(
        "Whenever Karn, Silver Golem blocks or becomes blocked, it gets -4/+4 until end of turn.",
        "Karn, Silver Golem",
    );
    assert_eq!(def.mode, TriggerMode::BlocksOrBecomesBlocked);
    assert_eq!(def.valid_card, Some(TargetFilter::SelfRef));
    assert!(def.valid_target.is_none(), "no blocker/attacker qualifier on Karn's trigger");
}
```

**5.14 — New parser tests** (`oracle_trigger_tests.rs`, alongside the Quagmire Lamprey block at line 6546):
- High-Rise Sawjack: `"Whenever High-Rise Sawjack blocks a creature with flying, High-Rise Sawjack gets +2/+0 until end of turn."` → `mode == Blocks`, `valid_target == Some(Typed{Creature, WithKeyword(Flying)})`.
- Goblin Cadets: `"Whenever Goblin Cadets blocks or becomes blocked, target opponent gains control of it."` → `mode == BlocksOrBecomesBlocked`, `valid_target` is `None` **or** `Some(Player)` depending on which lowering path fires — assert explicitly that if `Some(Player)`, the runtime `combat_filter()` helper (unit-tested directly, see 5.16) treats it as absent.
- Mammoth Harness: `"Whenever enchanted creature blocks or becomes blocked by a creature, the other creature gains first strike until end of turn."` → `mode == BlocksOrBecomesBlocked`, `valid_card == Some(AttachedTo{..})`, `valid_target == Some(Typed{Creature, ..})`.
- Venom: `"Whenever enchanted creature blocks or becomes blocked by a non-Wall creature, destroy the other creature at end of combat."` → same mode/valid_card shape, `valid_target` carries the non-Wall exclusion; `execute.effect` is `CreateDelayedTrigger` wrapping `Effect::Destroy { target: ParentTarget, .. }` gated `AtNextPhase{EndCombat}`.
- Quagmire Lamprey regression: assert the parsed effect's `target` field is `ParentTarget` (documents the premise the runtime fix resolves — this assertion is what makes the runtime test in 5.15 non-vacuous: without it, a reviewer can't tell whether 5.15's fix comes from the parser or the runtime).

**5.15 — `apply()`-level integration test (Venom) — fully concrete, per finding #5**

Home file: `crates/engine/tests/dazzling_beauty_become_blocked.rs`-style pattern (GameScenario/GameRunner), combined with the delayed-trigger scheduling assertion pattern from `crates/engine/tests/integration/std_longtail_b_delayed_effects.rs::fortune_schedules_end_of_combat_delayed_trigger` (lines 126-167, confirmed present and passing today), and the `DeclareBlockers`/`OrderTriggers`/`advance_until_stack_empty` combat-declaration recipe from `crates/engine/tests/integration/rules/combat.rs::becomes_blocked_by_creature_fires_for_each_blocker` (lines 143-191, confirmed passing today via direct `cargo test` run this round). Placed as a new test in `crates/engine/tests/integration/rules/combat.rs` (same file/module as its closest sibling).

```rust
/// CR 509.3d + CR 603.7: Venom's "blocks or becomes blocked by a non-Wall
/// creature, destroy the other creature at end of combat" — the originally
/// reported bug (a compound blocks-or-becomes-blocked trigger with a blocker
/// filter silently dropping "or becomes blocked" and, independently, the
/// runtime resolving "the other creature" to the wrong object).
#[test]
fn venom_destroys_the_creature_that_blocked_it_at_end_of_combat() {
    let mut scenario = GameScenario::new();
    scenario.at_phase(Phase::PreCombatMain);
    // P0 attacks with a Venom-enchanted creature.
    let attacker = scenario.add_creature(P0, "Fell Beast", 3, 3).id();
    let venom = scenario
        .add_aura_from_oracle(
            P0,
            "Venom",
            "Enchant creature\nWhenever enchanted creature blocks or becomes blocked by \
             a non-Wall creature, destroy the other creature at end of combat.",
        )
        .attach_to(attacker)
        .id();
    let blocker = scenario.add_creature(P1, "Bear", 2, 2).id();
    let mut runner = scenario.build();

    runner.pass_both_players();
    runner
        .act(GameAction::DeclareAttackers {
            attacks: vec![(attacker, AttackTarget::Player(P1))],
            bands: vec![],
        })
        .expect("Venom-enchanted creature should be able to attack");
    runner.pass_both_players();
    runner
        .act(GameAction::DeclareBlockers { assignments: vec![(blocker, attacker)] })
        .expect("Bear should be able to block");
    runner.advance_until_stack_empty();

    // CR 603.7: the trigger's effect creates a delayed "at end of combat,
    // destroy [the blocker]" trigger — proves the compound mode fired from
    // the BlockersDeclared event (not silently dropped) AND that "the other
    // creature" resolved to the Bear (blocker), not to Fell Beast (attacker,
    // Venom's own enchanted host).
    //
    // Note (implementer verification, per delayed_trigger.rs:96-156 read this
    // round): when the inner effect refs `ParentTarget`/`TriggeringSource`,
    // `snapshot_targets` resolves it via `resolve_event_context_target(...)`
    // and stores the result as `delayed_ability.targets: Vec<TargetRef>` —
    // NOT by rewriting `Effect::Destroy`'s own `target` field to
    // `TargetFilter::SpecificObject`. `TargetFilter::SpecificObject` and
    // `TargetRef::Object` are distinct types (`types/ability.rs:4256` vs
    // `7139`). The correct assertion is therefore against
    // `dt.ability.targets`, not `dt.ability.effect`'s target field:
    let scheduled_on_blocker = runner.state().delayed_triggers.iter().any(|dt| {
        matches!(dt.condition, DelayedTriggerCondition::AtNextPhase { phase: Phase::EndCombat })
            && dt.ability.targets.contains(&TargetRef::Object(blocker))
    });
    assert!(
        scheduled_on_blocker,
        "Venom must schedule an end-of-combat destroy targeting the BLOCKER, not the \
         attacker; delayed_triggers = {:?}",
        runner.state().delayed_triggers
    );

    // Advance through End of Combat so the delayed trigger resolves.
    runner.advance_to_phase(Phase::EndCombat);
    runner.advance_until_stack_empty();

    assert_eq!(
        runner.state().objects.get(&blocker).map(|o| o.zone),
        Some(Zone::Graveyard),
        "the blocker must be destroyed at end of combat"
    );
    assert_eq!(
        runner.state().objects.get(&attacker).map(|o| o.zone),
        Some(Zone::Battlefield),
        "the Venom-enchanted attacker (Fell Beast) must survive — Venom destroys the OTHER \
         creature, never its own host"
    );
}
```

Implementer verification note: `scenario.add_aura_from_oracle(..).attach_to(id)` and `runner.advance_to_phase(Phase::EndCombat)` must be confirmed against the actual `GameScenario`/`GameRunner` builder API at implementation time (grep `fn add_aura` / `fn attach_to` / `fn advance_to_phase` in `game/scenario.rs`) — if the exact builder method names differ, substitute the real ones; the *shape* of the test (attach aura, declare attackers, declare blockers, assert delayed-trigger target before End of Combat, advance phase, assert graveyard zone after) is what must be preserved, following the `dazzling_beauty_become_blocked.rs` and `std_longtail_b_delayed_effects.rs` precedents exactly. The `dt.ability.targets.contains(&TargetRef::Object(blocker))` assertion shape (not `TargetFilter::SpecificObject`) is now the primary, verified-correct assertion, not a hedged fallback (this round's `delayed_trigger.rs:96-156` read confirmed the snapshot storage shape directly).

**5.16 — Unit tests, `trigger_matchers.rs`** (near the existing tests at lines 4690-4708, 8825-8962):
- `matching_block_events` / `matching_becomes_blocked_events` each get a new test constructing a trigger with `valid_target = Some(TargetFilter::Player)` and asserting the returned events are identical to the no-filter (bare/once-per-combat) case — proves the `Player`-exclusion guard.
- `combat_filter()` gets a direct unit test: `Some(Player) → None`, `Some(Typed(..)) → Some(Typed(..))`, `None → None`.
- New test constructing `GameEvent::AttackerBecameBlockedByFilteredBlocker` directly and asserting `blocked_attacker_from_event` and `extract_source_from_event` both return the blocker id (the two mandatory new arms from Step 4b).

---

## Verification Matrix

| Claim | Seam | Test | Revert-failing assertion | Sibling/negative | Hostile fixture |
|---|---|---|---|---|---|
| "blocks or becomes blocked" no longer silently drops the remainder | `oracle_trigger.rs` root-cause dispatch | 5.13 (Karn), 5.14 (Venom/Mammoth Harness parse shape) | Revert → `def.mode` stays `Blocks`, `valid_target` stays `None` for Venom | plain `"blocks a creature"` (Wall of Frost, existing test unaffected) | "blocks or becomes blocked by two or more creatures" — threshold form must stay bare, mirroring the existing `BecomesBlocked` threshold guard (`trigger_becomes_blocked_by_two_or_more_creatures_stays_bare`) |
| `Blocks`-mode filter capture (`parse_blocks_a_filter`) | `oracle_trigger.rs` | 5.14 (High-Rise Sawjack) | Revert → `valid_target` is `None`, trigger over-fires on any block | Wall of Frost's filter-less "blocks a creature" (must still leave `valid_target = None`, since it has no restrictive quality — actually note: "blocks a creature" with no restriction IS captured as `Typed(Creature)` by both old and new code; the *reach* fixture is High-Rise Sawjack's "with flying" qualifier surviving into `properties`) | none (bare "blocks", no article) |
| `TargetFilter::Player` never mistaken for a CR 509 filter | `matching_block_events`, `matching_becomes_blocked_events`, `combat_filter` | 5.16, 5.14 (Goblin Cadets) | Revert (remove guard) → Nascent Metamorph/Vraska's Conquistador's blocks-half never fires (attacker-side filter check rejects `Player`-vs-object) | genuine `Typed` filter (High-Rise Sawjack) still applies correctly | Goblin Cadets fires once per combat (bare semantics), not once per blocker |
| Quagmire Lamprey's -1/-1 counter lands on the blocker, not itself | `blocked_attacker_from_event`, `extract_source_from_event` | New integration test mirroring 5.15's structure but for Quagmire Lamprey + `PutCounter` (add alongside) | Revert new `blocked_attacker_from_event` leading arm → counter lands on self | Acolyte-of-the-Inferno-shaped `DealDamage` cards (already-passing path (1)) must **not** regress — covered by re-running `becomes_blocked_by_creature_fires_for_each_blocker` after the change | two blockers on Quagmire Lamprey → two separate -1/-1 counters, one per blocker, none on Quagmire itself |
| Venom fires from `BlockersDeclared` (not silently dropped) and targets the blocker | full `apply()` pipeline | 5.15 | Revert compound-mode dispatch → no trigger fires at all; revert blocker-resolution fix → wrong creature destroyed | Mammoth Harness (immediate, non-delayed effect) as a second, simpler apply()-level case — recommended as a follow-up test using the identical setup minus the delayed-trigger/phase-advance steps | Wall creature blocking Venom's host → trigger does NOT fire (non-Wall filter), reach-guarded by asserting no delayed trigger is scheduled |
| No coverage/parse-status regression | `card-data`/coverage pipeline | N/A (no `Effect::Unimplemented` introduced or removed by this plan) | — | — | — |

**Identity/Provenance contract** (for "the other creature" / "that creature" / `ParentTarget` / `TriggeringSource`): source phrase → selected authority type: `ParentTarget` for "the other creature" (unconditional), `TriggeringSource` for "that creature" (conditional on non-self subject). Binding time: runtime, per-firing, from the narrowed single-assignment event (`GameEvent::AttackerBecameBlockedByFilteredBlocker` or `BlockersDeclared` with one assignment) — never snapshotted at parse time. Live semantics: re-resolved every firing (a creature blocking twice in the same combat, if ever legal, would resolve independently each time — not applicable under current combat rules but the mechanism doesn't assume otherwise). Storage: not stored on the permanent; resolved transiently from `state.current_trigger_event` at effect-resolution time via `resolve_event_context_target` (public wrapper around `resolve_event_context_target_for_event_or_state`). Consuming functions: `blocked_attacker_from_event`, `extract_source_from_event`. Invalidation: N/A (single-shot per trigger instance). Multi-authority hostile fixture: two simultaneous blockers on the same per-blocker filtered trigger must each independently resolve to their own blocker id, never a shared/first-wins id (covered by the existing `becomes_blocked_by_creature_fires_for_each_blocker` test's two-blocker setup, re-run as a regression guard after this change).
