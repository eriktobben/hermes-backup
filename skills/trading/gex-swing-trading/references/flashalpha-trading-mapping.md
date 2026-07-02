# FlashAlpha API ↔ Vol Desk System Mapping

*How Vol Desk concepts map to FlashAlpha API fields. Use this reference when building scanner scripts or verifying data alignment.*

## Level Mappings

| Vol Desk Term | FlashAlpha Endpoint | Field Path | Notes |
|---|---|---|---|
| pTrans (positive transition) | `/v1/exposure/levels/{symbol}` | `levels.gamma_flip` | Strike where net GEX crosses zero to positive |
| nTrans (negative transition) | `/v1/exposure/levels/{symbol}` | `levels.max_negative_gamma` | Strike with most negative GEX |
| zeroGEX | `/v1/exposure/levels/{symbol}` | `levels.gamma_flip` | Same as gamma flip — where net GEX = 0 |
| +GEX (target) | `/v1/exposure/levels/{symbol}` | `levels.max_positive_gamma` | Strike with highest positive GEX |
| COTMP (Center of Put Mass) | `/v1/exposure/levels/{symbol}` | `levels.put_wall` | Strike with highest put GEX concentration |
| COTMC (Center of Call Mass) | `/v1/exposure/levels/{symbol}` | `levels.call_wall` | Strike with highest call GEX concentration |

## Dealer Delta / Balance

| Vol Desk Concept | FlashAlpha Endpoint | Field Path |
|---|---|---|
| Current dealer delta balance | `/v1/exposure/dex/{symbol}` | `net_dex` (aggregate), per-strike `net_dex` |
| Prior session delta | Compute from historical cache or `/v1/exposure/dex/{symbol}` stored daily | Store in local DB for db_change calc |
| db_change | Computed | `current_net_dex - prior_net_dex` (normalized recommended) |

The DEX endpoint returns `net_dex` — aggregate net dealer delta exposure. For db_change, store `net_dex` daily and compute the delta each session.

## Gamma Data

| Vol Desk Concept | FlashAlpha Endpoint | Field Path |
|---|---|---|
| Net gamma exposure | `/v1/exposure/gex/{symbol}` | `net_gex` |
| Per-strike GEX | `/v1/exposure/gex/{symbol}` | `strikes[].net_gex` |
| Gamma regime | `/v1/exposure/summary/{symbol}` | `regime` ("positive_gamma" or "negative_gamma") |

## Screener for Multi-Symbol Scans

For scanning 700+ names, the screener endpoint (`POST /v1/screener`) is more efficient on Growth+ plans than calling individual endpoints per symbol.

**Available screener fields relevant to GEX trading** (Growth plan, 20 symbols):
- `symbol`, `price`, `regime`, `net_gex`, `net_dex` — stock-level exposure
- `gamma_flip` — the flip level
- `atm_iv` — at-the-money implied volatility

**Limitations**: The Growth screener covers 20 symbols. For 700+ names, batch calls to per-symbol endpoints or Alpha plan (~250 symbols) needed.

## Rate Limit Budgeting

For scanning ~700 names per evening:

| Endpoint Type | Calls per Name | Total Calls Needed | Free (5) | Basic (100) | Growth (2500) | Alpha (∞) |
|---|---|---|---|---|---|---|
| Summary only | 1 | ~700 | ❌ | ❌ | ✅ | ✅ |
| Summary + Levels | 2 | ~1400 | ❌ | ❌ | ✅ | ✅ |
| Summary + Levels + DEX | 3 | ~2100 | ❌ | ❌ | ✅ | ✅ |
| Full (all 3 + Sheet) | 4 | ~2800 | ❌ | ❌ | ❌ | ✅ |

Growth plan (2500/day): sufficient for 2-3 endpoints per name on a ~700-name universe.

## API Response Shape Examples

### GEX Response
```json
{
  "symbol": "SPY",
  "net_gex": -2847392,
  "gamma_flip": 582.50,
  "net_gex_label": "negative",
  "strikes": [
    { "strike": 580, "net_gex": -941820 },
    { "strike": 585, "net_gex": -723401 },
    { "strike": 590, "net_gex": 412093 }
  ],
  "as_of": "2026-03-11T16:22:47Z"
}
```

### Levels Response
```json
{
  "symbol": "SPY",
  "underlying_price": 597.505,
  "as_of": "2026-02-28T16:30:45Z",
  "levels": {
    "gamma_flip": 595.25,
    "max_positive_gamma": 600.0,
    "max_negative_gamma": 585.0,
    "call_wall": 600.0,
    "put_wall": 595.0,
    "highest_oi_strike": 600.0,
    "zero_dte_magnet": 598.0
  }
}
```

### Summary Response
```json
{
  "symbol": "SPY",
  "underlying_price": 597.505,
  "as_of": "2026-02-28T16:30:45Z",
  "gamma_flip": 595.25,
  "regime": "positive_gamma",
  "exposures": {
    "net_gex": 2850000000,
    "net_dex": -450000000,
    "net_vex": 1200000000,
    "net_chex": 850000000
  },
  "hedging_estimate": {
    "spot_down_1pct": {
      "dealer_shares_to_trade": 4780000,
      "direction": "BUY",
      "notional_usd": 2852000000
    },
    "spot_up_1pct": {
      "dealer_shares_to_trade": -4780000,
      "direction": "SELL",
      "notional_usd": 2852000000
    }
  }
}
```
