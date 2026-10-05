# Pipeline map — hop-by-hop commands, events, and payloads

Lookup table for tracing one specific hop. Direction: app = production Laravel (remote), relay = daemon on this box, oc = supervised OpenCode on :4096.

## App → relay (commands, Reverb `private-relay.<relay_id>`, event `relay.command`)

| Command | Payload (key: meaning) | TTL | Sent by |
|---|---|---|---|
| `worktree.create` | `session_id` (session public_id), `project_directory`, `branch`, `base_branch?`, `install_command?` | 900s | page on first prompt / retry / restart |
| `session.create` | `directory` (worktree path), `title?` | 60s | `WorktreeMirror` on `worktree.ready`; page "Finish setup" |
| `session.prompt` | `session_id` (opencode id), `directory`, `text`, `agent?`, `model?`, `attachments?` | 60s (180s w/ attachments) | `DrainSessionQueue` only |
| `session.abort` | `session_id`, `directory` | 60s | page abort / interrupt |
| `session.messages`, `session.todo`, `session.diff`, `session.fork`, `session.delete` | `session_id` + `directory` (+ `messageID?`) | varies | page actions |
| `worktree.remove` / `worktree.merge` / `worktree.rename` | `project_directory`, `path`, `branch?` | 300s+ | page / cleanup |

Command tracking: dispatcher writes `relay-cmd:<id>` into cache (state pending → ok/error); **results are not written to any DB row**. A queued-message delivery additionally persists `command_id` on the `queued_messages` row at claim time so the ack can always find it.

## Relay → app (signed POST `/api/relay/events`)

Body `{seq, events:[{type, payload}]}`. Types handled by `IngestEventsController`:

| Type | Payload | Handled by |
|---|---|---|
| `relay.hello` / `relay.heartbeat` | `hostname`, `version`, `system` stats, `opencode_version/engine`, `channel` state | relay liveness + stats |
| `command.result` | `command_id`, `ok`, `result`, `error` | completes cache entry; acks queued prompts; special-cases `session.sync`, `session.messages`, `worktree.remove`, `session.delete` — **not `session.create`** |
| `relay.batch` | `{events:[...]}` (opencode stream + worktree events) | fans out to the mirrors below |
| `session.created/updated/deleted/status/idle` | `session_id`, `directory?`, `title?`, `parent_id?`, `status?` | `SessionUpserter::upsertEvent` (adoption lives here) |
| `message.updated` / `message.part.updated` | `session_id`, `message_id`, `part_id`, `data`… | `MessageMirror` |
| `permission.asked/replied`, `question.asked/replied/rejected` | `session_id`, `request_id`, … | Permission/Question mirrors |
| `worktree.progress/ready/failed/renamed` | `session_id` (**app public_id**), `stage`, `path?`, `branch?`, `error?` | `WorktreeMirror` |

## Relay → OpenCode (HTTP on :4096)

- v1 client sets `x-opencode-directory: <directory>` per request — directory scoping rides in this header, not the URL.
- `POST /session` (create), `POST /session/{id}/message` (promptAsync = accept-and-run), `GET /session` (list), health at `/global/health`.
- SSE event stream the relay consumes: **`/global/event`** (global; all projects). The bare `/event` route is directory-scoped by the same header — a headerless connection only sees the server-cwd project's events.
- Normalized outbound event shape: `{session_id, directory, title, parent_id, status}`; the normalizer requires `properties.sessionID` + `properties.info` on session events, else the event is dropped relay-side.

## OpenCode → relay (SSE, v1)

| Raw type | Normalized to | Notes |
|---|---|---|
| `session.created` / `session.updated` | same | needs `properties.info.directory` for adoption to match |
| `session.status` | same | `properties.status.type` |
| `session.idle` | same | synthesized `status: 'idle'` |
| `message.updated` / `message.part.updated` | same | part capped at 256 KB UTF-8, snapshot 4 MB |
| `permission.*` / `question.*` / `todo.updated` | same | |

Events are batched (≈100 ms flush) and POSTed once; **a failed POST drops the batch with only a log line** (`opencode event forward failed`). No `Last-Event-ID` replay — a gap during a reconnect is permanent.

## Adoption query (the classic strand)

`SessionUpserter::upsertEvent` — for an unknown `opencode_session_id`, finds a placeholder with the same `relay_id`, `opencode_session_id IS NULL`, `directory = <event directory>`, `worktree_status IN (queued, creating, ready)`. Any mismatch → event silently dropped (`return null`, no log). On success: sets the id, and if the session isn't busy and a pending row exists, dispatches `DrainSessionQueue`.

## Drain guards (`DrainSessionQueue::handle`, in order)

1. Session row missing → done.
2. `opencode_session_id IS NULL` → return (waits for adoption).
3. `status = 'busy'` → return (waits for idle edge).
4. Row in `sending` younger than 15 min → return (`hasInFlightRelayCommand`).
5. Relay offline → mark pending rows with error, broadcast, return.
6. Claim oldest pending row (`interrupt` mode jumps the queue), persist `command_id`, dispatch `session.prompt`.

`QueueSweep` (scheduled each minute in production): reaps `sending` rows older than 95 s back to `pending`, and dispatches drains only for sessions with `opencode_session_id` set, `status='idle'`, quiet >30 s, relay seen <60 s ago.
