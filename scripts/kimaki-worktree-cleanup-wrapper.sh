#!/usr/bin/env bash
# Kimaki worktree cleanup — wrapper for cron (no_agent mode)
# Stille ved "alt OK", kun output ved cleanup eller feil
cd ~/.hermes/scripts || exit 1

output=$(python3 kimaki-worktree-cleanup.py --apply 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "❌ KIMAKI WORKTREE CLEANUP FEILET (exit=$exit_code)"
    echo "$output"
    exit $exit_code
fi

# Sjekk om noe faktisk ble gjort (tall > 0 på cleanup/feil)
cleanup_count=$(echo "$output" | grep -oP 'Ryddet opp:\s+\K\d+')
orphaned_count=$(echo "$output" | grep -oP 'Orphaned kataloger:\s+\K\d+')
error_count=$(echo "$output" | grep -oP 'Feil:\s+\K\d+')

if [ "${cleanup_count:-0}" -gt 0 ] || [ "${orphaned_count:-0}" -gt 0 ] || [ "${error_count:-0}" -gt 0 ]; then
    echo "$output"
fi

exit 0
