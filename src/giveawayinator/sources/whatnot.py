"""Whatnot live-show source (prototype) backed by an Apify actor.

Whatnot's GraphQL API is auth-gated (login required) and we keep the bot logged out, so
like the TikTok cloud path we offload to an Apify actor. The default actor's
`searchLiveStreams` mode returns currently-live shows matching a keyword, which we map to
Posts (always `is_live=True`, since these are live streams).

IMPORTANT LIMITATION: Whatnot giveaways are in-stream events that run for ~5 minutes and
require you to be present at the draw. The API exposes live *shows*, not which show has an
active giveaway right now. So this surfaces live Pokemon shows; the pipeline's giveaway
parser then keeps the ones whose titles advertise a giveaway. Shows that run giveaways
without saying so in the title won't be flagged. The intended use is "tell me which
Pokemon shows to jump into", with entry done by hand in the Whatnot app.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from ..models import Post
from .apify import Fetcher, _default_fetcher

_RUN_SYNC = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"


class WhatnotSource:
    def __init__(
        self,
        token: str,
        actor: str = "devcake~whatnot-data-scraper",
        keywords: list[str] | None = None,
        max_results: int = 20,
        fetcher: Fetcher = _default_fetcher,
    ):
        if not token:
            raise ValueError("Whatnot source requires a token (source.whatnot.token or APIFY_TOKEN)")
        self.token = token
        self.actor = actor
        self.keywords = keywords or ["pokemon"]
        self.max_results = max_results
        self._fetcher = fetcher

    def fetch(self, hashtags: list[str], max_per_hashtag: int) -> Iterable[Post]:
        url = _RUN_SYNC.format(actor=self.actor)
        payload = {
            "mode": "searchLiveStreams",
            "searchKeywords": self.keywords or [h.lstrip("#") for h in hashtags],
            "maxResults": self.max_results or max_per_hashtag,
        }
        items = self._fetcher(url, {"token": self.token}, payload)
        for item in items:
            post = self._to_post(item)
            if post:
                yield post

    @staticmethod
    def _to_post(item: dict) -> Post | None:
        sid = item.get("stream_id")
        if not sid or not item.get("is_live", True):
            return None
        seller = item.get("seller") or {}
        author = seller.get("username") or "unknown"
        title = item.get("title") or ""
        url = item.get("url") or f"https://www.whatnot.com/live/{sid}"

        posted_at = None
        ts = item.get("start_time")
        if ts:
            try:
                posted_at = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        return Post(id=str(sid), url=url, author=author, caption=title, posted_at=posted_at, is_live=True)
