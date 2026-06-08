"""Load and validate config.toml."""

from __future__ import annotations

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
class SourceConfig:
    kind: str = "sample"
    headless: bool = True
    min_delay: float = 2.0
    max_delay: float = 5.0


@dataclass
class DiscordConfig:
    webhook_url: str = ""


@dataclass
class NotifyConfig:
    channels: list[str] = field(default_factory=lambda: ["console"])
    discord: DiscordConfig = field(default_factory=DiscordConfig)


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
    store = raw.get("store", {})
    notify = raw.get("notify", {})
    discord = notify.get("discord", {})
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
        ),
        notify=NotifyConfig(
            channels=notify.get("channels", ["console"]),
            discord=DiscordConfig(webhook_url=discord.get("webhook_url", "")),
        ),
        filter=FilterConfig(
            max_age_days=flt.get("max_age_days", 7),
            require_pokemon_keyword=flt.get("require_pokemon_keyword", True),
        ),
        store_path=store.get("path", "seen.db"),
    )
