---
name: content-monitoring
description: "Monitor external content sources for updates — RSS/Atom feeds via blogwatcher-cli, classified marketplace listings with dedup/filtering, and e-commerce price-drop watchdog scripts. Covers setup, scheduling, and cron delivery patterns for all three."
tags: [monitoring, rss, blogs, classifieds, alerts, cron, web-scraping, price-tracking]
platforms: [linux, macos, windows]
related_skills: [cronjob]
---

# Content Monitoring

Automatically monitor external content sources — RSS feeds, classified marketplaces,
and e-commerce product pages — and get notified about changes or new items.

## When to use

- User wants to track blog or RSS feed updates
- User wants daily/hourly alerts for new classified listings (cars, housing, gear)
- User wants to know when a specific product goes on sale ("varsle når prisen faller")
- User wants to set up cron-driven watchdog scripts
- User asks about content monitoring, alert workflows, or periodic content checks

---

## § RSS/Feed Monitoring with blogwatcher-cli

Track blog and RSS/Atom feed updates using the `blogwatcher-cli` tool. Supports
automatic feed discovery, HTML scraping fallback, OPML import, and read/unread management.

### Installation

```bash
# Go
go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest

# Binary (Linux amd64)
curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli

# macOS
curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli
```

### Managing Blogs

```bash
blogwatcher-cli add "My Blog" https://example.com
blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml
blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"
blogwatcher-cli import subscriptions.opml
blogwatcher-cli blogs
blogwatcher-cli remove "My Blog" --yes
```

### Scanning & Reading

```bash
blogwatcher-cli scan
blogwatcher-cli scan "My Blog"
blogwatcher-cli articles
blogwatcher-cli articles --all
blogwatcher-cli articles --blog "My Blog"
blogwatcher-cli read 1
blogwatcher-cli read-all
```

### Environment Variables

All flags via `BLOGWATCHER_` prefix: `BLOGWATCHER_DB`, `BLOGWATCHER_WORKERS`,
`BLOGWATCHER_SILENT`, `BLOGWATCHER_YES`, `BLOGWATCHER_CATEGORY`.

### Docker

```bash
docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan
```

### Notes

- Auto-discovers RSS/Atom feeds from blog homepages
- Falls back to HTML scraping if RSS fails and `--scrape-selector` is configured
- Database at `~/.blogwatcher-cli/blogwatcher-cli.db` by default

---

## § Classified Marketplace Alerts

Build durable daily/periodic alerts for classified marketplaces (cars, housing, gear)
with deduping, budget math, and media-rich notifications.

### When to use

- User wants ongoing alerts for new listings matching constraints (price, fuel type, location)
- User wants alerts delivered on schedule with links/images and computed metrics
- Official API may be unavailable, so a fallback strategy is needed

### Outcome

A cron-driven alert job that:
1. Pulls fresh listings from a stable source (API first, web fallback)
2. Filters against user constraints
3. Dedupes using persisted `seen` IDs
4. Enriches records (e.g., listing price from detail page JSON-LD)
5. Computes user-specific finance estimates
6. Sends message only when there are new matches (silent otherwise)

### Standard Workflow

1. **Confirm constraints** — hard filters, text filters, finance assumptions
2. **Try official API first** — if API key unavailable, ask or fall back to web
3. **Implement script** under `~/.hermes/scripts/` — deterministic, idempotent
4. **Persist state** in `~/.hermes/cron/state/<job>_seen.json`
5. **Compute monthly loan estimate** using annuity formula
6. **Cron delivery** — prefer `cronjob(create, no_agent=true, script=...)` for watchdog-style

### Message Format

For each new listing include:
- Title + classification tag
- Price
- Monthly estimates (5/7/8 years)
- Compact metadata (year, km, fuel)
- Listing URL + image markdown

### Pitfalls

- Marketplace search pages mix leasing with sale content — explicitly exclude leasing keywords
- Detail page JSON-LD is more reliable than search snippets for actual price
- Cap per-run items (first 10-15) and summarize remaining count
- First run should seed state to avoid flooding historical matches

### FINN.no Specific Patterns

See `references/finn-no-pattern.md` for FINN-specific API/auth and parsing patterns
used for Norwegian car alerts.

---

## § E-Commerce Price Drop Alerts

Monitor a specific product page for price reductions and notify only when
a sale or discount appears. Ideal for Norwegian e-commerce stores (begood.no,
komplett.no, elkjøp.no, etc.) where products don't have RSS feeds or APIs.

### When to use

- User wants to know when a specific product goes on sale
- User says "gi meg beskjed hvis X kommer på tilbud" or "varsle når prisen faller"
- Product page is a standard Shopify/WooCommerce/custom store without APIs

### Standard Workflow

1. **Inspect the product page** — find where prices live in the HTML. Common patterns:
   - Shopify stores: `<span class="products_price">998,-</span>` + hidden input `<input name="original_price" value="998,-" />`
   - JS variables: `var product_price = "998";` and `var baseprice = "798.4";`
   - Sale indicators: `.price-old s` (strikethrough), `sale-badge` class, compare-at price
2. **Write a watchdog script** under `~/.hermes/scripts/` that:
   - Fetches the page with `urllib.request` (no heavy deps needed)
   - Extracts current price and original/compare-at price
   - Outputs a message ONLY if on sale (silent otherwise — zero output)
   - Includes product name, price delta, percentage, and link in the message
3. **Create cron with `no_agent=True`** and the script filename (path resolves under `~/.hermes/scripts/`)
4. **Verify** by running the script manually — empty stdout means "not on sale"

### Script Template

```python
#!/usr/bin/env python3
"""Watchdog: outputs sale message if product is discounted, nothing otherwise."""
import re
import urllib.request

URL = "https://store.example.com/product/slug"

def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def main():
    html = fetch()
    # Adapt selectors per store:
    m_current = re.search(r'var\s+product_price\s*=\s*"(\d+)"', html)
    m_orig = re.search(r'name=["\']original_price["\']\s+value=["\']([^"\']+)', html)
    has_sale_badge = bool(re.search(r'class="price-old"', html))

    current = float(m_current.group(1)) if m_current else None
    # Parse "998,-" or "1.299,-" format
    if m_orig:
        raw = m_orig.group(1).replace(".", "").replace(",", ".").rstrip(".-")
        original = float(raw) if raw else None
    else:
        original = None

    if current is None:
        print(f"Kunne ikke hente pris. Sjekk manuelt: {URL}")
        return

    if (original and original > current) or has_sale_badge:
        pct = round((1 - current / original) * 100) if original else 0
        print(f"🎉 TILBUD på produktet!")
        print(f"Nå: {current:.0f},- (ordinærpris: {original:.0f},-)")
        print(f"Spart: {original - current:.0f},- ({pct}% rabatt)")
        print(f"\n🔗 {URL}")
    # else: silent — no output

if __name__ == "__main__":
    main()
```

### Cron Setup

```python
cronjob(action="create",
        schedule="0 9 * * *",       # daily at 09:00
        script="my-price-watchdog.py",  # just filename, resolves under ~/.hermes/scripts/
        no_agent=True,               # script IS the job, no LLM needed
        name="Price alert: Product Name",
        deliver="origin")
```

### Pitfalls

- **Regex with escaped quotes**: HTML often renders `\"original_price\"` — test with
  `cat -v` or Python before writing regex. Use `["\']` alternation for flexibility.
- **Norwegian price formats**: "1.299,-" means 1299 NOK. Strip dots first, then
  replace comma with dot for float parsing. The `,-` suffix is decorative.
- **`no_agent=True` requires `script` field**: `prompt` and `skills` are ignored.
  If stdout is empty, nothing is delivered (silent mode — this is by design).
- **Script path**: cron resolves script names under `~/.hermes/scripts/`. Pass just
  the filename, not an absolute or `~/` path.
- **`deliver="origin"`** sends back to the current chat. Use specific platform:chat_id
  for other channels.
- **Some stores render prices via JavaScript** — `curl` won't see them. Use
  `browser_navigate` during inspection, but the cron script can often find prices
  in hidden inputs, JS variables, or meta tags that are server-rendered.

### References

- `references/finn-no-pattern.md` — FINN-specific extraction patterns for Norwegian marketplace
- `references/shopify-price-patterns.md` — common Shopify/WooCommerce HTML patterns for price extraction
