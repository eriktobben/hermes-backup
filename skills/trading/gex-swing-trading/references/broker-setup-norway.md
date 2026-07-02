# Broker API Setup for Norwegian Traders

*How to connect automated GEX swing trading to a live brokerage from Norway.*

## Recommended: Interactive Brokers (IBKR)

IBKR is the gold standard for algorithmic options trading globally. Fully available for Norwegian residents.

### Account Setup
1. Open an **Individual or Joint account** at [interactivebrokers.com](https://www.interactivebrokers.com)
2. Choose account type that supports options trading (IBKR Pro recommended for API access)
3. Complete verification (passport, address proof — standard for Norwegian residents)
4. Fund the account (SEPA/wire transfer from Norwegian bank)
5. Apply for options trading permissions (level appropriate for your strategy)

### API Setup

**Option 1: TWS API (Python — recommended)**
1. Install **Trader Workstation (TWS)** or **IB Gateway** on the machine
2. Enable API connections in TWS: `File → Global Configuration → API → Settings`
   - Enable "Enable ActiveX and Socket Clients"
   - Set port (default: 7496 for TWS live, 7497 for TWS paper)
   - Check "Allow connections from localhost only"
3. Install Python library:
   ```bash
   pip install ib_insync
   ```
4. Connection code:
   ```python
   from ib_insync import IB
   ib = IB()
   ib.connect('127.0.0.1', 7497, clientId=1)  # Paper trading port
   ```

**Option 2: IBKR Web API (REST)**
- Modern REST API with OAuth/SSO auth
- Broader capabilities (account management, reporting in addition to trading)
- Python SDK available via [ibkr-api](https://www.interactivebrokers.com/campus/ibkr-api-page/web-api/)

### Paper Trading
- Use **IBKR Paper Trading Account** (separate login from live)
- TWS Paper port: 7497
- Test all entry/exit logic in paper before going live
- Paper account simulates real market conditions

### Options Trading from Norway — Key Considerations
- **Tax**: Norwegian residents report capital gains to Skatteetaten. Options profits are taxable as capital income (22% in 2025). Keep detailed trade logs.
- **Settlement**: USD-denominated account — currency conversion from NOK to USD via IBKR's competitive FX rates
- **Regulatory**: IBKR is authorized by the FCA (UK) and regulated internationally — fine for Norwegian residents
- **KYC**: Standard identity and source-of-wealth verification

## Alternative: Saxo Bank

Danish bank with strong European presence. Available for Norwegian residents.

### Saxo OpenAPI
- REST API with streaming endpoints
- Supports options, futures, stocks, forex
- Rate limits apply — check Saxo OpenAPI documentation
- Community Python SDK: `saxo-py` or build with `requests`

### Pros & Cons vs IBKR
- **Pro**: Norwegian bank relationship, EUR-denominated accounts easier
- **Pro**: Simpler API authentication (OAuth 2.0)
- **Con**: More limited options chain data in API
- **Con**: Smaller algorithmic trading community than IBKR

## Architecture for Auto-Trading

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Scanner     │────▶│  Decision    │────▶│  Executor    │
│  (evening)   │     │  Engine      │     │  (morning)   │
└──────────────┘     └──────────────┘     └──────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌──────────────┐
                    │  Position    │     │  IBKR        │
                    │  Tracker     │     │  Gateway     │
                    └──────────────┘     └──────────────┘
```

1. **Evening scanner** runs after market close, screens 700+ names, outputs watchlist
2. **Decision engine** runs at open, checks 5-min candle close above pTrans
3. **Executor** sends entry/exit orders to IBKR Gateway
4. **Position tracker** monitors stops (daily check via cron)

## Security
- **NEVER** store API credentials in scripts committed to git
- Use environment variables or a vault (e.g., `~/.hermes/secrets/`)
- IBKR Gateway supports IP whitelisting — limit to localhost
- Run trades through paper account first (minimum 1 week of paper trading recommended)
