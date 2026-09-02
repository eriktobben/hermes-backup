# Kimaki/OpenCode unresponsive in Discord (no full reboot first)

Use this when the bot stops responding in Discord and appears to require a server reboot.

## Fast checks
1. Process state:
   - `pm2 show kimaki`
   - `ps aux | grep -Ei 'kimaki|opencode' | grep -v grep`
2. Crash pattern in logs:
   - `tail -n 200 ~/.pm2/logs/kimaki-error.log`
   - Look for `Killed` or `exited with signal SIGKILL`.
3. Runtime health:
   - `free -h` (check RAM + swap)
   - `df -h`
4. OOM evidence:
   - `journalctl --since '24 hours ago' --no-pager | grep -Ei 'oom|out of memory|sigkill|killed process|node::OOMErrorHandler'`

## Known pattern observed
- Repeated `SIGKILL` restarts in PM2 logs.
- No swap configured (`Swap: 0B`).
- Prior Node OOM traces in journald (`FatalProcessOutOfMemory`).
- Large SQLite state files (`~/.local/share/opencode/opencode.db`, `~/.kimaki/discord-sessions.db`) can add memory/IO pressure over time.

## Immediate mitigation
- Restart only Kimaki/OpenCode processes (PM2), not full server reboot.
- Add swap (e.g., 4–8G) on low-memory hosts.
- Pin Kimaki version for PM2 startup instead of floating npx resolution.
- Add PM2 memory guard + restart backoff.
- Ensure PM2 start command exports Bun in PATH, e.g.:
  - `pm2 start /usr/bin/bash --name kimaki -- -lc 'export PATH="$HOME/.bun/bin:$PATH"; exec npx -y kimaki@0.12.0'`

## Disk full causing crash loops (ENOSPC → ENOTEMPTY)

**Symptom:** Kimaki crash-loops with thousands of restarts. PM2 logs show `ENOTEMPTY` errors during `npx` install, or `ENOSPC: no space left on device`. The real issue is 100% disk usage — npm cannot download or extract packages.

**Why ENOTEMPTY appears:** When npm tries to install on a full disk, it may partially extract packages then fail. On retry, it tries to rename partial directories, but the rename target already exists from the failed attempt → `ENOTEMPTY`. This is a red herring — the root cause is always disk space.

**Diagnosis:**
```bash
df -h /
pm2 status | grep kimaki  # check restart count (high = crash loop)
tail -50 ~/.pm2/logs/kimaki-error.log | grep -E 'ENOSPC|ENOTEMPTY'
```

**Fix sequence:**
1. Stop Kimaki first to prevent it from burning restarts during cleanup:
   ```bash
   pm2 stop kimaki
   ```
2. Identify space consumers:
   ```bash
   du -h --max-depth=1 /home/erik | sort -rh | head -15
   ```
3. Safe cleanup targets (order by safety):
   - `npm cache clean --force` (⚠️ needs ~1GB free to run — if disk is 100% full, manually delete dirs first)
   - `rm -rf ~/.kimaki/worktrees/*` (old worktrees, safe — nightly GC deletes these anyway)
   - `rm -rf ~/.cache/*` (general cache)
   - `rm -rf ~/.bun/install/cache/*` (Bun package cache)
   - `rm -rf ~/.npm/_npx/` (npx cache — if corrupted, this is required before restart)
4. After freeing space, run `npm cache clean --force` to reclaim remaining npm cache.
5. If Kimaki still fails with `ERR_MODULE_NOT_FOUND` after freeing space, the npx cache is corrupted:
   ```bash
   rm -rf ~/.npm/_npx/
   ```
6. Restart: `pm2 restart kimaki`
7. Verify: `pm2 status | grep kimaki` (should show online, low restart count)

**Known big space consumers on this server (as of Sep 2026):**
- `~/.npm` — npm cache (can grow to 19GB+)
- `~/.openclaw` — OpenClaw workspaces/memory (~17GB, ask user before deleting)
- `~/.kimaki/worktrees` — Kimaki worktrees (~7GB)
- `~/.cache` — general XDG cache (~11GB)
- `~/.bun` — Bun cache (~1.6GB)

## Thread-specific deadlock pattern (high-value)
Symptom set:
- Bot process is online in PM2 but thread does not respond.
- Logs show `context window exceeds limit` and repeated listener reconnect lines for the same thread ID.

Targeted fix (no reboot):
1. Back up DB: `cp ~/.kimaki/discord-sessions.db ~/.kimaki/discord-sessions.db.bak-$(date +%Y%m%d-%H%M%S)`
2. Remove only the affected thread/session rows in SQLite (`thread_sessions`, `session_events`, `part_messages`) for that thread ID.
3. Restart Kimaki in PM2.
4. Ask user to continue in a fresh thread (or recreate session mapping).

Why this works:
- It clears corrupted/oversized thread context without deleting other active project sessions.

## Follow-up hygiene
- Rotate/truncate PM2 logs.
- Periodically vacuum/cleanup app DBs if supported by upstream tooling.
- Keep a short runbook of exact commands and expected outputs.
