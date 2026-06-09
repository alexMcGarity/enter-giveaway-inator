"""Classify posts as giveaways and extract entry requirements from captions.

This is intentionally heuristic (regex + keyword matching) rather than an LLM call:
it is fast, free, fully offline, and easy to unit test. Swap in an LLM later behind
the same `parse` function if you want richer extraction.
"""

from __future__ import annotations

import re

from .models import Giveaway, Post, Requirements

# --- keyword sets ---------------------------------------------------------

POKEMON_KEYWORDS = [
    "pokemon",
    "pokémon",
    "tcg",
    "booster",
    "charizard",
    "elite trainer",
    "etb",
    "psa",
    "graded card",
    "card giveaway",
]

GIVEAWAY_SIGNALS = [
    "giveaway",
    "give away",
    "giving away",
    "win this",
    "winner",
    "enter to win",
    "free to enter",
    "raffle",
    "givey",  # Whatnot slang: "giveys"
]

# Whatnot live-show lingo: sellers advertise giveaways as "FREE <prize>" or "free every
# 5 mins" rather than the word "giveaway". Kept precise (a prize word must follow soon)
# so it does not fire on "free shipping" and the like.
FREE_PRIZE_PATTERN = re.compile(
    r"\bfree\b[^.\n!]{0,20}\b(booster|pack|box|slab|rip|case|sealed|claim|card|every)\b",
    re.IGNORECASE,
)

# Phrases that mean the giveaway is happening on a livestream right now, where you
# join by tapping the giveaway / treasure-box button instead of commenting on a post.
LIVE_SIGNALS = [
    "live giveaway",
    "giveaway on live",
    "giveaway live",
    "on my live",
    "in my live",
    "join my live",
    "join the live",
    "come to my live",
    "live now",
    "i'm live",
    "im live",
    "going live",
    "treasure box",
    "treasure chest",
    "gift box",
    "tap the giveaway",
    "🔴",
]

# Each requirement maps to a list of patterns that indicate it.
FOLLOW_PATTERNS = [r"\bfollow\b", r"must be following", r"\bf4f\b"]
LIKE_PATTERNS = [
    r"\blike (this|the post|the vid|my|and|&|\+|to (enter|win))\b",
    r"\bdrop a like\b",
    r"\bsmash.{0,6}like\b",
    r"\bdouble tap\b",
]
COMMENT_PATTERNS = [r"\bcomment\b", r"\bdrop a comment\b", r"comment below", r"\bcomment your\b"]
SAVE_PATTERNS = [r"\bsave (this|the post)\b", r"\bbookmark\b"]
SHARE_PATTERNS = [r"\bshare\b", r"\brepost\b", r"\bre-post\b", r"share to your story"]

# Any tag-a-friend ask: "tag 3 friends", "tag your friends", "tag a friend",
# "tag two mutuals", "tag someone", "tag friends".
TAG_ANY_PATTERN = re.compile(
    r"\btag\s+(?:\w+\s+){0,2}(?:friends?|people|mutuals?|someone)\b",
    re.IGNORECASE,
)
# When a specific count is given, capture it: "tag 3 friends", "tag three friends".
TAG_COUNT_PATTERN = re.compile(
    r"\btag\s+(?:(\d+)|(a|one|two|three|four|five))\s+(?:friends?|people|mutuals?)",
    re.IGNORECASE,
)
WORD_NUMBERS = {"a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

# Loose deadline grabber: "ends 6/15", "closes Friday", "winner announced Sunday"
DEADLINE_PATTERN = re.compile(
    r"\b((?:ends?|closes?|deadline|winner announced|drawn?)\b[^.\n!]{0,40})",
    re.IGNORECASE,
)


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def find_keywords(text: str, keywords: list[str]) -> list[str]:
    low = text.lower()
    return [k for k in keywords if k.lower() in low]


def is_giveaway(caption: str) -> bool:
    """True if the caption looks like an actual giveaway (not just a card post)."""
    if _matches_any(caption, [re.escape(s) for s in GIVEAWAY_SIGNALS]):
        return True
    return bool(FREE_PRIZE_PATTERN.search(caption))


def is_pokemon(caption: str, keywords: list[str] | None = None) -> bool:
    return bool(find_keywords(caption, keywords or POKEMON_KEYWORDS))


def is_live_giveaway(caption: str) -> bool:
    """True if the caption indicates the giveaway is running on a livestream."""
    return _matches_any(caption, [re.escape(s) for s in LIVE_SIGNALS])


def parse_requirements(caption: str) -> Requirements:
    """Pull the entry to-do list out of a caption."""
    req = Requirements(
        follow=_matches_any(caption, FOLLOW_PATTERNS),
        like=_matches_any(caption, LIKE_PATTERNS),
        comment=_matches_any(caption, COMMENT_PATTERNS),
        save=_matches_any(caption, SAVE_PATTERNS),
        share=_matches_any(caption, SHARE_PATTERNS),
    )

    if TAG_ANY_PATTERN.search(caption):
        req.tag = True
        count_match = TAG_COUNT_PATTERN.search(caption)
        if count_match:
            digit, word = count_match.groups()
            req.tag_friends = int(digit) if digit else WORD_NUMBERS.get((word or "").lower(), 1)

    deadline_match = DEADLINE_PATTERN.search(caption)
    if deadline_match:
        req.deadline = deadline_match.group(1).strip()

    return req


def parse(post: Post, keywords: list[str] | None = None) -> Giveaway | None:
    """Return a Giveaway if the post qualifies, else None."""
    if not is_giveaway(post.caption):
        return None
    matched = find_keywords(post.caption, keywords or POKEMON_KEYWORDS)
    return Giveaway(
        post=post,
        requirements=parse_requirements(post.caption),
        matched_keywords=matched,
        live=post.is_live or is_live_giveaway(post.caption),
    )
