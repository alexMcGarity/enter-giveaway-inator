"""Clock-time scheduling: run at fixed times of day rather than a fixed interval."""

from __future__ import annotations

from datetime import datetime, timedelta


def parse_times(spec: str) -> list[tuple[int, int]]:
    """Parse "10:00,17:00" into [(10, 0), (17, 0)]."""
    times: list[tuple[int, int]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        hh, mm = part.split(":")
        hour, minute = int(hh), int(mm)
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError(f"Invalid time {part!r} (expected HH:MM, 24-hour)")
        times.append((hour, minute))
    if not times:
        raise ValueError("No times given")
    return times


def next_run_at(times: list[tuple[int, int]], now: datetime) -> datetime:
    """Next datetime strictly after `now` matching one of the daily (hour, minute) times.

    `now` may be timezone-aware; the candidates inherit its tzinfo, so passing a zoneinfo
    datetime keeps the schedule correct across DST changes.
    """
    candidates = []
    for hour, minute in times:
        cand = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if cand <= now:
            cand += timedelta(days=1)
        candidates.append(cand)
    return min(candidates)
