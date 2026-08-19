#!/bin/bash
# Daily restart of opencode serve to prevent posix_spawn ENOENT bug
# Server is UTC. 03:00 UTC = 05:00 CEST (summer) / 04:00 CET (winter)

set -e

OLD_PID=$(pgrep -f "opencode serve" | head -1)
if [ -z "$OLD_PID" ]; then
    echo "❌ Ingen opencode serve-prosess funnet. Sjekker om Kimaki kan starte en..."
    pgrep -f kimaki > /dev/null 2>&1 && echo "   Kimaki kjører, så ACP-transporten burde starte en ved behov"
    exit 1
fi

OLD_PORT=$(cat /proc/$OLD_PID/cmdline 2>/dev/null | tr '\0' ' ' | grep -oP -- '--port \K\d+' || echo "ukjent")

kill "$OLD_PID"
sleep 4

if pgrep -f "opencode serve" > /dev/null 2>&1; then
    # Suksess — ingen output (stille i Discord)
    :
else
    echo "⚠️  Opencode server kom ikke opp igjen automatisk. Sjekk Kimaki."
    exit 1
fi

# Prune stale git worktrees
cd /home/erik/.kimaki/projects/kimaki
git worktree prune 2>/dev/null
