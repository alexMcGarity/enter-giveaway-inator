"""Notifier that opens live-candidate streams in the user's logged-in browser.

Only acts on giveaways flagged live, and caps how many tabs it opens per run so a busy
batch does not bury you in browser tabs. Non-live giveaways are ignored here (they still
reach the other channels).
"""

from __future__ import annotations

from typing import Callable

from ..browser import open_url
from ..models import Giveaway


class BrowserNotifier:
    def __init__(self, max_opens: int = 3, opener: Callable[[str], bool] = open_url):
        self.max_opens = max_opens
        self._opener = opener
        self._opened = 0

    def notify(self, giveaway: Giveaway) -> None:
        if not giveaway.live or self._opened >= self.max_opens:
            return
        self._opener(giveaway.post.live_url)
        self._opened += 1
