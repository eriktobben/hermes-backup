# Car color detection from Norwegian ads

## Why this matters

Norwegian car buyers often have strong color preferences (svart, hvit, grå — or NOT rød). FINN's JSON-LD search data does NOT include exterior color. You must use other methods to determine a car's color before recommending it.

## Method 1: Statens vegvesen lookup (most reliable)

Every FINN ad for a registered car includes a link to Statens vegvesen under "Nyttige lenker":

```
https://www.vegvesen.no/kjoretoy/kjop-og-salg/kjoretoyopplysninger/sjekk-kjoretoyopplysninger?registreringsnummer=XX12345
```

The license plate (registreringsnummer) is visible in the ad page — look for the link text "Sjekk tid for neste EU-kontroll" which contains the reg.nr in its URL.

**How to extract the reg.nr from a FINN ad page:**
1. Navigate to the ad page with `browser_navigate`
2. Find the link in the "Nyttige lenker" section — it contains the reg.nr
3. Navigate to the vegvesen URL and extract the "Farge" field from the vehicle data
4. The result shows the official registered color (e.g., "Svart", "Hvit", "Grá", "Rod")

This is the gold standard — gives you the exact factory-registered color.

**Alternatively**, use the vegvesen lookup directly: navigate to the vegvesen URL and check the vehicle information table. The color field is clearly labeled.

## Method 2: Ad description text (when available)

Some ads explicitly mention color in the description text. Look for keywords like:
- Norwegian: hvit, svart, sort, grå, blå, rød, grønn, brun, beige, sølv, hvitperle
- English: white, black, blue, red, grey, gray, silver, pearl, midnight, deep blue
- Tesla-specific: Midnight Silver Metallic, Pearl White, Solid Black, Deep Blue Metallic, Red Multi-Coat

Scroll to the full ad description with `browser_scroll` + `browser_snapshot(full=true)`.

## Method 3: Image analysis (unreliable — use as last resort)

FINN CDN image URLs follow the pattern:
```
https://images.finncdn.no/dynamic/default/item/{ad_id}/{uuid}
```

You can download the first image and use PIL to find dominant colors, but this is unreliable because:
- The first image is often a thumbnail that includes background/environment
- Lighting conditions affect color detection
- A white car in shadow can look gray; a black car in sunlight can look dark blue

**When it works**: only for extreme colors — bright red, bright blue, or when the car fills the entire frame.

## Tesla Model 3 facelift timeline

For Tesla-specific evaluations:

| Generation | Period | Key differences |
|---|---|---|
| Pre-facelift | 2017-2023 | Fysiske blinklysspaker, regnsensor, ultralydssensorer, kromdetaljer |
| Highland (facelift) | Sept 2023+ | Redesignet front/bak, fjernet spaker, ventilasjonsseter, stillere kabin, bakskjerm |

All 2020-modeller er pre-facelift. Ikke bruk facelift som beslutningskriterium mellom 2020-modeller.

## Norwegian Tesla Model 3 exterior colors (2020)

- Pearl White Multi-Coat (standard, hvit)
- Solid Black (svart)
- Midnight Silver Metallic (grå)
- Deep Blue Metallic (blå)
- Red Multi-Coat (rød — ekstra kostnad)

## Workflow: checking color for a shortlist

When user has a color preference and you've identified ~5-10 comparable candidates:

1. Filter JSON-LD to matching trim level → get ad IDs
2. Pick 3-5 most price-relevant candidates
3. Use `delegate_task` with 1-3 tasks (each opens 1-3 ads via browser_navigate)
4. For each ad: extract reg.nr from the "Nyttige lenker" section URL → navigate to vegvesen → read color
5. Return a table: ad ID, price, km, color, location, seller type
6. Present the filtered shortlist to the user sorted by match quality
