# Auto-Thread Gateway Configuration (Whitelist Plugin)

The Discord gateway auto-creates threads when `discord.auto_thread: true` (default) and a message triggers the bot. This happens at the platform adapter level before any agent session starts.

**Since ~June 2026:** Erik/Tobben's setup uses a **whitelist plugin** (`auto-thread-whitelist`) that monkey-patches the Discord adapter to only create auto-threads in channels listed in `discord.auto_thread_channels`. This replaces the older `no_thread_channels` blacklist approach.

## Plugin Location

```
~/.hermes/plugins/auto-thread-whitelist/
├── plugin.yaml
└── __init__.py
```

The plugin reads `discord.auto_thread_channels` from config.yaml at gateway startup and monkey-patches `DiscordAdapter._auto_create_thread`. Only channels in the whitelist get auto-threads; all other channels get inline responses.

**Why a plugin?** Modifying the adapter code in `~/.hermes/hermes-agent/` would be overwritten on `hermes update`. The plugin lives outside the source tree under `~/.hermes/plugins/` and survives updates.

## Config (`~/.hermes/config.yaml`)

```yaml
discord:
  auto_thread: true                  # Must be true for auto-thread to work at all
  auto_thread_channels:              # WHITELIST — only these channels get threads
    - 1511404097302171818            # serena-dev
    - 1511501933180092478            # masterfeed-dev
  # no_thread_channels: []           # NOT USED — replaced by whitelist plugin
  free_response_channels: '*'        # All channels are free-response
  thread_require_mention: false

plugins:
  enabled:
    - auto-thread-whitelist          # Must be enabled for whitelist to work
```

## How It Applies

| Channel | Auto-thread |
|---------|-------------|
| `serena-dev` (1511404097302171818) | ✔ — in whitelist |
| `masterfeed-dev` (1511501933180092478) | ✔ — in whitelist |
| Any other channel | ✘ — not in whitelist |

## Adding/Removing Channels

To add a new channel to the auto-thread whitelist:

1. Get the Discord channel ID (right-click channel → Copy ID)
2. Add it to `discord.auto_thread_channels` in `~/.hermes/config.yaml`
3. Restart the gateway: `hermes gateway restart`

To remove a channel, remove it from the list.

## How the Plugin Works (for maintainers)

```python
# In ~/.hermes/plugins/auto-thread-whitelist/__init__.py:

from plugins.platforms.discord.adapter import DiscordAdapter

original = DiscordAdapter._auto_create_thread

async def _patched_auto_create_thread(self, message):
    channel_id = str(message.channel.id)
    if channel_id not in whitelist:
        return None              # Skip thread creation
    return await original(self, message)

DiscordAdapter._auto_create_thread = _patched_auto_create_thread
```

The patch is applied at plugin load time (during `discover_plugins()` at gateway startup) before any messages are processed.

## Restart Required

Changes to these config values take effect on **gateway restart**:
```bash
hermes gateway restart
# or
systemctl --user restart hermes-gateway
```
