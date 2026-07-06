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

### [research] Audit the AWS host before hosting phase.rs there

- **Status:** open
- **Source:** 2026-07-06 planning discussion
- **Why this is its own item:** read-only investigation, no changes to the
  live host — cleanly separable from, and a hard prerequisite for, the
  "Host my fork at phase.teamserio.us" item below. Do this first; it'll
  likely change details in that item's plan.
- **What's already confirmed** (don't re-ask): nginx is the reverse proxy;
  its config lives only on the host, not in any repo; `teamserio.us`
  itself deploys via GitHub Actions → SSH wipe + SCP copy to `/prod-www/`
  (secrets `DEPLOY_HOST`, `DEPLOY_USERNAME`, `DEPLOY_SSH_KEY`,
  `DEPLOY_HOST_PORT`, currently only on the `teamserio.us` repo).
- **What's genuinely unconfirmed:**
  1. **TLS termination point** — is it nginx + certbot/Let's Encrypt on the
     box itself, or does an AWS-layer component (ALB, CloudFront) terminate
     TLS in front of nginx? This changes where a `phase.teamserio.us` cert
     needs to be issued and whether nginx even needs a cert block at all.
  2. **nginx config layout** — single `nginx.conf`, or
     `sites-available`/`sites-enabled` per-site convention? Pull the
     existing `teamserio.us` server block as the literal template to copy
     for `phase.teamserio.us`.
  3. **OS/distro and package manager** on the host (`/etc/os-release`) —
     needed to know how to install/verify Docker.
  4. **Is Docker already installed and in use** on this host for anything?
     `docker --version`, `docker ps`. phase-server's documented self-host
     path (README "Dedicated Server") is Docker-based; if Docker isn't
     already there, that's a real setup step, not a given.
  5. **DNS management for `teamserio.us`** — Route53, the registrar
     directly, Cloudflare, something else? Needed to add the `phase` A/CNAME
     record. (This one may not need host SSH at all — could be checked from
     wherever the domain's DNS is actually managed.)
  6. **Host capacity** — `free -h`, `df -h`, `nproc`. Confirm there's room
     for another Docker container + static site alongside the existing
     sites before assuming it'll just fit.
  7. **Firewall/security group** — confirm only 80/443 (or whatever's
     already open) is exposed, and that phase-server binding to
     `127.0.0.1` behind nginx (per README's own reverse-proxy guidance)
     doesn't need any new inbound rule.
  8. **Deploy secrets are per-GitHub-repo, not shared** — `DEPLOY_HOST`
     etc. exist on the `teamserio.us` repo's GitHub settings only; the
     fork (`rykerwilliams/phase`) will need its own copies added, or a
     dedicated SSH key/user scoped just to the phase deploy path (worth
     considering over reusing the exact same key as `teamserio.us`, to
     keep blast radius contained if either pipeline were ever compromised).
- **Prompt:**
  > SSH into the AWS host that serves `teamserio.us` and audit it,
  > read-only — do not change anything. Report back on: (1) how TLS is
  > terminated (nginx+certbot on-box, or an AWS-layer component in front —
  > check for an ALB/CloudFront setup too, not just the box itself); (2)
  > the nginx config layout and the literal existing server block for
  > `teamserio.us` as a template; (3) OS/distro and package manager; (4)
  > whether Docker is already installed/in use; (5) where `teamserio.us`'s
  > DNS is managed; (6) available CPU/RAM/disk headroom; (7) current
  > firewall/security-group rules. Also separately note whether
  > `DEPLOY_HOST`/`DEPLOY_USERNAME`/`DEPLOY_SSH_KEY`/`DEPLOY_HOST_PORT` are
  > only configured as secrets on the `teamserio.us` GitHub repo (expected)
  > and whether a dedicated, more narrowly-scoped SSH credential for the
  > phase deploy path is worth setting up instead of reusing the existing
  > one. Feed the findings back into the "Host my fork at
  > phase.teamserio.us" backlog item's plan — don't implement anything yet.

### [infra] Host my fork of phase.rs at phase.teamserio.us

- **Status:** open (blocked on the host-audit item above)
- **Source:** 2026-07-06 planning discussion
- **Context (verified, not assumed):**
  - Target: run my fork at `phase.teamserio.us`, on the same AWS host that
    already serves `teamserio.us` and other sites behind a single **nginx**
    reverse proxy.
  - nginx config lives **only on the host** (SSH-edited, not tracked in any
    repo) — no config-as-code to read/PR against; changes have to be made
    live over SSH and `nginx -t && systemctl reload nginx` (or equivalent).
  - Known-working deploy pattern, copied from `teamserio.us`
    (`/mnt/c/git/teamserio.us/.github/workflows/jekyll-build-and-deploy-prod.yml`):
    GitHub Actions builds the static site, then `appleboy/ssh-action` wipes
    the target directory and `appleboy/scp-action` copies the fresh build
    over SSH to a directory on the host (teamserio.us uses `/prod-www/`).
    Secrets: `DEPLOY_HOST`, `DEPLOY_USERNAME`, `DEPLOY_SSH_KEY`,
    `DEPLOY_HOST_PORT`. Phase.rs's client build is a static bundle too
    (`pnpm build` in `client/`), so the same SSH/SCP pattern applies
    directly — just to a new directory (e.g. `/phase-www/`) and a new
    nginx server block for `phase.teamserio.us`.
  - Unlike the Jekyll blog, phase.rs also needs a **running backend**:
    `phase-server` (WebSocket, `/ws`, plus `/health`) per README's
    "Dedicated Server" Docker instructions. That needs to run persistently
    on the same host (`docker run -d --restart unless-stopped`, bound to
    `127.0.0.1:9374` per README's own guidance for the reverse-proxy case),
    with nginx adding a `location /ws { proxy_pass ...; proxy_set_header
    Upgrade ...; }` block for `phase.teamserio.us` alongside the static
    file block.
  - Card data must be generated **from this fork**
    (`scripts/gen-card-data.sh`), not pulled from upstream's published
    data, or fork-only fixes (e.g. Hollow One) silently won't show up in
    play. The upstream `phase-server` Docker image
    (`ghcr.io/phase-rs/phase-server`) is built from upstream too — the
    fork needs its own image (root `Dockerfile`) built and either pushed
    to `ghcr.io/rykerwilliams/phase-server` or built directly on the host.
  - TLS for the new subdomain: unconfirmed whether the host already uses
    certbot/Let's Encrypt for its other sites — check on the host before
    assuming a mechanism.
  - Project is a **non-commercial fan project** under the WotC Fan Content
    Policy — hosting must stay within that (no monetization, etc.).
- **Prompt:**
  > Produce a concrete, step-by-step plan to host my phase.rs fork
  > (`rykerwilliams/phase`) at `phase.teamserio.us`, on the same AWS host
  > that already serves teamserio.us behind nginx (config is host-only,
  > SSH-edited, not in any repo). Mirror teamserio.us's own deploy pattern
  > (`.github/workflows/jekyll-build-and-deploy-prod.yml` in
  > `/mnt/c/git/teamserio.us`) for the static client: GitHub Actions builds
  > `client/` with `pnpm build` against card data generated from *this
  > fork* (not upstream's), then `appleboy/ssh-action` + `scp-action` ships
  > it to a new directory on the host (e.g. `/phase-www/`). Additionally
  > plan: (1) the phase-server Docker container running persistently on
  > the host bound to localhost only, built from the fork's own
  > `Dockerfile`; (2) the exact nginx server block for
  > `phase.teamserio.us` — static file serving plus a `/ws` WebSocket
  > proxy to phase-server, and how it should get a TLS cert (check what
  > the host already uses for its other sites before assuming certbot);
  > (3) whether GitHub Actions should also build+push the fork's
  > `phase-server` image, or whether it's simpler to `git pull` + rebuild
  > directly on the host when the fork's engine changes. Confirm the nginx
  > software/config approach and get my explicit go-ahead on the exact SSH
  > commands and nginx block before touching the live host — it's serving
  > my real blog and other sites, so nothing here should run unattended.

### [feature] Configurable, non-copyrighted card back art

- **Status:** open
- **Source:** 2026-07-06 planning discussion
- **Context (verified against the repo, not assumed):**
  - Card back art is currently hardcoded: `CARD_BACK_URL` in
    `client/src/services/scryfall.ts:33-34`, hotlinked from Scryfall's
    generic-back CDN asset, deliberately non-configurable to avoid bundling
    WotC-copyrighted art. No config/env override exists today.
  - There's an almost-exact architectural precedent already upstream to
    mirror: **board background** is a real, pluggable preference —
    `boardBackground` (`"auto-wubrg" | "random" | "none" | "custom" |
    string`) plus `customBackgroundUrl` in the preferences store, resolved
    in `client/src/components/board/BattlefieldBackground.tsx:20-54`
    (curated art, plain colors, deck-color auto-match, or a user-supplied
    custom image URL), surfaced in `PreferencesModal.tsx:97-106+` and
    `BoardContextMenu.tsx:71`.
  - The audio theme system (`client/src/audio/themeRegistry.ts`) is a
    second precedent for "load user-supplied asset by URL, validate,
    cache" if a richer manifest (e.g. a full back-art *set* rather than one
    URL) ends up being wanted instead of a single image URL.
  - This is generically useful (not fork-specific) and follows an existing,
    already-accepted pattern closely enough that it's a real candidate for
    an upstream PR to `phase-rs/phase`, not just a personal fork
    customization — worth floating to the maintainer/Discord before
    building, in case there's already a reason it wasn't done (e.g. a
    licensing concern specific to *any* non-default back art, even
    non-copyrighted).
- **Prompt:**
  > Add a configurable card-back-art preference to phase.rs, mirroring the
  > existing `boardBackground`/`customBackgroundUrl` pattern
  > (`client/src/components/board/BattlefieldBackground.tsx`,
  > preferences store). Default stays the current hardcoded Scryfall
  > generic back (`client/src/services/scryfall.ts` `CARD_BACK_URL`) so
  > behavior is unchanged out of the box; add a preference (e.g.
  > `cardBackUrl: "default" | string`) that lets a user supply their own
  > non-copyrighted image URL, surfaced in the same preferences modal /
  > context-menu pattern board background uses. This is a frontend-only,
  > display-layer change per CLAUDE.md's engine/frontend split — no engine
  > involvement expected. Use the `/add-frontend-component` skill for the
  > UI piece. Before implementing, check whether this is better proposed
  > upstream to `phase-rs/phase` (it mirrors an already-accepted pattern
  > and isn't fork-specific) rather than kept as a fork-only customization
  > — flag that choice back to me rather than assuming either way.

### [feature] Theme Pack system (bundled, per-deployment branding)

- **Status:** open
- **Source:** 2026-07-06 planning discussion
- **Motivation:** not just cosmetic options for one player — the real goal
  is per-deployment branding. If I end up hosting this at multiple
  subdomains (e.g. `phase.teamserio.us` vs. a hypothetical
  clevelandrocs-flavored instance), each deployment should be able to ship
  a different **default look** as one bundled unit, while individual
  players can still override pieces for themselves. This depends on the
  card-back-art item above as one of its building blocks — do that one
  first, then build the pack registry on top of it plus the two systems
  that already exist.
- **Context (verified against the repo, not assumed):**
  - **Two real precedents to generalize from, don't invent a third
    pattern:** the audio theme registry
    (`client/src/audio/themeRegistry.ts` — `BUILT_IN_THEMES`, validated
    JSON manifest, load-by-URL, IndexedDB cache) and the board-background
    preference (`boardBackground`/`customBackgroundUrl`,
    `BattlefieldBackground.tsx:20-54`). A "theme pack" is naturally a
    manifest that bundles: a palette (see below), a card back URL (once
    the item above ships), a board-skin selection, and an audio theme
    reference — i.e. compose the two existing per-facet systems plus two
    new facets into one selectable unit, rather than building a
    from-scratch bundling mechanism.
  - **Curated background art is currently a single global, hardcoded
    list**, not scoped per anything: `BATTLEFIELDS` in
    `client/src/components/board/battlefields.ts` (flat array, one fixed
    set for every player/deployment). "Set the curated art for
    backgrounds" (per pack) means this list needs to become
    pack-scoped/overridable rather than a single module-level constant —
    same shape of change as making `CARD_BACK_URL` configurable.
  - **Color palette has no runtime system at all today** — single static
    `@theme` block in `client/src/index.css:20-96` (Tailwind v4's
    CSS-native config; there is no `tailwind.config.*` to layer variants
    onto). Making the palette swappable is the one facet with no existing
    precedent to mirror — likely needs its own small registry (CSS custom
    properties swapped via a `data-theme-pack` attribute on `<html>`,
    analogous to how the existing dark/light `data-theme` toggle already
    works per the artifact-design conventions used elsewhere) rather than
    literally copying the audio/board pattern.
  - **Card frame / card face style is UNINVESTIGATED** — no research done
    yet on how individual card rendering works or whether it's realistically
    swappable. Do not assume it's a small change; investigate the actual
    card-rendering component(s) first as step 1 of implementing this, and
    report back what's actually involved before committing to scope.
  - Per-deployment default selection likely wants a build-time or
    server-config mechanism (env var read at build, or a config JSON
    served alongside `card-data.json`) rather than requiring every new
    visitor to manually pick a pack — but confirm this against how
    `client/public/*` config/meta files are already loaded before
    designing a new one.
- **Prompt:**
  > Design (don't implement yet) a Theme Pack system for phase.rs that
  > bundles: color palette, board-skin (background image + a pack-scoped
  > curated art list, generalizing the current global `BATTLEFIELDS` in
  > `client/src/components/board/battlefields.ts`), card back art (once
  > the separate card-back-art backlog item ships), and an audio theme
  > reference (`client/src/audio/themeRegistry.ts`) into one selectable
  > unit. Goal: a given deployment (e.g. `phase.teamserio.us`) can ship
  > with its own default pack while individual players can still override
  > any single facet via existing per-facet preferences. Explicitly
  > investigate and report on card frame/face rendering (how individual
  > cards are drawn today, whether style is realistically swappable)
  > before scoping that facet in or out — this hasn't been researched yet.
  > For the color palette facet, propose a mechanism analogous to the
  > existing dark/light theme toggle (a root attribute swapping CSS custom
  > properties) rather than a new one-off system. Reuse the audio-theme
  > registry's manifest/validation/caching pattern for the pack manifest
  > itself rather than inventing new loading/caching logic. Produce a plan
  > with the mandatory `/engine-planner`-style architectural sections
  > (though this is frontend-only, no engine involvement) — pattern
  > coverage, building-block reuse, logic placement — then stop for review
  > before writing code, since this touches several existing preference
  > systems and a wrong seam here is expensive to unwind later.

---

## Done

_(none yet)_
