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
