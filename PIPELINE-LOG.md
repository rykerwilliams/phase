# Card-Fix Pipeline Log

Personal, fork-only log of the `/engine-implementer`-style card-bug-fix
pipeline (plan → review-plan → implement → review-impl → commit → PR).
Lives only on this fork's `main`, same rule as `BACKLOG.md` — never for an
upstream PR. Purpose: track how long each stage actually takes and *why*,
so the pattern feeds back into scoping and instructing future fixes rather
than re-learning the same lessons every time.

## Format

One entry per backlog item, appended as it completes each pipeline stage.
Timing is `duration_ms`/`tool_uses` as reported by the spawned agent's own
usage block — not wall-clock from my perspective, since agents can be
paused/resumed across turns. Treat the numbers as directional (this dev
machine's cargo builds are unusually slow — see recurring lesson below),
not as a scientific benchmark.

---

## Standing lessons (apply to every future fix, check before starting)

1. **Never trust an issue's framing as fact — reproduce it.** Two of three
   investigations tonight found the report was wrong in some way:
   Underworld Breach (#1033) was already fixed upstream; Pact of Negation
   (#1058)'s symptom was real but misattributed to AI when it's a
   parser bug hitting any player. Always build a scratch repro (or trace
   the exact code path) before writing a plan, and say so explicitly if
   the bug doesn't reproduce or reproduces differently than described.
2. **A plan's root-cause narrative can be confidently wrong even when the
   diagnosis and fix are basically right.** Ad Nauseam (#1032) round 1
   claimed `pending_continuation` was last-write-wins/clobbering; it
   actually accumulates via `append_to_sub_chain`. This wasn't cosmetic —
   it would have shipped a non-discriminating test. Independent review
   must re-derive claims from the actual code, not just sanity-check
   plausibility.
3. **Additive/order-independent effects make final-aggregate assertions
   vacuous.** If an effect repeats and its totals (life loss, card count)
   are the same regardless of *when* each step applied, a test must
   assert state at the specific checkpoint where buggy vs. fixed behavior
   diverges (e.g., between iterations), not just the end state. Ask this
   explicitly for any repeat/batch/deferred-effect fix.
4. **Look for whether a narrower point-fix for the same architectural bug
   already exists and was never generalized.** Pact of Negation's bug is
   the same "rider attached to the wrong AST parent" class as a prior fix
   for Ashling, the Limitless (#4369, `unless_pay` hoist) — that fix was
   scoped only to its own clause shape and never extended to the
   two-sentence "If you don't, X." shape the whole Pact cycle uses. When
   a fix cites a "sibling precedent," check whether the precedent itself
   was under-scoped.
5. **Sub-agents don't receive task-notifications for their own background
   children — only the parent session does.** An executor that starts a
   slow background build (clippy, cargo test) and then ends its turn to
   "wait for a notification" will simply stop. Always instruct executors
   to block synchronously (foreground, generous timeout) on long builds
   instead.
6. **This dev machine is slow for Rust builds** — lib compile ~31 min,
   full-workspace clippy ~34 min. Budget for this; prefer scoped/crate- or
   test-filtered commands over full-workspace ones where the plan allows,
   and don't schedule short CI-style polling intervals against local
   builds.
7. **Always use Oracle text verified against Scryfall**, never memory or
   the issue's paraphrase — feed it to every planning agent explicitly
   labeled as verified.
8. **"Verified against Scryfall" isn't enough by itself — the exact
   formatting (embedded newlines between sentences) matters and must be
   preserved.** Pact of Negation (#1058) round 1's entire root-cause
   diagnosis was invalidated because the scratch repro used a
   paraphrased single-line version of the Oracle text instead of the
   verbatim two-line text (`"Counter target spell.\nAt the beginning of
   your next upkeep..."`). The parser dispatches per-line
   (`oracle_text.split('\n')`), so joining two sentences onto one line
   silently routes to a *different* parser code path than the real card
   ever hits — reproducing a bug that doesn't exist on `main` while
   missing whatever the real defect (if any) actually is. Any scratch
   repro or plan must call the real parse entry point
   (`parse_oracle_text`) on the literal multi-line string, never a
   manually reflowed/joined paraphrase, and should ideally paste the
   verbatim value with its newlines shown explicitly to make this
   checkable at review time.
9. **A genuinely generic process/doc fix marked "local-only, not for
   upstream PR" silently stops applying to any real work.** The
   "Verify the card, not just the rule" CLAUDE.md principle and its
   matching `engine-planner` Step 0 hard gate — which would have caught
   lesson 8 directly — were committed to this fork's `main` only
   (`4f5c2e0c7`, by explicit request at the time) alongside genuinely
   fork-specific items like `BACKLOG.md`. But every fix worktree is cut
   fresh from `origin/main`, so that rule never reached any actual fix
   session, including the one that needed it hours later. Lesson: before
   marking a `CLAUDE.md`/skill/doc change "local-only," check whether it
   is actually fork-specific (personal infra, credentials, branding) or
   a generic process improvement — the latter belongs in its own clean
   upstream PR immediately, not bundled with divergent fork state, or it
   will quietly never take effect. Fixed via
   [phase-rs/phase#5342](https://github.com/phase-rs/phase/pull/5342).
10. **A fix can compile clean and pass its own test while sitting on a
    dead code path for the real card.** Relic of Progenitus (#1077):
    the fix modified `inject_subject_target`'s `Effect::ChangeZone` arm,
    and a self-written test asserted a top-level `ChangeZone` effect —
    both looked plausible and the code compiled. CI failed the new test
    on the real parse: the actual emitted shape was
    `Effect::TargetOnly { target: Player }` wrapping a `sub_ability`,
    because `lower_subject_predicate_ast` has an *earlier* return
    (mod.rs:16674, for any "target player" + `ChangeZone`/
    `ChangeZoneAll` combo) that fires before `inject_subject_target` is
    ever reached. The original fix and test were internally consistent
    with each other but never with the production dispatch order.
    Lesson: when a function has multiple early returns before the code
    you're modifying, trace which one the *actual* real-world input
    hits (e.g. via a debug print of the parsed AST, or careful manual
    walk of every guard in order) — do not assume the arm you found via
    grep is the one that executes. Treat a locally-compiling,
    locally-passing test as necessary, not sufficient; CI (or a genuine
    live run against the real emitted AST) is the actual gate. Also:
    background `cargo test`/`cargo check` runs on this session's sandbox
    were repeatedly killed mid-compile at the same point (3+ times in a
    row) even with no explicit timeout set — a real, unexplained
    environment ceiling distinct from the "slow builds" of lesson 6;
    when hit repeatedly, fall back to `cargo check` plus careful manual
    trace rather than retrying indefinitely, and say so explicitly in
    the PR rather than silently shipping unverified.

---

## #1033 — Underworld Breach

- **Outcome:** no code change — already fixed on `main` by `aa4ee3455`.
  Verified independently (ran the actual test suite myself, not just
  trusted the planner). Commented on the GitHub issue with evidence,
  couldn't close (no permissions).
- **Planning stage:** 1 round, ~7.4h agent-reported duration, 61 tool
  calls. (High duration likely reflects this machine's slow test-compile
  cycles during the investigation, not idle time.)
- **Why it took as long as it did:** the planner had to trace the full
  escape-cost pipeline end-to-end (parser → static grant → cast prep →
  additional-cost payment) *and* run the existing regression suite to
  confirm the bug didn't reproduce, rather than a quick grep — proving a
  negative takes real verification, not less.

## #1032 — Ad Nauseam

- **Outcome:** real bug, fixed, tested, merged into the queue as
  [phase-rs/phase#5315](https://github.com/phase-rs/phase/pull/5315).
- **Planning:** round 1 ~29m/65 tools; round 2 (revision after review
  gaps) ~10m/45 tools.
- **Plan review:** round 1 ~13m/47 tools (found the root-cause narrative
  error — see standing lesson 2); round 2 ~8m/46 tools (clean).
- **Implementation:** ~2.4h total across resumed turns — dominated by a
  ~31min lib compile and a ~34min full-workspace clippy run, not by
  actual coding/debugging time. Had to be nudged twice to stop ending its
  turn early to "wait for a notification" (standing lesson 5).
- **Implementation review:** ~37.5m/67 tools, clean bar one LOW
  informational note (theoretical edge-case coverage gap, judged
  low-risk by architectural equivalence, not treated as blocking).
- **End-to-end wall clock (plan start → PR opened):** roughly 4-5 hours,
  the large majority of which was cargo build/test/clippy time on this
  machine rather than agent reasoning time.

## #1058 — Pact of Negation

- **Status:** round 1 plan BLOCKED by review — root cause was diagnosed
  from a corrupted repro, redoing planning from scratch.
- **Planning round 1:** ~64.6m/258 tool calls — notably deeper than Ad
  Nauseam's planning (65 tools) because the agent built and ran an
  actual scratch reproduction test with a printed AST dump. Diagnosed a
  parser AST-wiring bug (the "If you don't, lose the game" rider
  attaching to `CreateDelayedTrigger`'s wrapper instead of nesting
  inside the delayed effect) and identified an under-scoped precedent
  fix (Ashling's `unless_pay` hoist, #4369).
- **Plan review round 1:** ~27.2m/50 tools — **BLOCKED, not just
  gapped.** The reviewer independently ran `parse_oracle_text` on the
  literal verbatim Scryfall text (`"Counter target spell.\nAt the
  beginning of..."`, real embedded newline) and got a *correctly nested*
  AST — the exact opposite of round 1's finding. Root cause: round 1's
  scratch repro used a paraphrased single-line join of the two sentences
  instead of the verbatim multi-line text, which routes to a different
  parser dispatch branch (`oracle_text.split('\n')`-based) than the real
  card ever hits. The reviewer reproduced round 1's claimed bug *only*
  when deliberately re-joining the lines — confirming the diagnosis, not
  just asserting it. See standing lesson 8. Also caught a misapplied CR
  citation (603.12, reflexive triggers) that doesn't fit this card's
  "if you don't" cost-gate shape (that's CR 118.12 territory).
  All open items the round-1 plan deferred to "the implementer" were
  reclassified as blocking, since they were downstream of the same false
  premise.
- **This is the highest-value catch of the night**: round 1's fix would
  have been implemented, tested against its own (wrong) mental model,
  and likely shipped a no-op or actively harmful change to a code path
  the real card never touches, while leaving the actual reported
  behavior (if it's even still broken — not yet re-established) unfixed.
- **Planning round 2 (redo with verbatim text):** ~58.8m/165 tool calls.
  Confirmed the reviewer's finding exactly — the real card's AST is
  already correctly shaped — then pivoted to a full runtime
  `GameRunner` simulation (unpaid → loss, paid → no loss, both
  confirmed correct) and found a pre-existing regression test
  (`issue_3871_summoners_pact.rs`) covering the identical rider shape.
  No AI-specific gap found. **Outcome: no bug, no code change** — same
  shape of result as Underworld Breach. Commented on
  [phase-rs/phase#1058](https://github.com/phase-rs/phase/issues/1058)
  with evidence.
- **Bonus finding:** the round-1 mistake led directly to discovering
  standing lesson 9 (a real process gap upstream of this specific bug),
  fixed via [phase-rs/phase#5342](https://github.com/phase-rs/phase/pull/5342).
- **Total for this item:** 2 planning rounds + 1 plan review round,
  ~2.6h combined agent time, zero lines of engine code changed — the
  value was entirely in *not* shipping a wrong fix, plus fixing the
  meta-process gap that caused the wrong turn in the first place.

## #1272 — Violent Urge

- **Outcome:** no code change — already fixed generically by an
  unrelated prior PR (#2999, "ParentTarget GenericEffect binding for
  targeted pump/debuff abilities", fixing the same bug class reported
  separately for Mu Yanling, issue #2922). Violent Urge just never got
  a follow-up regression test or issue closure. Commented on
  [phase-rs/phase#1272](https://github.com/phase-rs/phase/issues/1272).
- **Planning:** 1 round, ~32m/121 tool calls. First fix this session to
  explicitly read `PIPELINE-LOG.md` itself as a mandatory step before
  investigating (per the prompt) — went straight to a real AST dump
  plus a 3-creature runtime test (target/bystander/opponent) rather
  than a multi-round back-and-forth, suggesting the standing-lessons
  list is starting to pay for itself by shortening investigation time,
  not just improving correctness.
- **Independent spot-check:** confirmed the cited commit is a real
  ancestor of the branch and that the described types/comments
  (`ParentTarget`, the issue #2922 comment) actually exist in the
  codebase, without needing to re-run the full scratch test myself.
- **Running tally tonight:** 5 items investigated, 1 real bug fixed
  (Ad Nauseam), 4 already-fixed/non-reproducing (Underworld Breach,
  Pact of Negation, Violent Urge, plus several more closed out by
  concurrent sessions working the same backlog — see `BACKLOG.md`'s
  Done section). The false-positive rate in the original GitHub issues
  is turning out to be very high once actually re-verified against
  current `main` — worth remembering before assuming any `needs-triage`
  issue is still live.

## #1077 — Relic of Progenitus (concurrent session)

- **Outcome:** real bug in the first ability only ("target player exiles
  a card from their graveyard" bound to the activator instead of the
  targeted player); the second ability ("exile all graveyards, draw a
  card") was confirmed already working, narrowing the original two-part
  report. Root cause: `parse_zone_suffix_nom`'s "their" possessive
  parses scope-agnostically as `Owned { controller: ScopedPlayer }`,
  uncorrected for an explicitly *targeted* subject. Fixed by
  generalizing `rebind_owned_scope` (previously hardcoded to
  `ControllerRef::ChosenPlayer` for the Bounce/Skullwinder case) to
  accept any `ControllerRef`. Same class also covers Scrabbling Claws,
  Merrow Bonegnawer, Graveyard Shovel, Grave Birthing, and Gravestorm.
- **Round 1 shipped to a wrong code path — see standing lesson 10.**
  The fix was applied in `inject_subject_target`'s `ChangeZone` arm and
  a self-written test asserted a top-level `ChangeZone` effect; both
  compiled and the test passed locally. CI (`matthewevans`) failed the
  test on the real parse: production actually emits `TargetOnly{target:
  Player}` wrapping a `sub_ability`, via an *earlier* return in
  `lower_subject_predicate_ast` (mod.rs:16674) that fires before
  `inject_subject_target` is ever reached for this exact card shape.
  Round 2 applied the same `rebind_owned_scope` call at the actual
  early-return site and rewrote the test against the real `TargetOnly`+
  `sub_ability` AST shape (mirroring the existing
  `target_subject_damage_equal_to_its_power_uses_target_source_power`
  precedent).
- **Repeated background-build kills:** `cargo test`/`cargo check` in a
  fresh worktree were killed mid-compile 3 times in a row at the
  identical point (`Compiling engine v0.18.0`), with no explicit timeout
  set on the later attempts — a real environment ceiling, not
  contention (dependency checks always completed fine first). Round 1
  shipped on `cargo check`-level confidence plus source trace after
  hitting this; round 2's retest completed normally once the actual
  compile error (a second missed `rebind_owned_scope` call site,
  `retarget_effect_to_chosen_player`'s `Bounce` arm) was fixed.
- **PR:** [phase-rs/phase#5347](https://github.com/phase-rs/phase/pull/5347).
- **Concurrency note:** this item was worked by a separate concurrent
  session from the one that authored the entries above — logged here
  for the shared lesson (10), not to duplicate this file's per-session
  timing convention.
