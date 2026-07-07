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
- *(entry will be updated as the redo proceeds)*
