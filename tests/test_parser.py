from datetime import datetime, timezone

from giveawayinator import parser
from giveawayinator.models import Post


def _post(caption: str) -> Post:
    return Post(
        id="x",
        url="https://tiktok.com/@a/video/1",
        author="a",
        caption=caption,
        posted_at=datetime.now(timezone.utc),
    )


def test_detects_giveaway():
    assert parser.is_giveaway("Huge giveaway! win this booster box")
    assert parser.is_giveaway("Giving away a booster box today")
    assert not parser.is_giveaway("Look at this card I pulled today")


def test_requirements_full_checklist():
    caption = (
        "Pokemon giveaway! follow me, like this post, comment your favorite, "
        "save this and tag 3 friends. Ends 6/15."
    )
    req = parser.parse_requirements(caption)
    assert req.follow
    assert req.like
    assert req.comment
    assert req.save
    assert req.tag_friends == 3
    assert req.deadline and "6/15" in req.deadline


def test_tag_word_number():
    req = parser.parse_requirements("tag two friends to enter")
    assert req.tag and req.tag_friends == 2

    req2 = parser.parse_requirements("tag a friend below")
    assert req2.tag and req2.tag_friends == 1


def test_tag_without_count():
    # "tag your friends" has no number, but is still a tag requirement.
    for caption in ["tag your friends", "make sure to tag friends", "tag someone below"]:
        req = parser.parse_requirements(caption)
        assert req.tag is True
        assert req.tag_friends == 0
        assert any("Tag friend(s)" == item for item in req.as_checklist())


def test_no_tag_requirement():
    req = parser.parse_requirements("follow and like to win")
    assert req.tag is False


def test_parse_returns_none_for_non_giveaway():
    assert parser.parse(_post("just a cool pokemon card #tcg")) is None


def test_parse_matches_pokemon_keywords():
    gw = parser.parse(_post("Charizard ETB giveaway! follow + like to win"))
    assert gw is not None
    assert "charizard" in gw.matched_keywords
    assert gw.requirements.follow and gw.requirements.like


def test_detects_live_giveaway_from_caption():
    gw = parser.parse(_post("Pokemon giveaway on live! tap the treasure box, follow to win"))
    assert gw is not None
    assert gw.live is True


def test_regular_post_is_not_live():
    gw = parser.parse(_post("Pokemon giveaway! comment and follow to win this charizard"))
    assert gw is not None
    assert gw.live is False


def test_live_flag_from_post_even_without_caption_signal():
    live_post = Post(
        id="live-x",
        url="https://www.tiktok.com/@a/live",
        author="a",
        caption="booster box giveaway, follow to win",
        is_live=True,
    )
    gw = parser.parse(live_post)
    assert gw is not None
    assert gw.live is True
    assert gw.post.live_url == "https://www.tiktok.com/@a/live"


def test_checklist_fallback_when_no_requirements():
    req = parser.parse_requirements("giveaway, details in bio")
    items = req.as_checklist()
    assert any("read the caption" in i.lower() for i in items)
