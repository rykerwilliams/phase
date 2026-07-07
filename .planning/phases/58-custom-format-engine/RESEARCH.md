---
phase: 58-custom-format-engine
doc: RESEARCH
subsystem: engine-formats
status: research-and-design (no implementation)
---

# Phase 58 — RESEARCH

All findings below are from reading source this session. File:line citations
are given; where a search found nothing relevant that is stated explicitly.

## 1. EC ruleset (re-verified 2026-07-07, raw GitHub fetch)

Fetched `raw.githubusercontent.com/northern-information/lordsofthepit.com/main/src/pages/formats.md`.
Matches the 2026-07-07 background with two clarifications: (a) 93-94's and 95's
**legal-set lists explicitly include Collector's Edition + International
Collector's Edition** as reprint sources; (b) Eternal Chaos's mechanic is
implemented via three "boostie" cards (Booster Tutor ×4, Opening Ceremony ×4,
Summon the Pack restricted to 1) plus errata allowing tutoring from packs opened
during the match.

### Old School 93-94
- **Legal sets:** Alpha, Beta, Unlimited, Collector's Edition, International
  Collector's Edition, Arabian Nights, Antiquities, Revised, Legends, The Dark,
  Fallen Empires.
- **Restricted (1 copy):** Ancestral Recall, Balance, Black Lotus, Braingeyser,
  Chaos Orb, Channel, Demonic Tutor, Library of Alexandria, Mana Drain, Mind
  Twist, Mox Emerald, Mox Jet, Mox Pearl, Mox Ruby, Mox Sapphire, Recall,
  Regrowth, Sol Ring, Time Vault, Time Walk, Timetwister, Wheel of Fortune.
- **Banned:** Bronze Tablet, Contract from Below, Darkpact, Demonic Attorney,
  Jeweled Bird, Rebirth, Tempest Efreet.
- **Reprint policy:** non-foil reprints with original frame + art, any language;
  no proxies.
- **Legacy rules:** mana burn only. (Plus Chaos Orb / Falling Star flip Oracle,
  and a "no draws" 50-minute Chaos-Orb tiebreaker — tournament-ops, not engine.)

### Old School 95
- **Legal sets:** all of 93-94 **plus** Fourth Edition, Ice Age, Chronicles,
  Renaissance, Homelands.
- **Restricted:** 93-94's list **plus** Demonic Consultation, Mana Crypt.
- **Banned:** 93-94's list **plus** Amulet of Quoz, Timmerian Fiends.
- **Legacy rules:** mana burn only.

### Middle School
- **Legal sets:** Fourth Edition through Scourge (1995–2003).
- **Restricted:** NONE. Instead, 25 cards fully **banned:** Amulet of Quoz,
  Balance, Brainstorm, Bronze Tablet, Channel, Dark Ritual, Demonic
  Consultation, Flash, Goblin Recruiter, Imperial Seal, Jeweled Bird, Mana
  Crypt, Mana Vault, Memory Jar, Mind's Desire, Mind Twist, Rebirth, Strip Mine,
  Tempest Efreet, Timmerian Fiends, Tolarian Academy, Vampiric Tutor, Windfall,
  Yawgmoth's Bargain, Yawgmoth's Will.
- **Reprint policy:** permissive — CE/ICE, world-championship, artist proofs,
  and even modern-bordered reprints "begrudgingly" allowed.
- **Legacy rules:** mana burn **AND** damage-uses-the-stack **AND** pre-M10 wish
  templating (all three).

### Classic Magic
- **Legal sets:** Alpha through Scourge (1993–2003) — the full pre-Mirrodin pool.
- **Restricted (37):** Ancestral Recall, Balance, Black Lotus, Black Vise,
  Braingeyser, Burning Wish, Channel, Demonic Consultation, Demonic Tutor, Fact
  or Fiction, Fastbond, Flash, Gush, Imperial Seal, Library of Alexandria,
  Lion's Eye Diamond, Lotus Petal, Mana Crypt, Mana Vault, Memory Jar, Maze of
  Ith, Merchant Scroll, Mind Twist, Mind's Desire, Mox Emerald, Mox Jet, Mox
  Pearl, Mox Ruby, Mox Sapphire, Mystical Tutor, Necropotence, Regrowth,
  Shahrazad, Sol Ring, Strip Mine, Stroke of Genius, Time Walk, Timetwister,
  Tolarian Academy, Vampiric Tutor, Wheel of Fortune, Windfall, Yawgmoth's
  Bargain, Yawgmoth's Will. (List as published; count the entries as canonical.)
- **Banned:** Amulet of Quoz, Bronze Tablet, Chaos Orb, Contract from Below,
  Darkpact, Demonic Attorney, Falling Star, Jeweled Bird, Rebirth, Tempest
  Efreet, Timmerian Fiends.
- **Reprint policy:** old-bordered cards only; new-border of any kind illegal
  (proxy or not).
- **Legacy rules:** mana burn AND damage-uses-the-stack AND wish-cycle
  restoration. B&R twice yearly (Jan 1 / Jul 1).

### Eternal Chaos (stretch — not designed in depth)
Built on 93-94 base; adds Booster Tutor ×4, Opening Ceremony ×4, Summon the Pack
×1; errata to tutor from packs opened during the match; sideboard = packs;
one new pack cracked between games; all pack cards removed after match; optional
per-match "Gentleman's Agreement" banlist.

## 2. Legality-pipeline gap — CONFIRMED absent

- `card_db.rs:109` — `let normalized = normalize_legalities(&entry.legalities);`
  is the single ingest site. Source is MTGJSON `AtomicCard.legalities`
  (`oracle_gen.rs:778/814/883`).
- `LegalityFormat` (`legality.rs:12-28`) has 15 variants; **none** are
  oldschool/middleschool/classic. `from_key` (`legality.rs:69-88`) returns
  `None` for any unlisted key, and `normalize_legalities` (`legality.rs:125-137`)
  `continue`s past `None` — the key is dropped.
- The test at `legality.rs:286-313` uses `"oldschool"`-shaped names as the
  canonical example of "unknown keys are dropped".
- **Conclusion:** the four EC formats have zero per-card legality signal in the
  pipeline, and even if MTGJSON published one for `oldschool` it wouldn't
  survive normalization today. The custom-format engine must define its own
  legal-set-code + banned/restricted-name mechanism and must NOT depend on
  external per-card legality data. This is *correct* — Scryfall/MTGJSON cannot
  be relied on to track player-authored custom formats.

## 3. Set-membership + reprint policy — building block confirmed, one data gap

- `CardDatabase::printings_for(name) -> Option<&[String]>` (`card_db.rs:227-230`)
  returns set codes; backed by `printings_index` populated from the export
  `printings` field (`card_db.rs:101-103`).
- **This is the enforceable legality key**: a card is pool-legal for a custom
  format iff at least one of its printings' set codes is in the format's
  `legal_sets` list.
- **Data gap:** printings are *set codes only* — there is **no per-printing
  frame/border/art metadata** in the runtime DB. So "original frame/art only"
  (93-94) vs "old-border only" (Classic) vs "modern border begrudgingly allowed"
  (Middle School) are **not fully distinguishable** from current data. However,
  set-code membership is a *good approximation*: a modern reprint of an Alpha
  card lives in a modern set code, which is simply not in `legal_sets`, so it is
  excluded automatically. The reprint-policy nuance mainly affects special
  reprint set codes (CE/ICE/world-championship/artist-proof), which are
  themselves distinct set codes and can be added/omitted from `legal_sets` per
  format. **Recommendation:** model reprint policy as *which set codes are in the
  legal list*, and flag frame/art-level fidelity as a known limitation (needs a
  new per-printing data field if we ever want to enforce it precisely).

## 4. `DeckCopyLimit::UpTo(1)` reuse — feasible for the ceiling, WRONG layer for the source

Read `deck_validation.rs` copy-limit + restricted paths in full.

- `DeckCopyLimit` (`format.rs:100-105`) is a **card-intrinsic** override: it
  models what an individual card's *own rules text* says ("A deck can have up to
  N cards named ~", "only one copy"). It is resolved per-card from
  `face.deck_copy_limit` / Oracle text in `copy_limit_violations`
  (`deck_validation.rs:2412-2449`, esp. the `UpTo(n)` arm at 2434-2435).
- A format **restricted list** is a *format-level policy*, not a property of the
  card. Overloading `DeckCopyLimit::UpTo(1)` to carry it would conflate two
  abstraction layers — exactly the smell CLAUDE.md's "separate abstraction
  layers in enum design" warns against. (It would also break for a card that has
  BOTH a real intrinsic limit and a format restriction.)
- **The right existing building block already exists**:
  `restricted_copy_violations` (`deck_validation.rs:2462-2485`) enforces the CR
  100.2b `<= 1` ceiling **format-generally**, driven by a `restricted_canonical:
  HashSet<String>` of names. Today that set is populated from
  `LegalityStatus::Restricted` (`deck_validation.rs:388-390`). For a custom
  format we simply populate the *same* set from the format's restricted-name
  list, and reuse the *same* enforcer. Zero new copy-limit concept needed.
- **Finding:** reuse `restricted_copy_violations` (the enforcement path), NOT
  `DeckCopyLimit::UpTo`. Correct the task's framing accordingly.

## 5. Mana burn — SMALL; hook point identified

- Modern CR: **mana burn is obsolete.** `docs/MagicCompRules.txt:8277-8278`
  glossary "Mana Burn (Obsolete)": "Older versions of the rules stated that
  unspent mana caused a player to lose life… That rule no longer exists."
  (Removed by the 2010 "M10" rules update.) So implementing it is adding an
  *optional legacy rule* absent from current CR — annotate as pre-M10/removed,
  citing the obsolete-glossary entry.
- The engine already fully models unspent-mana emptying at step/phase
  boundaries: `turns.rs:264` "CR 500.5: Mana pools empty between phases/steps",
  routed through `enter_phase` → `drain_pending_phase_transition_progress`
  (`turns.rs:295`) → a `ProposedEvent::EmptyManaPool` replacement pipeline
  (`turns.rs:379`) → `apply_empty_mana_pool_decisions` (`types/mana.rs:1692`).
- **The exact hook point** is the `UnitDisposition::Drop` arm
  (`types/mana.rs:1707-1716`): each dropped unit is `player.mana_pool.mana
  .remove(...)` and emits `GameEvent::ManaPoolEmptied`. Mana burn = count the
  units actually dropped for a player during a step-end empty and, when the
  active `LegacyRuleSet.mana_burn` flag is set, deal that many damage to that
  player's owner at that same point.
- **Size: small.** One flag check + a damage application at (or just after) the
  drop site, plus a `GameEvent` for the burn. No new state machine. The infra
  (per-unit disposition, APNAP drain, replacement pipeline) already exists.
  Care needed: burn is per *point of unspent mana*, counted after replacement
  effects (Kruphix/Horizon Stone `Keep` dispositions) have run — the Drop-arm
  count already reflects that, which is why the drop site (not the pre-pipeline
  pool) is the correct hook.

## 6. "Damage uses the stack" — LARGE / deep; honest assessment

- Modern combat damage is **simultaneous and explicitly does NOT use the
  stack**: `docs/MagicCompRules.txt:2406` "CR 510.2 … This turn-based action
  doesn't use the stack. No player has the chance to cast spells or activate
  abilities between the time combat damage is assigned and the time it's dealt."
- The engine implements exactly this modern model in
  `game/combat_damage.rs` (**3,658 lines**) as a simultaneous batch
  (`resolve_combat_damage`, `combat_damage.rs:102`; batch/replacement machinery
  throughout — see the "batch" references at 814/832/862/926). `combat.rs` is a
  further 10,821 lines. `engine_combat.rs::handle_assign_combat_damage`
  (`engine_combat.rs:538`) drives assignment then calls
  `resolve_combat_damage` immediately — there is **no intermediate
  priority/stack round** between assignment and dealing.
- Pre-6th-edition "damage on the stack" put assigned combat damage **on the
  stack as a stack object** that players could respond to before it resolved.
  That is a *reversal of CR 510.2's control flow* and touches the combat step
  state machine, the stack, and priority passing — not a leaf value.
- **Size: large, and I will not guess a smaller number to look complete.** There
  is no existing hook-point for interposing priority between damage assignment
  and dealing; the immediate-dealing path is load-bearing across thousands of
  lines and hundreds of tests. This is plausibly a multi-week combat rework and
  should be treated as its own sub-project, gated behind
  `LegacyRuleSet.damage_uses_stack`, and very likely **out of the initial MVP**.
  Middle School and Classic Magic are still *playable* without it (with a
  documented rules-fidelity caveat) since it only changes response windows in
  combat.

## 7. Analogous Trace — `GameFormat::Limited` (phase 53 prior art)

From `git show 80404a98b:.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`:

Adding `GameFormat::Limited` was a single, tightly-scoped TDD change:
- Added `Limited` to `FormatGroup` and `GameFormat`.
- Added `FormatConfig::limited()` (40-card, 20 life, 2-player).
- Extended **all** exhaustive match arms: `legality_format` (`None`),
  `sideboard_policy` (`Unlimited`), `label`, `for_format`, plus the registry.
- The one "surprise" was a second exhaustive match in
  `deck_validation.rs::format_compatibility_check` that also required an arm —
  the compiler caught it (non-exhaustive match error), and it was added as a
  pass-through.
- RED→GREEN→(no REFACTOR); 8 new tests; full engine suite stayed green.

**Lessons this phase inherits:**
1. An additive `GameFormat` variant is a well-trodden, compiler-guided path —
   every exhaustive match is a checklist the compiler enforces.
2. There are **two** exhaustive-match sites to remember: `format.rs` and
   `deck_validation.rs`. Grep for `match .*format` / `GameFormat::` before
   assuming five arms.
3. Structural params (life/deck/players) live in `FormatConfig`; legality is a
   separate axis (`legality_format` → `LegalityFormat`). Our custom layer must
   respect that separation but *replace* the `LegalityFormat` axis with a
   set-list + name-list payload, because custom formats have no `LegalityFormat`.

## 8. Idiomatic-Rust note on the legacy-rules axis

Mana burn, damage-uses-stack, and pre-M10 wish templating are **independent**
binary rule-modules (93-94 = burn only; Middle School/Classic = burn + stack +
wish). They are not mutually exclusive and not orderable, so an `enum` is the
*wrong* model (it cannot express "burn + wish, no stack" without enumerating
2^N combinations). The idiomatic model is a small struct of documented `bool`
fields (or `bitflags`), each gating one independent rules module — this is the
one place a bool cluster is correct precisely because each axis is a separate
CR-era toggle. This satisfies CLAUDE.md's intent ("mana burn and
damage-uses-stack do NOT travel together… never a single old-rules boolean")
while staying honest that the members are independent switches, not a
parameterization of one axis.
