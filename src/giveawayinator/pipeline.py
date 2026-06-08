"""Glue: fetch -> filter -> parse -> dedupe -> notify."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from . import parser
from .config import Config
from .models import Giveaway
from .notifiers import Notifier
from .sources import Source
from .store import SeenStore


@dataclass
class RunStats:
    fetched: int = 0
    giveaways: int = 0
    notified: int = 0
    skipped_seen: int = 0
    skipped_filtered: int = 0


def _too_old(giveaway: Giveaway, max_age_days: int) -> bool:
    if max_age_days <= 0 or giveaway.post.posted_at is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    return giveaway.post.posted_at < cutoff


def run_once(
    config: Config,
    source: Source,
    store: SeenStore,
    notifiers: list[Notifier],
) -> RunStats:
    stats = RunStats()
    posts = source.fetch(config.search.hashtags, config.search.max_posts_per_hashtag)

    pending: list[Giveaway] = []
    for post in posts:
        stats.fetched += 1

        giveaway = parser.parse(post, config.search.keywords)
        if giveaway is None:
            stats.skipped_filtered += 1
            continue

        if config.filter.require_pokemon_keyword and not giveaway.matched_keywords:
            stats.skipped_filtered += 1
            continue

        if _too_old(giveaway, config.filter.max_age_days):
            stats.skipped_filtered += 1
            continue

        stats.giveaways += 1

        if store.has_seen(post.id):
            stats.skipped_seen += 1
            continue

        pending.append(giveaway)

    # Live giveaways are happening right now, so surface them before regular posts.
    pending.sort(key=lambda g: not g.live)

    for giveaway in pending:
        for notifier in notifiers:
            notifier.notify(giveaway)
        store.mark_seen(giveaway.post.id, giveaway.post.url)
        stats.notified += 1

    return stats
