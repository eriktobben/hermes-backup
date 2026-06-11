# Daily cron publishing to here.now

Pattern for cron jobs that research, create content, publish to here.now, and deliver a short link.

## Structured prompt

A daily-publish cron job prompt follows four steps:

1. **Research** — gather/curate content (web search, data sources, etc.)
2. **Create** — write a self-contained HTML file in a stable workdir
3. **Publish** — run publish.sh on that directory
4. **Deliver** — output only the link + a 1-line teaser (no full content)

## Workdir + state persistence

Use a stable working directory (e.g. `/home/user/Projects/<name>/`) so `.herenow/state.json` persists between runs. This lets publish.sh find the previous slug and claim token, enabling update-in-place of the same URL.

```bash
mkdir -p /home/user/Projects/daily-thing
# publish.sh writes .herenow/state.json here
```

## HTML page conventions

- Dark-themed, mobile-friendly, self-contained (no external CSS/JS)
- Date prominently at top in Norwegian format (`12. juni 2026`)
- Sections with emoji headers
- Sources cited as hyperlinks
- ~5-10 bullet points unless exceptional news

## Publish command

```bash
PUBLISH=~/.hermes/skills/productivity/here-now/scripts/publish.sh
bash "$PUBLISH" /path/to/workdir --client hermes --title "Page Title - $(date +%d.%m.%Y)"
```

- With API key: site is **permanent**
- Without API key: site **expires in 24h** (fine for daily content)

## Delivery format

Only post to Discord:
```
🧠 **Title — date**
https://slug.here.now/
One-line teaser of top news.
```

## Recap-overwrite semantics

Each run overwrites the same URL with fresh content. No history is kept — it's a "today's page," not an archive.

## Pitfalls

- `file` binary may not be installed (`which file`). publish.sh has a `file` requirement check — patch it to make `file` optional since the extension-based content-type detection covers common cases (.html, .css, .js, .png, etc.).
- Use `--client hermes` for attribution tracking on the here.now side.
- If creating a new slug fails (e.g. name taken), omit `--slug` to auto-generate a fresh one.
