from giveawayinator import browser
from giveawayinator.models import Giveaway, Post, Requirements
from giveawayinator.notifiers.browser import BrowserNotifier


def _gw(live: bool, author: str = "shop") -> Giveaway:
    return Giveaway(
        post=Post(id=author, url=f"https://www.tiktok.com/@{author}/live", author=author,
                  caption="giveaway", is_live=live),
        requirements=Requirements(),
        live=live,
    )


def test_live_search_url_encodes_query():
    assert browser.live_search_url("pokemon giveaway") == (
        "https://www.tiktok.com/search/live?q=pokemon+giveaway"
    )


def test_open_live_search_respects_limit():
    opened = []
    urls = browser.open_live_search(
        ["a", "b", "c", "d"], limit=2, opener=lambda u: opened.append(u) or True
    )
    assert len(urls) == 2
    assert opened == urls


def test_browser_notifier_only_opens_live():
    opened = []
    n = BrowserNotifier(max_opens=5, opener=lambda u: opened.append(u) or True)
    n.notify(_gw(live=False))
    assert opened == []  # video post, not live -> no tab
    n.notify(_gw(live=True, author="ripper"))
    assert opened == ["https://www.tiktok.com/@ripper/live"]


def test_browser_notifier_caps_opens():
    opened = []
    n = BrowserNotifier(max_opens=2, opener=lambda u: opened.append(u) or True)
    for i in range(5):
        n.notify(_gw(live=True, author=f"a{i}"))
    assert len(opened) == 2
