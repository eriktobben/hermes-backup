# Worktree Cleanup Investigation Methodology

## When to use
When a Kimaki worktree disappears and you need to diagnose which cleanup mechanism caused it.

## Step 1: Check the DB
```python
python3 -c "
import sqlite3, os
db = sqlite3.connect(os.path.expanduser('~/.kimaki/discord-sessions.db'))
for r in db.execute(\"SELECT thread_id, workspace_name, workspace_directory, project_directory, status, created_at FROM thread_workspaces WHERE workspace_directory LIKE '%<hash>%'\"):
    print(r)
"
```

## Step 2: Check Kimaki logs
```bash
grep -E "<hash>|<thread_id>" ~/.kimaki/kimaki.log | tail -30
```

Look for:
- `Created via workspace SDK` — worktree creation timestamp
- `Using project directory` — last usage before disappearance
- `cleanup failed` with `NotFound: FileSystem.access` — OpenCode GC tried to access deleted directory

## Step 3: Check OpenCode GC timestamps
```bash
grep "2026-<date>T02:" ~/.local/share/opencode/log/opencode.log | grep "cleanup failed"
```

The GC runs at ~02:00-02:54. If the error says "NotFound", the directory was already deleted before GC ran.

## Step 4: Check snapshot directories
```bash
ls -la ~/.local/share/opencode/snapshot/ | grep <hash_prefix>
stat ~/.local/share/opencode/snapshot/<hash>/
```

Modified timestamps on snapshot dirs show when OpenCode last touched them.

## Step 5: Check if git branch survived
```bash
cd <project_directory> && git branch -a | grep <branch_name>
```

## Diagnosis matrix

| Worktree dir | Git branch | Cause | Fix |
|-------------|-----------|-------|-----|
| Gone | Exists | OpenCode GC (normal) | Auto-restored at 02:15 or manual: `git worktree add <dir> <branch>` |
| Gone | Gone | OpenCode GC + Kimaki cleanup (>14 days) OR OpenCode GC + branch deletion | Find equivalent branch in project (v2, develop, main) |
| Exists | Exists | No cleanup happened | Check for other issues |
| Exists | Gone | Unusual — check `git worktree prune` output | Recreate from current worktree state |

## Key timestamps to check
- WIP auto-commit: 01:50 UTC
- OpenCode GC: ~02:00-02:54 UTC
- Restore/cleanup cron: 02:15 UTC
- Kimaki restart: 05:00 UTC (restart-opencode.sh)

## Common pitfall: wrong DB table
Both `thread_worktrees` and `thread_workspaces` exist. Kimaki uses `thread_workspaces`. Scripts that query `thread_worktrees` will find nothing.
