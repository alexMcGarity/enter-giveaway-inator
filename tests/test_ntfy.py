import pytest

from giveawayinator.models import Giveaway, Post, Requirements
from giveawayinator.notifiers.ntfy import NtfyNotifier


def _gw(live: bool, author: str = "shop") -> Giveaway:
    return Giveaway(
        post=Post(id=author, url=f"https://www.tiktok.com/@{author}/video/1", author=author,
                  caption="giveaway", is_live=live),
        requirements=Requirements(follow=True),
        live=live,
    )


class Capture:
    def __init__(self):
        self.calls = []

    def __call__(self, url, body, headers):
        self.calls.append((url, body, headers))
        return True


def test_requires_topic():
    with pytest.raises(ValueError):
        NtfyNotifier(topic="")


def test_live_only_skips_non_live():
    cap = Capture()
    n = NtfyNotifier(topic="t", live_only=True, sender=cap)
    n.notify(_gw(live=False))
    assert cap.calls == []


def test_live_push_has_app_link_and_ascii_headers():
    cap = Capture()
    n = NtfyNotifier(topic="mytopic", server="https://ntfy.sh", live_only=True, sender=cap)
    n.notify(_gw(live=True, author="ripper"))

    assert len(cap.calls) == 1
    url, body, headers = cap.calls[0]
    assert url == "https://ntfy.sh/mytopic"
    assert headers["Click"] == "https://www.tiktok.com/@ripper/live"  # opens the app on mobile
    assert headers["Tags"] == "red_circle"
    assert headers["Priority"] == "high"
    # Headers must be latin-1 safe (no emoji in Title) or ntfy/httpx will reject them.
    for value in headers.values():
        value.encode("latin-1")
    assert isinstance(body, bytes)


def test_non_live_pushed_when_live_only_false():
    cap = Capture()
    n = NtfyNotifier(topic="t", live_only=False, sender=cap)
    n.notify(_gw(live=False, author="cardshop"))
    assert len(cap.calls) == 1
    _, _, headers = cap.calls[0]
    assert headers["Tags"] == "gift"
