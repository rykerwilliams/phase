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

### [bug-fix] Underworld Breach doesn't enforce its escape cost (GitHub #1033)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1033](https://github.com/phase-rs/phase/issues/1033),
  surfaced via a Vintage-relevance sweep of unclaimed `[Card Bug]` issues —
  no open PR addresses this.
- **Verified Oracle text** (Scryfall, not from memory): "Each nonland card
  in your graveyard has escape. The escape cost is equal to the card's mana
  cost plus exile three other cards from your graveyard. At the beginning
  of the end step, sacrifice this enchantment." ({1}{R})
- **Reported bug:** casting a card via escape shows "Exile (0/0" and lets
  the cast through without exiling anything — reporter looped a single
  Dark Ritual infinitely with an empty graveyard. Underworld Breach also
  lets itself be recast from the graveyard via its own escape ability,
  which shouldn't be legal since it grants escape to *other* nonland cards
  in the graveyard, not a recursive grant to itself once it's already on
  the stack/battlefield each time.
- **Before implementing:** re-confirm this still reproduces on current
  `main` — the issue is unlabeled/`needs-triage` and may already be stale.
- **Prompt:**
  > Fix Underworld Breach (GitHub phase-rs/phase#1033): its escape-cost
  > grant isn't enforcing "exile three other cards from your graveyard" —
  > the UI shows a 0-card exile requirement and lets the cast through
  > without exiling anything, and the card can illegally re-escape itself
  > from the graveyard turn after turn. Verify current Oracle text against
  > Scryfall before touching anything, trace how escape costs are
  > authored/resolved elsewhere in the engine (this is a general "has
  > escape" grant pattern, likely shared with cards like Uro/Prized
  > Amalgam-style escape — build for the class per CLAUDE.md, not just
  > this card), and confirm CR annotations for escape (CR 702.148 area —
  > verify the exact number against `docs/MagicCompRules.txt` before
  > citing it). Use `/add-engine-effect` or `/casting-stack-conditions` as
  > appropriate once you've traced the existing cost-resolution authority.

### [bug-fix] Ad Nauseam's repeat loop never adds revealed cards to hand (GitHub #1032)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1032](https://github.com/phase-rs/phase/issues/1032),
  surfaced via the same Vintage-relevance sweep as the Underworld Breach
  item above — no open PR addresses this.
- **Verified Oracle text** (Scryfall, not from memory): "Reveal the top
  card of your library and put that card into your hand. You lose life
  equal to its mana value. You may repeat this process any number of
  times." ({3}{B}{B})
- **Reported bug:** the repeat-loop UI reveals the top card each time
  "repeat" is clicked but never actually moves it to hand; life loss is
  batched and applied all at once at the end instead of per-repetition
  as each card is added.
- **Before implementing:** re-confirm this still reproduces on current
  `main` — the issue is unlabeled/`needs-triage` and may already be stale.
- **Prompt:**
  > Fix Ad Nauseam (GitHub phase-rs/phase#1032): the "repeat this process"
  > loop reveals the top card of the library each click but never puts it
  > into hand, and life loss is applied once in bulk at the end instead of
  > immediately after each individual reveal/hand-add. Verify current
  > Oracle text against Scryfall before touching anything. This is a
  > repeated-optional-effect pattern (reveal → move zone → lose life →
  > ask to repeat) — trace how other "you may repeat this process" or
  > iterative reveal effects are modeled in the engine first (per
  > CLAUDE.md's "trace before you build") rather than writing a
  > card-specific loop. Use `/add-interactive-effect` for the
  > choice/WaitingFor round-trip piece.

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

### [bug-fix] Karn, the Great Creator's static doesn't stop opponents' artifact activations (GitHub #1080)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1080](https://github.com/phase-rs/phase/issues/1080);
  Karn is the centerpiece of Karn Shops, one of Vintage's current top
  archetypes — no open PR.
- **Verified Oracle text:** "Activated abilities of artifacts your
  opponents control can't be activated." plus his +1/−2 loyalty abilities.
  ({4}, planeswalker)
- **Reported bug:** with Karn in play, if an opponent's land is turned into
  an artifact creature (e.g. via Liquimetal Coating), the opponent can
  still activate abilities from it — the static isn't being applied to
  permanents that become artifacts after Karn is already on the
  battlefield, or isn't checked at activation time at all.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Karn, the Great Creator (GitHub phase-rs/phase#1080): his static
  > "Activated abilities of artifacts your opponents control can't be
  > activated" isn't enforced against permanents that become artifacts
  > after Karn enters (e.g. a land turned into an artifact creature by
  > Liquimetal Coating). Verify Oracle text against Scryfall first. Trace
  > how other "can't activate abilities" static restrictions are checked
  > at activation time (this is a general activation-legality-check
  > pattern, not Karn-specific — CR 602.5 governs activated ability
  > legality checks, verify the number against
  > `docs/MagicCompRules.txt`) and make sure the check re-evaluates
  > current characteristics rather than caching type at ETB. Use
  > `/add-static-ability`.

### [bug-fix] Cityscape Leveler's Powerstone token is delayed and goes to the wrong controller (GitHub #1079)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1079](https://github.com/phase-rs/phase/issues/1079);
  sideboard/maindeck payoff in Vintage Karn Shops — no open PR.
- **Verified Oracle text:** "When you cast this spell and whenever this
  creature attacks, destroy up to one target nonland permanent. Its
  controller creates a tapped Powerstone token." Trample, Unearth {8}.
  ({8})
- **Reported bug:** the Powerstone token isn't created immediately when
  the ability resolves (sometimes appears only after a later
  trigger/cast), and it's always created under the Leveler's controller
  instead of the destroyed permanent's controller.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Cityscape Leveler (GitHub phase-rs/phase#1079): the Powerstone
  > token from "Its controller creates a tapped Powerstone token" must be
  > created as part of the same resolution as the destroy effect, under
  > the *destroyed permanent's controller* — not the Leveler's controller,
  > and not deferred to a later trigger. Verify Oracle text against
  > Scryfall first. Trace how other "destroy target permanent, its
  > controller creates X" effects resolve controller references (this is
  > a general `ControllerRef` composition pattern per CLAUDE.md, not
  > Leveler-specific) before writing new resolution logic.

### [bug-fix] Expressive Iteration sends cards to the wrong zones (GitHub #1271)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1271](https://github.com/phase-rs/phase/issues/1271);
  played in Vintage Izzet fast-mana shells — no open PR.
- **Verified Oracle text:** "Look at the top three cards of your library.
  Put one of them into your hand, put one of them on the bottom of your
  library, and exile one of them. You may play the exiled card this
  turn." ({U}{R})
- **Reported bug:** after choosing the hand card, the engine sends the
  chosen exile-card to the graveyard (unplayable) and sends the real
  bottom-of-library card to exile instead — the zone assignments for the
  other two cards are swapped/wrong.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Expressive Iteration (GitHub phase-rs/phase#1271): of the two
  > non-hand cards from "look at the top three," one must go to the
  > bottom of the library and the other to exile (playable this turn) —
  > currently the exile-destined card is going to the graveyard and the
  > bottom-library card is going to exile instead. Verify Oracle text
  > against Scryfall first. This is the same "look at N, distribute to
  > different zones" shape as other impulse-draw-plus-card-advantage
  > effects — trace how zone assignment is wired for the modal choice
  > before fixing, since a swapped zone-target bug like this may also
  > affect other multi-destination reveal effects sharing the same
  > resolver path.

### [bug-fix] Relic of Progenitus targeting and second mode are both broken (GitHub #1077)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1077](https://github.com/phase-rs/phase/issues/1077);
  standard Vintage sideboard graveyard hate against Dredge (a current
  top-3 Vintage archetype) — no open PR.
- **Verified Oracle text:** "{T}: Target player exiles a card from their
  graveyard. {1}, Exile this artifact: Exile all graveyards. Draw a
  card." ({1})
- **Reported bug:** activating the first ability prompts for a target
  player but then shows the *activator's own* graveyard regardless of who
  was targeted, plus asks for a card selection even though the ability
  itself doesn't target a card. The second ability (exile all graveyards
  + draw) doesn't trigger/work at all — only the first ability seems to
  fire.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Relic of Progenitus (GitHub phase-rs/phase#1077): (1) the first
  > ability's target player isn't respected — it shows the activator's
  > own graveyard instead of the targeted player's, and the exiled card
  > should be chosen by the *targeted player*, not the activator; (2) the
  > second ability (sacrifice-cost "exile all graveyards, draw a card")
  > isn't available/doesn't resolve at all — this card has two
  > independent activated abilities, not one. Verify Oracle text against
  > Scryfall first. Trace how other two-activated-ability artifacts expose
  > both abilities as separate choices before fixing.

### [bug-fix] Endurance's ETB fizzles if killed in response (GitHub #1059)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#1059](https://github.com/phase-rs/phase/issues/1059);
  free pitch-elemental graveyard hate/blocker played across Legacy/Vintage
  — no open PR.
- **Verified Oracle text:** "Flash, Reach. When this creature enters, up
  to one target player puts all the cards from their graveyard on the
  bottom of their library in a random order. Evoke — Exile a green card
  from your hand." ({1}{G}{G})
- **Reported bug:** if Endurance is killed in response to its own ETB
  trigger, the trigger fizzles instead of resolving.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Endurance (GitHub phase-rs/phase#1059): its ETB trigger ("up to
  > one target player puts all cards from their graveyard on the bottom
  > of their library") must still resolve even if Endurance is removed in
  > response to the trigger — per CR 603.3d/603.6b, a triggered ability
  > exists independently on the stack once it triggers and doesn't fizzle
  > just because its source left the battlefield (verify the exact CR
  > numbers against `docs/MagicCompRules.txt` before citing). This is a
  > general "leaves-battlefield-after-trigger" correctness class, not
  > Endurance-specific — check whether other ETB triggers share the same
  > bug via whatever resolves triggered abilities independent of source
  > continued existence.

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

### [bug-fix] Mother of Runes doesn't let you choose the protection color (GitHub #624)

- **Status:** open
- **Source:** GitHub issue [phase-rs/phase#624](https://github.com/phase-rs/phase/issues/624);
  Middle-School/Premodern-era (Urza's Legacy) white-aggro staple, still a
  played 1-drop across Legacy/Premodern/Canadian-Highlander today — no
  open PR.
- **Verified Oracle text:** "{T}: Target creature you control gains
  protection from the color of your choice until end of turn." ({W})
- **Reported bug:** the granted protection isn't tied to an actual player
  choice — engine behaves as if it grants protection from a fixed/random
  color rather than prompting the controller to pick one.
- **Before implementing:** re-confirm still reproduces on current `main`.
- **Prompt:**
  > Fix Mother of Runes (GitHub phase-rs/phase#624): "protection from the
  > color of your choice" requires a color-choice prompt to the ability's
  > controller at activation, then grants protection from that specific
  > chosen color — not a fixed or random color. Verify Oracle text against
  > Scryfall first. This is a general "choose a color" cost/effect
  > parameter shared by many cards (e.g. other protection-granting
  > effects, color-choice CDAs) — trace how color choice is modeled
  > elsewhere in the engine before adding a new mechanism. Use
  > `/add-interactive-effect` for the choice round-trip.

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

---

## Done

_(none yet)_
