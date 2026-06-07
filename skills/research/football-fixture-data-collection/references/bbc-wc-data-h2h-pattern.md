# BBC wc-data extraction pattern (migrated)

- Seed page: `https://www.bbc.com/sport/football/teams/<team>/scores-fixtures`
- Extract `window.__INITIAL_DATA__` from HTML.
- Decode twice (escaped JSON string -> JSON object).
- Find `sport-data-scores-fixtures?...` key in `data` entries.
- Query: `https://www.bbc.com/wc-data/container/sport-data-scores-fixtures`
- Params: `selectedStartDate`, `selectedEndDate`, `todayDate`, `urn`.
- Parse path: `eventGroups[] -> secondaryGroups[] -> events[]`.
- Use `runningScores.fulltime` for completed match scores.
- Use year-bounded windows to avoid broad-range `400` failures.
- Deduplicate H2H rows by `(date, home, away)` before summarizing.
