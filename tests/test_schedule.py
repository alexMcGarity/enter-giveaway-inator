from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from giveawayinator.schedule import next_run_at, parse_times

CT = ZoneInfo("America/Chicago")
TIMES = [(10, 0), (17, 0)]


def test_parse_times():
    assert parse_times("10:00,17:00") == [(10, 0), (17, 0)]
    assert parse_times(" 9:30 , 23:15 ") == [(9, 30), (23, 15)]


def test_parse_times_rejects_garbage():
    with pytest.raises(ValueError):
        parse_times("25:00")
    with pytest.raises(ValueError):
        parse_times("")


def test_next_run_before_first_time():
    now = datetime(2026, 6, 8, 8, 0, tzinfo=CT)
    assert next_run_at(TIMES, now) == datetime(2026, 6, 8, 10, 0, tzinfo=CT)


def test_next_run_between_times():
    now = datetime(2026, 6, 8, 12, 0, tzinfo=CT)
    assert next_run_at(TIMES, now) == datetime(2026, 6, 8, 17, 0, tzinfo=CT)


def test_next_run_after_last_time_rolls_to_next_day():
    now = datetime(2026, 6, 8, 19, 0, tzinfo=CT)
    assert next_run_at(TIMES, now) == datetime(2026, 6, 9, 10, 0, tzinfo=CT)


def test_central_is_dst_aware():
    # In June, America/Chicago is CDT (UTC-5); in January it is CST (UTC-6).
    summer = next_run_at(TIMES, datetime(2026, 6, 8, 8, 0, tzinfo=CT))
    winter = next_run_at(TIMES, datetime(2026, 1, 8, 8, 0, tzinfo=CT))
    assert summer.utcoffset().total_seconds() == -5 * 3600
    assert winter.utcoffset().total_seconds() == -6 * 3600
