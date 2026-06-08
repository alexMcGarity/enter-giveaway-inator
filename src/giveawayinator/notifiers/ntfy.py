"""Phone push via ntfy.sh.

TikTok's live giveaway / treasure-box button only exists in the mobile app, so for live
giveaways the entry has to happen on your phone. This pushes an alert to the ntfy app on
your phone with a tap action that opens `@creator/live`, which on a phone with TikTok
installed opens the app right on the stream, where the button lives.

ntfy carries metadata in HTTP headers, which must be latin-1 / ASCII. So the title stays
plain text and emoji are sent via the `Tags` header (ntfy renders shortcodes like
`red_circle` as emoji). The message body is UTF-8 and may contain the caption's emoji.
"""

from __future__ import annotations

from typing import Callable

import httpx

from ..models import Giveaway

Sender = Callable[[str, bytes, dict[str, str]], bool]


def _default_sender(url: str, body: bytes, headers: dict[str, str]) -> bool:
    resp = httpx.post(url, content=body, headers=headers, timeout=15)
    resp.raise_for_status()
    return True


class NtfyNotifier:
    def __init__(
        self,
        topic: str,
        server: str = "https://ntfy.sh",
        live_only: bool = True,
        sender: Sender = _default_sender,
    ):
        if not topic:
            raise ValueError("ntfy notifier requires notify.ntfy.topic in config.toml")
        self.url = f"{server.rstrip('/')}/{topic}"
        self.live_only = live_only
        self._sender = sender

    def notify(self, giveaway: Giveaway) -> None:
        if self.live_only and not giveaway.live:
            return

        post = giveaway.post
        if giveaway.live:
            title = f"LIVE Pokemon giveaway: @{post.author}"
            body = "Open in the TikTok app and tap the giveaway / treasure box to join."
            steps = [s for s in giveaway.requirements.as_checklist() if "No explicit" not in s]
            if steps:
                body += "\nAlso: " + ", ".join(steps)
            click = post.live_url
            tags = "red_circle"
            priority = "high"
        else:
            title = f"Pokemon giveaway: @{post.author}"
            body = ", ".join(giveaway.requirements.as_checklist())
            click = post.url
            tags = "gift"
            priority = "default"

        headers = {
            "Title": title,
            "Click": click,
            "Tags": tags,
            "Priority": priority,
        }
        self._sender(self.url, body.encode("utf-8"), headers)
