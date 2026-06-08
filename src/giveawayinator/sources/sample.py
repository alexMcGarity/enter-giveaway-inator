"""A fake source that replays bundled example posts.

Lets you exercise the whole pipeline (parse -> dedupe -> notify) with zero scraping,
which is how the tests and the `--source sample` demo run.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from ..models import Post

_SAMPLES = [
    Post(
        id="sample-1",
        url="https://www.tiktok.com/@cardshop/video/0000000000000000001",
        author="cardshop",
        caption=(
            "🎉 POKEMON GIVEAWAY 🎉 Win this Charizard ETB! To enter: follow me, "
            "like this post, and tag 3 friends in the comments. Winner announced Friday!"
        ),
        posted_at=datetime.now(timezone.utc),
        hashtag="pokemongiveaway",
    ),
    Post(
        id="sample-2",
        url="https://www.tiktok.com/@tcgdeals/video/0000000000000000002",
        author="tcgdeals",
        caption=(
            "Giving away a booster box! 💥 Comment your favorite starter and save this "
            "post to enter. Ends 6/15."
        ),
        posted_at=datetime.now(timezone.utc),
        hashtag="pokemontcggiveaway",
    ),
    Post(
        id="sample-3",
        url="https://www.tiktok.com/@justcards/video/0000000000000000003",
        author="justcards",
        caption="Pulled a gorgeous Charizard today, look at this art! #pokemon #tcg",
        posted_at=datetime.now(timezone.utc),
        hashtag="pokemon",
    ),
    Post(
        id="live-pokeripperz-sample",
        url="https://www.tiktok.com/@pokeripperz/live",
        author="pokeripperz",
        caption=(
            "🔴 LIVE NOW ripping a booster box! Pokemon giveaway on live — tap the "
            "treasure box to enter, follow to qualify. Winner picked on stream!"
        ),
        posted_at=datetime.now(timezone.utc),
        hashtag="pokemontcggiveaway",
        is_live=True,
    ),
]


class SampleSource:
    def fetch(self, hashtags: list[str], max_per_hashtag: int) -> Iterable[Post]:
        yield from _SAMPLES
