"""Source registry."""

from __future__ import annotations

from ..config import SourceConfig
from .base import Source
from .sample import SampleSource
from .tiktok import TikTokSource

__all__ = ["Source", "SampleSource", "TikTokSource", "build_source"]


def build_source(cfg: SourceConfig) -> Source:
    if cfg.kind == "sample":
        return SampleSource()
    if cfg.kind == "tiktok":
        return TikTokSource(
            headless=cfg.headless,
            min_delay=cfg.min_delay,
            max_delay=cfg.max_delay,
        )
    raise ValueError(f"Unknown source kind: {cfg.kind!r} (expected 'sample' or 'tiktok')")
