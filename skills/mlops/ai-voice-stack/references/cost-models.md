# AI Voice Stack Cost Models

## Per-Minute Cost Breakdown (BYOK)

| Component | Provider | Cost/min |
|-----------|----------|----------|
| Orchestration | Retell.ai | $0.07 |
| STT | Deepgram Nova-3 | $0.005 |
| LLM | GPT-4o-mini | $0.01 |
| TTS | Cartesia Sonic | $0.04 |
| Telephony | Twilio Norway | $0.03 |
| **Total** | | **~$0.155/min** |

## Per-Customer Monthly Cost (200 calls × 2 min avg = 400 min)

| Item | Cost |
|------|------|
| Infrastructure (400 × $0.155) | ~$62 (~650 kr) |
| Support (1-2 hrs/mo) | ~200 kr |
| **Total COGS** | **~850 kr/mo** |

## Pricing Tiers (Norwegian market)

| Tier | Price | Calls | COGS | Margin |
|------|-------|-------|------|--------|
| Start | 990 kr/mo | 50 | ~130 kr | ~87% |
| Pro | 2,490 kr/mo | 200 | ~850 kr | ~66% |
| Business | 4,990 kr/mo | 400 | ~1,700 kr | ~66% |

Overage pricing: 10-15 kr/call (COGS ~8 kr/call = 20-47% margin on overage)

## Revenue Scaling

| Customers | Revenue/mo | COGS/mo | Support | Result |
|-----------|------------|---------|---------|--------|
| 10 | 14,900 kr | 8,500 kr | 2,000 kr | 4,400 kr |
| 50 | 74,500 kr | 42,500 kr | 10,000 kr | 22,000 kr |
| 200 | 298,000 kr | 170,000 kr | 30,000 kr | 98,000 kr |

## Key Metrics

- **CAC:** ~500-2,000 kr (marketing)
- **LTV:** 990 × 12 × 75% margin = ~8,910 kr
- **LTV/CAC:** 4-18x
- **Break-even:** 15-20 customers
- **Time to positive cashflow:** 2-3 months

## Norwegian-Specific Cost Considerations

- Norwegian telephony is 2-3× US rates (Twilio: $0.03/min outbound vs $0.01 in US)
- SMS costs: 46elks (~€0.02/msg) vs Twilio ($0.07/msg) — 3.5× savings with 46elks
- Support in Norwegian requires native speakers — budget higher than English support
- VAT (MVA) at 25% applies to B2C sales in Norway
