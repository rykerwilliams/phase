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
| Mercenaries / Total War / Typhoon — wrong player/controller scope (misparse backlog root-cause #9) — PR open, not yet merged | old-school-1993-95 | in-progress | rykerwilliams-old-school | 2026-07-11 | `fix/mercenaries-total-war-typhoon-player-scope` | phase-rs/phase#5646 |
| Merieke Ri Berit — "can't be regenerated" failed to bind to the Destroy nested in its delayed trigger (originally misfiled as category #6's or-disjunction, which was already correct) — PR open, not yet merged | old-school-1993-95 | in-progress | rykerwilliams-old-school | 2026-07-12 | `fix/merieke-ri-berit-cant-regenerate` | phase-rs/phase#5717 |
| Power Leak — confirmed two bugs: (1) `PreventDamage.amount` uses `Next(1)` ("prevent the next 1 damage" shield semantic) instead of a dynamic ref to the mana amount paid via the preceding `PayCost`; (2) `PreventDamage.target` is `Any` instead of `TriggeringPlayer` (the sibling `DealDamage` effect correctly uses `TriggeringPlayer` — looks like a dropped "that damage" anaphor, similar in shape to the Maze of Ith "that creature" fix, PR #5484) | old-school-1993-95 | in-progress | rykerwilliams-old-school | 2026-07-12 | `fix/power-leak-dynamic-prevention` | — |
| Necromancy — plain Enchantment ETB-becomes-Aura reanimator (issue #640), structurally different from Animate Dead (`Effect::ReturnAsAura` shape, not the Enchant-keyword chain #5449 built) | old-school-1993-95 | open | — | — | — | — |
| Nether Spirit — dropped intervening-if ("only creature card in your graveyard" self-reanimation trigger); confirmed via `card-data.json` (`condition: null`), part of open cluster issue #1384 | misparse-general | open | — | — | — | — |
| Worldgorger Dragon + Animate Dead — the famous notorious combo (ETB exiles all your other permanents incl. the attached Animate Dead → Aura's own LTB delayed-sacrifice fires → Dragon sacrificed → Dragon's own LTB mass-returns everything). Individually-correct primitives (`ChangeZoneAll`/`TrackedSet`, Animate Dead's destination-agnostic delayed trigger) architecturally look right, but **zero runtime test exists anywhere** for this interaction — discovered while scanning a decklist that plays both cards together. Needs a discriminating integration test before trusting it; may reveal a real gap once actually driven end-to-end (same lesson as the Animate Dead fix itself: individually-correct pieces can still fail composed). | misparse-general | open | — | — | — | — |
| **[Discovered, engine bug, not misparse]** Damage-redirection `ShieldKind::Prevention` static abilities (Pariah, Palisade Giant, Veteran Bodyguard, Weathered Bodyguards) never actually deal the redirected damage to `redirect_target` — `game/replacement.rs`'s CR 614.9 redirection branch only fires for `ShieldKind::Redirection`, never `ShieldKind::Prevention`, so `redirect_target: SelfRef` is dead data for this whole class. The creature the damage is "redirected to" never takes damage, can never die from it, and never triggers "dealt damage" abilities off it. Confirmed via direct code trace during the Veteran Bodyguard fix (see that PR, once opened, for the exact file:line citations). Needs its own plan+review — touches shared resolver code (`game/replacement.rs`, `damage_done_applier`), affects multiple already-shipped cards. | old-school-1993-95 | open | — | — | — | — |
| **[Discovered, engine bug, not misparse]** `TargetFilter::TriggeringPlayer` (and likely other event-context refs, e.g. `EventContextAmount`) resolves to the WRONG player when a triggered ability's resolution pauses on a mid-chain player choice (confirmed via `WaitingFor::PayAmountChoice`/`GameAction::SubmitPayAmount`) and then resumes — `engine_resolution_choices::handle_resolution_choice`'s `finish_with_continuation` doesn't restore `state.current_trigger_event` before resolving the rest of the chain, and `PendingContinuation` (`types/game_state.rs:1052`) doesn't carry it at all, so `TriggeringPlayer` finds no event and falls back to the ability's source controller instead of the actual triggering player. Confirmed via a direct A/B GameRunner test during the Power Leak fix: Warp Artifact (no payment step) correctly resolves to the enchanted controller; Power Leak (same trigger shape, but with a "may pay any amount of mana" pause first) incorrectly resolves to the Aura's own controller. Blast radius not yet fully mapped — affects any triggered ability that pauses on a mid-resolution choice and then reads event context afterward. Needs its own plan+review — touches shared continuation/resolution-choice state machine (`engine_resolution_choices.rs`, `PendingContinuation`), not a single-card fix. Blocking Power Leak's runtime correctness (parser-only fixes for that card are otherwise done, see the in-progress row above). | old-school-1993-95 | open | — | — | — | — |

## Done

| Item | Track | PR |
|---|---|---|
| Animate Dead / Dance of the Dead reanimation (#4767) | old-school-1993-95 | phase-rs/phase#5449 (merged) |
| Glasses of Urza reveal-hand (#5251) | old-school-1993-95 | phase-rs/phase#5464 (merged) |
| Maze of Ith untap + bidirectional prevent (#1094) | old-school-1993-95 | phase-rs/phase#5484 (merged) |
| Winter Orb / Static Orb untap restriction | old-school-1993-95 | phase-rs/phase#5394 (merged) |
| "Blocks or becomes blocked by [filter]" trigger class (Cockatrice, Venom, Mammoth Harness, Karn Silver Golem, +3 more) | old-school-1993-95 | phase-rs/phase#5423 (merged) |
| Nettling Imp / Norritt / Arcum's Whistle continuity-controlled target filter | old-school-1993-95 | phase-rs/phase#5463 (merged) |
| Circle of Protection / Rune of Protection qualified "source of your choice" damage prevention (13 cards) | old-school-1993-95 | phase-rs/phase#5488 (merged) |
| Veteran Bodyguard / Weathered Bodyguards — dropped tap-gate + unblocked/combat source restriction on damage redirection | old-school-1993-95 | phase-rs/phase#5518 (merged); small follow-up fixing 2 post-merge review comments (wrong CR citation, Pattern 3 dropping as-long-as gate) at phase-rs/phase#5531 |
| Land's Edge — dropped intervening-if (misparse backlog root-cause #2) | old-school-1993-95 | phase-rs/phase#5547 (merged, test-only -- confirmed the existing CostPaidObjectMatchesFilter building block already handles this card correctly, zero production code changed; reduced from 573 to 114 lines per maintainer review before merge) |
| Fireball — dynamic "for each" cost dropped (misparse backlog root-cause #5) | old-school-1993-95 | phase-rs/phase#5545 (merged) |
| Fireball — runtime gameplay cost still doesn't scale with target count (separate engine bug, split out of #5545) | old-school-1993-95 | phase-rs/phase#5556 (merged) |
| Land Equilibrium — dropped chained "then" clause (misparse backlog root-cause #4) | old-school-1993-95 | phase-rs/phase#5602 (merged) |
