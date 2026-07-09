# Bun Runtime Degradation — `err_15f5fc94` Variant

## Occurrence
2026-07-09 — Tobben's session: `err_15f5fc94` instead of the previously documented `err_e2b0c342`. Same root cause, different error ref.

## Forward diagnosis rule
**The error ref is NOT a stable identifier.** Each occurrence generates a unique ref (e.g. `err_e2b0c342`, `err_15f5fc94`, `err_<random>`). Do NOT match against a specific ref string — instead:

1. Look for the `posix_spawn('/bin/sh') ENOENT` line in PM2/Kimaki error logs.
2. Or match the stack trace pattern: `execAsync` → `createWorktreeCore` → `child_process:179`.
3. Or grep for `UnknownError` + `"message":"Unexpected server error"` in Kimaki logs.

## Session-specific detail (2026-07-09)

### Symptom
```
🌳 Worktree: opencode/kimaki--kn-d-g-gjnnm-all-tstr-og-vrfsr-at-d
❌ Workspace creation failed: {"name":"UnknownError","data":{"message":"Unexpected server error. Check server logs for details.","ref":"err_15f5fc94"}}
```

### Full error chain (from `pm2 logs kimaki --lines 20`)
```
OPENCODE at <anonymous> (node:child_process:179:32)
OPENCODE at execAsync (kimaki/dist/exec-async.js:7:25)
OPENCODE at createWorktreeCore (kimaki/dist/git-worktree-core.js:254:32)
OPENCODE at async create (kimaki/dist/kimaki-workspace-adaptor.js:57:34)
```

### Environmental state at failure
- **Kimaki** (PM2): uptime 3D, PID 2568038
- **`opencode serve`** (standalone): uptime since Jul06 (~3 days), PID 2568082, originally on port 33333
- **Port conflict?** No — nothing else on 33333
- **`/bin/sh` on disk**: exists and works from shell
- **Worktree**: directory created at `.kimaki/worktrees/6c5a794b/` but **empty** — `git worktree add` did not complete
- **Session**: Discord thread was still created (renamed to "⬦ Verifiser mocking i tester") despite worktree failure — Kimaki fell through

### Fix applied
1. Identified the opencode server was **standalone** (not under PM2):
   ```bash
   ps aux | grep 'opencode serve' | grep -v grep
   # → /home/erik/.npm-global/bin/opencode serve --port 33333 --print-logs --log-level WARN
   ```
2. Killed the server:
   ```bash
   pkill -f "opencode serve"
   ```
3. Kimaki auto-started a replacement on a random port (33861):
   ```bash
   # New PID, new port — auto-detected
   /home/erik/.npm-global/bin/opencode serve --port 33861 --print-logs --log-level WARN
   ```
4. Verified the new server responded HTTP 200.

### Key differences from `err_e2b0c342` pattern
| Aspect | `err_e2b0c342` (previous) | `err_15f5fc94` (this session) |
|--------|---------------------------|-------------------------------|
| Error ref | `err_e2b0c342` | `err_15f5fc94` |
| Server mgmt | Under PM2 | Standalone (direct `opencode serve`) |
| Kimaki mgmt | Under PM2 | Under PM2 |
| Fix | `pm2 restart kimaki` | `pkill -f "opencode serve"` |
| Session created? | N/A | Yes (fallthrough) |
| Worktree state | N/A | Empty directory, no git worktree |

### Prevention takeaway
Neither PM2 nor standalone opencode server setups survive the ~44h Bun degradation window on their own. The opencode server process must be restarted periodically regardless of how it's managed.
