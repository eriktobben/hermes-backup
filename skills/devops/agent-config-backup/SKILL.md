---
name: agent-config-backup
description: Automated git-based backup of AI agent configuration and data for disaster recovery. What to include, what to exclude (secrets), how to schedule silently, and how to restore.
version: 1.0.0
metadata:
  tags: [backup, git, disaster-recovery, cron, hermes]
---

# Agent Config Backup — Automated Git Backup

Set up an hourly git-backed backup of an AI agent's configuration and persistent data so the agent can be fully restored if something goes wrong.

## When to use

- User asks "can you back up my agent config to git?"
- User asks for disaster recovery setup
- User wants to version-control their agent's skills, memory, plugins, or scripts

## What to include

| What | Why |
|------|-----|
| `config.yaml` | Main configuration — model, provider, tools, agent behaviour |
| `SOUL.md` / personality files | Agent personality/tone definition |
| `skills/` | Installed skills (procedural knowledge) |
| `plugins/` | Installed plugins (custom functionality) |
| `memories/` | Persistent user profile + agent notes |
| `scripts/` | Custom automation scripts |
| `sessions/` | Conversation history **only if user explicitly wants it** (JSONL files are git-friendly; SQLite DB is not) |
| `hooks/` | Shell hook configuration |
| `cron/` | Scheduled job definitions and state |
| `gateway/` | Platform sync state |
| `pairing/` | Platform pairing data |
| Channel/thread mapping JSON files | Discord, channel_directory, etc. |
| Kanban board DB | If agent uses Kanban |

## What to exclude

| What | Why |
|------|-----|
| `.env` / secrets files | API keys, tokens — **never commit to git** |
| `auth.json` | OAuth tokens — never commit to git |
| `logs/` | Runtime logs — not needed for restore, can be large |
| Source code directories | Reinstallable from package manager (e.g. `hermes update`, `pip install`) |
| `state.db` (SQLite) | **Do not back up SQLite session DBs** — they change on every message, bloat the repo, and git cannot delta-compress them efficiently. Restore from session files instead. |
| `cache/`, image/audio caches | Temporary, regenerated automatically |

## Secret handling

GitHub's push protection blocks commits containing secrets. The correct strategy:

1. **Put secrets in `.gitignore`** — add `.env`, `auth.json`, and similar to `.gitignore`
2. **Create an env template** — extract variable names from the real `.env`, blank out values:
   ```bash
   grep -E '^[A-Z_]+[A-Z_0-9]*=' ~/.hermes/.env \
     | sed 's/=.*$/=""/' \
     > env.template.txt
   ```
3. **Write a README** documenting which variables need manual filling on restore

## Backup script pattern

Create a script at `~/.hermes/scripts/agent-backup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$HOME/Projects/agent-backup"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

cd "$BACKUP_DIR"
[ ! -d .git ] && { echo "ERROR: Not a git repo" >&2; exit 1; }

# ── Sync files ──
cp "$HERMES_HOME/config.yaml" "$BACKUP_DIR/" 2>/dev/null || true
cp "$HERMES_HOME/SOUL.md" "$BACKUP_DIR/" 2>/dev/null || true
# ... more files ...

# Generate env template
grep -E '^[A-Z_]+[A-Z_0-9]*=' "$HERMES_HOME/.env" 2>/dev/null \
  | sed 's/=.*$/=""/' > "$BACKUP_DIR/env.template.txt" || true

# Directories with rsync (--delete removes stale files)
rsync -a --delete "$HERMES_HOME/skills/" "$BACKUP_DIR/skills/" 2>/dev/null || true
rsync -a --delete "$HERMES_HOME/sessions/" "$BACKUP_DIR/sessions/" 2>/dev/null || true
# ... more dirs ...

# ── Commit and push ──
git add -A
git diff --cached --quiet && exit 0  # nothing changed
git commit -q -m "Backup — $TIMESTAMP"

# Try push; only speak on failure
if ! git push origin main 2>/dev/null && ! git push origin master 2>/dev/null; then
  echo "ERROR: Git push failed at $TIMESTAMP" >&2
  exit 1
fi
# Success — silent
exit 0
```

**Key details:**
- `git commit -q` — suppresses git's own output so the script is truly silent on success
- `2>/dev/null` — suppresses cp/rsync noise
- `set -euo pipefail` — fail fast on unexpected errors
- Write all actual errors to stderr (`>&2`)
- Only exit non-zero on failure (triggers cron error alerts)

## Silent-on-success pattern

For `no_agent=True` cron jobs, the delivery semantics are:
- **Empty stdout + exit 0** → completely silent (no notification)
- **Non-empty stdout** → sent as a message (even on success)
- **Non-zero exit / stderr** → sent as an error alert

Design the script to:
1. Exit 0 with no stdout when nothing changed
2. Exit 0 with no stdout when backup succeeded (commit + push)
3. Exit 1 with stderr when something failed

## Scheduling with cronjob tool

Use the cronjob tool with `no_agent=True` (pure script execution — no LLM tokens):

```bash
# Create
cronjob(
  action="create",
  name="Agent backup to GitHub",
  schedule="every 1h",
  script="agent-backup.sh",   # relative to ~/.hermes/scripts/
  no_agent=True,
  deliver="origin"             # error alerts come back to current conversation
)

# Update
cronjob(action="update", job_id="...", deliver="origin")
```

**Why `no_agent=True`:** The backup script is a simple shell script — no reasoning needed. Running an LLM agent for every backup tick would waste tokens and slow things down.

## Restore procedure

In a README in the backup repo, document:

```bash
# 1. Install the agent (e.g. curl install script)
# 2. Clone the backup repo
# 3. Copy config files back
cp /tmp/backup/config.yaml ~/.hermes/
rsync -a /tmp/backup/skills/ ~/.hermes/skills/
# ... etc.
# 4. Create .env from env.template.txt and fill in keys
cp /tmp/backup/env.template.txt ~/.hermes/.env
nano ~/.hermes/.env
# 5. Verify
hermes doctor
```

## Reference files

- `references/hermes-backup-script.sh` — concrete working script for Hermes backup, used in production at Serena AS. Adapt paths and file lists for other agents.

## Pitfalls

- **GitHub push protection** blocks secrets. Test the initial push — if it fails, check the error for which file triggered it and add that file to `.gitignore`.
- **SQLite DBs in git** are a bad idea. A single message can change 80% of the binary blob. Use individual JSONL session files instead.
- **Don't back up the agent's own source code** — it's huge (3+ GB) and reinstallable via the package manager.
- **Cron job script paths** must be relative to `~/.hermes/scripts/` — use just the filename, not an absolute or `~/` path.
- **Set git credentials upfront** — the backup script runs unattended. If using HTTPS, ensure the remote URL has no interactive auth requirement. If using SSH, ensure the key is loaded without passphrase interaction.
