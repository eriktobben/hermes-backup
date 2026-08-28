# Stuck Branch Worktree Fix

## Problem
When Kimaki tries to create a worktree but the branch name is already registered in git's worktree system (from a previous failed/interrupted creation), git refuses with:
```
fatal: 'opencode/kimaki--prntfnksjn-kn-d-lg-en-sd-hvr-mn-kn' is already used by worktree at '/home/erik/.kimaki/worktrees/a9b1eb4f/-prntfnksjn-kn-d-lg-en-sd-hvr-mn-kn'
```

## Diagnosis
1. Check if the branch exists: `cd <project-dir> && git worktree list | grep <branch-slug>`
2. The branch may exist in `git worktree list` output even if the directory is gone or corrupted
3. The worktree directory might exist but be incomplete (no `.git` file, or wrong content)

## Fix Sequence
```bash
# 1. Prune stale worktree references
cd <project-directory>
git worktree prune

# 2. Delete the stuck branch
git branch -D "opencode/kimaki-<slug>"

# 3. Clean up leftover directories
rm -rf ~/.kimaki/worktrees/<hash>/
rm -rf ~/.kimaki/worktrees/<other-hash>/  # if multiple exist

# 4. Restart Kimaki
pm2 restart kimaki
```

## Root Cause Analysis

### Kimaki Code Path
In `src/worktrees.ts`, the `createWorktreeWithSubmodules` function runs:
```typescript
const createCommand = `git worktree add ${JSON.stringify(worktreeDir)} -B ${JSON.stringify(name)} ${JSON.stringify(targetRef)}`
```

The `-B` flag means: "create branch, and if it already exists, reset it". But git's worktree locking prevents this when the branch is registered to ANY worktree — even stale/corrupted ones.

### Why Branches Get Stuck
1. **Interrupted creation**: If `git worktree add` starts but the process is killed/interrupted before completion
2. **Kimaki error paths**: If Kimaki's error handling deletes the directory but not the git worktree registration
3. **OpenCode GC**: The nightly GC deletes worktree directories but may leave branch registrations

### Prevention (Not Yet Implemented)
Kimaki should run `git worktree prune` before attempting new worktree creation. This is not currently done in the codebase.

## Related Issues
- OpenCode GC deleting worktree directories nightly (covered in main SKILL.md)
- Worktree cleanup cron job at 02:15 (covered in main SKILL.md)
- Kimaki v0.14.0+ SyntaxError in new-worktree.js (covered in main SKILL.md)
