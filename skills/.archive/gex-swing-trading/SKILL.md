---
name: gex-swing-trading
description: "Build and automate mechanical swing trading systems for single-stock options based on GEX (Gamma Exposure) and dealer positioning data. Covers data sourcing, screening, entry/exit logic, regime gates, and broker integration. Use when the user asks to build, automate, research, or improve a GEX-based swing trading system."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, options, gex, gamma, dealer-positioning, swing-trading]
    related_skills: [native-mcp]
---

# GEX Swing Trading Automation

## Overview

Mechanical swing trading systems for single-stock options that use Gamma Exposure (GEX) and dealer delta positioning to identify entries and manage exits. Core thesis: when dealer delta positioning flips bullish on a name with strong options structure, price tends to accelerate toward the next major gamma level (+GEX).

This skill covers the full pipeline: data sourcing → daily scanning → entry screening → position management → broker execution.

## When to Use

- User describes a GEX-based trading system (pTrans, nTrans, +GEX, gamma flip, dealer delta)
- User asks to build a scanner/screener for options trading based on dealer positioning
- User wants to automate evening scans or trade monitoring with cron
- User asks about data sources for GEX/DEX/options flow data
- User wants to connect a trading system to a broker API (Interactive Brokers, Saxo)
- User asks about backtesting GEX-based strategies

## Architecture Pattern

```
Data Source (e.g. FlashAlpha API)
    │
    ▼
Gamma Scanner ──► (700+ names) ──► CSV/JSON output
    │
    ▼
P2P Scanner ──► (filtered candidates) ──► Watchlist
    │
    ▼
Trade Executor ──► Broker API (IBKR) ──► Live trades
```

## Data Sources

### FlashAlpha (Recommended)
[https://flashalpha.com](https://flashalpha.com) — Real-time options analytics REST API for 6,000+ equities & ETFs + CME index futures.

**Key Endpoints for GEX Swing Trading:**

| Vol Desk Concept | FlashAlpha Endpoint | Field |
|---|---|---|
| Dealer delta balance | `/v1/exposure/dex/{symbol}` | `net_dex`, per-strike `net_dex` |
| Gamma exposure | `/v1/exposure/gex/{symbol}` | `net_gex`, per-strike `net_gex` |
| +GEX (max positive gamma) | `/v1/exposure/levels/{symbol}` | `levels.max_positive_gamma` |
| pTrans / gamma flip | `/v1/exposure/levels/{symbol}` | `levels.gamma_flip` |
| nTrans (max negative gamma) | `/v1/exposure/levels/{symbol}` | `levels.max_negative_gamma` |
| COTMC (call wall) | `/v1/exposure/levels/{symbol}` | `levels.call_wall` |
| COTMP (put wall) | `/v1/exposure/levels/{symbol}` | `levels.put_wall` |
| Summary (regime + GEX/DEX) | `/v1/exposure/summary/{symbol}` | `regime`, `exposures.*` |
| Full strike sheet | `/v1/exposure/sheet/{symbol}` | All exposures per strike |
| Screener (multi-symbol) | `POST /v1/screener` | Filter/sort/rank across symbols |

**Pricing Tiers:**
- Free: 5 req/day, single expiry GEX, 15-min freshness
- Basic ($63/mo): 100 req/day, ETFs/indexes, DEX/VEX/CHEX, 15-sec freshness
- Growth ($239/mo): 2,500 req/day, full-chain GEX, screener (20 symbols), flow analytics
- Alpha ($1,199/mo): Unlimited, screener (~250 symbols), historical replay since 2018

For scanning 700+ names, **Growth** or **Alpha** plan required.

### FlashAlpha MCP Integration
FlashAlpha publishes an MCP server at `https://lab.flashalpha.com/mcp` (API key) or `https://lab.flashalpha.com/mcp-oauth` (OAuth). Configure in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  flashalpha:
    url: "https://lab.flashalpha.com/mcp"
    headers:
      X-Api-Key: "your-api-key"
    timeout: 30
```

After restart, tools appear as `mcp_flashalpha_*` for agent use.

### Other Data Sources
- **GEXStream** (gexstream.com) — Real-time gamma exposure analytics
- **Open source**: `github.com/alexjust-data/gex-options-realtime` — FastAPI-based GEX calculator

## Common System Filter Rules

Most GEX swing trading systems share these filter categories:

1. **Structural Quality** — Grade score across N rules (call/put GEX ratios, OI depth, gamma positioning)
2. **Dealer Delta Change** — db_change = delta_balance_change from prior session. Catches names where dealer positioning is actively shifting.
3. **COTMP Cushion** — How far spot is above Center of Put Mass. Structural floor.
4. **Spike-Crash Pattern** — Block setups where +GEX target is a prior spike high where institutional selling already occurred.
5. **Risk/Reward (R/R)** — Upside to +GEX relative to downside to pTrans. Minimum 2:1 typical.
6. **Regime Gates** — Market-level filters before approving new entries (basket direction, bull:bear ratio, VIX positioning)

## Entry Mechanics

- Trigger is NOT the level or pre-market price — it's the **first 5-minute candle close above pTrans** at the open
- Pre-entry states: CONFIRMED (all filters pass, spot above pTrans), PENDING (within 0.5% below pTrans), BLOCKED (any filter failed)

## Position Management (Stops)

| Stop | Rule |
|---|---|
| Structural | Close below nTrans → exit at next open |
| Hard cap | -10% from entry while below pTrans → exit immediately |
| Time | Day 7 without 50% progress toward T1 → exit |
| Stalling | <10%/day progress for 3 consecutive sessions → exit |

T1 = +GEX level. At T1, either bank or lock stop to entry and ride toward T2.

## Broker API Integration for Norway

### Interactive Brokers (Recommended)
- **Python library**: `ib_insync` (pip installable) or official `ibapi` (TWS API)
- **Setup**: Run TWS Gateway or IB Gateway on the machine, enable API connections, configure port
- **Capabilities**: Stocks, options, futures, 170 markets in 40 countries
- **Docs**: [IBKR API Campus](https://www.interactivebrokers.com/campus/ibkr-api-page/ibkr-api-home/)
- **Order types**: All TWS order types, including advanced algos and extended hours

### Saxo Bank (Alternative)
- **API**: Saxo OpenAPI (REST)
- **Python SDK**: Available via community libraries
- **Capabilities**: Options, futures, stocks, forex
- **Danish bank** — strong European regulatory framework

## Pitfalls

- **Rate limits**: Free FlashAlpha tier (5/day) is unusable for scanning. Account for rate limits in scanner design. Batch requests and cache results.
- **Time zones**: GEX data refreshes during market hours only. Evening scans should run after market close (16:30 ET / 22:30 CET).
- **Terminology mismatch**: Different data providers use different names for levels. Map explicitly: gamma_flip ↔ pTrans, max_positive_gamma ↔ +GEX, put_wall ↔ COTMP, call_wall ↔ COTMC.
- **Pre-market trap**: Never enter on pre-market snapshots — the system requires a confirmed 5-min candle close at the open. Script the entry monitor separately from the daily scan.
- **Data freshness**: Free plan = 15-min delay. Near-live requires at least Basic ($63/mo). For entry triggers, 15-sec freshness (Basic+) is essential.
- **Screener vs per-symbol API**: The screener endpoint (POST /v1/screener) is more efficient for 20+ symbols than calling GEX/DEX/levels individually. On Alpha plan the screener covers ~250 symbols.
- **Historical backtesting**: Requires Alpha plan ($1,199/mo) or the Historical API replay feature.

## Verification Checklist

- [ ] FlashAlpha API key obtained and working (test with `curl -H "X-Api-Key: ..." https://lab.flashalpha.com/v1/exposure/summary/SPY`)
- [ ] Scanner script processes all names without hitting rate limits (track req/sec)
- [ ] pTrans → +GEX mapping verified against FlashAlpha levels endpoint
- [ ] R/R calculation uses correct levels (downside = spot - pTrans, upside = +GEX - spot)
- [ ] Regime gate data available (SPY/QQQ price, bull:bear ratio source, VIX DEX)
- [ ] Cron schedule set for after market close (e.g. 22:30 CET / 16:30 ET)
- [ ] IBKR Gateway running and accessible from the scanner machine
- [ ] Stop-loss orders tested on paper trading account before live
