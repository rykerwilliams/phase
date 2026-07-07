---
phase: 58-custom-format-engine
doc: PLAN
subsystem: engine-formats
status: research-and-design (no implementation)
tags: [format, custom-format, legacy-rules, mana-burn]
---

# Phase 58 — PLAN

Design-only. No code is written in this phase. Below is the proposed
architecture, the custom-vs-built-in coexistence design, the delivery-surface
recommendation, and the sequencing.

## Mandatory architectural sections

### Pattern Coverage — build for the class, not the four formats

Every element below handles the *category* "data-driven format", not the four
EC formats specifically:

- **`CustomFormatDef`** is one schema instantiated N times. The four EC formats
  are four values; a future "my playgroup's Old-School-plus-Portal" is the
  N+1th value with zero engine change.
- **Legal-set membership** is `printings ∩ legal_sets ≠ ∅` — works for any set
  list, not four hardcoded pools.
- **Restricted/banned enforcement** reuses the *format-general* CR 100.2b
  enforcer (`restricted_copy_violations`) and the illegal-card path, sourced
  from name lists — works for any list.
- **`LegacyRuleSet`** is three independent rule-module toggles — works for any
  future era-rule combination, not "old rules on/off".

No arm anywhere may read `if format == OldSchool93_94`. Behavior is driven by
the resolved `CustomFormatDef` data only.

### Building Blocks — reused, not reinvented

| Need | Existing block reused | Location |
|------|----------------------|----------|
| Structural game params (life, deck size, players, sideboard) | `FormatConfig` | `types/format.rs` |
| Set codes per card | `CardDatabase::printings_for` | `card_db.rs:227` |
| Format-level 1-copy ceiling (CR 100.2b) | `restricted_copy_violations` + `restricted_canonical` set | `deck_validation.rs:2462` / `:373` |
| 4-copy default + card-intrinsic overrides (CR 100.2a) | `copy_limit_violations` | `deck_validation.rs:2412` |
| Illegal-card reporting | existing `illegal_cards` accumulation | `deck_validation.rs:372-406` |
| Step-end unspent-mana drop (mana-burn hook) | `apply_empty_mana_pool_decisions` Drop arm | `types/mana.rs:1707` |
| Format registry → frontend | `GameFormat::registry()` / `FormatMetadata` | `format.rs:326` |

New building blocks introduced (all general): `CustomFormatDef`,
`CustomFormatId`, `ReprintPolicy`, `LegacyRuleSet`, and a
`custom_format_registry()` of bundled presets.

### Logic Placement — engine owns everything

All of it lives in the `engine` crate. Deck legality, set-membership checks,
banned/restricted enforcement, and legacy-rule behavior are engine logic. The
frontend receives the resolved `CustomFormatDef` (or a display projection of it)
via the existing registry/WASM export and *renders* it — it never re-derives
legality. This matches "the engine owns all logic / the frontend is a display
layer".

### Extension vs Creation

We **extend** the existing format system, we do not fork it:
- One additive `GameFormat::Custom(CustomFormatId)` variant (mirrors the
  `GameFormat::Limited` additive-variant precedent).
- `FormatConfig` gains an `Option<CustomFormatRules>` payload — additive field,
  `None` for all official formats, serde-default so existing serialized configs
  round-trip.
- Deck validation gains one match arm that routes `Custom` to a new
  `evaluate_custom_format` that *calls the existing* copy-limit and restricted
  enforcers with a data-sourced name set.

### Analogous Trace

`GameFormat::Limited` (phase 53) — see RESEARCH.md §7. We follow its
compiler-guided "extend every exhaustive match" method exactly, and we inherit
its lesson that there are two match sites (`format.rs` + `deck_validation.rs`).

## 1. Schema — the general custom-format layer

```text
CustomFormatId(u16)                     // Copy handle; keeps GameFormat: Copy

GameFormat::Custom(CustomFormatId)      // one additive, typed variant

CustomFormatRules {                     // the resolved ruleset payload
    id: CustomFormatId,
    // structural params reuse FormatConfig's existing fields (life/deck/etc.)
    legal_sets: Vec<SetCode>,           // set codes; membership = pool legality
    reprint_policy: ReprintPolicy,
    banned: Vec<CardName>,              // fully illegal
    restricted: Vec<CardName>,          // legal, max 1 (CR 100.2b path)
    legacy: LegacyRuleSet,
}

ReprintPolicy {                         // enum — enforceable today only at set-code granularity
    OriginalPrintingsOnly,              // 93-94 / Classic intent (see limitation)
    AllowSpecialReprintSets,            // CE/ICE/world-champ/proof set codes included in legal_sets
    AllowAnyPrinting,                   // Middle School "begrudgingly"
}

LegacyRuleSet {                         // three INDEPENDENT toggles (RESEARCH §8)
    mana_burn: bool,
    damage_uses_stack: bool,
    pre_m10_wish_reaches_exile: bool,   // RESEARCH §9: Wishes reach owned face-up
                                        // exile (pre-M10 "removed from the game").
                                        // NOTE: renamed from the first-pass
                                        // placeholder `pre_m10_wish_templating`
                                        // — it is a functional POOL-SCOPE toggle,
                                        // not a wording/templating change.
}
```

**Where the payload lives.** `FormatConfig` gains
`custom_rules: Option<CustomFormatRules>` (serde `#[serde(default,
skip_serializing_if = "Option::is_none")]`). Because `FormatConfig` is already
the per-game config carried on `GameState` and serialized across the WASM/P2P
boundaries, embedding the resolved ruleset there means **no global mutable
registry** is needed at runtime — deck validation and the mana-burn hook both
read it from the config they already hold. `GameFormat` stays `Copy` (the heavy
`Vec`s live in `FormatConfig`, which is `Clone`, not the enum).

**Bundled presets** are typed constructors, exactly analogous to
`FormatConfig::premodern()`:

```text
CustomFormatDef::old_school_93_94() -> CustomFormatDef
CustomFormatDef::old_school_95()    -> extends 93-94's set/list Vecs
CustomFormatDef::middle_school()    -> restricted empty, larger banned
CustomFormatDef::classic_magic()    -> own combined lists
custom_format_registry() -> Vec<CustomFormatDef>   // parallel to GameFormat::registry()
```

(`CustomFormatDef` = display metadata + `CustomFormatRules`; the registry hands
the frontend labels/short-labels/descriptions just like `FormatMetadata`.)

## 2. Parameterizing the four EC formats as data (not four blocks)

The four formats form an incremental chain. Express it with builder-style reuse,
mirroring how `FormatConfig::pioneer()` spreads `..Self::standard()`:

- `old_school_93_94()` — base: sets = [LEA, LEB, 2ED, CED, CEI, ARN, ATQ, 3ED,
  LEG, DRK, FEM]; restricted = [22 names]; banned = [7 names]; legacy = {mana_burn}.
- `old_school_95()` — `let mut d = old_school_93_94(); d.legal_sets.extend([4ED,
  ICE, CHR, REN, HML]); d.restricted.extend([Demonic Consultation, Mana Crypt]);
  d.banned.extend([Amulet of Quoz, Timmerian Fiends]; legacy unchanged`.
- `middle_school()` — sets = Fourth Edition..Scourge; restricted = []; banned =
  [25 names]; reprint = AllowAnyPrinting; legacy = {mana_burn, damage_uses_stack,
  pre_m10_wish_reaches_exile}.
- `classic_magic()` — sets = Alpha..Scourge; restricted = [37 names]; banned =
  [11 names]; reprint = OriginalPrintingsOnly; legacy = {mana_burn,
  damage_uses_stack, pre_m10_wish_reaches_exile}.

Set codes must be verified against the engine's `set_catalog` (MTGJSON codes)
during implementation — the codes above are the expected MTGJSON codes but
must be confirmed, not assumed. Card names are validated at preset-construction
time by a unit test that asserts every banned/restricted name resolves in the
`CardDatabase` (guards against typos silently no-op'ing a ban).

## 3. Deck-legality algorithm (engine, data-driven)

`evaluate_custom_format(db, request, rules) -> CompatibilityCheck`:

1. Structural checks (deck size, sideboard) via existing `FormatConfig` fields.
2. Pool legality: for each card, `db.printings_for(name)`; legal iff any
   printing's set code ∈ `rules.legal_sets`. Else → illegal ("not legal in
   <format>"), reusing the existing `illegal_cards` accumulation shape.
3. Banned: name ∈ `rules.banned` → illegal (distinct "banned" label).
4. Restricted: name ∈ `rules.restricted` → insert into `restricted_canonical`,
   then call the **existing** `restricted_copy_violations` (CR 100.2b, `<= 1`).
5. Default 4-copy limit + card-intrinsic overrides via the **existing**
   `copy_limit_violations`.

This reuses four existing helpers verbatim and adds only the set-membership +
name-set sourcing. `GameFormat::Custom` gets one arm in
`format_compatibility_check` routing to `evaluate_custom_format`.

`legality_format()` returns `None` for `Custom` (no `LegalityFormat` mapping —
custom formats don't use the external legality table). `sideboard_policy`,
`label`, `for_format`, etc. each get a `Custom` arm reading the resolved def.

## 4. Legacy rules wiring

- **Mana burn** (`LegacyRuleSet.mana_burn`): at the step-end drop site
  (`types/mana.rs:1707`), tally dropped units per player; after the drain, if
  the flag is set, deal that many damage to the owner and emit a new
  `GameEvent::ManaBurn { player_id, amount }`. Annotate as a pre-M10 rule
  removed by the M10 update (cite the obsolete-glossary entry
  `MagicCompRules.txt:8277`). ~Small; no new state machine.
- **Pre-M10 Wish exile access** (`pre_m10_wish_reaches_exile`): fully traced in
  RESEARCH §9. This is a REAL functional difference (not wording-only): pre-M10,
  the "removed from the game" zone counted as *outside the game*, so a Wish could
  retrieve an owned card that had been removed from the game (modern: exile); the
  M10 update (CR 400.11/400.11a — "outside the game is not a zone"; only the
  sideboard is outside the game) removed this. The engine already implements the
  modern (post-M10) Wish cycle generically as `Effect::SearchOutsideGame` with
  `source_pool: OutsideGameSourcePool::Sideboard` (`types/ability.rs:246`), and
  already implements owned-face-up-exile retrieval for the Karn/Coax class via
  `OutsideGameSourcePool::SideboardAndFaceUpExile` + the tested
  `collect_face_up_exile_candidates` collector and `put_face_up_exile_into` mover
  (`game/effects/search_outside_game.rs:72,105,141`). **SMALL** (revise the prior
  "Medium"): the only change is a one-line pool-widening at the existing resolver
  hook (`search_outside_game.rs:72`) — when the flag on
  `GameState.format_config` (`types/game_state.rs:6787`) is set, treat a
  `Sideboard`-pool search as if it were `SideboardAndFaceUpExile`. No parser
  change (the flag is a runtime-resolution concern, not a parse concern), no new
  effect/state/WaitingFor, full reuse of the tested collector/mover. Annotate as
  a legacy rule reverting the M10 change (cite CR 400.11 / 400.11a / 701.23j).
- **Damage uses the stack** (`damage_uses_stack`): LARGE (RESEARCH §6). Its own
  sub-project; likely out of MVP. Gated by the flag so Middle School / Classic
  are playable without it (with a documented fidelity caveat) until it lands.

## 5. Frontend

The `custom_format_registry()` is exposed through the same WASM export path as
`GameFormat::registry()`; the client renders custom formats in the picker from
engine data (label, short-label, description, group). A new `FormatGroup`
variant (e.g. `Retro` or `Custom`) may be added for visual clustering. No
legality logic on the client.

## 6. Testing (building-block level, per CLAUDE.md)

- Set-membership legality: assert cards from in-pool and out-of-pool sets pass /
  fail — for arbitrary set lists, not just the four presets.
- Restricted path: 2 copies of a restricted-list name flags; 1 copy passes —
  driven by a synthetic def, proving the general mechanism.
- Preset integrity: every banned/restricted name in all four presets resolves in
  the DB; each preset's `legacy` matches the EC spec.
- Mana burn: unspent N mana at step end deals N with flag on, 0 with flag off —
  tests the flag+hook, not a specific card.
- Serde round-trip of `FormatConfig` with `Some(custom_rules)` and `None`.

## 7. Delivery surface — (a) UI vs (b) config vs (c) both — RECOMMENDATION (confirm with user)

- **(a) Player-facing designer UI.** A client screen to author a format
  interactively, saved/shared. *Changes:* the schema above **plus** persistence
  (where do saved formats live — server DB? user profile?), a sharing/import
  mechanism, validation UX, and a way for both players in a P2P/multiplayer game
  to agree on the exact ruleset (the host's `CustomFormatRules` must be
  authoritative and transmitted, like `FormatConfig` already is). Large surface.
- **(b) Operator/preset config.** Formats delivered as bundled, version-
  controlled preset data (the four EC formats as `CustomFormatDef` constructors),
  optionally extendable by a self-hosted instance via a config the server loads
  at startup. *Changes:* just the schema + presets + one deck-validation arm +
  the registry export. The `GATED_SETS` env-var pattern is the *rough* precedent
  for "deployment reads config", but we deliberately do **not** copy it (it's
  generation-time and narrow); presets are typed Rust constructors, audited like
  `FormatConfig::premodern()`.
- **(c) Both, one schema.** (b) first; (a) is later an editor + load-path over
  the identical `CustomFormatDef`.

**Recommendation (for the user to confirm): ship (b) now, design the schema so
(c) is the natural end state.** Reasoning: the four EC formats are known, curated
rulesets that *should* be audited, version-controlled, and test-covered as
engine data — exactly what typed bundled presets give us, and exactly the
existing `FormatConfig::premodern()` pattern. A full player-facing designer (a)
is a large, mostly-frontend + persistence + multiplayer-agreement surface that
should not gate delivering the four formats. Because the engine is data-driven
from day one (`CustomFormatDef` is the single source of truth whether authored
by a constructor or, later, a UI), (a) becomes purely additive: an editor that
emits a `CustomFormatDef` and a load path that registers it. This is the
judgment call CLAUDE.md says to surface — please confirm (b)-first before
implementation.

## 8. Sequencing

1. **General engine** — `CustomFormatId`, `CustomFormatRules`, `ReprintPolicy`,
   `LegacyRuleSet`, `GameFormat::Custom` variant + all match arms,
   `FormatConfig.custom_rules`, `evaluate_custom_format` reusing existing
   enforcers, registry export. (Compiler-guided, mirrors phase 53.)
2. **Four EC formats as data** — the four `CustomFormatDef` constructors +
   registry entries + preset-integrity tests. Validates the engine from step 1.
3. **Mana burn** — `LegacyRuleSet.mana_burn` at the drop-site hook. Small.
   Enables full fidelity for 93-94 / 95 and partial for Middle School / Classic.
4. **Pre-M10 Wish exile access** (`pre_m10_wish_reaches_exile`) — SMALL
   (RESEARCH §9); one-line pool-widening at `search_outside_game.rs:72`, gated by
   the flag, reusing the existing tested face-up-exile collector/mover. Can land
   with or just after mana burn (step 3).
5. **Damage uses the stack** — LARGE; its own sub-project; likely post-MVP.
   Middle School / Classic are playable-with-caveat until it lands.
6. **Eternal Chaos (stretch)** — depends on 93-94 existing (step 2) **plus** a
   genuinely new in-match pack-opening mechanic (Booster Tutor / Opening
   Ceremony / Summon the Pack + tutor-from-opened-packs errata + pack-based
   sideboard). Not designed here; flagged as a follow-on that is mostly a new
   *mechanic*, only lightly a new *format*.

## Risks / open items

- **Set-code verification** against `set_catalog` at implementation time (codes
  in §2 are expected-but-unconfirmed MTGJSON codes).
- **Reprint-policy fidelity** limited to set-code granularity (RESEARCH §3) —
  frame/art enforcement needs new per-printing data; flagged for the user.
- **Damage-uses-the-stack** effort is genuinely large and not fully scoped here;
  do not commit it to MVP without a dedicated combat-rework spike.
