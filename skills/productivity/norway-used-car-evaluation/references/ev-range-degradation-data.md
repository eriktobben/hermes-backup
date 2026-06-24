# EV range data & battery degradation research

## NAF real-world range tests — Tesla Model 3 LR AWD (2021)

**Chassis**: 2021 Model 3 Long Range AWD (reg. des. 2020)
**Battery**: 75 kWh NCA (original WLTP 580 km, OTA-upgraded to 614 km)
**Test method**: Mixed driving (city/land/motorway at speed limits), driven until car stops completely (incl. reserve below 0%)

| Test | WLTP | Measured | Deviation | Source |
|:----|:----:|:--------:|:---------:|:-------|
| NAF Sommer 2021 (20-25°C) | 614 km | **654,9 km** | +6,7 % | NTB/NAF pressemelding 08.06.2022 |
| NAF Vinter 2022 (~0°C, snø/is) | 614 km | **514,8 km** | −16,1 % | NTB/NAF pressemelding 08.06.2022 |
| NAF Vinter 2022 (andre publikasjon) | 580 km | **521 km** | −10,2 % | tv2.no/broom 01.02.2022 |

### Why NAF measures more than WLTP in summer

NAF's route includes city driving, country roads, and highways at posted speed limits — which is more efficient than WLTP's lab cycle in some conditions. Also, NAF drives until the car stops (including the buffer below 0%), adding 15-30 km compared to stopping at 0%.

### Classification
Tesla Model 3 LR AWD (2021) is one of only **4 out of 66 EVs tested** that exceed 500 km in BOTH summer and winter (alongside Mercedes EQS 580, BMW iX xDrive50, Ford Mustang Mach-E LR RWD).

## 2021 Model 3 LR AWD — 75 kWh vs 82 kWh battery variants

The 2021 Model 3 LR AWD was sold with **two different battery packs** depending on production date:

| Variant | Production | Battery | WLTP | OTA history |
|:--------|:-----------|:-------:|:----:|:------------|
| **Early 2021** | ~des 2020 – mai 2021 | 75 kWh LG NCA (opprinnelig) | 580 km → **614 km** (OTA update mai 2021) | Tesla unlocked extra capacity/efficiency via software |
| **Late 2021** | ~nov 2021 → | **82 kWh** Panasonic/LG NCA | **614 km** from factory | Full 614 km from day one |

### How to identify which one

| Method | 75 kWh (OTA upgrade) | 82 kWh |
|:-------|:--------------------:|:------:|
| **Rebil/FINN listing says** | "580 km (WLTP)" or "75 kWh" | "614 km (WLTP)" or "82 kWh" |
| **Vegvesen data shows** | Range may show 580 or 614 km | Range shows 614 km |
| **First registration** | Before ~May 2021 | After ~November 2021 |
| **Practical difference** | ~72,5 kWh usable → ~450-530 km real range | ~79 kWh usable → ~490-570 km real range |

**Important**: The 614 km WLTP upgrade was pushed as an OTA update to ALL 2021 LR AWD cars (including the 75 kWh ones) in May 2021. So seeing "614 km" in an ad does NOT guarantee 82 kWh — it could be the 75 kWh software-upgraded version. The only reliable ways to tell are:
1. Check the registration date — cars registered before May 2021 are almost certainly 75 kWh
2. Check the Rebil/FINN spec — "75 kWh" in the listing = 75 kWh regardless of stated WLTP
3. Read the actual battery capacity from the car's service menu during inspection

### What it means in practice
The 82 kWh version gives approximately **20-30 km more real-world range** at highway speeds. For daily driving the difference is negligible; for long journeys it means slightly more margin between Supercharger stops.

## Battery degradation references

### Recurrent Auto data (16.000+ vehicles)
- **Most Model 3 batteries maintain >94%** of original range after 3 years / 40.000-50.000 miles
- Initial degradation is steepest in year 1, then flattens
- Source: recurrentauto.com/questions/how-much-battery-degradation-should-i-expect-in-my-tesla-model-3

### Tesla 2023 Impact Report
- Average ~85 % retention at 200.000 miles (320.000 km)
- Confirms battery life well exceeds the 70% warranty threshold

### Tesla Battery Check (teslabatterycheck.com)
| Milage | Loss | Remaining |
|:-------|:----:|:---------:|
| First 50.000 miles (80.000 km) | 3–7 % | 93–97 % |
| 50.000-150.000 miles (80.000-240.000 km) | +3–5 % | 88–94 % |
| Beyond 150.000 miles (240.000 km) | +2–3 % | 85–90 % |

### Practical check during inspection — full charge method (preferred)
1. Charge to 100 %
2. Read estimated range from the Tesla UI (energy screen or range display)
3. Compare to original WLTP (for 2021 LR AWD: 580-614 km)
4. Rule of thumb: >90 % = green, 80-90 % = yellow, <80 % = possible warranty claim

### Partial-charge estimation technique (when seller hasn't fully charged)

Often the seller/biloppsynsperson only has access to the car at a partial charge (e.g. 35 %). The estimation is still useful:

1. Read the **battery percentage** and **estimated range** from the Tesla UI
2. Calculate: **Estimert rekkevidde ved 100 % = (range ÷ battery %) × 100**
3. Example: 35 % ladet → 172 km → 172 ÷ 0,35 = **491 km ved 100 %**

**Calibration caveat:** Tesla's BMS is most accurate at high SoC (80-100 %) or after a full charge cycle. At low/mid SoC, the estimate can be off by ~±5 %. The practical range window:

| Reading at 35 % | Tilsvarer ved 100 % | Sannsynlig faktisk range |
|:----------------|:-------------------:|:------------------------:|
| 172 km (optimistisk BMS) | ~491 km | ~475–485 km |
| 172 km (nøytral BMS) | ~491 km | ~491 km |
| 172 km (pessimistisk BMS) | ~491 km | ~500–510 km |

**For 2021 Model 3 LR AWD (75 kWh):**
- EPA baseline new: ~499-518 km ved 100 % (dette er hva Tesla-skjermen viser, IKKE WLTP)
- WLTP: 580-614 km (mer optimistisk lab-tall, ikke direkte sammenlignbart)
- Forventet ved 111.600 km: 490-510 km → ~3-10 % degradering 🟢

**Konklusjon:** Ved 35 % lading og 172 km visning er batteriet **meget bra** (~3 % degradering). Ingen grunn til bekymring selv om BMS ikke er perfekt kalibrert på lav ladning.

### Sendbar sjekkliste for tredjeparts inspeksjon
Når en annen person (familiemedlem, bekjent) skal sjekke batteriet for deg:

```
SJEKK BATERIHELSE — Tesla Model 3

1. Sett deg i bilen, se på displayet — noter batteri % og km
2. Regn ut: km ÷ prosent × 100 = estimert rekkevidde ved fullt batteri
3. For 2021 LR AWD: forvent 490-510 km (🟢 bra)
4. Hvis mulig: lad til 100% og les av direkte
5. Sjekk at batterigaranti gjelder (8 år / 192.000 km)
6. Alt over 475 km estimert range ved 100% = 💚
```
