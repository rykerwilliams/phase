# Shared Card-Fix Worklist

Coordination board for concurrent AI agents fixing `phase-rs/phase` cards
from this fork. Lives only on `rykerwilliams/phase`'s `main` — never
appears in a PR to `phase-rs/phase` (every fix branch is cut fresh from
`origin/main`, never from this fork's `main`, so this file is automatically
excluded from PR diffs, same mechanism as `BACKLOG.md`).

**Read the Rules before touching this file.**

## Rules

1. **Sync first, every time.** `git fetch myfork main && git merge --ff-only myfork/main`
   immediately before reading or editing this file — it changes constantly
   and a stale read defeats the whole point.
2. **Check before claiming.** Only claim a row whose Status is `open`.
3. **Never take over another agent's claim.** Don't edit a `claimed` or
   `in-progress` row that isn't yours except to add a short `Note` (e.g.
   flagging a dependency or a suspected-stale claim). If a claim looks
   abandoned (claimed long ago, no branch, no visible progress), don't
   reassign it yourself — leave a note and let a human decide.
4. **Claim atomically, push immediately.** To claim: set Status to
   `claimed`, fill in Agent (a short stable name for your session/track) and
   Claimed-At (date, UTC), commit with message `claim: <item name>`, and
   `git push myfork main` right away, before starting any other work. Git
   has no real locking — the only safety margin is how fast you push after
   checking Status was `open`.
5. **Handle a rejected push.** If the push is rejected, fetch + merge
   --ff-only again. If someone else claimed the *same* row in that window,
   back off and pick a different item — don't fight over it. If the
   conflict was on an unrelated row, just retry your push.
6. **Update status as you go.** `claimed` → `in-progress` (fill in Branch)
   once you've actually started → `done` (fill in PR) *only once the PR is
   actually merged* — an open, unmerged PR stays `in-progress` with the PR
   link filled in, not `done`. The agent who claimed an item owns watching
   its PR through review/CI to merge; don't drop it as soon as the PR opens.
   Use `blocked` / `abandoned` with a one-line reason if you drop it. Never
   leave a stale claim with no explanation for the next agent to find.
7. **Never delete rows.** Move finished/abandoned rows to the "Done" table
   at the bottom instead, so there's a record of what happened to every
   item.
8. **Commit worklist edits separately from code.** A claim/status change is
   its own small commit — never bundle it into a commit that also contains
   a card fix's actual code changes.
9. **Fork-only, forever.** Never reference, quote, or link this file from
   any PR body to `phase-rs/phase`. It's internal coordination only, exactly
   like `BACKLOG.md`.

## Cargo build lock

Each worktree has its own `target/` dir (verified — not shared), but
`~/.cargo`'s package cache/registry *is* shared across every worktree, and
with ~10 worktrees active concurrently, several agents running
`cargo build`/`test`/`clippy` at the same moment causes real lock
contention on that shared cache and can exhaust CPU/RAM (observed:
`clippy-driver.exe` processes at 1.8–5.7 GB each). `cargo fmt` doesn't
compile anything and needs no lock.

**Current holder:** `none`

Protocol — before running any compiling cargo command (`build`, `test`,
`clippy`, `run`, anything that isn't `fmt`):

1. Sync this file first (Rule 1).
2. If "Current holder" is `none`, claim it: set it to `<agent-name> since <UTC timestamp>`,
   commit as `cargo-lock: claim (<agent-name>)`, push immediately —
   before running your command, not after.
3. If the push is rejected, re-sync and check who holds it now. If someone
   else claimed it in that window, **wait and retry later** — don't run
   your cargo command anyway and don't fight over the lock row.
4. Run your command(s).
5. The moment you're done (pass or fail), release it: set "Current holder"
   back to `none`, commit as `cargo-lock: release (<agent-name>)`, push
   immediately. Don't hold the lock longer than the build/test run itself —
   don't hold it across a whole multi-step implementation session.
6. If you find a holder that's been sitting far longer than any real build
   should take (say 20+ minutes) with no explanation, don't clear it
   yourself — leave a note and let a human decide, same as a stale item
   claim.

This is advisory, not a technical lock — it only works if every agent
actually checks and respects it. Treat holding it like holding a talking
stick: grab it, do the one thing you needed it for, let go.

## Open / in-progress

| Item | Track | Status | Agent | Claimed-At | Branch | PR |
|---|---|---|---|---|---|---|
| Worldgorger Dragon + Animate Dead — the famous notorious combo (ETB exiles all your other permanents incl. the attached Animate Dead → Aura's own LTB delayed-sacrifice fires → Dragon sacrificed → Dragon's own LTB mass-returns everything). Individually-correct primitives (`ChangeZoneAll`/`TrackedSet`, Animate Dead's destination-agnostic delayed trigger) architecturally look right, but **zero runtime test exists anywhere** for this interaction — discovered while scanning a decklist that plays both cards together. Needs a discriminating integration test before trusting it; may reveal a real gap once actually driven end-to-end (same lesson as the Animate Dead fix itself: individually-correct pieces can still fail composed). | misparse-general | open | — | — | — | — |
| Damage-redirection `ShieldKind::Prevention` static abilities never actually deal the redirected damage — `game/replacement.rs`'s CR 614.9 redirection branch only fired for `ShieldKind::Redirection`, never `ShieldKind::Prevention`, so `redirect_target: SelfRef` was dead data for this whole class. PR open, CI fully green (6 plan-review rounds, 1 clean impl-review round). **Rescoped mid-investigation to exactly 3 cards** (Palisade Giant, Veteran Bodyguard, Weathered Bodyguards) — Pariah and Pariah's Shield were originally believed affected but turned out to need materially different fixes on independent verification of their real Oracle text (see the 2 new follow-up rows below); this PR does not touch either. | old-school-1993-95 | in-progress | rykerwilliams-old-school | 2026-07-14 | `fix/shield-prevention-redirect` | phase-rs/phase#5850 |
| **[Discovered, engine bug, follow-up from #5850's investigation]** Pariah — real Oracle text is "...is dealt to **enchanted creature** instead," but `parse_damage_redirection_replacement`'s redirect-detection (`oracle_replacement.rs`, `scan_contains(working_lower, "is dealt to ~ instead")`) only recognizes literal self-reference, not "enchanted creature" — so Pariah parses today with `redirect_target: None`, meaning it's a plain, no-op prevention shield with no redirect at all (not even the dead-data version #5850 fixes for the other 3 cards). Needs a parser fix recognizing "enchanted creature" via the existing `TargetFilter::AttachedTo` combinator (already used for this exact phrase elsewhere — `oracle_replacement.rs:4879`/`6134`/`7536` are the precedent sites), plus resolving whether `DamageRedirectTarget` (currently `Controller`/`SourceObject`/`ChosenObjectTarget` only) needs a 4th variant to represent "the object I'm attached to," or whether `AttachedTo` can resolve without going through `DamageRedirectTarget` at all — open design question for whoever picks this up. | old-school-1993-95 | open | — | — | — | — |
| **[Discovered, engine bug, follow-up from #5850's investigation]** Pariah's Shield — mis-scoped in the current parser: it hard-codes `redirect_target: TargetFilter::SelfRef` without ever parsing its actual "any target" clause, and is mechanically a CR 615.5 prevention-with-additional-effect (like Phyrexian Hydra), not a CR 614.9 redirection — applying #5850's fix mechanism to it would actually *regress* it, since Pariah's Shield is an enchantment and would always fail the redirect-recipient legality check (converting "prevents all damage" into "damage passes through unprevented"). Needs its own remodel following the existing Phyrexian Hydra pattern (`extract_prevention_followup`, `oracle_replacement.rs:9112-9201`; the aggregate-stash mechanic, `replacement.rs:1543-1551`, `QuantityRef::EventContextAmount`), including parsing a genuine "any target" choice each time it fires. | old-school-1993-95 | open | — | — | — | — |
| **[Follow-up, engine cleanup, not a bug]** `TargetFilter::TriggeringPlayer`-across-pause bug (see above) is now FIXED in phase-rs/phase#5742 via a new, general `PendingContinuation.trigger_context` mechanism (extends `ResolvingTriggerContext`, wired into `drain_pending_continuation`). That fix deliberately did NOT consolidate two other, narrower pre-existing mechanisms solving the same conceptual problem for two other pause types — `GameState.pending_choose_zone_trigger_context` (used only by `ChooseFromZoneChoice`) and `WaitingFor::ChooseObjectsSelection.trigger_event` (used only by that specific choice type) — both remain fully functional and now give redundant (not conflicting) protection. Consolidating all three onto the single new path is a real, identified follow-up (documented in a doc comment on `ResolvingTriggerContext`, `types/game_state.rs`), deferred to keep the bugfix's blast radius focused. Low urgency — no known correctness gap, purely an architecture-symmetry cleanup. | old-school-1993-95 | open | — | — | — | — |
| **[Discovered, engine bug, not misparse]** Nyssa of Traken (*Doctor Who*, 2023 — NOT old-school, mistagged below previously) ("Whenever Nyssa attacks, sacrifice any number of artifacts. When you sacrifice one or more artifacts this way, tap up to that many target creatures and draw that many cards.") — the tap/draw sub-ability parses to `AbilityCondition::ZoneChangedThisWay` (not `WhenYouDo`/`QuantityCheck` like Swashbuckler Extraordinaire's near-identical shape), which collects its target slots UP FRONT at trigger creation (before the sacrifice/`EffectZoneChoice` even happens) instead of via fresh reflexive target selection after the count is known. Confirmed via a standalone probe: driving the real attack trigger offers exactly 1 target slot (leaking in the attacker count, same underlying mechanism as the Swashbuckler regression but via a different, upfront-collection code path that a `try_begin_reflexive_target_selection`-scoped fix can't reach), and afterward neither the tap nor the "draw that many" effect ever fires (0 cards drawn). Discovered while trying to build a class-generalization sibling test for the Swashbuckler fix (PR #5742) — do NOT conflate with that fix; needs its own plan+review. | misparse-general | open | — | — | — | — |

## Done

| Item | Track | PR |
|---|---|---|
| Power Leak — 3 parser bugs + `TriggeringPlayer`-across-pause runtime bug + 2 CI regressions from the fix itself (Swashbuckler target-count leak, then a roll-die/d20 tier-ordering leak) — all fixed; merged | old-school-1993-95 | phase-rs/phase#5742 (merged) |
| Nether Spirit — dropped intervening-if ("only creature card in your graveyard" self-reanimation trigger, part of cluster issue #1384); new `parse_source_is_only_type_in_zone` combinator, zero runtime changes (reused the existing `SourceInZone`/`trigger_condition_source_zones` derivation path, Jocasta Automaton Avenger precedent) | misparse-general | phase-rs/phase#5884 (merged) |
| Animate Dead / Dance of the Dead reanimation (#4767) | old-school-1993-95 | phase-rs/phase#5449 (merged) |
| Glasses of Urza reveal-hand (#5251) | old-school-1993-95 | phase-rs/phase#5464 (merged) |
| Maze of Ith untap + bidirectional prevent (#1094) | old-school-1993-95 | phase-rs/phase#5484 (merged) |
| Winter Orb / Static Orb untap restriction | old-school-1993-95 | phase-rs/phase#5394 (merged) |
| Necromancy — plain Enchantment ETB-becomes-Aura reanimator (issue #640), new whole-body "grant" recognizer + generalized shared chain builder (`EnchantGrantShape::Swap`/`GrantOnly`); root cause was falling through the Animate Dead-class combinator straight to `Effect::Unimplemented` with no target-bearing effect node ever built | old-school-1993-95 | phase-rs/phase#5778 (merged) |
| "Blocks or becomes blocked by [filter]" trigger class (Cockatrice, Venom, Mammoth Harness, Karn Silver Golem, +3 more) | old-school-1993-95 | phase-rs/phase#5423 (merged) |
| Nettling Imp / Norritt / Arcum's Whistle continuity-controlled target filter | old-school-1993-95 | phase-rs/phase#5463 (merged) |
| Circle of Protection / Rune of Protection qualified "source of your choice" damage prevention (13 cards) | old-school-1993-95 | phase-rs/phase#5488 (merged) |
| Veteran Bodyguard / Weathered Bodyguards — dropped tap-gate + unblocked/combat source restriction on damage redirection | old-school-1993-95 | phase-rs/phase#5518 (merged); small follow-up fixing 2 post-merge review comments (wrong CR citation, Pattern 3 dropping as-long-as gate) at phase-rs/phase#5531 |
| Land's Edge — dropped intervening-if (misparse backlog root-cause #2) | old-school-1993-95 | phase-rs/phase#5547 (merged, test-only -- confirmed the existing CostPaidObjectMatchesFilter building block already handles this card correctly, zero production code changed; reduced from 573 to 114 lines per maintainer review before merge) |
| Fireball — dynamic "for each" cost dropped (misparse backlog root-cause #5) | old-school-1993-95 | phase-rs/phase#5545 (merged) |
| Fireball — runtime gameplay cost still doesn't scale with target count (separate engine bug, split out of #5545) | old-school-1993-95 | phase-rs/phase#5556 (merged) |
| Land Equilibrium — dropped chained "then" clause (misparse backlog root-cause #4) | old-school-1993-95 | phase-rs/phase#5602 (merged) |
| Mercenaries / Total War / Typhoon — wrong player/controller scope (misparse backlog root-cause #9) | old-school-1993-95 | phase-rs/phase#5646 (merged) |
| Merieke Ri Berit — "can't be regenerated" failed to bind to the Destroy nested in its delayed trigger (originally misfiled as category #6's or-disjunction, which was already correct) | old-school-1993-95 | phase-rs/phase#5717 (merged) |
