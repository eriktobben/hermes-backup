# Norsk Tipping Oddsen probing notes

Session-tested signals when trying to fetch pre-match odds programmatically:

- `https://www.norsk-tipping.no/sport/oddsen/sportsbook/` loads a JS shell with:
  - `config/environment.js`
  - `config/settings.js`
  - `config/components.js`
  - `app/js/app.*.js`
- `environment.api.url` exposed host:
  - `https://www-opr1.sport2.norsk-tipping.no`
- JS bundle shows betting endpoints under `/API/` (e.g. `betting/fo/bet/calculate`, `betting/fo/allowedBetTypesWithCalculation`) but these are betslip-oriented and not sufficient alone for open event odds retrieval.
- POSTs to `https://www-opr1.sport2.norsk-tipping.no/services` with guessed methods returned generic:
  - `{"errorType":"INTERNAL_ERROR","data":[]}`
- Practical conclusion: without full app/session context, deterministic raw odds extraction can fail; ask user for screenshot/manual odds and proceed with value analysis.
