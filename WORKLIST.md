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

**Current holder:** `custom-format-phase-1d-lead since 2026-09-06T17:46:48Z`

Protocol — before running any compiling cargo command (`build`, `test`,
`clippy`, `run`, anything that isn't `fmt`):

1. Sync this file first (Rule 1).
2. If "Current holder" is `none`, claim it: set it to `<agent-name> since <UTC timestamp>`,
   commit as `cargo-lock: claim (<agent-name>)`, push immediately —
   before running your command, not after. **If you already know your run
   is long, append an estimate, and append your build's PID:
   `<agent-name> since <UTC timestamp> (expected ~75m, full suite, pid 512357)`.**
   Both optional and both purely additive inside the holder string — an agent
   that ignores them reads the row exactly as before. The estimate is the
   difference between a holder another agent can reason about and one they have
   to interrupt to ask about. The PID is the difference between a lock that is
   *cooperative* and one that is *verifiable*: see Rule 6.
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
   claim. **A holder carrying an `(expected ~Nm)` estimate and still inside
   it is NOT stale — don't query it, just queue.** Also check the holder's
   own history (`git log --grep="cargo-lock"`) before treating a hold as
   abnormal: some tracks legitimately hold for over an hour.

   **Decide staleness by asking the kernel, not by guessing from elapsed
   time.** If the holder published a PID:

   ```bash
   kill -0 <pid> 2>/dev/null && echo alive || echo dead
   readlink /proc/<pid>/cwd          # which worktree owns this build
   ```

   Alive, with a cwd in the holder's own worktree, means the hold is healthy
   no matter how long it has run — queue and say nothing. If the holder did
   not publish a PID you can still usually attribute a build:
   `ps -eo pid,etimes,args | grep -E 'cargo|rustc'`, then `readlink` each
   cwd. **Do this BEFORE messaging the holder.** Elapsed time only ever
   supports a guess; the kernel answers. Even so, a dead PID is grounds for
   a note, not for clearing the row yourself — that is still a human call.

   > **FOR A HUMAN — the 20-minute number is probably wrong now, and two
   > agents hit it independently on 2026-09-06.** `custom-format-phase-1d-lead`
   > reports a ~75-minute uncontended full-suite run, and its actual holds on
   > this board have been 112, 128, 81 and 74 minutes — all legitimate, all
   > tripping this rule by a wide margin. As written, the correct behaviour (a
   > long verified run) is indistinguishable from the failure mode the rule
   > exists to catch, so the only way to tell them apart is to interrupt the
   > holder and ask — which both `custom-format-phase-1d-lead` and
   > `swords-608-2b` had to do. The `(expected ~Nm)` convention added to
   > protocol step 2 above makes them distinguishable without guessing a
   > number, which is why the 20-minute threshold itself has been left ALONE
   > here: raising it affects every agent following this board, and Rule 6's
   > own logic is that a human decides, not one agent unilaterally.
   > — raised by `swords-608-2b`, concurred by `custom-format-phase-1d-lead`
   >
   > **Second, related, and already adopted by both of us: publish your build's
   > PID in the holder string.** Every other safeguard here — the timestamp, the
   > duration estimate, releasing on exit — depends on the holder behaving
   > correctly or dying politely. A PID depends on nothing; the kernel answers.
   > It is the only part of this design that survives a holder being SIGKILLed
   > mid-build, which is exactly what the harness's OOM-class reaper does and
   > exactly what no `trap` can catch (`SIGKILL` is uncatchable, so
   > `trap release EXIT INT TERM HUP` converts only the *graceful* deaths from
   > leaks). On 2026-09-06 a 90-minute hold was resolved as healthy by a single
   > `readlink /proc/<pid>/cwd` after four messages between two agents had failed
   > to settle it. The field is additive inside the holder string, so agents that
   > ignore it are unaffected. Both `swords-608-2b` and
   > `custom-format-phase-1d-lead` now publish it.

This is advisory, not a technical lock — it only works if every agent
actually checks and respects it. Treat holding it like holding a talking
stick: grab it, do the one thing you needed it for, let go.

## Open / in-progress

| Item | Track | Status | Agent | Claimed-At | Branch | PR |
|---|---|---|---|---|---|---|
| **[Engine bug, CR 608.2b, issues #5965 + #8058]** Swords to Plowshares — a spell whose only target became illegal (died, or gained hexproof) in response still resolves instead of being countered on resolution: #8058 gains life off a dead creature, #5965 exiles a creature that gained hexproof. **One defect, not two** — hexproof IS rechecked correctly by `can_target`; the chain-level fizzle is masked. `flatten_targets_in_chain` concatenates targets from `sub_ability`/`else_ability` riders, and Swords' life-gain rider is a context-ref (`GainLife { player: ParentTargetController }`) whose arm in `validate_targets_in_chain` (`ability_utils.rs:2434-2438`) returns its targets UNFILTERED — deliberately, it exists for Flickerwisp. So the validated list is non-empty even when the real target is illegal and `check_fizzle` (`targeting.rs:534`, fizzles iff the legal list is empty) never fires. Class-general: hits every 'target X. <anaphor rider>' spell, not just Swords. Fix is scoped to counting only genuinely-specified targets at the fizzle seam, leaving the Flickerwisp arm intact. Running through `/engine-implementer`; plan is at review round 4, code design frozen since round 2. | fizzle-608-2b | in-progress | swords-608-2b | 2026-09-06 | (not yet cut) | — |
| **[Discovered, engine bug, follow-up from #5850's investigation]** Pariah — real Oracle text is "...is dealt to **enchanted creature** instead," but `parse_damage_redirection_replacement`'s redirect-detection (`oracle_replacement.rs`, `scan_contains(working_lower, "is dealt to ~ instead")`) only recognizes literal self-reference, not "enchanted creature" — so Pariah parses today with `redirect_target: None`, meaning it's a plain, no-op prevention shield with no redirect at all (not even the dead-data version #5850 fixes for the other 3 cards). Needs a parser fix recognizing "enchanted creature" via the existing `TargetFilter::AttachedTo` combinator (already used for this exact phrase elsewhere — `oracle_replacement.rs:4879`/`6134`/`7536` are the precedent sites), plus resolving whether `DamageRedirectTarget` (currently `Controller`/`SourceObject`/`ChosenObjectTarget` only) needs a 4th variant to represent "the object I'm attached to," or whether `AttachedTo` can resolve without going through `DamageRedirectTarget` at all — open design question for whoever picks this up. | old-school-1993-95 | open | — | — | — | — |
| **[Discovered, engine bug, follow-up from #5850's investigation]** Pariah's Shield — mis-scoped in the current parser: it hard-codes `redirect_target: TargetFilter::SelfRef` without ever parsing its actual "any target" clause, and is mechanically a CR 615.5 prevention-with-additional-effect (like Phyrexian Hydra), not a CR 614.9 redirection — applying #5850's fix mechanism to it would actually *regress* it, since Pariah's Shield is an enchantment and would always fail the redirect-recipient legality check (converting "prevents all damage" into "damage passes through unprevented"). Needs its own remodel following the existing Phyrexian Hydra pattern (`extract_prevention_followup`, `oracle_replacement.rs:9112-9201`; the aggregate-stash mechanic, `replacement.rs:1543-1551`, `QuantityRef::EventContextAmount`), including parsing a genuine "any target" choice each time it fires. | old-school-1993-95 | open | — | — | — | — |
| **[Follow-up, engine cleanup, not a bug]** `TargetFilter::TriggeringPlayer`-across-pause bug (see above) is now FIXED in phase-rs/phase#5742 via a new, general `PendingContinuation.trigger_context` mechanism (extends `ResolvingTriggerContext`, wired into `drain_pending_continuation`). That fix deliberately did NOT consolidate two other, narrower pre-existing mechanisms solving the same conceptual problem for two other pause types — `GameState.pending_choose_zone_trigger_context` (used only by `ChooseFromZoneChoice`) and `WaitingFor::ChooseObjectsSelection.trigger_event` (used only by that specific choice type) — both remain fully functional and now give redundant (not conflicting) protection. Consolidating all three onto the single new path is a real, identified follow-up (documented in a doc comment on `ResolvingTriggerContext`, `types/game_state.rs`), deferred to keep the bugfix's blast radius focused. Low urgency — no known correctness gap, purely an architecture-symmetry cleanup. | old-school-1993-95 | open | — | — | — | — |
## Done

| Item | Track | PR |
|---|---|---|
| **[Abandoned — deprioritized by user, 2026-07-19]** Nyssa of Traken (*Doctor Who*, 2023) — upfront target-slot-collection bug (tap/draw sub-ability parses to `AbilityCondition::ZoneChangedThisWay`, collects target slots before the sacrifice count is known, same failure family as the Swashbuckler regression via a different, upfront-collection code path). Confirmed real via a standalone probe, never claimed/started. Not fixed — left here as a record in case anyone wants to pick it up later. | misparse-general | — |
| Aura-attachment host search (`legal_aura_attachment_targets`) only scanned the battlefield on non-cast entry, never graveyards/hand — fixed via `enchant_filter.extract_zones()` + `zone_object_ids`, reusing the `object_count_matching_ids` pattern; class-general (Animate Dead, Dance of the Dead, Necromancy, Spellweaver Volute, Don't Worry About It) | misparse-general | phase-rs/phase#6072 (merged) |
| Worldgorger Dragon self-loop combo — the "famous notorious combo" this whole investigation started from. **Now fully closes end-to-end.** 4 distinct engine defects found and fixed across this one PR (5+ maintainer review rounds, all addressed): (1) mass-exile ETB never got the `Duration::UntilHostLeavesPlay` stamp (`trigger_is_etb_exile_pending_duration` only matched singular `ChangeZone`, not `ChangeZoneAll`) — one-line class-general widening; (2) the widening would have also silently broken Realm Razer (its LTB has an `enter_tapped: true` rider the automatic return can't carry) — maintainer caught this, fixed by requiring zero entry modifiers before pairing; (2b) excluding Realm Razer left it falsely "fully supported" in coverage — fixed by parameterizing the relation with an explicit `ModifierUnsupported` outcome that attaches `Effect::unimplemented(...)` so coverage honestly flags the gap, plus a coverage-level regression test; (3) the returning Aura itself couldn't re-attach to WGD-in-graveyard (`legal_aura_attachment_targets` battlefield-only) — fixed separately as #6072, merged into this branch. Two earlier hypotheses (CR 303.4g graveyard-sweep; keyword-reset-on-exile) were empirically refuted before landing on the real root causes. | misparse-general | phase-rs/phase#6055 (merged) |
| Damage-redirection `ShieldKind::Prevention` static abilities never actually deal the redirected damage (Palisade Giant, Veteran Bodyguard, Weathered Bodyguards) — `redirect_target: SelfRef` was dead data for this whole class; new shared `redirect_damage_event` helper, gated on `redirect_target == SelfRef && amount == All`. Pariah and Pariah's Shield rescoped out mid-investigation as separate follow-up items (need materially different fixes) | old-school-1993-95 | phase-rs/phase#5850 (merged) |
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
