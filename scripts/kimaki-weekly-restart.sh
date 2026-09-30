#!/bin/bash
# Weekly Kimaki/opencode restart — memory hygiene + Bun runtime degradation guard.
# opencode serve grows with session count and its Bun runtime degrades after
# ~44h uptime (posix_spawn '/bin/sh' ENOENT). Restart weekly at low activity.
#
# Quiet on success (no Discord noise); prints only on WARNING/ERROR.

set -u

BEFORE=$(ps -eo rss,args | grep '[o]pencode serve' | awk '{s+=$1} END {print s+0}')
BEFORE_MB=$((BEFORE/1024))

# Kill any opencode server first (tracked one + orphans)
pkill -f 'opencode serve' 2>/dev/null
sleep 2

# Restart Kimaki — spawns a fresh opencode server with clean Bun runtime
pm2 restart kimaki >/dev/null 2>&1

# Wait for the new opencode server to appear
N=0
for i in $(seq 1 15); do
  N=$(ps -eo args | grep -c '[o]pencode serve')
  [ "$N" -ge 1 ] && break
  sleep 2
done
sleep 10

ORPHAN_COUNT=$(ps -eo args | grep '[o]pencode serve' | grep -cv grep || true)
AFTER=$(ps -eo rss,args | grep '[o]pencode serve' | awk '{s+=$1} END {print s+0}')
AFTER_MB=$((AFTER/1024))

if [ "$ORPHAN_COUNT" -eq 0 ]; then
  echo "ERROR $(date '+%F %R'): ingen opencode serve etter restart (var ${BEFORE_MB}MB før). Sjekk 'pm2 logs kimaki' og 'systemctl --user status pm2'."
  exit 1
fi

if [ "$ORPHAN_COUNT" -gt 1 ]; then
  NEWEST=$(ps -eo pid,lstart,args | grep '[o]pencode serve' | sort -k2,5 | tail -1 | awk '{print $1}')
  ps -eo pid,args | grep '[o]pencode serve' | grep -v grep | awk '{print $1}' | while read -r pid; do
    [ "$pid" != "$NEWEST" ] && kill "$pid" 2>/dev/null
  done
  echo "WARNING $(date '+%F %R'): $ORPHAN_COUNT opencode serve etter restart — orphans drept, newest beholdt (pid $NEWEST). RSS: ${BEFORE_MB}MB → ${AFTER_MB}MB."
  exit 0
fi

# Success: stay silent (stdout would be delivered as a Discord message)
exit 0
