# Footer-only / no-response in new Discord threads

## Symptom
- User sees model footer (e.g., `using ...`) but no substantive answer in Discord thread.
- Happens even in new thread/session.

## High-signal log pattern
- Repeated listener churn:
  - `SESSION [LISTENER] Connected to event stream for thread <id>`
  - `SESSION [LISTENER] Stream ended normally for thread <id>, reconnecting in 500ms`
- Sometimes accompanied by:
  - `SESSION [SESSION EVENT DB] Debounced persistence failed ...`
  - `Failed query: insert into "session_events" ...`
  - `No OpenCode client for thread <id>, retrying ...`

## Verification pattern that prevents misdiagnosis
1. Read session transcript directly:
   - `kimaki session read <sessionId>`
2. If transcript shows normal assistant reasoning/tool calls, model execution succeeded.
3. Then validate delivery path:
   - listener reconnect loops
   - `thread_sessions` mapping and `session_events` insert behavior

## Useful SQL probes
```sql
-- mapping
select thread_id, session_id, created_at
from thread_sessions
where thread_id = '<thread_id>';

-- event presence
select count(*), min(event_index), max(event_index)
from session_events
where thread_id = '<thread_id>';

-- schema/index sanity
select sql from sqlite_master where type='table' and name='session_events';
select name, sql from sqlite_master where type='index' and tbl_name='session_events';
```

## Interpretation
- **Transcript exists + Discord empty** => model/provider not primary fault.
- Prioritize runtime stream/DB state repair (session mapping cleanup, DB integrity checks, process restart with stable env).
- Keep model changes as secondary mitigation, not first diagnosis.
