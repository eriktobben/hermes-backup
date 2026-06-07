# Kimaki Discord shows model footer only, but no response body

## Symptom
- Discord message footer shows `using <provider/model>`
- No assistant text appears
- Kimaki may reconnect listeners repeatedly and eventually restart

## High-signal log indicators
- `context window exceeds limit (...)` from model/provider path
- `SESSION [LISTENER] Stream ended normally ... reconnecting in 500ms` (loop)
- `Failed query: insert into "session_events" ...` during busy/status event persistence

## Root-cause pattern seen in production
1. Model appeared correctly selected in footer, but runtime model source came from DB overrides (`channel_models` / `global_models`), not just file config.
2. Prompt/context was too large for selected model (MiniMax path), producing context-limit failures and empty body behavior.
3. Optional plugins (notably `opencode-swarm`) could inflate prompt size enough to trigger failures.

## Recovery checklist
1. Align model in all locations:
   - `~/.kimaki/opencode-config.json`
   - `~/.config/opencode/opencode.json`
   - `~/.config/opencode/opencode-swarm.json` (if present)
   - SQLite DB: `channel_models`, `global_models`
2. Prefer provider-qualified model IDs consistently (example: `opencode-go/minimax-m2.7`) across config + DB.
3. Remove/disable heavy plugin(s) temporarily (e.g. `opencode-swarm`) and restart Kimaki.
4. Archive/clear affected thread sessions, then retest in a **new** thread.
5. Verify with direct CLI outside Discord:
   - `opencode --pure run "Respond with exactly: OC_MODEL_OK"`

## Notes
- Footer correctness does **not** prove end-to-end response viability.
- Always inspect Kimaki + PM2 logs before concluding model routing is fixed.
