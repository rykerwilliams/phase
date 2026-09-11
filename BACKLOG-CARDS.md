# Card backlog — generated from `backlog/watchlist.txt`

> **Working this? Read [`OLD-CARD-RUNBOOK.md`](OLD-CARD-RUNBOOK.md) first**, or just run `/backlog-batch`.

_Generated 2026-09-11 against `upstream/main` `1cde7a25d` · 1106 open issues · watchlist resolves to 6594 cards_

**Do not hand-edit** — regenerate with `python3 backlog/scan.py`. To change what is tracked, edit `backlog/watchlist.txt`.

| verdict | count | meaning |
|---|---:|---|
| **LIVE** | 105 | No signal that it is fixed. Best candidates. |
| partial-coverage | 51 | Card appears in some test; nothing ties a fix to THIS issue. |
| CHECK-DIRECTION | 17 | A commit/test cites the issue — but a commit can cite an issue to **fix**, **defer**, be **blocked on**, or **file** it. Only the first means fixed. Run the direction check before believing this bucket. |

```bash
git log -1 --format='%b' <sha> | grep -B2 -A3 '#<N>\b'   # the direction check
```

★ = a card you explicitly named in the watchlist.


## LIVE — best candidates (105)

| issue | card(s) | title | labels |
|---|---|---|---|
| [#6301](https://github.com/phase-rs/phase/issues/6301) | Force of Will (1996) | [Card Bug] Force of Will: Can't be castet | status:confirmed, area:engine, area:frontend |
| [#5936](https://github.com/phase-rs/phase/issues/5936) | Stampede (1997) | Game broke with a prio bug for something my friend couldn't pay for — The card was Slinza, t... | status:needs-repro, area:engine, priority:p0-softlock |
| [#6875](https://github.com/phase-rs/phase/issues/6875) | Krark-Clan Shaman (2003) | Krark-clan shaman — Game doesn't allow the ability to be used more than once; the first sacr... | status:needs-runtime-verify, area:engine, priority:p1-core-mechanic |
| [#6389](https://github.com/phase-rs/phase/issues/6389) | Goblin Sharpshooter (2002) | goblin sharpshooter — Doesn't untap when someone's commander dies Here's why it should (Than... | status:needs-runtime-verify, area:engine, priority:p1-core-mechanic |
| [#8115](https://github.com/phase-rs/phase/issues/8115) | Extortion (1999) | Temporal Extortion — doesn't grant an extra turn even when uncountered; also broken in PvP | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#8060](https://github.com/phase-rs/phase/issues/8060) | Reclamation (1995) | Natively-printed Cascade triggers but never casts the exiled spell (Natural Reclamation, Den... | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#7353](https://github.com/phase-rs/phase/issues/7353) | Blatant Thievery (2002) | Blatant Thievery — Says to choose 6 targets and won't let you target anything. | status:confirmed, area:engine, area:parser |
| [#6924](https://github.com/phase-rs/phase/issues/6924) | Phyrexian Altar (2000), Reclamation (1995) | Moldervine Reclamation does not trigger when a token is sacrificed with Phyrexian Altar | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#6916](https://github.com/phase-rs/phase/issues/6916) | Sleeper Agent (1998) | Xantcha, Sleeper Agent — You cannot choose which opponent that gets Xantcha. | status:confirmed, area:engine, area:parser |
| [#6902](https://github.com/phase-rs/phase/issues/6902) | Sneak Attack (1998) | Sneak Attack — Creates an end step trigger, but that trigger only sometimes makes you sacrif... | status:confirmed, area:engine, area:parser |
| [#6862](https://github.com/phase-rs/phase/issues/6862) | Reclamation (1995) | esper's to magicite allows any card to become an artifact not just a creature — AI just exil... | status:confirmed, area:engine, area:ai |
| [#6508](https://github.com/phase-rs/phase/issues/6508) | Citadel of Pain (2000) | Citadel of Pain — damages its controller instead of opponents | status:confirmed, area:engine, area:parser |
| [#6395](https://github.com/phase-rs/phase/issues/6395) | Nicol Bolas (1995) | Nicol Bolas, Dragon God draws a card for the +1 but exiles at random from your hand for each... | status:confirmed, area:engine, area:parser |
| [#4784](https://github.com/phase-rs/phase/issues/4784) | Nicol Bolas (1995) | Nicol Bolas, Planeswalker — I used Nicol Bolas Ult on the AI bot, and it did 7 damage to the... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#4732](https://github.com/phase-rs/phase/issues/4732) | Instigator (1999) | Firkraag, Cunning Instigator is taking counters and card draw illegally — The +1/+1 and card... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#4731](https://github.com/phase-rs/phase/issues/4731) | Reins of Power (1998) | Reins of Power targeting incorrectly — [[Reins of power]] is giving the casting player contr... | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#4231](https://github.com/phase-rs/phase/issues/4231) | Final Fortune (2001) | Fake Fortune — [[Final Fortune]] - when played, upon the end step the card was cast, the eng... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#836](https://github.com/phase-rs/phase/issues/836) | Battle Cry (1995) | Hero of Bladehold — Tokens are being spawned but Battle cry trigger is not happening. | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#782](https://github.com/phase-rs/phase/issues/782) | Thought Lash (1996) | Thought Lash — The activated ability can be activated without paying the cost of exiling the... | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#8116](https://github.com/phase-rs/phase/issues/8116) | Goblin Sharpshooter (2002) | Goblin Sharpshooter equipped with Basilisk Collar doesn't untap when its target is destroyed | status:needs-repro, area:engine, priority:p2-wrong-game-result |
| [#7450](https://github.com/phase-rs/phase/issues/7450) | Vaevictis Asmadi (1995) | Vaevictis Asmadi, the Dire — "for each player, choose target permanent that player controls"... | status:confirmed, area:parser, priority:p3-card-specific |
| [#7435](https://github.com/phase-rs/phase/issues/7435) | Delirium (1996) | Pick the Brain — the delirium multi-zone same-name search is unparsed, so `ChangeZone` reads... | status:confirmed, area:parser, priority:p3-card-specific |
| [#7431](https://github.com/phase-rs/phase/issues/7431) | Mist of Stagnation (2002) | Mist of Stagnation — "chooses a permanent for each card in their graveyard" is unparsed; "un... | status:confirmed, area:parser, priority:p3-card-specific |
| [#7427](https://github.com/phase-rs/phase/issues/7427) | Delirium (1996) | Invasive Surgery — the delirium multi-zone same-name search is unparsed, so `ChangeZone` rea... | status:confirmed, area:parser, priority:p3-card-specific |
| [#7419](https://github.com/phase-rs/phase/issues/7419) | Afterlife (1999) | Afterlife from the Loam — "for each player, choose up to one target creature card" is unpars... | status:confirmed, area:parser, priority:p3-card-specific |
| [#7157](https://github.com/phase-rs/phase/issues/7157) | Peacekeeper (1997) | Emperor of Bones didn't grant creature haste nor trigger its etb — Emperor of Bones ability ... | status:confirmed, area:engine, priority:p3-card-specific |
| [#6771](https://github.com/phase-rs/phase/issues/6771) | Breakthrough (2002) | Breakthrough card not working correctly — it lets you draw 4 cards but doesn't make you disc... | status:confirmed, area:engine, area:parser |
| [#6770](https://github.com/phase-rs/phase/issues/6770) | Manabond (1998) | Manabond card not working correctly — it triggers at the end of the turn, discard correctly ... | status:confirmed, area:engine, area:parser |
| [#5654](https://github.com/phase-rs/phase/issues/5654) | Plagiarize (2002) | Notion Thief + Plagiarize: compound 'skips that draw and you draw' substitute drops to Unimp... | status:confirmed, area:engine, area:parser |
| [#4509](https://github.com/phase-rs/phase/issues/4509) | Lost in Thought (2002) | Lost in Thought ignore-effect escape clause dropped (cluster 36) | status:confirmed, area:engine, area:parser |
| [#8088](https://github.com/phase-rs/phase/issues/8088) | Override (2003) | Volrath, the Shapestealer — copy ability drops the "except it's 7/5" override | status:needs-repro, area:engine, priority:p3-card-specific |
| [#7344](https://github.com/phase-rs/phase/issues/7344) | Goblin Sledder (2002) | Goblin sledder — Doesn't correctly get +1/+1 until the end of turn when sacrificing Mogg War... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#6465](https://github.com/phase-rs/phase/issues/6465) | Treachery (1999) | Attached Card Display — I ephemerated agent of treachery with skullclamp equipped to it -- a... | status:needs-repro, area:engine, area:frontend |
| [#6001](https://github.com/phase-rs/phase/issues/6001) | Serra Avatar (1998) | Aethermage's touch — Steps to Reproduce: Serra Avatar was cheated out with Aethermage's touch. | status:needs-repro, area:engine, priority:p3-card-specific |
| [#4965](https://github.com/phase-rs/phase/issues/4965) | Biorhythm (2002) | cannot cast biorhythm — 8 mana is plenty | status:needs-repro, area:engine, priority:p3-card-specific |
| [#4748](https://github.com/phase-rs/phase/issues/4748) | Oblation (2002) | Oblation — Shuffled my nonland permanent into my deck but did not have me draw two cards in ... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#4228](https://github.com/phase-rs/phase/issues/4228) | Reconnaissance (1998) | reconnaissance — not working as it should. | status:needs-repro, area:engine, priority:p3-card-specific |
| [#3658](https://github.com/phase-rs/phase/issues/3658) | Mana Vault (1997) | Mana Vault (paying even though its not tapped) — I think when i first summoned the card I ta... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#5273](https://github.com/phase-rs/phase/issues/5273) | Squallmonger (1999) | Squallmonger — Cool card played by the AI. | status:needs-repro, area:ai, priority:p4-ui-polish |
| [#7742](https://github.com/phase-rs/phase/issues/7742) | Need for Speed (2001) | need for speed | status:confirmed, area:engine |
| [#8762](https://github.com/phase-rs/phase/issues/8762) | Spelljack (2002) | Counter's rider branch drops its tail: Spelljack and five more lose the instruction after th... | — |
| [#8751](https://github.com/phase-rs/phase/issues/8751) | Apocalypse (1997) | Golbez, Crystal Collector, Apocalypse Demon, Consuming Aberration End Step Trigger BUG | status:needs-triage |
| [#8738](https://github.com/phase-rs/phase/issues/8738) | City of Traitors (1998) | [Card Bug] City of Traitors misses land-play trigger after Cavern of Souls choice | — |
| [#8590](https://github.com/phase-rs/phase/issues/8590) | Safeguard (1997) | Brokers' Safeguard reports supported=true/gap_count=0 while swallowing the exile, the return... | — |
| [#8526](https://github.com/phase-rs/phase/issues/8526) | Coral Fighters (1996), Sealed Fate (1996) | parser: "defending player's" and "target opponent's" library reads bind the controller (Cora... | — |
| [#8493](https://github.com/phase-rs/phase/issues/8493) | Cataclysm (1998) | Sin, Unending Cataclysm — [[Sin, Unending Cataclysm]] does not give the option to remove cou... | status:needs-triage |
| [#8453](https://github.com/phase-rs/phase/issues/8453) | Syncopate (2001) | Syncopate does not respect paying with Gilded Goose — In the attached game state AI will att... | status:needs-triage |
| [#8448](https://github.com/phase-rs/phase/issues/8448) | Instigator (1999) | Firkraag getting counters for any creature doing any damage to their opponent(s) — [[Firkraa... | status:needs-triage |
| [#8433](https://github.com/phase-rs/phase/issues/8433) | Credit Voucher (1999) | Credit Voucher Ability — Steps to Reproduce: Casting Credit Voucher and paying cost to use a... | status:needs-triage |
| [#8420](https://github.com/phase-rs/phase/issues/8420) | Honor Guard (2003) | Crimson honor guard — It is in play and not dealing damage even though no on e but me had th... | status:needs-triage |
| [#8419](https://github.com/phase-rs/phase/issues/8419) | Carrion Feeder (2003) | Can't play card — I can't cast the carrion feeder in my hand. | status:needs-triage |
| [#8402](https://github.com/phase-rs/phase/issues/8402) | Auriok Steelshaper (2003) | Auriok steelshaper — Keeps targeting even though it doesn't have an activated ability. | status:needs-triage |
| [#8166](https://github.com/phase-rs/phase/issues/8166) | Override (2003) | Cluster: copiable-values override/reset defects across copy effects (Aug 2026 Discord batch) | — |
| [#7902](https://github.com/phase-rs/phase/issues/7902) | Tangle Wire (2000) | Tangle Wire — During their upkeep, the opponent does not choose which permanents to tap. | status:needs-triage |
| [#7868](https://github.com/phase-rs/phase/issues/7868) | Toymaker (1999) | The celestial toymaker — [[The celestial toymaker]] currently lets you take one of the three... | status:needs-triage |
| [#7860](https://github.com/phase-rs/phase/issues/7860) | Invigorate (1999) | Invigorate — Says there is no ABI for rather than pay this spell's mana part of the spell | status:needs-triage |
| [#7854](https://github.com/phase-rs/phase/issues/7854) | Superior Numbers (1996) | Superior Numbers — SN sorcery cast by opp would have dealt 1 damage to one target of my crea... | status:needs-triage |
| [#7850](https://github.com/phase-rs/phase/issues/7850) | Stitch Together (2002) | Stitch Together  bug — This card seems bugged atm. | status:needs-triage |
| [#7809](https://github.com/phase-rs/phase/issues/7809) | Cabal Coffers (2002) | [Card Bug] Cabal Coffers | status:needs-triage |
| [#7675](https://github.com/phase-rs/phase/issues/7675) | Delirium (1996) | Winter Cynical Oppotunist and Into The Pit — Winter delirium allowed the player to exile the... | status:needs-triage |
| [#7662](https://github.com/phase-rs/phase/issues/7662) | Massacre (2000) | swarmyard massacre not resolving correctly — This may be a bug due to the creature with prot... | status:needs-triage |
| [#7644](https://github.com/phase-rs/phase/issues/7644) | Massacre (2000) | Meathook massacre — No life gained from eney units dying. | status:needs-triage |
| [#7643](https://github.com/phase-rs/phase/issues/7643) | Opportunist (1997) | Morbid opportunist — Not triggering to draw a card when a creature dies. | status:needs-triage |
| [#7460](https://github.com/phase-rs/phase/issues/7460) | Thran Tome (1997) | Parser: ChooseFromZone chooser defaults to Controller where the card names an opponent (Intu... | — |
| [#7458](https://github.com/phase-rs/phase/issues/7458) | Choking Vines (1997) +1 | Engine: DamageAll/DestroyAll tracked-set consumers are invisible to next_sub_needs_tracked_s... | — |
| [#5922](https://github.com/phase-rs/phase/issues/5922) | Sleeper Agent (1998) | Xantcha, sleeper agent — game gets an engine connnection lost, and has an action failed error. | status:needs-runtime-verify, area:engine, priority:p0-panic |
| [#4131](https://github.com/phase-rs/phase/issues/4131) | Illicit Auction (1999), Mages' Contest (2000) | engine: open-bid life auction unimplemented (Illicit Auction, Pain's Reward, Mages' Contest) | area:engine, area:parser |
| [#2814](https://github.com/phase-rs/phase/issues/2814) | Decompose (2001) | [Refactor] Decompose casting.rs into CR 601.2-aligned submodules — split 41k-line casting mo... | area:engine |
| [#5487](https://github.com/phase-rs/phase/issues/5487) | Jet Medallion (1997), Land Tax (1995), Phyrexian Tower (1998) | Stuck decision: ModalFaceChoice | status:confirmed, area:engine, area:frontend |
| [#4554](https://github.com/phase-rs/phase/issues/4554) | Windborn Muse (2003) | Stuck decision: CombatTaxPayment | status:confirmed, area:engine, area:frontend |
| [#7456](https://github.com/phase-rs/phase/issues/7456) | Song of Blood (1997) | Parser: CreateDelayedTrigger's hand-set `uses_tracked_set: false` leaves 9 cards' inner trac... | status:confirmed, area:engine, area:parser |
| [#5678](https://github.com/phase-rs/phase/issues/5678) | Aladdin's Lamp (1995), Mangara's Tome (1996), Words of War (2002) | Alms Collector: 'would draw two or more cards' antecedent never parses to a Draw replacement... | status:confirmed, area:engine, area:parser |
| [#774](https://github.com/phase-rs/phase/issues/774) | Vanishing (1997) | Does not recognize time counters as targets for proliferate — [[Kilo, Apogee Mind]] with [[D... | status:confirmed, area:engine, priority:p3-card-specific |
| [#3671](https://github.com/phase-rs/phase/issues/3671) | Inspirit (2002) | Simulacrum Synthesizer — **Steps to Reproduce:** I had **Simulacrum Synthesizer** on the bat... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#6659](https://github.com/phase-rs/phase/issues/6659) | Feedback (1997) | Deck builder copy-limit affordance: alias spellings counted separately, search-add ungated | status:confirmed, area:engine, area:deckbuilder |
| [#6463](https://github.com/phase-rs/phase/issues/6463) | Fyndhorn Elves (1995) | Declare Attackers — The game asks me if I would like to attack when I have no eligible attac... | status:confirmed, area:engine, area:frontend |
| [#7739](https://github.com/phase-rs/phase/issues/7739) | Massacre (2000) | Toski, Bearer of Secrets | status:confirmed, area:engine |
| [#8785](https://github.com/phase-rs/phase/issues/8785) | Override (2003) | [Card Bug] Weathered Sentinels: attack permission is parsed as a Defender grant | — |
| [#8741](https://github.com/phase-rs/phase/issues/8741) | Fickle Efreet (2000), Rogue Skycaptain (1996), Rohgahh of Kher Keep (1994) | Akroan Horse: ETB chooses an opponent but fails to transfer control | — |
| [#8707](https://github.com/phase-rs/phase/issues/8707) | Contamination (1998) | check-parser-combinators.sh silently skips its own seam suite when the suite or python3 is a... | — |
| [#8701](https://github.com/phase-rs/phase/issues/8701) | Kaervek's Spite (1997) | parse_additional_cost_line turns an unreadable cost into no cost, making three spells castab... | — |
| [#8653](https://github.com/phase-rs/phase/issues/8653) | Feedback (1997) | P2P hosting fails on Linux desktop: WebKitGTK's enable-webrtc defaults to false and wry neve... | — |
| [#8584](https://github.com/phase-rs/phase/issues/8584) | Helm of Obedience (1996), Hungry Hungry Heifer (1998), Inheritance (1996) +1 | Sacrifice{SelfRef} inherits the parent instruction's object target and sacrifices the wrong ... | — |
| [#8449](https://github.com/phase-rs/phase/issues/8449) | Reflexes (2003) | Taskmaster, Mercenary Mimic — able to copy a creature on the battlefield | status:needs-triage |
| [#8443](https://github.com/phase-rs/phase/issues/8443) | Opportunity (2001) | Astral Cornucopia not seen as valid mana for casting spells — I have 6 charge counters on [[... | status:needs-triage |
| [#8170](https://github.com/phase-rs/phase/issues/8170) | Celestial Convergence (2000), Goblin Game (2001), Loxodon Peacekeeper (2003) +6 | parser: superlative-comparison player subject ("the player who/with … gains control / takes ... | — |
| [#7893](https://github.com/phase-rs/phase/issues/7893) | Food Chain (1999) | Misthollow griffin doesn't allow cast from exile. — The whole point of misthollow griffin is... | status:needs-triage |
| [#7891](https://github.com/phase-rs/phase/issues/7891) | Timberwatch Elf (2003) | Thranduil, the elven king not showing all activated abilities of all elf cards in your grave... | status:needs-triage |
| [#7864](https://github.com/phase-rs/phase/issues/7864) | Krosan Tusker (2002) | Ellie and Alan, Paleontologists — The Active Abillity of the Card is not working. | status:needs-triage |
| [#7789](https://github.com/phase-rs/phase/issues/7789) | Disappear (1999) | [Card Bug] Cannot properly cash-in Storage Land counters | status:needs-triage |
| [#7785](https://github.com/phase-rs/phase/issues/7785) | Mobilize (1997) | [Card Bug] Zurgo Thunder's Decree does not work as intended | status:needs-triage |
| [#7619](https://github.com/phase-rs/phase/issues/7619) | Necromancy (1997) | Necromany targetting Worldspine wurm — Worldspine Wurm is discarded on cleanup step of my turn. | status:needs-triage |
| [#7610](https://github.com/phase-rs/phase/issues/7610) | Lightning Greaves (2003) | [Card Bug] Monk gyatso airbend | status:needs-triage |
| [#7521](https://github.com/phase-rs/phase/issues/7521) | Opportunity (2001) | AI crews a Vehicle with every creature it controls, then declares no attackers | — |
| [#7492](https://github.com/phase-rs/phase/issues/7492) | Archivist (2003) | Paused player_scope fan-out loses completed seats' per-player counts | — |
| [#7468](https://github.com/phase-rs/phase/issues/7468) | Choking Vines (1997), Energy Arc (1996), Shower of Coals (2001) +2 | Engine: 5 tracked-set consumer shapes are invisible to `next_sub_needs_tracked_set`, so prod... | — |
| [#7466](https://github.com/phase-rs/phase/issues/7466) | Bamboozle (2001) | Engine: the tracked-set publish arm for head `Reveal` is unshipped — 0 observable fixes, and... | — |
| [#7465](https://github.com/phase-rs/phase/issues/7465) | Opportunist (1997) | Engine: the tracked-set publish arm for head `CopySpell` is unshipped — 4 rows not structura... | — |
| [#7464](https://github.com/phase-rs/phase/issues/7464) | Terminate (2001) | Engine: the tracked-set publish arm for head `TargetOnly` is unshipped — 82 gated rows, the ... | — |
| [#7463](https://github.com/phase-rs/phase/issues/7463) | Bamboozle (2001), Goblin Machinist (2002) | Engine: the tracked-set publish arm for head `Pump` is unshipped — 38-row upper bound, 2 mea... | — |
| [#7462](https://github.com/phase-rs/phase/issues/7462) | Slaughter (1998) | Engine: any chain tracked set — including an empty one — pre-empts ChooseFromZone's zone sca... | — |
| [#5169](https://github.com/phase-rs/phase/issues/5169) | Accumulated Knowledge (2000), Control Magic (1995), Crystal Spray (2000) +3 | New Format Plan: Dandan | area:engine |
| [#3042](https://github.com/phase-rs/phase/issues/3042) | Riptide Shapeshifter (2002) | Extend RevealUntil parser coverage (+ multi-match count) for "reveal until you reveal …" cards | area:engine, area:parser |
| [#2816](https://github.com/phase-rs/phase/issues/2816) | Terminate (2001) | feat(engine): multi-match Ripple — cast all same-named revealed cards (CR 702.60a) | area:engine |
| [#1148](https://github.com/phase-rs/phase/issues/1148) | Lightning Greaves (2003), Mask of Memory (2003) | Sigarda's Aid + Cloud, Ex-SOLDIER memory issue? — im not exactly sure what caused it, nor ca... | status:needs-runtime-verify, area:engine, priority:p0-panic |

## Partial coverage — verify what the test asserts (51)

| issue | card(s) | title | labels |
|---|---|---|---|
| [#6377](https://github.com/phase-rs/phase/issues/6377) | Isochron Scepter (2003) | Isochron scepter used on opponents turn broke game — [[isochron scepter]] | status:needs-repro, area:engine, priority:p0-softlock |
| [#8101](https://github.com/phase-rs/phase/issues/8101) | Candelabra of Tawnos (1994) | High-trigger-volume interactions (e.g. Candelabra of Tawnos, X≈80) cause multi-minute engine... | status:confirmed, area:engine, priority:p1-core-mechanic |
| [#7365](https://github.com/phase-rs/phase/issues/7365) | Doomsday (1999) | Doomsday Excruciator bug — It exiled all permanents on the board + all but the bottom of my ... | status:confirmed, area:engine, area:parser |
| [#8078](https://github.com/phase-rs/phase/issues/8078) | Wash Out (2000) | Wash Out — bounces all permanents instead of only the chosen color | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#6374](https://github.com/phase-rs/phase/issues/6374) | Leviathan (1997) | summon: leviathan bounces everything that isn't a Kraken — [[summon: leviathan]] even though... | status:confirmed, area:engine, area:parser |
| [#1102](https://github.com/phase-rs/phase/issues/1102) | Doomsday (1999) | Doomsday — My opponent cast Doomsday and exiled a few cards from their deck (they were left ... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#698](https://github.com/phase-rs/phase/issues/698) | Dark Ritual (1999), Victimize (1998) | Cards that did not work during a play through — Victimize and dark ritual both went to grave... | status:needs-repro, area:engine, priority:p2-wrong-game-result |
| [#8134](https://github.com/phase-rs/phase/issues/8134) | Mountain (2003) | Revealed cards stay visible even after the information should no longer be current (Mountain... | status:confirmed, area:frontend, priority:p3-card-specific |
| [#7188](https://github.com/phase-rs/phase/issues/7188) | Demonic Tutor (1994), Three Visits (1999) | three visits — [[three visits]] lets you search entire deck for any card like a demonic tutor. | status:confirmed, area:engine, priority:p3-card-specific |
| [#5914](https://github.com/phase-rs/phase/issues/5914) | City of Brass (2003) | City of Brass Autopass — The game doesn't autopass for me when I have no abilities or spells... | status:confirmed, area:engine, area:frontend |
| [#604](https://github.com/phase-rs/phase/issues/604) | Calming Licid (1998) | [Card Bug] calming licid cannot attack (entered game on my last turn) | status:confirmed, area:engine, priority:p3-card-specific |
| [#8153](https://github.com/phase-rs/phase/issues/8153) | Force of Nature (1997) | Storm, Force of Nature — storm doesn't seem to carry over into Main Phase 2 | status:needs-repro, area:engine, priority:p3-card-specific |
| [#6484](https://github.com/phase-rs/phase/issues/6484) | Peregrine Drake (1998), Tortured Existence (1998) | Hashaton/Peregrine Drake/Tortured Existence. — Im not able to select peregrine drake as the ... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#5969](https://github.com/phase-rs/phase/issues/5969) | Harrow (2000) | Harrow / Automatic mana tapper — Steps to Reproduce: | status:needs-repro, area:engine, area:frontend |
| [#5238](https://github.com/phase-rs/phase/issues/5238) | Forgotten Ancient (2003) | Forgotten Ancient Delve — Casting Tasigur, the Golden Fang does not trigger Forgotten Ancient. | status:needs-repro, area:engine, priority:p3-card-specific |
| [#7731](https://github.com/phase-rs/phase/issues/7731) | Overload (2000) | Winds of Abandon overload | status:confirmed, area:engine |
| [#8589](https://github.com/phase-rs/phase/issues/8589) | Equilibrium (2001), Land Equilibrium (1994) | Land Equilibrium binds its forced sacrifice to the entering land's controller instead of the... | — |
| [#8437](https://github.com/phase-rs/phase/issues/8437) | Goblin Bombardment (1997) | Goblin Bombardment — Sacrifices the creature with no effect | status:needs-triage |
| [#8394](https://github.com/phase-rs/phase/issues/8394) | Overload (2000) | Eldritch Immunity — [[Eldritch Immunity]] overload does not protect each creature and still ... | status:needs-triage |
| [#7842](https://github.com/phase-rs/phase/issues/7842) | Worn Powerstone (1998) | Archelos, Lagoon Mystic — A,LM was untapped, and opp cast Worn Powerstone, which would enter... | status:needs-triage |
| [#7680](https://github.com/phase-rs/phase/issues/7680) | Forgotten Ancient (2003) | Vorinclex, Monstrous Raider / Forgotten Ancient interaction — When moving counters from [[Fo... | status:needs-triage |
| [#7677](https://github.com/phase-rs/phase/issues/7677) | Solitary Confinement (2002) | Solitary Confinement — It doesn't seem to work: the opponent deals damage to me with Gutters... | status:needs-triage |
| [#7626](https://github.com/phase-rs/phase/issues/7626) | Oath of Druids (1998) | Oath of Druids ability issues — When the ability triggered on opponent's turn it still asked... | status:needs-triage |
| [#7620](https://github.com/phase-rs/phase/issues/7620) | Recurring Nightmare (1998) | Recurring Nightmare on Worldspine Wurm creates duplicate triggers — Duplicate Worldspine Wur... | status:needs-triage |
| [#6834](https://github.com/phase-rs/phase/issues/6834) | Lotus Petal (1997) | Game stuck: Cannot pay mana cost | status:confirmed, area:engine, priority:p0-softlock |
| [#7354](https://github.com/phase-rs/phase/issues/7354) | Abundance (1998) | Autopass — If I have Shang-Chi, Master of Kung-Fu in play as my only unused mana source, the... | status:confirmed, area:engine, area:ai |
| [#6413](https://github.com/phase-rs/phase/issues/6413) | Mountain (2003) | Elegant Parlor — Double triggers and the triggers are delayed to after you pass priority whe... | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#686](https://github.com/phase-rs/phase/issues/686) | Memory Jar (1999) | Cards that don't work as intended. — Dark deal - Only the caster discards all card and you d... | status:confirmed, area:parser, priority:p2-wrong-game-result |
| [#8127](https://github.com/phase-rs/phase/issues/8127) | Counterspell (2001) | Norn's Decree grants a poison counter from non-combat damage (Vivi Ornitier's spell-cast dam... | status:needs-repro, area:engine, priority:p2-wrong-game-result |
| [#8121](https://github.com/phase-rs/phase/issues/8121) | Overload (2000) | March of Progress used by the AI targeting Etherium Sculptor made no token | status:needs-repro, area:engine, priority:p2-wrong-game-result |
| [#7424](https://github.com/phase-rs/phase/issues/7424) | Swords to Plowshares (1995) | Happy Yargle Day! — the random named-card choice is unparsed; "copy the chosen card ... you ... | status:confirmed, area:parser, priority:p3-card-specific |
| [#6983](https://github.com/phase-rs/phase/issues/6983) | Counterspell (2001) | [Card Bug] Unless payments derived from board state are unsupported | status:confirmed, area:engine, area:parser |
| [#6502](https://github.com/phase-rs/phase/issues/6502) | White Knight (2003) | Valiant Endeavor — spell does nothing on resolution | status:confirmed, area:engine, area:parser |
| [#6369](https://github.com/phase-rs/phase/issues/6369) | Opportunity (2001), Sol Ring (1994) | Activating Strionic Resonator — I'm not sure how [[Strionic Resonator]] identifies an eligib... | status:needs-repro, area:engine, priority:p3-card-specific |
| [#7758](https://github.com/phase-rs/phase/issues/7758) | Curiosity (2003) | Grima, Saruman's footman | status:confirmed, area:engine |
| [#7730](https://github.com/phase-rs/phase/issues/7730) | Curiosity (2003) | Blight Effects | status:confirmed, area:engine |
| [#7729](https://github.com/phase-rs/phase/issues/7729) | Sol Ring (1994) | Dopplegang | status:confirmed, area:engine |
| [#8656](https://github.com/phase-rs/phase/issues/8656) | Swords to Plowshares (1995) | change_zone::resolve affects an illegal target when CR 608.2b re-validation drops it (bypass... | — |
| [#8626](https://github.com/phase-rs/phase/issues/8626) | Exploration (1998), Lightning Bolt (1995), Mountain (2003) +2 | AI: Native Medium measurement pilot passes an available lethal Bolt in a four-player witness | — |
| [#8596](https://github.com/phase-rs/phase/issues/8596) | Lightning Bolt (1995) | Composite name resolution accepts unpaired halves, letting decklist typos bypass unknown-car... | — |
| [#8587](https://github.com/phase-rs/phase/issues/8587) | Chaos Orb (1993), Confound (2001), Crazed Armodon (1997) +5 | destroy::resolve skips its self-destroy and destroys the inherited parent target when abilit... | — |
| [#8585](https://github.com/phase-rs/phase/issues/8585) | Fatespinner (2003), Primal Clay (1999), Teferi's Realm (1997) | Mystic Barrier's upkeep re-choice never reaches the permanent — named_choice_authority treat... | — |
| [#8561](https://github.com/phase-rs/phase/issues/8561) | Grizzly Bears (2003) | Devour-shape entrant with an external ETB-counter source still strands its resolution stack | — |
| [#8512](https://github.com/phase-rs/phase/issues/8512) | Overload (2000) | CastingVariant::Surge is never elected as a sole candidate, so Surge casts fall through to N... | — |
| [#8400](https://github.com/phase-rs/phase/issues/8400) | Exploration (1998) | Wildgrowth Walker — Wildgrowth Walker not adding additional life and adding +1/+1 counters t... | status:needs-triage |
| [#8261](https://github.com/phase-rs/phase/issues/8261) | Awesome Presence (1996), Graxiplon (2002), Mana Leak (2003) +4 | Parser: fold the unless-clause payer-subject onto a single authority | — |
| [#8003](https://github.com/phase-rs/phase/issues/8003) | Lightning Bolt (1995) | Action-worded mill trigger binds "it" to the milled card instead of the trigger source (wron... | — |
| [#7587](https://github.com/phase-rs/phase/issues/7587) | Formation (1995), Wall of Blossoms (1998) | Creatures with Defender are listed in valid_attacker_ids at DeclareAttackers (v0.59.0) | — |
| [#7509](https://github.com/phase-rs/phase/issues/7509) | Library of Leng (1997) | A parked CR 616.1 replacement choice is destroyed by the spell's own CR 608.2n graveyard move | — |
| [#7481](https://github.com/phase-rs/phase/issues/7481) | Oubliette (1993) | Event-less effect heads publish an empty tracked set: DoublePTAll (God-Eternal Rhonas) and s... | — |
| [#5056](https://github.com/phase-rs/phase/issues/5056) | Conspiracy (1999) | Implement the Vanguard variant (CR 902) | area:engine, area:card-data, area:frontend |

## Cites an issue — run the direction check (17)

| issue | card(s) | title | labels |
|---|---|---|---|
| [#8058](https://github.com/phase-rs/phase/issues/8058) | Swords to Plowshares (1995) | Swords to Plowshares still grants life when the spell fizzles before resolution | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#5653](https://github.com/phase-rs/phase/issues/5653) | Chains of Mephistopheles (1994) +2 | Chains of Mephistopheles / Magus of the Chains: result-referential conditions silently dropp... | status:confirmed, area:engine, area:parser |
| [#8147](https://github.com/phase-rs/phase/issues/8147) | Mobilize (1997) | Voice of Victory (Mobilize) — Warrior tokens are never sacrificed at the next end step | status:fixed-unreleased, area:engine, priority:p2-wrong-game-result |
| [#1098](https://github.com/phase-rs/phase/issues/1098) | Land Grant (1999) | Land Grant — Alternative cost - show hand with no land cards - doesn't work | status:confirmed, area:engine, priority:p3-card-specific |
| [#5965](https://github.com/phase-rs/phase/issues/5965) | Swords to Plowshares (1995) | Swords to Plowshares — Steps to Reproduce: | status:needs-repro, area:engine, priority:p3-card-specific |
| [#1674](https://github.com/phase-rs/phase/issues/1674) | Decompose (2001) | parser/oracle_static.rs` monolith (1016 KB) — decompose into per-category module hierarchy p... | area:parser |
| [#4886](https://github.com/phase-rs/phase/issues/4886) | Disappear (1999) | [Card Bug] Stuck at choosing Jinnie's replacement effect | status:confirmed, area:engine, priority:p0-softlock |
| [#7453](https://github.com/phase-rs/phase/issues/7453) | Formation (1995) | Parser: "<subject> can't block it" (pronoun object) collapses to a self-scoped CantBlock — 1... | status:confirmed, area:engine, area:parser |
| [#1235](https://github.com/phase-rs/phase/issues/1235) | Lion's Eye Diamond (1996), Mountain (2003), Phyrexian Altar (2000) | feasible_mana_capacity sum over-counts chain-sacrifice configurations | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#1234](https://github.com/phase-rs/phase/issues/1234) | Ashnod's Altar (1999), Lion's Eye Diamond (1996), Phyrexian Altar (2000) | feasible_mana_capacity: colored-shard feasibility under non-tap mana sources | status:confirmed, area:engine, priority:p2-wrong-game-result |
| [#1272](https://github.com/phase-rs/phase/issues/1272) | Delirium (1996) | [Card Bug] Violent Urge giving Double Strike to all creatures | status:needs-runtime-verify, area:engine, priority:p3-card-specific |
| [#8775](https://github.com/phase-rs/phase/issues/8775) | Lightning Bolt (1995) | Ogre Battlecaster: "where X is that spell's mana value" resolves X to 0 — the delayed trigge... | — |
| [#7962](https://github.com/phase-rs/phase/issues/7962) | Quicksilver Elemental (2003) | Parser: injected duration defaults are indistinguishable from printed windows (16 sites; 4 c... | — |
| [#7923](https://github.com/phase-rs/phase/issues/7923) | Abeyance (1997), Override (2003) | Seam: leading duration silently discards trailing ", and" conjuncts and arbitrary trailing t... | — |
| [#7721](https://github.com/phase-rs/phase/issues/7721) | Anavolver (2001), Cetavolver (2001), Faerie Squadron (2000) +4 | Kicker cycle: "enters with ... and with <ability>" silently drops the granted ability (9 cards) | — |
| [#7510](https://github.com/phase-rs/phase/issues/7510) | Library of Leng (1997) | Declining an optional discard replacement drops the remaining discards of a multi-card discard | — |
| [#6287](https://github.com/phase-rs/phase/issues/6287) | Override (2003) | Preview/staging server image cannot self-bootstrap data (needs a signed staging data manifest) | area:sync, area:multiplayer |
