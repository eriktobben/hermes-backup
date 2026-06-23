---
name: norway-used-car-evaluation
description: Evaluate used-car options in Norway with strict monthly-loan caps, compare EV vs petrol/hybrid tradeoffs, and pull concrete FINN listings with image/link evidence.
---

# Norway used car evaluation

## When to use
- User wants help choosing between EV and petrol/hybrid in Norway.
- User provides a hard monthly budget and down payment.
- User wants concrete FINN candidates (links + images), not only generic model advice.
- User asks to set up automated daily FINN monitoring with here.now publishing (see `references/automated-finn-monitoring.md`).
- User asks "is this price fair?" about a specific listing — trigger market comparison analysis.
- User shares a Rebil.no (or similar fixed-price dealer) listing — enable Rebil extraction, technical test analysis, and dealer negotiation advice.

## Core outcomes
1. Convert monthly payment + down payment + term into a realistic car-price range.
2. Explain EV vs petrol/hybrid tradeoffs for the user's charging reality.
3. Return a shortlist of concrete listings with direct links and image URLs.
4. Answer "is this price fair?" with real market data when user asks.

## Workflow
1. **Collect minimum decision inputs**
   - km/month or km/year
   - loan-only vs total-cost budget
   - ownership horizon (years)
   - home charging availability
   - transmission requirement
   - size/use constraints
   - mechanical reliability preferences (timing chain vs belt, hybrid complexity fears)
   - **Formidlingssalg-klarering**: Når bruker gir en FINN-URL, sjekk om det er formidlingssalg eller vanlig forhandlerkjøp. Tilpass prisforventning og kjøpsråd deretter.

2. **Compute affordability envelope (always calculate, don't eyeball)**
   - Use amortized loan PV formula across plausible interest band (e.g., 4–10%).
   - Add user down payment.
   - Reserve a buffer for fees/registration before setting target listing price.
   - Example: 50k down + 1500 kr/mnd at 7% over 5y ≈ 70k loan → ~120k total budget
   - CRITICAL: Always verify the loan term (nedbetalingstid) — 5y vs 8y vs 10y dramatically changes the envelope. Same monthly payment at 10y gives ~135k loan → ~195k total.
   - Always explicitly ask: "Hvor mange år vil du betale over?" — don't assume a term.

3. **Decision framing**
   - If no home charging: explicitly warn that EV fast-charging can erase fuel-cost advantage vs a cheap petrol car used mostly for short trips. However, note that 5-10 km daily city driving on an EV still beats petrol on running cost.
   - If user requests long winter intercity EV legs with limited charging stops: require extra real-world range margin vs WLTP. Rule of thumb: expect 60-75% of WLTP in winter. Kristiansand–Oslo (320 km) needs a car with at least 400 km WLTP for comfortable one-stop winter driving.
   - For petrol constraint questions (timing chain vs belt): note that a recently replaced timing belt is a *positive*, not a negative — document the replacement interval and cost as a sjekkpunkt rather than a hard filter.
   - For hybrid skepticism: the user's logic (two drivetrains = two failure modes) is valid for high-mileage used cars. Flag this tradeoff honestly.
   - Elbil without home charging is viable IF the user can fast-charge weekly for city use, and the car has ≥ 100 kW CCS for efficient highway charging.

4. **Pull live market examples (FINN) — with fallback**
   - **If user provides a specific FINN URL**: extract via curl+grep from the individual ad page (`/mobility/item/{id}`). The page contains SSR data with price, km, year, battery, etc. embedded in the HTML — see `references/finn-html-extraction-notes.md` for exact grep patterns. Much faster than browser_navigate.
   - **If user asks for search results or "is this price fair?"**: attempt FINN extraction via JSON-LD method (see references). The JSON-LD on search pages gives you up to ~50 listings with prices and descriptions in one curl call — much faster than browser.
     - **MULTI-PAGE**: JSON-LD only covers the FIRST search results page (~25-49 results). When the user wants a complete market overview (e.g. all 2021 LR AWD under 260k), iterate pages 1, 2, 3 by appending &page=N to the search URL. Merge results and deduplicate by ad ID. A single page may miss 30-50% of total candidates.
     - When doing price fairness comparison: filter the JSON-LD output to comparable trim levels (e.g., filter out SR/SR+ when comparing LR AWD, filter out Performance when comparing standard Long Range), then sort by price to position the user's car in the market.
     - Kilometerstand er kritisk - JSON-LD gir ikke km. Du MA folge opp med km-data pa sammenlignbare biler for du konkluderer om prisen er riktig. Se workflow under for parallel deep-check.
     - Fargepreferanse - JSON-LD inneholder ikke farge. Nar brukeren har en fargepreferanse, ma du sjekke farge via en av metodene i references/car-color-detection.md. Gjor dette etter JSON-LD-utfiltreringen, pa 3-5 aktuelle kandidater med delegate_task.
     - Parallel deep-check med delegate_task (for km, farge, sted, selgertype):
       1. Kjor JSON-LD-ekstraksjon -> fa ad-IDs + priser + trim-beskrivelser
       2. Filtrer til sammenlignbar trim (f.eks. bare LR AWD, ikke SR eller Performance)
       3. Velg 5-10 mest relevante kandidater (prisnaere, fornuftig utstyr)
       4. Bruk delegate_task med tasks array (max 3 parallelt) for a sjekke km, farge, sted, selgertype og ekstrautstyr. Hver task apner 1-3 annonser via browser_navigate.
     - Dette er MYE mer effektivt enn a sjekke en og en annonse sekvensielt.
   - **If extraction fails** (>60s timeout or empty data), **do not fabricate listings**.
   - Fallback: provide market-informed model advice with known price ranges (e.g., "Kona Electric 64 kWh 2019: 115-135k for 70k km") and clickable search URLs the user can open.
   - Include `https://www.finn.no/car/used/search.html?fuel=2&make=65&model=2391&price_to=150000&transmission=1` style links — use proper query parameters (fuel=2=EV, transmission=1=automatic).
   - **Verify critical specs via vegvesen lookup**: When the user has a specific car with a registration number, use `references/vegvesen-registration-lookup.md` to verify official WLTP range, motor effect (trim), colour, and first registration date directly from Statens vegvesen. This catches FINN ad inaccuracies (e.g., a car advertised as "614 km WLTP" may actually show 580 km in the official register).

5. **Present shortlist clearly**
   - Group by powertrain (hybrid/petrol/EV).
   - Include why each candidate fits, plus one "check before buy" note per car.
   - Keep it tight: avoid reprinting the spec table from the ad.
   - In Norwegian, use consistent bokmål spelling.

## Formidlingssalg (broker/commission sale)

**Norwegian dealers sometimes sell cars as "formidlingssalg"** — the dealer acts as a broker between a private seller and the buyer, not as the seller themselves. This is increasingly common.

### Critical legal difference

| Aspekt | Vanlig forhandlerkjøp | Formidlingssalg |
|---|---|---|
| Reklamasjon | 5 år (forbrukerkjøpsloven) | Som privatsalg — "som den er" |
| Mislighold | Selger har bevisbyrde etter 6 mnd | Kjøper må bevise skjulte feil |
| Angrerett | 14 dager (ved fjernsalg) | Ingen automatisk angrerett |
| Prisforventning | Forhandlerpris (høyere) | Privatpris (lavere, + provisjon) |

### Håndtering i evaluering

1. **Alltid spør** "Er dette ordinært forhandlerkjøp eller formidlingssalg?" — står ofte i liten tekst i annonsen.
2. **Prisen skal være lavere** ved formidlingssalg — du får ikke forbrukervernet, så du bør ikke betale forhandlerpris. Forhandle hardere.
3. **Anbefal uavhengig bilinspeksjon** (NAF-test eller lignende) siden du ikke har forbrukerkjøpsloven i ryggen.
4. **Få alle avtaler skriftlig** — muntlige løfter fra forhandler er lite verdt.
5. **Formidlingssalg påvirker markedsprissammenligning** — når du sammenligner med andre annonser, vær bevisst på om de er forhandler-, formidlings- eller privatsalg. Sammenlign epler med epler.

## Real-world EV range — beyond WLTP

### Winter range by model (NAF-test data, Norway)

Not all EVs are equal in winter. Do not use a generic "60-75% of WLTP" rule — retention varies dramatically:

| Model (år) | WLTP | Sommer (NAF) | Vinter (NAF) | Vinterandel |
|:-----------|:----:|:------------:|:------------:|:-----------:|
| Tesla M3 LR AWD (2021) | 614 km | 654,9 km | 514,8 km | **84 %** |
| Tesla M3 LR (2020) | 610 km | 612 km | 404 km | **66 %** |
| Tesla MY LR Dual | ~565 km | 545 km | 452 km | **80 %** |
| BMW iX xDrive50 | ~630 km | 568,5 km | 503 km | **80 %** |
| BMW i4 M50 | ~510 km | 521 km | 406 km | **78 %** |
| Ford Mach-E LR RWD | 610 km | 617,9 km | 502,5 km | **82 %** |
| Kia EV6 2WD | ~530 km | 500,2 km | 429 km | **81 %** |
| Hyundai IONIQ 5 AWD | ~480 km | 502 km | 369 km | **73 %** |
| Polestar 2 SM | ~540 km | 520,6 km | 400 km | **74 %** |
| VW ID.4 | ~520 km | 532 km | 414 km | **80 %** |
| Skoda Enyaq iV80 | ~530 km | 522 km | 347 km | **65 %** |
| Tesla MS LR | ~663 km | 645 km | 469,8 km | **71 %** |

**Key takeaway**: Tesla 2021+ (med varmepumpe) er best i klassen på vinter — ~84 %. Skoda Enyaq taper ~35 %, IONIQ 5 AWD taper ~27 %. Velg modell med omhu når kunden kjører lange vinterturer.

**Kilde**: NAF/Motor rekkeviddetester (NTB pressemelding juni 2022) — faktiske målinger til bilen stopper, på norsk vinterføre.

### Battery degradation by mileage (NCA/NMC)

Degradering flater ut etter ~80.000 km. Nyttig for å forventningsavstemme kjøper:

| Km (ca.) | Forventet degradering | Gjenværende kapasitet |
|:--------:|:---------------------:|:---------------------:|
| 0-80.000 km | 3-7 % | 93-97 % |
| 80.000-240.000 km | +3-5 % (flater ut) | 88-94 % |
| 240.000+ km | +2-3 % | 85-90 % |

For LFP (Tesla SR/SR+ 2021+): lavere total degradering, men mer kalibreringsavhengig.

**Slik sjekker du batterihels på en Tesla under befaring:**
- Lad til 100 % → les estimert range fra skjermen
- Over 90 % av WLTP = 💚, 80-90 % = 💛, under 80 % = vurder garantisak

Se `references/ev-range-degradation-data.md` for detaljerte datakilder og metoder.

## XtraGaranti Diamond E — hva dekker den egentlig?

Rebil inkluderer 6 mnd XtraGaranti Diamond E (AutoConcept). Dette er en reparasjonsforsikring, ikke utvidet nybilgaranti.

### Dekning — Diamond E (elbil)

| Dekkes ✅ | Dekkes ikke ❌ |
|:----------|:--------------|
| Elmotor | **Høyspenningsbatteri (eksplisitt unntatt)** |
| Ladesystem (ladeport, ladeenhet, kabel) | Slitasje (bremser, fjæring) |
| Varmepumpe/kjøle-/varmesystem | Støy, justering, smøring |
| Elektronikk/styreenheter | Feil som fantes før garantiregistrering |
| Multimedia (fabrikkskjerm) | Service må være fulgt |
| Panorama/soltak | |
| Firehjulsdrift | |
| **Maks 100.000 kr per skade** | Nedgraderes til Sølv/Bronse ved 9 år / 180.000 km |

### Vurdering

- **Inkludert 6 mnd** = verdt å ha, ingen kostnad
- **Betalt utvidelse** = sjelden verdt på Tesla. Du har allerede: forbrukerkjøpsloven (5 år reklamasjon) + Tesla-fabrikkgaranti på batteri (8 år / 192.000 km)
- Unntak: kun vurder utvidelse om prisen er < 1.000 kr/år

## Rebil / fixed-price dealer evaluation

Norwegian fixed-price dealers like **Rebil** operate differently from FINN private sellers or traditional dealers.

### How Rebil works
- **Fixed-price model**: Cars are priced at a fixed "lave priser" — limited negotiation margin. Their stated policy is that cosmetic wear is already factored into the price.
- **No formidlingssalg risk**: Rebil sells as a proper dealer (forhandlerkjøp) with full consumer protections (5-year reclamation, 14-day angrerett at distance).
- **Includes warranty**: Minimum 6 months (XtraGaranti Diamond via AutoConcept on their cars).
- **Can still negotiate**: While they claim fixed pricing, you can (and should) ask for a discount — especially if you have leverage like a technical test showing outstanding issues. Expect small concessions (2–5%) rather than large discounts.

### Extracting data from Rebil pages
Rebil pages contain SSR JSON with the car data embedded. Extract with:

```bash
curl -sL 'https://app.rebil.no/cars/{car-id}' | grep -oP '"price":[0-9]+'
curl -sL 'https://app.rebil.no/cars/{car-id}' | grep -oP '"km":[0-9]+'
# Full JSON blob
curl -sL 'https://app.rebil.no/cars/{car-id}' | grep -oP '__NEXT_DATA__.*</script>' | sed 's/.*<script id="__NEXT_DATA__" type="application\/json">//;s/<\/script>.*//' | python3 -m json.tool 2>/dev/null || echo "JSON extraction failed, try browser"
```

Key fields in the SSR JSON: `price`, `km`, `year`, `horsepower`, `el_battery_capacity`, `el_rang`, `reg_number`, `chassis_number`, `exterior_color.name`, `equipment[]`, `guarantee_duration`, `warranty_type`.

### Interpreting a "Teknisk test med påkost" (technical inspection report)

Rebil provides a detailed technical test PDF on request (before it's published publicly). The report follows a standard format:

**Report structure:**
1. **Front page**: Car identity, test date, km at test, overall status (OK/IKKE OK)
2. **Anmerkninger (remarks) table**: Each issue numbered with:
   - **Punkt** (category — Eksteriør, Hjuloppheng/styring, Bremser, Interiør, etc.)
   - **Beskrivelse** (description of the issue)
   - **Plassering** (location)
   - **Påkost** (cost column — may be empty; indicates it was flagged for cost estimation)
3. **Bildedokumentasjon**: Photo evidence of each issue (pages 3–12 typically)
4. **Testforhold/Data**: Key numbers — nøkler, ladekabler, dekkdata (tread depth per wheel), klima test, servicehistorikk
5. **Punkter kontrollert**: The full checklist of what was inspected (helps identify gaps in the inspection)

**How to analyze the report:**
- **Check overall status first** — "OK" means no safety-critical issues
- **Categorize issues into tiers:**
  - 🟠 **Safety/mechanical** (must fix): front windshield cracks, suspension bushings, wheel bearings, brake components
  - 🟡 **Function** (should fix): door mechanisms, window regulators, lock mechanisms, door checks
  - 🟢 **Cosmetic** (nice to fix): scratches, dents, stone chips, alloy curb rash, interior wear
- **Cross-reference with what the dealer says they fixed** — ask explicitly which items from the report have been addressed
- **Prioritize cost**: front windshield replacement in Norway is ~8–15k, suspension arms/bushings ~3–8k, cosmetic bodywork varies widely (see references/cosmetic-repair-costs.md)

### Negotiation tactics — specific plays

**Before negotiating, know what you want to optimize for**: lowest cash price, most included repairs, or fastest secure-the-car. These trade off against each other.

**Good cop framing**: "Jeg er interessert og klar til å slå til — hjelp meg å komme i mål" works better than "jeg synes prisen er for høy".

**Bundle-strategi (mest effektiv)**: Kombiner rabatt + tilleggstjenester + reparasjoner i én forespørsel i stedet for å forhandle punktvis.

**Plays ranked by likelihood of success:**

1. **🔧 Få dem til å utbedre feil fra teknisk test** (mest sannsynlig)
   - De fleste forhandlere fikser mekaniske feil før salg uansett
   - Spesielt: rutebytte, understell, dørlåser
   - Si: "Jeg har sett testen — kan dere fikse punkt X og Y før levering?"

2. **💰 Rabatt** (mulig, men begrenset hos fixed-price)
   - 2-5 % typisk (5-12k på en 240k bil)
   - Over 5 % er sjeldent hos Rebil

3. **🧼 Tilleggstjenester** (lettest å få ja på)
   - Polering, bulkutbedring (PDR), nye dekk
   - Koster dem lite, føles verdifullt for deg

4. **📦 Bundle-eksempel**
   - "236.000 kr + polering + bulkfiks = vi har en avtale"
   - Får flere små ja i stedet for å forhandle hver ting separat

**Pitfalls in negotiation:**
- ❌ **Ikke overforhandle** etter en god deal. Hvis de har gitt 5-15k i verdi (rabatt + reparasjoner + tjenester), stopp. Hver ekstra runde øker risikoen for at noen trykker "kjøp" på nettsiden.
- ❌ **Ikke dra inn småting etter hverandre** — samle alt i én melding
- ❌ **Ikke sammenlign med privatsalg** — forhandlerpris inkluderer garanti, reklamasjon og overhead
- ✅ **Betinget kjøp**: "Kan vi signere kontrakt med forbehold om visuell sjekk?" — sikrer bilen mens du har handlingsrom

**EU-kontroll som punkt:**
- Bransjestandard: forhandler bør levere med ≥ 12 mnd gyldig kontroll
- Rebil og lignende tar den kun innen 3 mnd før salg
- Hvis nei: aksepter — kontroll koster ~1.000 kr

**Tidsaspekt**: Når den tekniske testen er publisert forsvinner info-asymmetrien din. Handle raskt etter at forhandleren har svart.

### Google search as first-pass Finn market technique

Google search with `site:finn.no` is a **reliable first-pass technique** for quick market price comparison — not just a last-resort fallback. It bypasses Finn's SPA entirely:

```bash
# Quick price check — Google returns 6-10 results with prices in snippets
# Navigate browser to:
https://www.google.com/search?q=site:finn.no+Tesla+Model+3+Long+Range+2021+pris
```

**What Google snippets give you** (from session data):
- Price (kr), km, year, key features, location
- Enough to spot the price range in 15 seconds

**Limitations:** ~6-10 results only (not comprehensive). Use JSON-LD when you need comprehensive data. Use Google when you need a quick answer.

**Follow-up workflow after Google:**
1. Google search → see price snapshots in results
2. Pick the most comparable ads (same year, similar km, same trim)
3. Open individual `/mobility/item/{id}` pages for full specs via browser_navigate or curl+grep
4. Build a comparison table for the user

### Tire data from technical inspection

The "Teknisk test med påkost" report includes tire condition data on its "Testforhold/Data" page:

```
VINTERDEKK PRODUKSJONSDATO DEKK: Uke 34, 2024
SOMMERDEKK PRODUKSJONSDATO DEKK: Uke 42, 2024

MØNSTERDYBDE (mm):
         Venstre  Høyre
Aksel 1    5,0     4,9    (summer)
Aksel 2    5,3     5,4
Aksel 1    6,3     7,2    (winter)
Aksel 2    4,6     4,8
```

**How to interpret:**
- **Production date**: "Uke 34, 2024" = week 34 of 2024. Under 3 years = good.
- **Tread depth**: Legal minimums — summer 3 mm, winter 5 mm. Above 5 mm summer / 6 mm winter = plenty of life. 4-5 mm = 1-2 more seasons. 3-4 mm = replace next season.
- **Mixed production dates**: "2 dekk er fra 2425" = partial replacement, not full set. Note this.
- **Asymmetric wear**: >1.5 mm difference left/right on same axle suggests alignment issues — cross-reference with suspension findings in the test report.

## Pitfalls
- Returning only model names without live listings when user asked to check FINN.
- Mixing lease campaign ads with purchase candidates.
- Over-trusting WLTP for winter route feasibility. Use model-specific NAF test data instead of generic 60-75% rule — Tesla 2021+ LR beholder ~84% av WLTP om vinteren, mens Enyaq/IONIQ 5 taper 25-35%.
- Ignoring user clarification that changes financing horizon (3y vs 5–8y materially changes budget).
- Over-negotiating after already getting a good deal. Hvis Rebil/dealer har gitt deg 5-15k i verdi totalt (rabatt + reparasjoner + tjenester), stopp. Hver ekstra runde øker risikoen for at noen trykker "kjøp" på nettsiden.
- Å be om EU-kontroll hos Rebil-type forhandlere: de tar den kun innen 3 mnd før salg. Ikke la et nei her bli en dealbreaker — den koster ~1.000 kr og bilen vil garantert passere.
- FINN.no is a fully client-side rendered SPA — browser navigation may timeout and curl returns no listing data. Never rely on HTML extraction from Finn.no without first verifying it still works in the current session.
- Individual FINN ad pages (`/mobility/item/{id}`) ARE extractable via curl+grep (see reference `finn-html-extraction-notes.md`). **Start with this approach when the user provides a specific URL** rather than trying browser_navigate.
- FINN's search API (`/mobility/search/api/car?subvertical=car&...`) exists but returns unreliable/unfiltered data — do not use it for extracting live listings. Rely on the JSON-LD method or individual ad-page extraction instead.
- When scraping fails, **do not fabricate listings**. Instead give market-informed model advice + direct search links the user can open.
- Long replies with repeated car details don't add value; keep the shortlist tight: per candidate = why it fits + one check-before-buy note. Avoid re-listing spec tables from the ad.
- Not all users share the same Norwegian dialect — some prefer **bokmål** (default), others nynorsk or English. Match user language.
- Rare car names like "E-TRON" in the ad title are not typos; let them pass through as-is.
- **Formidlingssalg oversight**: forgetting to check whether a listing is formidlingssalg can lead to wrong price expectations and legal assumptions. Always verify before giving a buy recommendation.
- **Price fairness without mileage context**: when comparing prices, kilometerstand is a primary price driver. JSON-LD gives price + description but not km — you MUST follow up with mileage data on comparables before concluding whether a price is fair.
- **Inconsistent spec data pitfall**: FINN's SSR data may have inaccurate or mismatched `car_model_spec` field. Always cross-check `engine_effect` (hk) and `battery_capacity` (kWh) against `car_model_spec` to verify trim level. For Tesla Model 3: 498hk+70kWh=LR AWD, 462hk+75kWh=some LR variants, 346hk+65kWh=SR+ (even if spec says "Long Range AWD"). Report mismatches to the user as a red flag.
- **Seller refuses NAF test**: If a seller (especially a dealer) declines a buyer-funded NAF test (or similar independent inspection), treat it as a strong negative signal. Legitimate sellers with nothing to hide have no reason to refuse. Flag this distinctly to the user — it may indicate hidden issues the seller knows about.

## Output template
- `Budsjett (beregnet): [range]`
- `Anbefalt drivlinje gitt lading: [reasoned choice]`
- `Aktuelle annonser:`
  - `Model, year, km`
  - `FINN link`
  - `Image`
  - `Why fit + what to verify`

## References
- See `references/finn-html-extraction-notes.md` for FINN extraction pattern and session-derived guardrails.
- See `references/automated-finn-monitoring.md` for setting up automated daily FINN monitoring with cron + here.now publishing.
- See `references/car-color-detection.md` for methods to determine exterior color from Norwegian car ads, including vegvesen lookup, ad text parsing, and image analysis. Also includes Tesla Model 3 facelift timeline.
- See `references/cosmetic-repair-costs.md` for estimated Norwegian body shop prices for common cosmetic issues (riper, bulk, steinsprut, felgmerker, interior wear, full packages).
- See `references/tesla-white-interior-care.md` for protecting Tesla vegan leather white/black seats — ceramic coatings, seat cover options, maintenance routines, and confirmed-safe products.
- See `references/tesla-subscription-pricing-norway.md` for Tesla software subscription prices (Premium Connectivity 129 kr/mnd, FSD 99 €/mnd), what's included on used vs new cars, and charging cost comparisons (home / Supercharger / petrol).
- See `references/vegvesen-registration-lookup.md` for looking up official specs (WLTP range, motor effect, VIN, colour) from Statens vegvesen via registration number — use this to verify FINN ad claims.
- See `references/tesla-model-3-beginner-guide.md` for a day-1 guide for new Tesla Model 3 owners: charging strategy, controls, Autopilot, maintenance, app features, and common questions.