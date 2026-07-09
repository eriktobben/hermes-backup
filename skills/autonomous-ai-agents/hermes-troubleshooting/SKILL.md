---
name: hermes-troubleshooting
description: Systematic diagnostics for Hermes Agent runtime failures — cron jobs, ACP subprocess crashes, provider errors, and delivery issues. Load this skill when a user reports that Hermes itself is broken/throwing/failing, not when an application they're building with Hermes has a bug.
---

# Hermes Troubleshooting

Diagnosis methodology for failures within Hermes Agent itself. This skill covers
finding and interpreting the actual error source when Hermes reports a failure
through its cron delivery, logs, or CLI.

## Principles

1. **Read the output** — Cron jobs save full output to `~/.hermes/cron/output/<job_id>/<date>.md`.
   The error message in the user's chat is a user-facing summary; the real detail is in the file.
2. **Trace the error chain** — Hermes wraps errors multiple times (subprocess → API call →
   agent loop → scheduler → delivery). Always trace back to the original exception type
   and location, not the final user-facing message.
3. **Check the history** — Is the failure consistent or intermittent? Compare last N runs
   by checking output files in the job_id directory.

## Common failure patterns

### ACP subprocess crash → `[Errno 32] Broken pipe`

See `references/hermes-acp-crash-patterns.md` for full details.

**Quick summary:** When a cron job fails with `RuntimeError: [Errno 32] Broken pipe`,
the ACP subprocess (opencode-go / copilot) crashed during execution. The unprotected
`proc.stdin.write()` in `agent/copilot_acp_client.py:492` is the crash site. This is
intermittent, not a permanent configuration problem.

### Kimaki/OpenCode workspace creation fails with Bun posix_spawn ENOENT

**Symptom:** Kimaki reports `Workspace creation failed` with `UnknownError` and a ref like `err_e2b0c342` or `err_15f5fc94`, and the underlying error is `ENOENT: no such file or directory, posix_spawn '/bin/sh'` in logs.

> **Error ref varies per occurrence** — do NOT match on the exact ref string. The real signature is the `child_process` stack trace and `posix_spawn('/bin/sh') ENOENT` in PM2/Kimaki logs. See `expert-skill:discord-agent-runtime-diagnosis` → "Bun runtime degradation" section for full detail.

**Root cause:** The OpenCode ACP server (Bun-compiled `opencode` binary) has been running for 40+ hours. Bun's runtime develops an internal issue where `posix_spawn('/bin/sh')` fails with ENOENT even though `/bin/sh` exists and works from the shell. This prevents git commands from running for worktree creation.

**Detection (server may be PM2-managed or standalone):**
```bash
pm2 list | grep -i opencode
ps aux | grep 'opencode serve' | grep -v grep
```

**Fix**

*If under PM2:*
```bash
pm2 restart kimaki
```

*If standalone (not under PM2):*
```bash
pkill -f "opencode serve"
```
Kimaki will auto-start a replacement on a random port.

**Fallthrough note:** Kimaki may still create the Discord session despite the worktree failure — the thread is renamed and a session is created, just without an isolated worktree. An empty worktree directory is left behind in `.kimaki/worktrees/<hash>/`.

**Prevention:** Consider a weekly cron job to restart both Kimaki and the opencode server (e.g. Sunday night) to avoid the ~44h degradation window.

### Provider connection errors

- `ReadTimeout` / `TimeoutError` — provider slow or unreachable. Check provider status.
- `RateLimitError` / HTTP 429 — provider quota exhausted. Try a fallback or wait.
- `AuthenticationError` / HTTP 401 — API key invalid or expired. Run `hermes setup`.
- `BadRequestError` / HTTP 400 — often context overflow (prompt too long).

### Cron delivery failures

- `no delivery target resolved` — the job has no origin and no home channel configured.
  Check `deliver` field on the job and home channel config for the platform.

### Upstream provider intermittent failure → `Broken pipe` on ALL jobs

When `[Errno 32] Broken pipe` appears on MULTIPLE cron jobs using the **same provider** on
the **same day(s)**, the root cause is likely the upstream provider (opencode.ai, etc.)
dropping TCP connections mid-stream — not a local ACP subprocess crash.

**Key diagnostic: cross-job correlation**

```bash
cronjob action=list
# Check last_status and last_run_at across jobs sharing the same provider
```

If the AI Daily Briefing AND FINN bilvarsel (and any other job on the same provider)
all failed on the same days with the same error, it is a **provider outage**:

| Run | Briefing | FINN | Interpretation |
|-----|:--------:|:----:|----------------|
| Same-day failure (both ❌) | ❌ | ❌ | Upstream provider issue |
| Staggered failure (one ❌, one ✅) | ❌ | ✅ | Job-specific / ACP crash |

The 23–24 June incident showed all opencode-go jobs failing simultaneously — opencode.ai
was dropping connections server-side. A manual retry on 25 June succeeded for both.

**Mitigation: no_agent retry wrapper**

For transient provider failures, convert the LLM-driven cron job to a no_agent
wrapper script that retries with backoff. See `references/provider-retry-patterns.md`.

## Error tracing reference

When an error is reported for a cron job, trace it through this chain:

```
User-facing message (chat/notification)
  → _summarize_cron_failure_for_delivery (cron/scheduler.py)
    → run_job exception handler (cron/scheduler.py:2226-2246)
      → run_conversation result (agent/conversation_loop.py)
        → interruptible_api_call (agent/chat_completion_helpers.py)
          → provider/client call (raw error origin)
```

Each wrapper adds a layer of indirection. The original exception type and message
are preserved if you look at the right level.
