# Worktree cleanup recovery

## Symptom
User says "I worked on a Kimaki thread yesterday, today when I try to continue I get:

```
✗ Directory does not exist or is not accessible: /home/erik/.kimaki/worktrees/<hash>/<worktree-name>
```

## Root cause
OpenCode's snapshot/git-GC cleanup removes stale git worktree directories overnight (~02:00). The DB (`thread_workspaces` table) and git branch survive. Only the local checkout on disk is deleted.

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

### 2. Verify the git branch exists
```bash
cd <project_directory>
git branch -a | grep <worktree_branch_fragment>
```

### 3. Recreate the worktree
```bash
cd <project_directory>
git worktree add <worktree_path> <branch_name>
```

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
OpenCode's `snapshot` service periodically runs git GC and cleanup. The "cleanup failed" messages in the log (168 occurrences in the log) are from this service failing to clean up its own snapshot repos, but the side effect is git worktree removal. The `thread_workspaces` DB status is never updated to reflect the physical deletion, so Kimaki silently passes a stale path to the agent.
