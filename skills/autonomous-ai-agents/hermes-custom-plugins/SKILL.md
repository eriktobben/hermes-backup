---
name: hermes-custom-plugins
description: Create custom Hermes plugins that live in ~/.hermes/plugins/ to extend or override gateway behaviour (monkey-patch adapters, add slash commands, intercept hooks). Use when the user wants to modify platform behaviour (Discord, Telegram, etc.) without editing the Hermes source tree.
---

# Hermes Custom Plugins

Custom plugins in `~/.hermes/plugins/<name>/` survive `hermes update` because they live outside the Hermes source tree.

## Structure

```
~/.hermes/plugins/<name>/
├── plugin.yaml          # Manifest (required)
└── __init__.py          # Plugin code with register(ctx) (required)
```

### plugin.yaml

```yaml
name: my-plugin
version: 1.0.0
description: "What it does."
author: "Your Name"
kind: standalone            # standalone | backend | platform | exclusive
```

### __init__.py

```python
import logging

logger = logging.getLogger(__name__)

def register(ctx):
    """Called during gateway startup / plugin discovery."""
    # — read custom config keys —
    # — monkey-patch an adapter method —
    # — register hooks: ctx.register_hook("hook_name", fn) —
    # — register slash commands: ctx.register_command("name", handler=fn, description="") —
```

## Custom Config Keys

Read values from `config.yaml` in `register()`:

```python
import yaml
from hermes_cli.config import get_hermes_home

config_path = get_hermes_home() / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f) or {}

my_setting = config.get("discord", {}).get("my_custom_key", [])
```

Add the key to `~/.hermes/config.yaml`:

```yaml
discord:
  my_custom_key:
    - 1234567890
```

## Monkey-Patching an Adapter

Best for adding behaviour the adapter doesn't natively support. Patch the **smallest method possible** — prefer `_auto_create_thread` over `_handle_message`.

```python
from plugins.platforms.discord.adapter import DiscordAdapter

original = DiscordAdapter._some_method

async def _patched(self, arg):
    # custom logic
    if some_condition:
        return None  # skip original
    return await original(self, arg)

DiscordAdapter._some_method = _patched
```

**Important:** Import the adapter lazily (inside `register()`, not at module top level) to avoid import-order issues at gateway startup.

## Enable the Plugin

```yaml
# config.yaml
plugins:
  enabled:
    - my-plugin-name
```

Then restart: `hermes gateway restart`

## Available Hooks

Registered via `ctx.register_hook("event_name", fn)`:

| Hook | When | Signature |
|------|------|-----------|
| `post_tool_call` | After each tool call | `fn(tool_name, args, result, task_id, session_id, tool_call_id, **_)` |
| `on_session_end` | Session ends | `fn(session_id, completed, interrupted, **_)` |
| `pre_tool_call` | Before a tool runs (can block) | `fn(tool_name, args, task_id, session_id, tool_call_id, **_)` → return `{"action": "block", "message": "..."}` |

Event hooks (from `gateway/hooks.py`): `gateway:startup`, `session:start`, `session:end`, `session:reset`, `agent:start`, `agent:step`, `agent:end`, `command:*`. Create `~/.hermes/hooks/<name>/` with `HOOK.yaml` + `handler.py`.

## Slash Commands

```python
def _handler(raw_args: str) -> Optional[str]:
    # Return text to send back, or None for silent
    return "Result text"

def register(ctx):
    ctx.register_command("command-name", handler=_handler, description="Shows in /help")
```

## Pitfalls

- **Import order** — Import adapters inside `register()`, not at module top level. Gateway may not have loaded the platform module yet during Python import phase.
- **Exception safety** — Wrap everything in `try/except` with `exc_info=True` logging so a plugin failure never blocks gateway startup.
- **Method signatures** — Patch the SMALLEST method possible to minimise breakage from Hermes updates. If a patched method's signature changes, the plugin silently becomes a no-op.
- **No user interaction** — `register()` runs at startup with no user present. Don't use `clarify` or prompt for input.
- **Config format** — YAML lists: `[123, 456]` or multiline `- 123`. Strings handled via `isinstance(auto_thread_channels, str)` check for comma-separated fallback.
- **Restart required** — Plugin changes (`__init__.py` edits, config changes) take effect on `hermes gateway restart`, not mid-session.
