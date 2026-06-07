---
name: opencode
description: "Delegate coding to OpenCode CLI (features, PR review)."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Autonomous, Refactoring, Code-Review]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

Use [OpenCode](https://opencode.ai) as an autonomous coding worker orchestrated by Hermes terminal/process tools. OpenCode is a provider-agnostic, open-source AI coding agent with a TUI and CLI.

## When to Use

- User explicitly asks to use OpenCode
- You want an external coding agent to implement/refactor/review code
- You need long-running coding sessions with progress checks
- You want parallel task execution in isolated workdirs/worktrees

## Prerequisites

- OpenCode installed: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- Auth configured: `opencode auth login` or set provider env vars (OPENROUTER_API_KEY, etc.)
- Verify: `opencode auth list` should show at least one provider
- Git repository for code tasks (recommended)
- `pty=true` for interactive TUI sessions

## OpenCode Configuration Files

OpenCode reads its config from `~/.config/opencode/`. Two key files control which models are used:

### `opencode.json` — Main/Orchestrator Model

```json
{
  "model": "opencode-go/deepseek-v4-pro",
  "variant": "max",
  "permission": {
    "bash": "allow",
    "read": "allow",
    "write": "allow"
  },
  "plugin": [
    "superpowers@git+https://github.com/obra/superpowers.git",
    "@cortexkit/opencode-magic-context@latest"
  ]
}
```

The `model` field is the **orchestrator/planning** model — the model that drives the main TUI session, planning, and high-level reasoning.
The `variant` field (optional) sets the **reasoning effort** — see [Reasoning Variants](#reasoning-variants) below.

### `opencode-swarm.json` — Subagent Models (Swarm Mode)

When OpenCode swarm mode is installed, this file configures the role-specific subagents. Each agent can have its own model and reasoning variant:

```json
{
  "agents": {
    "architect": { "model": "opencode-go/deepseek-v4-pro", "variant": "max" },
    "coder":     { "model": "opencode-go/deepseek-v4-flash", "variant": "max" },
    "reviewer":  { "model": "opencode-go/deepseek-v4-flash", "variant": "max" },
    "critic":    { "model": "opencode-go/deepseek-v4-pro", "variant": "max" },
    "explorer":  { "model": "opencode-go/deepseek-v4-flash", "variant": "max" }
  },
  "guardrails": {
    "max_tool_calls": 200,
    "max_duration_minutes": 30
  },
  "council_mode": "phase_complete",
  "code_graph": {
    "enabled": true,
    "languages": ["php", "javascript", "python"]
  }
}
```

### Swarm Role Guidance

Different swarm roles benefit differently from strong vs fast models:

| Role | Job | Recommended Tier |
|------|-----|-----------------|
| **Architect** | High-level planning, code structure decisions | Strong model (e.g. `deepseek-v4-pro`) |
| **Coder** | Implements code changes | Fast model (e.g. `deepseek-v4-flash`) |
| **Reviewer** | Checks code for bugs, style, logic errors | Fast model (Flash is sufficient for pattern-based review) |
| **Critic** | Edge cases, security, architectural weaknesses | **Strong model** — most reasoning-heavy subagent role, benefits most from Pro |
| **Explorer** | Scans codebase, finds files, reads context | Fast model (purely mechanical) |

### Dual-Provider Pattern (Orchestrator + Subagents)

You can mix providers across roles. A common pattern routes strong models through a direct provider and fast models through a proxy:

| Role | Config File | Provider | Example |
|------|-------------|----------|---------|
| **Orchestrator/Planning** | `opencode.json` → `model` | Direct provider (e.g. `deepseek`) | `deepseek/deepseek-v4-pro` |
| **Subagents** (coder, reviewer, explorer) | `opencode-swarm.json` → `agents.*.model` | Proxy provider (e.g. `opencode-go`) | `opencode-go/deepseek-v4-flash` |

This keeps strong-model API calls on the direct provider's billing while letting the proxy handle faster/cheaper subagent traffic.

**Model naming convention:** `provider/model-name` — e.g. `deepseek/deepseek-v4-pro`, `opencode-go/deepseek-v4-flash`, `opencode-go/minimax-m2.7`.

### Checking Available Models & Capabilities

List all models from a provider:
```bash
opencode models <provider>          # e.g. deepseek, opencode-go, openrouter
```

Get detailed model metadata (cost, limits, supported variants):
```bash
opencode models <provider> --verbose
```

This shows per-model info including:
- `cost` — input/output/cache-read prices
- `limit` — context and output token limits
- `capabilities.reasoning` — whether the model supports reasoning
- `variants` — available reasoning-effort levels (each maps to a `reasoningEffort` parameter)

### Reasoning Variants

Models that support reasoning (capabilities.reasoning: true) expose one or more variants. Each variant maps to a `reasoningEffort` parameter sent to the API:

| `variant` value | `reasoningEffort` | Use case |
|----------------|-------------------|----------|
| `low` | `low` | Quick pattern matching, simple lookups |
| `medium` | `medium` | Balanced reasoning |
| `high` | `high` | Thorough analysis |
| `max` | `max` | Maximum reasoning depth — best for complex bugs, architecture, security review |

Set the variant per-agent in `opencode-swarm.json` via `"variant": "max"`, or globally in `opencode.json` via `"variant": "max"` at the top level.

**Note:** Max reasoning increases response time and token consumption. If subagents feel slow, drop them to `high` or `medium`.

**Note:** Changes take effect on next OpenCode session start — no restart needed, just exit and relaunch.

## Binary Resolution (Important)

Shell environments may resolve different OpenCode binaries. If behavior differs between your terminal and Hermes, check:

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

If needed, pin an explicit binary path:

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## One-Shot Tasks

Use `opencode run` for bounded, non-interactive tasks:

```
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context files with `-f`:

```
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Show model thinking with `--thinking`:

```
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

Force a specific model:

```
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Interactive Sessions (Background)

For iterative work requiring multiple exchanges, start the TUI in background:

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

**Important:** Do NOT use `/exit` — it is not a valid OpenCode command and will open an agent selector dialog instead. Use Ctrl+C (`\x03`) or `process(action="kill")` to exit.

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit message (press twice if needed) |
| `Tab` | Switch between agents (build/plan) |
| `Ctrl+P` | Open command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+X N` | New session |
| `Ctrl+X E` | Open editor |
| `Ctrl+C` | Exit OpenCode |

### Resuming Sessions

After exiting, OpenCode prints a session ID. Resume with:

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Common Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue the last OpenCode session |
| `--session <id>` / `-s` | Continue a specific session |
| `--agent <name>` | Choose OpenCode agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--format json` | Machine-readable output/events |
| `--file <path>` / `-f` | Attach file(s) to the message |
| `--thinking` | Show model thinking blocks |
| `--variant <level>` | Reasoning effort (high, max, minimal) |
| `--title <name>` | Name the session |
| `--attach <url>` | Connect to a running opencode server |

## Procedure

1. **Worktree first:** Before running OpenCode, ensure you have a dedicated git worktree. Check `git worktree list`, create if needed: `git worktree add <sti> -b <branch> main`.
2. **Workdir = worktree:** ALL OpenCode-kommandoer må ha `workdir` satt til worktree-stien. Kjør ALDRI OpenCode fra main-repoet.
3. Verify tool readiness:
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
4. For bounded tasks, use `opencode run '...'` (no pty needed) med `workdir` satt til worktree.
5. For iterative tasks, start `opencode` with `background=true, pty=true` og `workdir` i worktree.
6. Monitor long tasks with `process(action="poll"|"log")`.
7. If OpenCode asks for input, respond via `process(action="submit", ...)`.
8. Exit with `process(action="write", data="\\x03")` or `process(action="kill")`.
9. Summarize file changes, test results, and next steps back to user.

## PR Review Workflow

OpenCode has a built-in PR command:

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Or review in a temporary clone for isolation:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Parallel Work Pattern

Use separate workdirs/worktrees to avoid collisions:

```
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

### Strong isolation contract (recommended for Discord/Kimaki and any multi-session workflow)

For each session/thread, isolate **both** filesystem and git history:

1. Create a unique worktree path.
2. Create a unique branch for that session.
3. Run OpenCode with `workdir` set to that worktree path only.
4. Never share a live branch across active sessions.

Preferred command (creates worktree + branch in one step):

```
git worktree add <worktree-path> -b <session-branch> <base-ref>
```

Example:

```
git worktree add ~/.kimaki/worktrees/<project>/<session-slug> -b feature/<session-slug> origin/main
```

Why both are required:
- Branch-only in the same directory still shares unstaged files.
- Worktree-only with shared branch can mix commits from different sessions.

Quick verification (run per active session):

```
pwd
git rev-parse --show-toplevel
git branch --show-current
```

Isolation is healthy when each session has a distinct path and branch.
## Session & Cost Management

List past sessions:

```
terminal(command="opencode session list")
```

Check token usage and costs:

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## Pitfalls

- Interactive `opencode` (TUI) sessions require `pty=true`. The `opencode run` command does NOT need pty.
- `/exit` is NOT a valid command — it opens an agent selector. Use Ctrl+C to exit the TUI.
- PATH mismatch can select the wrong OpenCode binary/model config.
- If OpenCode appears stuck, inspect logs before killing:
  - `process(action="log", session_id="<id>")`
- Avoid sharing one working directory across parallel OpenCode sessions.
- Enter may need to be pressed twice to submit in the TUI (once to finalize text, once to send).

### Kimaki/Discord-specific pitfall: worktree-triggered listener loops

When OpenCode is brokered through Kimaki (Discord bot), the bot can appear to "reply once then stop" after thread/worktree bootstrap.

High-signal pattern in Kimaki logs:
- `SESSION [LISTENER] Connected to event stream ...`
- `SESSION [LISTENER] Stream ended normally ..., reconnecting in 500ms` (repeats)
- eventually `Opencode server exited ... signal: SIGKILL` and bot restarts

Fast containment sequence:
1. Archive the affected thread session (`kimaki session archive <thread_id>`).
2. Disable auto-worktrees for the affected channel (toggle command or channel_worktrees DB flag) to keep service usable.
3. Confirm model source-of-truth is aligned in **both config and DB overrides**:
   - Files: `~/.kimaki/opencode-config.json`, `~/.config/opencode/opencode.json` (and swarm config if installed)
   - DB: `channel_models` and `global_models` rows for the channel/app
4. Run a direct OpenCode smoke test **outside Kimaki** to validate provider/model behavior:
   - `opencode --pure run "Respond with exactly: OC_MODEL_OK"`
   - If this hangs or exits without final output, switch to a known-good model (e.g. `openai/gpt-5.4-mini`) and retest.
5. If Discord shows only footer (`using provider/model`) with no answer body, check for model context-window failures in logs (e.g. `context window exceeds limit`).
   - This commonly happens when a plugin inflates prompt size.
   - Temporarily remove heavy plugins (e.g. `opencode-swarm`) from OpenCode config and restart Kimaki.
6. Restart Kimaki and retest with a **new** thread.
7. If stable with worktrees OFF, keep production on that mode while isolating worktree/bootstrap behavior.

**Related: Hermes session reset can erase worktree context.** Default reset policy resets sessions each night at 4 AM. If a user returns to a thread after reset, the agent starts fresh and won't know about existing worktrees. See `discord-dev-channel-workflow` skill → `references/session-reset-worktree-troubleshooting.md`.

See `references/kimaki-discord-worktree-loop.md`, `references/kimaki-footer-only-no-response.md`, and `references/worktree-isolation-verification.md` for concrete runbooks and indicators.

## Verification

Smoke test:

```
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Success criteria:
- Output includes `OPENCODE_SMOKE_OK`
- Command exits without provider/model errors
- For code tasks: expected files changed and tests pass

## Rules

1. Prefer `opencode run` for one-shot automation — it's simpler and doesn't need pty.
2. Use interactive background mode only when iteration is needed.
3. Always scope OpenCode sessions to a single repo/workdir.
4. For long tasks, provide progress updates from `process` logs.
5. Report concrete outcomes (files changed, tests, remaining risks).
6. Exit interactive sessions with Ctrl+C or kill, never `/exit`.
