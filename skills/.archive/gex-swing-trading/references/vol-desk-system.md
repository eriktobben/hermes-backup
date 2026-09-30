# Vol Desk System Rules

*Reference for Tobben's mechanical swing trading system. Load this reference when working on the Vol Desk scanner, P2P screener, or trade executor.*

## Core Thesis

When dealer delta positioning flips bullish on a name with strong options structure, price tends to accelerate toward the next major gamma level — the +GEX. Enter just above pTrans and ride to +GEX as T1.

## Daily Scans

### Gamma Screen (Master File)
700+ names with per-symbol:
- Dealer delta balance (current + prior session delta)
- Grade across 11 structural rules
- OI depth
- Minervini momentum score
- Key GEX levels: pTrans, nTrans, zeroGEX, +GEX, COTMP, COTMC

### P2P Scan (pTrans to +GEX)
Filtered subset where spot has crossed above pTrans. Shows R/R and cushion to +GEX target.

## Five Entry Filters (ALL required)

| # | Filter | Threshold | Exception |
|---|--------|-----------|-----------|
| 1 | Grade | ≥ 9/11 | Grade ≤ 8 = hard block, no exceptions |
| 2 | db_change | ≥ 0.50 | Grade 11 DEEP: ≥ 0.30. Sustained (delta at 1.00 for 2 sessions): exempt |
| 3 | COTMP cushion | ≥ 2.0% | Grade 11 DEEP or high db_change: ≥ 1.0% |
| 4 | Spike-crash pattern | Must NOT exist | 0/3 win rate on validated data. Hard no. |
| 5 | R/R | ≥ 2.0 | Minimum 2:1 upside to +GEX vs downside to pTrans |

## Entry States

| State | Condition |
|---|---|
| CONFIRMED | All filters pass, spot above pTrans, greenlit at open |
| PENDING | Within 0.5% below pTrans, watching first candle |
| BLOCKED | Any filter failed |

**Trigger**: First 5-minute candle close above pTrans at the open. NOT pre-market, NOT crossed the level — must be a confirmed 5-min close.

## Position Management (Stops)

| Stop | Rule |
|---|---|
| S1 — nTrans | Close below nTrans → exit at next open |
| S2 — Hard cap | −10% from entry while below pTrans → immediate exit |
| S3 — Time stop | Day 7 without ≥50% progress toward T1 → exit |
| S4 — Stalling | <10%/day progress for 3 consecutive sessions → exit |

### State While in Position
- **CONFIRMED**: Above pTrans, not yet at target → hold
- **WATCH**: Below pTrans but above nTrans → hold existing, add nothing

## Taking Profit
- **T1** = +GEX level
- Two choices at T1: (a) exit and bank, or (b) lock stop to entry and ride toward T2
- Cannot hold T2 without first locking T1

## Regime Gates (Daily, before new entries)

| Gate | Condition |
|---|---|
| Basket | SPY or QQQ up >0.5% on session |
| Bull:Bear | >3.0:1 bull:bear names in full 700-name universe |
| VIX delta | Dealer positioning on VIX must be negative (bearish vol = bullish equities) |

- **P2P Track 1** (mechanical): Can run at 2/3 gates on strong setups
- **B Continuation**: Requires full 3/3 gates
- Daily checks on HYG and sector ETF positioning as credit/rotation overlay

## B Continuation Bucket

Names in confirmed uptrends pulling back into or breaking above a GEX level. Different thesis — trend continuation, not pTrans break. Requires:
- Minervini score ≥ 100
- Clean staircase structure
- Dealer positioning supporting continuation
- Full 3/3 regime gates
- Same stop framework as P2P

## Validated Edge (First 2 Weeks)
- db_change ≥ 0.50 on entry → **100% win rate** on closed trades
- Spike-crash pattern → **0% win rate**
