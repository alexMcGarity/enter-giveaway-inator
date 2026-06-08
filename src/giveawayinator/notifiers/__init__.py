"""Notifier registry."""

from __future__ import annotations

from ..config import NotifyConfig
from .base import Notifier
from .console import ConsoleNotifier
from .discord import DiscordNotifier

__all__ = ["Notifier", "ConsoleNotifier", "DiscordNotifier", "build_notifiers"]


def build_notifiers(cfg: NotifyConfig) -> list[Notifier]:
    notifiers: list[Notifier] = []
    for channel in cfg.channels:
        if channel == "console":
            notifiers.append(ConsoleNotifier())
        elif channel == "desktop":
            from .desktop import DesktopNotifier  # lazy: optional dependency

            notifiers.append(DesktopNotifier())
        elif channel == "discord":
            notifiers.append(DiscordNotifier(cfg.discord.webhook_url))
        elif channel == "browser":
            from .browser import BrowserNotifier  # opens live candidates in your browser

            notifiers.append(BrowserNotifier())
        elif channel == "ntfy":
            from .ntfy import NtfyNotifier  # phone push with a tap-to-open-app action

            notifiers.append(
                NtfyNotifier(
                    topic=cfg.ntfy.topic,
                    server=cfg.ntfy.server,
                    live_only=cfg.ntfy.live_only,
                )
            )
        else:
            raise ValueError(f"Unknown notify channel: {channel!r}")
    return notifiers
