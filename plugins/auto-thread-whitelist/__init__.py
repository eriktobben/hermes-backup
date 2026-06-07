"""Auto-thread whitelist plugin for Hermes Discord gateway.

Reads ``discord.auto_thread_channels`` from config.yaml and patches
``DiscordAdapter`` to only auto-thread in whitelisted channels.

Survives ``hermes update`` since this lives outside the Hermes source tree.
"""

import logging
import os

logger = logging.getLogger(__name__)

_whitelist: set = set()


def register(ctx):
    """Plugin entry point — called during gateway/discovery startup."""
    global _whitelist
    try:
        import yaml

        from hermes_cli.config import get_hermes_home

        config_path = get_hermes_home() / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        discord_cfg = config.get("discord", {})
        raw = discord_cfg.get("auto_thread_channels", [])

        if isinstance(raw, str):
            raw = [ch.strip() for ch in raw.split(",") if ch.strip()]

        _whitelist = {str(ch) for ch in raw} if raw else set()

        if not _whitelist:
            logger.info(
                "auto-thread-whitelist: no auto_thread_channels configured, "
                "leaving default auto-thread behaviour unchanged"
            )
            return

        # IMPORTANT: The plugin system loads adapters under hermes_plugins.*
        # namespace, NOT the standard plugins.* path. We must import from
        # the correct module to patch the right class.
        import hermes_plugins.discord_platform.adapter as _discord_adapter_mod

        original = _discord_adapter_mod.DiscordAdapter._handle_message

        async def _patched_handle_message(self, message):
            channel_id = str(getattr(message.channel, "id", ""))

            old_val = os.environ.get("DISCORD_AUTO_THREAD")
            if channel_id not in _whitelist:
                os.environ["DISCORD_AUTO_THREAD"] = "false"
                logger.info(
                    "auto-thread-whitelist: DISABLED auto-thread for channel %s",
                    channel_id,
                )
            else:
                os.environ["DISCORD_AUTO_THREAD"] = "true"
                logger.info(
                    "auto-thread-whitelist: ENABLED auto-thread for channel %s",
                    channel_id,
                )

            try:
                return await original(self, message)
            finally:
                if old_val is not None:
                    os.environ["DISCORD_AUTO_THREAD"] = old_val
                else:
                    os.environ.pop("DISCORD_AUTO_THREAD", None)

        _discord_adapter_mod.DiscordAdapter._handle_message = _patched_handle_message

        logger.info(
            "auto-thread-whitelist: patched DiscordAdapter._handle_message — "
            "%d whitelisted channel(s): %s",
            len(_whitelist),
            ", ".join(sorted(_whitelist)),
        )

    except Exception:
        logger.warning(
            "auto-thread-whitelist: failed to patch DiscordAdapter",
            exc_info=True,
        )

