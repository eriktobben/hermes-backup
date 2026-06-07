# FINN.no extraction notes (cars)

## Current status (June 2026)

**Finn.no is a fully client-side rendered SPA (React/warp-ds).**

Both approaches have known failure modes:
- **Browser navigation** often times out (>60s) — Finn's JS bundle is heavy.
- **curl HTML fetch** of search results pages returns only the shell HTML with no actual listing data. The JSON-LD markup found in the page is from related/random ads, NOT the search results.

## What works (three tiers)

### Tier 1 (best effort, rare success): Browser navigation
In rare sessions where `browser_navigate` loads quickly, look for:
- Repeated `<article ...>` blocks with `sf-search-ad` classes
- Per-listing data: title, URL (`/mobility/item/<id>`), image URL, year/km/fuel/transmission

### Tier 2 (reliable): Individual ad‑page extraction via curl
**Individual FINN ad pages** (`/mobility/item/{ad_id}`) contain **significant SSR data** despite the JS shell — it's embedded in the HTML server-side. Use curl + grep patterns:

```bash
# Basic info from <meta> and <title>
curl -sL "https://www.finn.no/mobility/item/{id}" -H "User-Agent: Mozilla/5.0 ..." \
  | grep -oP '<title>[^<]+</title>'                           # → "Hyundai Kona - 2021 - Grå"
  | grep -oP '<meta name="description" content="[^"]*"'       # → ad description text
  | grep -oP '<meta property="og:image" content="[^"]*"'      # → main image URL

# Price — look for "price": NUMBER
grep -oP '"price":\s*[0-9]+'

# Mileage — look for key-value blob
grep -oP '"key":"mileage","value":\["([0-9]+)"\]'            # → 88000

# Other specs (battery, year, drivetrain, color, seats, etc.)
grep -oP '"key":"(batteryCapacity|modelYear|drivetrain|color|seats|owners|car_make|car_model)","value":\[[^\]]+\]'

# Registration date
grep -oP '"key":"first_registration","value":\["[^"]+"\]'

# Ad ID is in the URL path — use as identifier
```

**Limitations**: Only works for individual ad pages (not search results). Price data may appear in JS bundles too — verify by checking multiple matches.

### Tier 3 (always available): Fallback — market knowledge + search links

When extraction fails or there's no specific ad to inspect:
1. Provide **direct search links** the user can click:
   ```
   https://www.finn.no/car/used/search.html?fuel=2&make=65&model=2391&price_to=150000&transmission=1
   ```
   - `fuel=2` = EV
   - `transmission=1` = automatic
   - `make=65` = Hyundai (etc.)
   
2. Base recommendations on **known market prices**:
   - Hyundai Kona Electric 64 kWh 2019: 115-135k for 70-90k km
   - Kia e-Niro 64 kWh 2019: 130-155k for 60-80k km
   - Renault Zoe ZE50 R135 2020: 90-120k for 40-60k km

3. Use **Google search** trick as last resort:
   ```
   site:finn.no Hyundai Kona Electric 64 kWh 2019 pris
   ```
   (May also be blocked by rate-limiting.)

## Fallback URL templates for common searches

| Modell | Finn-søk URL |
|--------|-------------|
| Kona Electric 64 kWh | `/car/used/search.html?fuel=2&make=65&model=2391&price_to=150000` |
| Kia e-Niro 64 kWh | `/car/used/search.html?fuel=2&make=455&model=1262&price_to=160000` |
| Mazda 3 | `/car/used/search.html?fuel=1&make=495&model=1396&price_to=110000` |

## Budget calculation helper

When a user provides down payment + monthly loan cap:

```python
# amortized loan PV
P = M * (1 - (1 + r)^(-n)) / r
total_budget = P + down_payment - buffer (5000-10000 for fees)
```

## Evaluation notes from real session (June 2026)

### Timing belt vs chain nuance
- Timing belt replacement is routine maintenance (5000-10000 kr every 6-10 years).
- A recently replaced belt with documentation is a *positive*, not a negative.
- Document the interval and cost as a sjekkpunkt — don't hard-exclude belt cars.

### EV winter range heuristic
- Kr.sand–Oslo = 320 km.
- With one charging stop in winter: car needs ≥400 km WLTP (60-75% winter derate).
- Hyundai Kona 64 kWh (449 WLTP) ≈ 280-320 km real winter → one quick stop.
- Tesla Model 3 SR+ (491 WLTP) ≈ 320-370 km real winter → maybe 0 stops.

### Hybrid vs pure EV for high-km used
- Two drivetrains = more failure points; valid concern for 150k+ km used hybrids.
- A used plug-in hybrid without home charging is just a heavy petrol car — not recommended.

### Budget-friendly bensin alternatives
- Mazda 3 SkyActiv 2.0 (2015-2019): timing chain, reliable, 70-100k
- Toyota Auris/Corolla 1.2T (2015-2018): timing chain, Toyota reliability, 80-110k
- Suzuki Swift 1.2 (2017-2020): cheap, simple, chain-driven, 60-90k
