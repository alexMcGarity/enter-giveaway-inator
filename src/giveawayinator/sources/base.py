"""Source interface: anything that can yield candidate posts."""

from __future__ import annotations

from typing import Iterable, Protocol

from ..models import Post


class Source(Protocol):
    """A source of candidate posts for a set of hashtags."""

    def fetch(self, hashtags: list[str], max_per_hashtag: int) -> Iterable[Post]:
        """Yield posts found under the given hashtags."""
        ...
