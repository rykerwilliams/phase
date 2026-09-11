# Old-card bug runbook — start here, no input required

**Fork-only working document.** Like `WORKLIST.md` and `BACKLOG.md`, it never appears in a PR to
`phase-rs/phase`.

A fresh session can pick this up cold and produce a merged fix without asking anything. Work the
steps in order. Every non-obvious fact below cost a real mistake to learn; none of it is inferable
from the repo.

---

## 0. TL;DR

1. Pick the top unclaimed row from **`BACKLOG-CARDS.md` → LIVE**.
2. Run the **staleness check** (§3). Roughly a third of open issues are already fixed. If fixed:
   comment recommending closure and pick the next one — that is a complete, valuable unit of work.
3. Claim a row in `WORKLIST.md`.
4. Reproduce with a **failing test first**, then fix, then prove the test fails on revert.
5. PR, answer review, update the board. You cannot merge or close — hand off.

---

## 1. There is no single "fix a card" skill

It is a pipeline. Invoke the gate skills; they are not optional.

| when | skill |
|---|---|
| any new enum variant on `Effect`/`AbilityCondition`/`QuantityRef`/`TargetFilter`/… | **`add-engine-variant`** — mandatory gate BEFORE proposing it |
| any parser work | **`oracle-parser`** — single source of truth; nom-combinator mandate |
| writing a cast-pipeline test | **`card-test`** — documents six harness foot-guns incl. vacuous negative assertions |
| does the card even claim to support the clause? | **`bug-coverage-classifier`** |
| need a plan that survives architectural review | **`engine-planner`** → **`review-engine-plan`** |
| full pipeline (plan → review → implement → review → commit, via spawned agents) | **`engine-implementer`** |
| reviewing your own diff before pushing | **`review-impl`** — findings-only; run it on yourself |
| CR annotations | **`validate-cr-annotations`** — every CR number grepped from `docs/MagicCompRules.txt` first |
| commands, module map, env vars | **`project-reference`** |

**`ship-commits` does not fully apply here.** It ends in `gh pr merge --squash --auto`, and this
account has **no write access to `phase-rs/phase`**. Push the branch and open the PR; stop there.

---

## 2. Environment facts that will otherwise cost you hours

Verified 2026-09-10.

- **Tilt is NOT running**, despite what `CLAUDE.md` says. Use direct cargo, under the lock (§4).
- **The fork's `main` is ~551 commits behind `upstream/main`.** ALWAYS branch from `upstream/main`,
  never from `origin/main`, or you will develop against dead code and your reads will be wrong.
  ```bash
  git fetch upstream main
  git worktree add -b fix/<slug> .claude/worktrees/<slug> upstream/main
  ```
- **Background builds get silently killed.** The harness memory guard reaps them: status `killed`,
  no output, reads like a hang. Swap is pinned full (idle, not thrashing — the box is fine; see
  `[[long-builds-killed-by-memory-reaper]]` in project memory). Run builds in the **foreground**:
  ```bash
  nice -n 5 timeout 560 cargo test -j 2 -p phase-engine --test integration -- <filter>
  ```
- **Foreground Bash is capped at 600s.** A cold worktree build (~25 min) and
  `cargo clippy --all-targets` (~15 min) therefore **cannot complete locally at all**.
  - Reuse a **warm worktree** (switch branches inside one whose `target/` is already built) — this
    is the difference between a 1-3 min incremental build and a 25 min cold one.
  - Let CI's "Rust lint (fmt, clippy, parser gate)" own clippy, and **say so in the PR** rather than
    claiming a local green.
- **No `jq`.** Use `python3`, or `gh --jq` (built in).
- **No full `card-data.json`** — only the curated test fixture, which is missing many cards
  (Gifts Ungiven, for one). A db-backed test for a missing card **silently skips** in CI. Build the
  card from verified Oracle text instead:
  ```rust
  scenario.add_spell_to_hand_from_oracle(P0, "Name", false, ORACLE).with_mana_cost(ManaCost::zero())
  ```
- **~12 concurrent worktrees**, several belonging to other agents. Never touch one you did not
  create. Never `git stash`, `git checkout`, or `git restore` files you did not modify.

---

## 3. Staleness check — ALWAYS FIRST, before claiming anything

Open issues are frequently already fixed; `Closes #N` often fails to close them. On 2026-09-09/10,
**9 of 21 checked issues were already fixed but still open.**

```bash
grep -rn '<Card Name>' crates/ --include=*.rs | head        # a test naming the card?
git log upstream/main --grep='#<N>\b' --oneline | head      # a commit citing the issue?
git grep -l 'issue #<N>' upstream/main -- crates/engine/tests
git merge-base --is-ancestor <sha> upstream/main && echo shipped
```

**Then check the reference DIRECTION — this is the step that matters:**

```bash
git log -1 --format='%b' <sha> | grep -B2 -A3 '#<N>\b'
```

A commit can cite an issue to **fix** it, to **defer** it, to declare itself **blocked on** it, or to
**file** it. Only the first means fixed. Ignoring direction produced 5 false positives out of 17.
Real examples: *"reference follow-up issues #1234 … deferred limitations"*; *"Refs #7721 — PARTIAL …
the issue must stay open"*; *"blocked on #7962"*; *"the value gap is filed as #8775"*.

Also beware: squash-merge subjects read `title (#issue) (#PR)`, so a bare `#N` match may be a **PR**
number, not an issue.

**If already fixed:** comment naming the fixing commit/PR and the test that pins it, recommend
closure, move the row to the backlog's Done table. Do not re-implement. This is a real result.

---

## 4. Cargo lock protocol (mandatory, cooperative)

`WORKLIST.md` line ~59 holds an advisory lock. Before ANY compiling cargo command:

```bash
git fetch origin main && git merge --ff-only origin/main
sed -n '59p' WORKLIST.md                       # must read: none
# claim, commit as "cargo-lock: claim (<agent>)", push IMMEDIATELY, then build
# release the moment you finish: "cargo-lock: release (<agent>)"
```

Include `(expected ~Nm)` and your build PID. A holder inside its estimate is **not** stale — queue,
do not ping. Verify a suspicious holder with `kill -0 <pid>` and `readlink /proc/<pid>/cwd`, not by
guessing from elapsed time. `cargo fmt` needs no lock.

---

## 5. The work itself

1. **Verify the card's real Oracle text from Scryfall** — never from the issue's paraphrase, never
   from memory. `https://api.scryfall.com/cards/named?exact=<name>`.
2. **Reproduce with a failing test before fixing anything.** If it does not fail first, you have not
   reproduced the bug and you do not know that your fix does anything.
3. **Root-cause at the right seam.** Ask: does this fix the card, or the class? A payload bug that
   looks like a UI bug is an engine bug (see #8135). Fix the invariant, not the symptom.
4. **Run `add-engine-variant` before any new enum variant.** It will usually tell you to
   parameterize an existing variant instead of adding a sibling — that is the correct outcome.
5. **CR annotations:** grep `docs/MagicCompRules.txt` for every number before writing it. A wrong CR
   number is worse than none. Do **not** annotate plumbing — set identity, data structures, and
   serialization are not game rules, and a citation there is a false verification signal.
6. **Prove the test discriminates.** Temporarily revert the production change and confirm the test
   fails. State the observed failure in the PR. A test that never failed proves nothing.
7. **Self-review with `review-impl`** before pushing.

---

## 6. Verification standard

- `cargo fmt --all` — always, needs no lock.
- Targeted tests, then the full lib suite (`--lib`, ~6 min run) if you touched anything shared.
- **Touched a shared primitive? Run the integration suite too** (`--test integration`, ~32 min, must
  be foreground-chunked). That is where the real consumers live and where an ordering change shows up.
- Clippy: CI's job. Say so explicitly.
- Never claim "verified" for a state you did not actually run.

---

## 7. PR, review, handoff

- Push to `origin` (the fork); open the PR against `phase-rs/phase`.
- Attribution trailers: `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` on
  commits; `🤖 Generated with [Claude Code](https://claude.com/claude-code)` on the PR body.
- **Expect a review, and expect it to be right.** Recent real findings against this work: an
  unsupported CR citation; a regression asserting cardinality where identity was the property; a
  library-position assertion that would have passed on a bottom-append; a monotonicity argument that
  only held once both values passed the threshold. Fix rather than defend; reply on the thread saying
  what changed.
- A red CI check may be a **flake** — verify before assuming it is yours (diff scope, does it pass
  locally, did a sibling PR pass the same job). Document the evidence rather than silently re-running.
- **You cannot merge, close, or auto-queue.** Get it green, answer review, then hand off and say so.
- Update `WORKLIST.md` (row → Done on merge) and `BACKLOG-CARDS.md`.

---

## 8. Best current candidates

From the backlog's LIVE table. The five below carry a merged commit that documents the exact gap,
which makes them unusually well-specified:

| issue | card(s) | what the commit says is missing |
|---|---|---|
| #7721 | Anavolver, Necravolver, Rakavolver | quoted-ability kicker rider; 10 of 13 lines fixed, 3 cards each missing one half |
| #1234 | Phyrexian Altar, Lion's Eye Diamond | colored-shard feasibility under non-tap mana sources |
| #1235 | same class | `feasible_mana_capacity` over-counts chain-sacrifice configurations |
| #7962 | Quicksilver Elemental | injected duration defaults indistinguishable from printed windows |
| #8775 | Ogre Battlecaster | "where X is that spell's mana value" resolves X to 0 |

Also strong, plain card bugs: **#782** Thought Lash (cost not paid), **#6508** Citadel of Pain
(damages the wrong player), **#4731** Reins of Power (control to the wrong side), **#6902** Sneak
Attack, **#4231** Final Fortune.

Do not touch **#5965 / #8058** (Swords to Plowshares) — owned by `swords-608-2b` on the board.
