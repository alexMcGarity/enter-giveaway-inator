"""Core data models shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Post:
    """A single TikTok post that may be a giveaway."""

    id: str
    url: str
    author: str
    caption: str
    posted_at: datetime | None = None
    hashtag: str | None = None  # the hashtag we found it under
    is_live: bool = False  # True if this is a LIVE stream, not a regular video

    @property
    def live_url(self) -> str:
        """A link that opens this creator's livestream, where the giveaway button lives."""
        if self.is_live and "/live" in self.url:
            return self.url
        return f"https://www.tiktok.com/@{self.author}/live"


@dataclass
class Requirements:
    """Entry requirements parsed out of a giveaway caption."""

    follow: bool = False
    like: bool = False
    comment: bool = False
    save: bool = False
    share: bool = False
    tag: bool = False  # tagging friends is required (count may be unspecified)
    tag_friends: int = 0  # specific number of friends to tag, 0 if unspecified
    deadline: str | None = None  # raw text of any deadline we spotted

    def as_checklist(self) -> list[str]:
        """Human-readable to-do list for entering this giveaway."""
        items: list[str] = []
        if self.follow:
            items.append("Follow the account")
        if self.like:
            items.append("Like the post")
        if self.comment:
            items.append("Leave a comment")
        if self.save:
            items.append("Save the post")
        if self.share:
            items.append("Share / repost")
        if self.tag_friends:
            items.append(f"Tag {self.tag_friends} friend(s)")
        elif self.tag:
            items.append("Tag friend(s)")
        if not items:
            items.append("No explicit requirements found — read the caption")
        return items


@dataclass
class Giveaway:
    """A post we've classified as a giveaway, with parsed requirements."""

    post: Post
    requirements: Requirements
    matched_keywords: list[str] = field(default_factory=list)
    live: bool = False  # giveaway is running on a livestream right now
