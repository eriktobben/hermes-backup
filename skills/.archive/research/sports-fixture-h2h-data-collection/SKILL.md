---
name: sports-fixture-h2h-data-collection
description: Collect upcoming football fixtures and recent head-to-head results reliably when common stats sites block bots or time out.
---

# Sports fixture + H2H data collection

## When to use
- User asks for next match/opponent and recent H2H results.
- Typical football sites (SofaScore, Transfermarkt, Statbunker, etc.) are blocked (403) or JS-heavy.
- You need reproducible, scriptable extraction from public web data.

## Core workflow
1. **Find upcoming fixture first** (don’t start with H2H blind).
   - Use BBC team scores/fixtures page as seed:
     - `https://www.bbc.com/sport/football/teams/<team>/scores-fixtures`
2. **Extract machine data from BBC page**.
   - Parse `window.__INITIAL_DATA__` from page HTML.
   - This field is a JSON-*string*, so decode twice:
     - first `json.loads(...)` to unescape string
     - second `json.loads(...)` to parse object
3. **Identify API container key** inside `data` entries:
   - key prefix: `sport-data-scores-fixtures?...`
4. **Query BBC wc-data endpoint directly** for deterministic pulls:
   - `https://www.bbc.com/wc-data/container/sport-data-scores-fixtures`
   - Params: `selectedStartDate`, `selectedEndDate`, `todayDate`, `urn`
5. **Collect historical results in chunks**.
   - Use year-by-year windows (`YYYY-01-01` to `YYYY-12-31`).
   - Long multi-year ranges can return `400`.
6. **Parse events**:
   - Path: `eventGroups[] -> secondaryGroups[] -> events[]`
   - Competition label: `secondaryGroups[].displayLabel`
   - Date: `event.startDateTime`
   - Status: `event.status` (`PreEvent`, `PostEvent`)
   - Scores for completed matches: `home.runningScores.fulltime`, `away.runningScores.fulltime`
7. **Build H2H slice**.
   - Filter events where both target teams appear.
   - De-duplicate by `(date, home, away)`.
   - Sort desc by date and take last N completed matches.
   - Optionally split by competition (e.g., PL-only vs all comps).

## Bookmaker odds collection (Norsk Tipping-specific)
1. **Expect UI/API friction**:
   - `browser_navigate` may time out on sportsbook pages.
   - Site is JS-heavy with multiple script bundles and dynamic API calls.
2. **Useful reconnaissance endpoints**:
   - Front page scripts can reveal sportsbook shell:
     - `https://www.norsk-tipping.no/sport/oddsen/sportsbook/`
     - config files can expose API host hints (e.g. `environment.api.url`).
3. **Do not assume direct unauthenticated odds API access**:
   - Generic POSTs to discovered `/services` endpoints can return only generic errors.
   - Some sportsbook calls require app/session/device context that is hard to reproduce in raw requests.
4. **Fallback strategy when live odds cannot be fetched deterministically**:
   - Be explicit about limitation.
   - Ask user for current odds (or screenshot) and continue with value/edge calculations immediately.

## Pitfalls
- **403/anti-bot** is common on many football stats sites; don’t get stuck retrying one provider.
- BBC `window.__INITIAL_DATA__` is escaped JSON text, not direct JSON object.
- Some event fields like `home.score` may be absent; prefer `runningScores.fulltime` for completed matches.
- Year ranges that are too broad may fail with `400`; iterate yearly.
- H2H counts can be duplicated in merged datasets; always de-dup.
- Bookmaker endpoints discovered in JS bundles may still be unusable without browser/app context.

## Verification checklist
- Confirm the “next match” is `status=PreEvent` and correct competition.
- Confirm H2H rows are `status=PostEvent` for score-based summaries.
- Cross-check at least one sample row manually against rendered fixture page.
- If user asked league-only stats, ensure cup matches are excluded from that summary.

## References
- `references/norsk-tipping-oddsen-probing.md` — practical endpoint probing results and why screenshot/manual-odds fallback may be required.

## Minimal Python pattern
```python
import requests

URL = "https://www.bbc.com/wc-data/container/sport-data-scores-fixtures"
params = {
  "selectedStartDate": "2025-01-01",
  "selectedEndDate": "2025-12-31",
  "todayDate": "2026-05-18",
  "urn": "urn:bbc:sportsdata:football:team:manchester-united",
}
js = requests.get(URL, params=params, timeout=30).json()
for g in js.get("eventGroups", []):
    for sg in g.get("secondaryGroups", []):
        comp = sg.get("displayLabel")
        for ev in sg.get("events", []):
            home = ev.get("home", {}).get("fullName")
            away = ev.get("away", {}).get("fullName")
            status = ev.get("status")
            hs = ev.get("home", {}).get("runningScores", {}).get("fulltime")
            as_ = ev.get("away", {}).get("runningScores", {}).get("fulltime")
```
