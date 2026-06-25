# Provider retry patterns for cron jobs

When an LLM-driven cron job fails due to an **intermittent upstream provider failure**
(e.g. opencode.ai dropping TCP connections), the simplest fix is a no_agent wrapper
script that retries with backoff. This pattern avoids touching the provider config
or the Hermes source code.

## When to use this pattern

- The failure pattern is **intermittent** (works most days, fails occasionally)
- **Multiple jobs** using the same provider fail on the same days (cross-job correlation)
- Manual retry (`cronjob action=run`) succeeds within minutes/hours
- The error is `[Errno 32] Broken pipe`, `ReadError`, or `ReadTimeout` from the provider

## Pattern: no_agent retry wrapper

1. Create a Python script at `~/.hermes/scripts/<name>-retry.py` that:
   - Contains the full cron job prompt embedded as a string
   - Calls `hermes chat -q "PROMPT" --quiet --yolo` via subprocess to execute the actual task
   - Implements retry backoff: attempt → wait N min → retry → wait M min → retry
   - On success: prints the output (cron delivers stdout verbatim)
   - On final failure: prints an error report (cron delivers it)

2. Update the cron job:
   - `no_agent: true`
   - `script: "<name>-retry.py"`
   - Clear `prompt` and `skills` (now embedded in the script)
   - Keep the same `schedule`, `deliver`, and `origin`

## Example script structure

```python
#!/usr/bin/env python3
import subprocess, sys, time

HERMES = "/home/erik/.local/bin/hermes"

PROMPT = """... full cron prompt ..."""

def run_task():
    proc = subprocess.run(
        [HERMES, "chat", "-q", PROMPT, "-Q", "--yolo"],
        capture_output=True, text=True, timeout=600,
    )
    return proc.returncode, (proc.stdout or "") + "\n" + (proc.stderr or "")

attempts = [
    (0, "First attempt"),
    (300, "Backoff 5min → second attempt"),
    (600, "Backoff 10min → third attempt"),
]

for delay, label in attempts:
    if delay > 0:
        print(f"[{label}]", flush=True)
        time.sleep(delay)
    exit_code, output = run_task()
    if exit_code == 0:
        if output:
            print(output)
        sys.exit(0)
    print(f"❌ {label} failed (exit {exit_code})", flush=True)

# All attempts failed — report
print("❌❌❌ ALL ATTEMPTS FAILED")
print(output[:2000])
sys.exit(1)
```

## Key flags for `hermes chat -q`

| Flag | Purpose |
|------|---------|
| `-q "PROMPT"` | Single query, non-interactive |
| `-Q` / `--quiet` | Suppress banner, spinner, tool previews |
| `--yolo` | Skip dangerous command approval prompts |
| `-s <skill>` | Load a skill (e.g. `-s here-now`) |
| `-t <tools>` | Enable specific toolsets (e.g. `-t web,search,terminal`) |

## Requirements

- `hermes` CLI must be on a known path (find with `which hermes`)
- The script must be executable and pass Python syntax: `python3 -c "import py_compile; py_compile.compile('script.py', doraise=True)"`
- Cron context has no TTY — `hermes chat -q` handles this, but avoid anything that needs interactive input
- `--yolo` is needed because the cron context can't approve shell commands

## Pitfalls

- `hermes chat -q` with `-Q` still outputs tool call progress lines — the delivery to the user will contain some interstitial text mixed with the final response. Keep the final response prominent (e.g. the briefing link on its own line).
- 10-minute timeout per subprocess call. If the task genuinely takes longer, increase `timeout=` in the script.
- When retrying, each attempt is a **fresh session** — no state from previous attempts is preserved. The script is the only state.
- If the provider is completely down (not intermittent), retries just waste resources. Always verify the pattern is intermittent first.
- The `hermes chat -q` subprocess calls the same provider config — it will hit the same intermittent failures, which is why the retry exists.

## Cross-job diagnostics (pre‑retry)

Before building a retry wrapper, confirm it's a provider-wide issue:

```bash
# List all jobs and their last status
cronjob action=list

# Check output files for failed runs
ls -lt ~/.hermes/cron/output/<job_id>/
cat ~/.hermes/cron/output/<job_id>/latest.md

# Compare failure dates across jobs sharing the same provider
# If all jobs failed on the same dates → upstream provider issue
# If only one job failed → job-specific / ACP crash
```
