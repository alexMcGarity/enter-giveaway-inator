"""Dedupe store so we only notify about each post once."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class SeenStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen (
                post_id    TEXT PRIMARY KEY,
                url        TEXT,
                notified_at TEXT
            )
            """
        )
        self._conn.commit()

    def has_seen(self, post_id: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM seen WHERE post_id = ?", (post_id,))
        return cur.fetchone() is not None

    def mark_seen(self, post_id: str, url: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO seen (post_id, url, notified_at) VALUES (?, ?, ?)",
            (post_id, url, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SeenStore":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
