import pytest

from giveawayinator import parser
from giveawayinator.sources.whatnot import WhatnotSource

# A trimmed real item shape captured from the devcake searchLiveStreams actor.
SAMPLE_ITEM = {
    "type": "live_stream",
    "stream_id": "6b25564f-c910-4a56-a22a-e5db190605c9",
    "title": "Pokemon GIVEAWAY every 10 min + slab rips",
    "status": "PLAYING",
    "is_live": True,
    "viewer_count": 139,
    "start_time": "2026-06-09T15:16:24.288000+00:00",
    "seller": {"username": "t_slabs"},
    "url": "https://www.whatnot.com/live/6b25564f-c910-4a56-a22a-e5db190605c9",
}


def test_requires_token():
    with pytest.raises(ValueError):
        WhatnotSource(token="")


def test_to_post_maps_live_stream():
    post = WhatnotSource._to_post(SAMPLE_ITEM)
    assert post is not None
    assert post.id == "6b25564f-c910-4a56-a22a-e5db190605c9"
    assert post.author == "t_slabs"
    assert post.is_live is True
    assert post.url.startswith("https://www.whatnot.com/live/")
    assert post.live_url == post.url  # already a /live URL
    assert post.posted_at is not None


def test_to_post_skips_non_live_or_id_less():
    assert WhatnotSource._to_post({"title": "no id"}) is None
    assert WhatnotSource._to_post({"stream_id": "x", "is_live": False}) is None


def test_fetch_builds_live_search_payload_and_maps():
    captured = {}

    def fake_fetcher(url, params, payload):
        captured["url"] = url
        captured["params"] = params
        captured["payload"] = payload
        return [SAMPLE_ITEM, {"title": "skipped, no id"}]

    src = WhatnotSource(token="tok", keywords=["pokemon", "pokemon tcg"], max_results=15,
                        fetcher=fake_fetcher)
    posts = list(src.fetch([], max_per_hashtag=30))

    assert len(posts) == 1
    assert captured["params"] == {"token": "tok"}
    assert captured["payload"]["mode"] == "searchLiveStreams"
    assert captured["payload"]["searchKeywords"] == ["pokemon", "pokemon tcg"]
    assert captured["payload"]["maxResults"] == 15
    assert "devcake~whatnot-data-scraper" in captured["url"]


def test_giveaway_parser_flags_whatnot_show():
    # A live Whatnot show whose title advertises a giveaway parses as a live giveaway.
    post = WhatnotSource._to_post(SAMPLE_ITEM)
    gw = parser.parse(post, ["pokemon", "pokémon", "tcg"])
    assert gw is not None
    assert gw.live is True
    assert "pokemon" in gw.matched_keywords
