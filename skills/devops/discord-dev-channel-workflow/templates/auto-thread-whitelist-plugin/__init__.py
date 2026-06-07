"""Auto-thread whitelist plugin for Hermes Discord gateway.

Reads ``discord.auto_thread_channels`` from config.yaml and monkey-patches
``DiscordAdapter._auto_create_thread`` to only create auto-threads in
whitelisted channels. Channels not in the list get inline responses instead.

Survives ``hermes update`` since this lives outside the Hermes source tree
(under ``~/.hermes/plugins/``).

Usage:
  1. Add to ``~/.hermes/config.yaml``::

        discord:
          auto_thread_channels:
            - 1234567890  # Only these channels get auto-threads

        plugins:
          enabled:
            - auto-thread-whitelist

  2. Restart the gateway: ``hermes gateway restart``

If ``auto_thread_channels`` is empty or absent, the plugin does nothing
and default auto-thread behavior (controlled by ``discord.auto_thread``)
applies unchanged.
"""

import logging

logger = logging.getLogger(__name__)


def register(ctx):
    """Plugin entry point — called during gateway/discovery startup."""
    try:
        import yaml

        from hermes_cli.config import get_hermes_home

        config_path = get_hermes_home() / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        discord_cfg = config.get("discord", {})
        auto_thread_channels = discord_cfg.get("auto_thread_channels", [])

        if isinstance(auto_thread_channels, str):
            auto_thread_channels = [
                ch.strip() for ch in auto_thread_channels.split(",") if ch.strip()
            ]

        whitelist = {str(ch) for ch in auto_thread_channels} if auto_thread_channels else set()

        if not whitelist:
            logger.info(
                "auto-thread-whitelist: no auto_thread_channels configured, "
                "leaving default auto-thread behaviour unchanged"
            )
            return

        # Lazy-import the Discord adapter and monkey-patch _auto_create_thread.
        from plugins.platforms.discord.adapter import DiscordAdapter

        original = DiscordAdapter._auto_create_thread

        async def _patched_auto_create_thread(self, message):
            channel_id = str(getattr(message.channel, "id", ""))
            if channel_id not in whitelist:
                logger.debug(
                    "auto-thread-whitelist: skipping thread in channel %s "
                    "(not in whitelist)",
                    channel_id,
                )
                return None
            return await original(self, message)

        DiscordAdapter._auto_create_thread = _patched_auto_create_thread

        logger.info(
            "auto-thread-whitelist: patched DiscordAdapter — "
            "%d whitelisted channel(s): %s",
            len(whitelist),
            ", ".join(sorted(whitelist)),
        )

    except Exception:
        logger.warning(
            "auto-thread-whitelist: failed to patch DiscordAdapter",
            exc_info=True,
        )
