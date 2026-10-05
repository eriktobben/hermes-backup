---
name: codepulse-development
description: Use when working on CodePulse (missioncontrol) stack.
---

# CodePulse (missioncontrol) Development

CodePulse is Tobben's agent dashboard: a Laravel app (`pineconehq/missioncontrol`) plus a
Bun/TypeScript relay that supervises opencode on a host machine. App ↔ relay talk over a
signed HTTP uplink and Reverb websockets. Tobben writes in Norwegian — keep user-facing
summaries in Norwegian; code, commits, and PR descriptions in English.

## Where everything lives

- **Active repo clone:** `/home/erik/Projects/missioncontrol-test` (Laravel at repo root,
  `relay/` as sibling folder). `Projects/missioncontrol` is a stale clone — never edit it.
- **Production app:** https://codepulse.pro — Laravel + Reverb + queue worker + scheduler on a
  remote Forge host; deploys from GitHub `main` via Forge. You generally cannot inspect it from
  this box, so rely on relay journals, the opencode DB, and local repro for evidence.
- **Production relay:** runs on this server as systemd user unit `mission-control-relay`
  (`/home/erik/.local/bin/relay run`), supervises opencode on `127.0.0.1:4096`, enrolled to
  codepulse.pro; config `~/.config/mission-control/relay.json` (engine `v1`).
- **opencode state is shared:** every opencode instance (any port) reads the same
  `~/.local/share/opencode/opencode.db`. Treat it as global state; clean up test sessions.

## Delivery chain (debug against this model)

New worktree session: placeholder row (`worktree_status=pending`, `opencode_session_id=null`) →
first message queued (`queued_messages.status=pending`) → `worktree.create` → relay creates
the worktree → `worktree.ready` → app dispatches `session.create` → relay creates the opencode
session → app **adopts** the placeholder (sets `opencode_session_id`) → `DrainSessionQueue`
claims the row → `session.prompt` → relay `promptAsync` → ack flips the row to `sent`.

Failure modes that strand sessions ("worktree created, message stuck pending"):

- Adoption historically relied ONLY on the forwarded `session.created` event. The relay uplink
  POSTs each event batch once and DROPS it on any non-2xx — no retry, no replay. One 500 from
  the app can lose the adoption event forever, and the drain refuses to send while
  `opencode_session_id` is null. The code now also converges adoption from the `session.create`
  command result (the relay retries those), contains per-event exceptions, matches
  `worktree_path` as well as `directory`, and the queue sweep reconciles stranded placeholders
  via `session.sync`. Preserve these invariants when touching the ingest/adoption path.
- Stranded fingerprint in opencode: session title still `New session - <ISO>` and the correct
  worktree directory → the first prompt never ran.
- A dead production queue worker strands *everything* identically — all delivery rides queued
  jobs, so every code fix looks ineffective while synchronous broadcasts (e.g. the
  `worktree.rename` a title change triggers) still work. Before re-debugging adoption, prove
  the queue consumer with the sync probe from `codepulse-relay-pipeline` → "Deploy & recovery
  probes" (`scripts/replay-relay-event.py`): a title replay must rename the worktree branch if
  the app is healthy.

## Dev workflow (repo AGENTS.md applies)

1. Work on a branch in `missioncontrol-test`; never commit to `main`.
2. `php artisan test` — full suite must pass (~30 s; 800+ tests). Subsets:
   `php artisan test tests/Feature/Sessions`.
3. Style: `php vendor/bin/pint <files>` — invoke through `php`; a bare `vendor/bin/pint`
   call can trip the command safety filter.
4. Push the branch and open a PR with `gh pr create` (gh authed as `lyrabot2000`).
5. App-only fixes need no relay rebuild. Relay changes go through the relay release flow
   (see `docs/forge-deployment.md` §7 in the repo).
6. After a merge, confirm the Forge deploy actually landed before calling a fix live: a deploy
   shows as one `command channel` blip in the relay journal (Forge runs `reverb:restart`). A
   "still broken" report made within ~1 minute of the merge may have tested pre-deploy code.

## Debugging & repro

- `references/debugging-playbook.md` — concrete commands: relay journal, opencode DB queries,
  event-stream probes, stranded-session checks, diagnostic order for "message stuck".
- `references/local-repro-harness.md` — stand up an isolated app + relay + opencode stack to
  reproduce or validate a message-flow fix without touching production.

## Pitfalls

- **Every PHP process that dispatches relay commands needs the app's `REVERB_*` env.** A
  driver/worker/sweep started with only `APP_ENV`/`DB_*` broadcasts to a dead default
  (`localhost:8080`) and commands silently never reach the relay — the only trace is
  `relay command broadcast failed` in `storage/logs/laravel.log`. Export `REVERB_*` for serve,
  worker, tinker/driver scripts, and the sweep alike.
- **Never pattern-kill relay/opencode processes.** Kill by stored PID or exact command match;
  a broad `pkill -f relay`-style kill can take down the production relay and its opencode.
- **Clean up test opencode sessions** (`DELETE http://127.0.0.1:4096/session/<id>`) — they are
  visible to every instance sharing the DB, and stray probe sessions pollute production state.
- **Check which clone you are in.** `missioncontrol-test` is the active working copy; the
  older `missioncontrol` clone must not be touched.
- Relay event batches have no replay: never design recovery that assumes "the event will arrive
  eventually". Converge from command results (retried) or reconcile actively (sweep).
