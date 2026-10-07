# Model provider probes (opencode)

Distinguish "the pipeline is broken" from "the model provider is broken", and test provider accounts directly without touching sessions.

## Where the pieces live

- Auth: `~/.local/share/opencode/auth.json` — `<provider>: {"type":"api","key":"…"}`; mirrored in the `credential` table in `opencode.db`.
- Provider registry (base URLs, env names, model ids): `~/.cache/opencode/models.json`; live list with models: `GET http://127.0.0.1:4096/config/providers`.
- Effective default model: `GET http://127.0.0.1:4096/config` → `model`.

## Direct gateway probe (status check, no sessions involved)

OpenAI-compatible POST to the provider base URL with the stored key. OpenCode Go example (`opencode-go`, base `https://opencode.ai/zen/go/v1`):

```bash
KEY=$(python3 -c "import json;print(json.load(open('$HOME/.local/share/opencode/auth.json'))['opencode-go']['key'])")
curl -s -X POST 'https://opencode.ai/zen/go/v1/chat/completions' \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -H 'x-opencode-session: ses_<any-real-session-id>' -A 'opencode/0.4.2' \
  -d '{"model":"<model-id>","messages":[{"role":"user","content":"Say OK"}],"max_tokens":8}'
```

- The `x-opencode-session` header is mandatory (400 `MissingSessionID` without it); any existing session id routes fine for a status probe.
- Send an app-like User-Agent: the default Python/urllib UA gets Cloudflare `error code: 1010`; an opencode-style UA passes.
- Read the result: HTTP 402 / `Insufficient account funds` = billing rejection. Repeat with a second model id — rejection across models = account-wide; success on another model = that model's upstream only. HTTP 200 = provider healthy.

## All sessions down at once

Prompts still land (user rows appear in `opencode.db`) but every assistant turn errors within a second; the journal shows identical `stream error` lines for all session ids; brand-new sessions fail their first turn too. That combination points at the shared provider — probe before touching relay/app code.

## Local server endpoints worth knowing (full spec: `GET /doc`)

- Create session: `POST /session` — directory routing via `x-opencode-directory: <dir>` header.
- Prompt: `POST /session/{id}/message` `{"parts":[{"type":"text","text":"…"}]}` — blocks until the turn completes and returns the assistant message incl. `info.error` on failure.
- Model switch (v2; fails on non-migrated v1 sessions with an FK error): `POST /api/session/{id}/model` `{"model":{"id":…,"providerID":…}}`.
- Delete session: `DELETE /session/{id}`.
- Full end-to-end probe: `scripts/probe-model-e2e.py` (scratch session → prompt → report → delete). Session-model switch helper: `scripts/switch-session-model.py`.
- After any per-session model switch: restart the relay unit, then confirm `GET /session/{id}` reports the new model.
