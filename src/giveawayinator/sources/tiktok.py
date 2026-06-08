"""TikTok hashtag source backed by Playwright.

IMPORTANT / read this:
  TikTok has no public API for this and its Terms of Service prohibit automated
  access. This source browses *public* hashtag pages politely (slow, rate-limited,
  read-only) purely to surface giveaways for a human to review. It does not log in,
  like, comment, or enter anything. Use a throwaway/secondary context, keep volume
  low, and stop if you hit a login wall or challenge. You are responsible for how
  you use it.

TikTok changes its DOM often, so the selectors below are best-effort and will need
maintenance. When they break, run with headless=false to see what changed.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Iterable

from ..models import Post

_HASHTAG_URL = "https://www.tiktok.com/tag/{tag}"


class TikTokSource:
    def __init__(self, headless: bool = True, min_delay: float = 2.0, max_delay: float = 5.0):
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay

    def _sleep(self) -> None:
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def fetch(self, hashtags: list[str], max_per_hashtag: int) -> Iterable[Post]:
        # Imported lazily so the rest of the project works without Playwright installed.
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise RuntimeError(
                "Playwright is required for the tiktok source. Install it with:\n"
                "  pip install playwright && playwright install chromium\n"
                "Or use source.kind = \"sample\" to try the pipeline without scraping."
            ) from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()
            try:
                for tag in hashtags:
                    yield from self._fetch_tag(page, tag, max_per_hashtag)
                    self._sleep()
            finally:
                context.close()
                browser.close()

    def _fetch_tag(self, page, tag: str, limit: int) -> Iterable[Post]:
        page.goto(_HASHTAG_URL.format(tag=tag), wait_until="domcontentloaded")
        self._sleep()

        # Bail early if TikTok is showing a login/challenge wall instead of content.
        if page.query_selector("text=Log in") and not page.query_selector("a[href*='/video/']"):
            return

        seen_urls: set[str] = set()
        # Scroll a few times to load more of the grid. Grab both regular videos and
        # any LIVE tiles (live creators show a badge linking to /@author/live).
        for _ in range(5):
            anchors = page.query_selector_all("a[href*='/video/'], a[href*='/live']")
            for a in anchors:
                href = a.get_attribute("href") or ""
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                # On hashtag grids the full description lives in the thumbnail's img
                # alt text; the anchor's own text is usually just the username.
                img = a.query_selector("img")
                img_alt = img.get_attribute("alt") if img else None
                caption = (img_alt or a.get_attribute("aria-label") or a.inner_text() or "").strip()
                post = self._to_post(href, caption, tag)
                if post:
                    yield post
                if len(seen_urls) >= limit:
                    return
            page.mouse.wheel(0, 2000)
            self._sleep()

    @staticmethod
    def _to_post(href: str, caption: str, tag: str) -> Post | None:
        # Videos: https://www.tiktok.com/@author/video/1234567890
        # Lives:  https://www.tiktok.com/@author/live
        parts = href.rstrip("/").split("/")
        if parts and parts[-1] == "live":
            author = parts[-2].lstrip("@") if len(parts) >= 2 else "unknown"
            # Lives recur, so key the dedupe id per author per day rather than forever.
            day = datetime.now(timezone.utc).strftime("%Y%m%d")
            return Post(
                id=f"live-{author}-{day}",
                url=href,
                author=author,
                caption=caption,
                hashtag=tag,
                is_live=True,
            )
        try:
            vid = parts[-1]
            author = parts[-3].lstrip("@") if len(parts) >= 3 else "unknown"
        except IndexError:
            return None
        if not vid.isdigit():
            return None
        return Post(id=vid, url=href, author=author, caption=caption, hashtag=tag)
