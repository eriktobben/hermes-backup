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
claims the row → `session.prompt` (payload carries only a reference — `message_id` + signed `fetch_url`; the relay downloads the content before `promptAsync`) → ack flips the row to `sent`.

Failure modes that strand sessions ("worktree created, message stuck pending"):

- **All sessions (incl. brand-new) fail at once ⇒ shared model provider, not delivery.** Prompts
  still land but every assistant turn errors within a second; the relay journal shows identical
  `stream error … Insufficient account funds` lines. Triage + gateway probe: `codepulse-relay-pipeline`
  → "Switching model provider" + `references/model-provider-probes.md`. Note the three pin layers —
  the default model in `~/.config/opencode/opencode.json`, per-session `session.model` in
  `opencode.db`, and agent models in `opencode.json` + `opencode-swarm.json` — a fix that touches
  only one layer leaves the rest broken.
- **Session stuck busy with no feedback** (opencode dies mid-turn, e.g. worktree directory
  vanished → ENOENT). The mirror stays `busy` forever, composer locks, user waits silently.
  Fix layers: `sessions.error` column + red banner in ⚡show (prominent, not just the tiny
  queued-card error); `session.error` notification event (push + toast for active users);
  QueueSweep `reapStalledBusySessions` (15-min threshold, requires relay online + no message
  activity → flips to idle + sets error + notifies); auto worktree recovery on missing-directory
  prompt errors (ENOENT/`FileSystem.realPath`/`NotFound` → dispatch `worktree.create`, Cache-capped
  at 3/hour); `worktree.ready` for adopted sessions with pending queued rows → re-drain.
  All of this lives in `resolveQueuedMessageAck` + `attemptWorktreeRecovery` + the sweep step.
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
  the app is healthy. A deploy's queue restart only signals a *running* worker — a daemon that
  is down (e.g. crash-looping on a boot-time DB error) stays down until an explicit
  Forge → Processes → Restart.

## Dev workflow (repo AGENTS.md applies)

1. Work on a branch in `missioncontrol-test`; never commit to `main`.
2. `php artisan test` — full suite must pass (~30 s; 800+ tests). Subsets:
   `php artisan test tests/Feature/Sessions`. Relay changes: also `cd relay && PATH="$HOME/.bun/bin:$PATH" ~/.bun/bin/bun test` — `bun` must be on PATH or the relay build-script tests fail with `bun: command not found`.
3. Style: `php vendor/bin/pint <files>` — invoke through `php`; a bare `vendor/bin/pint`
   call can trip the command safety filter.
4. Push the branch and open a PR with `gh pr create` (gh authed as `lyrabot2000`).
5. App-only fixes need no relay rebuild. For coordinated app↔relay contract changes the relay is backward compatible and the app is not — get the new relay running first, then merge the app PR (this host swaps the production relay binary locally; steps in `codepulse-relay-pipeline` → "Swapping the production relay binary"). Relay releases also use the release flow (`docs/forge-deployment.md` §7).
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
- **Widening a central service's signature breaks hand-rolled mocks.** Before changing e.g.
  `RelayCommandDispatcher::dispatch()`, grep the test tree for `Mockery::mock(<Class>)` helpers —
  their `andReturnUsing(fn ($a, $b, …))` closures restate the OLD parameter list and silently
  drop new trailing arguments, so tests keep asserting the old shape. Update every helper and
  re-run those files.
- **PHP arrow functions capture by value.** `fn ($e) => $arr[] = $e->payload` mutates the
  closure's own copy; use `function ($e) use (&$arr)` when a listener or handler must collect
  results for later assertions.
- **Dev worktree: run `composer install`, do not symlink `vendor`.** A symlinked vendor breaks
  Pest's app bootstrapping — `Event::fake()` fails with a null dispatcher because the framework
  resolves paths through the symlink incorrectly. Install properly in the worktree.
- **Test fixtures: `queued_messages.payload` is NOT NULL.** Always include `'payload' => []`
  when creating queued messages in tests. The Relay factory does NOT set `status_online` to
  true — set it explicitly (`$relay->update(['status_online' => true])`) when testing sweep
  logic that filters on relay liveness.
- **When debugging with the user waiting, deliver incrementally.** State findings as they
  land, don't go silent for long stretches. The user asked "hvor vanskelig kan det være" after
  70 minutes of quiet investigation — status updates and partial fixes beat silence.
- **After resolving test-file conflicts, re-run BOTH suites.** PHP and the relay's TS parse
  independently, and conflicts in append-style test files can drop the previous test's closing
  `});` — it surfaces as `Unexpected end of file` only in the suite whose files were affected.
  Keep both sides when both appended tests, then run both suites.
