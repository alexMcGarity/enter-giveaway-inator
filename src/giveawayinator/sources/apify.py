"""TikTok source backed by an Apify actor.

TikTok blocks datacenter IPs, so a cloud worker cannot scrape TikTok directly. Apify runs
the scrape on its own (residential / managed) infrastructure and returns JSON, which a
datacenter IP is free to fetch. We call the actor's run-sync endpoint, which runs the actor
and returns its dataset items in one HTTP request, then map those items to Posts.

The default actor is the Clockworks TikTok scraper. We use its *search* mode sorted by
LATEST within a recent date window, not hashtag mode: hashtag mode returns the same
all-time-popular posts every run (so after the first scan everything is already-seen),
whereas search-by-latest brings genuinely fresh posts each scan. Items expose `id`,
`text`, `webVideoUrl`, `authorMeta.name`, and `createTimeISO`; field access is defensive
so a slightly different actor shape still yields usable Posts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable

import httpx

from ..models import Post

Fetcher = Callable[[str, dict, dict], list]
_RUN_SYNC = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"


def _default_fetcher(url: str, params: dict, payload: dict) -> list:
    # Apify actor runs can take a while; allow a generous timeout.
    resp = httpx.post(url, params=params, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()


class ApifySource:
    def __init__(
        self,
        token: str,
        actor: str = "clockworks~tiktok-scraper",
        results_per_hashtag: int = 30,
        search_queries: list[str] | None = None,
        date_filter: str = "PAST_24_HOURS",
        sorting: str = "LATEST",
        fetcher: Fetcher = _default_fetcher,
    ):
        if not token:
            raise ValueError("Apify source requires a token (source.apify.token or APIFY_TOKEN)")
        self.token = token
        self.actor = actor
        self.results_per_hashtag = results_per_hashtag
        self.search_queries = search_queries or []
        self.date_filter = date_filter
        self.sorting = sorting
        self._fetcher = fetcher

    def fetch(self, hashtags: list[str], max_per_hashtag: int) -> Iterable[Post]:
        # Prefer configured search phrases; fall back to the hashtags as plain queries.
        queries = self.search_queries or [h.lstrip("#") for h in hashtags]
        url = _RUN_SYNC.format(actor=self.actor)
        payload = {
            "searchQueries": queries,
            "searchSection": "/video",
            "videoSearchSorting": self.sorting,
            "videoSearchDateFilter": self.date_filter,
            "resultsPerPage": self.results_per_hashtag or max_per_hashtag,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSubtitles": False,
        }
        items = self._fetcher(url, {"token": self.token}, payload)
        for item in items:
            post = self._to_post(item)
            if post:
                yield post

    @staticmethod
    def _to_post(item: dict) -> Post | None:
        vid = str(item.get("id") or "")
        author = (
            (item.get("authorMeta") or {}).get("name")
            or item.get("authorName")
            or "unknown"
        )
        caption = item.get("text") or item.get("caption") or ""
        url = item.get("webVideoUrl") or item.get("url")
        if not url and vid:
            url = f"https://www.tiktok.com/@{author}/video/{vid}"
        if not vid or not url:
            return None

        posted_at = None
        ts = item.get("createTimeISO")
        if ts:
            try:
                posted_at = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        return Post(id=vid, url=url, author=author, caption=caption, posted_at=posted_at)
