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

## Pitfalls
- Returning only model names without live listings when user asked to check FINN.
- Mixing lease campaign ads with purchase candidates.
- Over-trusting WLTP for winter route feasibility (real-world winter range is 60-75% of WLTP depending on model and temperature).
- Ignoring user clarification that changes financing horizon (3y vs 5–8y materially changes budget).
- FINN.no is a fully client-side rendered SPA — browser navigation may timeout and curl returns no listing data. Never rely on HTML extraction from Finn.no without first verifying it still works in the current session.
- Individual FINN ad pages (`/mobility/item/{id}`) ARE extractable via curl+grep (see reference `finn-html-extraction-notes.md`). **Start with this approach when the user provides a specific URL** rather than trying browser_navigate.
- FINN's search API (`/mobility/search/api/car?subvertical=car&...`) exists but returns unreliable/unfiltered data — do not use it for extracting live listings. Rely on the JSON-LD method or individual ad-page extraction instead.
- When scraping fails, **do not fabricate listings**. Instead give market-informed model advice + direct search links the user can open.
- Long replies with repeated car details don't add value; keep the shortlist tight: per candidate = why it fits + one check-before-buy note. Avoid re-listing spec tables from the ad.
- Not all users share the same Norwegian dialect — some prefer **bokmål** (default), others nynorsk or English. Match user language.
- Rare car names like "E-TRON" in the ad title are not typos; let them pass through as-is.
- **Formidlingssalg oversight**: forgetting to check whether a listing is formidlingssalg can lead to wrong price expectations and legal assumptions. Always verify before giving a buy recommendation.
- **Price fairness without mileage context**: when comparing prices, kilometerstand is a primary price driver. JSON-LD gives price + description but not km — you MUST follow up with mileage data on comparables before concluding whether a price is fair.

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