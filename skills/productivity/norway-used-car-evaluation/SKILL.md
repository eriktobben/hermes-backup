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

## Core outcomes
1. Convert monthly payment + down payment + term into a realistic car-price range.
2. Explain EV vs petrol/hybrid tradeoffs for the user’s charging reality.
3. Return a shortlist of concrete listings with direct links and image URLs.

## Workflow
1. **Collect minimum decision inputs**
   - km/month or km/year
   - loan-only vs total-cost budget
   - ownership horizon (years)
   - home charging availability
   - transmission requirement
   - size/use constraints
   - mechanical reliability preferences (timing chain vs belt, hybrid complexity fears)

2. **Compute affordability envelope (always calculate, don't eyeball)**
   - Use amortized loan PV formula across plausible interest band (e.g., 4–10%).
   - Add user down payment.
   - Reserve a buffer for fees/registration before setting target listing price.
   - Example: 50k down + 1500 kr/mnd at 7% over 5y ≈ 70k loan → ~120k total budget

3. **Decision framing**
   - If no home charging: explicitly warn that EV fast-charging can erase fuel-cost advantage vs a cheap petrol car used mostly for short trips. However, note that 5-10 km daily city driving on an EV still beats petrol on running cost.
   - If user requests long winter intercity EV legs with limited charging stops: require extra real-world range margin vs WLTP. Rule of thumb: expect 60-75% of WLTP in winter. Kristiansand–Oslo (320 km) needs a car with at least 400 km WLTP for comfortable one-stop winter driving.
   - For petrol constraint questions (timing chain vs belt): note that a recently replaced timing belt is a *positive*, not a negative — document the replacement interval and cost as a sjekkpunkt rather than a hard filter.
   - For hybrid skepticism: the user's logic (two drivetrains = two failure modes) is valid for high-mileage used cars. Flag this tradeoff honestly.
   - Elbil without home charging is viable IF the user can fast-charge weekly for city use, and the car has ≥ 100 kW CCS for efficient highway charging.

4. **Pull live market examples (FINN) — with fallback**
   - **If user provides a specific FINN URL**: extract via curl+grep from the individual ad page (`/mobility/item/{id}`). The page contains SSR data with price, km, year, battery, etc. embedded in the HTML — see `references/finn-html-extraction-notes.md` for exact grep patterns. Much faster than browser_navigate.
   - **If user asks for search results**: attempt FINN extraction via browser navigation. If it times out (>60s common), **do not fabricate listings**.
   - Fallback: provide market-informed model advice with known price ranges (e.g., "Kona Electric 64 kWh 2019: 115-135k for 70k km") and clickable search URLs the user can open.
   - Include `https://www.finn.no/car/used/search.html?fuel=2&make=65&model=2391&price_to=150000&transmission=1` style links — use proper query parameters (fuel=2=EV, transmission=1=automatic).

5. **Present shortlist clearly**
   - Group by powertrain (hybrid/petrol/EV).
   - Include why each candidate fits, plus one "check before buy" note per car.
   - Keep it tight: avoid reprinting the spec table from the ad.
   - In Norwegian, use consistent bokmål spelling.

## Pitfalls
- Returning only model names without live listings when user asked to check FINN.
- Mixing lease campaign ads with purchase candidates.
- Over-trusting WLTP for winter route feasibility (real-world winter range is 60-75% of WLTP depending on model and temperature).
- Ignoring user clarification that changes financing horizon (3y vs 5–8y materially changes budget).
- FINN.no is a fully client-side rendered SPA — browser navigation may timeout and curl returns no listing data. Never rely on HTML extraction from Finn.no without first verifying it still works in the current session.
- Individual FINN ad pages (`/mobility/item/{id}`) ARE extractable via curl+grep (see reference `finn-html-extraction-notes.md`). **Start with this approach when the user provides a specific URL** rather than trying browser_navigate.
- FINN's search API (`/mobility/search/api/car?subvertical=car&...`) exists but returns unreliable/unfiltered data — do not use it for extracting live listings. Rely on the HTML/fetch fallback instead.
- When scraping fails, **do not fabricate listings**. Instead give market-informed model advice + direct search links the user can open.
- Long replies with repeated car details don't add value; keep the shortlist tight: per candidate = why it fits + one check-before-buy note. Avoid re-listing spec tables from the ad.
- Not all users share the same Norwegian dialect — some prefer **bokmål** (default), others nynorsk or English. Match user language.
- Rare car names like "E-TRON" in the ad title are not typos; let them pass through as-is.

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