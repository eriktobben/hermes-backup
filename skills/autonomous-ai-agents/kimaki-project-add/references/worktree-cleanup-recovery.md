# Worktree cleanup recovery

## Symptom
User says "I worked on a Kimaki thread yesterday, today when I try to continue I get:

```
✗ Directory does not exist or is not accessible: /home/erik/.kimaki/worktrees/<hash>/<worktree-name>
```

## Root cause — two separate cleanup mechanisms

Kimaki worktrees are affected by **two independent nightly cleanup processes**:

1. **OpenCode snapshot GC (~02:00)**: The OpenCode binary runs `git gc --prune=7.days` on snapshot repos (under `~/.local/share/opencode/snapshot/`). Each snapshot repo has `worktree = <kimaki-worktree-path>` in its git config. **Deletes the entire worktree directory** (not just empties it). Git branch may or may not survive — observed both outcomes even for worktrees 1-2 days old. **Cannot be disabled** — it's compiled into the OpenCode binary with no config knob. Error in kimaki.log:
   ```
   [ERROR] [OPENCODE] cleanup failed ... git gc --prune=7.days ... NotFound: FileSystem.access (<worktree-path>)
   ```
   The error appears AFTER the directory is already gone — the GC is a downstream effect, not the cause.

2. **Our cron job (04:00, `3fca63db50fc`)**: `kimaki-worktree-cleanup.py --apply` deletes worktrees inactive >14 days — both directory AND git branch. This is controllable (edit/remove the cron job). Check with: `hermes cron list`.

The DB (`thread_workspaces` table) survives both cleanups. Only the local checkout on disk is deleted by #1; #2 also deletes the branch.

### ⚠️ Two broken scripts (fixed Aug 2026)

**Bug 1: WIP auto-commit queries wrong table**

The WIP auto-commit script (`kimaki-wip-autocommit.sh`, cron `76d12211602a`, runs 01:50) queries `thread_worktrees` table, but Kimaki registers worktrees in `thread_workspaces`. Result: the script **silently skips all modern worktrees** and never commits WIP changes before GC.

**Impact**: Uncommitted work IS lost when OpenCode GC runs. The script reports "Ingen aktive worktrees funnet" even when worktrees exist and have uncommitted changes.

**Fix**: Updated `~/.hermes/scripts/kimaki-wip-autocommit.sh` to query `thread_workspaces` instead of `thread_worktrees`. Also updated column references from `worktree_name`/`worktree_directory` to `workspace_name`/`workspace_directory`.

**Bug 2: Kimaki cleanup queries wrong table and deletes recent branches**

The Kimaki cleanup script (`kimaki-worktree-cleanup.py`, cron `3fca63db50fc`) had the same table bug — it queried `thread_worktrees` instead of `thread_workspaces`. Additionally, when it found a worktree directory was missing (deleted by OpenCode's GC), it would **delete the git branch** even if the worktree was only 1-2 days old.

**Impact**: For worktrees deleted by OpenCode's GC, the cleanup script would also delete the git branch, making recovery impossible. The script ran at 04:00, so any worktree deleted by OpenCode's GC at 02:00 would have its branch deleted 2 hours later.

**Fix**: Rewrote `kimaki-worktree-cleanup.py` as a 3-phase restore/cleanup script:
- **Phase 1 (Restore)**: Automatically restores worktrees <7 days old that were deleted by OpenCode's GC. Uses `git worktree add` to recreate from the surviving git branch.
- **Phase 2 (Cleanup)**: Deletes worktrees inactive >14 days (both directory and branch).
- **Phase 3 (Orphans)**: Removes orphaned worktree directories not tracked in the DB.

Cron job moved from 04:00 to **02:15** (15 minutes after OpenCode's GC at 02:00) to minimize downtime.

## Diagnosis (what to check)

### 1. Confirm the worktree directory vanished
```bash
ls -la ~/.kimaki/worktrees/<hash>/
# Empty directory => worktree was cleaned up
```

### 2. Check how many worktrees are affected
```bash
# Count empty vs non-empty worktree dirs
empty=$(find ~/.kimaki/worktrees/ -maxdepth 2 -type d -empty 2>/dev/null | wc -l)
full=$(find ~/.kimaki/worktrees/ -maxdepth 2 -mindepth 2 -type d 2>/dev/null | wc -l)
echo "Empty: $empty / Non-empty: $full"
# Typical state: 44 empty, 7 non-empty
```

### 3. Query the Kimaki DB
The `discord-sessions.db` SQLite DB has two relevant tables:

```python
import sqlite3
db = sqlite3.connect("/home/erik/.kimaki/discord-sessions.db")
c = db.cursor()

# thread_workspaces (newer, 194 rows) — has the worktree for this thread
c.execute("SELECT * FROM thread_workspaces WHERE thread_id = '<thread_id>'")

# thread_worktrees (older, 157 rows) — may NOT have an entry for recently-created worktrees
c.execute("SELECT * FROM thread_worktrees WHERE thread_id = '<thread_id>'")

# Check status distribution
c.execute("SELECT status, COUNT(*) FROM thread_workspaces GROUP BY status")
c.execute("SELECT status, COUNT(*) FROM thread_worktrees GROUP BY status")
```

Key finding: **`thread_workspaces` has the "ready" entry with workspace_directory. `thread_worktrees` may be empty for that thread. Kimaki's `getThreadWorktree()` only queries `thread_worktrees`**, so a thread created after the migration to `thread_workspaces` will have no worktree info from that function. The worktree is still resolved via a separate code path (likely the VOICE/SESSION handler).

### 4. Check Kimaki log
```bash
grep "38586ea2\|<worktree_name>" /home/erik/.kimaki/kimaki.log
```

Expected log pattern for a cleaned-up worktree:
```
[LOG] [DISCORD] Message in thread ⬦ <thread name> (<thread_id>)
[LOG] [DISCORD] Using project directory: <project_dir> (worktree: <missing_path>)
[LOG] [VOICE] [SESSION] Found session <session_id> for thread <thread_id>
```
The worktree path is logged but the agent then fails because the directory doesn't exist.

## Recovery steps

### 1. Locate the project and branch
From the DB or log:
- Project directory: the repo root (e.g. `/home/erik/Projects/serenahome`)
- Branch name: e.g. `opencode/kimaki--jg-nskr--lgg-tl-anlystcs-vd-brk-av-um`
- Worktree path: e.g. `/home/erik/.kimaki/worktrees/38586ea2/-jg-nskr--lgg-tl-anlystcs-vd-brk-av-um`

Query the DB:
```python
python3 -c "
import sqlite3, os
db = sqlite3.connect(os.path.expanduser('~/.kimaki/discord-sessions.db'))
for r in db.execute(\"SELECT thread_id, workspace_name, workspace_directory, project_directory FROM thread_workspaces WHERE workspace_directory LIKE '%<hash>%'\"):
    print(r)
"
```

### 2. Verify the git branch exists
```bash
cd <project_directory>
git branch -a | grep <worktree_branch_fragment>
```

### 3a. If branch exists → recreate worktree
```bash
cd <project_directory>
git worktree add <worktree_path> <branch_name>
```

### 3b. If branch is GONE → find the project's main dev branch
The Kimaki branch may have been deleted — even for worktrees only 1-2 days old, OpenCode GC can delete both the directory AND the branch. Check if the project has a main development branch with all the work:

```bash
cd <project_directory>
git branch -a
git log --oneline <candidate_branch> --since="<date thread was active>"
```

Common pattern: projects use `v2`, `develop`, or `main` as the real dev branch. The Kimaki branch was just a working copy. If the candidate branch has commits matching the thread's work, point the worktree there:

```bash
git worktree add <worktree_path> <candidate_branch>
```

**Example**: Thread "lag en v2 av rasletind en nett" — Kimaki branch gone (worktree was only 1-2 days old!), but `v2` branch had all 27 commits (fase0 + fase1). Recreated worktree on `v2`.

### 4. Verify
```bash
cd <project_directory> && git worktree list
# Should show all 3: main repo, recovered worktree, any other active worktrees
```

## Code reference
The relevant Kimaki source:
- `database.js:getThreadWorktree()` — queries `thread_worktrees` table only
- `discord-bot.js:399-428` — checks worktree status before routing message
- `discord-bot.js:427` — logs the worktree path being used
- `worktrees.js:createWorktreeWithSubmodules()` — creates new worktrees (not called on resume)

## Why it happens

OpenCode's snapshot service periodically runs `git gc --prune=7.days` on snapshot repos. Each snapshot repo points to the Kimaki worktree directory via its `worktree` git config. The GC deletes the entire worktree directory (not just empties it). The git branch may or may not survive — we've observed both outcomes even for worktrees 1-2 days old. The "cleanup failed" messages in the log (168+ occurrences) are from this service failing when the directory is already gone. The `thread_workspaces` DB status is never updated to reflect the physical deletion, so Kimaki silently passes a stale path to the agent.

**Two additional bugs were found and fixed (Aug 2026)**:

1. Both the WIP auto-commit and Kimaki cleanup scripts queried `thread_worktrees` (old table) instead of `thread_workspaces` (current table). This caused WIP auto-commit to skip all worktrees, and the cleanup script to delete branches for recently-deleted worktrees.

2. The cleanup script at 04:00 would delete git branches for worktrees that OpenCode's GC deleted at 02:00, even if the worktrees were only 1-2 days old. This made recovery impossible.

**Current state (post-fix)**:
- WIP auto-commit (01:50): Preserves uncommitted changes before GC
- OpenCode GC (02:00): Deletes worktree directories
- Restore & Cleanup (02:15): Automatically restores recent worktrees, cleans up old ones
