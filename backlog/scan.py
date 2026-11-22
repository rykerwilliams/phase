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

# Card names that are also ordinary English ("Balance", "Terror", "Shock").
# Applied to POOL lines only, and only on the prose-scanning fallback in `find()`;
# an explicitly named card always matches, and a report that states its own card
# list bypasses this entirely.
#
# This list used to carry a second job — blocking names that are substrings of
# MODERN card names ("Reclamation" inside "Sylvan Reclamation"). That job is now
# done structurally by `declared_names` + `_only_inside_longer_name`, because a
# hand-maintained blocklist can never be complete: every new set prints names
# that contain an old card's name, so the list silently decays into false
# attributions. Do not add substring cases here; they belong to the structural test.
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
        # Strip a trailing comment before stripping whitespace. Only a `#` that
        # follows whitespace starts one, so a name or query containing `#` is
        # left alone. Without this an annotated entry ("Void Mirror  # see
        # issue #8807") is sent to Scryfall verbatim and 404s, which reads as
        # a misspelled card rather than a comment the format didn't support.
        line = re.split(r"\s#", line, maxsplit=1)[0].strip()
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


def scryfall_all_names():
    """Every card name Scryfall knows, in one request (`/catalog/card-names`).

    Needed to tell a watched old card from a modern card whose name contains it.
    That judgment cannot be made from the watched pool alone: the pool has
    `Reclamation` and nothing else, so `Sylvan Reclamation` is invisible to it.
    """
    key = CACHE / "catalog_card_names.json"
    if OFFLINE and key.exists():
        return json.loads(key.read_text())
    try:
        names = _get("https://api.scryfall.com/catalog/card-names")["data"]
    except Exception as e:
        print(f"  ! card-name catalog unavailable: {e}", file=sys.stderr)
        return json.loads(key.read_text()) if key.exists() else []
    key.write_text(json.dumps(names))
    time.sleep(SLEEP)
    return names


def fetch_issues():
    key = CACHE / "issues.json"
    if OFFLINE and key.exists():
        return json.loads(key.read_text())
    raw = sh("gh", "issue", "list", "--repo", "phase-rs/phase", "--state", "open",
             "--limit", "2000", "--json", "number,title,body,labels,createdAt")
    key.write_text(raw)
    return json.loads(raw)


BRACKET = re.compile(r"\[\[([^\]]{2,60})\]\]")
CARDS_LINE = re.compile(r"^\*\*Cards:\*\*[ \t]*(.+?)[ \t]*$", re.M)
NOT_A_NAME = {"none detected", "none", "n/a", "-", "--"}
WORD = re.compile(r"[a-z0-9']+")


def _norm(s):
    """Fold a name to the `by_lower` key shape: lowercase, single-spaced, unpunctuated ends."""
    return " ".join(s.lower().replace("’", "'").split()).strip(" .,;:*_")


def _words(s):
    """A name as bare alphanumeric words, so punctuation never decides a match.

    Reports spell the same card "Nicol Bolas, Dragon-God", "Nicol Bolas, Dragon God"
    and "nicol bolas dragon god"; all three must compare equal to the catalog entry.
    """
    return WORD.findall(s.lower().replace("’", "'"))


def _seq_re(words):
    """Match a word sequence across any punctuation that separates its words."""
    return re.compile(r"(?<![A-Za-z0-9'’])"
                      + r"[^A-Za-z0-9]{1,4}".join(map(re.escape, words))
                      + r"(?![A-Za-z0-9'’])", re.I)


def declared_names(text):
    """The card names a report states for itself, as normalized strings.

    Discord-synced reports carry `[[Card Name]]` markup and a generated
    `**Cards:**` line, so for those the card set is *stated* rather than inferred
    from prose. Preferring it is what keeps "Sylvan Reclamation" from being
    attributed to Ice Age's "Reclamation" (issue #6862 was in the LIVE table on
    exactly that match). Returns an empty set for a hand-written issue, which is
    the signal to fall back to prose scanning.
    """
    out = set()
    for raw in BRACKET.findall(text):
        if n := _norm(raw):
            out.add(n)
    for line in CARDS_LINE.findall(text):
        for part in line.split(","):
            if (n := _norm(part)) and n not in NOT_A_NAME:
                out.add(n)
    return out


def _is_subphrase(name, others):
    """True when `name` sits as a whole-word run inside a longer declared name.

    The sync's own extraction splits multi-word names on their internal comma
    ("nicol bolas, dragon god" -> "nicol bolas" + "dragon-god"), so the short
    fragment can be declared alongside the full name. The full name wins.
    """
    return any(o != name and re.search(rf"(?<![a-z0-9']){re.escape(name)}(?![a-z0-9'])", o)
               for o in others)


def evidence_text(text):
    """The report minus its own generated restatement of the card list.

    `**Cards:** nicol bolas` is derived from the report, not evidence about it,
    and it always states the name in isolation — which is how #4784 ("Nicol
    Bolas, Planeswalker") kept being attributed to the 1995 Nicol Bolas.
    """
    return re.sub(r"<!--.*?-->", "", CARDS_LINE.sub("", text), flags=re.S)


def shadow_index(all_names, watched):
    """watched name -> real card names that strictly contain it as a word run.

    This is the structural replacement for blocklisting substrings by hand. The
    question "is `Reclamation` here really the 1995 card?" is decided by whether
    a longer card that contains it — `Sylvan Reclamation` — is named in the same
    report, which needs the FULL card universe, not just the watched pool.
    """
    idx = {}
    for full in all_names:
        w = _words(full)
        for i in range(len(w)):
            for j in range(i + 1, len(w) + 1):
                if (i, j) == (0, len(w)):
                    continue                            # the name itself, not a container
                if (sub := " ".join(w[i:j])) in watched:
                    idx.setdefault(sub, set()).add(" ".join(w))
    return idx


def _shadowed(text, name, idx):
    """True when a longer card containing `name` is named in the same report.

    Whole-report rather than per-occurrence: a reporter who writes "Nicol Bolas,
    Planeswalker" once and "Nicol Bolas Ult" after it means the modern card both
    times, so one shorthand mention must not resurrect the old card.
    """
    low = text.lower()
    for longer in idx.get(" ".join(_words(name)), ()):
        w = longer.split()
        if all(t in low for t in w) and _seq_re(w).search(text):
            return True
    return False


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

    catalog = scryfall_all_names()
    shadows = shadow_index(catalog, {" ".join(_words(n)) for n in cards})
    print(f"card-name catalog: {len(catalog)} names; {len(shadows)} watched names are "
          f"contained in a longer card", file=sys.stderr)
    if not catalog:
        sys.exit("ABORT: no card-name catalog, so a watched name cannot be told apart "
                 "from a longer modern card containing it (the 'Reclamation' inside "
                 "'Sylvan Reclamation' class). BACKLOG-CARDS.md left UNTOUCHED.\n"
                 "Re-run with network, or --offline once the catalog has been cached.")

    def find(text):
        # Candidates come from the report's own card list AND from an n-gram sweep
        # of its prose. Neither alone is trustworthy: the sweep matches any watched
        # name sitting inside a longer modern one, and the generated `**Cards:**`
        # line is LLM-extracted, so it both truncates names ("nicol bolas" for
        # Nicol Bolas, Planeswalker) and omits the card the issue is titled after
        # (#6770 Manabond, #8453 Syncopate were declared as neither).
        decl = declared_names(text)
        out = {by_lower[d] for d in decl if d in by_lower}
        low = [t.lower().strip(".,") for t in tok.findall(text)]
        for i in range(len(low)):
            for n in range(1, min(maxw, len(low) - i) + 1):
                r = by_lower.get(" ".join(low[i:i + n]))
                if r and (r in forced or (len(r) >= 8 and r not in STOP)):
                    out.add(r)
        # Two structural rejections, replacing what the stoplist could not bound.
        ev = evidence_text(text)
        return {r for r in out
                if r in forced
                or not (_is_subphrase(r.lower(), decl) or _shadowed(ev, r, shadows))}

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


def selftest():
    """Pin the attribution rules against the report shapes that actually broke.

    Each case is a real issue reduced to the fragment that decided its verdict,
    so a future change to the matcher has to keep answering these the same way.
    Synthetic catalog, no network: this tests the predicates, not the pipeline.
    """
    catalog = ["Reclamation", "Sylvan Reclamation", "Extortion", "Temporal Extortion",
               "Nicol Bolas", "Nicol Bolas, Planeswalker", "Nicol Bolas, Dragon-God",
               "Instigator", "Firkraag, Cunning Instigator", "Thought Lash",
               "Blood Oath", "Hellhole Rats", "Manabond", "Final Fortune",
               "Peacekeeper", "Anointed Peacekeeper"]
    watched = {"reclamation", "extortion", "nicol bolas", "instigator", "thought lash",
               "blood oath", "manabond", "final fortune", "peacekeeper"}
    idx = shadow_index(catalog, watched)
    # (label, report text, watched name, expected: True = reject the attribution)
    cases = [
        ("#6862 modern card contains an old name",
         "AI just exiled [[Sylvan Reclamation]] with [[Espers to Magicite]].",
         "Reclamation", True),
        ("#8115 old name is a suffix of the real card",
         "Temporal Extortion doesn't grant an extra turn even when uncountered",
         "Extortion", True),
        ("#4784 shorthand later in the same report",
         "Nicol Bolas, Planeswalker — I used Nicol Bolas Ult on the AI bot",
         "Nicol Bolas", True),
        ("#4732 old name is a suffix, mid-name comma",
         "Firkraag, Cunning Instigator is taking counters illegally",
         "Instigator", True),
        ("#7157 old name inside an unrelated modern card",
         "Emperor of Bones ability on Anointed Peacekeeper",
         "Peacekeeper", True),
        ("#10233 comma-separated LIST is not a longer name",
         "unverified: Blood Oath, Hellhole Rats, Ihsan's Shade",
         "Blood Oath", False),
        ("#782 bare mention, nothing longer present",
         "Thought Lash — The activated ability can be activated without paying",
         "Thought Lash", False),
        ("#6770 titled after the old card",
         "Manabond card not working correctly — it triggers at the end of the turn",
         "Manabond", False),
        ("#4231 bracketed old card",
         "Fake Fortune — [[Final Fortune]] - when played, upon the end step",
         "Final Fortune", False),
    ]
    bad = 0
    for label, text, name, want in cases:
        got = _shadowed(evidence_text(text), name, idx)
        if got != want:
            bad += 1
            print(f"FAIL {label}: _shadowed({name!r}) = {got}, want {want}")
        else:
            print(f"ok   {label}")

    # The `**Cards:**` line is derived, not evidence: left in, it supplies a bare
    # mention that defeats the shadow test (this is exactly how #4784 survived).
    cards_line = ("Nicol Bolas, Planeswalker — broken\n**Cards:** nicol bolas\n")
    if not _shadowed(evidence_text(cards_line), "Nicol Bolas", idx):
        bad += 1
        print("FAIL **Cards:** line not stripped from evidence")
    else:
        print("ok   **Cards:** line excluded from evidence")

    # A truncated declared name loses to the full one declared beside it (#6395),
    # which is the guard for mid-name commas the catalog spelling won't match.
    d = declared_names("**Cards:** nicol bolas, dragon-god\n[[nicol bolas dragon god]]")
    if not _is_subphrase("nicol bolas", d):
        bad += 1
        print(f"FAIL truncated declared name not caught; declared={sorted(d)}")
    else:
        print("ok   truncated declared name loses to the full one")

    print(f"\n{'FAILED' if bad else 'PASS'}: {len(cases) + 2 - bad}/{len(cases) + 2} checks")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
