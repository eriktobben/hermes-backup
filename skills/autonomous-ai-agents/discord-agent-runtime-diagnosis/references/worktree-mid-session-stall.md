# Worktree Mid-Session Stall (Kimaki/OpenCode)

## Symptom pattern
- Auto-worktree thread starts normally (worktree created, submodules/npm install done).
- Session accepts prompt and may progress partially.
- Thread then appears to stop responding mid-task.

Typical log sequence:
- `DISCORD [WORKTREE] Creating worktree: ...`
- `WORKTREE ... initialized`
- `SESSION [INGRESS] promptAsync accepted ...`
- `Question requested ...`
- `reply for unknown request` (warning)
- Subsequent user messages accepted, but no stable completion flow for affected thread.

## What this means
This is usually orchestration/state drift in question/session handling under worktree mode, not a pure model failure.

**Important:** `reply for unknown request` is not exclusive to worktree mode. It can also be caused by zombie opencode server processes (see `references/zombie-opencode-servers.md`). Always check for orphaned servers first if worktree mode is not the common factor.

## Quick checks
1. Confirm affected thread uses worktree path (`Using project directory ... (worktree: ...)`).
2. Compare with simultaneous non-worktree sessions: if they complete normally, core runtime is likely healthy.
3. Check for concurrent `Aborted process` events around same timeframe.

## Immediate mitigation
1. Disable auto worktrees for affected channel (`channel_worktrees.enabled = 0`).
2. Restart bot process.
3. Continue operations in non-worktree mode.

## Re-enable strategy
- Use canary rollout only:
  - one channel or small thread cohort,
  - observe for `reply for unknown request`, repeated aborts, or missing `ASSISTANT COMPLETED`.
- If any recur, roll back to non-worktree mode and capture IDs + log window for upstream issue.
