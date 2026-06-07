---
name: football-fixture-data-collection
description: Collect upcoming football fixtures, historical match results, and optional odds context from resilient public-data workflows when common stats sites are blocked.
---

# Football Fixture Data Collection

## Umbrella class
Use when users ask for next match, opponent, recent H2H, or league-scoped match history and normal stats sites are blocked/JS-heavy.

## Core workflow
1. Resolve fixture source first (upcoming match before H2H).
2. Extract machine-readable payloads from stable sources.
3. Query deterministic endpoints directly where possible.
4. Pull history in bounded windows (year chunks) to avoid range failures.
5. Normalize events (date, competition, status, teams, score).
6. Filter/slice for requested views (H2H, league-only, recent N).
7. De-duplicate merged results and sort by date.
8. Cross-check at least one row against rendered page output.

## Source strategy subsection: BBC wc-data path
- Parse `window.__INITIAL_DATA__` when needed and decode escaped JSON safely.
- Use wc-data container endpoints with explicit date parameters.
- Prefer `runningScores.fulltime` for completed-match score extraction.

## Odds integration subsection
- Expect sportsbook anti-bot/session constraints.
- If deterministic odds retrieval fails, switch to explicit fallback: accept user-provided odds/screenshot and continue analysis.

## Verification checklist
- Next match is truly upcoming (`PreEvent`)
- Score-based summaries use completed events (`PostEvent`)
- Requested competition filter is correctly applied
- Duplicates removed before summary

## Support file guidance
- Keep provider-specific probing notes in `references/`
- Keep reusable extraction scripts in `scripts/`
