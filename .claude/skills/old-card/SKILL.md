---
name: old-card
description: Start or continue work on a buggy old MTG card (printed 2003 or earlier) from the local candidate backlog. Picks the next unclaimed candidate, runs the staleness check that decides whether the issue is already fixed, claims the coordination row, then drives reproduce-fix-verify-PR. Use when the user says "old card work", "next old card", "work the old-card backlog", or invokes /old-card with or without an issue number.
---

# old-card — work the old-card backlog end to end

Drives one candidate from `BACKLOG-old-cards-2003.md` to a merged-ready PR, or to a
recommend-closure comment when the issue turns out to be already fixed. **Both are successful
outcomes.** Roughly a third of open issues in this repo are already fixed but still open.

`$ARGUMENTS` — optional. An issue number (`/old-card 7721`) works that issue. Empty picks the next
unclaimed LIVE candidate.

---

## Step 0 — Load context (do this first, every time)

```bash
git fetch upstream main -q && git fetch origin main -q
git merge --ff-only origin/main -q
```

Read, in this order:
1. **`OLD-CARD-RUNBOOK.md`** — the authority. Environment constraints, lock protocol, verification
   standard, PR/handoff rules. Everything below is a summary of it; when they disagree, it wins.
2. **`BACKLOG-old-cards-2003.md`** — the candidate table.
3. **`WORKLIST.md`** — who is working on what, and the cargo lock.

Do not skip the runbook. It contains facts that are false in `CLAUDE.md` (Tilt is not running) and
constraints that are invisible from the repo (background builds are silently reaped; the fork's main
is ~551 commits behind upstream).

## Step 1 — Pick

With an issue number: use it. Without: take the highest row from the backlog's **LIVE** table that
is not claimed in `WORKLIST.md` and not owned by another agent. Prefer, in order: card named in the
issue **title** → `status:confirmed` → `p0`/`p1`/`p2` priority → a merged commit that already
documents the gap (the backlog's §8 list).

**Never** take #5965 or #8058 (Swords to Plowshares) — another agent owns them.

## Step 2 — Staleness check (MANDATORY, before claiming)

```bash
N=<issue>; CARD="<Card Name>"
grep -rn "$CARD" crates/ --include=*.rs | head
git log upstream/main --grep="#${N}\b" --oneline | head
git grep -l "issue #${N}" upstream/main -- crates/engine/tests
```

For every commit found, **check the reference direction** — this is the step people skip:

```bash
git log -1 --format='%b' <sha> | grep -B2 -A3 "#${N}\b"
```

A commit may cite an issue to **fix** it, **defer** it, be **blocked on** it, or **file** it. Only
the first means fixed. Squash subjects read `title (#issue) (#PR)`, so a bare match may be a PR
number. Ignoring direction produced 5 false positives out of 17 on the last sweep.

**If already fixed:** comment on the issue naming the fixing commit/PR and the test that pins it,
recommend closure, move the backlog row to its Done table, and **go back to Step 1**. Do not
re-implement. Do not open a PR.

## Step 3 — Claim

Add a row to `WORKLIST.md`'s Open table (item, track `old-school-1993-95`, status `in-progress`,
your agent name, date, branch). Commit as `claim: <item>` and push to `origin main` immediately.
Worklist edits are their own commit, never bundled with code.

## Step 4 — Set up worktree

```bash
git worktree add -b fix/<slug> .claude/worktrees/<slug> upstream/main
```

**From `upstream/main`, never `origin/main`.** Reuse a warm worktree of your own if you have one —
a cold build is ~25 min and will not fit the 600s foreground cap.

## Step 5 — Reproduce, then fix

1. **Verify the card's Oracle text from Scryfall**, not from the issue's paraphrase:
   `https://api.scryfall.com/cards/named?exact=<name>`
2. **Write a test that fails first.** If it does not fail, you have not reproduced the bug.
   Invoke **`card-test`** for the recipe and its six foot-guns.
3. Root-cause at the correct seam. Ask whether you are fixing the card or the class.
4. New enum variant? Invoke **`add-engine-variant`** first — it usually says parameterize instead.
5. Parser work? Invoke **`oracle-parser`**. Nom combinators from the first line.
6. CR annotations: grep `docs/MagicCompRules.txt` for every number. Never annotate plumbing.
7. **Prove the test discriminates**: revert the production change, confirm the test fails, record
   the observed failure for the PR.
8. Self-review with **`review-impl`** before pushing.

## Step 6 — Verify (claim the cargo lock first)

`WORKLIST.md` line ~59. Claim → build → release immediately. See the runbook §4.

```bash
cargo fmt --all                                    # no lock needed
nice -n 5 timeout 560 cargo test -j 2 -p phase-engine --test integration -- <filter>
nice -n 5 timeout 560 cargo test -j 2 -p phase-engine --lib
```

Touched a shared primitive? Run the integration suite too. Clippy cannot complete locally — CI owns
it; say so in the PR rather than claiming a local green.

## Step 7 — PR and hand off

Push to `origin`, open the PR against `phase-rs/phase`, link the issue, state what was verified and
what CI is covering. Attribution trailers per the runbook §7.

Expect review findings and expect them to be correct. Fix rather than defend, and reply on the
thread saying what changed. A red check may be a flake — prove it before assuming.

**You cannot merge, close, or auto-queue anything.** Get it green, answer review, hand off, say so.

## Step 8 — Record

Update `WORKLIST.md` (Done on merge) and `BACKLOG-old-cards-2003.md`. Then offer the next candidate.
