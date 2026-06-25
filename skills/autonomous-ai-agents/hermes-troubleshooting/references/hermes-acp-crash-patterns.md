# Hermes Agent ACP subprocess crash patterns

When the ACP (Agent Communication Protocol) subprocess — `opencode-go` or `copilot` —
crashes during a job, the error surfaces as `[Errno 32] Broken pipe` in the cron output.

## Symptom

User sees in chat:

```
⚠️ Cron 'AI Model Daily Briefing' failed: [Errno 32] Broken pipe
```

The output file (`~/.hermes/cron/output/<job_id>/<date>.md`) shows:

```
## Error

RuntimeError: [Errno 32] Broken pipe
```

## Root cause

The ACP subprocess crashed/exited during the job, closing its stdin pipe.
When Hermes tries to send the next JSON-RPC request via
`proc.stdin.write(json.dumps(payload) + "\n")`, the write to the closed pipe
raises `BrokenPipeError: [Errno 32] Broken pipe`.

## Exact crash site

**File:** `agent/copilot_acp_client.py`
**Line 492:** `proc.stdin.write(json.dumps(payload) + "\n")` inside `_request()`

There is **no try/except** around this write. The exception propagates uncaught
through the `_request` closure and up through `_run_prompt`.

## Error propagation chain

```
copilot_acp_client.py:492
  proc.stdin.write(payload + "\n")  ← BrokenPipeError raised
    ↓
chat_completion_helpers.py:239
  request_client.chat.completions.create(**api_kwargs)
  → exception caught at line 240, stored in result["error"]
    ↓
chat_completion_helpers.py:549-550
  if result["error"]: raise result["error"]
    ↓
agent/conversation_loop.py
  retry loop (backoff → fallback → failed)
    ↓ after all retries + fallbacks exhausted
conversation_loop.py:3513-3526
  returns {"failed": True, "error": _final_summary}
    ↓
cron/scheduler.py:2192-2198
  result["failed"] is True → raise RuntimeError(result["error"])
    ↓
cron/scheduler.py:93-98
  _summarize_cron_failure_for_delivery strips "RuntimeError: " prefix
  → "⚠️ Cron 'name' failed: [Errno 32] Broken pipe"
```

## Failure pattern

| Run result | Indicates |
|---|---|
| **Intermittent** (works for weeks, then fails a day) | Subprocess crash under specific conditions, not configuration |
| **Consistent** (fails every run) | Possibly missing binary, auth failure, or permanent error — **not** the typical pattern for this crash |
| **Exactly at the same step every run** | Specific tool call triggers the crash |

The AI Model Daily Briefing showed an intermittent pattern:
- 4 June: ✅ OK
- 5 June: ❌ Broken pipe  
- 6–22 June: ✅ OK (16 days)
- 23–24 June: ❌ Broken pipe (consecutive)

## Diagnostic steps

1. **Confirm the error**: `cronjob action=list` → check `last_status` and `last_error`
2. **Read the output file**: `~/.hermes/cron/output/<job_id>/<date>.md` for the full prompt
   (The error section only appears if the agent never produced a response)
3. **Check failure history**:
   ```bash
   grep -l "## Error" ~/.hermes/cron/output/<job_id>/*.md
   ```
4. **Try manual run**: `cronjob action=run job_id=<id>` to see if it's transient
5. **Check resources**: `free -h` and (if accessible) `dmesg | grep -i oom`

## Recovery options

| Option | Effort | Reliability |
|---|---|---|
| **Do nothing (wait for retry)** | None | Works if transient |
| **Switch to direct HTTP provider** | Medium | Most reliable — no subprocess to crash |
| **Add error handling to `_request()`** | Low | Wraps `proc.stdin.write()` in try/except to restart subprocess |

## Why this happens

ACP communicates with the LLM backend via a subprocess over stdin/stdout pipes.
This architecture is inherently less stable than direct HTTP:

- The subprocess (opencode-go) is a separate binary that can crash independently
- OOM killer, signal delivery, and resource limits affect subprocesses
- The subprocess makes its own API calls; if those fail ungracefully, the
  subprocess may panic and exit without clean shutdown
