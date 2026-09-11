#!/usr/bin/env python3
"""Regenerate BACKLOG-CARDS.md from backlog/watchlist.txt.

Fork-only tooling. Scans every OPEN phase-rs/phase issue for cards on the watchlist,
then classifies each hit by whether it looks already-fixed on upstream/main.

    python3 backlog/scan.py            # full run
    python3 backlog/scan.py --offline  # reuse cached issues + card pools
"""
import json, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "backlog" / ".cache"
CACHE.mkdir(exist_ok=True)
OFFLINE = "--offline" in sys.argv
UA = {"User-Agent": "phase-backlog/1.0", "Accept": "application/json"}

# Card names that are also ordinary English or substrings of modern card names.
# Applied to POOL lines only; an explicitly named card always matches.
STOP = set("""Sacrifice Nightmare Darkness Conversion Simulacrum Inquisition Necropolis Shapeshifter
Sentinel Seeker Terror Blight Cleansing Regeneration Righteousness Camouflage Deathgrip Blessing
Crusade Meekstone Cyclone Earthquake Firebreathing Resurrection Hurricane Tunnel Pestilence Balance
Fear Fog Web Blaze Flight Karma Twiddle Shatter Ambition Anarchy Archangel Assassinate Aura Barter
Betrayal Boomerang Browse Choke Clone Confusion Conquer Contagion Corrupt Cremate Crypt Dominate
Duress Enrage Envy Erosion Evacuation Exhaustion Extinction Fatigue Fecundity Flourish Foresight
Forget Frenzy Fugue Gamble Greed Grief Harrow Hush Impatience Impulse Insight Intuition Invasion
Kismet Lull Manipulate Meditate Mudslide Nausea Obliterate Opposition Ostracize Overrun Pandemonium
Panic Paralyze Perish Persecute Pillage Portent Predict Prosperity Provoke Pulse Purify Quash
Rampage Ransack Recall Reclaim Regress Reincarnation Rejuvenate Relearn Remedy Remove Repentance
Reprisal Restock Retaliation Retribution Revive Ruination Sabotage Sandstorm Savior Scald Scavenge
Scorch Screech Seizures Serenity Shackles Shock Sift Silence Smite Smother Snap Solidarity Spellbook
Spike Spite Splinter Squall Stasis Stupor Submerge Subversion Suffocation Sunburst Suppress Surge
Symbiosis Tempest Threaten Torment Torture Tranquility Transmute Tremor Turnabout Twitch Unnerve
Uproot Vengeance Verdigris Vertigo Vigilante Vitalize Wanderlust Warmth Weakness Whiteout Wildfire
Windfall Trickery Wish Vision Reset Volcano Miracle Plague Dread Rage Static Prophecy Legacy Mirage
Onslaught Judgment Odyssey Nemesis Exodus Stronghold Weatherlight Visions Homelands Alliances
Chronicles Legends Antiquities Bribery Reanimate Duplicity Ascension Awakening Bereavement""".split())


SLEEP = 0.25          # 4 req/s. Scryfall's ceiling is 10/s and they warn that
                      # ignoring it earns a NETWORK BLOCK, so stay well under.

def _get(url, tries=4):
    """One Scryfall GET, honouring their rate limit.

    On 429 Scryfall's own message says "try again after 60 seconds", so wait that
    long rather than a token backoff — a tight retry is what earns a block. Raises
    rather than returning partial data; callers must not paper over a short pool."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                wait = int(e.headers.get("Retry-After") or 60)
                print(f"    rate-limited; waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("unreachable")


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, cwd=ROOT).stdout


def read_watchlist():
    pools, names = [], []
    for line in (ROOT / "backlog" / "watchlist.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        (pools if line.startswith("q:") else names).append(
            line[2:].strip() if line.startswith("q:") else line)
    return pools, names


TRUNCATED = []


def scryfall_pool(q):
    key = CACHE / ("pool_" + re.sub(r"\W+", "_", q)[:60] + ".json")
    if OFFLINE and key.exists():
        return json.loads(key.read_text())
    out, url = {}, "https://api.scryfall.com/cards/search?" + urllib.parse.urlencode(
        {"q": q, "unique": "cards", "order": "name"})
    expected, records = None, 0
    while url:
        try:
            d = _get(url)
        except Exception as e:
            print(f"  ! pool {q!r} TRUNCATED at {len(out)} cards: {e}", file=sys.stderr)
            break
        expected = expected or d.get("total_cards")
        for c in d["data"]:
            records += 1
            out.setdefault(c["name"], c.get("released_at", "")[:4])
        url = d.get("next_page")
        time.sleep(SLEEP)
    # Compare RECORDS FETCHED against the API's total, not the deduped dict size.
    # The pool is keyed by card name, so two distinct cards sharing a name collapse
    # to one entry — legitimate, and not truncation. Comparing dict size flagged a
    # complete 6595-record pool as short by one and refused to write.
    if expected and records < expected:
        TRUNCATED.append(f"{q!r}: fetched {records} of {expected} records")
    elif expected and len(out) < records:
        print(f"  ({records - len(out)} duplicate name(s) collapsed)", file=sys.stderr)
    key.write_text(json.dumps(out))
    return out


def scryfall_named(name):
    key = CACHE / ("name_" + re.sub(r"\W+", "_", name)[:60] + ".json")
    if OFFLINE and key.exists():
        return json.loads(key.read_text())
    u = "https://api.scryfall.com/cards/named?" + urllib.parse.urlencode({"exact": name})
    try:
        d = _get(u)
        res = {d["name"]: d.get("released_at", "")[:4]}
    except Exception as e:
        print(f"  ! named {name!r} not resolved: {e}", file=sys.stderr)
        res = {}
    key.write_text(json.dumps(res))
    time.sleep(SLEEP)
    return res


def fetch_issues():
    key = CACHE / "issues.json"
    if OFFLINE and key.exists():
        return json.loads(key.read_text())
    raw = sh("gh", "issue", "list", "--repo", "phase-rs/phase", "--state", "open",
             "--limit", "2000", "--json", "number,title,body,labels,createdAt")
    key.write_text(raw)
    return json.loads(raw)


def main():
    pools, named = read_watchlist()
    cards, forced = {}, set()
    for q in pools:
        got = scryfall_pool(q)
        print(f"  pool {q!r}: {len(got)} cards", file=sys.stderr)
        cards.update(got)
    for n in named:
        got = scryfall_named(n)
        cards.update(got)
        forced.update(got)          # explicit names bypass the stoplist
    print(f"watchlist resolves to {len(cards)} cards ({len(forced)} explicitly named)", file=sys.stderr)
    # Refuse to overwrite a good backlog with a degraded one. A rate-limited or
    # truncated pool yields few/no cards, and silently writing that empty result
    # would look like "the backlog is clear" instead of "the scan failed".
    if not cards or TRUNCATED:
        why = "; ".join(TRUNCATED) or "watchlist resolved to 0 cards"
        sys.exit(f"ABORT: incomplete card pool ({why}). BACKLOG-CARDS.md left UNTOUCHED.\n"
                 "A truncated pool silently drops candidates and the shorter backlog looks "
                 "like real progress, so this refuses to write rather than mislead.\n"
                 "Wait 60s and re-run, or use --offline to reuse the cache.")

    issues = fetch_issues()
    by_lower = {n.lower(): n for n in cards}
    maxw = max((len(n.split()) for n in cards), default=1)
    tok = re.compile(r"[A-Za-z0-9'’,\.\-]+")

    def find(text):
        out = set()
        for m in re.findall(r"\[\[([^\]]{2,60})\]\]", text):
            r = by_lower.get(m.strip().lower())
            if r:
                out.add(r)
        low = [t.lower().strip(".,") for t in tok.findall(text)]
        for i in range(len(low)):
            for n in range(1, min(maxw, len(low) - i) + 1):
                r = by_lower.get(" ".join(low[i:i + n]))
                if r and (r in forced or (len(r) >= 8 and r not in STOP)):
                    out.add(r)
        return out

    # staleness signals, batched
    claimed = set(re.findall(r"#(\d{3,5})", sh("git", "log", "upstream/main", "--format=%s%n%b")))
    testrefs = set(re.findall(r"(\d{3,5})", sh("git", "grep", "-h", "-oE", r"issue #?[0-9]{3,5}",
                                               "upstream/main", "--", "crates/engine/tests", "crates/engine/src")))
    testnames = set(l.strip('"') for l in sh("git", "grep", "-h", "-oE",
                    r'"[A-Z][A-Za-z0-9 ,\x27.:-]{4,45}"', "upstream/main", "--",
                    "crates/engine/tests").splitlines())

    hits = {}
    for it in issues:
        found = find(it["title"] + "\n" + (it.get("body") or ""))
        if not found:
            continue
        num = str(it["number"])
        labels = [l["name"] for l in it["labels"]]
        covered = sorted(found & testnames)
        sig = []
        if num in claimed:
            sig.append("commit-mentions-issue")
        if num in testrefs:
            sig.append("test-references-issue")
        if covered:
            sig.append(f"card-in-tests({len(covered)})")
        verdict = ("CHECK-DIRECTION" if ("commit-mentions-issue" in sig or "test-references-issue" in sig)
                   else "partial-coverage" if covered else "LIVE")
        hits[num] = dict(title=it["title"], labels=labels, cards=sorted(found),
                         in_title=sorted(n for n in found if n.lower() in it["title"].lower()),
                         years={n: cards[n] for n in found}, signals=sig, verdict=verdict,
                         watched=sorted(found & forced))

    def rank(kv):
        h = kv[1]
        l = " ".join(h["labels"])
        p = next((i for i, t in enumerate(["p0-softlock", "p1-core-mechanic", "p2-wrong-game-result",
                                           "p3-card-specific", "p4-ui-polish"]) if t in l), 9)
        return (0 if h["watched"] else 1, 0 if h["in_title"] else 1, p,
                0 if "status:confirmed" in l else 1)

    sha = sh("git", "rev-parse", "--short", "upstream/main").strip()
    groups = {k: sorted([kv for kv in hits.items() if kv[1]["verdict"] == k], key=rank)
              for k in ("LIVE", "partial-coverage", "CHECK-DIRECTION")}

    o = []
    o.append("# Card backlog — generated from `backlog/watchlist.txt`\n")
    o.append("> **Working this? Read [`OLD-CARD-RUNBOOK.md`](OLD-CARD-RUNBOOK.md) first**, or just run `/backlog-batch`.\n")
    o.append(f"_Generated {datetime.date.today()} against `upstream/main` `{sha}` · "
             f"{len(issues)} open issues · watchlist resolves to {len(cards)} cards_\n")
    o.append("**Do not hand-edit** — regenerate with `python3 backlog/scan.py`. "
             "To change what is tracked, edit `backlog/watchlist.txt`.\n")
    o.append("| verdict | count | meaning |\n|---|---:|---|")
    o.append(f"| **LIVE** | {len(groups['LIVE'])} | No signal that it is fixed. Best candidates. |")
    o.append(f"| partial-coverage | {len(groups['partial-coverage'])} | Card appears in some test; nothing ties a fix to THIS issue. |")
    o.append(f"| CHECK-DIRECTION | {len(groups['CHECK-DIRECTION'])} | A commit/test cites the issue — but a commit can cite an issue to **fix**, **defer**, be **blocked on**, or **file** it. Only the first means fixed. Run the direction check before believing this bucket. |")
    o.append("\n```bash\ngit log -1 --format='%b' <sha> | grep -B2 -A3 '#<N>\\b'   # the direction check\n```\n")
    o.append("★ = a card you explicitly named in the watchlist.\n")

    hdr = "| issue | card(s) | title | labels |\n|---|---|---|---|"
    for key, title in (("LIVE", "LIVE — best candidates"),
                       ("partial-coverage", "Partial coverage — verify what the test asserts"),
                       ("CHECK-DIRECTION", "Cites an issue — run the direction check")):
        o.append(f"\n## {title} ({len(groups[key])})\n")
        o.append(hdr)
        for num, h in groups[key]:
            star = "★ " if h["watched"] else ""
            cs = ", ".join(f"{c} ({h['years'].get(c,'?')})" for c in (h["in_title"] or h["cards"])[:3])
            if len(h["cards"]) > 3:
                cs += f" +{len(h['cards'])-3}"
            t = h["title"].replace("|", "\\|")
            t = t[:92] + "..." if len(t) > 95 else t
            labs = [l for l in h["labels"] if l.startswith(("priority:", "status:", "area:"))][:3]
            o.append(f"| {star}[#{num}](https://github.com/phase-rs/phase/issues/{num}) | {cs} | {t} | {', '.join(labs) or '—'} |")

    (ROOT / "BACKLOG-CARDS.md").write_text("\n".join(o) + "\n")
    print(f"BACKLOG-CARDS.md: LIVE={len(groups['LIVE'])} "
          f"partial={len(groups['partial-coverage'])} check-direction={len(groups['CHECK-DIRECTION'])}")


if __name__ == "__main__":
    main()
