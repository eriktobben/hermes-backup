#!/usr/bin/env bash
# Kimaki worktree cleanup — wrapper for cron (no_agent mode)
# Kun output ved feil. Stille ved alt OK (inkludert vellykket cleanup).
cd ~/.hermes/scripts || exit 1

output=$(python3 kimaki-worktree-cleanup.py --apply 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "❌ KIMAKI WORKTREE CLEANUP FEILET (exit=$exit_code)"
    echo "$output"
    exit $exit_code
fi

exit 0
