# START HERE — tournament organizer PR 4/4 + protocol v6 (migrated machine)

**You cannot resume the originating Claude Code session.** Session transcripts are local to the
machine that created them (`~/.claude-profiles/<profile>/projects/<slug>/*.jsonl`) and are not in
this repo. This file plus `.handoff/engine-implementer-runs/` are the complete replacement for that
transcript. Read both before touching code.

## 0. What this branch is

- Branch: `wip/tournament-organizer-pr4-protocol-v6` on `myfork`
  (`git@github.com:rykerwilliams/phase.git`)
- Its parent, `5027f1bcd`, is the head of **open PR #8325**
  (`feat(client): tournament organizer frontend — pages, store, i18n, presentation (PR 4/4)`,
  branch `feat/tournament-organizer-pr4-frontend`).
- The tip commit is a **WIP checkpoint deliberately kept OFF the PR branch**. It is 2,289 lines of
  lobby **protocol v6** work whose verification status is unknown — it was sitting uncommitted in
  the worktree when the session ended. Do not push it onto the PR branch until it is verified.

## 1. Status of PR #8325 — read before doing more work on it

- `reviewDecision: CHANGES_REQUESTED`
- **Deferred by maintainer intake policy.** The maintainer bot triaged the head as a frontend-only
  change and noted: *"The local frontend-review allowlist does not include this author, so this
  route does not perform an implementation-diff review or approve the PR. A maintainer must
  explicitly take this PR or add a local frontend-review exception before it can receive
  substantive review."* The defer label is a routing marker, not a verdict.
- Failing check: `Superagent Security Scan` — `ACTION_REQUIRED`.
- CodeRabbit left a review; its findings were addressed in `3ce0f5c54`.

**Implication: piling more code onto #8325 does not unblock it.** The blocker is intake routing, not
the diff. The useful next action is a human ping to a maintainer to take the PR or add the review
exception, plus clearing the security scan.

## 2. Setup on the new machine

```bash
git clone git@github.com:rykerwilliams/phase.git phase && cd phase
git remote add origin git@github.com:phase-rs/phase.git   # upstream, READ-ONLY
git fetch --all
git checkout -b tournament-pr4-protocol-v6 myfork/wip/tournament-organizer-pr4-protocol-v6
pnpm install
./scripts/fetch-comp-rules.sh    # docs/MagicCompRules.txt is gitignored
```

**Push rule, non-negotiable: push only to `myfork`. Never push to the upstream `phase-rs/phase`
repo.**

## 3. What the WIP commit contains (lobby protocol 5 → 6)

Three triggers land together; each alone would force the bump.

1. **Broker-owned action legality** — `PairingView` gains a required `report_gate`;
   `TournamentSummary` gains a required `open_actions`. The broker, not each client, decides which
   affordances are legal.
2. **Broker-owned default scoring** — `CreateTournament::scoring` is *relaxed* from a required
   `ScoringPolicy` to an `Option`, `None` meaning the broker applies
   `ScoringPolicy::default_for_arity`; `TournamentSummary` gains a required `scoring`.
3. **Expiring/rotating credentials** — new `RenewTournamentCredential` /
   `TournamentCredentialRenewed` lobby message pair; `TournamentCreated` and `TournamentJoined`
   gain a required `expires_at_ms` beside their token.

Version movement, and the reasoning to preserve:
- `LOBBY_PROTOCOL_VERSION` 5 → 6, matched in `scripts/check-protocol-version.mjs`.
- `MIN_SUPPORTED_LOBBY_PROTOCOL` deliberately does **not** move. The server → client additions are
  inert against an older client (`JSON.parse` ignores unknown fields). The client → broker
  relaxation is *not* symmetric — a new client omitting `scoring` against a pre-6 broker gets a hard
  `missing field` parse error — so that direction is gated by a **client-side capability floor**,
  `MIN_LOBBY_PROTOCOL_FOR_DEFAULT_SCORING` in `client/src/adapter/ws-adapter.ts`, which keeps a
  below-floor client sending an explicit policy. Moving the broker floor instead would evict every
  older client over a field they can simply keep sending.
- `PROTOCOL_VERSION` does **not** move: no variant here carries `GameState` or `GameAction`.

## 4. Immediate next action

Verify the draft before anything else:

```bash
cargo fmt --all
cargo clippy -p lobby-broker -p server-core -p phase-server -p broker-wasm --all-targets -- -D warnings
cargo test -p lobby-broker -p server-core -p phase-server
node scripts/check-protocol-version.mjs
pnpm --dir client run type-check && pnpm --dir client test
```

Check Tilt first (`tilt get uiresource clippy >/dev/null 2>&1`; exit 0 = up) — if it is up, use
`tilt logs <resource>` / `./scripts/tilt-wait.sh` instead of running cargo directly, per CLAUDE.md.

If clean, replace the WIP commit with real `feat(protocol)/fix(lobby-broker)` commits and dispatch a
**review-impl round (Opus)** against `5027f1bcd..<new head>`. Only after that is clean should any of
it reach the PR branch — and given §1, coordinate with the user on whether it belongs in #8325 at
all or in a separate follow-up PR.

## 5. Standing rules for this pipeline

- **Model assignment (user standing instruction): Opus for all planning and review steps; Sonnet
  for all implementation steps.**
- **One PR per phase.** No bundling, no direct merge to upstream `main`.
- Lead/orchestrator owns commits; subagents never commit.
- Multi-agent safety (CLAUDE.md): never `git stash`, never `checkout`/`restore`/`reset` files you
  did not write.
- Protocol changes: any wire-shape change requires the version bump *and* a documented reason in
  the `LOBBY_PROTOCOL_VERSION` doc comment. Follow the numbered-entry style already in
  `crates/lobby-broker/src/protocol.rs`.

## 6. Process record

`.handoff/engine-implementer-runs/` holds the append-only records for tournament PRs 1–4, copied out
of `.git/` (which does not survive a clone):

| Path | What it is |
|---|---|
| `20260830-tournament-organizer-pr1/phase-fit` | PR 1 (core) round history |
| `20260831-tournament-organizer-pr2/phase-fit` | PR 2 (wiring) round history |
| `20260902-tournament-organizer-pr3/phase-fit` | PR 3 (worker shell) round history |
| `20260902-tournament-organizer-pr4/phase-fit` | PR 4 round history — the big one, 250 KB |
| `20260902-tournament-organizer-pr4/phase-charter` | PR 4 charter |
| `20260902-tournament-organizer-pr4/phase-{1..5}-plan.md` | accepted per-phase plans |
| `20260902-tournament-organizer-pr4/review-round-2-{charter,plan}.md` | round-2 review findings |
| `20260902-tournament-organizer-pr4/rpc-correlation-plan.md` | the RPC-correlation plan (protocol v5) |

Earlier PRs in the series live on `myfork` branches `feat/tournament-organizer-pr1-core`,
`feat/tournament-organizer-pr2-wiring`, `feat/tournament-organizer-pr3-worker-shell`.

**Delete `HANDOFF.md` and `.handoff/` before this work becomes a real PR.** They are migration
scaffolding, not project documentation.
