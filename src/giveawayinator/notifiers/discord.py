"""Post giveaway alerts to a Discord channel via webhook."""

from __future__ import annotations

import httpx

from ..models import Giveaway


class DiscordNotifier:
    def __init__(self, webhook_url: str):
        if not webhook_url:
            raise ValueError("Discord notifier requires notify.discord.webhook_url in config.toml")
        self.webhook_url = webhook_url

    def notify(self, giveaway: Giveaway) -> None:
        post = giveaway.post
        req = giveaway.requirements

        if giveaway.live:
            fields = [
                {
                    "name": "🔴 LIVE NOW",
                    "value": "Open the live and tap the Giveaway / treasure-box button to join.",
                    "inline": False,
                }
            ]
            checklist = req.as_checklist()
            if checklist[0] != "No explicit requirements found — read the caption":
                fields.append({"name": "Also asks you to", "value": "\n".join(checklist), "inline": False})
            title = f"🔴 LIVE Pokemon giveaway from @{post.author}"
            url = post.live_url
            color = 0xED4245  # red
        else:
            fields = [{"name": "To enter", "value": "\n".join(req.as_checklist()), "inline": False}]
            title = f"🎁 Pokemon giveaway from @{post.author}"
            url = post.url
            color = 0x57F287  # green

        if req.deadline:
            fields.append({"name": "Deadline", "value": req.deadline, "inline": True})

        embed = {
            "title": title,
            "description": post.caption[:1000],
            "url": url,
            "color": color,
            "fields": fields,
        }
        resp = httpx.post(self.webhook_url, json={"embeds": [embed]}, timeout=15)
        resp.raise_for_status()
