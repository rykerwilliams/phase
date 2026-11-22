# Card backlog — generated from `backlog/watchlist.txt`

> **Working this? Read [`OLD-CARD-RUNBOOK.md`](OLD-CARD-RUNBOOK.md) first**, or just run `/backlog-batch`.

_Generated 2026-11-22 against `upstream/main` `429c5df26e` · 1667 open issues · watchlist resolves to 6595 cards_

**Do not hand-edit** — regenerate with `python3 backlog/scan.py`. To change what is tracked, edit `backlog/watchlist.txt`.

| verdict | count | meaning |
|---|---:|---|
| **LIVE** | 102 | No signal that it is fixed. Best candidates. |
| partial-coverage | 246 | Card appears in some test; nothing ties a fix to THIS issue. |
| CHECK-DIRECTION | 42 | A commit/test cites the issue — but a commit can cite an issue to **fix**, **defer**, be **blocked on**, or **file** it. Only the first means fixed. Run the direction check before believing this bucket. |

```bash
git log -1 --format='%b' <sha> | grep -B2 -A3 '#<N>\b'   # the direction check
```

★ = a card you explicitly named in the watchlist.


## LIVE — best candidates (102)

| issue | card(s) | title | labels |
|---|---|---|---|
| [#4731](https://github.com/phase-rs/phase/issues/4731) | Reins of Power (1998) | Reins of Power targeting incorrectly — [[Reins of power]] is giving the casting player contr... | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#9862](https://github.com/phase-rs/phase/issues/9862) | Kamahl's Summons (2002), Temporary Truce (1997) | Per-player "this way" counts: Kamahl's Summons creates no Bears; Truce and Temporary Truce g... | area:engine, priority:p2-wrong-game-result |
| [#9843](https://github.com/phase-rs/phase/issues/9843) | Mundungu (1997) | Mundungu: "unless its controller pays {1} and 1 life" lowers to a flat {1} | area:parser, priority:p2-wrong-game-result |
| [#7431](https://github.com/phase-rs/phase/issues/7431) | Mist of Stagnation (2002) | Mist of Stagnation — "chooses a permanent for each card in their graveyard" is unparsed; "un... | status:confirmed, area:parser, priority:p3-card-specific |
| [#6771](https://github.com/phase-rs/phase/issues/6771) | Breakthrough (2002) | Breakthrough card not working correctly — it lets you draw 4 cards but doesn't make you disc... | status:confirmed, area:engine, area:parser |
| [#6770](https://github.com/phase-rs/phase/issues/6770) | Manabond (1998) | Manabond card not working correctly — it triggers at the end of the turn, discard correctly ... | status:confirmed, area:engine, area:parser |
| [#5654](https://github.com/phase-rs/phase/issues/5654) | Plagiarize (2002) | Notion Thief + Plagiarize: compound 'skips that draw and you draw' substitute drops to Unimp... | status:confirmed, area:engine, area:parser |
| [#4509](https://github.com/phase-rs/phase/issues/4509) | Lost in Thought (2002) | Lost in Thought ignore-effect escape clause dropped (cluster 36) | status:confirmed, area:engine, area:parser |
| [#9860](https://github.com/phase-rs/phase/issues/9860) | Raiding Party (1994) | Raiding Party: every Plains is destroyed even when each player taps white creatures | area:engine, priority:p3-card-specific |
| [#9856](https://github.com/phase-rs/phase/issues/9856) | Chromatic Armor (1995) | Chromatic Armor: "sources of the last chosen color" has no representation | area:parser, priority:p3-card-specific |
| [#5273](https://github.com/phase-rs/phase/issues/5273) | Squallmonger (1999) | Squallmonger — Cool card played by the AI. | status:needs-repro, area:ai, priority:p4-ui-polish |
| [#7742](https://github.com/phase-rs/phase/issues/7742) | Need for Speed (2001) | need for speed | status:confirmed, area:engine |
| [#11217](https://github.com/phase-rs/phase/issues/11217) | Drop of Honey (1993) | Drop of Honey / Porphyry Nodes: "destroy the creature with the least power" parses as Destro... | area:parser |
| [#11206](https://github.com/phase-rs/phase/issues/11206) | Cannibalize (1998) | Cannibalize: counters go to the exiled creature instead of the other target | — |
| [#11199](https://github.com/phase-rs/phase/issues/11199) | Duct Crawler (1998) | [Card Bug] "can't block this creature this turn" (activated or granted) drops the attacker: ... | — |
| [#11148](https://github.com/phase-rs/phase/issues/11148) | Spoils of Evil (1995) | An unparsed "for each" count leaves the second half of a compound body outside the Unimpleme... | — |
| [#11079](https://github.com/phase-rs/phase/issues/11079) | Fade Away (1998) | Killing Wave / Fade Away: per-creature 'unless' resolves one instance at a time instead of c... | — |
| [#11078](https://github.com/phase-rs/phase/issues/11078) | Read the Runes (2002) | Read the Runes: sacrifices and discards are interleaved per card instead of all sacrifices b... | — |
| [#10974](https://github.com/phase-rs/phase/issues/10974) | Catalyst Stone (2001) | [Card Bug] Catalyst Stone parses as two printed "Flashback {0}" keywords instead of flashbac... | — |
| [#10944](https://github.com/phase-rs/phase/issues/10944) | Dwarven Sea Clan (1995), Seasinger (1997) | Whose-controller non-damage predicates dropped: Seasinger lying-green, Dwarven Sea Clan, Lul... | — |
| [#10894](https://github.com/phase-rs/phase/issues/10894) | Teferi's Realm (1997) +1 | Parser: "that player" in each player's/each opponent's step triggers lowers to the controlle... | — |
| [#10844](https://github.com/phase-rs/phase/issues/10844) | Rootwater Shaman (1997) | "As though they had flash" misparsed on Rootwater Shaman, Arlinn [+1], Elsha of the Infinite | — |
| [#10817](https://github.com/phase-rs/phase/issues/10817) | Quicksilver Fountain (2003) | RemoveCounter leftovers: Quicksilver Fountain, Overseer of Vault 76, X counts (Cemetery Dese... | — |
| [#10754](https://github.com/phase-rs/phase/issues/10754) | Scythe of the Wretched (2003) | Scythe of the Wretched: creature dealt damage by the equipped creature dies, but is not retu... | — |
| [#10709](https://github.com/phase-rs/phase/issues/10709) | Psychic Theft (2000) | [engine] Delayed return of "that creature" may fall back to its own source when nothing was ... | — |
| [#10423](https://github.com/phase-rs/phase/issues/10423) | Elvish Soultiller (2003) | Elvish Soultiller: the chosen type may not bind once Soultiller has left the graveyard, so i... | — |
| [#10320](https://github.com/phase-rs/phase/issues/10320) | Cabal Therapy (2002) | AI cabal therapy | — |
| [#10319](https://github.com/phase-rs/phase/issues/10319) | Cabal Therapy (2002) | Game log cabal therapy | — |
| [#10273](https://github.com/phase-rs/phase/issues/10273) | Last Rites (2001) | Last Rites does not bind hand-choice cardinality to cards discarded this way | — |
| [#10187](https://github.com/phase-rs/phase/issues/10187) | Krark's Thumb (2003) | Krark's Thumb: keep choices are made flip by flip, not after all simultaneous flips are know... | — |
| [#10107](https://github.com/phase-rs/phase/issues/10107) | Infernal Harvest (1997) | Infernal Harvest is marked supported while its variable return cost loses X | — |
| [#9888](https://github.com/phase-rs/phase/issues/9888) | Frankenstein's Monster (1994) | Frankenstein's Monster: per-exiled-card choice of +2/+0, +1/+1 or +0/+2 counter unsupported | — |
| [#9801](https://github.com/phase-rs/phase/issues/9801) | Ashnod's Altar (1999) | Activating a mana-cost ability opens no mana-ability window; it is rejected when auto-pay fa... | — |
| [#9740](https://github.com/phase-rs/phase/issues/9740) | Shadowbane (1996) | Shadowbane loses controlled-recipient union and black-source prevention rider condition | — |
| [#9735](https://github.com/phase-rs/phase/issues/9735) | Mind Bomb (1997) | Mind Bomb subtracts the total discarded by all players instead of each player's own count | — |
| [#9731](https://github.com/phase-rs/phase/issues/9731) | Contamination (1998), Ritual of Subdual (1995) | Contamination + Ritual of Subdual: tapping a Forest adds {G}; the CR 616.1 order choice is s... | — |
| [#9515](https://github.com/phase-rs/phase/issues/9515) | Sporogenesis (1998) | Sporogenesis: "for each fungus counter on that creature" binds to ObjectScope::Target in a t... | — |
| [#9214](https://github.com/phase-rs/phase/issues/9214) | Veiled Apparition (1998) | Parser: animation "creature with <keyword> and \"<ability>\"" drops the keyword silently (Hi... | — |
| [#9123](https://github.com/phase-rs/phase/issues/9123) | Reconstruction (1994) | bunch of red exile spells — advance reconstruction - allows to play the milled card in grave... | status:needs-triage |
| [#9072](https://github.com/phase-rs/phase/issues/9072) | Abomination (1995) | Mayhem doesn't trigger off Currency Converter — I discarded Abomination and exiled it with C... | status:needs-triage |
| [#9071](https://github.com/phase-rs/phase/issues/9071) | Defense Grid (2003) | Defense Grid's Cost Increase — [[Defense Grid]] spells cost increasing ability affect the pl... | status:needs-triage |
| [#9068](https://github.com/phase-rs/phase/issues/9068) | Wheel of Torture (1999) | Wheel of Torture Reversal — Wheel of Torture still deals 3 damage despite there being more t... | status:needs-triage |
| [#9067](https://github.com/phase-rs/phase/issues/9067) | Bubbling Muck (1999) | Bubbling Muck not working correctly — Bubbling Muck does not give the additional mana when t... | status:needs-triage |
| [#9062](https://github.com/phase-rs/phase/issues/9062) | Dreamborn Muse (2003) | Dreamborn Muse — Isn't triggering ability on upkeep. | status:needs-triage |
| [#8993](https://github.com/phase-rs/phase/issues/8993) | Plaguebearer (1998) | Great Unclean One — Should create a Plaguebearer of Nurgle for each opponent with less life ... | status:needs-triage |
| [#8975](https://github.com/phase-rs/phase/issues/8975) | Turnabout (1998) | Turnabout does not let choose a player and resolves with no effect — When casting [[Turnabou... | status:needs-triage |
| [#8840](https://github.com/phase-rs/phase/issues/8840) | Skirk Drill Sergeant (2003) | Skirk Drill Sergeant: failed {2}{R} payment reanimates the dying Goblin | — |
| [#8526](https://github.com/phase-rs/phase/issues/8526) | Coral Fighters (1996), Sealed Fate (1996) | parser: "defending player's" and "target opponent's" library reads bind the controller (Cora... | — |
| [#8453](https://github.com/phase-rs/phase/issues/8453) | Syncopate (2001) | Syncopate does not respect paying with Gilded Goose — In the attached game state AI will att... | status:needs-triage |
| [#8433](https://github.com/phase-rs/phase/issues/8433) | Credit Voucher (1999) | Credit Voucher Ability — Steps to Reproduce: Casting Credit Voucher and paying cost to use a... | status:needs-triage |
| [#8402](https://github.com/phase-rs/phase/issues/8402) | Auriok Steelshaper (2003) | Auriok steelshaper — Keeps targeting even though it doesn't have an activated ability. | status:needs-triage |
| [#7902](https://github.com/phase-rs/phase/issues/7902) | Tangle Wire (2000) | Tangle Wire — During their upkeep, the opponent does not choose which permanents to tap. | status:needs-triage |
| [#7854](https://github.com/phase-rs/phase/issues/7854) | Superior Numbers (1996) | Superior Numbers — SN sorcery cast by opp would have dealt 1 damage to one target of my crea... | status:needs-triage |
| [#7850](https://github.com/phase-rs/phase/issues/7850) | Stitch Together (2002) | Stitch Together  bug — This card seems bugged atm. | status:needs-triage |
| [#7460](https://github.com/phase-rs/phase/issues/7460) | Thran Tome (1997) | Parser: ChooseFromZone chooser defaults to Controller where the card names an opponent (Intu... | — |
| [#7458](https://github.com/phase-rs/phase/issues/7458) | Choking Vines (1997) +1 | Engine: DamageAll/DestroyAll tracked-set consumers are invisible to next_sub_needs_tracked_s... | — |
| [#4131](https://github.com/phase-rs/phase/issues/4131) | Illicit Auction (1999), Mages' Contest (2000) | engine: open-bid life auction unimplemented (Illicit Auction, Pain's Reward, Mages' Contest) | area:engine, area:parser |
| [#2814](https://github.com/phase-rs/phase/issues/2814) | Decompose (2001) | [Refactor] Decompose casting.rs into CR 601.2-aligned submodules — split 41k-line casting mo... | area:engine |
| [#7456](https://github.com/phase-rs/phase/issues/7456) | Song of Blood (1997) | Parser: CreateDelayedTrigger's hand-set `uses_tracked_set: false` leaves 9 cards' inner trac... | status:confirmed, area:engine, area:parser |
| [#3671](https://github.com/phase-rs/phase/issues/3671) | Inspirit (2002) | Simulacrum Synthesizer — **Steps to Reproduce:** I had **Simulacrum Synthesizer** on the bat... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#6659](https://github.com/phase-rs/phase/issues/6659) | Feedback (1997) | Deck builder copy-limit affordance: alias spellings counted separately, search-add ungated | status:confirmed, area:engine, area:deckbuilder |
| [#11209](https://github.com/phase-rs/phase/issues/11209) | Blaze of Glory (1993) | Berserker's Frenzy: "before combat or during combat before blockers are declared" parses as ... | — |
| [#11074](https://github.com/phase-rs/phase/issues/11074) | Hellfire (1994) | Merged (mutated) permanent exiled by an effect counts once per component for "for each perma... | — |
| [#11064](https://github.com/phase-rs/phase/issues/11064) | Raiding Party (1994) | Disciple of Caelus Nin: "that weren't chosen this way" is dropped, so every other permanent ... | — |
| [#10842](https://github.com/phase-rs/phase/issues/10842) | Bomb Squad (2001) | PutCounterAll ordering profile records no population reads (same-event trigger ordering) | — |
| [#10835](https://github.com/phase-rs/phase/issues/10835) | Crypt Cobra (1996), Marsh Viper (1997) | AI poison classifier misses defending-player, triggering-player and parent-target-controller... | — |
| [#10797](https://github.com/phase-rs/phase/issues/10797) | Divine Intervention (1994) | 'When you remove a counter' trigger matches counter removal by any player | — |
| [#10764](https://github.com/phase-rs/phase/issues/10764) | Mindslaver (2003) | Control of a team ends when one of its players leaves (shared team turns) | — |
| [#10725](https://github.com/phase-rs/phase/issues/10725) | Animate Wall (1999), Coral Net (2002), Decomposition (1996) +3 | [Card Bug] Enchant clauses the keyword parser can't read are dropped from the card data | — |
| [#10673](https://github.com/phase-rs/phase/issues/10673) | Jovial Evil (1994) | Parser: where-X count's controller anaphor ignores a DECLARED-TARGET antecedent (ctx-free qu... | — |
| [#10486](https://github.com/phase-rs/phase/issues/10486) | Reconstruction (1994) | [Engine Bug] cap_distribution_target_slots: a later required target slot is truncated with t... | — |
| [#10375](https://github.com/phase-rs/phase/issues/10375) | Terminate (2001) | max_speed_standard_cards_ten_card_matrix test takes ~90s and times out under CI load | — |
| [#10233](https://github.com/phase-rs/phase/issues/10233) | Blood Oath (1999), Keeper of the Flame (1998), Planeswalker's Fury (2001) | ability_rw::target_recipient classifies DealDamage to a declared player ("that player") as a... | — |
| [#10162](https://github.com/phase-rs/phase/issues/10162) | Krark's Thumb (2003) | FlipCoins loses remaining logical flips when a selected branch pauses | — |
| [#10131](https://github.com/phase-rs/phase/issues/10131) | Benalish Hero (1997) | Shared-team block target map omits legal defense of a teammate | — |
| [#9987](https://github.com/phase-rs/phase/issues/9987) | Seton's Desire (2001), Stone-Tongue Basilisk (2001), Storage Matrix (1999) | "As long as <cond>, <unrecognized effect>" yields an empty conditional Continuous static wit... | — |
| [#9932](https://github.com/phase-rs/phase/issues/9932) | Spatula of the Ages (1998) | parser: two target-parse sites drop TargetFallback diagnostics for a target that survives (r... | — |
| [#9785](https://github.com/phase-rs/phase/issues/9785) | Edgewalker (2003) | [Card Bug] (latent) Spell cost-reduction election locks a sampled plan silently when every s... | — |
| [#9773](https://github.com/phase-rs/phase/issues/9773) | Squandered Resources (1997) | [Card Bug] (latent) A mana ability's Phyrexian cost paid from the floating pool (plan path) ... | — |
| [#9752](https://github.com/phase-rs/phase/issues/9752) | Grim Reminder (2003) | Read "each player/opponent who …" relative clauses (Kefka, Kynaios and Tiro, Mog, Infernal O... | — |
| [#9675](https://github.com/phase-rs/phase/issues/9675) | Kaervek's Purge (1996) | AI never casts X-cost removal whose target filter depends on X: the pre-cast gate checks tar... | — |
| [#9648](https://github.com/phase-rs/phase/issues/9648) | Hidden Ancients (1998), Hidden Gibbons (1999), Hidden Guerrillas (1998) +18 | Opal/Hidden/Veiled enchantments: "it becomes a creature" binds the triggering object, and th... | — |
| [#9601](https://github.com/phase-rs/phase/issues/9601) | Balance of Power (2003), Keeper of the Beasts (1998) | "If they control fewer lands than you, ... equal to the difference" parses with no condition... | — |
| [#9589](https://github.com/phase-rs/phase/issues/9589) | Flame Wave (1998), Flaming Gambit (2002), Goblin Lyre (1995) +1 | "creature that player or that planeswalker's controller controls" parses with no controller ... | — |
| [#9588](https://github.com/phase-rs/phase/issues/9588) | Heart of Bogardan (1997) | "deals N damage to target player and each creature (and planeswalker) that player controls" ... | — |
| [#9437](https://github.com/phase-rs/phase/issues/9437) | Spellshock (1998) | Stuck decision: CastOffer | — |
| [#9306](https://github.com/phase-rs/phase/issues/9306) | Terminate (2001) | ChooseFromZone chooser departure bypasses selection settlement and continuation semantics | — |
| [#9303](https://github.com/phase-rs/phase/issues/9303) | Terminate (2001) | Eliminating a ChooseOneOfBranch chooser drops the branch payload and continuation | — |
| [#9048](https://github.com/phase-rs/phase/issues/9048) | Repercussion (1999) | Hansk, Slayer Zealot ability problem — Hello! | status:needs-triage |
| [#8985](https://github.com/phase-rs/phase/issues/8985) | Mesmeric Orb (2003) | AI targeting logic wonkiness — I'm sure there are numerous issues with AI across all "diffic... | status:needs-triage |
| [#8910](https://github.com/phase-rs/phase/issues/8910) | Sneak Attack (1998) | Forward forwarded zone-choice results through re-paused battlefield entry | — |
| [#8906](https://github.com/phase-rs/phase/issues/8906) | Dominaria's Judgment (2001) | semantic-audit: DroppedCondition can't see conditions on nested static_abilities, flagging 8... | — |
| [#8862](https://github.com/phase-rs/phase/issues/8862) | Planar Guide (2003) | Tracked-set returns are silently dropped for singular ChangeZone delayed triggers | — |
| [#8741](https://github.com/phase-rs/phase/issues/8741) | Fickle Efreet (2000), Rogue Skycaptain (1996), Rohgahh of Kher Keep (1994) | Akroan Horse: ETB chooses an opponent but fails to transfer control | — |
| [#8653](https://github.com/phase-rs/phase/issues/8653) | Feedback (1997) | P2P hosting fails on Linux desktop: WebKitGTK's enable-webrtc defaults to false and wry neve... | — |
| [#8449](https://github.com/phase-rs/phase/issues/8449) | Reflexes (2003) | Taskmaster, Mercenary Mimic — able to copy a creature on the battlefield | status:needs-triage |
| [#7864](https://github.com/phase-rs/phase/issues/7864) | Krosan Tusker (2002) | Ellie and Alan, Paleontologists — The Active Abillity of the Card is not working. | status:needs-triage |
| [#7468](https://github.com/phase-rs/phase/issues/7468) | Choking Vines (1997), Energy Arc (1996), Shower of Coals (2001) +2 | Engine: 5 tracked-set consumer shapes are invisible to `next_sub_needs_tracked_set`, so prod... | — |
| [#7466](https://github.com/phase-rs/phase/issues/7466) | Bamboozle (2001) | Engine: the tracked-set publish arm for head `Reveal` is unshipped — 0 observable fixes, and... | — |
| [#7464](https://github.com/phase-rs/phase/issues/7464) | Terminate (2001) | Engine: the tracked-set publish arm for head `TargetOnly` is unshipped — 82 gated rows, the ... | — |
| [#3042](https://github.com/phase-rs/phase/issues/3042) | Riptide Shapeshifter (2002) | Extend RevealUntil parser coverage (+ multi-match count) for "reveal until you reveal …" cards | area:engine, area:parser |
| [#2816](https://github.com/phase-rs/phase/issues/2816) | Terminate (2001) | feat(engine): multi-match Ripple — cast all same-named revealed cards (CR 702.60a) | area:engine |

## Partial coverage — verify what the test asserts (246)

| issue | card(s) | title | labels |
|---|---|---|---|
| [#6377](https://github.com/phase-rs/phase/issues/6377) | Isochron Scepter (2003) | Isochron scepter used on opponents turn broke game — [[isochron scepter]] | status:needs-repro, area:engine, priority:p0-softlock |
| [#8101](https://github.com/phase-rs/phase/issues/8101) | Candelabra of Tawnos (1994) | High-trigger-volume interactions (e.g. Candelabra of Tawnos, X≈80) cause multi-minute engine... | status:confirmed, area:engine, priority:p1-core-mechanic |
| [#8078](https://github.com/phase-rs/phase/issues/8078) | Wash Out (2000) | Wash Out — bounces all permanents instead of only the chosen color | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#1102](https://github.com/phase-rs/phase/issues/1102) | Doomsday (1999) | Doomsday — My opponent cast Doomsday and exiled a few cards from their deck (they were left ... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#9840](https://github.com/phase-rs/phase/issues/9840) | Blackmail (2002), Cabal Interrogator (2003), Hollow Specter (2003) | Blackmail, Hollow Specter, Cabal Interrogator: "reveals X cards from their hand and you choo... | area:parser, priority:p2-wrong-game-result |
| [#698](https://github.com/phase-rs/phase/issues/698) | Dark Ritual (1999), Victimize (1998) | Cards that did not work during a play through — Victimize and dark ritual both went to grave... | status:needs-repro, area:engine, priority:p2-wrong-game-result |
| [#8134](https://github.com/phase-rs/phase/issues/8134) | Mountain (2003) | Revealed cards stay visible even after the information should no longer be current (Mountain... | status:confirmed, area:frontend, priority:p3-card-specific |
| [#7435](https://github.com/phase-rs/phase/issues/7435) | Delirium (1996) | Pick the Brain — the delirium multi-zone same-name search is unparsed, so `ChangeZone` reads... | status:confirmed, area:parser, priority:p3-card-specific |
| [#7427](https://github.com/phase-rs/phase/issues/7427) | Delirium (1996) | Invasive Surgery — the delirium multi-zone same-name search is unparsed, so `ChangeZone` rea... | status:confirmed, area:parser, priority:p3-card-specific |
| [#5914](https://github.com/phase-rs/phase/issues/5914) | City of Brass (2003) | City of Brass Autopass — The game doesn't autopass for me when I have no abilities or spells... | status:confirmed, area:engine, area:frontend |
| [#8088](https://github.com/phase-rs/phase/issues/8088) | Override (2003) | Volrath, the Shapestealer — copy ability drops the "except it's 7/5" override | status:needs-repro, area:engine, priority:p3-card-specific |
| [#6484](https://github.com/phase-rs/phase/issues/6484) | Peregrine Drake (1998), Tortured Existence (1998) | Hashaton/Peregrine Drake/Tortured Existence. — Im not able to select peregrine drake as the ... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#6001](https://github.com/phase-rs/phase/issues/6001) | Serra Avatar (1998) | Aethermage's touch — Steps to Reproduce: Serra Avatar was cheated out with Aethermage's touch. | status:needs-repro, area:engine, priority:p3-card-specific |
| [#5969](https://github.com/phase-rs/phase/issues/5969) | Harrow (2000) | Harrow / Automatic mana tapper — Steps to Reproduce: | status:needs-repro, area:engine, area:frontend |
| [#5238](https://github.com/phase-rs/phase/issues/5238) | Forgotten Ancient (2003) | Forgotten Ancient Delve — Casting Tasigur, the Golden Fang does not trigger Forgotten Ancient. | status:needs-repro, area:engine, priority:p3-card-specific |
| [#4965](https://github.com/phase-rs/phase/issues/4965) | Biorhythm (2002) | cannot cast biorhythm — 8 mana is plenty | status:needs-repro, area:engine, priority:p3-card-specific |
| [#4748](https://github.com/phase-rs/phase/issues/4748) | Oblation (2002) | Oblation — Shuffled my nonland permanent into my deck but did not have me draw two cards in ... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#4228](https://github.com/phase-rs/phase/issues/4228) | Reconnaissance (1998) | reconnaissance — not working as it should. | status:needs-repro, area:engine, priority:p3-card-specific |
| [#3658](https://github.com/phase-rs/phase/issues/3658) | Mana Vault (1997) | Mana Vault (paying even though its not tapped) — I think when i first summoned the card I ta... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#7731](https://github.com/phase-rs/phase/issues/7731) | Overload (2000) | Winds of Abandon overload | status:confirmed, area:engine |
| [#11208](https://github.com/phase-rs/phase/issues/11208) | Acidic Dagger (1996) | Acidic Dagger: "Activate only before blockers are declared" is dropped by the parser (CR 602.5) | — |
| [#11173](https://github.com/phase-rs/phase/issues/11173) | Force Bubble (2003) | Force Bubble: two Bubbles get a per-source choice instead of one per batch; coverage no long... | — |
| [#11066](https://github.com/phase-rs/phase/issues/11066) | Lotus Vale (1997), Scorched Ruins (1997) +6 | Lotus Vale, Scorched Ruins and the other sacrifice-Karoo lands are modeled as an optional "m... | — |
| [#11042](https://github.com/phase-rs/phase/issues/11042) | Blood Pet (2001) | [Card Bug] Underworld Breach + Think Twice: the flashback cast auto-sacrifices Blood Pet (st... | — |
| [#10926](https://github.com/phase-rs/phase/issues/10926) | Animate Land (2000) | AI refuses a land-animation spell when it controls lands but no creature (Animate Land) | — |
| [#10909](https://github.com/phase-rs/phase/issues/10909) | Soul Warden (1998) | Garruk's Uprising misses Admiral Brass's 4/4 return when Soul Warden is also on the battlefi... | — |
| [#10891](https://github.com/phase-rs/phase/issues/10891) | Sphere of Resistance (1998) | Primal Prayers' {E} alternative cost skips cost increases (Sphere of Resistance, CR 118.9d) | — |
| [#10880](https://github.com/phase-rs/phase/issues/10880) | Show and Tell (1998) | Show and Tell: Containment Priest put by one player exiles another player's simultaneously p... | — |
| [#10862](https://github.com/phase-rs/phase/issues/10862) | Platinum Angel (2003) | AI poison clock scores lethal against a seat that can't lose the game (Platinum Angel) | — |
| [#10770](https://github.com/phase-rs/phase/issues/10770) | Thorn Elemental (2003) | Client never offers "assign combat damage as though it weren't blocked" (Thorn Elemental) | — |
| [#10750](https://github.com/phase-rs/phase/issues/10750) | Skirk Prospector (2002) | Repeat-N activation for sacrifice-for-mana outlets (sacrifice N Goblins to Skirk Prospector ... | — |
| [#10749](https://github.com/phase-rs/phase/issues/10749) | Skirk Prospector (2002) | Allow explicit mana-source selection during ManaPayment when auto-pay can already finish (e.... | — |
| [#10748](https://github.com/phase-rs/phase/issues/10748) | Ashnod's Altar (1999), Phyrexian Altar (2000), Skirk Prospector (2002) +1 | [Card Bug] Mana-ability sacrifice costs prompt "sacrifice up to 1" and an illegal Skip (Skir... | — |
| [#10732](https://github.com/phase-rs/phase/issues/10732) | Overgrowth (1998) | Effect-payment capacity counts Overgrowth as one bonus mana instead of two | — |
| [#10708](https://github.com/phase-rs/phase/issues/10708) | Academy Rector (1999) | [engine] Departed-source referents outside #10699's inferred-anaphor class (Academy Rector, ... | — |
| [#10695](https://github.com/phase-rs/phase/issues/10695) | Cruel Fate (1997) | [Card Bug] Cruel Fate, Ransack: the chosen cards' destination is dropped and only one card i... | — |
| [#10560](https://github.com/phase-rs/phase/issues/10560) | Blood Moon (2003) | Scope proposal: board-dependent layer-4 ordering for Blood Moon and Urborg | — |
| [#10514](https://github.com/phase-rs/phase/issues/10514) | Kaervek's Spite (1997) | Payer can't choose the order of Kaervek's Spite's commit-time cost legs (CR 601.2h) | — |
| [#10228](https://github.com/phase-rs/phase/issues/10228) | Haunting Echoes (2001) | Haunting Echoes: basic-land exclusion dropped, per-card "all cards with the same name" searc... | — |
| [#10225](https://github.com/phase-rs/phase/issues/10225) | Haunting Echoes (2001) | "Search that player's library" searches the caster's library when "that player" comes from a... | — |
| [#10224](https://github.com/phase-rs/phase/issues/10224) | Override (2003) | Spirit Water Revival: the spell's own "Exile ~" line is skipped when its multi-clause "inste... | — |
| [#10207](https://github.com/phase-rs/phase/issues/10207) | Desperate Gambit (1997) | Desperate Gambit: current Oracle text offers no source choice, flips twice, and its lose bra... | — |
| [#10190](https://github.com/phase-rs/phase/issues/10190) | Ashnod's Altar (1999), Mindless Automaton (1998) +1 | Activation affordability ignores mana from sacrifice-cost mana abilities (Mindless Automaton... | — |
| [#10189](https://github.com/phase-rs/phase/issues/10189) | Preferred Selection (1996) | Preferred Selection — "sacrifice … and pay {2}{G}{G}" and "one of those cards" dispositions ... | — |
| [#10172](https://github.com/phase-rs/phase/issues/10172) | Animate Dead (1997) | Off-mode CR 104.4b backstop never confirms the Worldgorger + Animate Dead loop: fingerprint ... | — |
| [#10148](https://github.com/phase-rs/phase/issues/10148) | Krark's Thumb (2003) | Mirror March + Krark's Thumb: won-flip token copies Mirror March instead of the entering cre... | — |
| [#10124](https://github.com/phase-rs/phase/issues/10124) | Day of the Dragons (2003), Wormfang Crab (2002), Wormfang Drake (2002) +1 | Linked "return the exiled card(s)" outside the paired ETB/LTB shape binds the global Tracked... | — |
| [#10060](https://github.com/phase-rs/phase/issues/10060) | Delirium (1996), Stitch Together (2002) | [Card Bug] An "instead" clause that refers back to the parent's target loses it (Stitch Toge... | — |
| [#9946](https://github.com/phase-rs/phase/issues/9946) | Mana Drain (1994) | [Card Bug] Mana Drain: the mana arrives at the next precombat main phase, skipping a postcom... | — |
| [#9942](https://github.com/phase-rs/phase/issues/9942) | Aggravated Assault (2002) | [Card Bug] "Second main phase" triggers fire in every later main phase (Cautious Survivor + ... | — |
| [#9928](https://github.com/phase-rs/phase/issues/9928) | Aggravated Assault (2002) | [Card Bug] Loop shortcut never offered when the period holds mana abilities activated by han... | — |
| [#9926](https://github.com/phase-rs/phase/issues/9926) | Solitary Confinement (2002) | [Card Bug] Loop shortcut withheld beside Solitary Confinement: non-continuous static abiliti... | — |
| [#9900](https://github.com/phase-rs/phase/issues/9900) | Invulnerability (1997) | Invulnerability: the spell's prevention sentence is a printed replacement, so casting it doe... | — |
| [#9881](https://github.com/phase-rs/phase/issues/9881) | Control Magic (1995) +3 | AI enchants its own creature with Control Magic (28 of 39 casts): gain-control Auras fall th... | — |
| [#9864](https://github.com/phase-rs/phase/issues/9864) | Mana Clash (2003) | Mana Clash: coin and die defs are folded by `consolidate_die_and_coin_defs` after the loop c... | area:parser |
| [#9782](https://github.com/phase-rs/phase/issues/9782) | Snowfall (1995) +5 | [Card Bug] (latent) Optional tapped-for-mana trigger body (Snowfall shape) panics: top frame... | — |
| [#9743](https://github.com/phase-rs/phase/issues/9743) | Phyrexian Altar (2000) | A permanent that can't be sacrificed pays a sacrifice cost and stays on the battlefield (Ale... | — |
| [#9721](https://github.com/phase-rs/phase/issues/9721) | Dark Ritual (1999) | Storm may count later no-prompt copy casts in the same batch (Mizzix’s Mastery → Empty the W... | — |
| [#9717](https://github.com/phase-rs/phase/issues/9717) | Diabolic Edict (1997) | AI casts an instant that doesn't answer Diabolic Edict in response to it (Heroic Interventio... | — |
| [#9709](https://github.com/phase-rs/phase/issues/9709) | Greater Realm of Preservation (1997) | Greater Realm of Preservation / Penance: check next-time shield consumption | — |
| [#9650](https://github.com/phase-rs/phase/issues/9650) | Force Bubble (2003) | Force Bubble: "if damage would be dealt to you" replacement doesn't apply (no recipient filt... | — |
| [#9552](https://github.com/phase-rs/phase/issues/9552) | Demonic Consultation (1995) +1 | [Card Bug] Demonic Consultation: "choose a card name" search returns nothing when card-names... | — |
| [#9510](https://github.com/phase-rs/phase/issues/9510) | Living Death (1997) | Living Death applies Dust Animus's "enters with counters" replacement twice (4 +1/+1 counter... | — |
| [#9315](https://github.com/phase-rs/phase/issues/9315) | Warbreak Trumpeter (2003) | Oracle parser stack overflow on Windows for Warbreak Trumpeter face-up trigger | — |
| [#9223](https://github.com/phase-rs/phase/issues/9223) | Prismatic Strands (2002) | [Card Bug] Prismatic Strands from AI bot did not "Prevent all damage that sources of the col... | status:needs-triage |
| [#9126](https://github.com/phase-rs/phase/issues/9126) | Goblin Sharpshooter (2002) | Ojer Anoxil, Deepest might — Goblin sharpshooter's tap ability doesn't do damage equal to Oj... | status:needs-triage |
| [#9118](https://github.com/phase-rs/phase/issues/9118) | Opportunity (2001) | Without the Control option enabled, the game will pass by Sliver Gravemother's opportunity t... | status:needs-triage |
| [#9106](https://github.com/phase-rs/phase/issues/9106) | Mana Vault (1997) | My Phyrexian Metamorph that had copied a Mana Vault returned to my hand as a Mana Vault — I ... | status:needs-triage |
| [#9097](https://github.com/phase-rs/phase/issues/9097) | Mobilize (1997) | Zurgo, Thunder's Decree doesn't stop mobilized tokens from sacrificing — Steps to Reproduce:... | status:needs-triage |
| [#9096](https://github.com/phase-rs/phase/issues/9096) | Black Market (1999) | Black Market doesn't give mana at the start of pre-combat main phase. — I had 7 counters on ... | status:needs-triage |
| [#9091](https://github.com/phase-rs/phase/issues/9091) | Solemn Simulacrum (2003) | Titan's Presence — [[Titan's Presence]] exiled [[Hullbreaker Horror]] using [[Solemn Simulac... | status:needs-triage |
| [#9078](https://github.com/phase-rs/phase/issues/9078) | Metalworker (1999) | Metalworker's Ability — [[Metalworker]] tap ability to "Reveal any number of artifact cards ... | status:needs-triage |
| [#9020](https://github.com/phase-rs/phase/issues/9020) | City of Traitors (1998) | City of traitors not saccing after playing land — Issue when playing a land after city not s... | status:needs-triage |
| [#9016](https://github.com/phase-rs/phase/issues/9016) | Mountain (2003) | Thorin Mountain King's ability doesn't select separate targets — When you use the ability to... | status:needs-triage |
| [#8987](https://github.com/phase-rs/phase/issues/8987) | Metalworker (1999) | MetalWorker Tap Ability — I Tapped [MetalWorker} for its reveal cards and add mana but after... | status:needs-triage |
| [#8966](https://github.com/phase-rs/phase/issues/8966) | Spellweaver Helix (2003) | Spellweaver helix — Spellweaver helix begins to copy my attached spell every time someone ca... | status:needs-triage |
| [#8589](https://github.com/phase-rs/phase/issues/8589) | Land Equilibrium (1994) | Land Equilibrium binds its forced sacrifice to the entering land's controller instead of the... | — |
| [#8437](https://github.com/phase-rs/phase/issues/8437) | Goblin Bombardment (1997) | Goblin Bombardment — Sacrifices the creature with no effect | status:needs-triage |
| [#8419](https://github.com/phase-rs/phase/issues/8419) | Carrion Feeder (2003) | Can't play card — I can't cast the carrion feeder in my hand. | status:needs-triage |
| [#8394](https://github.com/phase-rs/phase/issues/8394) | Overload (2000) | Eldritch Immunity — [[Eldritch Immunity]] overload does not protect each creature and still ... | status:needs-triage |
| [#8166](https://github.com/phase-rs/phase/issues/8166) | Override (2003) | Cluster: copiable-values override/reset defects across copy effects (Aug 2026 Discord batch) | — |
| [#7860](https://github.com/phase-rs/phase/issues/7860) | Invigorate (1999) | Invigorate — Says there is no ABI for rather than pay this spell's mana part of the spell | status:needs-triage |
| [#7842](https://github.com/phase-rs/phase/issues/7842) | Worn Powerstone (1998) | Archelos, Lagoon Mystic — A,LM was untapped, and opp cast Worn Powerstone, which would enter... | status:needs-triage |
| [#7809](https://github.com/phase-rs/phase/issues/7809) | Cabal Coffers (2002) | [Card Bug] Cabal Coffers | status:needs-triage |
| [#7680](https://github.com/phase-rs/phase/issues/7680) | Forgotten Ancient (2003) | Vorinclex, Monstrous Raider / Forgotten Ancient interaction — When moving counters from [[Fo... | status:needs-triage |
| [#7677](https://github.com/phase-rs/phase/issues/7677) | Solitary Confinement (2002) | Solitary Confinement — It doesn't seem to work: the opponent deals damage to me with Gutters... | status:needs-triage |
| [#7675](https://github.com/phase-rs/phase/issues/7675) | Delirium (1996) | Winter Cynical Oppotunist and Into The Pit — Winter delirium allowed the player to exile the... | status:needs-triage |
| [#7626](https://github.com/phase-rs/phase/issues/7626) | Oath of Druids (1998) | Oath of Druids ability issues — When the ability triggered on opponent's turn it still asked... | status:needs-triage |
| [#7620](https://github.com/phase-rs/phase/issues/7620) | Recurring Nightmare (1998) | Recurring Nightmare on Worldspine Wurm creates duplicate triggers — Duplicate Worldspine Wur... | status:needs-triage |
| [#6413](https://github.com/phase-rs/phase/issues/6413) | Mountain (2003) | Elegant Parlor — Double triggers and the triggers are delayed to after you pass priority whe... | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#686](https://github.com/phase-rs/phase/issues/686) | Memory Jar (1999) | Cards that don't work as intended. — Dark deal - Only the caster discards all card and you d... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#8127](https://github.com/phase-rs/phase/issues/8127) | Counterspell (2001) | Norn's Decree grants a poison counter from non-combat damage (Vivi Ornitier's spell-cast dam... | status:needs-repro, area:engine, priority:p2-wrong-game-result |
| [#8121](https://github.com/phase-rs/phase/issues/8121) | Overload (2000) | March of Progress used by the AI targeting Etherium Sculptor made no token | status:needs-repro, area:engine, priority:p2-wrong-game-result |
| [#7424](https://github.com/phase-rs/phase/issues/7424) | Swords to Plowshares (1995) | Happy Yargle Day! — the random named-card choice is unparsed; "copy the chosen card ... you ... | status:confirmed, area:parser, priority:p3-card-specific |
| [#6983](https://github.com/phase-rs/phase/issues/6983) | Counterspell (2001) | [Card Bug] Unless payments derived from board state are unsupported | status:confirmed, area:engine, area:parser |
| [#6502](https://github.com/phase-rs/phase/issues/6502) | White Knight (2003) | Valiant Endeavor — spell does nothing on resolution | status:confirmed, area:engine, area:parser |
| [#9861](https://github.com/phase-rs/phase/issues/9861) | Override (2003) | Rootweaver Druid: the "put one onto the battlefield under your control and the rest under th... | area:engine, priority:p3-card-specific |
| [#6369](https://github.com/phase-rs/phase/issues/6369) | Opportunity (2001), Sol Ring (1994) | Activating Strionic Resonator — I'm not sure how [[Strionic Resonator]] identifies an eligib... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#6463](https://github.com/phase-rs/phase/issues/6463) | Fyndhorn Elves (1995) | Declare Attackers — The game asks me if I would like to attack when I have no eligible attac... | status:confirmed, area:engine, area:frontend |
| [#11275](https://github.com/phase-rs/phase/issues/11275) | Grizzly Bears (2003) | A paused player-scope sacrifice re-asks its CR 616.1 choice of the borrowed permanent's owne... | — |
| [#11259](https://github.com/phase-rs/phase/issues/11259) | Grizzly Bears (2003) | [Card Bug] Crew, Saddle, and Station apply to a new permanent after Ghostly Flicker | — |
| [#11241](https://github.com/phase-rs/phase/issues/11241) | Grizzly Bears (2003), Planar Void (1998), Tar Pit Warrior (1997) | Mid-resolution room abilities and reflexive triggers of instants and sorceries: abilities th... | — |
| [#11232](https://github.com/phase-rs/phase/issues/11232) | Living Death (1997), Planar Guide (2003), Tormod's Crypt (1995) | Delayed tracked-set returns do not return every component of an exiled merged permanent (CR ... | area:engine |
| [#11225](https://github.com/phase-rs/phase/issues/11225) | Moment of Silence (1999), Relentless Assault (2003) | AI: attacker-declaration-pending reads an added main phase before combat as postcombat (CR 5... | — |
| [#11169](https://github.com/phase-rs/phase/issues/11169) | Jade Monolith (1999) | DamageAll: simultaneous redirected portions publish one prevention application each (CR 615.13) | — |
| [#11159](https://github.com/phase-rs/phase/issues/11159) | Mind Rot (2003) | A paused discard batch survives its replacement chooser leaving the game | — |
| [#11158](https://github.com/phase-rs/phase/issues/11158) | Grizzly Bears (2003) | Rest in Peace sacrificed in a sacrifice batch doesn't exile the permanents sacrificed after it | — |
| [#11155](https://github.com/phase-rs/phase/issues/11155) | Soul Warden (1998), Suntail Hawk (2003) | [Card Bug] Out of the Tombs skips the graveyard return in its draw replacement | — |
| [#11124](https://github.com/phase-rs/phase/issues/11124) | Preferred Selection (1996) | Multi-publisher chain tracked set unions departures outside the reader's referent (Bristlebu... | — |
| [#11101](https://github.com/phase-rs/phase/issues/11101) | Mountain (2003) | Leyline Tyrant wide-battlefield ceiling test stays green with the 512 probe cap restored | — |
| [#11100](https://github.com/phase-rs/phase/issues/11100) | Sol Ring (1994) | [Card Bug] Syr Vondam, Sunstar Exemplar: the "put into exile while its power is 4 or greater... | — |
| [#11092](https://github.com/phase-rs/phase/issues/11092) | Basking Rootwalla (2002), Fiery Temper (2002) | Ward/unless discard bypasses Madness: card is moved straight to the graveyard (CR 702.35a) | — |
| [#11086](https://github.com/phase-rs/phase/issues/11086) | Control Magic (1995), Grizzly Bears (2003), Hill Giant (2003) | [Card Bug] Trial of a Time Lord IV offers the wrong linked cards for the owner’s library order | — |
| [#11067](https://github.com/phase-rs/phase/issues/11067) | Time Warp (1999) | Stranglehold and Trouble in Pairs skip every extra turn, including their controller's and te... | — |
| [#11060](https://github.com/phase-rs/phase/issues/11060) | Drop of Honey (1993), Grizzly Bears (2003), Karplusan Forest (2001) | Mana ability activation does not reset priority passes, so an earlier pass still counts (CR ... | — |
| [#11048](https://github.com/phase-rs/phase/issues/11048) | Llanowar Elves (2001), Soul Warden (1998) | Ability-triggering observers do not see a trigger whose controller left the game before it w... | — |
| [#11047](https://github.com/phase-rs/phase/issues/11047) | Soul Warden (1998) | Opponent's state view shows a manifested / face-down card's identity in a triggered ability'... | — |
| [#11046](https://github.com/phase-rs/phase/issues/11046) | Phyrexian Altar (2000) | [Card Bug] Zulaport Cutthroat + Extractor Demon: second sacrifice skips trigger ordering aft... | — |
| [#11041](https://github.com/phase-rs/phase/issues/11041) | Grizzly Bears (2003) | [Card Bug] Loop shortcut offered at 1000 beside Ward of Bones, whose per-opponent cast ban s... | — |
| [#11038](https://github.com/phase-rs/phase/issues/11038) | Grizzly Bears (2003) | [Card Bug] Captivating Glance: a lost clash gives control to no one ("that player" has no re... | — |
| [#11036](https://github.com/phase-rs/phase/issues/11036) | Elvish Warrior (2002) | [Card Bug] Oasis Ritualist: auto-pay can't pay {G}{G} with one "Add two mana of any one colo... | — |
| [#11035](https://github.com/phase-rs/phase/issues/11035) | Grizzly Bears (2003), Override (2003) | [Card Bug] Renata, Called to the Hunt: no +1/+1 counter on an opponent-owned Dryad Arbor pla... | — |
| [#11034](https://github.com/phase-rs/phase/issues/11034) | Academy Rector (1999), Raise Dead (2003), Shallow Grave (1996) | [Card Bug] Dread Slaver: "That creature is a black Zombie" applies to a new object after the... | — |
| [#10958](https://github.com/phase-rs/phase/issues/10958) | Ashnod's Altar (1999), Ball Lightning (1997), Blood Celebrant (2003) +2 | [Card Bug] A repeatable mana ability without {T} (pay life, sacrifice another) counts as one... | — |
| [#10941](https://github.com/phase-rs/phase/issues/10941) | Arc Lightning (1998) | committed_dump_walk: EXPECTED lacks rows for the legacy_saves dumps (#10830) and one dump fr... | — |
| [#10934](https://github.com/phase-rs/phase/issues/10934) | Raise the Alarm (2003) | Extractor Demon triggers twice per token exiled by Aether Snap (expected once each) | — |
| [#10932](https://github.com/phase-rs/phase/issues/10932) | Barter in Blood (2003), Soul Warden (1998) | Battlefield departures from unthreaded producers are not seen by the departed-observer windo... | — |
| [#10920](https://github.com/phase-rs/phase/issues/10920) | Lightning Blast (2003), Platinum Angel (2003) | AI policies test "mine vs enemy" by seat, not team (Two-Headed Giant teammates score as oppo... | — |
| [#10913](https://github.com/phase-rs/phase/issues/10913) | Grizzly Bears (2003) | [Card Bug] Moonlit Meditation's copy count leaks into Primo's "equal to the damage dealt" | — |
| [#10910](https://github.com/phase-rs/phase/issues/10910) | Override (2003) | Commander tax dropped when a commander is cast with an alternative cost (CR 903.8 + CR 118.9d) | — |
| [#10879](https://github.com/phase-rs/phase/issues/10879) | Hill Giant (2003) | Grafdigger's Cage returned in the same event blocks a co-returning creature (Eerie Ultimatum... | — |
| [#10876](https://github.com/phase-rs/phase/issues/10876) | Hill Giant (2003) | Multi-card return loses its "is/has" rider after an as-enters choice pause (Ever After / Sto... | — |
| [#10875](https://github.com/phase-rs/phase/issues/10875) | Hill Giant (2003) | Primeval Spawn's "exile it instead" self-replacement is unparsed; mixed-destination returns ... | — |
| [#10870](https://github.com/phase-rs/phase/issues/10870) | Conspiracy (1999) | Parser: "first upkeep" ordinal unmodelled (Hold the Perimeter triggers every upkeep) | — |
| [#10846](https://github.com/phase-rs/phase/issues/10846) | Grizzly Bears (2003), Obstinate Familiar (2001), Savannah Lions (2003) | Chea, Friend to Maybe Too Many grants flash to every spell ("Familiar" qualifier dropped) | — |
| [#10819](https://github.com/phase-rs/phase/issues/10819) | Mountain (2003) | [Card Bug] Token catalog: preset bodies miss keywords and subtypes their tokens have (Traini... | — |
| [#10803](https://github.com/phase-rs/phase/issues/10803) | Scathe Zombies (2003) | Degraded draft suggestions ignore common-card counts when card data is unavailable | — |
| [#10802](https://github.com/phase-rs/phase/issues/10802) | Living Armor (1995), Monkey Cage (1999), Sporogenesis (1998) | [Card Bug] Radagast the Brown: "where X is that creature's mana value" binds to ObjectScope:... | — |
| [#10793](https://github.com/phase-rs/phase/issues/10793) | Blinding Beam (2003), Demoralize (2001), Dread Charge (1997) +13 | CR 611.2c: rules-modifying effects from a resolved GenericEffect broadcast freeze their affe... | — |
| [#10780](https://github.com/phase-rs/phase/issues/10780) | Grizzly Bears (2003), Lightning Bolt (1995) | Attack arrows and incoming-attacker counts keep showing attacks whose target left combat (CR... | — |
| [#10769](https://github.com/phase-rs/phase/issues/10769) | Override (2003) | Desktop: let users choose the folder for offline card images | — |
| [#10760](https://github.com/phase-rs/phase/issues/10760) | Dream Fighter (1996), Minion of the Wastes (1997) | Mirror Match: keep the entering-block binding through pauses and replacements (follow-up to ... | — |
| [#10739](https://github.com/phase-rs/phase/issues/10739) | Override (2003) | Dragonsoul Prodigy conjures the wrong card and end-step shuffles the original source | — |
| [#10728](https://github.com/phase-rs/phase/issues/10728) | Alabaster Dragon (1997) | Etrata, the Silencer drops the hit-counter condition from its game-loss instruction | — |
| [#10703](https://github.com/phase-rs/phase/issues/10703) | Altar of Shadows (2003), Brightstone Ritual (2002), Burnt Offering (1995) +2 | data: derived is_mana_ability is kind-blind: true on 177 cards' triggered bodies and 27 card... | — |
| [#10702](https://github.com/phase-rs/phase/issues/10702) | Fertile Ground (2003), Mountain (2003) | perf: "pay any amount of {R}" offer takes ~46 s with 2000 floating {U} (grows superlinearly ... | — |
| [#10683](https://github.com/phase-rs/phase/issues/10683) | Grizzly Bears (2003), Swords to Plowshares (1995) | [Card Bug] Soulherder: does not trigger when a permanent that was a creature only on the bat... | — |
| [#10677](https://github.com/phase-rs/phase/issues/10677) | Grizzly Bears (2003), Swords to Plowshares (1995) | [Card Bug] Captain Marvel, Shooting Star: its own exile triggers "a creature other than Capt... | — |
| [#10543](https://github.com/phase-rs/phase/issues/10543) | Spike Feeder (1998) | Loop offers state counts whose take overflows a life total; near the limit the offer is sile... | — |
| [#10542](https://github.com/phase-rs/phase/issues/10542) | Animate Dead (1997), Curiosity (2003), Grave Pact (2003) +6 | Loop offers: real prompts the confirmer's replay cannot answer (OfferRefusal::UnanswerablePr... | — |
| [#10541](https://github.com/phase-rs/phase/issues/10541) | Aggravated Assault (2002), Animate Dead (1997), Curiosity (2003) +7 | Loop offers: real combos the confirmer's recurrence cover refuses (OfferRefusal::Cover) | — |
| [#10508](https://github.com/phase-rs/phase/issues/10508) | Kaervek's Spite (1997), Shallow Grave (1996), Wrath of God (2003) | Owner can't arrange cards put into a graveyard simultaneously (CR 404.3) | — |
| [#10497](https://github.com/phase-rs/phase/issues/10497) | Eunuchs' Intrigues (1999), Goblin War Cry (1998), Web of Inertia (2002) | Binding guard for controlled-creatures attack bans on spell and activated paths | — |
| [#10426](https://github.com/phase-rs/phase/issues/10426) | Jade Monolith (1999), Lightning Bolt (1995) | [Card Bug] Partial damage redirection discards nested replacement choices | status:needs-triage |
| [#10425](https://github.com/phase-rs/phase/issues/10425) | Jade Monolith (1999), Lightning Bolt (1995) | [Card Bug] Generated damage redirection can skip replacement ordering | status:needs-triage |
| [#10413](https://github.com/phase-rs/phase/issues/10413) | Bronze Tablet (1995), Carrionette (1997), Giant Trap Door Spider (1995) +2 | Compound "exile A and B" instructions exile each object as a separate event, so "one or more... | — |
| [#10380](https://github.com/phase-rs/phase/issues/10380) | Emperor Crocodile (2003), Innocent Blood (2001) | Combat damage places its dies triggers apart from the state triggers the same damage causes ... | — |
| [#10363](https://github.com/phase-rs/phase/issues/10363) | Animate Dead (1997), Grizzly Bears (2003), Worldgorger Dragon (2002) | Enters triggers miss a creature that enters together with the trigger's source, depending on... | — |
| [#10359](https://github.com/phase-rs/phase/issues/10359) | Snuff Out (1999) | snuff_out_from_card_database_alt_cost_destroys_target panics: "a spell trigger carrier outli... | — |
| [#10356](https://github.com/phase-rs/phase/issues/10356) | Override (2003) | [Engine Bug] proposed_event: permanent entry choices prefer the caster over the live controller | — |
| [#10295](https://github.com/phase-rs/phase/issues/10295) | Desperate Gambit (1997), Jade Monolith (1999), Mogg Fanatic (1997) | Damage-source options omit departed objects referred to by pending effects (CR 609.7a) | — |
| [#10242](https://github.com/phase-rs/phase/issues/10242) | Future Sight (2002) | Teferi off-battlefield Flash grant omits owned creature cards in the library | — |
| [#10216](https://github.com/phase-rs/phase/issues/10216) | Misinformation (1996) | Library-order prompt: NthFromTop reads the selection bottom-to-top, and every position is la... | — |
| [#10208](https://github.com/phase-rs/phase/issues/10208) | Awe Strike (2003), Impulsive Maneuvers (2001), Thrashing Wumpus (1999) | One-shot 'next time' shields only change the first recipient of non-combat simultaneous damage | — |
| [#10198](https://github.com/phase-rs/phase/issues/10198) | Plow Under (2003) | Vault 13: Dweller's Journey chapter III: "put the rest on the bottom of their owners' librar... | — |
| [#10178](https://github.com/phase-rs/phase/issues/10178) | Flock of Rabid Sheep (1998), Krark's Thumb (2003) | Multi-flip loops drop remaining flips when an interactive result branch pauses | — |
| [#10156](https://github.com/phase-rs/phase/issues/10156) | Grizzly Bears (2003) | Banisher Priest exiles its target when it left the battlefield before its enters trigger res... | — |
| [#10138](https://github.com/phase-rs/phase/issues/10138) | Grizzly Bears (2003) | Miracle trigger and a same-draw trigger skip the trigger-order prompt (Thunderous Wrath + Sh... | — |
| [#10137](https://github.com/phase-rs/phase/issues/10137) | Grizzly Bears (2003) | Venture room ability skips the trigger-order prompt alongside a co-triggered ability (Fates'... | — |
| [#10129](https://github.com/phase-rs/phase/issues/10129) | Grizzly Bears (2003) | Champion return strands the components of a championed merged (mutated) permanent (CR 730.3c) | — |
| [#10090](https://github.com/phase-rs/phase/issues/10090) | Counterspell (2001), Disenchant (2001) | Bestow form survives resolved battlefield zone-command replay | — |
| [#10045](https://github.com/phase-rs/phase/issues/10045) | Shield Bearer (1997) | Integration fixture misses 12 baseline keys selected by gen-test-fixture | — |
| [#10030](https://github.com/phase-rs/phase/issues/10030) | Override (2003) | Reclaim the Wastes: kicked count replacement becomes an extra unfiltered search | — |
| [#9962](https://github.com/phase-rs/phase/issues/9962) | Lightning Bolt (1995) | Copy retarget: "Keep Current Targets" and "Keep This Target" look identical for a single-tar... | — |
| [#9947](https://github.com/phase-rs/phase/issues/9947) | Hill Giant (2003) | [Card Bug] Vivien's Stampede: the delayed "next main phase this turn" trigger fires at every... | — |
| [#9924](https://github.com/phase-rs/phase/issues/9924) | Aggravated Assault (2002), Spined Wurm (2003) | [Card Bug] Automatic payment pays a lethal life cost (Mana Confluence) while Treasures that ... | — |
| [#9917](https://github.com/phase-rs/phase/issues/9917) | Dwell on the Past (2002), Gaea's Blessing (1997), Krosan Reclamation (2002) | Memory's Journey: the target player is asked for twice and card offers include other players... | — |
| [#9912](https://github.com/phase-rs/phase/issues/9912) | Counterspell (2001), Lightning Bolt (1995), Mountain (2003) | AI never takes an instant or sorcery with Impulse (0 of 360 picks) or Stock Up (26 of 2,470)... | — |
| [#9898](https://github.com/phase-rs/phase/issues/9898) | Lightning Bolt (1995) | AI spends instants and flash creatures in its own turn, so it almost never reaches the oppon... | — |
| [#9897](https://github.com/phase-rs/phase/issues/9897) | Flametongue Kavu (2001), Mountain (2003) | Archetype mulligan policies outvote the keep on playable hands at every depth: 6.5% of first... | — |
| [#9894](https://github.com/phase-rs/phase/issues/9894) | Giant Growth (2003) | AI casts pump and protection instants before blocks or with nothing to answer (1 of 74 pumps... | — |
| [#9893](https://github.com/phase-rs/phase/issues/9893) | Control Magic (1995), Glorious Anthem (2003), Pacifism (2003) | AI casts "creature or planeswalker" removal at its own creature when the opponent has no tar... | — |
| [#9891](https://github.com/phase-rs/phase/issues/9891) | Conspiracy (1999) | Muzzio's Preparations: "each creature you control with the chosen name enters with …" subjec... | — |
| [#9883](https://github.com/phase-rs/phase/issues/9883) | Control Magic (1995) | AI never takes an opponent's permanent with Zealous Conscripts (0 of 115 ETBs): gain-control... | — |
| [#9858](https://github.com/phase-rs/phase/issues/9858) | Energy Field (1998) | Team formats: "an opponent controls" / "each opponent" include teammates (ControllerRef::Opp... | area:engine |
| [#9825](https://github.com/phase-rs/phase/issues/9825) | Lightning Bolt (1995) | Bug: Alania, Divergent Storm copies resolve for the opponent instead of the controller | status:needs-triage |
| [#9800](https://github.com/phase-rs/phase/issues/9800) | Phyrexian Altar (2000), Steel Wall (2003) | Loop shortcut publishes a count its pinned destructible damage target does not survive | — |
| [#9764](https://github.com/phase-rs/phase/issues/9764) | Overload (2000) | [Card Bug] Teval, the Balanced Scale + Mizzix's Mastery: Mastery goes to the graveyard mid-r... | — |
| [#9746](https://github.com/phase-rs/phase/issues/9746) | Metallic Sliver (1997) | Automatic payment of a mana ability's cost sacrifices a creature without asking (Basal Slive... | — |
| [#9739](https://github.com/phase-rs/phase/issues/9739) | Mangara's Tome (1996), Natural Balance (1996), Noble Benefactor (1997) +4 | Jungle Wayfinder returns itself to hand when the search finds no basic land (empty search, t... | — |
| [#9729](https://github.com/phase-rs/phase/issues/9729) | Override (2003) | Self "leaves your graveyard" trigger resolves under the reanimator, not the graveyard-side s... | — |
| [#9727](https://github.com/phase-rs/phase/issues/9727) | Bogardan Phoenix (1997) | Triggered self-Endure can counter a returned incarnation after a flicker response | — |
| [#9723](https://github.com/phase-rs/phase/issues/9723) | Override (2003) | Dandân: a milled pile card keeps the load-time owner, so only seat 0 can activate its gravey... | — |
| [#9718](https://github.com/phase-rs/phase/issues/9718) | Wrath of God (2003) | AI: a scheduled-return self-blink (Aetherling) in response to Day of Judgment is read as "no... | — |
| [#9715](https://github.com/phase-rs/phase/issues/9715) | Hill Giant (2003) | AI: scheduled-return blinks are not valued — Guardian of Ghirapur declines at Medium, Kykar ... | — |
| [#9677](https://github.com/phase-rs/phase/issues/9677) | Counterspell (2001), Mystic Snake (2001) | AI casts flash creatures with an ETB counter (Voracious Greatshark class) into an empty stac... | — |
| [#9676](https://github.com/phase-rs/phase/issues/9676) | Counterspell (2001) | AI never counters cheap planeswalkers, enchantments and artifacts: assess_spell_impact price... | — |
| [#9673](https://github.com/phase-rs/phase/issues/9673) | Counterspell (2001) | AI: flicker of your own creature is treated as removal — Momentary Blink/Ephemerate/Cloudshi... | — |
| [#9671](https://github.com/phase-rs/phase/issues/9671) | Future Sight (2002) | AI: top-of-library permission candidates drift across determinized worlds in shared-library ... | — |
| [#9664](https://github.com/phase-rs/phase/issues/9664) | Bonesplitter (2003) | Hidetsugu and Kairi: with an empty library the dies trigger still costs the opponent 5 life | — |
| [#9628](https://github.com/phase-rs/phase/issues/9628) | Chrome Mox (2003), Duplicant (2003), Isochron Scepter (2003) | "Cards exiled with" lookup falls back to a previous incarnation's exiled cards when a perman... | status:needs-triage, area:engine |
| [#9625](https://github.com/phase-rs/phase/issues/9625) | Disenchant (2001) | [Card Bug] Trusty Boomerang — a granted ability that names its granting permanent still acts... | status:needs-triage, area:engine |
| [#9621](https://github.com/phase-rs/phase/issues/9621) | Mountain (2003) | Optional-effect, trigger-order and replacement modals show the engine's "~" self-reference i... | status:needs-triage, area:frontend |
| [#9616](https://github.com/phase-rs/phase/issues/9616) | Dragon Breath (2003) | coverage-data.json differs run to run on identical input: card order and top-N membership de... | status:needs-triage, area:card-data |
| [#9559](https://github.com/phase-rs/phase/issues/9559) | Animate Dead (1997), Grizzly Bears (2003) | "Leaves your graveyard" trigger (controller: You form) does not fire when an opponent reanim... | — |
| [#9555](https://github.com/phase-rs/phase/issues/9555) | Primitive Justice (1996), Slow Motion (1999), Taste of Paradise (1996) | Non-modal reflexive "When you do" after "pay {cost} up to N times" is deferred and never res... | — |
| [#9536](https://github.com/phase-rs/phase/issues/9536) | Brainstorm (1999), Doomsday (1999) | reposition_library_origins_after_batch_delivery scrambles the order of library-origin cards ... | — |
| [#9493](https://github.com/phase-rs/phase/issues/9493) | Prohibit (2000), Wrath of God (2003) | Feature request: a casual EDH table with intuitive Sandbox play and pre-agreed Undo | — |
| [#9426](https://github.com/phase-rs/phase/issues/9426) | Counterspell (2001), Grizzly Bears (2003), Multani's Presence (1999) | [Card Bug] Lullmage Mentor / Baral trigger when an ability (not a spell) is countered | — |
| [#9403](https://github.com/phase-rs/phase/issues/9403) | Battlegrowth (2003) | [Card Bug] Barroom Brawl: the second target accepts any creature, not one the opponent to yo... | — |
| [#9381](https://github.com/phase-rs/phase/issues/9381) | Gray Ogre (1995) | [Card Bug] Undying Flames deals no damage: its target is overwritten with the exiled card an... | — |
| [#9378](https://github.com/phase-rs/phase/issues/9378) | Isochron Scepter (2003) | [Card Bug] A copy cast with fresh targets puts every target on its first instruction (Mizzix... | — |
| [#9296](https://github.com/phase-rs/phase/issues/9296) | Darkwater Catacombs (2001), Mind Stone (1997) | [Card Bug] Auto-pay gives up with a filter land on board, and the AI's prospective payment s... | — |
| [#9288](https://github.com/phase-rs/phase/issues/9288) | Giant Growth (2003) | [Card Bug] Spellskite can't redirect a target on a later instruction (retarget pool reads on... | — |
| [#9286](https://github.com/phase-rs/phase/issues/9286) | Grizzly Bears (2003) | [Card Bug] Jeskai Revelation with one creature as both targets deals damage to the card afte... | — |
| [#9285](https://github.com/phase-rs/phase/issues/9285) | Giant Growth (2003) | [Card Bug] Deflecting Swat retarget hands priority to the retargeting player instead of the ... | — |
| [#9284](https://github.com/phase-rs/phase/issues/9284) | Grizzly Bears (2003) | [Card Bug] Aether Spike never counters: "for each {E} paid this way" binds to 0 | — |
| [#9120](https://github.com/phase-rs/phase/issues/9120) | Sol Ring (1994) | Karn, The Great Creator's stax ability. — [[Karn, the Great Creator]]'s passive text "activa... | status:needs-triage |
| [#9093](https://github.com/phase-rs/phase/issues/9093) | Battle Cry (1995) | Primaris Chaplain gives itself +1/+0 when attacking with Battlecry when it shouldn't be. — M... | status:needs-triage |
| [#9069](https://github.com/phase-rs/phase/issues/9069) | Cabal Coffers (2002) | Urborg, Tomb of Yawgmoth — Doesn't make lands (including itself) swamps. | status:needs-triage |
| [#9017](https://github.com/phase-rs/phase/issues/9017) | Disappear (1999) | PizzaFace, Gastromancer — [[PizzaFace, Gastromancer]] does not turn artifacts into artifact ... | status:needs-triage |
| [#9011](https://github.com/phase-rs/phase/issues/9011) | Phyrexian Altar (2000) | Sacrifice stack doesn't work properly with same trigger, triggered at different time — I tri... | status:needs-triage |
| [#8970](https://github.com/phase-rs/phase/issues/8970) | Disappear (1999) | Joshua, Phoenix's Dominant Equipped Issue — So I'm not sure quite what the bug is here but w... | status:needs-triage |
| [#8965](https://github.com/phase-rs/phase/issues/8965) | Phyrexian Dreadnought (1996) | Responding to Evoke triggers — Hey! | status:needs-triage |
| [#8656](https://github.com/phase-rs/phase/issues/8656) | Swords to Plowshares (1995) | change_zone::resolve affects an illegal target when CR 608.2b re-validation drops it (bypass... | — |
| [#8626](https://github.com/phase-rs/phase/issues/8626) | Exploration (1998), Lightning Bolt (1995), Mountain (2003) +2 | AI: Native Medium measurement pilot passes an available lethal Bolt in a four-player witness | — |
| [#8596](https://github.com/phase-rs/phase/issues/8596) | Lightning Bolt (1995) | Composite name resolution accepts unpaired halves, letting decklist typos bypass unknown-car... | — |
| [#8587](https://github.com/phase-rs/phase/issues/8587) | Chaos Orb (1993), Confound (2001), Crazed Armodon (1997) +5 | destroy::resolve skips its self-destroy and destroys the inherited parent target when abilit... | — |
| [#8585](https://github.com/phase-rs/phase/issues/8585) | Fatespinner (2003), Primal Clay (1999), Teferi's Realm (1997) | Mystic Barrier's upkeep re-choice never reaches the permanent — named_choice_authority treat... | — |
| [#8584](https://github.com/phase-rs/phase/issues/8584) | Helm of Obedience (1996), Hungry Hungry Heifer (1998), Inheritance (1996) +1 | Sacrifice{SelfRef} inherits the parent instruction's object target and sacrifices the wrong ... | — |
| [#8561](https://github.com/phase-rs/phase/issues/8561) | Grizzly Bears (2003) | Devour-shape entrant with an external ETB-counter source still strands its resolution stack | — |
| [#8512](https://github.com/phase-rs/phase/issues/8512) | Overload (2000) | CastingVariant::Surge is never elected as a sole candidate, so Surge casts fall through to N... | — |
| [#8400](https://github.com/phase-rs/phase/issues/8400) | Exploration (1998) | Wildgrowth Walker — Wildgrowth Walker not adding additional life and adding +1/+1 counters t... | status:needs-triage |
| [#8261](https://github.com/phase-rs/phase/issues/8261) | Awesome Presence (1996), Graxiplon (2002), Mana Leak (2003) +4 | Parser: fold the unless-clause payer-subject onto a single authority | — |
| [#8170](https://github.com/phase-rs/phase/issues/8170) | Celestial Convergence (2000), Goblin Game (2001), Loxodon Peacekeeper (2003) +5 | parser: superlative-comparison player subject ("the player who/with … gains control / takes ... | — |
| [#7893](https://github.com/phase-rs/phase/issues/7893) | Food Chain (1999) | Misthollow griffin doesn't allow cast from exile. — The whole point of misthollow griffin is... | status:needs-triage |
| [#7789](https://github.com/phase-rs/phase/issues/7789) | Disappear (1999) | [Card Bug] Cannot properly cash-in Storage Land counters | status:needs-triage |
| [#7785](https://github.com/phase-rs/phase/issues/7785) | Mobilize (1997) | [Card Bug] Zurgo Thunder's Decree does not work as intended | status:needs-triage |
| [#7619](https://github.com/phase-rs/phase/issues/7619) | Necromancy (1997) | Necromany targetting Worldspine wurm — Worldspine Wurm is discarded on cleanup step of my turn. | status:needs-triage |
| [#7610](https://github.com/phase-rs/phase/issues/7610) | Lightning Greaves (2003) | [Card Bug] Monk gyatso airbend | status:needs-triage |
| [#7587](https://github.com/phase-rs/phase/issues/7587) | Wall of Blossoms (1998) | Creatures with Defender are listed in valid_attacker_ids at DeclareAttackers (v0.59.0) | — |
| [#7521](https://github.com/phase-rs/phase/issues/7521) | Opportunity (2001) | AI crews a Vehicle with every creature it controls, then declares no attackers | — |
| [#7481](https://github.com/phase-rs/phase/issues/7481) | Oubliette (1993) | Event-less effect heads publish an empty tracked set: DoublePTAll (God-Eternal Rhonas) and s... | — |
| [#7463](https://github.com/phase-rs/phase/issues/7463) | Bamboozle (2001), Goblin Machinist (2002) | Engine: the tracked-set publish arm for head `Pump` is unshipped — 38-row upper bound, 2 mea... | — |
| [#5056](https://github.com/phase-rs/phase/issues/5056) | Conspiracy (1999) | Implement the Vanguard variant (CR 902) | area:engine, area:card-data, area:frontend |
| [#1148](https://github.com/phase-rs/phase/issues/1148) | Lightning Greaves (2003), Mask of Memory (2003) | Sigarda's Aid + Cloud, Ex-SOLDIER memory issue? — im not exactly sure what caused it, nor ca... | status:needs-runtime-verify, area:engine, priority:p0-panic |

## Cites an issue — run the direction check (42)

| issue | card(s) | title | labels |
|---|---|---|---|
| [#8058](https://github.com/phase-rs/phase/issues/8058) | Swords to Plowshares (1995) | Swords to Plowshares still grants life when the spell fizzles before resolution | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#6924](https://github.com/phase-rs/phase/issues/6924) | Phyrexian Altar (2000) | Moldervine Reclamation does not trigger when a token is sacrificed with Phyrexian Altar | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#5653](https://github.com/phase-rs/phase/issues/5653) | Chains of Mephistopheles (1994) +2 | Chains of Mephistopheles / Magus of the Chains: result-referential conditions silently dropp... | status:confirmed, area:engine, area:parser |
| [#4231](https://github.com/phase-rs/phase/issues/4231) | Final Fortune (2001) | Fake Fortune — [[Final Fortune]] - when played, upon the end step the card was cast, the eng... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#8147](https://github.com/phase-rs/phase/issues/8147) | Mobilize (1997) | Voice of Victory (Mobilize) — Warrior tokens are never sacrificed at the next end step | status:fixed-unreleased, area:engine, priority:p2-wrong-game-result |
| [#1098](https://github.com/phase-rs/phase/issues/1098) | Land Grant (1999) | Land Grant — Alternative cost - show hand with no land cards - doesn't work | status:confirmed, area:engine, priority:p3-card-specific |
| [#5965](https://github.com/phase-rs/phase/issues/5965) | Swords to Plowshares (1995) | Swords to Plowshares — Steps to Reproduce: | status:needs-repro, area:engine, priority:p3-card-specific |
| [#10957](https://github.com/phase-rs/phase/issues/10957) | Deep Analysis (2002) | [Card Bug] A granted alternative-cast keyword erases the printed one (Lier + Deep Analysis f... | — |
| [#10907](https://github.com/phase-rs/phase/issues/10907) | Animate Dead (1997), Soul Warden (1998), Worldgorger Dragon (2002) +1 | Mandatory-replay span covers half a period when one printed trigger fires twice per cycle (W... | — |
| [#10152](https://github.com/phase-rs/phase/issues/10152) | Phyrexian Processor (1998) | Phyrexian Processor: as-enters life payment and remembered-X token unsupported | — |
| [#9915](https://github.com/phase-rs/phase/issues/9915) | Imperial Edict (1999) | Imperial Edict: the creature is chosen by the caster at cast time (or the caster's own creat... | — |
| [#9899](https://github.com/phase-rs/phase/issues/9899) | Corrosion (1997), Oblivion Stone (2003), Temporal Distortion (2000) +3 | Untargeted "remove all … counters from all …" asks for one target and removes from that obje... | — |
| [#9747](https://github.com/phase-rs/phase/issues/9747) | Llanowar Elves (2001) | A second, equal granted ability is dropped: Marvin, Murderous Mimic with two Llanowar Elves ... | — |
| [#9282](https://github.com/phase-rs/phase/issues/9282) | Counterspell (2001) | [Card Bug] Counterspell removes the target spell's own cast trigger instead of the spell (ca... | — |
| [#1674](https://github.com/phase-rs/phase/issues/1674) | Decompose (2001) | parser/oracle_static.rs` monolith (1016 KB) — decompose into per-category module hierarchy p... | area:parser |
| [#4886](https://github.com/phase-rs/phase/issues/4886) | Disappear (1999) | [Card Bug] Stuck at choosing Jinnie's replacement effect | status:confirmed, area:engine, priority:p0-softlock |
| [#1235](https://github.com/phase-rs/phase/issues/1235) | Lion's Eye Diamond (1996), Mountain (2003), Phyrexian Altar (2000) | feasible_mana_capacity sum over-counts chain-sacrifice configurations | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#1234](https://github.com/phase-rs/phase/issues/1234) | Ashnod's Altar (1999), Lion's Eye Diamond (1996), Phyrexian Altar (2000) | feasible_mana_capacity: colored-shard feasibility under non-tap mana sources | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#1272](https://github.com/phase-rs/phase/issues/1272) | Delirium (1996) | [Card Bug] Violent Urge giving Double Strike to all creatures | status:needs-runtime-verify, area:engine, priority:p3-card-specific |
| [#7758](https://github.com/phase-rs/phase/issues/7758) | Curiosity (2003) | Grima, Saruman's footman | status:confirmed, area:engine |
| [#11195](https://github.com/phase-rs/phase/issues/11195) | Grizzly Bears (2003) | Winding Constrictor's "you get that many plus one" misses infect poison from Ram Through's e... | — |
| [#11123](https://github.com/phase-rs/phase/issues/11123) | Day of the Dragons (2003) | Timothar, Baron of Bats: granted Bat trigger never returns the exiled Vampire (CR 607.2a / 4... | — |
| [#11044](https://github.com/phase-rs/phase/issues/11044) | Grizzly Bears (2003) | [Card Bug] Sol, Advocate Eternal: Teamwork fires when Sol attacks alone, and "investigate fo... | — |
| [#10922](https://github.com/phase-rs/phase/issues/10922) | Ashnod's Altar (1999), Black Lotus (1993), Blood Celebrant (2003) +3 | AI keeps activating a costed mana ability after passing would finish the payment (Treasonous... | — |
| [#10901](https://github.com/phase-rs/phase/issues/10901) | Glorious Anthem (2003), Vanishing (1997) | Per-counter trigger multiplicity for "a [kind] counter is removed from ~" triggers (Protean ... | — |
| [#10759](https://github.com/phase-rs/phase/issues/10759) | Avenging Angel (1997), Lodestone Bauble (1996), Tel-Jilad Stylus (2003) | Merged-permanent library arrivals: owner arrangement, library-order privacy and simultaneous... | — |
| [#10630](https://github.com/phase-rs/phase/issues/10630) | Swords to Plowshares (1995) | Market Gnome: "while you're activating a craft ability" trigger qualifier is unrepresented (... | — |
| [#10414](https://github.com/phase-rs/phase/issues/10414) | Shared Fate (2003) | ChangeZone/ChangeZoneAll record the ability's controller as the exiling player even when ano... | — |
| [#10393](https://github.com/phase-rs/phase/issues/10393) | Yawgmoth's Will (1998) | Osteomancer Adept: forage graveyard cast grant grants nothing (classless CastFromZone; forag... | — |
| [#10195](https://github.com/phase-rs/phase/issues/10195) | Swords to Plowshares (1995) | Market Gnome: craft-only exile trigger parses with no condition and fires on any exile | — |
| [#10109](https://github.com/phase-rs/phase/issues/10109) | Plow Under (2003) | Monster Mash-Up and Grusilda, Monster Masher: "combined into one creature" is silently dropped | — |
| [#9778](https://github.com/phase-rs/phase/issues/9778) | Darkwater Catacombs (2001) | [Card Bug] Arena of Glory: auto-pay picks the Exert mana ability even when {T}: Add {R} suff... | — |
| [#9776](https://github.com/phase-rs/phase/issues/9776) | Grizzly Bears (2003) | [Card Bug] Nahiri, Storm of Stone: equip discount misparses as a free Equip {0} grant to you... | — |
| [#9766](https://github.com/phase-rs/phase/issues/9766) | Goblin Cadets (1998), Grizzly Bears (2003), Jinxed Idol (1997) +2 | [Card Bug] Donate, Harmless Offering: the target-player recipient is never offered, so contr... | — |
| [#9663](https://github.com/phase-rs/phase/issues/9663) | Tainted Pact (2001) | Protection Racket: the trigger moves Protection Racket itself, reveals the wrong library, an... | — |
| [#9600](https://github.com/phase-rs/phase/issues/9600) | Citadel of Pain (2000), Early Harvest (2001), Eunuchs' Intrigues (1999) +7 | "that player controls" / "they control" after a declared player parses as the caster's objec... | — |
| [#9509](https://github.com/phase-rs/phase/issues/9509) | Living Death (1997) | Simultaneous battlefield entries see each other: mass returns let entry replacements count c... | — |
| [#9377](https://github.com/phase-rs/phase/issues/9377) | Grizzly Bears (2003), Memory Lapse (2001) | Hidden-information leak: object ids (and id-keyed LKI/journal side tables) track cards into ... | — |
| [#9264](https://github.com/phase-rs/phase/issues/9264) | Decompose (2001) | Type the untyped `as long as` conditions (renown, keyword-presence) instead of leaving them ... | — |
| [#7923](https://github.com/phase-rs/phase/issues/7923) | Abeyance (1997), Override (2003) | Seam: leading duration silently discards trailing ", and" conjuncts and arbitrary trailing t... | — |
| [#7721](https://github.com/phase-rs/phase/issues/7721) | Anavolver (2001), Cetavolver (2001), Faerie Squadron (2000) +4 | Kicker cycle: "enters with ... and with <ability>" silently drops the granted ability (9 cards) | — |
| [#7510](https://github.com/phase-rs/phase/issues/7510) | Library of Leng (1997) | Declining an optional discard replacement drops the remaining discards of a multi-card discard | — |
