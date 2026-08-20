---
name: discord-agent-runtime-diagnosis
description: Diagnose Discord bot agent failures where threads show footer/model status but no final response. Separates model execution issues from transport/listener and session DB persistence failures.
---

# Discord Agent Runtime Diagnosis

Use this when a Discord-integrated coding agent (Kimaki/OpenCode-style) appears to start correctly (thread created, model footer shown) but users get no usable reply.

## Trigger signals
- "Only footer appears" / "using <model> but nothing else happens"
- Reconnect loop logs such as `Stream ended normally ... reconnecting in 500ms`
- Intermittent `No OpenCode client for thread ...`
- Session DB insert failures around `session_events`

## Core guardrail: split pipeline before blaming model
Do **not** assume model/provider regression first.

Run a three-way split-check:
1. **Model execution**: confirm whether model generated content (e.g., `kimaki session read <sessionId>`).
2. **Transport/listener**: inspect stream lifecycle (`Connected`/`Stream ended normally` loops).
3. **Persistence/state**: inspect SQLite mappings and event inserts (`thread_sessions`, `session_events`).

If (1) is true but Discord has no response, treat it as transport/persistence/runtime orchestration issue until disproven.

## Fast diagnostic sequence
1. Capture thread ID + mapped session ID.
2. Verify live process status (PM2) and immediate logs.
3. Read session transcript directly from source runtime.
4. Query DB for mapping + event counts for the thread.
5. Check for repeated reconnect loop pattern.
6. Check for failed insert patterns in logs (`Failed query: insert into "session_events" ...`).

## Controlled DB reset playbook (when state is corrupted)
Use only after taking a backup and confirming config tables are healthy.

1. Stop bot process (PM2).
2. Backup `~/.kimaki/discord-sessions.db` with timestamp.
3. Clear volatile runtime tables that commonly wedge delivery:
   - `session_events`
   - `part_messages`
   - `thread_sessions`
   - `thread_worktrees`
   - `session_models`
   - `ipc_requests`
4. Preserve durable config tables:
   - `bot_tokens`
   - `channel_directories`
   - `channel_models`
   - `global_models`
   - `channel_worktrees` (unless intentionally toggling)
5. Run `PRAGMA integrity_check`, then `VACUUM`.
6. Restart bot and run deterministic smoke test (`kimaki send --wait` with a short prompt like `PONG`).

## Worktree-mode instability signals
If failures happen only after enabling auto worktrees, treat worktree orchestration as suspect even when non-worktree threads pass.

Strong signals:
- Thread starts and worktree initializes successfully, then session stalls mid-task.
- `question requested` followed by `reply for unknown request` in same session.
- Intermittent `Aborted process` around concurrent sessions while worktree threads are active.

Mitigation:
1. Disable `channel_worktrees.enabled` for affected channel.
2. Restart bot.
3. Keep non-worktree mode as baseline.
4. Re-enable with canary rollout (single test channel/thread cohort) before broad enablement.

## Zombie opencode server accumulation
If the bot has been running for days uninterrupted and users report select dropdowns not responding, model timeouts (`Upstream idle timeout exceeded`), or `reply for unknown request` warnings — check for orphaned `opencode serve` processes.

### Detection
```bash
ps -eo pid,rss,%mem,etime,args | grep 'opencode serve' | grep -v grep
```

Healthy: one process, recent start time. Unhealthy: 2+ processes, especially with ELAPSED of multiple days (orphans from previous Kimaki incarnations).

### Root cause
Kimaki tracks exactly one server (`singleServer` in-memory). When the Kimaki process is killed (SIGKILL during upgrade, crash), the child opencode server is orphaned to PID 1. On restart, the new Kimaki has no way to discover it. Each `/restart-opencode-server` only kills the *currently tracked* server. Over weeks, orphaned processes accumulate, each consuming ~300–900MB and binding ports, eventually causing communication failures.

### Fix
```bash
kill -15 <orphan-pid1> <orphan-pid2>
```
Then run `/restart-opencode-server` in Discord for a clean slate.

### Prevention
After any Kimaki upgrade or manual restart, always run `/restart-opencode-server` to guarantee no orphaned processes remain. See `references/zombie-opencode-servers.md` for full analysis.

## Bun runtime degradation — `posix_spawn('/bin/sh')` ENOENT after extended uptime

If workspace creation fails with a `posix_spawn '/bin/sh' ENOENT` error (underlying `UnknownError` with a ref like `err_e2b0c342` or `err_15f5fc94`), the Bun-compiled `opencode serve` binary has developed an internal process-spawning failure.

**Error ref variation:** The leading error ref (e.g. `err_e2b0c342`, `err_15f5fc94`) changes per occurrence — **don't rely on the exact ref for diagnosis**. The real signature is the `child_process` stack trace and `posix_spawn '/bin/sh' ENOENT` in PM2/Kimaki logs.

### Mechanism
- The OpenCode ACP server is a Bun-compiled binary (`opencode`).
- After extended continuous uptime (~44+ hours), Bun's Node.js compatibility layer loses the ability to spawn `/bin/sh` for `child_process.exec()` calls (used by `createWorktreeCore` → `execAsync`).
- This is NOT a filesystem issue — `/bin/sh` exists, works from shell, and works from fresh Bun processes.
- It is a Bun runtime degradation, likely memory corruption or internal state drift inside the single long-lived process.

### Early-warning signals (precede the hard failure)
- Repeated `service=snapshot exitCode=1 stderr= cleanup failed` warnings in Kimaki logs.
- `service=snapshot exitCode=128 stderr=fatal: gc is already running` — git operations stalling.
- Workspace creation eventually fails hard with an `UnknownError` / `err_xxx` reference.

### Detection — standalone vs PM2-managed server
The opencode server may run in two configurations:

**PM2-managed** (common):
```bash
pm2 list | grep opencode
# or inspect Kimaki's child processes
```

**Standalone** (not under PM2 — started directly):
```bash
ps aux | grep 'opencode serve' | grep -v grep
```
Independent server processes survive Kimaki restarts and must be killed directly.

### Fix

**If under PM2:**
```bash
pm2 restart kimaki
```
This kills the Kimaki Node.js process and its child OpenCode server. PM2 restarts Kimaki, which spawns a fresh OpenCode server with a clean Bun runtime.

**If standalone (not under PM2):**
```bash
# Kill the server process directly
pkill -f "opencode serve"
# Or with a specific PID:
kill <pid>
```
After killing, Kimaki typically auto-starts a new opencode server on a random port (detectable via `ps aux | grep opencode`). Verify the new server responds:
```bash
# Find the new port
ps aux | grep "opencode serve" | grep -v grep
curl -s -o /dev/null -w "%{http_code}" http://localhost:<new-port>/
```

### Kimaki fallthrough — session created despite worktree failure
Kimaki may still create the Discord session (thread renamed, `[INGRESS] promptAsync accepted` logged) even when `git worktree add` fails. The session runs without an isolated worktree. Evidence:
- Discord thread shows the renamed title and model footer.
- `.kimaki/worktrees/<hash>/` directory exists but is **empty** (no git data).
- `git worktree list` in the project repo shows only the main checkout.
- `cleanup failed` is logged after the error.

If this happens, the session is functional but uses the main checkout rather than a worktree. The empty worktree directory can be cleaned up:
```bash
rmdir ~/.kimaki/worktrees/<hash>/
```

### Prevention
- Monitor Kimaki **and opencode server** uptime. If either is >48h, schedule a periodic restart during low-activity hours.
- Watch for `cleanup failed` warning clusters in logs — they precede the hard failure.
- After any OpenCode upgrade (`opencode upgrade`), restart the server immediately.
- See `references/bun-runtime-degradation-err-variant.md` for session-specific reproduction details.

## Session-scoped LLM failure pattern (important)
Do not treat all "stopped replying" reports as global runtime outages.

A frequent pattern is **one thread/session failing while others keep completing**.

Strong signals in logs:
- Failing thread shows `service=llm ... AI_APICallError` for its `session.id`.
- Healthy comparator thread (same bot/time window) still shows `DURATION ...` and `[ASSISTANT COMPLETED]`.
- Question-flow desync appears in failing thread: `reply for unknown request`.

Interpretation:
- This points to a **session-scoped provider/request-state failure** (or stale question state), not a total Discord gateway/runtime failure.

Immediate mitigation order:
1. Keep the bot running if other threads are healthy (avoid unnecessary global restarts).
2. Recover the failing thread/session first (archive session or force a new session on next message).
3. If desync repeats, archive thread and create a fresh thread in same channel as canary.
4. Escalate to global restart/DB reset only if failures spread beyond one/few sessions.

## Broken OpenCode plugin causing silent gateway death after restart

A broken plugin in `~/.config/opencode/plugins/` can cause Kimaki to appear healthy (bot connected, channels found, slash commands registered) while the Discord gateway silently stops delivering messages.

### Mechanism
1. OpenCode **auto-discovers** `.js` files in `~/.config/opencode/plugins/` — having a file there causes it to be loaded, even if not referenced in any config.
2. A plugin with wrong export type (e.g. exporting an object/class instead of a function) causes `Plugin export is not a function` errors at every session startup (~30 errors in rapid succession).
3. The plugin errors don't crash the server, but after a Kimaki restart the gateway connection can silently die — the bot reports "Connected to Discord!" and "Found N channel(s)" but receives zero events.

### Detection
- Bot appears healthy in PM2 (`online`, recent uptime) but no `DISCORD Message in thread` entries appear in logs after startup.
- `claude-mem.js` or similar `failed to load plugin ... Plugin export is not a function` errors spam at startup.
- Previous sessions were working, then Kimaki was restarted, and messages stopped arriving.

### Fix
1. Identify broken plugins:
   ```bash
   ls ~/.config/opencode/plugins/
   ```
2. Move broken plugins out of the way:
   ```bash
   mv ~/.config/opencode/plugins/broken-plugin.js ~/.config/opencode/plugins/broken-plugin.js.disabled
   ```
3. Remove from `~/.config/opencode/opencode.json` plugin array if referenced there.
4. Restart Kimaki — **may need two restarts** for gateway to fully re-establish:
   ```bash
   pm2 restart kimaki
   ```
5. Verify messages arrive by checking logs for `DISCORD Message in thread` entries.

### Pitfall
The first restart after clearing a broken plugin may not fully restore gateway event delivery. If no messages arrive within 1-2 minutes after the first restart, restart again. The gateway WebSocket connection sometimes needs a clean startup without plugin error noise to properly subscribe to events.

## Common pitfall
A brand-new Discord thread can still fail with "no response" even when context is small; this does **not** prove context-window overflow. The model may have produced output while listener/persistence broke before Discord delivery.

## Provider/parser null-payload failure pattern (`HTTP None` + `NoneType is not iterable`)
This is a distinct failure mode from Discord delivery issues.

Strong signals:
- User sees: `Non-retryable error (HTTP None)` and `'NoneType' object is not iterable`.
- `agent.log` contains: `Non-retryable client error: 'NoneType' object is not iterable`.
- `gateway.run` may log: `Skipping transcript persistence for failed request ... to prevent session growth loop`.

Interpretation:
- The failure occurred in model/provider client handling (or response parsing) **before** a normal HTTP status was surfaced.
- `HTTP None` is therefore expected in this mode and should not be misread as a Discord transport outage.

Triage and containment:
1. Confirm recurrence count and timestamps from `~/.hermes/logs/agent.log`.
2. Check whether failures are tied to a single session ID (session-scoped poisoning is common).
3. Start a fresh chat/session instead of continuing the failing one.
4. Restart gateway/service only if the pattern continues across new sessions.
5. If recurring, capture a compact evidence bundle (time, session_id, ±30–50 log lines around each hit) for upstream bugfix.

## References
- `references/footer-only-no-response.md` — concrete log signatures, SQL probes, and interpretation for the footer-only/no-response failure mode.
- `references/worktree-mid-session-stall.md` — signs and mitigation when auto-worktree threads stop mid-run despite healthy base runtime.
- `references/session-scoped-llm-failure.md` — how to diagnose and recover when one thread hits `AI_APICallError` while others still complete.
- `references/http-none-nonretryable.md` — `HTTP None`/`NoneType` parser-failure signatures and containment sequence.
- `references/zombie-opencode-servers.md` — how orphaned opencode server processes accumulate, why they cause `reply for unknown request`, and how to clean them up.
- `references/broken-plugin-gateway-death.md` — broken OpenCode plugin causing silent gateway death after restart (claude-mem.js case study).
