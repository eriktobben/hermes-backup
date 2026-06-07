# Zombie OpenCode Server Processes (Kimaki)

## Symptom pattern
- Bot works initially, then gradually degrades over days.
- `reply for unknown request` warnings appear for question/dropdown interactions — even in non-worktree sessions.
- Model timeouts (`Upstream idle timeout exceeded`) become more frequent.
- Slash commands (`/model`, `/restart-opencode-server`) work but select menus (question dropdowns) don't respond.

## Root cause
Each Kimaki process tracks exactly one opencode server in its `singleServer` in-memory variable. When Kimaki restarts (upgrade, crash, SIGKILL), the old server process is orphaned (reparented to PID 1) because:

1. `process.on('exit')` handlers do **not** run on SIGKILL.
2. The new Kimaki instance starts with `singleServer = null` — it has no way to discover orphaned processes.
3. Each `/restart-opencode-server` only kills the **currently tracked** server, not orphans from previous incarnations.

Over time, orphaned `opencode serve` processes accumulate, each consuming ~300–900MB RSS and binding many ephemeral ports.

## Diagnostic command
```bash
# List ALL opencode serve processes with age and memory
ps -eo pid,rss,%mem,etime,args | grep 'opencode serve' | grep -v grep
```

Healthy: one process (young, started by current Kimaki run).
Unhealthy: 2+ processes, especially if any show ELAPSED of multiple days.

## Immediate fix
```bash
# Kill all orphaned opencode servers (graceful first)
kill -15 <pid1> <pid2>
# Verify they're gone
ps -eo pid,args | grep 'opencode serve' | grep -v grep
# Then run /restart-opencode-server in Discord for a clean slate
```

## Why this causes "reply for unknown request"
Question/dropdown interactions follow this flow:

1. OpenCode creates a question → Kimaki builds a Discord select menu.
2. User picks an option → Discord sends component interaction → Kimaki sends reply to OpenCode.
3. If the reply reaches a **stale** server (orphaned from a previous incarnation), that server doesn't know about the question (different process, different in-memory state) → `reply for unknown request`.
4. The active server (tracked by current Kimaki) never receives the reply → dropdown appears to do nothing.

This is exacerbated when multiple servers are running because Kimaki's client cache may round-robin or connect to the wrong one.

## Prevention
- After any Kimaki upgrade or restart: run `/restart-opencode-server` in Discord to guarantee a clean server.
- Consider adding a startup check that kills any pre-existing `opencode serve` processes before spawning a new one (not yet implemented in kimaki v0.13.x).
