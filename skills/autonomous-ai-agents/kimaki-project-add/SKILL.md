---
name: kimaki-project-add
description: Registers a local repo as a Discord-visible Kimaki project and manages Kimaki worktrees — creation, nightly GC recovery, cleanup, and operational hardening.
tags: [kimaki, opencode, worktree, discord, git]
related_skills: [discord-agent-runtime-diagnosis]
---

# Kimaki Project Add (Discord visibility)

## When to use
Use this after creating or cloning a repository that should appear in Discord via Kimaki.

## Steps
1. Ensure the project directory exists (typically under `/home/erik/Projects/<repo-folder>`).
2. `cd` into the project directory.
3. **If the repo is empty (no commits yet), create a `main` branch:**
   ```bash
   git commit --allow-empty -m "Initial commit"
   git push -u origin main
   ```
   This ensures the repo has a `main` branch before registering with Kimaki.
4. Verify Kimaki starts without crashing:
   ```bash
   timeout 5 npx kimaki --version
   ```
   If it crashes with a SyntaxError, run the patch script (see pitfall below) and retry.
5. Register the project:
   ```bash
   npx kimaki project add
   ```
6. Confirm success output includes:
   - Created channels for project
   - Directory path
   - Discord channel URL

## Notes / pitfalls
- Run the command **inside** the target project folder, or Kimaki may register the wrong directory.
- If `kimaki` is not installed globally, `npx` will install and run it automatically.
- If Git clone fails with "Repository not found", verify repo URL and access rights for the active GitHub SSH identity.
- **Kimaki crashes with `SyntaxError: Illegal return statement`** after upgrade:
  - Kimaki v0.14.0+ has a fragile `new-worktree.js` that can leave orphaned duplicate lines after partial patches, causing a crash loop at startup.
  - First, run the patch script: `bash ~/.local/bin/kimaki-patch-worktree`
  - If the patch script reports "No Kimaki instances needed patching" but Kimaki still crashes, the file may have orphaned lines the patch doesn't yet handle. See `references/kimaki-new-worktree-orphan-fix.md` for manual fix steps.
  - After fixing, update `~/.local/bin/kimaki-patch-worktree` to cover the new orphan pattern so future upgrades handle it automatically.
- If Discord-side automation becomes unresponsive, avoid rebooting first; run the troubleshooting checks in `references/unresponsive-discord-bot.md`.
- **Workspace creation fails with `err_e2b0c342`**: the OpenCode ACP server may have developed a Bun runtime degradation after extended uptime. See `discord-agent-runtime-diagnosis` → "Bun runtime degradation" section. Fix: `pm2 restart kimaki`.

- **`fatal: 'branch-name' is already used by worktree`**: When a worktree creation fails or is interrupted, the branch can remain registered in git's worktree system even if the worktree directory was removed. Git refuses to create a new worktree with the same branch name. **Fix sequence**:
  1. `cd <project-directory> && git worktree prune` — removes stale worktree references
  2. `git branch -D "opencode/kimaki-<slug>"` — delete the stuck branch
  3. `rm -rf ~/.kimaki/worktrees/<hash>/` — clean up leftover directories
  4. `pm2 restart kimaki` — restart to pick up clean state
  5. User retries the worktree creation in Discord
  **Root cause**: Kimaki's `createWorktreeWithSubmodules` uses `git worktree add -B` which fails if the branch is "in use" by any registered worktree, even stale ones. The `-B` flag would reset an existing branch but cannot override the worktree lock. Kimaki does not currently run `git worktree prune` before creation attempts.
  See `references/stuck-branch-worktree-fix.md` for full investigation and code path analysis.

- **\\\\\\\"Directory does not exist or is not accessible\\\\\\\" on a known thread**: Two separate cleanup mechanisms affect Kimaki worktrees nightly:
  1. **OpenCode snapshot GC (~02:00)**: Internal to the OpenCode binary — runs `git gc --prune=7.days` on snapshot repos. **Deletes the entire worktree directory** (not just empties it). Git branch may or may not survive — we've observed both outcomes even for worktrees 1-2 days old. **Cannot be disabled** (compiled binary, no config knob). This is what causes the error message.
  2. **Our cron job (02:15)**: `kimaki-worktree-cleanup.py` now runs a 3-phase restore/cleanup process. Phase 1 restores recent worktrees (<7 days) deleted by OpenCode's GC. Phase 2 cleans up old worktrees (>14 days). Phase 3 handles orphaned directories.

  ⚠️ **Two broken scripts (fixed)**: Both the WIP auto-commit and the Kimaki cleanup script queried `thread_worktrees` table, but Kimaki registers worktrees in `thread_workspaces`. This caused:
  - WIP auto-commit to silently skip all worktrees (never preserving uncommitted changes)
  - Kimaki cleanup to delete branches for worktrees deleted by OpenCode's GC, even if they were recent (<14 days)

  **Fixes deployed** (Aug 2026):
  - `kimaki-wip-autocommit.sh` now queries `thread_workspaces`
  - `kimaki-worktree-cleanup.py` rewritten as 3-phase restore/cleanup script
  - Cron job `3fca63db50fc` moved from 04:00 to 02:15 (15 min after OpenCode GC)

  The automated fix for empty worktrees:
  1. The cron job at 02:15 automatically restores worktrees that are <7 days old
  2. For manual recovery, query the DB: `python3 -c "import sqlite3; c=sqlite3.connect('$HOME/.kimaki/discord-sessions.db'); print('\\\\\\\\\\\\\\\\n'.join(str(r) for r in c.execute('SELECT workspace_name, workspace_directory, project_directory FROM thread_workspaces WHERE thread_id=\\\\\\\\\\\\\"<thread_id>\\\\\\\\\\\\\"')))"`
  3. Verify the git branch still exists: `cd <project_directory> && git branch -a | grep <worktree_name>`
  4. If branch exists → recreate: `cd <project_directory> && git worktree add <workspace_directory> <worktree_branch>`
  5. If branch is GONE → find the project's main dev branch (e.g. `v2`, `develop`, `main`) with matching commits and recreate from there. Kimaki branches can be deleted even for worktrees only 1-2 days old.
    See `references/worktree-cleanup-recovery.md` for full session detail and `references/worktree-cleanup-investigation.md` for the diagnostic methodology.
  **Multi-day work**: Users who want to keep threads alive across days should know that OpenCode GC will delete the checkout nightly, and the git branch may also be lost — even for worktrees only 1-2 days old. The automated restore at 02:15 handles most cases. Recreation is instant if the branch survives; if not, find the equivalent branch in the project (e.g. `v2`, `develop`, `main`).
  See `references/worktree-cleanup-recovery.md` for full session detail and `references/worktree-cleanup-investigation.md` for the diagnostic methodology.

  ## Model switching via agent files

Kimaki uses OpenCode under the hood. Agent files (`.opencode/agent/*.md`) let you switch models with a single slash command instead of clicking through the `/model` menus.

### How it works
1. Create `.md` files in the project's `.opencode/agent/` directory
2. Restart Kimaki (`pm2 restart kimaki`)
3. Use `/agent` dropdown or `/<name>-agent` slash commands to switch

### Agent file format
```yaml
---
description: Short human-readable description
primary model: provider/model-id
permission:
  question: allow
  plan_enter: allow
---
```

### Provider names (as of July 2026)
- **OpenCode Go**: `opencode-go/<model-id>` — models like `deepseek-v4-flash`, `deepseek-v4-pro`, `mimo-v2.5`, `mimo-v2.5-pro`, `minimax-m3`
- **MiniMax direct**: `minimax/minimax-m3` — uses MiniMax token plan directly, not via OpenCode Go
- **Anthropic**: `anthropic/<model-id>`
- **OpenAI**: `openai/<model-id>`

To list available models: `curl -s "https://opencode.ai/zen/go/v1/models" -H "Authorization: Bearer dummy" | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]"`

### Pitfalls
- **Agent files are per-project, NOT global.** Kimaki calls `getClient().app.agents({ directory: projectDir })` — it only looks in the active project's `.opencode/agent/`. There is no global agent directory in OpenCode.
- **Global `opencode.json` agents are invisible to Kimaki.** Kimaki starts OpenCode with `OPENCODE_CONFIG=~/.kimaki/opencode-config.json` (its own config). Even if you define agents in `~/.config/opencode/opencode.json`, Kimaki's OpenCode instance never reads that file. Always create agent `.md` files in the project's `.opencode/agent/` directory for Kimaki visibility.
- **Wrong project directory = no agents visible.** Each Discord channel is mapped to a project directory. If you put agent files in `~/.kimaki/projects/kimaki/.opencode/agent/` but the thread uses `/home/erik/Projects/serenahome`, the agents won't appear. Check `kimaki.log` for `Using project directory: ...` to find the correct path.
- **Must restart Kimaki after adding/changing agent files.** `pm2 restart kimaki` — the agent list is loaded at OpenCode server startup.
- **Agent filter**: only agents with `mode: primary` or `mode: all` and `hidden: false` appear in the `/agent` dropdown. OpenCode's built-in `build` and `plan` agents are always present.

## OpenCode v2 compatibility

**Do NOT upgrade to OpenCode v2 yet** — Kimaki (v0.25.0) does not support it.

OpenCode v2 (beta, `npm install -g @opencode-ai/cli@beta`) has three breaking changes:
1. **Plugins** — New plugin API. V1 plugins will not work in V2.
2. **Server API and clients** — New contracts. Must use `@opencode-ai/client` instead of `@opencode-ai/sdk`.
3. **TUI configuration** — Moves to `cli.json`.

V1 and V2 can be installed side by side (`opencode` vs `opencode2`). Existing config is read automatically, but Kimaki's plugins and SDK calls use V1 APIs.

Monitor Kimaki releases for v2 support. When available, test in a non-production environment first.

See `references/opencode-v2-migration.md` for details.

## Operational hardening (PM2 / long-running bot)
When Kimaki is run as a persistent bot process, reduce freeze/restart loops by:
1. Avoid floating `npx kimaki` in PM2 for production-like runs; pin a known kimaki version.
2. Ensure swap exists on small-memory servers (0 swap increases SIGKILL/OOM risk).
3. Configure PM2 safeguards (`max_memory_restart`, backoff) so only the process restarts.
4. Enable log rotation for PM2 logs to prevent uncontrolled growth.
5. Ensure Bun is in the PM2 runtime PATH (or export it in the start command), otherwise Kimaki may repeatedly auto-install Bun and restart.
6. If one Discord thread is poisoned (context-window errors + listener reconnect loop), clear only that thread/session mapping in Kimaki DB instead of rebooting the server.

See detailed runbook: `references/unresponsive-discord-bot.md`.
