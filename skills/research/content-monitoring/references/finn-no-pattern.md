# FINN.no pattern for recurring car-listing alerts

## What was validated
- Docs page: `https://www.finn.no/api/doc/search`
- FINN Search API requires API key header (`x-FINN-apikey`) for `cache.api.finn.no` endpoints.
- Without key, API responses returned `403 Forbidden`.
- Practical fallback: scrape public mobility search HTML and enrich from listing detail JSON-LD.

## Practical extraction approach (web fallback)
1. Search page (`/mobility/search/car?...`) for listing cards:
   - listing URL `/mobility/item/<id>`
   - title (`<h2...>`)
   - metadata line (year, km, fuel, gearbox/range)
   - image URL (`images.finncdn.no/...`)
2. Detail page (`/mobility/item/<id>`) for price:
   - parse `<script type="application/ld+json">`
   - find `@type: Product`
   - read `offers.price` (NOK)

## Filtering logic used
- Include:
  - EV listings (metadata contains `El`)
  - Petrol listings only if text suggests timing-chain or timing-belt recently replaced.
- Exclude leasing/promoted leasing phrasing (e.g., `leasing`, `leiekampanje`, `0% rente`).

## Cron/watchdog behavior
- Use `cronjob(create, no_agent=true, script=...)`.
- Script writes **nothing** when no new matches.
- Script prints full digest when new IDs appear.
- Persist IDs in `~/.hermes/cron/state/<name>_seen.json`.

## Finance estimate used
- Inputs: price, down payment, APR, term months.
- Principal = `max(0, price - down_payment)`.
- Monthly = annuity formula
  - `M = P * r / (1 - (1+r)^(-n))`, `r = APR/12`.
- Report multiple terms (e.g., 5, 7, 8 years) to match user flexibility.
