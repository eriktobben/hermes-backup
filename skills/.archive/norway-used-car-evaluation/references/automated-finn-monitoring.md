# Automated FINN car monitoring (cron job pattern)

## Overview

Instead of one-shot evaluations, set up a **persistent daily cron job** that:
1. Scrapes FINN search results for matching cars (elbil + bensin med registerkjede)
2. Maintains a rolling 10-day window in a JSON state file
3. Publishes results to a here.now page (dark-themed HTML)
4. Delivers only the URL to the user daily

This complements the one-shot evaluation workflow in the main SKILL.md.

## Architecture

```
~/.hermes/scripts/finn_bilvarsel.py   ← data collection (runs first)
~/.hermes/cron/finn-bilvarsel/        ← workdir (here.now state + HTML)
  index.html                           ← generated dark-themed page
  .herenow/state.json                  ← here.now slug persistence
~/.hermes/cron/state/finn_bilvarsel_data.json  ← rolling window state
```

## Data collection script

The script (`~/.hermes/scripts/finn_bilvarsel.py`) does:

### State file format
```json
{
  "ads": {
    "465316415": {
      "id": "465316415",
      "title": "Tesla Model 3",
      "link": "https://www.finn.no/mobility/item/465316415",
      "desc": "...",
      "meta": "...",
      "img": "https://images.finncdn.no/...",
      "kind": "elbil",
      "price": 180000,
      "first_seen": "2026-06-12T09:00:00+00:00",
      "last_seen": "2026-06-12T09:00:00+00:00"
    }
  }
}
```

### Rolling window logic
- Each run scrapes FINN search results
- New ads get price extracted from individual ad page (one HTTP request)
- Existing ads update `last_seen` and listing info but keep cached price
- Ads with `first_seen` older than 10 days are purged
- State file is append-friendly and survives agent restarts

### Loan estimate calculation
The script pre-computes loan estimates per ad:
```python
EGENKAPITAL = 50000    # down payment
RENTE_AARLIG = 0.07    # annual interest rate
TERMS = [60, 84, 96]   # months (5, 7, 8 years)
MAX_MND = 2500          # monthly budget cap
PRICE_TO = 260000       # max car price in FINN search
```
Output includes `estimates` dict and `fits_budget` boolean per ad.

## Cron job setup

Convert a no_agent script cron to **agent-driven** with here-now skill:

```bash
# Instead of:
#   no_agent: true
#   script: my_script.py

# Use:
#   skills: [here-now]
#   workdir: /path/to/workdir
#   prompt: "Step-by-step instructions for agent"
```

### Agent prompt structure

```
1. Run data collection: python3 ~/.hermes/scripts/finn_bilvarsel.py > data.json
2. Create dark-themed HTML from JSON
3. Delete data.json (publish.sh rejects unexpected files)
4. cd to workdir && publish.sh --slug {slug} --client hermes
5. Output only URL + single-line teaser
```

## here.now publishing pitfalls

### CRITICAL: No trailing slash in path
publish.sh has a Bash bug: `${f#$TARGET/}` substitution fails when TARGET ends with `/`. Always pass the directory path WITHOUT trailing slash:

```bash
# WRONG - causes "Invalid file path: /abs/path/index.html (absolute paths not allowed)"
bash publish.sh /path/to/dir/ --slug my-slug

# RIGHT
cd /path/to/dir
bash ~/.here-now/publish.sh /path/to/dir --slug my-slug
```

### Workdir state persistence
Always `cd` to the workdir before running publish.sh so `.herenow/state.json` is created in the right place. This lets subsequent runs auto-detect the slug and update in place.

### Workflow
```bash
cd /path/to/workdir
bash ~/.here-now/publish.sh /path/to/workdir --slug existing-slug --client hermes --title "Page Title"
```

## HTML conventions for monitoring pages

- Dark theme (bg: #0d1117, cards: #161b22)
- Self-contained (no external CSS/JS)
- Sections: Tesla Model 3 (if present), then all ads sorted newest first
- Per ad card: budget badge (✅/⚠️), title+link, price, loan estimates (5/7/8y), meta, description, image
- Stats bar at top: counts per fuel type
- Footer with generation timestamp

## When to use this pattern vs one-shot evaluation

| Scenario | Approach |
|----------|----------|
| User asks "find me a car" | One-shot (main skill) |
| User wants daily monitoring | Automated cron (this reference) |
| User provides specific listing URL | Individual ad extraction (finn-html-extraction-notes.md) |
| Scraping fails | Fallback to market knowledge + search links |
