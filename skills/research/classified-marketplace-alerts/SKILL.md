---
name: classified-marketplace-alerts
description: Build durable daily/periodic alerts for classified marketplaces (cars, housing, gear) with deduping, budget math, and media-rich notifications.
version: 1.0.0
author: Hermes Agent
---

# Classified Marketplace Alerts

## When to use
- User wants ongoing alerts for new listings matching constraints (price, drivetrain/fuel, gearbox, location, etc.).
- User wants alerts delivered on schedule (daily/hourly) with links/images and computed metrics.
- Official API may exist but is unavailable (missing key/access), so fallback strategy is needed.

## Outcome
A cron-driven alert job that:
1. Pulls fresh listings from a stable source (API first, web fallback).
2. Filters against user constraints.
3. Dedupes using persisted `seen` IDs.
4. Enriches records (e.g., listing price from detail page JSON-LD).
5. Computes user-specific finance estimates.
6. Sends message only when there are new matches (silent otherwise).

## Standard workflow
1. **Confirm constraints explicitly**
   - Hard filters: fuel type(s), transmission, max price, excluded sales forms.
   - Text filters: required keywords (e.g., timing chain / recently changed timing belt).
   - Finance assumptions: down payment, max monthly payment, APR, terms.

2. **Try official API first**
   - Validate docs endpoint and auth requirement.
   - If API key/header is required and unavailable, ask user to choose:
     - provide key now,
     - proceed with web fallback now,
     - pause setup.

3. **Implement script under `~/.hermes/scripts/`**
   - Keep script deterministic and idempotent.
   - Persist state in `~/.hermes/cron/state/<job>_seen.json`.
   - Parse listing cards for IDs, title, metadata, image, URL.
   - Enrich each new listing from detail page JSON-LD (`@type: Product` → `offers.price`).

4. **Compute monthly loan estimate**
   - Principal = `max(0, price - down_payment)`.
   - Use annuity formula for each requested term.
   - Mark whether any term satisfies the user’s max monthly target.

5. **Cron delivery model**
   - Prefer `cronjob(create, no_agent=true, script=...)` for watchdog-style alerts.
   - Script must print message only when there are updates.
   - Empty stdout = no notification (desired quiet behavior).

6. **Verify before handoff**
   - Run script once to initialize baseline state.
   - Run again to confirm silent/noise behavior and output structure.
   - Trigger cron run once to confirm scheduler wiring.

## Message format (recommended)
For each new listing include:
- title + classification tag
- price
- monthly estimates (e.g., 5/7/8 years)
- compact metadata (year, km, fuel)
- listing URL
- image markdown

## Pitfalls
- Marketplace search pages often mix leasing/promoted content with sale listings; explicitly exclude leasing keywords.
- Search result snippets can have inconsistent price fields; detail page JSON-LD is typically more reliable for actual price.
- Do not spam: cap per-run items (e.g., first 10–15) and summarize remaining count.
- First run should seed state and avoid flooding historical matches.

## References
- `references/finn-no-pattern.md` — FINN-specific API/auth + parsing pattern used for car alerts.
