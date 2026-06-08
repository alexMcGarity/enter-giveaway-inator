import tempfile
from pathlib import Path

from giveawayinator.config import (
    Config,
    FilterConfig,
    NotifyConfig,
    SearchConfig,
    SourceConfig,
)
from giveawayinator.pipeline import run_once
from giveawayinator.sources.sample import SampleSource
from giveawayinator.store import SeenStore


class CollectingNotifier:
    def __init__(self):
        self.seen = []

    def notify(self, giveaway):
        self.seen.append(giveaway)


def _config(tmp_db: str) -> Config:
    return Config(
        search=SearchConfig(
            hashtags=["pokemongiveaway"],
            keywords=["pokemon", "pokémon", "charizard", "booster"],
            max_posts_per_hashtag=30,
        ),
        source=SourceConfig(kind="sample"),
        notify=NotifyConfig(channels=["console"]),
        filter=FilterConfig(max_age_days=0, require_pokemon_keyword=True),
        store_path=tmp_db,
    )


def test_run_once_notifies_and_dedupes():
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "seen.db")
        cfg = _config(db)
        notifier = CollectingNotifier()

        with SeenStore(db) as store:
            stats = run_once(cfg, SampleSource(), store, [notifier])

        # Three of the four sample posts are giveaways (the plain card photo is skipped).
        assert stats.giveaways == 3
        assert stats.notified == 3
        assert len(notifier.seen) == 3

        # The live giveaway must be surfaced first.
        assert notifier.seen[0].live is True
        assert all(not g.live for g in notifier.seen[1:])

        # Second run should notify nothing new (dedupe).
        notifier2 = CollectingNotifier()
        with SeenStore(db) as store:
            stats2 = run_once(cfg, SampleSource(), store, [notifier2])
        assert stats2.notified == 0
        assert stats2.skipped_seen == 3
