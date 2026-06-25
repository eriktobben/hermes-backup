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
