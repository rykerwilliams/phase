//! Issue #8060 — natively-printed Cascade triggers but never casts the exiled
//! spell (Natural Reclamation, Deny Reality).
//!
//! > Natural Reclamation {4}{G} Instant — "Cascade … Destroy target artifact or
//! > enchantment."
//! > Deny Reality {3}{U}{B} Sorcery — "Cascade … Return target permanent to its
//! > owner's hand."
//!
//! Both Oracle-verified from Scryfall; both carry `keywords: ['Cascade']`.
//! The reporter saw the exile-until-a-cheaper-nonland step happen, but the
//! "you may cast it without paying its mana cost" cast never occur. The
//! maintainer ruled out total cascade breakage ("it worked on Maelstrom
//! Wanderer") and narrowed it to natively-printed Cascade.
//!
//! MEASURED BEFORE WRITING THIS: native-vs-granted alone does NOT explain the
//! report. `cascade_intervening_if_pipeline.rs` already drives a natively
//! printed Cascade SORCERY through the full `apply()` pipeline to a pending
//! `CastOffer` and passes, and `cast_during_resolution_pipeline.rs` already
//! accepts that offer and asserts the hit lands on the stack. So the defect
//! must live in something those fixtures do not vary.
//!
//! What they do not vary is TARGETING. Every existing cascade fixture casts a
//! targetless cascade spell and offers a targetless hit. Both reported cards
//! target. That is two distinct hypotheses with different mechanisms, and this
//! file separates them rather than assuming either:
//!
//!   * H1 — the cascade SPELL targets. A targeted cast detours through
//!     `WaitingFor::TargetSelection` before reaching the stack. The cascade
//!     trigger counts `Keyword::Cascade` in `obj.cast_spell_keywords`, a
//!     snapshot written in `finalize_cast_with_phyrexian_choices_inner`. If the
//!     target-first route reaches the stack without passing that site, the
//!     instance count is 0 and NO cascade trigger fires — no exile, no offer.
//!
//!   * H2 — the cascade HIT targets. `CastChoice::Cast` documents that "the
//!     cast pipeline still enforces target legality"; a targeted hit must raise
//!     target selection DURING the cascade trigger's resolution. If that cannot
//!     be raised mid-resolution, the exile and the offer both happen and only
//!     the cast fails.
//!
//! The two predict different observations, which is the point: H1 fails with no
//! offer at all; H2 fails with the offer present and the hit never reaching the
//! stack. The reporter's "the exile step happened" points at H2, but that is a
//! Discord paraphrase rather than a measurement, so the test discriminates.
//!
//! `both_untargeted_is_the_control` is the negative control. It mirrors the
//! known-green shape, so a red arm above cannot be blamed on this harness.
//!
//! Mana pips are Red rather than the printed {4}{G}/{3}{U}{B}: cascade's gate
//! reads MANA VALUE only (CR 702.85a — "a nonland card that costs less"), and
//! MV is preserved exactly (5 for the cascade spell, 1 for the hit). Oracle
//! text is verbatim.

use engine::game::scenario::{GameRunner, GameScenario, P0};
use engine::types::ability::TargetRef;
use engine::types::actions::{CastChoice, GameAction};
use engine::types::game_state::{CastOfferKind, CastPaymentMode, WaitingFor};
use engine::types::identifiers::ObjectId;
use engine::types::mana::{ManaCost, ManaCostShard, ManaType, ManaUnit};
use engine::types::phase::Phase;
use engine::types::zones::Zone;

// Verbatim Oracle text (Scryfall, 2026-09-18), reminder text included.
const NATURAL_RECLAMATION: &str = "Cascade (When you cast this spell, exile cards from the top of your library until you exile a nonland card that costs less. You may cast it without paying its mana cost. Put the exiled cards on the bottom in a random order.)\nDestroy target artifact or enchantment.";
const DENY_REALITY_TAIL: &str = "Return target permanent to its owner's hand.";
// The bare keyword, exactly as the existing green cascade fixtures spell it.
const BARE_CASCADE: &str = "Cascade";

/// MV 5 — matches Natural Reclamation's {4}{G} and Deny Reality's {3}{U}{B}.
fn cascade_source_cost() -> ManaCost {
    ManaCost::Cost {
        shards: vec![ManaCostShard::Red],
        generic: 4,
    }
}

/// MV 1 — strictly below the source MV, so it is a cascade HIT (CR 702.85a).
fn hit_cost() -> ManaCost {
    ManaCost::Cost {
        shards: vec![ManaCostShard::Red],
        generic: 0,
    }
}

fn red_pool(scenario: &mut GameScenario, count: usize) {
    let units: Vec<ManaUnit> = (0..count)
        .map(|_| ManaUnit::new(ManaType::Red, ObjectId(0), false, vec![]))
        .collect();
    scenario.with_mana_pool(P0, units);
}

/// Resolve the cascade trigger sitting above the spell on the stack.
fn pass_to_resolve_trigger(runner: &mut GameRunner) {
    runner.act(GameAction::PassPriority).expect("p0 pass");
    runner.act(GameAction::PassPriority).expect("p1 pass");
}

fn describe(runner: &GameRunner) -> String {
    format!("{:?}", runner.state().waiting_for)
        .chars()
        .take(140)
        .collect()
}

/// H1 — the cascade SPELL targets.
///
/// Natural Reclamation's own shape: a targeted cascade spell. The cast detours
/// through target selection before the spell reaches the stack. If that route
/// misses the `cast_spell_keywords` snapshot, no cascade trigger is synthesized
/// and the exile step never happens.
///
/// Revert-proof by construction: the reach-guard below asserts the spell really
/// did raise a target prompt, so a green result cannot come from the spell
/// quietly not targeting at all.
#[test]
fn a_targeted_cascade_spell_still_triggers_and_offers_its_hit() {
    let mut scenario = GameScenario::new();
    scenario.at_phase(Phase::PreCombatMain);
    red_pool(&mut scenario, 5);

    // TWO legal targets for "destroy target artifact or enchantment", not one.
    // Load-bearing: with a single candidate the engine AUTO-SELECTS it and
    // raises no prompt at all, so the reach-guard below fires and this arm never
    // reaches the assertions it exists for. (Measured: a one-artifact board sent
    // the cast straight to `Priority`.) Two candidates make the choice real, so
    // the targeted-cast route is genuinely exercised.
    let artifact = scenario
        .add_creature(P0, "Target Artifact", 0, 0)
        .as_artifact()
        .id();
    let _second_artifact = scenario
        .add_creature(P0, "Other Artifact", 0, 0)
        .as_artifact()
        .id();

    // Keyword HINTS are load-bearing here, and their absence is why two earlier
    // runs of this arm died at the reach-guard. Production gets
    // `keywords: ['Cascade']` from MTGJSON and merges it via
    // `merge_extracted_keywords`; a hand-built card that only calls
    // `from_oracle_text` supplies no such list. Measured without them: the whole
    // Oracle text collapsed to a single
    // `Unimplemented { name: "unrecognized_clause_head",
    //  description: "Cascade Destroy target artifact or enchantment" }`
    // — the keyword line and the effect line JOINED — and the spell reached the
    // stack with `keywords: []`. So the arm was never a targeted-cascade test at
    // all; it was an unparsed blob that happened to cast.
    // NOTE the constructor: `add_spell_to_hand` (no Oracle), not
    // `add_spell_to_hand_from_oracle`. The latter parses the text itself, so
    // pairing it with `from_oracle_text_with_keywords` would parse the same card
    // twice — once hint-less, once hinted — and leave the object carrying both
    // results. The precedents (`angels_grace.rs`, `affinity_plural_subtype.rs`)
    // all apply the hinted parse to a builder that has not parsed yet.
    let spell = scenario
        .add_spell_to_hand(P0, "Natural Reclamation", true)
        .with_mana_cost(cascade_source_cost())
        .from_oracle_text_with_keywords(&["Cascade"], NATURAL_RECLAMATION)
        .id();
    let hit = scenario
        .add_spell_to_library_top(P0, "Cheap Hit", true)
        .with_mana_cost(hit_cost())
        .id();

    let mut runner = scenario.build();
    let card_id = runner.state().objects[&spell].card_id;
    let cast_result = runner
        .act(GameAction::CastSpell {
            object_id: spell,
            card_id,
            targets: vec![],
            payment_mode: CastPaymentMode::Auto,
        })
        .expect("reach-guard: a targeted cascade spell must be castable with MV-5 mana");
    // Capture the event stream of each step. With the snapshot proven populated,
    // the open question is whether the SpellCast trigger collection ever ran for
    // this route, or ran and had the cascade trigger dropped afterwards. Only the
    // events can tell those apart.
    let cast_events: Vec<String> = cast_result
        .events
        .iter()
        .map(|event| format!("{event:?}").chars().take(90).collect::<String>())
        .collect();

    // Reach-guard: this arm is only meaningful if the spell genuinely targets.
    let target_events: Vec<String>;
    match runner.state().waiting_for.clone() {
        WaitingFor::TargetSelection { .. } => {
            let declared = runner
                .act(GameAction::SelectTargets {
                    targets: vec![TargetRef::Object(artifact)],
                })
                .expect("declaring the artifact target must succeed");
            target_events = declared
                .events
                .iter()
                .map(|event| format!("{event:?}").chars().take(90).collect::<String>())
                .collect();
        }
        other => {
            // Two runs died here printing only `waiting_for`, which cannot say
            // WHY. Report the parse and the board so the cause is measured
            // rather than guessed: an effect that never lowered to a targeted
            // Destroy, or artifacts that are not legal targets, both produce
            // "no prompt" and are told apart only by this dump.
            let state = runner.state();
            let spell_obj = &state.objects[&spell];
            let abilities: Vec<String> = spell_obj
                .abilities
                .iter()
                .map(|ability| format!("{:?}", ability.effect).chars().take(180).collect())
                .collect();
            let artifacts: Vec<String> = [artifact, _second_artifact]
                .iter()
                .map(|id| {
                    let obj = &state.objects[id];
                    format!(
                        "{}: zone={:?} types={:?}",
                        obj.name, obj.zone, obj.card_types.core_types
                    )
                })
                .collect();
            panic!(
                "reach-guard: \"destroy target artifact or enchantment\" must raise a target \
                 prompt — without one this arm tests nothing.\n\
                 waiting_for: {other:?}\n\
                 spell zone: {:?}  keywords: {:?}\n\
                 parsed abilities ({}): {abilities:#?}\n\
                 candidate targets: {artifacts:#?}\n\
                 reading: no targeted Destroy among the abilities => the keyword + reminder \
                 text + effect-line shape did not lower an effect (parser, not cascade);\n\
                 \x20        a targeted Destroy present but no prompt => the slot found no \
                 legal target among the artifacts above.",
                spell_obj.zone,
                spell_obj.keywords,
                spell_obj.abilities.len(),
            )
        }
    }

    // STAGED SAMPLES. A single post-walk reading of `deferred_triggers` cannot
    // tell "never collected" from "collected, then lost". Sample immediately
    // after target declaration (before ANY priority pass), then again after the
    // first pass, so the two are separable:
    //   * >0 here, 0 later  => collected and PARKED, then lost during the walk
    //   * 0 here            => SpellCast never fed collection on this route,
    //                          even though the event was emitted
    // CR 603.4: cascade's synthesized trigger carries a `WasCast` intervening-if
    // re-checked AT RESOLUTION against the spell's live `cast_from_zone`. Sample
    // it HERE, while the spell is still on the Stack — the post-walk reading is
    // worthless because the spell has left the stack by then and
    // `clear_post_collection_transients` legitimately clears the field.
    let cast_from_zone_on_stack = runner.state().objects[&spell].cast_from_zone;
    let spell_zone_after_targets = runner.state().objects[&spell].zone;
    // THE VALUE THE RE-CHECK ACTUALLY READS. `WasCast` resolves through
    // `TriggerSourceRead::cast_from_zone()`, which for a SpellCast-triggered
    // ability consults the LATCHED `TriggerSourceContext` carried on the trigger
    // — not the spell object's field, which is only populated later in
    // `resolve_top`. Every earlier sample was a proxy; this is the real thing.
    let latched_cast_from_zone: Vec<String> = runner
        .state()
        .stack
        .iter()
        .filter_map(|entry| {
            entry.ability().map(|ability| {
                // Discriminant ONLY, then the value. Debug-formatting the whole
                // `StackEntryKind` and truncating afterwards discarded the value:
                // the entry Debug is enormous, so `trigger_source=` never survived
                // the cut and the measurement read back as entry kinds alone.
                let kind = match &entry.kind {
                    engine::types::game_state::StackEntryKind::Spell { .. } => "Spell",
                    engine::types::game_state::StackEntryKind::TriggeredAbility { .. } => {
                        "TriggeredAbility"
                    }
                    engine::types::game_state::StackEntryKind::ActivatedAbility { .. } => {
                        "ActivatedAbility"
                    }
                    engine::types::game_state::StackEntryKind::KeywordAction { .. } => {
                        "KeywordAction"
                    }
                };
                format!(
                    "{kind}: trigger_source={:?}",
                    ability
                        .trigger_source
                        .as_ref()
                        .map(|context| context.cast_from_zone)
                )
            })
        })
        .collect();
    let deferred_after_targets = runner.state().deferred_triggers.len();
    let pending_cast_after_targets = runner.state().pending_cast.is_some();
    let waiting_after_targets: String = format!("{:?}", runner.state().waiting_for)
        .chars()
        .take(56)
        .collect();

    // POSITIVE REACH-GUARD on the instrument itself. "The hit stayed in the
    // library" is consistent with a real cascade defect AND with a fixture whose
    // spell never carried Cascade at all — three earlier runs of this arm failed
    // for exactly that second reason. Prove the keyword is attached before
    // drawing any conclusion from the trigger not firing.
    let spell_keywords = runner.state().objects[&spell].keywords.clone();
    assert!(
        spell_keywords.contains(&engine::types::keywords::Keyword::Cascade),
        "reach-guard: the spell must actually carry Keyword::Cascade, or \"no trigger \
         fired\" says nothing about cascade. keywords = {spell_keywords:?}"
    );

    // A BOUNDED WALK, not a fixed pass count. The control resolves in exactly
    // two passes, but a targeted cast spends a step on target declaration, so a
    // hardcoded two could simply stop short — measured symptom of that: the hit
    // still in Library with `stack depth: 1`, i.e. something still pending. The
    // trail turns that into a readable sequence instead of a puzzle, and stops
    // the arm from blaming the engine for an exhausted pass budget.
    let mut trail: Vec<String> = Vec::new();
    for _ in 0..12 {
        let waiting = runner.state().waiting_for.clone();
        trail.push(format!("{waiting:?}").chars().take(56).collect::<String>());
        if matches!(
            waiting,
            WaitingFor::CastOffer {
                kind: CastOfferKind::Cascade { .. },
                ..
            }
        ) {
            break;
        }
        if runner.state().stack.is_empty() && runner.state().objects[&hit].zone != Zone::Library {
            break;
        }
        // Capture WHAT EACH PASS DID, not just what it waited on. A trail of
        // bare `waiting_for` strings reports twelve identical `Priority` entries
        // and explains nothing; the working route creates its cascade trigger
        // during these passes, so the events per pass are the discriminator.
        match waiting {
            WaitingFor::Priority { .. } => match runner.act(GameAction::PassPriority) {
                Ok(step) => {
                    let kinds: Vec<String> = step
                        .events
                        .iter()
                        .map(|event| {
                            format!("{event:?}")
                                .split_whitespace()
                                .next()
                                .unwrap_or("?")
                                .to_string()
                        })
                        .collect();
                    trail.push(format!(
                        "   -> stack={} events={kinds:?}",
                        runner.state().stack.len()
                    ));
                }
                Err(_) => break,
            },
            _ => break,
        }
    }

    let stack_dump: Vec<String> = runner
        .state()
        .stack
        .iter()
        .map(|entry| format!("{:?}<-{:?}", entry.kind, entry.source_id))
        .collect();

    // THE TWO DRAIN GATES, sampled rather than reasoned about. The cascade
    // trigger is collected into `state.deferred_triggers` and only reaches the
    // stack when a drain runs. `triggers::drain_deferred_triggers_after_stack_
    // object_announcement` hard-returns when `pending_cast.is_some()`, and the
    // `casting_costs` wrapper returns early unless the wait it is installing is
    // `Priority`. Whether the trigger is PARKED (collected, never drained) or
    // ABSENT (never collected) is the whole identity of this defect, and only
    // these two readings separate them.
    let deferred_len = runner.state().deferred_triggers.len();
    let pending_cast_set = runner.state().pending_cast.is_some();
    let resolution_completion_set = runner.state().pending_resolution_completion.is_some();

    assert_eq!(
        runner.state().objects[&hit].zone,
        Zone::Exile,
        "CR 702.85a: cascade must exile down to the hit for a TARGETED cascade spell.\n\
         MEASURED CAUSE (do not re-derive): the trigger DOES fire — both routes show \
         stack=2 before any pass. It resolves as a NO-OP. The cascade trigger's latched \
         `TriggerSourceContext.cast_from_zone` is None here but Some(Hand) on the working \
         untargeted route, so the CR 603.4 `WasCast` intervening-if re-check fails at \
         resolution and the trigger leaves the stack having done nothing — \
         [StackResolved] alone, versus [ZoneChanged, EffectResolved, StackResolved] when \
         it works. The latch copies `obj.cast_from_zone` via `snapshot_for_zone_change`, \
         and that field is still None on this route when SpellCast collection runs.\n\
         spell keywords: {spell_keywords:?}\n\
         cast_spell_keywords: {:?}\n\
         cast_from_zone: {:?}\n\
         stack ({}): {stack_dump:?}\n\
         priority trail: {trail:?}\n\
         events @ CastSpell ({}): {cast_events:#?}\n\
         events @ SelectTargets ({}): {target_events:#?}\n\
         AFTER SelectTargets (before any priority pass): cast_from_zone={cast_from_zone_on_stack:?} \
         spell_zone={spell_zone_after_targets:?} deferred_triggers={deferred_after_targets} \
         pending_cast={pending_cast_after_targets} waiting_for={waiting_after_targets}\n\
         LATCHED trigger_source.cast_from_zone per stack entry: {latched_cast_from_zone:#?}\n\
         (this is the value `WasCast` actually re-checks — compare against the working \
         route's baseline line above; a None here with Some(Hand) there names the seam)\n\
         NOTE the trail shows stack=2 before any pass on BOTH routes, so the cascade trigger \
         IS created and IS on the stack here. The working route's trigger resolves with \
         [ZoneChanged, EffectResolved, StackResolved]; this one resolves with [StackResolved] \
         ALONE — a NO-OP resolution, consistent with the CR 603.4 WasCast intervening-if \
         re-check failing against a missing cast_from_zone.\n\
         AFTER the walk: deferred_triggers: {deferred_len}   pending_cast: {pending_cast_set}   \
         pending_resolution_completion: {resolution_completion_set}\n\
         waiting_for = {}\n\
         reading: SpellCast IS emitted (at SelectTargets), so collection had its input.\n\
         \x20        deferred_triggers > 0 => the cascade trigger was COLLECTED AND PARKED \
         and no drain ever ran; the two flags above say which gate held\n\
         \x20        (drain hard-returns on pending_cast.is_some(); the casting_costs \
         wrapper returns early unless the installed wait is Priority).\n\
         \x20        deferred_triggers == 0 => NOT conclusive on its own — this is sampled \
         after the priority walk, so it means either never-collected or \
         collected-then-drained-and-dropped; re-sample immediately after SelectTargets \
         to separate those.",
        runner.state().objects[&spell].cast_spell_keywords,
        runner.state().objects[&spell].cast_from_zone,
        runner.state().stack.len(),
        cast_events.len(),
        target_events.len(),
        describe(&runner)
    );
    assert!(
        matches!(
            runner.state().waiting_for,
            WaitingFor::CastOffer {
                kind: CastOfferKind::Cascade { hit_card, .. },
                ..
            } if hit_card == hit
        ),
        "cascade must leave a CastOffer for the exiled hit; waiting_for = {}",
        describe(&runner)
    );
}

/// H2 — the cascade HIT targets.
///
/// `CastChoice::Cast` documents that "the cast pipeline still enforces target
/// legality", so a targeted hit must declare targets while the cascade trigger
/// is still resolving. If that cannot happen mid-resolution, the exile and the
/// offer both occur and only the cast fails — exactly the reported shape.
#[test]
fn accepting_cascade_casts_a_hit_that_needs_targets() {
    let mut scenario = GameScenario::new();
    scenario.at_phase(Phase::PreCombatMain);
    red_pool(&mut scenario, 5);

    // A legal target for the HIT's "return target permanent to its owner's hand".
    let bystander = scenario.add_creature(P0, "Bystander", 2, 2).id();

    let spell = scenario
        .add_spell_to_hand_from_oracle(P0, "Cascade Sorcery", false, BARE_CASCADE)
        .with_mana_cost(cascade_source_cost())
        .id();
    let hit = scenario
        .add_spell_to_library_top(P0, "Targeted Hit", true)
        .with_mana_cost(hit_cost())
        .from_oracle_text(DENY_REALITY_TAIL)
        .id();

    let mut runner = scenario.build();
    let card_id = runner.state().objects[&spell].card_id;
    runner
        .act(GameAction::CastSpell {
            object_id: spell,
            card_id,
            targets: vec![],
            payment_mode: CastPaymentMode::Auto,
        })
        .expect("casting the cascade source must succeed");

    pass_to_resolve_trigger(&mut runner);

    // Reach-guard: the offer must exist, or "the cast did not happen" would be
    // trivially true for the wrong reason.
    assert!(
        matches!(
            runner.state().waiting_for,
            WaitingFor::CastOffer {
                kind: CastOfferKind::Cascade { hit_card, .. },
                ..
            } if hit_card == hit
        ),
        "reach-guard: cascade must offer the targeted hit; waiting_for = {}",
        describe(&runner)
    );

    runner
        .act(GameAction::CascadeChoice {
            choice: CastChoice::Cast,
        })
        .expect("accepting the cascade offer must be a legal action");

    // A targeted hit may legitimately stop on a target prompt before reaching
    // the stack; answer it if so. What must NOT happen is the hit silently
    // ending up anywhere other than the stack.
    if let WaitingFor::TargetSelection { .. } = runner.state().waiting_for.clone() {
        runner
            .act(GameAction::SelectTargets {
                targets: vec![TargetRef::Object(bystander)],
            })
            .expect("declaring the hit's target must succeed");
    }

    assert_eq!(
        runner.state().objects[&hit].zone,
        Zone::Stack,
        "CR 608.2g + CR 702.85a: accepting cascade must cast the hit during resolution. \
         A hit that needs targets must still reach the stack; landing anywhere else means \
         the cast was dropped. waiting_for = {}",
        describe(&runner)
    );
}

/// BUILDER CONTROL — untargeted, but built exactly the way the targeted arm is
/// (`add_spell_to_hand` + `from_oracle_text_with_keywords`).
///
/// Without this arm the experiment is confounded: the targeted arm differs from
/// `both_untargeted_is_the_control` in TWO ways at once — it targets, AND it is
/// built through the hinted-keyword path rather than `add_spell_to_hand_from_oracle`.
/// That is not a theoretical worry: `from_oracle_text_with_keywords` re-indexes
/// triggers only when the object is on the BATTLEFIELD, and these spells are in
/// hand. So a failure in the targeted arm could belong to the builder, not to
/// targeting.
///
/// This arm holds targeting fixed (none) and varies only the builder:
///   * GREEN => the hinted builder is fine; the targeted arm's failure is really
///     about TARGETING, and #8060 reproduces.
///   * RED   => the builder path is the cause, the targeted arm proves nothing
///     about cascade, and the fixture is at fault (again).
#[test]
fn the_hinted_builder_alone_still_cascades() {
    let mut scenario = GameScenario::new();
    scenario.at_phase(Phase::PreCombatMain);
    red_pool(&mut scenario, 5);

    let spell = scenario
        .add_spell_to_hand(P0, "Hinted Cascade Sorcery", false)
        .with_mana_cost(cascade_source_cost())
        .from_oracle_text_with_keywords(&["Cascade"], BARE_CASCADE)
        .id();
    let hit = scenario
        .add_spell_to_library_top(P0, "Cheap Hit", true)
        .with_mana_cost(hit_cost())
        .id();

    let mut runner = scenario.build();
    let card_id = runner.state().objects[&spell].card_id;
    runner
        .act(GameAction::CastSpell {
            object_id: spell,
            card_id,
            targets: vec![],
            payment_mode: CastPaymentMode::Auto,
        })
        .expect("casting the hinted cascade source must succeed");

    let spell_keywords = runner.state().objects[&spell].keywords.clone();
    assert!(
        spell_keywords.contains(&engine::types::keywords::Keyword::Cascade),
        "reach-guard: the hinted builder must attach Keyword::Cascade; keywords = \
         {spell_keywords:?}"
    );

    // BASELINE for the failing arm. This route works, so whatever it shows here
    // is what "collected correctly" looks like at the moment just after the cast
    // completes. Printed rather than asserted because a passing test emits no
    // assertion message; the runner passes --nocapture.
    let baseline_latched: Vec<String> = runner
        .state()
        .stack
        .iter()
        .filter_map(|entry| {
            entry.ability().map(|ability| {
                let kind = match &entry.kind {
                    engine::types::game_state::StackEntryKind::Spell { .. } => "Spell",
                    engine::types::game_state::StackEntryKind::TriggeredAbility { .. } => {
                        "TriggeredAbility"
                    }
                    engine::types::game_state::StackEntryKind::ActivatedAbility { .. } => {
                        "ActivatedAbility"
                    }
                    engine::types::game_state::StackEntryKind::KeywordAction { .. } => {
                        "KeywordAction"
                    }
                };
                format!(
                    "{kind}: trigger_source={:?}",
                    ability
                        .trigger_source
                        .as_ref()
                        .map(|context| context.cast_from_zone)
                )
            })
        })
        .collect();
    println!(
        "[baseline: WORKING untargeted route] LATCHED={baseline_latched:?} cast_from_zone={:?} \
         spell_zone={:?} \
         deferred_triggers={} pending_cast={} pending_resolution_completion={} waiting_for={:?}",
        runner.state().objects[&spell].cast_from_zone,
        runner.state().objects[&spell].zone,
        runner.state().deferred_triggers.len(),
        runner.state().pending_cast.is_some(),
        runner.state().pending_resolution_completion.is_some(),
        runner.state().waiting_for
    );

    // Same per-pass capture as the failing arm, on the route that WORKS. The
    // comparison is the evidence: whichever pass creates the cascade trigger
    // here is the step the targeted route must be missing.
    for step_index in 0..2 {
        let before: String = format!("{:?}", runner.state().waiting_for)
            .chars()
            .take(40)
            .collect();
        let step = runner
            .act(GameAction::PassPriority)
            .expect("baseline priority pass");
        let kinds: Vec<String> = step
            .events
            .iter()
            .map(|event| {
                format!("{event:?}")
                    .split_whitespace()
                    .next()
                    .unwrap_or("?")
                    .to_string()
            })
            .collect();
        println!(
            "[baseline pass {step_index}] from {before} -> stack={} events={kinds:?}",
            runner.state().stack.len()
        );
    }

    assert_eq!(
        runner.state().objects[&hit].zone,
        Zone::Exile,
        "the hinted builder alone must still cascade. If this is red, the targeted arm's \
         failure belongs to the BUILDER, not to targeting.\n\
         spell keywords: {spell_keywords:?}\n\
         cast_spell_keywords: {:?}\n\
         waiting_for = {}",
        runner.state().objects[&spell].cast_spell_keywords,
        describe(&runner)
    );
}

/// Negative control — both untargeted, mirroring the known-green shape. If this
/// arm ever reddens, the harness is at fault and the arms above prove nothing.
#[test]
fn both_untargeted_is_the_control() {
    let mut scenario = GameScenario::new();
    scenario.at_phase(Phase::PreCombatMain);
    red_pool(&mut scenario, 5);

    let spell = scenario
        .add_spell_to_hand_from_oracle(P0, "Cascade Sorcery", false, BARE_CASCADE)
        .with_mana_cost(cascade_source_cost())
        .id();
    let hit = scenario
        .add_spell_to_library_top(P0, "Cheap Hit", true)
        .with_mana_cost(hit_cost())
        .id();

    let mut runner = scenario.build();
    let card_id = runner.state().objects[&spell].card_id;
    runner
        .act(GameAction::CastSpell {
            object_id: spell,
            card_id,
            targets: vec![],
            payment_mode: CastPaymentMode::Auto,
        })
        .expect("casting the cascade source must succeed");

    pass_to_resolve_trigger(&mut runner);

    assert!(
        matches!(
            runner.state().waiting_for,
            WaitingFor::CastOffer {
                kind: CastOfferKind::Cascade { hit_card, .. },
                ..
            } if hit_card == hit
        ),
        "control: the untargeted shape must offer its hit; waiting_for = {}",
        describe(&runner)
    );

    runner
        .act(GameAction::CascadeChoice {
            choice: CastChoice::Cast,
        })
        .expect("accepting the cascade offer must succeed");

    assert_eq!(
        runner.state().objects[&hit].zone,
        Zone::Stack,
        "control: the untargeted hit must reach the stack; waiting_for = {}",
        describe(&runner)
    );
}
