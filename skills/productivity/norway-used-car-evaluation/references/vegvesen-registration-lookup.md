# Norwegian registration lookup — Statens vegvesen

When you need to verify a car's specs (battery size, official WLTP range, motor effect, first registration date, VIN, owners), use Statens vegvesen's free lookup service. This is **essential for used car evaluation** because FINN ads often omit or misreport battery capacity, drivetrain, colour, and production date.

## Quick URL

```
https://www.vegvesen.no/kjoretoy/kjop-og-salg/kjoretoyopplysninger/sjekk-kjoretoyopplysninger?registreringsnummer=ABC12345
```

Replace `ABC12345` with the actual registration number (spaces optional).

## Data you can extract

The page returns sections that expand on click via browser_click. Use browser_navigate to load, then browser_click on the section buttons:

| Section | How to expand | Key data points |
|:--------|:--------------|:----------------|
| **Registreringsdata** | Click button (ref from snapshot) | VIN (understellsnr), first registration date, colour, seats, top speed |
| **Motor/kraftoverføring** | Click button | **Elektrisk rekkevidde** (official WLTP), motor count, effect per motor (kW), AWD status |
| **EU-kontroll** | Click button | Next EU control deadline, status |
| **Eieropplysninger** | Click button | Owner history (login for full names) |
| **Mål og vekt** | Click button | Curb weight, total weight, trailer capacity |
| **Kilometerstand** | Click button | Recorded km from EU inspections |

## Why use this

FINN ads often lack or misreport battery capacity, WLTP range, drivetrain, and colour. The vegvesen register is **the authoritative source** — it's what the car was type-approved with.

| Verification use case | Why it matters |
|:----------------------|:---------------|
| **Battery vs WLTP** | The "Elektrisk rekkevidde" field shows the official homologated WLTP — confirms whether a 2021 Model 3 LR is 580 km (75 kWh) or 614 km (82 kWh) |
| **Motor effect** | Confirms trim level (e.g. 158+208 kW = 366 kW total = LR AWD, not SR/SR+ with 208 kW single motor) |
| **First registration** | Mid-2021 registration? Likely 82 kWh battery. Late 2020? Likely 75 kWh. |
| **Colour** | Not always in FINN ad text — vegvesen has it |
| **VIN** | Useful for warranty checks (Tesla SC lookup) and Carfax-style checks |
| **AWD vs RWD** | Motor count tells you directly |

## Limitation

- **Avregistrerte biler** (deregistered — the dealer has taken it off the road) still show all technical data but owner history requires login
- The page **requires cookies** (Cookiebot) — the browser tool works, curl does not work well
- Rate-limited to ~50 lookups/hour from one IP
