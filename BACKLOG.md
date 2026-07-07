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

### [infra] Follow up on PR #5236 and PR #5304 (mulligan bottoming fix)

- **Status:** open
- **Source:** 2026-07-07, this session's Serum Powder / CR 103.5 mulligan
  bottoming fix.
- **Context:** As of 2026-07-07, PR [phase-rs/phase#5236](https://github.com/phase-rs/phase/pull/5236)
  (the core mulligan-declare-point-bottoming fix) is CI-green and
  **approved** by `matthewevans`, but not yet confirmed merged. PR
  [phase-rs/phase#5304](https://github.com/phase-rs/phase/pull/5304) (the
  isolated `.claude/skills/add-interactive-effect/SKILL.md` doc fix, split
  out of #5236 because `.claude/skills/**` is a hard-stop path for the
  automated PR review loop per `.agents/pr-review-policy.toml`) is
  CI-green but still shows `CHANGES_REQUESTED` from the same reviewer —
  expected and permanent by design, since skill-file PRs are excluded
  from that automated loop entirely. #5304 needs a human to merge it
  directly; it will never clear the bot review on its own.
- **Follow up around 2026-07-14 (about a week out)** if neither has moved:
  check whether #5236 actually got merged despite approval, and whether
  #5304 has been merged manually or needs a nudge.
- **Prompt:**
  > Check the current status of phase-rs/phase PR #5236 and PR #5304
  > (`gh pr view 5236 --repo phase-rs/phase`, `gh pr view 5304 --repo
  > phase-rs/phase`). If either is still open with no new activity, post a
  > polite follow-up comment or ping asking for merge. If #5236 has
  > drifted out of sync with `origin/main` (check `mergeStateStatus`),
  > sync it from a fresh worktree before pinging. If both have already
  > merged, mark this backlog item done.

### [feature] Custom/"design your own" format engine, instance-configurable — first presets: Eternal Central retro formats (93-94, 95, Middle School, Classic Magic)

- **Status:** open
- **Source:** 2026-07-07 planning discussion. Authoritative EC ruleset
  source (user-provided): https://github.com/northern-information/lordsofthepit.com/blob/main/src/pages/formats.md
  — fetched and confirmed this session, quoted below. Re-fetch before
  implementing in case the source has been updated since.
- **Reframed scope (2026-07-07, mid-discussion):** this item started as
  "add 4 hardcoded EC formats" and was deliberately widened to a more
  general capability once the user raised it — **don't build the narrow
  version.** The real ask has three layers, broadest first:
  1. A **general custom/"design your own format" engine**: players
     and/or instance operators can define a format (legal card pool,
     restricted/banned lists, deck-size rules, sideboard policy, starting
     life, mulligan variant, etc.) as *data*, without a phase.rs code
     change or rebuild.
  2. That data-driven format definition also needs an **independently
     toggleable "legacy/alternate rules" flag set** — see below, this is
     NOT the same axis as card-pool/banned-list restriction.
  3. The four EC formats (plus, as a stretch goal, LotP's "Eternal Chaos"
     variant) become the **first bundled presets** built on top of (1)
     and (2), proving the general system works, rather than a parallel
     hardcoded implementation that the custom-format engine would later
     have to duplicate or reconcile with.
  - This ordering matters: per CLAUDE.md's "build for the class, not the
    card," if a general custom-format system is the real target, building
    it first and expressing the four EC formats *through* it (as data) is
    the aligned design — not the other way around. Don't let "just ship 4
    formats fast" pull the implementation back to the narrow, hardcoded
    version once work starts.
- **Legacy/alternate rules — a separate, independently-toggleable axis
  from deck legality (confirmed this session via the EC source data):**
  Mana burn applies to **all four** EC formats (93-94, 95, Middle School,
  *and* Classic Magic). "Damage Uses the Stack" and pre-M10 Wish
  templating apply **only** to Middle School and Classic Magic — NOT
  93-94 or 95. Because these don't travel together, they must be modeled
  as independent flags (e.g. `LegacyRules { mana_burn: bool,
  damage_uses_stack: bool, pre_m10_wish_templating: bool, ... }`) that the
  core engine's rules logic checks generically wherever each applies —
  never as a per-format hardcoded check (`if format == MiddleSchool`).
  This flag set is itself part of what "design your own format" needs to
  expose, since real old-format communities disagree on which legacy
  rules to combine.
  - **These two legacy rules are NOT the same size of engine change —
    investigate both independently, don't assume parity:**
    - **Mana burn** was removed from the modern Comprehensive Rules
      entirely by the 2010 "M10" update (not present in current CR at
      all) — re-adding it as an optional flag is likely a well-contained
      addition IF the engine already tracks unspent mana when a pool
      empties at a step/phase boundary (probably does, since pool-emptying
      is itself required for any ruleset) — investigate that hook point
      specifically as the likely small, tractable piece.
    - **"Damage Uses the Stack"** is a deeper, pre-6th-edition combat
      resolution difference (damage was itself a stacked, response-able
      event rather than the current immediate-effect model) — likely
      touches core combat-damage-resolution ordering, not just a
      step-boundary check. Investigate whether the current engine has
      *any* hook-point for this before assuming it's comparable in size
      to mana burn. If it's genuinely large, ship deck-legality +
      mana-burn support first, with damage-on-the-stack as an explicitly
      separate, clearly-labeled follow-on — don't let it block everything
      else.
  - Neither of us knows yet how deep this goes in the current engine —
    that uncertainty is exactly what the research phase needs to resolve,
    not something to guess a size for now.
- **Instance-configurability and the design-interface question — genuinely
  open, don't assume an answer:** "instance customizable via configs" and
  "design your own format" could mean either (or both, feeding the same
  underlying schema): (a) a **player-facing UI** where someone builds a
  format interactively in the client and it's saved/shareable, or (b) an
  **operator-facing config file** a self-hosted phase-server instance
  loads at startup/build time to enable house-rule formats for that
  deployment only (the closest existing precedent for *that* half is
  `GATED_SETS` in `crates/engine/src/database/set_gating.rs` — an
  env-var-driven, generation-time config knob, though it's a narrow
  pre-release-embargo tool, not a general format-definition mechanism).
  Resolve which (or both) is wanted, and if both, confirm they share one
  underlying data schema rather than becoming two divergent
  implementations, before designing either.
- **The four EC-attributed formats (content confirmed, architecture is
  the open question above) — not two, "all EC variants" expands the
  original "93/94 + Middle School" ask to all four on the source page:**
  1. **Old School 93-94** — Alpha, Beta, Unlimited, Arabian Nights,
     Antiquities, Revised, Legends, The Dark, Fallen Empires. Reprints
     allowed only with original frame/art. Restricted (1 copy): Ancestral
     Recall, Balance, Black Lotus, Braingeyser, Chaos Orb, Channel,
     Demonic Tutor, Library of Alexandria, Mana Drain, Mind Twist, all
     five Moxes, Recall, Regrowth, Sol Ring, Time Vault, Time Walk,
     Timetwister, Wheel of Fortune. Banned: Bronze Tablet, Contract from
     Below, Darkpact, Demonic Attorney, Jeweled Bird, Rebirth, Tempest
     Efreet. Legacy rules: mana burn only. "No Draws" rule (tied matches
     after 50 minutes settled by Chaos Orb flip, not a draw).
  2. **Old School 95** — 93-94's pool plus Fourth Edition, Ice Age,
     Chronicles, Renaissance, Homelands. Restricted list = 93-94's plus
     Demonic Consultation and Mana Crypt. Banned list = 93-94's plus
     Amulet of Quoz and Timmerian Fiends. Legacy rules: mana burn only
     (same as 93-94).
  3. **Middle School** — 1995-2003 (Fourth Edition through Scourge).
     Reprints allowed (Collector's Edition/International Collector's
     Edition, World Championship, artist proofs; even modern-bordered
     reprints "begrudgingly" allowed). **No restricted list** — 25 named
     cards fully banned instead (Amulet of Quoz, Balance, Brainstorm,
     Bronze Tablet, Channel, Dark Ritual, Demonic Consultation, Flash,
     Goblin Recruiter, Imperial Seal, Jeweled Bird, Mana Crypt, Mana
     Vault, Memory Jar, Mind's Desire, Mind Twist, Rebirth, Strip Mine,
     Tempest Efreet, Timmerian Fiends, Tolarian Academy, Vampiric Tutor,
     Windfall, Yawgmoth's Bargain, Yawgmoth's Will). Legacy rules: mana
     burn AND damage-uses-the-stack AND pre-M10 Wish templating (all
     three).
  4. **Classic Magic** — full 1993-2003 pool (Alpha through Scourge), no
     new-border reprints of any kind (proxy or not). Its own restricted
     list (37 cards, mostly a superset spanning both eras — Ancestral
     Recall, Black Lotus, Necropotence, Vampiric Tutor, Yawgmoth's
     Bargain/Will, etc.) and banned list (11 cards). Legacy rules: mana
     burn AND damage-uses-the-stack AND wish-cycle restoration (same set
     as Middle School). Banlist updates twice yearly in the real world
     (Jan 1 / Jul 1) — likely irrelevant for a single-operator fork, but
     worth noting if this ever needs periodic re-sync.
  - **Stretch goal, not core scope:** "Eternal Chaos" on the same page is
    a Lords-of-the-Pit-specific variant built on top of EC 93-94 (adds
    booster-pack tutoring during matches, a dynamically-built sideboard
    from opened packs instead of a pre-built one, and a "Gentleman's
    Agreement" pre-match ban option) — it's NOT itself an EC-defined
    format, it's LotP's own house rule layered on 93-94. Confirmed wanted
    (2026-07-07), but explicitly sequenced after the four core EC formats
    (and the general custom-format engine they're built on) ship — it
    depends on 93-94 already existing and adds a genuinely new mechanic
    (in-match pack-opening + dynamic sideboard), not just a rules-flag
    combination.
  - **Stub — Type 4's core rules as a possible future variant, NOT
    researched or designed, just flagged for later consideration
    (2026-07-07).** While cross-checking Dandan (`#5169`, a shared-library
    format proposal — see below) against this design, confirmed via
    WebSearch that **Type 4** (a real, decades-old casual format:
    unlimited mana at all times, no lands, one spell per turn, chaos
    targeting, last-player-standing) has a documented "all players use the
    pool as a shared library" variant — the same zone-sharing shape as
    Dandan. Type 4's shared-library variant is a candidate future preset
    for the general custom-format engine's `SharedZones` building block
    (see below), and its *other* core rules (infinite mana, no lands,
    one-spell-per-turn, chaos targeting) are a candidate future
    `LegacyRuleSet`-style axis in the same framework — each independently
    toggleable, the same way mana-burn/damage-on-stack are for the EC
    formats. **None of this has been investigated for engine feasibility**
    (no idea yet how large "unlimited mana"/"no lands"/"one spell per
    turn" are as engine changes) — this is a bare stub for a future
    research pass, not a scoped ask. See
    `.planning/phases/58-custom-format-engine/CONTEXT.md`'s Dandan
    cross-reference for the verified sourcing.
- **Architecture context already confirmed this session (applies whether
  the general custom-format engine turns out to be built on top of
  `GameFormat` or alongside it):**
  - `GameFormat`/`FormatConfig`/`FormatMetadata` (`crates/engine/src/types/format.rs`)
    is a real, well-established, self-documenting pattern for *built-in*
    formats (see `GameFormat::Premodern`: one enum variant, one
    `FormatConfig::premodern()` builder inheriting from `standard()`, one
    `FormatMetadata` registry entry, one `LegalityFormat` mapping) — but
    it's a closed, compile-time Rust enum, which is the right shape for a
    fixed official-format list and the *wrong* shape for player/operator-
    authored custom formats. The custom-format engine likely needs an
    additive, data-driven layer alongside this (e.g. a
    `GameFormat::Custom(CustomFormatId)` variant or an entirely separate
    format-identity concept), not a wholesale rewrite of `GameFormat`
    into stringly-typed data.
  - **Real prior art for a new-format planning cycle in this exact repo**:
    `GameFormat::Limited` — see `.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`,
    committed at `80404a98b` (`.planning/` is gitignored and was later
    stripped from tracking entirely — commit "Remove planning docs" — so
    it no longer exists in a fresh checkout; retrieve it via `git show
    80404a98b:.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`).
  - `Premodern`'s (and every built-in format's) per-card legality comes
    from an *externally-sourced* per-card `legalities` field ingested
    into `CardLegalities` (`crates/engine/src/database/legality.rs` +
    `card_db.rs`'s `normalize_legalities(&entry.legalities)`) — this
    mirrors Scryfall/MTGJSON's own bulk-data legality keys (`"standard"`,
    `"premodern"`, `"pioneer"`, etc.). **None of the four EC formats are
    expected to have that external per-card legality signal already
    populated** — confirm directly (check an actual card's raw ingested
    legality data for an `"oldschool"`/`"middleschool"`/`"classic"` key)
    rather than assuming, but if absent as expected, this is exactly the
    kind of thing the general custom-format engine needs to support
    natively: a locally-defined legal-set-code + restricted/banned-name
    list, evaluated directly against each card's set code and name,
    independent of the `CardLegalities` pipeline. `set_gating.rs` was
    checked as a candidate for this and does NOT fit (pre-release
    embargo tool only).
  - **`DeckCopyLimit::UpTo(n)`** (already exists in `format.rs`, currently
    used for per-card overrides like Relentless Rats/Nazgûl/Commander
    singleton) may directly be the right building block for "restricted
    to 1 copy" in a custom format's restricted list — check reuse before
    inventing a second, parallel "restricted list" concept.
  - **Parameterize, don't proliferate** (per CLAUDE.md) applies twice
    here: once at the "custom format schema vs. four separate EC formats"
    level (the four EC presets should be four instances of one schema,
    not four hardcoded blocks), and again within any built-in-format
    fallback path if one still exists after the custom engine is built.
  - **Design/research output belongs in `.planning/phases/<NN>-<slug>/`**
    (CONTEXT/RESEARCH/PLAN/SUMMARY/VERIFICATION docs per CLAUDE.md's own
    "Planning" section) — gitignored, stays local, decoupled from any PR,
    matching how the `GameFormat::Limited` cycle above was actually run.
    Research/design can happen well before implementation and by a
    different session/agent; don't conflate the two phases.
- **Prompt:**
  > Research and produce a plan (don't implement yet, write it to
  > `.planning/phases/<NN>-custom-format-engine/`) for a general,
  > data-driven "design your own format" engine in phase.rs, with the
  > four Eternal Central retro formats (Old School 93-94, Old School 95,
  > Middle School, Classic Magic) as the first bundled presets exercising
  > it. Do NOT scope this narrowly as "hardcode 4 GameFormat variants" —
  > the actual ask is the general engine first, formats as data on top of
  > it. Re-fetch https://github.com/northern-information/lordsofthepit.com/blob/main/src/pages/formats.md
  > to confirm the exact card pools/restricted/banned lists quoted in this
  > backlog item (as of 2026-07-07) haven't changed. First read
  > `crates/engine/src/types/format.rs` in full (trace `GameFormat::Premodern`
  > end-to-end) and `.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`
  > (retrieve via `git show 80404a98b:.planning/phases/53-limited-draft-core/53-01-SUMMARY.md`
  > since `.planning/` is gitignored) as prior art for how a new-format
  > planning cycle has actually been scoped in this repo. Design: (1) a
  > data-driven custom-format definition schema (legal-set list,
  > restricted/banned name lists, deck-size/sideboard rules, and an
  > independently-toggleable `LegacyRules` flag set covering at minimum
  > mana burn and damage-uses-the-stack — confirmed NOT to travel together,
  > since 93-94/95 use only mana burn while Middle School/Classic Magic
  > use both, so they must be separate flags, not one "old rules" bool);
  > (2) how that schema relates to the existing closed `GameFormat` enum
  > (additive `Custom` variant vs. parallel concept — the existing enum
  > should stay closed/typed for official formats, this needs to be a
  > separate additive layer, not a rewrite into stringly-typed data); (3)
  > resolve whether "design your own format" means a player-facing UI, an
  > operator-facing per-instance config file (nearest existing precedent:
  > `GATED_SETS` in `crates/engine/src/database/set_gating.rs`, though it
  > doesn't fit as a mechanism, only as a rough shape of "env/config-driven
  > deployment customization"), or both sharing one schema — don't assume
  > an answer. Confirm directly whether the card-data pipeline's
  > `CardLegalities`/`LegalityFormat` mechanism already carries any signal
  > for these EC formats (expected: no) before designing the new
  > locally-defined legal-set/banned-list mechanism the custom-format
  > engine will need regardless. Separately and independently investigate
  > mana burn (likely small — check whether the engine already tracks
  > unspent mana at pool-emptying boundaries) versus "damage uses the
  > stack" (likely much larger — a pre-6th-edition combat-resolution
  > difference, not a deck-legality filter; report whether the engine has
  > any hook for this at all) — do not assume they're the same size of
  > change. If damage-on-the-stack is large, propose shipping
  > deck-legality + mana-burn support for all four EC formats first, with
  > damage-on-the-stack as a clearly separate, non-blocking follow-on. The
  > LotP-specific "Eternal Chaos" variant (booster-pack tutoring built on
  > 93-94, not itself an EC-defined format) is a confirmed stretch goal —
  > sequence it after the core engine and four EC presets ship; note it in
  > the plan but don't block on it.

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
  `DEPLOY_HOST_PORT`, currently only on the `teamserio.us` repo). **TLS
  terminates at the reverse proxy itself** (confirmed by the user) — not
  an AWS-layer component (ALB/CloudFront) in front of it, so a
  `phase.teamserio.us` cert needs to be issued for nginx directly, not
  requested through an AWS console/ACM flow.
- **What's genuinely unconfirmed:**
  1. **Exact TLS mechanism on the box** — likely certbot/Let's Encrypt
     given nginx terminates TLS itself, but not confirmed which ACME
     client or whether renewal is a cron job/systemd timer — check
     `which certbot`, `systemctl list-timers`, and `/etc/letsencrypt/`
     (or equivalent) before assuming certbot specifically.
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
  > read-only — do not change anything. TLS is confirmed to terminate at
  > the nginx reverse proxy itself (not an AWS-layer ALB/CloudFront), so
  > just confirm (1) the exact mechanism (`which certbot`, look for a
  > renewal cron/systemd timer, check `/etc/letsencrypt/` or equivalent);
  > (2) the nginx config layout and the literal existing server block for
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

### [bug-fix] Ad Nauseam's repeat loop never adds revealed cards to hand (GitHub #1032)

- **Status:** in-progress — fixed, tested, PR open awaiting CI/review:
  [phase-rs/phase#5315](https://github.com/phase-rs/phase/pull/5315)
- **Source:** GitHub issue [phase-rs/phase#1032](https://github.com/phase-rs/phase/issues/1032),
  surfaced via the same Vintage-relevance sweep as the Underworld Breach
  item above.
- **Verified Oracle text** (Scryfall, not from memory): "Reveal the top
  card of your library and put that card into your hand. You lose life
  equal to its mana value. You may repeat this process any number of
  times." ({3}{B}{B})
- **Confirmed real bug (2026-07-07)**, reproduced from scratch via parsed
  Oracle text in an isolated worktree, through two rounds of
  `/engine-planner` + `/review-engine-plan` (round 1 had a factual error
  in its root-cause model — claimed `pending_continuation` was
  last-write-wins/clobbering, when it actually accumulates via
  `append_to_sub_chain` — which would have produced a non-discriminating
  test; round 2 corrected this) and one clean `/review-impl` pass.
- **Root cause:** `engine_resolution_choices.rs`'s `RepeatDecision`
  accept-handler re-entered `resolve_ability_chain` without resetting
  `state.waiting_for` away from the just-answered `RepeatDecision`
  prompt, which fooled `waits_for_resolution_choice` into deferring each
  iteration's `ChangeZone`(hand)/`LoseLife` sub-chain into
  `pending_continuation` instead of running it immediately — deferred
  pairs accumulated and all drained in one batch on decline, matching the
  reported symptom exactly.
- **Fix:** one-line `set_priority(state, player)` reset, mirroring the
  sibling `decline` branch and the analogous `OptionalEffectChoice`
  resume handler, both of which already do this. Class-level fix — covers
  every `RepeatContinuation::ControllerChoice` card with a multi-step
  body, not just Ad Nauseam. CR 107.1c + CR 608.2c verified against
  `docs/MagicCompRules.txt`.
- **Verification:** new discriminating integration test (asserts hand/life
  *between* accepts, not just final aggregate — final totals are
  identical whether the bug is present or not) confirmed to fail on the
  unfixed code and pass on the fixed code; 9/9 sibling repeat-mechanism
  tests and 3/3 existing lib unit tests unaffected; `cargo fmt`/`clippy
  -D warnings` clean.

### [bug-fix] Pact of Negation doesn't lose the game on unpaid deferred cost (GitHub #1058)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1058](https://github.com/phase-rs/phase/issues/1058);
  Vintage staple (free counterspell protecting combo, ~77% inclusion in
  relevant decks) — no open PR.
- **Verified Oracle text:** "Counter target spell. At the beginning of
  your next upkeep, pay {3}{U}{U}. If you don't, you lose the game." ({0})
- **Reported bug:** AI doesn't lose the game when it can't/doesn't pay the
  deferred {3}{U}{U} cost on the following upkeep.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Pact of Negation (GitHub phase-rs/phase#1058): the deferred
  > "pay {3}{U}{U} at your next upkeep or lose the game" clause isn't
  > enforced. Verify Oracle text against Scryfall first. This is a
  > delayed-triggered-cost pattern shared by the whole Pact cycle (Pact of
  > Negation, Pact of the Titan, Slaughter Pact, etc.) — trace how any
  > existing Pact is modeled before assuming none are, and build/fix the
  > shared delayed-trigger + "lose the game if unpaid" primitive rather
  > than a one-off check. Use `/add-trigger` for the delayed-trigger wiring.

### [bug-fix] Relic of Progenitus's first ability doesn't respect the targeted player (GitHub #1077)

- **Status:** open — narrowed from the original two-part report
- **Source:** GitHub issue [phase-rs/phase#1077](https://github.com/phase-rs/phase/issues/1077);
  standard Vintage sideboard graveyard hate against Dredge (a current
  top-3 Vintage archetype) — no open PR.
- **Verified Oracle text:** "{T}: Target player exiles a card from their
  graveyard. {1}, Exile this artifact: Exile all graveyards. Draw a
  card." ({1})
- **Investigated 2026-07-07:** traced against current `main` before
  implementing. The *second* ability ("exile all graveyards, draw a
  card") uses only well-tested primitives (exile-self cost,
  `ChangeZoneAll`, `Draw`) and multi-activated-ability parsing is
  foundational engine-wide — no evidence this is actually broken as the
  original report claimed. Narrowing this item to the first ability only.
- **Reported bug (first ability, still real):** `inject_subject_target`
  (`oracle_effect/mod.rs`) rewrites the subject for `Discard`, `Draw`,
  `Scry`, `Token`, `ChangeZoneAll`, `Shuffle`, etc., but **not**
  `Effect::ChangeZone` — the single-card exile this ability needs. The
  generic exile fallback (`oracle_effect/imperative.rs`) only has a
  hardcoded `attach_controller_if_absent(ControllerRef::You)` arm for
  "...from your hand"; there's no possessive-pronoun-to-target-player
  binding for "...from their graveyard." This matches the reported
  symptom (shows activator's own graveyard instead of the targeted
  player's).
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Relic of Progenitus's first ability (GitHub phase-rs/phase#1077):
  > "Target player exiles a card from their graveyard" must bind the
  > exile's subject/controller to the *targeted player*, not the
  > activator. Verify Oracle text against Scryfall first. `ChangeZone`
  > is missing from `inject_subject_target`'s handled-effect list
  > (`oracle_effect/mod.rs`) alongside `Discard`/`Draw`/`Scry`/`Token`/
  > `ChangeZoneAll`/`Shuffle` — this is a possessive-pronoun-to-target
  > binding gap in a shared building block, not a Relic-specific fix, so
  > check whether other "target player discards/exiles/puts a card from
  > their [zone]" effects share the same gap before scoping the fix to
  > just `ChangeZone`. Do NOT touch the second ability ("exile all
  > graveyards, draw a card") — investigation confirmed it already works
  > correctly; the original issue's claim about it not working appears to
  > be false.

### [bug-fix] Violent Urge grants delirium bonus to all creatures, not just the target (GitHub #1272)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1272](https://github.com/phase-rs/phase/issues/1272);
  Old School 93/94-legal (Legends) — flagged for completeness during a
  format sweep, but honestly a minor/fringe card even in its own era, not
  a real played staple. Low conviction, tracked anyway per instruction.
- **Verified Oracle text:** "Target creature gets +1/+0 and gains first
  strike until end of turn. Delirium — If there are four or more card
  types among cards in your graveyard, that creature gains double strike
  until end of turn." ({R})
- **Reported bug:** with delirium active, double strike is granted to all
  creatures instead of just the targeted creature.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Violent Urge (GitHub phase-rs/phase#1272): the delirium clause
  > ("that creature gains double strike") must apply only to the single
  > targeted creature, not all creatures — "that creature" refers back to
  > the same target as the base +1/+0/first strike effect, it isn't a new
  > unrestricted grant. Verify Oracle text against Scryfall first. This
  > looks like a `~`/target-reference resolution bug likely shared by
  > other delirium/threshold "that creature gains X" follow-up clauses —
  > check whether the same reference-scoping bug affects other
  > conditional-bonus cards with an identical "target creature ... ;
  > condition — that creature also gains Y" shape before scoping the fix
  > to just this card.

### [bug-fix] Solitary Confinement prevents damage to all players instead of just its controller (GitHub #1062)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1062](https://github.com/phase-rs/phase/issues/1062);
  Middle-School-era (Judgment) casual prison piece — moderate match, not
  a top competitive staple even in its era, tracked for completeness.
- **Verified Oracle text:** "At the beginning of your upkeep, sacrifice
  this enchantment unless you discard a card. Skip your draw step. You
  have shroud. Prevent all damage that would be dealt to you." ({2}{W})
- **Reported bug:** the damage-prevention clause is being applied
  globally (prevents damage to all players) instead of scoped to the
  enchantment's controller only.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Solitary Confinement (GitHub phase-rs/phase#1062): "Prevent all
  > damage that would be dealt to you" must scope to the enchantment's
  > controller only, not all players. Verify Oracle text against Scryfall
  > first. This looks like a `you`-reference resolved as a global/no-op
  > scope instead of `ControllerRef::You` in a damage-prevention shield —
  > check whether the same "prevent all damage to you" pattern (shared by
  > other damage-prevention enchantments/effects) has the same
  > controller-scoping bug elsewhere before fixing this one card in
  > isolation.

### [bug-fix] Calming Licid: transform effect no-ops and summoning sickness misapplied (GitHub #605, #604)

- **Status:** open
- **Source:** GitHub issues [phase-rs/phase#605](https://github.com/phase-rs/phase/issues/605)
  and [phase-rs/phase#604](https://github.com/phase-rs/phase/issues/604);
  Homelands (1995) — legal in Middle School, but Homelands commons are
  notoriously weak and this was never actually a played card, even
  casually. Low conviction, tracked anyway per instruction.
- **Verified Oracle text:** "{W}, {T}: This creature loses this ability
  and becomes an Aura enchantment with enchant creature. Attach it to
  target creature. You may pay {W} to end this effect. Enchanted creature
  can't attack." ({2}{W})
- **Reported bugs:**
  1. (#605) Activating the ability targeting an enemy creature does
     nothing — the creature-to-Aura transform + attach never happens.
  2. (#604) Separately, a Calming Licid that entered on a prior turn
     can't be declared as an attacker on a later turn — summoning
     sickness appears to be checked incorrectly (still treating it as
     having just entered).
- **Before implementing:** re-confirm both still reproduce on current
  `main` — these may already share a root cause (e.g. some persistent
  "just entered"/ability-availability flag not clearing correctly) worth
  investigating together rather than as two unrelated fixes.
- **Prompt:**
  > Fix Calming Licid (GitHub phase-rs/phase#605 and #604): (1) its
  > activated ability ("becomes an Aura enchantment ... attach it to
  > target creature") doesn't perform the creature-to-Aura type change +
  > attach at all when activated; (2) separately, it can't attack on a
  > later turn even though it should no longer have summoning sickness.
  > Verify Oracle text against Scryfall first. This is the Licid cycle's
  > shared "creature becomes an Aura and attaches to another permanent,
  > with a way to revert" mechanic (Homelands' five Licids all share this
  > text shape) — trace how any existing type-changing "becomes an Aura"
  > effect is modeled before writing new logic, and check whether the
  > summoning-sickness bug is actually caused by the same underlying
  > state transition (e.g. the type-change incorrectly resetting an
  > "entered this turn" flag) rather than two unrelated defects.

### [bug-fix] Molten Echoes gives haste to the wrong object and skips its end-step exile (GitHub #4709, #4708)

- **Status:** open
- **Source:** GitHub issues [phase-rs/phase#4709](https://github.com/phase-rs/phase/issues/4709)
  and [phase-rs/phase#4708](https://github.com/phase-rs/phase/issues/4708);
  Middle-School-era (Torment) — obscure even in its own era, low
  conviction, tracked anyway per instruction.
- **Verified Oracle text** (note: differs from both issues' "expected
  behavior" — the real card says *exile*, not sacrifice, and grants haste
  to the *token*, matching #4709 but contradicting #4708's assumption):
  "As this enchantment enters, choose a creature type. Whenever a
  nontoken creature you control of the chosen type enters, create a token
  that's a copy of that creature. That token gains haste. Exile it at the
  beginning of the next end step." ({2}{R}{R})
- **Reported bugs:**
  1. (#4709) The *original* nontoken creature gets haste instead of the
     copy token — confirmed wrong against Oracle text, "that token gains
     haste" clearly refers to the created copy.
  2. (#4708) Reporter expected the token to be *sacrificed* at end step;
     actual text says *exile*, and only "it" (the single token just
     created) — not a sacrifice-all-tokens effect. The real bug to fix is
     that the token isn't being exiled at the next end step at all
     (whether via a missing delayed trigger or one that never fires), not
     that it isn't being sacrificed.
- **Before implementing:** re-confirm still reproduces on current `main`,
  and implement the *exile*, not sacrifice, behavior — do not blindly
  follow the issue's "expected behavior" text.
- **Prompt:**
  > Fix Molten Echoes (GitHub phase-rs/phase#4709 and #4708). Verify
  > Oracle text against Scryfall first — note the real text says the
  > created *token* gains haste (not the original creature, which #4709
  > correctly flags) and that the token is *exiled* at the beginning of
  > the next end step (a delayed trigger scoped to that one token, not a
  > sacrifice-all-copies effect — #4708's "expected behavior" wording is
  > wrong on this point, don't implement it as written). Fix: (1) haste is
  > currently granted to the wrong object; (2) the delayed "exile at next
  > end step" trigger for the token isn't firing at all. Trace how other
  > "create a token copy, then exile/sacrifice it later" delayed-trigger
  > effects are modeled (this is a general delayed-trigger-on-a-specific-
  > object pattern) before writing new resolution logic.

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

### [feature] Add a Premodern metagame decks feed

- **Status:** open
- **Source:** 2026-07-07 request
- **Context (verified against the repo, not assumed):** phase.rs already has
  a per-format metagame-decks feed system, distinct from the Commander-only
  "precon" system (`useDecks.ts`, `PreconDeckModal.tsx`) — don't confuse the
  two. The relevant one is `client/src/data/feedRegistry.ts:12-74`, which
  lists a bundled feed JSON per format (`mtggoldfish-standard.json`,
  `-modern`, `-pioneer`, `-commander`, `-legacy`, `-vintage`, `-pauper`) at
  `client/public/feeds/*.json`, in the shape `{id, name, description, icon,
  format, version, updated, source, decks: [{name, author, colors, tags,
  main:[{count,name}], sideboard, commander?}]}`. **No
  `mtggoldfish-premodern.json` exists yet** — that's the gap. `Premodern` is
  already a fully supported engine format
  (`crates/engine/src/types/format.rs:42` `GameFormat::Premodern`,
  `client/src/data/formatRegistry.ts:76-84`), so this is purely a
  missing-feed gap, not a missing-format gap.
  - Feed generation already has an external-source pipeline to extend:
    `crates/feed-scraper/src/scrape.rs` scrapes
    `https://www.mtggoldfish.com/metagame/{format}` (URL built at
    `scrape.rs:16`) via a `--format` CLI arg (`main.rs:19-21`, comma-separated
    list), writing feed JSON into `client/public/feeds/`. MTGGoldfish does
    have a `/metagame/premodern` page, so `--format premodern` should work
    with no scraper changes — just needs to be added to the invocation.
    `.github/workflows/refresh-feeds.yml:34` (daily cron) currently only
    passes `--format standard,modern,pioneer,commander`; add `premodern` to
    that list so it refreshes automatically going forward (existing
    legacy/vintage/pauper feeds exist but appear to have been generated
    manually/separately, not via the cron — check whether they should also
    be added to the cron list while touching this, or leave that as a
    separate decision).
  - Minor: `config_format_tag()` in `scrape.rs:283-302` has a hardcoded
    format-name list used only for a title-matching fallback tag; it doesn't
    include `"premodern"` today. Not blocking (falls back to a generic
    `"metagame"` tag, cosmetic only) but worth adding while in this file.
  - **tcdecks.net has no existing precedent anywhere in this repo** — if
    MTGGoldfish's `/metagame/premodern` page turns out to be thin/stale
    (Premodern has a much smaller competitive scene than the formats
    `feed-scraper` currently targets), tcdecks.net would be a second,
    net-new source requiring its own scraper — confirm MTGGoldfish coverage
    is adequate first before building a second source for one format.
- **Prompt:**
  > Add a Premodern feed to phase.rs's metagame-decks system (not the
  > Commander-only precon system — those are separate; this is
  > `client/src/data/feedRegistry.ts` + `client/public/feeds/*.json`).
  > `Premodern` is already a supported engine format
  > (`crates/engine/src/types/format.rs`); the gap is purely the missing
  > `mtggoldfish-premodern.json` feed. Extend `crates/feed-scraper` (already
  > scrapes `mtggoldfish.com/metagame/{format}`, see `scrape.rs`) with
  > `--format premodern` and add it to the `.github/workflows/refresh-feeds.yml`
  > cron's `--format` list so it refreshes automatically. Check MTGGoldfish's
  > actual `/metagame/premodern` page first to confirm it has real deck data
  > worth scraping (Premodern's competitive scene is much smaller than
  > Standard/Modern/Pioneer) — only reach for tcdecks.net as a second source
  > if MTGGoldfish's Premodern coverage turns out inadequate, since
  > tcdecks.net has zero existing scraper precedent in this repo and would be
  > net-new work. Register the new feed in `feedRegistry.ts` following the
  > existing per-format entries exactly. Also add `"premodern"` to the
  > format-name list in `config_format_tag()` (`scrape.rs`) for a correct
  > fallback tag.

---

## Done

### [bug-fix] ~~Underworld Breach doesn't enforce its escape cost~~ — already fixed (GitHub #1033)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1033](https://github.com/phase-rs/phase/issues/1033),
  surfaced via a Vintage-relevance sweep of unclaimed `[Card Bug]` issues.
- **Investigated 2026-07-07** in an isolated worktree via the full
  `engine-implementer` planning step (`/engine-planner`), then
  independently re-verified by me directly (not just trusting the
  planner agent): ran `cargo test -p engine --lib escape` and confirmed
  all 31 tests pass, including the exact scenario in this issue
  (`granted_escape_requires_exile_cost_payment`,
  `ai_escape_cast_from_graveyard_pays_mana_and_exiles_five_cards`).
  Confirmed `aa4ee3455` ("Generalize graveyard keyword grants: parse
  escape continuation (Underworld Breach)...") is a real, merged ancestor
  of current `main` via `git merge-base --is-ancestor`.
- **Findings:**
  1. The "exile 0/0, cast goes through anyway" bug no longer reproduces —
     `effective_escape_data` (`game/keywords.rs`) refuses any escape grant
     with no residual cost, and both `can_pay_escape_additional_cost`
     (`game/casting.rs`) and the `AbilityCost::Exile` arm of
     `pay_additional_cost` (`game/casting_costs.rs`) gate on the real
     fixed count (3), not a clamped-to-available count.
  2. The "Breach re-escapes itself from the graveyard" concern is
     RAW-legal-question resolved as **not a bug**: per CR 604.2, a static
     ability's continuous effect only exists while its source remains on
     the battlefield (or in the zone the ability specifies) — once
     Breach's own end-step trigger sacrifices it, its escape-granting
     effect stops existing before it could apply to Breach sitting in the
     graveyard. The engine's `for_each_static_effect_source` sources
     grants exclusively from `battlefield_sources`, so this is already
     correct.
- **Action taken:** closed as resolved on GitHub with this evidence;
  no PR needed for this item.

### [bug-fix] ~~Karn, the Great Creator's static doesn't stop opponents' artifact activations~~ — already fixed (GitHub #1080)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1080](https://github.com/phase-rs/phase/issues/1080);
  Karn is the centerpiece of Karn Shops, one of Vintage's current top
  archetypes.
- **Investigated 2026-07-07** by tracing the actual code on current `main`
  before touching anything, per this repo's "verify the card, not just the
  rule" policy — no worktree code changes were needed.
- **Findings:**
  1. `is_blocked_by_cant_be_activated` (`game/casting.rs`) evaluates
     `StaticMode::CantBeActivated`'s `TypeFilter::Artifact` against
     **live** `obj.card_types.core_types` at activation time, not a
     cached/ETB-time snapshot.
  2. `ContinuousModification::AddType` (`game/layers.rs:4861`) — the
     mechanism Liquimetal Coating uses to turn a permanent into an
     artifact — pushes directly into that same `core_types` field during
     the continuous-effects layer pass. A land turned into an artifact
     *after* Karn is already on the battlefield therefore feeds the
     identical live field Karn's static checks against — exactly the
     scenario this issue describes.
  3. This was generalized in `d1c99a805` ("prohibitions: widen
     CantBeActivated…"), which explicitly lists "Karn, the Great Creator
     (first static)" as one of the cards it unlocked, and is already an
     ancestor of current `main` (confirmed via `git merge-base
     --is-ancestor`).
  4. Two dedicated tests already cover this exact mechanism:
     `karn_blocks_opponent_artifact_activation` and
     `karn_permits_own_artifact_activation` in `game/casting_tests.rs`.
- **Action taken:** could not close the issue directly (insufficient
  GitHub permissions on `phase-rs/phase`); posted evidence as a comment
  instead ([issuecomment-4908412649](https://github.com/phase-rs/phase/issues/1080#issuecomment-4908412649))
  asking a maintainer to confirm and close. No PR needed for this item.

### [bug-fix] ~~Cityscape Leveler's Powerstone token is delayed and goes to the wrong controller~~ — already fixed (GitHub #1079)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1079](https://github.com/phase-rs/phase/issues/1079);
  sideboard/maindeck payoff in Vintage Karn Shops.
- **Investigated 2026-07-07** by tracing current `main` before touching
  anything.
- **Findings:** the generic "[verb] target permanent. Its controller
  creates a token" shape is a tested, general pattern, not per-card
  logic. `oracle_effect/tests.rs`
  (`effect_its_controller_creates_tokens_sets_parent_target_controller_owner`)
  confirms "Its controller creates two Map tokens" lowers
  `owner: TargetFilter::ParentTargetController` — the destroyed/exiled
  object's controller, not the source's. Immediacy is proven by a
  full-pipeline test on a structurally identical real card, Fractured
  Identity (`oracle_pipeline_snapshot_tests.rs`,
  `fractured_identity_each_player_other_than_controller_copies_exiled_permanent`):
  its second sentence becomes a `sub_ability`
  (`AbilityDefinition::sub_ability`, `types/ability.rs`) — a
  same-resolution continuation, never a new/delayed trigger. No
  card-specific code exists for Cityscape Leveler; it rides this
  already-correct general path.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.

### [bug-fix] ~~Expressive Iteration sends cards to the wrong zones~~ — already fixed (GitHub #1271)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1271](https://github.com/phase-rs/phase/issues/1271);
  played in Vintage Izzet fast-mana shells.
- **Investigated 2026-07-07.** `game/effects/mod.rs` contains a dedicated
  regression test, `expressive_iteration_dig_chain_reaches_library_bottom_and_exile`
  (citing issue #1162), using the exact card text, that drives the real
  parser + real resolver and asserts: card kept → Hand, card chosen for
  bottom → Library back, and the third, unchosen card → Exile with
  `CastingPermission::PlayFromExile` — precisely the correct (non-swapped)
  zone assignment. Source-level evidence directly contradicts the
  reported swap; a full `cargo test -p engine` run could not be completed
  in-session to get a live green confirmation, but the assertions are
  unambiguous.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.

### [bug-fix] ~~Endurance's ETB fizzles if killed in response~~ — already fixed (GitHub #1059)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#1059](https://github.com/phase-rs/phase/issues/1059);
  free pitch-elemental graveyard hate/blocker played across
  Legacy/Vintage.
- **Investigated 2026-07-07.** The general CR 608.2a/b class ("a trigger
  whose source leaves the battlefield before it resolves must still
  resolve") is explicitly tested:
  `fabricate_e2e_source_gone_servo_branch_still_creates_tokens`
  (`database/synthesis.rs`) bounces the trigger's source mid-resolution
  and asserts the trigger is NOT removed. `resolve_ability_chain`
  (`game/effects/mod.rs`) has no source-existence gate. Endurance's
  simple "up to one target player" ETB rides this same generic path.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.

### [bug-fix] ~~Mother of Runes doesn't let you choose the protection color~~ — already fixed (GitHub #624)

- **Status:** done — verified already fixed, no code change needed
- **Source:** GitHub issue [phase-rs/phase#624](https://github.com/phase-rs/phase/issues/624);
  Middle-School/Premodern-era (Urza's Legacy) white-aggro staple, still
  played across Legacy/Premodern/Canadian-Highlander today.
- **Investigated 2026-07-07.** `crates/engine/tests/fixtures/integration_cards.json`
  and the golden `mother_of_runes_ir.snap` both show a real
  `Choose { choice_type: Color, persist: true }` step feeding
  `Protection: ChosenColor`. `game/effects/choose.rs` sets
  `WaitingFor::NamedChoice` for `ChoiceType::Color` — a genuine
  interactive prompt, not a fixed/random pick.
- **Action taken:** posted evidence as a comment (no permission to close
  directly). No PR needed.
