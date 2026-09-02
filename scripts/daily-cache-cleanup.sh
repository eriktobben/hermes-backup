#!/usr/bin/env bash
# Daily disk cleanup — npm, bun, kimaki worktrees, general cache, logs
# Stille ved alt OK. Kun output ved cleanup eller feil.
set -euo pipefail

DISK_WARN_PCT=75
DISK_CRITICAL_PCT=90
freed=0

# --- npm cache ---
npm_before=$(du -sb ~/.npm 2>/dev/null | cut -f1 || echo 0)
npm cache clean --force 2>/dev/null && true
npm_after=$(du -sb ~/.npm 2>/dev/null | cut -f1 || echo 0)
npm_freed=$(( (npm_before - npm_after) / 1073741824 ))
[ "$npm_freed" -gt 0 ] && freed=$((freed + npm_freed))

# --- bun cache ---
bun_before=$(du -sb ~/.bun/install/cache 2>/dev/null | cut -f1 || echo 0)
rm -rf ~/.bun/install/cache/* 2>/dev/null && true
bun_after=$(du -sb ~/.bun/install/cache 2>/dev/null | cut -f1 || echo 0)
bun_freed=$(( (bun_before - bun_after) / 1073741824 ))
[ "$bun_freed" -gt 0 ] && freed=$((freed + bun_freed))

# --- general cache: delete files older than 14 days ---
cache_before=$(du -sb ~/.cache 2>/dev/null | cut -f1 || echo 0)
find ~/.cache -type f -atime +14 -delete 2>/dev/null && true
find ~/.cache -type d -empty -delete 2>/dev/null && true
cache_after=$(du -sb ~/.cache 2>/dev/null | cut -f1 || echo 0)
cache_freed=$(( (cache_before - cache_after) / 1073741824 ))
[ "$cache_freed" -gt 0 ] && freed=$((freed + cache_freed))

# --- pm2 logs (rotate: keep last 1000 lines per log) ---
for f in ~/.pm2/logs/*.log; do
    [ -f "$f" ] || continue
    lines=$(wc -l < "$f")
    if [ "$lines" -gt 1000 ]; then
        tail -1000 "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
    fi
done 2>/dev/null && true

# --- kimaki worktrees older than 14 days ---
# ⚠️ BRUK KUN dette scriptet for worktree-cleanup. IKKE slett ~/.kimaki/worktrees/* manuelt!
cd ~/.hermes/scripts 2>/dev/null && python3 kimaki-worktree-cleanup.py --apply 2>/dev/null && true

# --- prune orphaned git worktrees across all projects ---
for dir in /home/erik/Projects/*/; do
    if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
        cd "$dir" && git worktree prune 2>/dev/null && true
    fi
done

# --- npm _npx stale cache (older than 30 days) ---
find ~/.npm/_npx -mindepth 1 -maxdepth 1 -type d -mtime +30 -exec rm -rf {} + 2>/dev/null && true

# --- disk check ---
disk_pct=$(df / | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
disk_avail=$(df -h / | awk 'NR==2 {print $4}')

if [ "$disk_pct" -ge "$DISK_CRITICAL_PCT" ]; then
    echo "🚨 DISK KRITISK: ${disk_pct}% brukt, ${disk_avail} ledig"
elif [ "$disk_pct" -ge "$DISK_WARN_PCT" ]; then
    echo "⚠️ DISK ADVARSEL: ${disk_pct}% brukt, ${disk_avail} ledig"
elif [ "$freed" -gt 0 ]; then
    echo "🧹 Ryddet ${freed}GB totalt. Disk: ${disk_pct}% brukt, ${disk_avail} ledig"
fi
