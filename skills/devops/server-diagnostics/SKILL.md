---
name: server-diagnostics
description: Check server health when apps are slow or unresponsive.
tags: [server, diagnostics, disk, memory, performance, cleanup]
---

# Server Diagnostics

## When to use
Use when the user reports slow performance, unresponsive applications (especially OpenCode), or asks to check if the server is overloaded.

## Diagnostic sequence

Run these checks in order. **Disk is checked first** because it's the most common cause of unresponsiveness.

### 1. Quick health check
```bash
uptime          # load average
df -h /         # disk usage
free -h         # RAM + swap
top -bn1 | head -20  # top processes
```

**Key indicators:**
- **Disk at 90%+**: Critical — applications will hang. This is the #1 cause of unresponsiveness.
- **Swap at 80%+**: System is memory-pressure. Heavy processes should be restarted.
- **Load average > CPU cores**: CPU bottleneck.

**The chain of causation**: Disk at 100% → swap operations fail → applications cannot write temp files or logs → apps hang/become unresponsive. This is why OpenCode becomes unresponsive when disk is full — it's not a RAM or CPU issue.

### 2. Find disk consumers
```bash
du -h --max-depth=1 /home/erik 2>/dev/null | sort -hr | head -20
```

**Check opencode.db explicitly** — it is a single file that can dwarf everything else, and most of it may be reclaimable dead space:
```bash
ls -lh ~/.local/share/opencode/opencode.db*
python3 -c "import sqlite3; db=sqlite3.connect('file:' + __import__('os').path.expanduser('~/.local/share/opencode/opencode.db') + '?mode=ro', uri=True); print('pages:', db.execute('PRAGMA page_count').fetchone()[0], 'freelist:', db.execute('PRAGMA freelist_count').fetchone()[0], 'page_size:', db.execute('PRAGMA page_size').fetchone()[0])"
```
`freelist × page_size` = reclaimable GB via `VACUUM`. Never run VACUUM while `opencode serve` processes hold the db — coordinate with the user first.

**When `du` times out**: The disk is so full that filesystem I/O is struggling. Work in smaller chunks — check individual directories instead of the whole tree.

### 3. Find memory consumers
```bash
ps aux --sort=-%mem | head -10
```

### 4. Check for active processes in directories before cleanup
```bash
# Check kimaki worktrees
for dir in ~/.kimaki/worktrees/*/; do
  name=$(basename "$dir")
  count=$(ps aux | grep -E "php|node" | grep -v grep | grep -c "$dir" 2>/dev/null)
  if [ "$count" -gt 0 ]; then
    echo "$name: AKTIV ($count processes)"
  fi
done
```

## Cleanup procedure

### Hard gate: never delete without explicit approval
Present findings and a proposed deletion list, then WAIT for the user's yes. No item is pre-approved — not even regenerable caches. If the user says "ask me first" once, that applies to everything for the rest of the session. Deleting before approval and reporting after is a correction-worthy failure even when the target was cache.

### Candidate list — what to PROPOSE, not what to delete

Regenerable caches (propose without deeper checks):
1. **OpenCode snapshots**: `rm -rf ~/.local/share/opencode/snapshot/*`
2. **npm cache**: `rm -rf ~/.npm/_cacache`
3. **uv/pip caches**: `rm -rf ~/.cache/uv ~/.cache/pip`
4. **pnpm store**: `rm -rf ~/.local/share/pnpm/store`
5. **Old npx/bunx caches**: `find ~/.npm/_npx -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +`, `/tmp/bunx-*`
6. **Stale /tmp test dirs**: e.g. `find /tmp/opencode -maxdepth 1 -type d -mtime +2` — check `lsof +D <dir>` for open handles first

Needs verification before proposing:
- **opencode.db** — often the single biggest item (23 GB seen; 16 GB was freelist). Diagnose with `PRAGMA page_count` / `PRAGMA freelist_count` (see "Find disk consumers"); a VACUUM reclaims it, but only when no `opencode serve` process holds the db.
- Kimaki worktrees and project session worktrees — verification flow below.
- Project directories; anything with recent modification dates.
- System-level items (old snap revisions, apt cache, journal): need root. Check `sudo -n true` first; if it fails, give the user the exact commands to run themselves instead of failing mid-cleanup.

### Verify a worktree dir is safe to delete
Two criteria must BOTH hold:
1. No active processes pointing into the dir (step 4 above).
2. Clean AND pushed — every sub-repo's work is on origin.

```bash
# In a git worktree .git is a FILE, not a directory — never pass -type d here
for dir in ~/.kimaki/worktrees/*/ /path/to/project/.worktrees/*/; do
  find "$dir" -maxdepth 2 -name ".git" 2>/dev/null | while read gitfile; do
    repodir=$(dirname "$gitfile")
    dirty=$(git -C "$repodir" status --porcelain 2>/dev/null | wc -l)
    branch=$(git -C "$repodir" branch --show-current)
    ahead=$(git -C "$repodir" rev-list --count "origin/$branch..HEAD" 2>/dev/null)
    echo "$(basename "$repodir"): dirty=$dirty branch=${branch:-DETACHED} ahead=$ahead"
  done
done
```

- `dirty=0` and `ahead=0` → the branch lives on origin; deleting the worktree dir loses nothing (the branch survives in the main repo, confirmed via `git rev-parse --git-common-dir`).
- `ahead>0` or detached HEAD → do NOT delete; offer to push first.

### Session worktrees inside projects
Opencode/kimaki sessions create `.worktrees/session-*` dirs inside projects — 30-50 dirs × ~300-400 MB = 8-9 GB per project seen. Apply the same verification flow (active processes, dirty, pushed) to each before proposing deletion; recent ones (< a few days) are usually still in play.

## Kimaki worktree dependency cleanup
Each kimaki worktree with feature branches has its own `vendor/` + `node_modules/` (~400-500MB each). With many inactive worktrees, this adds up to 10-15GB.

**Before deleting vendor/node_modules:**
1. Check which subdirectories have active PHP/Node processes
2. Only clean dependencies from inactive subdirectories
3. The main worktree (e.g., `3b985546`) contains many sub-feature-dirs — treat each separately

```bash
# Example: clean inactive kimaki subdirectories
ACTIVE=("-admnpnlt-admn-sr-ikk-br-ut-hr-nsk" "-other-active-dir")
for dir in ~/.kimaki/worktrees/<hash>/*/; do
  name=$(basename "$dir")
  skip=false
  for active in "${ACTIVE[@]}"; do
    if [ "$name" = "$active" ]; then skip=true; break; fi
  done
  if [ "$skip" = true ]; then continue; fi
  rm -rf "$dir/vendor" "$dir/node_modules"
done
```

## "Is this project safe to delete?" verification flow
When user asks if a project can be deleted:
1. Check git status: `cd <project> && git status` — working tree clean?
2. Check remote: `git remote -v` — is code on origin?
3. Check disk breakdown: `du -h --max-depth=1 <project>` — what's taking space?
4. Many projects have `python/venv` (5GB+) or `node_modules` that can be deleted and recreated
5. Present findings to user before deleting

## Pitfalls

- **Disk at 100% causes `du` timeouts**: The filesystem I/O is overwhelmed. Use shorter timeouts and check directories individually.
- **"Regenerable" does not mean "pre-approved"**: OpenCode snapshots, npm/uv caches and bunx caches are safe *content-wise*, but this user requires explicit approval before ANY deletion — propose, then wait. Deleting first and reporting after is the failure mode, even for caches.
- **Worktree deletion needs BOTH checks**: no active processes AND clean+pushed (`dirty=0`, `rev-list --count origin/<branch>..HEAD` = 0). A clean worktree can still hold unpushed commits; a pushed branch can still have an active dev process in the dir.
- **In git worktrees `.git` is a FILE, not a directory**: `find ... -name ".git" -type d` silently finds nothing and the check "passes" vacuously. Drop `-type d`.
- **A deleted worktree does not lose the branch**: the branch lives in the main repo's `.git` (confirm with `git rev-parse --git-common-dir`). Only uncommitted/unpushed work is at risk — which is why the push-state check is the real gate, not "does it have a .git".
- **Root cleanup may be impossible non-interactively**: snap revisions, apt cache and journal vacuum need sudo; check `sudo -n true` first, and if it fails hand the user the exact commands instead of failing halfway through a cleanup.
- **Swap exhaustion causes cascading failures**: When swap is full, the OOM killer starts terminating processes. Restart heavy processes (especially OpenCode) before this happens.
- **After cleanup, restart heavy processes**: OpenCode and other long-running processes may have accumulated memory leaks or stale state. A restart frees memory and resets swap usage.
- **Kimaki worktree dependencies add up**: Each feature branch dir has ~500MB of vendor/node_modules. 30+ inactive dirs = 15GB. Clean dependencies from inactive dirs only.

## Target metrics
- Disk: below 85%
- Swap: below 50%
- Load average: below CPU core count