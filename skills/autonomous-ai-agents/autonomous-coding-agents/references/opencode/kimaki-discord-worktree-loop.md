# Kimaki + OpenCode: Discord thread stops after worktree bootstrap

## Symptom
- User message creates a Discord thread and worktree successfully.
- Initial status appears, then no further bot response.
- Logs show repeated listener reconnects and eventual OpenCode process death.

## Log signature (high confidence)
- `SESSION [LISTENER] Connected to event stream for thread <id>`
- `SESSION [LISTENER] Stream ended normally for thread <id>, reconnecting in 500ms` (repeating)
- later: `Opencode server exited ... signal: SIGKILL`

## Containment-first runbook
1. Verify bot/runtime health:
   - `pm2 ls`
   - `tail -n 200 ~/.pm2/logs/kimaki-error.log`
2. Archive the problematic thread:
   - `npx -y kimaki@<pinned> session archive <thread_id>`
3. Disable auto-worktrees for the channel (preferred temporary containment):
   - via slash command (if available): `/toggle-worktrees`
   - or DB flag in `channel_worktrees` (`enabled=0` for channel)
4. Run a direct OpenCode smoke test **outside Kimaki** to validate provider/model behavior:
   - `opencode --pure run "Respond with exactly: OC_MODEL_OK"`
   - If this hangs or exits without final output, switch to a known-good model (e.g. `openai/gpt-5.4-mini`) and retest.
5. Restart Kimaki and retest with a **new** thread.
6. If stable with worktrees OFF, keep production on that mode while isolating worktree/bootstrap behavior.

## Secondary hardening discovered useful
- Start Kimaki in PM2 with explicit PATH including bun + npm-global bins.
- Ensure healthcheck/restart scripts use the same explicit PATH to avoid drift (`bun not found` cases).
- Keep swap enabled and monitor for memory pressure, but do not assume memory is sole cause when listener-loop signature appears.

## Notes
- This pattern can recur on specific thread IDs; archiving/removing stale thread-session mappings can break reconnect loops.
- Even when worktrees are disabled, listener loops can still happen if the selected model/provider stream never yields assistant output (busy → stream ends → reconnect loop).
- In this case, direct OpenCode CLI (`opencode --pure run ...`) is the fastest discriminator between Kimaki plumbing vs model/provider instability.
- Unknown/invalid model mappings can destabilize runtime; validate active model config if logs show provider/model errors.
- If you manually delete `thread_sessions` while a listener is active, `session_events` inserts can fail on FK constraints and trigger noisy shutdowns. Prefer: archive thread, restart, then cleanup stale rows.
