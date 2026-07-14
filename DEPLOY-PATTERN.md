# One host, one proxy, two pipelines

A minimal, no-orchestrator deploy pattern: nginx terminates TLS and routes
traffic on a single EC2 box; GitHub Actions pushes builds to it over SSH.
Written up after extracting it from phase.rs's actual deploy setup so it can
be reapplied elsewhere without re-deriving it each time.

**Scope:** one host, 1–5 low-traffic services. **Orchestration:** none — cron
+ SSH. No ECS, no load balancer, no CD tool. **Source:** phase.rs / teamserio.us.

---

## When this pattern fits

This is the deploy shape for a project too small to justify ECS, a load
balancer, or a CD tool: **one EC2 host already running nginx for other
sites**, onto which you add one more server block, one more static directory,
and — if there's a backend — one more Docker container bound to localhost.
Each project's GitHub repo owns its own workflow and its own scoped SSH
credential; the host itself has no project-specific config beyond what's
edited directly over SSH.

It does not fit once you need zero-downtime rolling deploys, more than one
host, or a backend that can't tolerate a few seconds of restart — the pattern
below stops the container, pulls the new image, and starts it again.

## Architecture

```
GitHub Actions (per repo, own workflow + secrets)
        │
        │  SSH / SCP
        ▼
Single EC2 host
  nginx :80/:443  (TLS via certbot)
    ├─ /var/www/site-a         (static)
    ├─ /var/www/site-b         (static)
    ├─ proxy_pass 127.0.0.1:9001   (app A)
    └─ proxy_pass 127.0.0.1:9002   (app B, /ws upgrade)
```

nginx is the only thing with inbound ports open. Every app container binds to
`127.0.0.1` only — it is unreachable except through the proxy.

## 1. Audit the host before touching it

Do this **read-only**, before writing a single line of workflow YAML. It's a
short SSH session, and it determines almost every detail below — don't assume
any of it from a different host you've used before.

- [ ] **TLS mechanism** — `which certbot`, check `systemctl list-timers` and
      `/etc/letsencrypt/`. Confirm TLS terminates at nginx itself, not at an
      AWS-layer ALB/CloudFront — that changes where the cert gets issued.
- [ ] **nginx config layout** — one `nginx.conf`, or `sites-available`/
      `sites-enabled`? Pull an existing server block as the literal template.
- [ ] **OS and package manager** — `/etc/os-release`. Determines how you'd
      install anything missing.
- [ ] **Docker already present?** — `docker --version`, `docker ps`. If your
      app has no backend, skip this and the container step entirely.
- [ ] **DNS management** — Route 53, registrar, Cloudflare? Often checkable
      without host SSH at all.
- [ ] **Headroom** — `free -h`, `df -h`, `nproc`. Confirm room for one more
      container plus a static directory alongside whatever's already there.
- [ ] **Firewall / security group** — confirm only 80/443 are open, and that
      a container on `127.0.0.1` needs no new inbound rule.

## 2. Secrets are per-repo, not shared

If the host already serves another project, its deploy secrets live on *that
project's* repo only — they will not be visible to a new one. Add your own
copies, and consider a dedicated SSH key scoped to just this app's deploy
path rather than reusing an existing one, so a compromise of one pipeline
doesn't hand over the others.

| Name | Kind | Holds |
|---|---|---|
| `DEPLOY_HOST` | secret | Hostname or IP of the box. |
| `DEPLOY_SSH_KEY` | secret | Private key for a deploy-only user — not your personal key. |
| `DEPLOY_PORT` | variable | SSH port, if not 22 (many hosts move it to cut bot noise). |
| `DEPLOY_USER` | variable | The deploy account name (e.g. `deploy`), not root. |
| an app-level secret | secret | Whatever credential your running service needs at boot — name it for your app. |

## 3. Backend: schedule-checked container deploy

The shape: resolve a version, SSH in, stop the old container, run the new one
with a restart policy, then poll a health endpoint before declaring success.
Running it on a **schedule** (not just manual dispatch) means new upstream
releases roll out on their own — the trigger below checks the
currently-running image first and skips the SSH round-trip entirely if
nothing changed.

```yaml
# .github/workflows/deploy-backend.yml
on:
  workflow_dispatch:
    inputs:
      version: { required: false, default: '' }
  schedule:
    - cron: '17 * * * *'   # hourly; offset the minute so you're not on the crowd's :00

jobs:
  deploy:
    steps:
      # resolve $VERSION from input, or GET the latest upstream release
      # write DEPLOY_SSH_KEY to ~/.ssh, ssh-keyscan the host into known_hosts
      # on schedule only: `docker inspect <container> --format '{{.Config.Image}}'`
      #   — if it already matches the target image, skip the rest and exit
      # over ssh:
      #   docker pull $IMAGE
      #   docker stop --time 30 <name> ; docker rm <name>
      #   docker run -d --name <name> --restart unless-stopped \
      #     -p 127.0.0.1:$PORT:$PORT -v <name>-data:/var/lib/<name> \
      #     -e ...  $IMAGE
      #   poll `curl -fsS http://127.0.0.1:$PORT/health` for ~30s before failing
```

Bind the published port to `127.0.0.1`, never `0.0.0.0` — nginx is the only
thing that should be able to reach it. The health-check loop is what turns a
silent bad deploy into a red CI run instead of a quietly-dead container.

## 4. Frontend: build, then wipe-and-replace

A static bundle deploy is simpler than the backend's — there's no process to
restart, just a directory to replace atomically enough that a mid-copy
request doesn't see a half-written tree. Piping a `tar` stream over SSH
avoids the extra round-trip of a separate SCP action and keeps permissions
intact.

```yaml
# .github/workflows/deploy-frontend.yml
on:
  workflow_dispatch:
    inputs:
      version: { required: false, default: '' }

jobs:
  build-and-deploy:
    steps:
      # checkout the version/tag to build, install toolchain + deps
      # build the static bundle (`pnpm build`, `npm run build`, etc.)
      # write DEPLOY_SSH_KEY, ssh-keyscan as above
      # ssh: rm -rf /var/www/<site>/* ; mkdir -p /var/www/<site>
      # tar -czf - -C dist/ . | ssh ... "tar -xzf - -C /var/www/<site>"
```

## 5. nginx: one server block per site

Config lives on the host, edited over SSH — there is usually nothing to put
in a repo here. Copy an existing working server block for the same host as
your literal starting point rather than writing one from scratch; the TLS
and redirect boilerplate is easy to get subtly wrong.

```nginx
server {
    listen 443 ssl;
    server_name app.example.com;

    ssl_certificate     /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;

    # static frontend
    root /var/www/app;
    location / { try_files $uri $uri/ /index.html; }

    # backend, with websocket upgrade if you need one
    location /ws {
        proxy_pass http://127.0.0.1:9001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /api/ {
        proxy_pass http://127.0.0.1:9001;
    }
}

server {
    listen 80;
    server_name app.example.com;
    return 301 https://$host$request_uri;
}
```

`nginx -t` before every reload, always — a syntax error in one site's block
can take down every other site on the same nginx instance.

## The lesson this doc exists because of

> **Version skew between independent pipelines.** Backend and frontend are
> separate workflows with separate triggers — it's tempting to give the
> backend a `schedule` so it tracks upstream automatically, and leave the
> frontend as manual-dispatch-only because it changes less often. That
> combination quietly ships a backend ahead of a frontend that doesn't speak
> its protocol yet, and nothing fails loudly when it happens — the two sides
> just start disagreeing.
>
> **Fix it before it fires, not after:** either put both deploys behind the
> *same* trigger (a single workflow, or two workflows chained via
> `workflow_run`), or keep the backend's `schedule:` trigger disabled entirely
> — `workflow_dispatch` only — until the frontend deploy is automated to
> match. A scheduled deploy for one half of a two-part system is a bug
> waiting on a clock.

## Reuse checklist for a new project

- [ ] Run the host audit (§1) even if you've deployed to this exact host
      before — package versions and disk headroom drift.
- [ ] Cut a scoped deploy user + SSH key for this project specifically.
- [ ] Pick ports for each backend service, bind them to `127.0.0.1` only, and
      record them somewhere that outlives your memory of this project.
- [ ] Write the nginx block from an existing one on the same host, then
      `nginx -t` before reloading.
- [ ] Issue the cert for the new subdomain using whatever ACME client the
      audit found.
- [ ] Decide the trigger shape up front — if there's more than one
      deployable part, make the coupling (see "the lesson" above) a conscious
      choice, not a default you back into.
- [ ] Add the health check to the backend workflow before the first real
      deploy, not after the first silent failure.

---

*Extracted from the phase.rs / teamserio.us deploy setup — generalized for
reuse elsewhere, not tied to either project's specifics.*
