---
name: norwegian-price-comparison
description: >
  Find cheapest products in Norway by scraping price comparison sites and retailers.
  Use when the user wants to buy something, find the best price, compare products,
  or asks "what's the cheapest X I can get" in a Norwegian context.
  Covers tire prices, electronics, car parts, groceries, or any physical product.
tags: [research, norway, price, shopping, comparison]
---

# Norwegian Price Comparison

Find the cheapest product for the user's specific needs in the Norwegian market.

## Workflow

### 1. Check user context FIRST (MANDATORY)
Before asking ANY clarifying questions, use `mnemosyne_recall` to check for known facts:
- Their car model, gear, preferences
- Previous purchases or stated constraints
- Budget preferences

**This is not optional.** Users get frustrated when you ask about things you should already know (e.g., "which Tesla do you have?" when it's in memory). If you already know what they need (e.g., tire size for their known car), don't ask — just search.

If memory returns nothing relevant, THEN ask clarifying questions.

### 2. Identify the product and specs
Determine exact specifications needed:
- For tires: width, profile, rim, season, speed/load index
- For electronics: model numbers, compatibility
- For car parts: OEM numbers, compatibility

### 3. Search for prices

#### Primary source: Prisjakt.no (price comparison)
Prisjakt aggregates prices from multiple Norwegian retailers and has simpler HTML than individual stores.

**Category URLs** (most reliable — use when available):
```
https://www.prisjakt.no/s/dekk-23545-r-18/
https://www.prisjakt.no/s/sommerdekk-23545-r-18/
```

**Search URLs** (fallback):
```
curl -s -L "https://www.prisjakt.no/search?search=<query>" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  --connect-timeout 15 --max-time 25
```

Note: Search URLs may hit Cloudflare challenges. Category URLs are more stable.

**Extraction pattern** (works reliably on Prisjakt category pages):
```python
import re

with open('/tmp/prisjakt.html', 'r') as f:
    html = f.read()

text = re.sub(r'<[^>]+>', '\n', html)
lines = [l.strip() for l in text.split('\n') if l.strip()]

results = []
for i, line in enumerate(lines):
    if '<product-spec>' in line:  # e.g., '235/45' and 'R18'
        for j in range(max(0, i-5), min(len(lines), i+5)):
            m = re.search(r'([\d\s\xa0]+)\s*kr', lines[j])
            if m:
                price_str = m.group(1).replace(' ', '').replace('\xa0', '')
                try:
                    price = int(price_str)
                except:
                    continue
                if MIN_PRICE < price < MAX_PRICE:
                    results.append((price, line))
                    break

results.sort(key=lambda x: x[0])  # Sort by price ascending
```

**Note:** Norwegian sites use `\xa0` (non-breaking space) in numbers — always clean with `.replace('\xa0', '')`.

#### Fallback sources (if Prisjakt fails)
- **Finn.no** — for used items and private sellers
- **Biltema** — good for budget car parts/tires
- **XXL** — seasonal sales on tires
- **Dekkonline.no** — specialized tire retailer

Most Norwegian retail sites use heavy JavaScript rendering and won't work with simple curl. Prisjakt is the most reliable for price data.

### 4. Present results
- Sort by price (cheapest first)
- Show per-item price AND total for the set (e.g., 4 tires)
- Note any compatibility requirements (load index, speed rating for tires)
- Flag budget brands vs. premium with honest quality notes

## Pitfalls

### Proactive memory check (CRITICAL)
Users get frustrated when you ask about facts you should already know. Always use `mnemosyne_recall` before asking "which model?" or "what size?" — if it's in memory, use it. Example failure: "Du vet jo at jeg har en Model 3 fra 2021. Hvorfor klarer du ikke finne det?"

### Norwegian language ambiguity
- "Bytte dekk" can mean "sell tires" OR "replace/buy new tires" — context determines which. When ambiguous, clarify.
- "Hjul" = wheels (with rims), "dekk" = tires (rubber only). Users sometimes mix these.

### Price scraping
- Norwegian retail sites (Biltema, XXL, Dekkonline) use React/Next.js with client-side rendering — simple curl returns empty pages
- Prisjakt.no works because it server-renders product listings
- Finn.no requires specific URL structures that change frequently
- Always use proper User-Agent headers or requests get blocked
- **Browser tools can also timeout** on these JS-heavy sites — don't rely solely on browser_navigate for price scraping
- DuckDuckGo lite and Google search via curl often return empty results due to bot detection
- **Best fallback**: Use Prisjakt.no category URLs (e.g., `/s/dekk-23545-r-18/`) which are more stable than search URLs

### Tesla-specific requirements
- Minimum load index for Model 3: 96 (check specific variant)
- Minimum speed rating: W (270 km/h) for most models
- EVs wear tires faster due to torque/weight — mention this when relevant

## Example: Tire price comparison
```
User: "Hva er det billigste jeg kan kjøpe dekk for på Teslaen?"
Context: User has Tesla Model 3 2021 → 235/45R18

1. Search Prisjakt for "dekk-23545-r-18"
2. Extract all 235/45 R18 tires with prices
3. Filter by valid load/speed index (≥96W)
4. Present sorted by price, noting brand origin and quality tier
```
