---
name: competitive-analysis
description: Analyze a competitor's website/product to extract their value proposition, identify strengths/weaknesses, and generate differentiation strategies. Use when the user wants to understand a competitor, find gaps in the market, or plan how to outperform an existing solution.
tags: [research, strategy, b2b, startup, differentiation]
---

# Competitive Analysis

Systematic framework for analyzing competitors and generating actionable differentiation strategies.

## Workflow

### Phase 1: Competitor Reconnaissance

1. **Navigate the competitor site** with browser tools — visit homepage, "how it works", pricing, product pages, and target audience pages
2. **Extract core elements:**
   - Value proposition (what they promise)
   - Target audience (who they serve)
   - Pricing model (how they charge)
   - Onboarding flow (sign-up process)
   - Feature set (what's included)
   - Integrations (what they connect to)
3. **Use curl + Python** to scrape page content when browser snapshots are truncated by heavy nav menus:
   ```bash
   curl -sL URL | python3 -c "
   import sys, re
   html = sys.stdin.read()
   html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
   html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
   text = re.sub(r'<[^>]+>', ' ', html)
   text = re.sub(r'\s+', ' ', text).strip()
   print(text[:5000])
   "
   ```
4. **Check structured data** (JSON-LD) for company info:
   ```bash
   curl -sL URL | python3 -c "
   import sys, re
   html = sys.stdin.read()
   json_ld = re.findall(r'<script[^>]*type=\"application/ld\+json\"[^>]*>(.*?)</script>', html, re.DOTALL)
   for j in json_ld: print(j[:3000])
   "
   ```

### Phase 2: Strength/Weakness Mapping

Map findings across these dimensions:

| Dimension | Questions to answer |
|-----------|-------------------|
| **Target audience** | Who do they serve? What size companies? What industries? |
| **Value proposition** | What's their core promise? What pain do they solve? |
| **Pricing** | Model (subscription/usage/flat), tiers, hidden costs |
| **Onboarding** | Self-serve vs. sales-assisted? Speed to value? |
| **Feature depth** | Core features vs. nice-to-haves? What's missing? |
| **Integrations** | What ecosystem do they plug into? What's missing? |
| **Trust signals** | Reviews, case studies, customer count, certifications |
| **Geography** | Local vs. international? Language support? |

### Phase 3: Gap Analysis

For each dimension, identify:
- **What they do well** (defend against or match)
- **What they don't do** (differentiation opportunity)
- **What they do poorly** (exploitable weakness)
- **What they could do but haven't** (first-mover advantage)

### Phase 4: Differentiation Strategy

Generate strategies across these categories:

1. **Audience narrowcasting** — serve a specific segment better than they serve everyone
2. **Workflow integration** — connect to tools the competitor ignores
3. **Self-serve automation** — remove human touchpoints the competitor requires
4. **Pricing innovation** — different model, more transparency, better unit economics
5. **Bundle/packaging** — combine what competitor sells separately (or vice versa)
6. **Local advantage** — language, compliance, payment methods, support hours
7. **Feature gap** — build what they don't have (prioritize by customer pain)
8. **Trust/transparency** — be more open about pricing, process, or metrics

### Phase 5: Prioritization

Rank differentiation strategies by:
- **Impact** — how much does this move the needle for target customers?
- **Feasibility** — how hard is this to build/deliver?
- **Defensibility** — can the competitor easily copy this?
- **Speed** — how fast can we ship this?

## Output Format

Structure the analysis as:
1. **Competitor snapshot** (what they do, who they serve)
2. **Strengths** (what they're good at)
3. **Weaknesses/gaps** (exploitable opportunities)
4. **Differentiation strategies** (ranked by impact × feasibility)
5. **Recommended start focus** (top 3-4 things to build first)

## Pitfalls

- **Don't just list features** — focus on the *why* behind customer choices
- **Watch for Swedish/Norwegian market differences** — payment methods, compliance (GDPR, Bokføringslov), trust signals differ
- **Check Trustpilot/Google reviews** for real customer complaints — these are the best gap signals
- **Don't assume their pricing is their weakness** — often it's process, integrations, or support
- **B2B vs B2C framing matters** — a "self-serve" B2B product still needs team management, invoicing, and admin features that B2C doesn't
