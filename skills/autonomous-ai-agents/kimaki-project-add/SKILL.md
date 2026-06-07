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
3. Run:
   ```bash
   npx kimaki project add
   ```
4. Confirm success output includes:
   - Created channels for project
   - Directory path
   - Discord channel URL

## Notes / pitfalls
- Run the command **inside** the target project folder, or Kimaki may register the wrong directory.
- If `kimaki` is not installed globally, `npx` will install and run it automatically.
- If Git clone fails with "Repository not found", verify repo URL and access rights for the active GitHub SSH identity.
- If Discord-side automation becomes unresponsive, avoid rebooting first; run the troubleshooting checks in `references/unresponsive-discord-bot.md`.

## Operational hardening (PM2 / long-running bot)
When Kimaki is run as a persistent bot process, reduce freeze/restart loops by:
1. Avoid floating `npx kimaki` in PM2 for production-like runs; pin a known kimaki version.
2. Ensure swap exists on small-memory servers (0 swap increases SIGKILL/OOM risk).
3. Configure PM2 safeguards (`max_memory_restart`, backoff) so only the process restarts.
4. Enable log rotation for PM2 logs to prevent uncontrolled growth.
5. Ensure Bun is in the PM2 runtime PATH (or export it in the start command), otherwise Kimaki may repeatedly auto-install Bun and restart.
6. If one Discord thread is poisoned (context-window errors + listener reconnect loop), clear only that thread/session mapping in Kimaki DB instead of rebooting the server.

See detailed runbook: `references/unresponsive-discord-bot.md`.
