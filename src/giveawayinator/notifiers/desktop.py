"""Native desktop notification via plyer (optional dependency)."""

from __future__ import annotations

from ..models import Giveaway


class DesktopNotifier:
    def __init__(self) -> None:
        try:
            from plyer import notification  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Desktop notifications need plyer. Install with: pip install 'enter-giveawayinator[desktop]'"
            ) from exc

    def notify(self, giveaway: Giveaway) -> None:
        from plyer import notification

        post = giveaway.post
        if giveaway.live:
            title = f"🔴 LIVE Pokemon giveaway: @{post.author}"
            message = f"Open the live and tap the Giveaway / treasure-box button.\n{post.live_url}"
        else:
            steps = ", ".join(giveaway.requirements.as_checklist())
            title = f"🎁 Pokemon giveaway: @{post.author}"
            message = f"{steps}\n{post.url}"
        notification.notify(title=title, message=message, timeout=15)
