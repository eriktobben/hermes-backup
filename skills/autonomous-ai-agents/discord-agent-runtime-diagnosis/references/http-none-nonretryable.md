# `HTTP None` + `Non-retryable` + `NoneType is not iterable`

Use this note when users report errors like:
- `Non-retryable error (HTTP None)`
- `❌ Non-retryable error (HTTP None): 'NoneType' object is not iterable`

## What it usually means
This is typically a provider/client response-handling failure (null payload or unexpected shape), not a normal HTTP response error and not necessarily a Discord transport failure.

- `HTTP None` => no concrete HTTP status surfaced at failure site.
- `NoneType ... not iterable` => code attempted to iterate a null value in request/response handling.

## Log signatures to confirm
Look in `~/.hermes/logs/agent.log` for:
- `Non-retryable client error: 'NoneType' object is not iterable`
- optional paired signal in gateway flow:
  - `Skipping transcript persistence for failed request in session ... to prevent session growth loop.`

## Practical containment order
1. Check if failures cluster on one `session_id`.
2. Move user to a fresh session/thread.
3. If fresh sessions are healthy, avoid heavy resets.
4. If fresh sessions also fail, restart gateway/service.
5. If still recurring, collect bug report bundle:
   - exact timestamps
   - session IDs
   - ±30–50 lines around each matching error
   - provider + model in use

## Why this matters
Without this distinction, operators often misclassify the incident as Discord gateway instability and over-rotate to DB cleanup/restarts. In this pattern, session rotation and evidence capture are usually higher-value first actions.
