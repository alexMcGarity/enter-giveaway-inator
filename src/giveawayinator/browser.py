"""Browser handoff: send the user into TikTok LIVE in their own logged-in browser.

TikTok gates all live discovery behind login, and we deliberately do not log the bot
in. So instead of scraping live rooms, we open the relevant TikTok URLs in the user's
default browser, where they are already signed in and can see who is actually streaming
and tap the giveaway button themselves. The bot never authenticates; the human does.
"""

from __future__ import annotations

import urllib.parse
import webbrowser
from typing import Callable

LIVE_SEARCH_URL = "https://www.tiktok.com/search/live?q={q}"


def live_search_url(query: str) -> str:
    """TikTok LIVE search results page for a query (currently-live rooms)."""
    return LIVE_SEARCH_URL.format(q=urllib.parse.quote_plus(query))


def open_url(url: str) -> bool:
    """Open a URL in the user's default browser. Returns False if it could not."""
    try:
        return webbrowser.open(url, new=2)
    except Exception:
        return False


def open_live_search(
    queries: list[str],
    limit: int = 3,
    opener: Callable[[str], bool] = open_url,
) -> list[str]:
    """Open TikTok LIVE search for the given queries. Returns the URLs opened."""
    opened: list[str] = []
    for query in queries[:limit]:
        url = live_search_url(query)
        opener(url)
        opened.append(url)
    return opened
