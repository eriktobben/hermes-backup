#!/usr/bin/env bash
# Kimaki WIP Auto-Commit — kjører kl. 01:50 (10 min før OpenCode's GC kl. 02:00)
# Committer uncommitted changes i alle aktive worktrees slik at arbeidet
# bevares i git-greina selv om worktree-katalogen blir slettet.
#
# FIX (Aug 2026): Bruker thread_workspaces (ikke thread_worktrees) —
# det er her Kimaki lagrer worktree-info for moderne sessions.
set -euo pipefail

KIMAKI_DB="$HOME/.kimaki/discord-sessions.db"
NOW=$(date -u '+%Y-%m-%d %H:%M UTC')
COMMITTED=0
SKIPPED=0
ERRORS=0

echo "=== KIMAKI WIP AUTO-COMMIT ==="
echo "Tid: $NOW"
echo ""

# Hent alle worktrees med status 'ready'
# Bruker thread_workspaces (ikke thread_worktrees) — det er her Kimaki lagrer worktree-info
WORKTREES=$(python3 -c "
import sqlite3, json
conn = sqlite3.connect('$KIMAKI_DB')
conn.row_factory = sqlite3.Row
rows = conn.execute('''
    SELECT tw.thread_id, tw.workspace_name, tw.workspace_directory, tw.project_directory
    FROM thread_workspaces tw
    WHERE tw.status = 'ready' AND tw.workspace_directory IS NOT NULL
''').fetchall()
for r in rows:
    print(json.dumps(dict(r)))
" 2>/dev/null)

if [ -z "$WORKTREES" ]; then
    echo "Ingen aktive worktrees funnet."
    exit 0
fi

while IFS= read -r line; do
    WT_DIR=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['workspace_directory'])")
    WT_NAME=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['workspace_name'])")
    PROJECT_DIR=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['project_directory'])")

    if [ ! -d "$WT_DIR" ]; then
        echo "  ⏩ $WT_DIR finnes ikke (allerede ryddet) — hopper over"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    cd "$WT_DIR" || continue

    # Sjekk om det er uncommitted changes (arbeidsfordeling + stashed)
    DIRTY=$(git status --porcelain 2>/dev/null || true)
    if [ -z "$DIRTY" ]; then
        echo "  ✅ $WT_NAME — ingen endringer å committe"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Auto-commit WIP
    CHANGED_COUNT=$(echo "$DIRTY" | wc -l)
    echo "  🔷 $WT_NAME — $CHANGED_COUNT endringer, committer WIP..."
    git add -A 2>/dev/null || true
    if git commit -m "wip: auto-commit before nightly GC ($NOW)" --no-verify 2>/dev/null; then
        echo "  ✅ $WT_NAME — committet"
        COMMITTED=$((COMMITTED + 1))
    else
        echo "  ⚠️  $WT_NAME — commit feilet"
        ERRORS=$((ERRORS + 1))
    fi

    # Push til origin slik at arbeidet også er på remote
    BRANCH=$(git branch --show-current 2>/dev/null || true)
    if [ -n "$BRANCH" ]; then
        git push origin "$BRANCH" --no-verify 2>/dev/null || true
    fi

done <<< "$WORKTREES"

echo ""
echo "=== OPPSUMMERING ==="
echo "  Committe:  $COMMITTED"
echo "  Hoppet over: $SKIPPED"
echo "  Feil:      $ERRORS"
