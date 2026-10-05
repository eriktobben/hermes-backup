---
name: codepulse-relay-pipeline
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [codepulse, relay, opencode, laravel, message-delivery, diagnosis]
    related_skills: [diagnose, channel-repo-routing, server-diagnostics]
description: "Diagnose stuck CodePulse relay/OpenCode messages."
---

# CodePulse relay pipeline

## Overview

CodePulse (codepulse.pro) drives OpenCode through a relay daemon on this box: the Laravel app (production, remote) broadcasts commands over Reverb; the relay executes them against a supervised local OpenCode server and streams events back over signed HTTP. Every user prompt is delivered through a database queue (`DrainSessionQueue`), and new worktree sessions depend on an event-driven "adoption" step before their first message can go out. Most stuck-message reports trace to one specific hop in this chain — locate the hop from persisted state first, code second.

## When to use

- A CodePulse session message is stuck pending / sending / never delivered
- A new worktree session creates its worktree but the first prompt never runs
- Asked to diagnose, operate, or reproduce the relay or its OpenCode instance
- Don't use for: Hermes/Kimaki runtime failures (use `hermes-troubleshooting` / `discord-agent-runtime-diagnosis`), generic server health (use `server-diagnostics`)

## Component map

| Piece | Where |
|---|---|
| Active app repo | `/home/erik/Projects/missioncontrol-test` — the sibling `missioncontrol` dir is a **stale older checkout**; never edit it |
| Relay daemon | systemd --user unit `mission-control-relay.service`; binary `~/.local/bin/relay`; source in `<repo>/relay/` |
| Relay config | `~/.config/mission-control/relay.json` — `relay_id` equals `Relay.public_id` in the app DB; requests are HMAC-signed over `timestamp.body` with the relay secret |
| OpenCode | Supervised by the relay on `127.0.0.1:4096`, engine `v1`, binary from `~/.npm-global` |
| Production Laravel app | **Remote** Forge server (codepulse.pro) — app DB and Laravel logs are not readable from this box by default |
| Ground-truth store | `~/.local/share/opencode/opencode.db` (SQLite; shared by all local opencode instances) |

## Diagnosis order

Work outside-in: persisted state at each hop before reading any code.

1. **Locate live components** — `systemctl --user status mission-control-relay`, `ps aux | grep -E 'relay|opencode'`, read `relay.json`. Confirm the relay is the one enrolled to production.
2. **Read OpenCode ground truth** — query `opencode.db`:
   - `session` table: title matching `New session - <ISO timestamp>` means the **first prompt never ran** (titles are only LLM-generated after a turn). `directory` names the worktree it belongs to.
   - `event` table: types carry a `.1` suffix (`session.created.1`); its `created` column can be `0` — use the session table's `time_created` instead.
3. **Classify the strand** from the app-side pattern (when accessible): `sessions.opencode_session_id IS NULL` + `worktree_status='ready'` + a `queued_messages` row stuck `pending` = adoption never happened. `status='sending'` with no ack = prompt dispatched but unacknowledged.
4. **Probe OpenCode directly** — `curl 127.0.0.1:4096/global/health`, `GET /session` (lists all sessions with directories and titles). See the SSE trap below before concluding events are missing.
5. **Relay journal** — `journalctl _PID=<relay pid>`. Filter by `_PID`, **not** `-u <unit>`: the supervised opencode child logs under mismatched unit attribution. A healthy keepalive shows no `command channel ... disconnected` lines after startup.
6. **Read code only at the implicated hops** — `SessionUpserter::upsertEvent` (adoption), `DrainSessionQueue` (send guards), `IngestEventsController` (ingest + command results), `WorktreeMirror` (worktree events → `session.create`). Hop-by-hop payloads: `references/pipeline-map.md`.

## The fragile chain (new session, first message)

Placeholder session row (`worktree_status='pending'`) → first prompt promotes it (`directory=<project>/.worktrees/<branch>`, status `queued`) and enqueues the message → `worktree.create` → relay creates the git worktree → `worktree.ready` event → app sets status `ready` and dispatches `session.create` → relay creates the OpenCode session (directory travels in the `x-opencode-directory` header) → OpenCode emits `session.created` on the SSE stream → relay normalizes and POSTs `/api/relay/events` → `SessionUpserter` adopts the placeholder (matches on `directory` + `worktree_status ∈ queued/creating/ready`) and sets `opencode_session_id` → dispatches `DrainSessionQueue` → row claimed `pending→sending` → `session.prompt` → OpenCode runs the turn → `command.result` ack → row `sent`.

## Known fragilities

- **Adoption silently no-ops.** If the placeholder query misses (directory mismatch, `worktree_status` outside the allowed set), `upsertEvent` returns `null` with **no log**; the event is dropped and nothing retries it — `QueueSweep` only drains sessions where `opencode_session_id` is already set. This is the classic permanent strand.
- **Event batches are fire-and-forget.** An HTTP 500 from `/api/relay/events` loses the whole batch — no retry, no replay. One uncaught exception in any event mirror kills every event behind it in the same batch.
- **`session.create` results are never applied to the row.** Convergence relies solely on the `session.created` event; the command result is only recorded.
- **Everything rides the queue — and a dead queue worker masquerades as every other bug.** With `queue:work` not running, no prompt is ever delivered for any session, and every code fix looks ineffective no matter how healthy the relay, OpenCode and adoption are. Split the two failure domains before touching code: synchronous broadcasts (commands sent inside a web request — e.g. the `worktree.rename` a title change triggers) keep working while queued paths (`DrainSessionQueue` deliveries, sweep drains, push notifications) stay silent — that means the queue consumer is the broken link; fix it in Forge (Processes → the `queue:work` daemon; a crash-looping daemon shows why in its log), not in the code. Prove the split with the sync-path probe under "Deploy & recovery probes".

## Deploy & recovery probes

- **Confirm a deploy landed before trusting a "still broken" report.** Forge appends `reverb:restart` to the deploy script, so a deploy appears on the relay as exactly one `command channel connected -> disconnected -> connected` blip: `journalctl _PID=<relay pid> | grep 'command channel'`. A session created within ~1 minute of a merge may have run the old code — align the merge/deploy/session timestamps before re-debugging the fix itself.
- **Replay real, lost events instead of waiting for a retry that never comes.** Batches are fire-and-forget, but any event OpenCode actually emitted (verify it in the `event` table first) can be re-signed with the relay's HMAC and replayed once to the app's `/api/relay/events` — `scripts/replay-relay-event.py`. Replays are idempotent: adopt-or-update, and a duplicate `session.created` cannot double-dispatch a drain.
- **The rename probe isolates the synchronous half end-to-end.** Replay `session.updated` with a real title for a stuck session: adoption dispatches `worktree.rename` on a broadcast (never the queue) and the relay renames the git branch on disk — check `git -C <repo> branch --list 'session-*'`. Rename fires while queued delivery stays silent ⇒ adoption and relay commands are healthy and only the queue consumer is down. Keep the probe title's slug in the `session-<6 alnum>` shape (e.g. "session probe1") so the app's later real-title rename still passes its `^session-[a-z0-9]{6}$` guard.

## Local repro (isolated stack)

`scripts/e2e-chat.sh` in the repo is the working template. For a custom repro of the delivery chain:

- Point `XDG_CONFIG_HOME` at a temp dir so enrollment never touches the production relay config.
- **Patch `opencode_port` away from 4096** in the enrolled `relay.json` before `relay run` — otherwise the supervisor clobbers the production relay's OpenCode.
- Run `php artisan queue:work` — `DrainSessionQueue` is a queued job; without a worker the repro strands by construction.
- The project's git repo needs a real `origin` remote: `worktree.create` runs `git fetch origin <base>` and fails without one (bare origin + clone works).
- `REVERB_*` env must match between app and relay — enrollment echoes the app's Reverb settings into the relay config.

## Common pitfalls

1. **Probe the SSE endpoint the client actually uses.** OpenCode `/event` is directory-scoped via the `x-opencode-directory` header — a headerless probe there misses every other directory's events and falsely suggests events are never emitted. The relay (v1) subscribes to `/global/event`, which is global.
2. **Edit the wrong checkout.** Two missioncontrol dirs exist; `missioncontrol-test` is active. Confirm with `git log -1` dates before touching files.
3. **Share state between repro and production.** Repro daemons must get their own `XDG_CONFIG_HOME` and opencode port; the opencode SQLite store is shared, so probe sessions created during diagnosis land in the same `session` table as real ones (delete them after).
4. **Trust journald unit labels for spawned children.** The relay's supervised opencode logs under its own `_PID`; `-u mission-control-relay` can miss or misattribute those lines.
5. **Read intent from code, outcome from rows.** A 2xx ingest response with unchanged state points at a silent drop inside the app (return-null path), not a transport failure — don't stop at "the event was sent".

## Verification checklist

- [ ] Active repo confirmed (`missioncontrol-test`, current `main`) before any edit
- [ ] Strand classified from persisted state (never-ran vs unacknowledged vs un-adopted) before hypothesising
- [ ] SSE probes hit `/global/event` (or match the client's real endpoint) before concluding events are missing
- [ ] Any repro stack isolated from production ports and relay config
- [ ] Queue consumer confirmed (sync probe fires, queued paths move) before blaming code for a fresh strand
- [ ] Probe sessions cleaned out of `opencode.db` afterwards
