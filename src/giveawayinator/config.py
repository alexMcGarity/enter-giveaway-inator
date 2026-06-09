"""Load and validate config.toml."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SearchConfig:
    hashtags: list[str]
    keywords: list[str]
    max_posts_per_hashtag: int = 30
    # Phrases used to open TikTok's LIVE search in your own browser, where you are
    # logged in and can see who is actually streaming right now.
    live_queries: list[str] = field(default_factory=lambda: ["pokemon giveaway", "pokemon cards"])


@dataclass
class ApifyConfig:
    # Apify actor that scrapes TikTok and returns dataset items. Default is the widely
    # used Clockworks TikTok scraper; swap for any actor with a compatible input/output.
    actor: str = "clockworks~tiktok-scraper"
    token: str = ""
    results_per_hashtag: int = 30  # results per search query per scan
    # Search by newest in a recent window so each scan brings FRESH posts (hashtag mode
    # returns stable all-time-popular posts that dedupe to nothing after the first scan).
    search_queries: list[str] = field(
        default_factory=lambda: [
            "pokemon giveaway",
            "pokemon card giveaway",
            "pokemon tcg giveaway",
        ]
    )
    date_filter: str = "PAST_24_HOURS"  # ALL_TIME | PAST_24_HOURS | PAST_WEEK | ...
    sorting: str = "LATEST"  # MOST_RELEVANT | MOST_LIKED | LATEST


@dataclass
class WhatnotConfig:
    # Apify actor for Whatnot live-show discovery (prototype). searchLiveStreams mode.
    actor: str = "devcake~whatnot-data-scraper"
    token: str = ""
    keywords: list[str] = field(default_factory=lambda: ["pokemon"])
    max_results: int = 20


@dataclass
class SourceConfig:
    kind: str = "sample"  # "sample" | "tiktok" | "apify" | "whatnot"
    headless: bool = True
    min_delay: float = 2.0
    max_delay: float = 5.0
    apify: ApifyConfig = field(default_factory=ApifyConfig)
    whatnot: WhatnotConfig = field(default_factory=WhatnotConfig)


@dataclass
class DiscordConfig:
    webhook_url: str = ""


@dataclass
class NtfyConfig:
    topic: str = ""
    server: str = "https://ntfy.sh"
    live_only: bool = True  # only push live giveaways (the ones you enter in the app)


@dataclass
class NotifyConfig:
    channels: list[str] = field(default_factory=lambda: ["console"])
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    ntfy: NtfyConfig = field(default_factory=NtfyConfig)


@dataclass
class FilterConfig:
    max_age_days: int = 7
    require_pokemon_keyword: bool = True


@dataclass
class Config:
    search: SearchConfig
    source: SourceConfig
    notify: NotifyConfig
    filter: FilterConfig
    store_path: str = "seen.db"


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config not found at {path}. Copy config.example.toml to config.toml and edit it."
        )
    with path.open("rb") as fh:
        raw = tomllib.load(fh)

    search = raw.get("search", {})
    source = raw.get("source", {})
    apify = source.get("apify", {})
    whatnot = source.get("whatnot", {})
    store = raw.get("store", {})
    notify = raw.get("notify", {})
    discord = notify.get("discord", {})
    ntfy = notify.get("ntfy", {})
    flt = raw.get("filter", {})

    return Config(
        search=SearchConfig(
            hashtags=search.get("hashtags", []),
            keywords=search.get("keywords", []),
            max_posts_per_hashtag=search.get("max_posts_per_hashtag", 30),
            live_queries=search.get("live_queries", ["pokemon giveaway", "pokemon cards"]),
        ),
        source=SourceConfig(
            kind=source.get("kind", "sample"),
            headless=source.get("headless", True),
            min_delay=source.get("min_delay", 2.0),
            max_delay=source.get("max_delay", 5.0),
            apify=ApifyConfig(
                actor=apify.get("actor", "clockworks~tiktok-scraper"),
                token=os.environ.get("APIFY_TOKEN", apify.get("token", "")),
                results_per_hashtag=apify.get("results_per_hashtag", 30),
                search_queries=apify.get(
                    "search_queries",
                    ["pokemon giveaway", "pokemon card giveaway", "pokemon tcg giveaway"],
                ),
                date_filter=apify.get("date_filter", "PAST_24_HOURS"),
                sorting=apify.get("sorting", "LATEST"),
            ),
            whatnot=WhatnotConfig(
                actor=whatnot.get("actor", "devcake~whatnot-data-scraper"),
                token=os.environ.get("APIFY_TOKEN", whatnot.get("token", "")),
                keywords=whatnot.get("keywords", ["pokemon"]),
                max_results=whatnot.get("max_results", 20),
            ),
        ),
        notify=NotifyConfig(
            channels=notify.get("channels", ["console"]),
            # Secrets prefer env vars (Fly secrets / cloud) over the file, so they never
            # have to be baked into config.cloud.toml or the image.
            discord=DiscordConfig(
                webhook_url=os.environ.get("DISCORD_WEBHOOK_URL", discord.get("webhook_url", "")),
            ),
            ntfy=NtfyConfig(
                topic=os.environ.get("NTFY_TOPIC", ntfy.get("topic", "")),
                server=os.environ.get("NTFY_SERVER", ntfy.get("server", "https://ntfy.sh")),
                live_only=ntfy.get("live_only", True),
            ),
        ),
        filter=FilterConfig(
            max_age_days=flt.get("max_age_days", 7),
            require_pokemon_keyword=flt.get("require_pokemon_keyword", True),
        ),
        store_path=store.get("path", "seen.db"),
    )
