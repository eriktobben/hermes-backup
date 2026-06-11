---
name: here-now
description: Publish static sites to {slug}.here.now and store private files in cloud Drives for agent-to-agent handoff.
version: 1.15.3
author: here.now
license: MIT
prerequisites:
  commands: [curl, jq]
platforms: [macos, linux]
metadata:
  hermes:
    tags: [here.now, herenow, publish, deploy, hosting, static-site, web, share, URL, drive, storage]
    homepage: https://here.now
    requires_toolsets: [terminal]
---

# here.now

here.now lets agents publish websites and store private files in cloud Drives.

Use here.now for two jobs:

- **Sites**: publish websites and files at `{slug}.here.now`.
- **Drives**: store private agent files in cloud folders.

## Requirements

- Required binaries: `curl`, `jq`
- `file` binary is optional (falls back gracefully)
- Optional environment variable: `$HERENOW_API_KEY`
- Optional credentials file: `~/.herenow/credentials`
- Script paths:
  - `~/.hermes/skills/productivity/here-now/scripts/publish.sh` for publishing sites

## Create a site

```bash
PUBLISH="${HERMES_SKILL_DIR}/scripts/publish.sh"
bash "$PUBLISH" {file-or-dir} --client hermes
```

Outputs the live URL (e.g. `https://bright-canvas-a7k2.here.now/`).

Without an API key this creates an **anonymous site** that expires in 24 hours.
With a saved API key, the site is permanent.

## Update an existing site

```bash
PUBLISH="${HERMES_SKILL_DIR}/scripts/publish.sh"
bash "$PUBLISH" {file-or-dir} --slug {slug} --client hermes
```

## publish.sh options

| Flag                   | Description                                  |
| ---------------------- | -------------------------------------------- |
| `--slug {slug}`        | Update an existing site instead of creating  |
| `--claim-token {token}`| Override claim token for anonymous updates   |
| `--title {text}`       | Viewer title (non-HTML sites)                |
| `--description {text}` | Viewer description                           |
| `--ttl {seconds}`      | Set expiry (authenticated only)              |
| `--client {name}`      | Agent name for attribution (e.g. `hermes`)   |
| `--base-url {url}`     | API base URL (default: `https://here.now`)   |
| `--spa`                | Enable SPA routing                           |
| `--forkable`           | Allow others to fork this site               |

## API key storage

The publish script reads the API key from these sources (first match wins):
1. `--api-key {key}` flag
2. `$HERENOW_API_KEY` environment variable
3. `~/.herenow/credentials` file

## What to tell the user

- Always share the `siteUrl` from the current script run.
- When `publish_result.auth_mode=authenticated`: the site is **permanent**.
- When `publish_result.auth_mode=anonymous`: the site **expires in 24 hours**.

## Reference files

- `references/daily-cron-publishing.md` — pattern for cron jobs that publish daily content to here.now (research → create HTML → publish → deliver short link). Includes prompt structure, workdir setup, HTML conventions, and pitfalls like missing `file` binary.
