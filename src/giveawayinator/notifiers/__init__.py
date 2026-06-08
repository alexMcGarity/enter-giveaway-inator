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
        else:
            raise ValueError(f"Unknown notify channel: {channel!r}")
    return notifiers
