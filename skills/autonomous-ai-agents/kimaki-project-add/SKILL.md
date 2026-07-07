---
name: kimaki-project-add
description: Registers a local repo as a Discord-visible Kimaki project by running `npx kimaki project add` from the project directory. Use when setting up a new project folder/repo that should be visible in Discord channels.
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

- **"Directory does not exist or is not accessible" on a known thread**: Kimaki worktrees under `~/.kimaki/worktrees/<hash>/` get cleaned up overnight (~02:00), likely by OpenCode's snapshot/git-GC cleanup. The git branch with all commits survives — only the local checkout directory is removed. 44 of 51 worktree hash dirs are typically empty. The fix:
  1. Identify the thread's project and worktree branch. Check the kanal's `config.json` for project directory, or query the DB: `python3 -c "import sqlite3; c=sqlite3.connect('$HOME/.kimaki/discord-sessions.db'); print('\\n'.join(str(r) for r in c.execute('SELECT workspace_name, workspace_directory, project_directory FROM thread_workspaces WHERE thread_id=\"<thread_id>\"')))"` — or query by workspace_session: `SELECT w.* FROM thread_workspaces w JOIN thread_sessions s ON w.thread_id=s.thread_id WHERE s.session_id='<session_id>'`
  2. Verify the git branch still exists: `cd <project_directory> && git branch -a | grep <worktree_name>`
  3. Recreate the worktree: `cd <project_directory> && git worktree add <workspace_directory> <worktree_branch>`
  See `references/worktree-cleanup-recovery.md` for full session detail with DB queries and log analysis.

## Operational hardening (PM2 / long-running bot)
When Kimaki is run as a persistent bot process, reduce freeze/restart loops by:
1. Avoid floating `npx kimaki` in PM2 for production-like runs; pin a known kimaki version.
2. Ensure swap exists on small-memory servers (0 swap increases SIGKILL/OOM risk).
3. Configure PM2 safeguards (`max_memory_restart`, backoff) so only the process restarts.
4. Enable log rotation for PM2 logs to prevent uncontrolled growth.
5. Ensure Bun is in the PM2 runtime PATH (or export it in the start command), otherwise Kimaki may repeatedly auto-install Bun and restart.
6. If one Discord thread is poisoned (context-window errors + listener reconnect loop), clear only that thread/session mapping in Kimaki DB instead of rebooting the server.

See detailed runbook: `references/unresponsive-discord-bot.md`.
