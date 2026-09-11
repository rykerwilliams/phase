---
name: backlog-add
description: Add cards or a whole format/set pool to the local card backlog watchlist, then rescan open issues and report what it found. Use when the user says "add <card> to the backlog", "track <format>", "watch these cards", "I care about vintage/legacy/premodern", or invokes /backlog-add with card names or a Scryfall query.
---

# backlog-add — put cards on the watchlist and rescan

The backlog is generated from `backlog/watchlist.txt`. This skill edits that file and regenerates
`BACKLOG-CARDS.md`, so the user never hand-edits either.

`$ARGUMENTS` — card names (comma or newline separated), and/or a Scryfall query, and/or a format
name. Empty → show the current watchlist and ask what to add.

## Steps

1. **Classify each argument.**
   - Looks like a Scryfall query (`f:`, `set:`, `year`, `banned:`, `is:`, `t:`) → pool line, `q: <query>`.
   - A format name ("vintage", "premodern", "old school") → translate to a query, but see the
     breadth warning below before writing it.
   - Anything else → an exact card name.

2. **Verify every card name against Scryfall before writing it.** A misspelled name silently never
   matches and the user will think the card is clean.
   ```bash
   curl -s "https://api.scryfall.com/cards/named?exact=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "Card Name")" | head -c 200
   ```
   Use the canonical `name` Scryfall returns, not the user's spelling. If it 404s, try `?fuzzy=`
   and confirm the match with the user rather than guessing.

3. **Warn on breadth before adding a wide pool.** `f:vintage` is ~25k cards — nearly everything ever
   printed — so it matches almost every issue and produces a backlog that is noise. Say so and offer
   the high-signal slices instead:
   `banned:vintage`, `restricted:vintage`, `is:reserved`, `f:premodern`, `year<=2003`,
   `set:lea or set:leb or set:2ed`.
   Add the broad pool anyway if the user still wants it — it is their call, just not a silent one.

4. **Append to `backlog/watchlist.txt`** under the right section (`# ---- pools ----` or
   `# ---- named cards ----`). Never remove existing lines. Skip duplicates.

5. **Regenerate and report the delta:**
   ```bash
   python3 backlog/scan.py
   ```
   The scanner aborts rather than overwriting a good backlog if the watchlist resolves to zero cards
   (Scryfall rate-limits on bursts). If it aborts, wait a minute and re-run; `--offline` reuses the
   cache. Report: how many cards the watchlist now resolves to, and the new LIVE / partial /
   CHECK-DIRECTION counts, plus any issues newly surfaced for the cards just added (they are
   marked ★).

6. **Commit** `backlog/watchlist.txt` and `BACKLOG-CARDS.md` to the fork's `main`, then say whether
   anything is worth working now — and that `/backlog-batch` will pick it up.

## Notes

- An explicitly named card **always** matches, bypassing the ~200-entry stoplist that filters pool
  lines. If the user names a card that is also ordinary English (`Balance`, `Shock`, `Fear`), tell
  them it will produce false positives — then honour the request.
- Everything here is fork-only; it never reaches a PR to `phase-rs/phase`.
