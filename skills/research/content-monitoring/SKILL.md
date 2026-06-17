---
name: content-monitoring
description: "Monitor external content sources for updates — RSS/Atom feeds via blogwatcher-cli and classified marketplace listings with dedup, filtering, and cron delivery. Covers setup, scheduling, and watchdog patterns for both blog feeds and classified ad alerts."
tags: [monitoring, rss, blogs, classifieds, alerts, cron, web-scraping]
platforms: [linux, macos, windows]
related_skills: [cronjob]
---

# Content Monitoring

Automatically monitor external content sources — RSS feeds and classified marketplaces —
and get notified about new items. Two complementary approaches for two different data sources.

## When to use

- User wants to track blog or RSS feed updates
- User wants daily/hourly alerts for new classified listings (cars, housing, gear)
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

### References

- `references/finn-no-pattern.md` — FINN-specific extraction patterns for Norwegian marketplace
