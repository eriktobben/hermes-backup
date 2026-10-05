# Isolated local repro harness (app + relay + opencode)

Stand up a fully isolated stack to reproduce or validate a message-flow fix without touching
production. Modeled on `scripts/e2e-chat.sh` in the repo.

## Recipe

1. Work dir outside the repo, e.g. `~/.hermes/tmp/<name>/`. Create a bare `origin.git` plus a
   `repo` clone of it — a real `origin` remote is required because `worktree.create` runs
   `git fetch origin <base>`.
2. Env for EVERY process (export, don't inline per-process): `REVERB_APP_ID/KEY/SECRET`,
   `REVERB_HOST=127.0.0.1`, `REVERB_PORT=<free port, e.g. 8123>`,
   `REVERB_SERVER_PORT=<same>`. App DB: fresh sqlite file via `DB_CONNECTION=sqlite`,
   `DB_DATABASE=<file>`, `APP_ENV=local`.
3. `php artisan migrate:fresh --force` then
   `php artisan db:seed --class=E2eSeeder --force` (creates user + team id 1).
4. Start, in background, storing PIDs: `php artisan serve --port 8999`,
   `php artisan reverb:start`, and `php artisan queue:work` against the TEST sqlite (the queue
   worker is required — drains are queued jobs).
5. Enroll a second, local relay:
   `XDG_CONFIG_HOME=<work>/config bun relay/src/cli.ts enroll --url http://127.0.0.1:8999 --token
   $(php artisan mission-control:issue-enrollment-token 1 | tail -n1) --name repro-host`.
   Then patch `<work>/config/mission-control/relay.json` so `opencode_port` is a FREE port
   (e.g. 4199) — the default 4096 collides with the production relay's opencode.
6. Start it: `XDG_CONFIG_HOME=<work>/config bun relay/src/cli.ts run` — it spawns its own
   opencode on the patched port (which still shares the opencode DB, so clean up afterwards).
7. Register a project row (tinker) whose `directory` points at `<work>/repo`, then drive flows
   with a small bootstrap PHP script:

   ```php
   require '<repo>/vendor/autoload.php';
   $app = require '<repo>/bootstrap/app.php';
   $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
   // replicate the page flow: create placeholder session, set worktree fields,
   // create a pending queued message, then:
   app(RelayCommandDispatcher::class)->dispatch($relay, 'worktree.create',
       app(WorktreeCreatePayload::class)->build($session, $project, $branch), 900);
   ```

8. Observe: poll the test sqlite (python3 `sqlite3`), the relay log file, the opencode API on
   the repro port, and the queue worker output.

## Gotchas (each cost real time)

- `WorktreeCreatePayload::build()` is an INSTANCE method → `app(WorktreeCreatePayload::class)->build(...)`.
- The `Relay` model has NO `withoutTeamScope()` scope (it is not team-scoped); `Project`,
  `Session`, and `QueuedMessage` do.
- Every process that broadcasts (driver scripts, `queue:work`, the sweep) needs the `REVERB_*`
  env or commands go to a dead default (`localhost:8080`) — visible only as
  `relay command broadcast failed` in the app log.
- Cleanup: kill by stored PIDs only — never pattern-kill, because the production relay runs on
  the same box. Delete any test opencode sessions via `DELETE /session/:id` and remove the
  work dir.

## Simulating the "lost event" strand (for recovery fixes)

1. Create the opencode session directly via the API on the repro port with the
   `x-opencode-directory` header pointing at a worktree path — do this BEFORE inserting the
   placeholder, so the forwarded `session.created` finds no placeholder and is dropped.
2. Insert the stranded state: session row with `opencode_session_id=null`,
   `worktree_status='ready'`, `worktree_path` set, `last_activity_at` several minutes old, plus
   a pending queued message with an old `updated_at` (raw `DB::table` update to bypass
   timestamps).
3. Run `php artisan mission-control:queue-sweep` (with `REVERB_*` exported) and watch the
   recovery: sweep → `session.sync` → snapshot adopts the orphan opencode session → drain → the
   queued message flips to `sent` and opencode shows the user+assistant messages.
