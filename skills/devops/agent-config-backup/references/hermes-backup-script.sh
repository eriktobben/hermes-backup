#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Hermes Backup Script
# Runs every hour via Hermes cron.
# Commits config + data (excluding secrets) to GitHub.
#
# Silent on success — only produces output/errors on
# failure, so cron only notifies the user when something
# goes wrong.
# ──────────────────────────────────────────────────────

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$HOME/Projects/hermes-backup"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

cd "$BACKUP_DIR"

if [ ! -d .git ]; then
  echo "ERROR: $BACKUP_DIR is not a git repository" >&2
  exit 1
fi

# ── Sync files ────────────────────────────────────────

# Top-level config files
cp "$HERMES_HOME/config.yaml"     "$BACKUP_DIR/config.yaml"           2>/dev/null || true
cp "$HERMES_HOME/SOUL.md"         "$BACKUP_DIR/SOUL.md"               2>/dev/null || true
cp "$HERMES_HOME/channel_directory.json" "$BACKUP_DIR/"               2>/dev/null || true
cp "$HERMES_HOME/discord_threads.json"   "$BACKUP_DIR/"               2>/dev/null || true
cp "$HERMES_HOME/gateway_state.json"     "$BACKUP_DIR/"               2>/dev/null || true
cp "$HERMES_HOME/kanban.db"              "$BACKUP_DIR/kanban.db"      2>/dev/null || true

# Keep env.template.txt up to date with current variable names
grep -E '^[A-Z_]+[A-Z_0-9]*=' "$HERMES_HOME/.env" 2>/dev/null \
  | sed 's/=.*$/=""/' \
  > "$BACKUP_DIR/env.template.txt" \
  || true

# Directories (rsync for efficiency, --delete removes stale files)
rsync -a --delete "$HERMES_HOME/skills/"    "$BACKUP_DIR/skills/"     2>/dev/null || true
rsync -a --delete "$HERMES_HOME/sessions/"  "$BACKUP_DIR/sessions/"   2>/dev/null || true
rsync -a --delete "$HERMES_HOME/plugins/"   "$BACKUP_DIR/plugins/"    2>/dev/null || true
rsync -a --delete "$HERMES_HOME/memories/"  "$BACKUP_DIR/memories/"   2>/dev/null || true
rsync -a --delete "$HERMES_HOME/scripts/"   "$BACKUP_DIR/scripts/"    2>/dev/null || true
rsync -a --delete "$HERMES_HOME/hooks/"     "$BACKUP_DIR/hooks/"      2>/dev/null || true
rsync -a --delete "$HERMES_HOME/cron/"      "$BACKUP_DIR/cron/"       2>/dev/null || true
rsync -a --delete "$HERMES_HOME/gateway/"   "$BACKUP_DIR/gateway/"    2>/dev/null || true
rsync -a --delete "$HERMES_HOME/pairing/"   "$BACKUP_DIR/pairing/"    2>/dev/null || true

# ── Stage, commit, push ───────────────────────────────

git add -A

if git diff --cached --quiet; then
  # Nothing changed — silent exit
  exit 0
fi

git commit -q -m "Hermes backup — $TIMESTAMP"

# Try pushing; only speak on failure
if ! git push origin main 2>/dev/null; then
  if ! git push origin master 2>/dev/null; then
    echo "ERROR: Git push failed at $TIMESTAMP" >&2
    exit 1
  fi
fi

# Success — silent
exit 0
