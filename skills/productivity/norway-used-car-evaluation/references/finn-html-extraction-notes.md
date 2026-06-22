# FINN.no extraction notes (cars)

## Current status (June 2026)

**Finn.no is a fully client-side rendered SPA (React/warp-ds).**

Both approaches have known failure modes:
- **Browser navigation** often times out (>60s) — Finn's JS bundle is heavy.
- **curl HTML fetch** of search results pages — limited data available via JSON-LD.

You CAN extract listing data from search results pages. FINN embeds a `<script id="seoStructuredData" type="application/ld+json">` tag with the first ~49 listings as structured JSON-LD data containing price, brand, model, description, and URL.

```bash
# Extract JSON-LD from search page
curl -sL 'https://www.finn.no/mobility/search/car?registration_class=1&variant=1.8078.2000501&price_to=200000' \
  | sed -n '/seoStructuredData/,/<\/script>/p' \
  | sed 's/.*<script[^>]*>//;s/<\/script>.*//' \
  | python3 -m json.tool
```

The JSON-LD structure is:
```json
{
  "@type": "CollectionPage",
  "mainEntity": {
    "@type": "ItemList",
    "itemListElement": [
      {"@type": "ListItem", "item": {
        "name": "...", "description": "...",
        "offers": {"price": "160000"},
        "url": "https://www.finn.no/mobility/item/466755434"
      }}
    ]
  }
}
```

**However**, the JSON-LD only includes description text (not year, km, battery size, etc.). For full details, still use individual ad page extraction on the URLs found.

**The description text is surprisingly informative** — FINN listings use a short-hand format like `"560km(WLTP)/LR/AWD/MCU2/Navi/R.kamera/Pano/AP/Memory"`. You can filter and classify listings by matching these patterns (e.g., `"LR" in desc or "LONG RANGE" in desc` to find Long Range, `"AWD" in desc` for four-wheel drive, `"SR"` or `"SR+"` for Standard Range, `"Performance"` for Performance). This works well enough to identify trim levels without opening individual ads.

**Beware**: Some listings have out-of-band prices (e.g. "4400" or "5900" kr) — these are likely financing/monthly-rate displays, not the actual car price. Filter by price > 10000 to skip these.

## Bulk market overview: JSON-LD extraction (reliable, fast)

**For getting ALL listings** on a search results page (up to ~50), the JSON-LD method works well:

```bash
# Download search page (follow redirects with -L)
curl -sL 'https://www.finn.no/mobility/search/car?registration_class=1&sort=PUBLISHED_DESC&variant=0.8078&variant=1.8078.2000501&year_from=2020&year_to=2020' \
  -o /tmp/finn_search.html

# Extract from JSON-LD with python3
python3 -c "
import json, re
html = open('/tmp/finn_search.html').read()
m = re.search(r'<script id=\\"seoStructuredData\\" type=\\"application/ld+json\\">(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1))
items = data['mainEntity']['itemListElement']
for e in items:
    i = e['item']
    print(i['offers']['price'], i['description'][:80], i['url'])
"
```

**Important**: FINN redirects `make=` and `model=` query params to `variant=` internally. If you see a redirect response, follow it with `-L`. The final stable URL format uses `variant=0.XXXX&variant=1.XXXX.YYYYY` pairs.

**What the JSON-LD gives you**:
- Price (always accurate, shows total not financing)
- Description (trim-level text like "LR/AWD/Pano/AP/Memory" — enough to filter SR vs LR vs Performance)
- URL (ad ID for follow-up)
- Model name and brand
- Image URL

**What it does NOT give**:
- Mileage (km)
- Year (but year is implicit from the search filter)
- Location
- Seller type (dealer/private/formidlingssalg)

### Parallel deep-check with delegate_task

When you need mileage + location + seller type for multiple comparables:

1. First run JSON-LD extraction to get the ad IDs and prices
2. Pick the ~10 most relevant comparables
3. Use `delegate_task` with one task containing all URLs — subagent opens each via `browser_navigate` and reads the specs from the page

```python
# Pseudocode pattern for parallel checking
delegate_task(
    tasks=[{
        "goal": "Check mileage for these 10 FINN ads at {urls}",
        "context": "For each ad: open URL, extract km, location, seller type, extra features. Return table.",
        "toolsets": ["browser", "terminal"]
    }]
)
```

One subagent handling 10 ads takes ~2 minutes (the main bottleneck is browser_navigate loading the JS shell). This is faster than checking them sequentially yourself.

## What works (three tiers)

### Tier 1 (best effort, rare success): Browser navigation
In rare sessions where `browser_navigate` loads quickly, look for:
- Repeated `<article ...>` blocks with `sf-search-ad` classes
- Per-listing data: title, URL (`/mobility/item/<id>`), image URL, year/km/fuel/transmission

### Tier 2 (reliable): Individual ad-page extraction via curl/Python

**Individual FINN ad pages** (`/mobility/item/{ad_id}`) contain **significant SSR data** despite the JS shell — it's embedded in the HTML server-side.

#### Approach A: curl + grep (quick field extraction)

```bash
# Basic info from <meta> and <title>
curl -sL "https://www.finn.no/mobility/item/{id}" -H "User-Agent: Mozilla/5.0 ..." \
  | grep -oP '<title>[^<]+</title>'
  | grep -oP '<meta name="description" content="[^"]*"'
  | grep -oP '<meta property="og:image" content="[^"]*"'

# Price
grep -oP '"price":\s*[0-9]+'

# Mileage
grep -oP '"key":"mileage","value":\["([0-9]+)"\]'

# Other specs (use underscore-key variant names where available)
grep -oP '"key":"(battery_capacity|modelYear|drivetrain|color|seats|owners|car_make|car_model|car_model_spec|engine_effect|wheel_drive|exterior_color|registration_number)","value":\[[^\]]+\]'
```

Key fields and their values (Tesla Model 3 examples):
| key | meaning | example values |
|-----|---------|---------------|
| `mileage` | km-stand | `154000` |
| `price` | pris i kr | `199532` |
| `year` | årsmodell | `2021` |
| `car_model_spec` | trim/utstyr shorthand | `580km(WLTP)/LR/AWD/Krok/MCU2/Navi/R.kam/Pano/AP/V.pumpe` |
| `engine_effect` | HK (hestekrefter) | `498` (LR AWD), `462` (some LR), `346` (SR+) |
| `battery_capacity` | batteri kWh | `70`, `75`, `65` |
| `driving_range` | WLTP rekkevidde km | `614`, `580` |
| `exterior_color` | fargekode | `9`=Hvit, `14`=Svart, `6`=Grå/Midnight Silver |
| `wheel_drive` | drivverk | `2`=AWD |
| `owners` | antall eiere | `1`, `2` |
| `transmission` | girkasse | `2`=automat |
| `sales_form` | salgsform | `1`=brukt |
| `dealer_segment` | selgertype | `1`=forhandler, `0`=privat |
| `registration_number` | bilskilt | `ED18626` |
| `feature_package` | utstyrspakke | `PREMIUM` |

#### Approach B: Python script (better for complex extractions — recommended for 3+ ads)

Complex shell escaping (dollar signs, curly braces, quotes in Python regex inside bash heredocs) leads to silent failures. Save a .py script to /tmp and invoke it per URL instead:

```python
# /tmp/finn_extract.py
import sys, re, urllib.request

url = sys.argv[1]
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')

# Meta description (contains feature text!)
m = re.search(r'<meta name="description" content="([^"]+)"', html)
if m:
    desc = m.group(1)
    desc = desc.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    desc = desc.replace('&nbsp;', ' ').replace('&ndash;', '-')
    print(f'META_DESC: {desc[:400]}')

# All key-value specs — collect into dict
for key in ['mileage', 'price', 'year', 'car_model_spec', 'engine_effect',
            'battery_capacity', 'driving_range', 'exterior_color', 'owners',
            'wheel_drive', 'sales_form', 'dealer_segment', 'registration_number',
            'feature_package', 'first_registration', 'org_id']:
    m = re.search(rf'"key":"{key}","value":\["([^"]+)"\]', html)
    if m:
        print(f'{key.upper()}: {m.group(1)}')
```

Run with:
```bash
python3 /tmp/finn_extract.py "https://www.finn.no/mobility/item/{ad_id}"
```

**What the meta description contains**: The `<meta name="description">` tag often holds the real ad text (features, condition, seller notes) — unlike `adBody` which is loaded via JS. Extract it first; it's the richest source of feature information.

**What is NOT available via SSR**:
- `adBody` (full ad description text — JS-loaded)
- `first_registration` (first registration date — often absent from SSR)
- `org_name` / `dealerName` (dealer/business name)
- These must be obtained via browser_navigate or left as unknown

**Field consistency pitfall**: Always cross-check `car_model_spec` against `engine_effect` and `battery_capacity`. In one session the spec field said "Long Range AWD" while the actual data (346hk, 65kWh) matched a Standard Range+ — either a mislabeled ad or a data error. Never trust `car_model_spec` alone; validate against the numerical specs.

**car_model_spec shorthand decoding** (Tesla Model 3):
| Code | Meaning |
|------|---------|
| LR | Long Range |
| AWD | Firehjulstrekk |
| SR / SR+ | Standard Range (Plus) |
| P / Performance | Performance |
| MCU2 | Media Control Unit 2 (3.0) |
| AP | Autopilot |
| Navi | Navigasjon |
| R.kam / R.kamera | Ryggekamera |
| Pano | Panoramatak |
| V.pumpe | Varmepumpe |
| Krok | Hengerfeste |
| Skinn | Skinninteriør |
| Memory | Seteminne |

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
   - Tesla Model 3 SR+ 2021: 180-210k for 80-120k km
   - Tesla Model 3 LR AWD 2021: 195-240k for 80-150k km

3. Use **Google search** trick as last resort:
   ```
   site:finn.no Tesla Model 3 2021 pris
   ```
   (May also be blocked by rate-limiting.)

## Fallback URL templates for common searches

| Modell | Finn-søk URL |
|--------|-------------|
| Kona Electric 64 kWh | `/car/used/search.html?fuel=2&make=65&model=2391&price_to=150000` |
| Kia e-Niro 64 kWh | `/car/used/search.html?fuel=2&make=455&model=1262&price_to=160000` |
| Tesla Model 3 LR | `/car/used/search.html?fuel=2&make=8078&model=2000501&price_to=250000` |
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

### Seller-refuses-NAF-test red flag
- If a seller (especially a dealer) refuses a paid NAF test, treat it as a strong negative signal. A legitimate seller with nothing to hide has no reason to decline a buyer-funded independent inspection. Flag this to the user explicitly.
