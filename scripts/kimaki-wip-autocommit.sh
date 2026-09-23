#!/usr/bin/env bash
# Kimaki WIP Auto-Commit & Cleanup — kjører kl. 01:50 (før GC kl. 02:00)
#
# Oppførsel:
#   1. Worktree eldre enn 14 dager OG uten endringer siste 14 dager → slettes
#   2. Hvis worktreet har uncommitted endringer → lag branch, commit WIP, push, opprett PR
#   3. ALDRI commit til main
set -euo pipefail

KIMAKI_DB="$HOME/.kimaki/discord-sessions.db"
NOW=$(date -u '+%Y-%m-%d %H:%M UTC')
DELETED=0
PR_CREATED=0
SKIPPED=0
ERRORS=0

echo "=== KIMAKI WORKTREE CLEANUP ==="
echo "Tid: $NOW"
echo ""

# Hent alle worktrees med status 'ready'
WORKTREES=$(python3 -c "
import sqlite3, json
conn = sqlite3.connect('$KIMAKI_DB')
conn.row_factory = sqlite3.Row
rows = conn.execute('''
    SELECT tw.thread_id, tw.workspace_name, tw.workspace_directory, tw.project_directory,
           tw.created_at
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
    WT_CREATED=$(echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('created_at',''))")

    if [ ! -d "$WT_DIR" ]; then
        echo "  ⏩ $WT_DIR finnes ikke (allerede ryddet) — hopper over"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    cd "$WT_DIR" || continue

    # Sjekk om worktreet er på main — ALDRI jobb med main
    BRANCH=$(git branch --show-current 2>/dev/null || true)
    if [ "$BRANCH" = "main" ] || [ -z "$BRANCH" ]; then
        echo "  ⚠️  $WT_NAME — branch er '$BRANCH' (tom eller main) — hopper over av sikkerhet"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Sjekk alder: opprettet for mer enn 14 dager siden?
    DAYS_OLD=0
    if [ -n "$WT_CREATED" ]; then
        CREATED_TS=$(date -d "$WT_CREATED" +%s 2>/dev/null || echo "0")
        NOW_TS=$(date +%s)
        DAYS_OLD=$(( (NOW_TS - CREATED_TS) / 86400 ))
    fi

    # Sjekk siste aktivitet: siste commit-dato i worktree
    LAST_COMMIT_DATE=$(git log -1 --format="%ci" 2>/dev/null || echo "1970-01-01")
    LAST_COMMIT_TS=$(date -d "$LAST_COMMIT_DATE" +%s 2>/dev/null || echo "0")
    NOW_TS=$(date +%s)
    DAYS_SINCE_COMMIT=$(( (NOW_TS - LAST_COMMIT_TS) / 86400 ))

    echo "  📋 $WT_NAME — opprettet ${DAYS_OLD}d siden, siste commit ${DAYS_SINCE_COMMIT}d siden"

    # Hvis worktreet er yngre enn 14 dager ELLER har aktivitet siste 14 dager → behold
    if [ "$DAYS_OLD" -lt 14 ] || [ "$DAYS_SINCE_COMMIT" -lt 14 ]; then
        echo "  ✅ $WT_NAME — beholdes (for ny eller nylig aktivitet)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Worktree er kvalifisert for sletting (>=14 dager gammel, >=14 dager uten aktivitet)
    echo "  🗑️  $WT_NAME — kvalifisert for sletting (${DAYS_OLD}d gammel, ${DAYS_SINCE_COMMIT}d siden siste commit)"

    # Sjekk om det er uncommitted endringer
    DIRTY=$(git status --porcelain 2>/dev/null || true)
    if [ -n "$DIRTY" ]; then
        # Det er uferdig arbeid → opprett PR for å bevare det
        WIP_BRANCH="wip/cleanup-$(date -u '+%Y%m%d-%H%M%S')-$(echo "$WT_NAME" | tr '/' '-')"
        echo "  🔷 $WT_NAME — uferdig arbeid funnet, oppretter PR på branch $WIP_BRANCH..."

        git checkout -b "$WIP_BRANCH" 2>/dev/null || {
            echo "  ❌ $WT_NAME — kunne ikke opprette branch"
            ERRORS=$((ERRORS + 1))
            continue
        }

        git add -A 2>/dev/null || true
        if git commit -m "wip: redningsarbeid fra $WT_NAME (automatisk, $NOW)" --no-verify 2>/dev/null; then
            git push origin "$WIP_BRANCH" --no-verify 2>/dev/null || {
                echo "  ❌ $WT_NAME — push feilet"
                ERRORS=$((ERRORS + 1))
                git checkout main 2>/dev/null || true
                git branch -D "$WIP_BRANCH" 2>/dev/null || true
                continue
            }

            # Opprett PR via gh CLI
            PR_URL=$(gh pr create \
                --base main \
                --head "$WIP_BRANCH" \
                --title "wip: redningsarbeid fra $WT_NAME" \
                --body "Automatisk PR opprettet under worktree-cleanup ($NOW).

Worktree \`$WT_NAME\` var ${DAYS_OLD} dager gammel og uten aktivitet i ${DAYS_SINCE_COMMIT} dager.
Den inneholdt uferdig arbeid som ble commitet for å bevare det.

**Vennligst gjennomgå og merge eller lukk denne PR-en.**" \
                2>/dev/null) || {
                echo "  ❌ $WT_NAME — PR opprettelse feilet"
                ERRORS=$((ERRORS + 1))
                git checkout main 2>/dev/null || true
                git branch -D "$WIP_BRANCH" 2>/dev/null || true
                continue
            }

            echo "  ✅ $WT_NAME — PR opprettet: $PR_URL"
            PR_CREATED=$((PR_CREATED + 1))
        else
            echo "  ⚠️  $WT_NAME — commit feilet (tom worktree?)"
            ERRORS=$((ERRORS + 1))
            git checkout main 2>/dev/null || true
            git branch -D "$WIP_BRANCH" 2>/dev/null || true
            continue
        fi

        git checkout main 2>/dev/null || true
    else
        # Ingen uferdig arbeid → trygt å slette worktree
        echo "  🧹 $WT_NAME — ingen uferdig arbeid, sletter..."
    fi

    # Slett worktree-katalogen (fjerner fra git worktree)
    git worktree remove "$WT_DIR" --force 2>/dev/null || rm -rf "$WT_DIR"
    DELETED=$((DELETED + 1))
    echo "  ✅ $WT_NAME — slettet"

done <<< "$WORKTREES"

echo ""
echo "=== OPPSUMMERING ==="
echo "  Slettet:     $DELETED"
echo "  PR opprettet: $PR_CREATED"
echo "  Hoppet over:  $SKIPPED"
echo "  Feil:        $ERRORS"
