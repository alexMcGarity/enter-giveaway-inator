import pytest

from giveawayinator.sources.apify import ApifySource


def test_requires_token():
    with pytest.raises(ValueError):
        ApifySource(token="")


def test_to_post_maps_clockworks_item():
    item = {
        "id": "7648369754712902944",
        "text": "Pokemon giveaway! follow to win",
        "webVideoUrl": "https://www.tiktok.com/@nightfall_gx/video/7648369754712902944",
        "authorMeta": {"name": "nightfall_gx"},
        "createTimeISO": "2026-06-08T05:00:00.000Z",
    }
    post = ApifySource._to_post(item)
    assert post is not None
    assert post.id == "7648369754712902944"
    assert post.author == "nightfall_gx"
    assert post.caption.startswith("Pokemon giveaway")
    assert post.url.endswith("/video/7648369754712902944")
    assert post.posted_at is not None


def test_to_post_skips_item_without_id():
    assert ApifySource._to_post({"text": "no id here"}) is None


def test_to_post_builds_url_when_missing():
    item = {"id": "123", "text": "hi", "authorName": "someone"}
    post = ApifySource._to_post(item)
    assert post is not None
    assert post.url == "https://www.tiktok.com/@someone/video/123"


def test_fetch_uses_injected_fetcher_and_maps_items():
    captured = {}

    def fake_fetcher(url, params, payload):
        captured["url"] = url
        captured["params"] = params
        captured["payload"] = payload
        return [
            {"id": "1", "text": "giveaway a", "authorMeta": {"name": "a"},
             "webVideoUrl": "https://www.tiktok.com/@a/video/1"},
            {"text": "no id, skipped"},
            {"id": "2", "text": "giveaway b", "authorMeta": {"name": "b"},
             "webVideoUrl": "https://www.tiktok.com/@b/video/2"},
        ]

    src = ApifySource(token="tok", actor="clockworks~tiktok-scraper", fetcher=fake_fetcher)
    posts = list(src.fetch(["#pokemongiveaway", "pokemoncards"], max_per_hashtag=30))

    assert [p.id for p in posts] == ["1", "2"]  # the id-less item is dropped
    assert captured["params"] == {"token": "tok"}
    # No search_queries configured -> hashtags become the queries ('#' stripped).
    assert captured["payload"]["searchQueries"] == ["pokemongiveaway", "pokemoncards"]
    assert captured["payload"]["videoSearchSorting"] == "LATEST"
    assert captured["payload"]["videoSearchDateFilter"] == "PAST_24_HOURS"
    assert "clockworks~tiktok-scraper" in captured["url"]


def test_fetch_uses_configured_search_queries():
    captured = {}

    def fake_fetcher(url, params, payload):
        captured["payload"] = payload
        return []

    src = ApifySource(
        token="tok",
        search_queries=["pokemon giveaway", "charizard giveaway"],
        date_filter="PAST_WEEK",
        sorting="LATEST",
        fetcher=fake_fetcher,
    )
    list(src.fetch(["ignored_hashtag"], max_per_hashtag=30))
    assert captured["payload"]["searchQueries"] == ["pokemon giveaway", "charizard giveaway"]
    assert captured["payload"]["videoSearchDateFilter"] == "PAST_WEEK"
