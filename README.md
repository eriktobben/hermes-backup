# Hermes Backup

Automatic hourly backup of Hermes Agent configuration and data.

## What's backed up

| What | Why |
|------|-----|
| `config.yaml` | All Hermes settings — model, provider, tools, agent behaviour |
| `SOUL.md` | Agent personality file |
| `skills/` | All installed skills (procedural knowledge) |
| `plugins/` | All installed plugins (custom functionality) |
| `memories/` | Persistent memory (user profile + agent notes) |
| `scripts/` | Custom automation scripts |
| `sessions/` | Conversation history (delta-friendly, individual JSONL files) |
| `cron/` | Scheduled job definitions |
| `gateway/` | Platform sync state (Discord, etc.) |
| `hooks/` | Shell hook configuration |
| `pairing/` | Platform pairing data |
| `channel_directory.json` | Channel-to-repo mappings |
| `discord_threads.json` | Discord thread state |
| `gateway_state.json` | Gateway health state |
| `kanban.db` | Kanban board data |

## What's NOT backed up

| What | Why |
|------|-----|
| `.env` (→ `env.txt`) | API keys / secrets — **not committed to git** |
| `auth.json` | OAuth tokens — **not committed to git** |
| `logs/` | Runtime logs (not needed for restore) |
| `hermes-agent/` | Source code (reinstall via `hermes update`) |
| `state.db` | Session DB (large, state-snapshots excluded) |
| `cache/`, `audio_cache/`, `image_cache/` | Temporary caches |

## Restore procedure

If you need to restore Hermes from this backup:

```bash
# 1. Install Hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. Clone this repo
git clone https://github.com/eriktobben/hermes-backup.git /tmp/hermes-restore

# 3. Copy config and data
cp /tmp/hermes-restore/config.yaml ~/.hermes/config.yaml
cp /tmp/hermes-restore/SOUL.md ~/.hermes/SOUL.md
cp /tmp/hermes-restore/channel_directory.json ~/.hermes/
cp /tmp/hermes-restore/discord_threads.json ~/.hermes/
cp /tmp/hermes-restore/gateway_state.json ~/.hermes/
cp /tmp/hermes-restore/kanban.db ~/.hermes/
rsync -a /tmp/hermes-restore/skills/ ~/.hermes/skills/
rsync -a /tmp/hermes-restore/sessions/ ~/.hermes/sessions/
rsync -a /tmp/hermes-restore/plugins/ ~/.hermes/plugins/
rsync -a /tmp/hermes-restore/memories/ ~/.hermes/memories/
rsync -a /tmp/hermes-restore/scripts/ ~/.hermes/scripts/
rsync -a /tmp/hermes-restore/hooks/ ~/.hermes/hooks/
rsync -a /tmp/hermes-restore/cron/ ~/.hermes/cron/
rsync -a /tmp/hermes-restore/gateway/ ~/.hermes/gateway/
rsync -a /tmp/hermes-restore/pairing/ ~/.hermes/pairing/

# 4. Restore API keys — copy env.template.txt to ~/.hermes/.env and fill in keys
cp /tmp/hermes-restore/env.template.txt ~/.hermes/.env
nano ~/.hermes/.env   # ← fill in your API keys

# 5. Restore auth tokens (if auth.json is available outside git)
# You may need to re-authenticate:
#   hermes login --provider opencode-go
#   hermes login --provider minimax-oauth

# 6. Verify
hermes doctor

# 7. Clean up
rm -rf /tmp/hermes-restore
```

## How the backup works

An hourly cron job runs `~/.hermes/scripts/hermes-backup.sh`, which:
1. Copies Hermes data (excluding secrets) into this repo
2. Commits any changes with a timestamp
3. Pushes to GitHub

Only files that have changed since the last backup are committed.
