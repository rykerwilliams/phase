# Backlog

Personal backlog for `rykerwilliams/phase`. Lives only on this fork's `main` —
it is a divergent file and must never appear in a PR to `phase-rs/phase`.
Every feature/fix branch is cut fresh from `origin/main` (upstream), never
from this fork's `main`, so this file is automatically excluded from PR
diffs — no extra tooling required.

## Format

Each item is written so it can be pasted with little or no editing as the
opening instruction to the next pipeline step (usually `/engine-implementer`
for a bug fix, or a plain investigation prompt for research/infra work).

- **Title**
- **Type** — `bug-fix` | `feature` | `infra` | `research`
- **Status** — `open` | `in-progress` | `done`
- **Source** — where this came from
- **Prompt** — ready-to-paste instruction for the next agent/skill invocation

Move an item to the bottom "Done" section (don't delete it) once it ships,
so there's a record of what's already been resolved.

---

## Open

### [infra] Host my fork of phase.rs somewhere

- **Status:** open
- **Source:** 2026-07-06 planning discussion
- **Context (verified against the repo, not assumed):**
  - The engine change lives in the Rust `engine` crate; anything hosted
    needs card data regenerated *from this fork* (`scripts/gen-card-data.sh`)
    so fixes like the Hollow One one actually show up in play — pulling
    upstream's published card-data.json would silently discard fork-only
    fixes.
  - There's an existing, documented, self-host path for the **multiplayer
    server**: the `ghcr.io/phase-rs/phase-server` Docker image (README
    "Dedicated Server" section). That image is built from `phase-rs/phase`
    upstream, so it won't include fork changes — the fork would need its
    own image build (the repo's own `Dockerfile` at the root) pushed
    somewhere the fork controls (e.g. `ghcr.io/rykerwilliams/phase-server`).
  - The **frontend** (client) is deployed to GitHub Pages via
    `.github/workflows/deploy.yml`, but every job in that workflow is
    gated with `if: github.repository == 'phase-rs/phase'` — it will not
    run on a fork as-is. Either adjust that condition on the fork (messy,
    diverges further from upstream and complicates future merges) or build
    the static client separately (`pnpm build` in `client/`) and host it
    on any static host (GitHub Pages on the fork with a from-scratch
    workflow, Cloudflare Pages, Netlify, etc.), pointed at a
    fork-controlled `phase-server` instance's `wss://` URL.
  - Project is licensed as a **non-commercial fan project** under the WotC
    Fan Content Policy (README, "Non-Commercial Fan Project") — any
    hosting plan should stay within that policy (no monetization, etc.).
- **Prompt:**
  > Research and propose 2-3 concrete options for hosting a running
  > instance of my fork of phase.rs (`rykerwilliams/phase`) so I can play
  > games against it directly, including any fixes I've made that haven't
  > landed upstream yet. Needs: (1) a card-data pipeline built from *this
  > fork*, not upstream's published data; (2) a `phase-server` instance
  > built from this fork's `Dockerfile` and hosted somewhere I control
  > (compare a VPS/Docker host, a managed container platform like
  > Fly.io/Railway, and running it locally with a tunnel like Cloudflare
  > Tunnel/ngrok for occasional play); (3) a static host for the client
  > build pointed at that server (GitHub Pages on the fork with its own
  > un-gated workflow, vs. Cloudflare Pages/Netlify). For each option, give
  > setup steps, rough ongoing cost, and how much it diverges from
  > upstream's own CI/deploy setup (divergence = future merge pain). Stay
  > within the project's non-commercial Fan Content Policy constraint. Do
  > not implement anything yet — present the comparison and let me choose.

---

## Done

_(none yet)_
