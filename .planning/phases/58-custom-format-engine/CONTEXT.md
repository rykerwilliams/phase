---
phase: 58-custom-format-engine
doc: CONTEXT
subsystem: engine-formats
status: research-and-design (no implementation)
tags: [format, custom-format, old-school, middle-school, classic-magic, legacy-rules]
---

# Phase 58 — Custom ("Design Your Own") Format Engine — CONTEXT

## Why this matters

phase.rs today models formats as a **closed, compile-time `GameFormat` enum**
(`crates/engine/src/types/format.rs`). That is exactly the right shape for the
fixed roster of *official* formats (Standard, Commander, Premodern, …): typed,
exhaustively matched, audited, version-controlled. It is the *wrong* shape for
**player/operator-authored custom formats**, whose card pools, banned/restricted
lists, and alternate-rule toggles are open-ended data that must not require an
engine recompile and a new enum variant per format.

The goal of this phase is to design a **general, data-driven custom-format
layer** that coexists with the closed enum, and to validate that layer by
expressing **four Eternal Central (EC) retro formats as bundled preset data on
top of it**:

- Old School 93-94
- Old School 95
- Middle School
- Classic Magic

The four EC formats are the *proof*, not the *point*. The deliverable that
survives is the general engine; the four formats are its first four data
instances. Per this repo's CLAUDE.md "build for the class, not the card"
principle, we build the format *class*, then instantiate the four as data — we
do **not** hardcode four new `GameFormat` variants.

## Confirmed (verified against source this session)

- **`GameFormat` is a closed `Copy` enum** with ~23 variants, threaded through
  many exhaustive matches (`legality_format`, `sideboard_policy`,
  `grants_free_first_mulligan`, `uses_commander`, `supplies_fixed_deck`,
  `label`, `for_format`, plus `deck_validation.rs::format_compatibility_check`).
  Verified `format.rs` in full. Adding an *additive* variant is the established
  extension pattern (see the `GameFormat::Limited` prior art, phase 53).
- **Legality today is externally sourced per-card.** `card_db.rs:109` calls
  `normalize_legalities(&entry.legalities)`; the raw map comes from MTGJSON
  `AtomicCard.legalities` via the export binary (`bin/oracle_gen.rs:778`,
  `883`). `LegalityFormat::from_key` (`legality.rs:69`) **drops any key it does
  not recognize**. There is **no** `oldschool` / `middleschool` / `classic`
  variant in `LegalityFormat`, so even MTGJSON's `oldschool` key (if present) is
  silently discarded today. The existing test at `legality.rs:293-297`
  explicitly documents that unknown keys like `"oldschool"` are dropped. →
  **None of the four EC formats have any signal in the current pipeline.**
  Confirmed by reading `legality.rs`, `card_db.rs`, and `oracle_gen.rs`.
- **`set_gating.rs` does NOT fit** as a format-restriction mechanism. Confirmed
  by reading it in full: it is a `GATED_SETS`-env-var-driven, *generation-time*
  pre-release embargo tool that overrides a card's legalities to
  `all_formats_banned()`. It is narrow deployment tooling, not a runtime,
  general, per-format card-pool mechanism. Useful only as a *rough shape
  reference* for "how this codebase does deployment-level config", not an
  architecture to copy.
- **Set-membership data exists and is the right key.**
  `CardDatabase::printings_for(name) -> Option<&[String]>` (`card_db.rs:227`)
  returns the set codes a card was printed in. This is the building block a
  set-list-driven custom format needs.
- **`DeckCopyLimit::UpTo(1)` is the WRONG layer for a format restricted list**
  (see RESEARCH.md §4). The correct existing building block is the
  format-level restricted-list enforcer `restricted_copy_violations`
  (`deck_validation.rs:2462`), which already implements the CR 100.2b 1-copy
  ceiling generically.
- **Mana burn is small; "damage uses the stack" is large.** Verified hook
  points (RESEARCH.md §5). Mana burn is a localized addition at the mana-pool
  drop site. "Damage uses the stack" is a fundamental reversal of CR 510.2 and a
  deep combat/stack/priority rework.
- **Legend-rule scope change is REAL and the engine is hardcoded to modern; a
  legacy flag is SMALL — but no EC preset uses it.** Fully investigated
  (RESEARCH.md §10). The legend rule (introduced by *Legends* 1994, legal in
  93-94/95) was **global / any-controller** through 2013, then M14 (2013-07-13)
  made it **per-controller + choice** (current CR 704.5j,
  `MagicCompRules.txt:5510`). The engine's `check_legend_rule`
  (`sba.rs:902-956`) is hardcoded to the modern per-controller-with-choice form
  (loops per player, filters `controller == player_id`, pauses with
  `WaitingFor::ChooseLegend`). Re-adding the pre-M14 global-choiceless form is
  SMALL — it mirrors the existing `check_world_rule` (`sba.rs:1348`) shape and
  reuses the shared SBA departure mover. Modeled as a typed
  `LegendRuleScope { Modern, PreM14AnyController }` enum on `LegacyRuleSet` (not a
  bool). **HONEST CAVEAT:** EC's published rulesets do **not** list a legend-rule
  reversion (their only legacy exceptions are mana burn / damage-on-stack /
  wish), so all four EC presets default to `Modern`; the scope enum ships as a
  *general* historical-rules axis (like Block Constructed's `mana_burn`), not an
  EC-preset behavior. Planeswalker uniqueness needs no flag — the four pools end
  at Scourge (2003) and planeswalkers postdate that (Lorwyn 2007). The
  planeswalker-uniqueness → legend-rule fold happened at **Ixalan (2017-09-28)**,
  not Dominaria 2018.
- **Pre-M10 Wish templating is small and is a REAL functional difference.**
  Fully investigated (RESEARCH.md §9). It reverts the M10 change that made exile
  an in-game zone (CR 400.11/400.11a): pre-M10, Wishes could retrieve an owned
  card removed from the game, not just from the sideboard. The engine already
  implements the modern (post-M10) Wish cycle generically
  (`Effect::SearchOutsideGame`, `OutsideGameSourcePool::Sideboard`) AND already
  implements owned-face-up-exile retrieval for the Karn/Coax class
  (`SideboardAndFaceUpExile` + tested collector/mover in
  `search_outside_game.rs`). The legacy flag is therefore a one-line pool-widening
  at one existing resolver hook — SMALL, not the "Medium" the first pass guessed.
  Flag renamed `pre_m10_wish_templating` → `pre_m10_wish_reaches_exile` (it is a
  pool-scope toggle, not a wording change).

## Open (needs a human decision — do NOT resolve unilaterally)

1. **Delivery surface** — player-facing format designer UI (a), operator/preset
   config (b), or both over one schema (c). PLAN.md §7 lays out all three and
   makes a recommendation, but the final call is the user's.
2. **Reprint-policy fidelity.** The engine has set codes per printing but **no
   frame/art metadata per printing** (RESEARCH.md §3). "Original frame/art only"
   is not fully enforceable from current data; set-code-list membership is the
   enforceable approximation. Whether that approximation is acceptable, or
   whether printing-level frame data must be ingested, is a product decision.
3. **Classic Magic B&R cadence.** EC updates Classic's banlist twice yearly
   (Jan 1 / Jul 1). Bundled-preset data is version-controlled, so updates are
   ordinary edits — but whether we want a dated/versioned banlist history is
   open.

## Source data

- **Authoritative EC ruleset**, re-verified this session (2026-07-07) against
  `https://github.com/northern-information/lordsofthepit.com/blob/main/src/pages/formats.md`
  (raw fetched). Full verbatim card lists captured in RESEARCH.md §1.
- **Prior art**: `GameFormat::Limited` planning cycle, phase 53. Retrieved via
  `git show 80404a98b:.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`.
  Summarized in RESEARCH.md §7 (Analogous Trace).

## Relationship to adjacent work — scope boundaries (do NOT accommodate here)

- **Vanguard (CR 902) is orthogonal to this design — do not entangle them.**
  GitHub issue phase-rs/phase#5056 ("Implement the Vanguard variant (CR 902)")
  requests Vanguard support; verified **still OPEN and unaddressed**
  (`gh issue view 5056 --json state` → `"OPEN"`, 2026-07-07). Vanguard is
  genuinely unimplemented (no `CoreType::Vanguard`, no `GameFormat::Vanguard`, no
  Vanguard cards in `card-data.json`). Per the issue's own analysis, phase.rs
  already implements **three of the four** CR "nontraditional card lives in the
  command zone" casual variants — Planechase (CR 901, `game/planechase.rs`),
  Commander (CR 903, `game/commander.rs`), Archenemy (CR 904, `game/archenemy.rs`)
  — and Vanguard (CR 902) is "structurally the simplest of the four… a per-player,
  game-long static modifier plus a command-zone ability source, which is a strict
  subset of what archenemy.rs/planechase.rs already do." **Vanguard therefore
  belongs to the existing command-zone-supplemental-card family, NOT to the
  `CustomFormatDef`/`LegacyRuleSet` mechanism designed here.** The two are
  independent: this custom-format engine neither depends on nor blocks Vanguard,
  and this design does **not** need to accommodate it. Flagged so a reader does
  not mistakenly try to fold Vanguard into the custom-format layer.

## Stretch goal (explicitly lower priority — do not design in depth)

- **Eternal Chaos** (a Lords-of-the-Pit variant on top of 93-94, NOT an
  EC-defined format): in-match booster-pack tutoring, a dynamically-built
  sideboard from opened packs, and a pre-match "Gentleman's Agreement" banlist.
  Depends on 93-94 already existing **plus** a genuinely new in-match
  pack-opening mechanic. Sequenced last; see PLAN.md §8.
