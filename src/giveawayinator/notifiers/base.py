"""Notifier interface."""

from __future__ import annotations

from typing import Protocol

from ..models import Giveaway


class Notifier(Protocol):
    def notify(self, giveaway: Giveaway) -> None:
        """Deliver a single giveaway alert."""
        ...
