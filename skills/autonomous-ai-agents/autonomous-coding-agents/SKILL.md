---
name: autonomous-coding-agents
description: "Delegate coding work to external autonomous coding agent CLIs — Claude Code, OpenAI Codex, or OpenCode. Includes a selection guide, shared usage patterns, and per-tool sections. Use when the user wants to use an autonomous coding agent or delegates a coding task to an external CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, External-CLI, Claude, Codex, OpenCode, Automation]
    related_skills: [hermes-agent, kanban-codex-lane, subagent-driven-development, kanban-worker]
---

# Autonomous Coding Agents — Hermes Orchestration Guide

Delegate coding tasks to external autonomous agent CLIs. The three supported tools are **Claude Code** (Anthropic), **Codex** (OpenAI), and **OpenCode** (provider-agnostic open-source). Each runs as a subprocess from Hermes; Hermes owns verification, safety, and the Kanban lifecycle.

## Selection Guide

| Criterion | Claude Code | Codex | OpenCode |
|-----------|-------------|-------|----------|
| Provider | Anthropic | OpenAI | Provider-agnostic (OpenRouter, OpenAI, etc.) |
| Installation | `npm i -g @anthropic-ai/claude-code` | `npm i -g @openai/codex` | `npm i -g opencode-ai` or `brew install anomalyco/tap/opencode` |
| One-shot (no pty) | `-p "prompt"` | `exec "prompt"` | `run "prompt"` |
| Interactive PTY | tmux + `claude` (full TUI) | `codex` (basic TUI) | `opencode` (full TUI) |
| PR review built-in | `--from-pr N` | manual | `opencode pr N` |
| Needs git repo | No (but recommended) | Yes (required) | No (but recommended) |
| Structured output | `--output-format json` | No | `--format json` |
| Session resumption | `--continue` / `--resume <id>` | No | `-c` / `-s <id>` |

Pick the agent that the user asks for, or default to **OpenCode** when the user has no preference (provider-agnostic, actively maintained).

## Shared Patterns Across All Agents

### Auth Detection

```bash
# Check what's available for each
command -v claude && claude --version 2>/dev/null
command -v codex && codex --version 2>/dev/null
command -v opencode && opencode --version 2>/dev/null
```

### Workspace Isolation (Required for parallel work)

Never run an autonomous agent in the user's dirty checkout. Always use a git worktree:

```bash
git worktree add -b <agent>/<branch-slug> /tmp/<slug>-worktree main
```

Run the agent with `workdir=/tmp/<slug>-worktree`. Clean up when done:

```bash
git worktree remove /tmp/<slug>-worktree
git branch -D <agent>/<branch-slug>
```

### Post-Run Verification (Hermes owns)

After any autonomous agent finishes, Hermes must independently verify:

1. **Filesystem reality check** — do the claimed files exist?
2. **Read-back sanity** — does the code look correct?
3. **Test run** — do existing tests still pass? Run the canonical test command.
4. **Git state** — does `git status` make sense?
5. **Safety scan** — no hardcoded secrets, no risk-gate weakening, no out-of-scope changes.

**Never trust an agent's self-report as proof of completion.** Always verify directly.

### PR Review Workflow (any agent)

| Step | Tool |
|------|------|
| Fetch PR branch locally | `git fetch origin pull/N/head:pr-N` |
| Check it out | `git checkout pr-N` |
| Run agent to review | See tool-specific sections below |
| Post findings | `gh pr comment N --body "..."` |

---

## Claude Code (detailed)

### Prerequisites

```bash
npm install -g @anthropic-ai/claude-code
claude auth login --console          # API key billing
claude auth status --text            # verify
```

### One-Shot (Print Mode) — Preferred

```bash
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

Key flags:
- `-p "prompt"` — one-shot, exits when done (no PTY needed)
- `--max-turns N` — prevent runaway loops (required for print mode)
- `--allowedTools 'Read,Edit'` — restrict capabilities
- `--output-format json` — structured result with `costUSD`, `session_id`, `num_turns`
- `--model <alias>` — `sonnet`, `opus`, `haiku`
- `--dangerously-skip-permissions` — auto-approve all tools (CI)

### Interactive (PTY via tmux) — Multi-Turn

```bash
# Start session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")
terminal(command="tmux send-keys -t claude-work 'cd /path/to/proj && claude' Enter")

# Handle workspace trust dialog (Enter for default "Yes")
terminal(command="sleep 5 && tmux send-keys -t claude-work Enter")
# Handle permissions dialog (Down then Enter)
terminal(command="sleep 3 && tmux send-keys -t claude-work Down && sleep 0.3 && tmux send-keys -t claude-work Enter")

# Send task
terminal(command="tmux send-keys -t claude-work 'Refactor auth to use JWT' Enter")
terminal(command="sleep 30 && tmux capture-pane -t claude-work -p -S -50")
```

### PR Review

```bash
# Quick: pipe diff to print mode
terminal(command="git diff main...HEAD | claude -p 'Review this diff for bugs and security issues.' --max-turns 3", timeout=60)

# Deep: from PR number
terminal(command="claude -p 'Review PR thoroughly' --from-pr 42 --max-turns 10", workdir="/path/to/repo", timeout=120)
```

### MCP Integration

```bash
claude mcp add -s user github -- npx @modelcontextprotocol/server-github
claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb
```

### Pitfalls

- `--max-turns` is print-mode only; ignored in interactive sessions
- `--dangerously-skip-permissions` dialog defaults to "No, exit" — must send Down then Enter
- Session resumption requires same working directory
- `claude --bare` skips plugins, MCP discovery, CLAUDE.md — fastest for CI

Full reference: `references/claude-code.md`

---

## Codex (detailed)

### Prerequisites

```bash
npm install -g @openai/codex
# Auth: OPENAI_API_KEY or Codex OAuth credentials
# Must run inside a git repository
# Use pty=true in terminal — Codex is an interactive TUI
```

### One-Shot

```bash
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```bash
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

### Background Mode (Long Tasks)

```bash
result = terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
session_id = result["session_id"]

# Monitor
process(action="poll", session_id=session_id)
process(action="log", session_id=session_id)
process(action="submit", session_id=session_id, data="yes")  # Answer if Codex asks
process(action="kill", session_id=session_id)                  # If needed
```

### Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution |
| `--full-auto` | Sandboxed; auto-approves file changes |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

### PR Reviews

```bash
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main
```

### Pitfalls

- **Always use `pty=true`** — Codex hangs without a PTY
- **Git repo required** — won't run outside a git directory
- Use `exec` for one-shots; `--full-auto` for building
- `--yolo` is dangerous — prefer `--full-auto` for safety-sensitive repos

Full reference: `references/codex.md`

---

## OpenCode (detailed)

### Prerequisites

```bash
npm i -g opencode-ai  # or: brew install anomalyco/tap/opencode
opencode auth login   # Configure providers
opencode auth list    # Verify at least one provider
```

### Binary Resolution

Shell environments may resolve different OpenCode binaries:

```bash
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

Pin explicit path if needed: `$HOME/.opencode/bin/opencode`

### One-Shot (no pty needed)

```bash
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context files: `-f config.yaml -f .env.example`
Force model: `--model openrouter/anthropic/claude-sonnet-4`
Show thinking: `--thinking`

### Interactive (Background PTY)

```bash
result = terminal(command="opencode", workdir="~/project", background=true, pty=true)
session_id = result["session_id"]

# Send a prompt
process(action="submit", session_id=session_id, data="Implement OAuth refresh flow")

# Monitor
process(action="poll", session_id=session_id)
process(action="log", session_id=session_id)

# Exit — Ctrl+C (NOT /exit)
process(action="write", session_id=session_id, data="\x03")
```

### PR Review

```bash
# Built-in PR command
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

### Session & Cost Management

```bash
opencode session list
opencode stats --days 7 --models anthropic/claude-sonnet-4
```

### Pitfalls

- Interactive TUI sessions require `pty=true`; `opencode run` does NOT need pty
- `/exit` is NOT a valid command — opens an agent selector. Use Ctrl+C
- PATH mismatch can select wrong binary/model config
- Enter may need to be pressed twice to submit in TUI
- Always use isolated worktrees for parallel sessions

Full reference: `references/opencode.md` — config files (`opencode.json`, `opencode-swarm.json`), dual-model orchestration pattern, TUI keybindings, PR review, and pitfalls.

---

## Pitfalls (All Agents)

1. **Never trust agent self-report as completion proof** — always verify with direct tool calls
2. **Always isolate in a git worktree** — never run in dirty main checkout
3. **Set `--max-turns` or equivalent budget** to prevent runaway costs
4. **Monitor background processes** with `process(action="poll")` — don't fire-and-forget
5. **Clean up tmux sessions and worktrees** when done
6. **Prefer print/one-shot mode** over interactive for automation
7. **Report concrete outcomes** — files changed, tests run, verification results
8. **Safety-sensitive repos** (finance, trading, production): never use `--yolo`, always review diffs
