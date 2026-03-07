import pytest
from datetime import datetime, timezone, timedelta
from claude_reset.utils import (
  format_countdown,
  format_local_time,
  iso_to_datetime,
)


class TestFormatCountdown:
  def test_hours_and_minutes(self):
    delta = timedelta(hours=2, minutes=15, seconds=30)
    assert format_countdown(delta) == "2h 15m"

  def test_minutes_only(self):
    delta = timedelta(minutes=45, seconds=10)
    assert format_countdown(delta) == "45m"

  def test_days_and_hours(self):
    delta = timedelta(days=3, hours=4, minutes=20)
    assert format_countdown(delta) == "3d 4h"

  def test_less_than_one_minute(self):
    delta = timedelta(seconds=30)
    assert format_countdown(delta) == "< 1m"

  def test_zero_delta(self):
    delta = timedelta(0)
    assert format_countdown(delta) == "< 1m"

  def test_negative_delta(self):
    delta = timedelta(seconds=-10)
    assert format_countdown(delta) == "expired"

  def test_exactly_one_hour(self):
    delta = timedelta(hours=1)
    assert format_countdown(delta) == "1h 0m"

  def test_exactly_one_day(self):
    delta = timedelta(days=1)
    assert format_countdown(delta) == "1d 0h"

  def test_days_hours_minutes_truncates_minutes(self):
    """When days > 0, minutes should be omitted for brevity."""
    delta = timedelta(days=2, hours=5, minutes=30)
    assert format_countdown(delta) == "2d 5h"


class TestFormatLocalTime:
  def test_converts_utc_to_local_format(self):
    dt = datetime(2026, 3, 7, 14, 30, 0, tzinfo=timezone.utc)
    result = format_local_time(dt)
    # Should contain hour:minute pattern
    assert ":" in result

  def test_includes_day_for_future_dates(self):
    """When reset is more than 24h away, should include day name."""
    dt = datetime.now(timezone.utc) + timedelta(days=3)
    result = format_local_time(dt)
    # Should contain a day abbreviation
    day_abbrs = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    assert any(day in result for day in day_abbrs)

  def test_no_day_for_same_day(self):
    """When reset is within 24h, should not include day name."""
    dt = datetime.now(timezone.utc) + timedelta(hours=2)
    result = format_local_time(dt)
    day_abbrs = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    assert not any(day in result for day in day_abbrs)


class TestIsoToDatetime:
  def test_parses_iso_with_z_suffix(self):
    result = iso_to_datetime("2026-03-07T14:00:00Z")
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 7
    assert result.hour == 14
    assert result.tzinfo == timezone.utc

  def test_parses_iso_with_offset(self):
    result = iso_to_datetime("2026-03-07T14:00:00+00:00")
    assert result.tzinfo is not None

  def test_invalid_format_raises(self):
    with pytest.raises(ValueError):
      iso_to_datetime("not-a-date")

  def test_empty_string_raises(self):
    with pytest.raises(ValueError):
      iso_to_datetime("")
