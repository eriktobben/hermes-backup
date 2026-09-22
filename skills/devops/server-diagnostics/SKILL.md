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

### Safe to delete without asking:
1. **OpenCode snapshots**: `rm -rf ~/.local/share/opencode/snapshot/*` (often 10-15GB)
2. **npm cache**: `rm -rf ~/.npm/_cacache`
3. **pip cache**: `rm -rf ~/.cache/pip`
4. **pnpm store**: `rm -rf ~/.local/share/pnpm/store`
5. **Old npx cache**: `find ~/.npm/_npx -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +`

### Ask user before deleting:
- Kimaki worktrees (check for active processes and uncommitted changes first)
- Project directories
- Any directory with recent modification dates

### Verify uncommitted changes before deleting worktrees:
```bash
for dir in ~/.kimaki/worktrees/*/; do
  find "$dir" -name ".git" -type d 2>/dev/null | while read gitdir; do
    repodir=$(dirname "$gitdir")
    cd "$repodir" && git status 2>/dev/null | grep -E "Changes to be committed|Changes not staged|Untracked files"
  done
done
```

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
- **OpenCode snapshots are cache, not data**: Safe to delete. They're cached file states from previous sessions.
- **Kimaki worktrees with active PHP/Node processes must NOT be deleted**: Always check for running processes first.
- **Swap exhaustion causes cascading failures**: When swap is full, the OOM killer starts terminating processes. Restart heavy processes (especially OpenCode) before this happens.
- **After cleanup, restart heavy processes**: OpenCode and other long-running processes may have accumulated memory leaks or stale state. A restart frees memory and resets swap usage.
- **Kimaki worktree dependencies add up**: Each feature branch dir has ~500MB of vendor/node_modules. 30+ inactive dirs = 15GB. Clean dependencies from inactive dirs only.

## Target metrics
- Disk: below 85%
- Swap: below 50%
- Load average: below CPU core count