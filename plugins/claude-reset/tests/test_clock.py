import json
import os
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from claude_reset.clock import (
  get_session_elapsed,
  write_session_start,
  read_session_start,
  format_elapsed,
)


@pytest.fixture
def clock_dir():
  with tempfile.TemporaryDirectory() as tmpdir:
    yield tmpdir


class TestWriteAndReadSessionStart:
  def test_writes_and_reads_back(self, clock_dir):
    path = os.path.join(clock_dir, "session.json")
    now = datetime.now(timezone.utc)
    write_session_start(path, now)
    result = read_session_start(path)
    assert abs((result - now).total_seconds()) < 1

  def test_read_missing_file_returns_none(self, clock_dir):
    path = os.path.join(clock_dir, "nonexistent.json")
    assert read_session_start(path) is None

  def test_read_corrupted_file_returns_none(self, clock_dir):
    path = os.path.join(clock_dir, "session.json")
    with open(path, "w") as f:
      f.write("not json{{{")
    assert read_session_start(path) is None


class TestFormatElapsed:
  def test_minutes_only(self):
    assert format_elapsed(timedelta(minutes=23)) == "23m"

  def test_hours_and_minutes(self):
    assert format_elapsed(timedelta(hours=1, minutes=15)) == "1h 15m"

  def test_less_than_one_minute(self):
    assert format_elapsed(timedelta(seconds=30)) == "< 1m"

  def test_zero(self):
    assert format_elapsed(timedelta(0)) == "< 1m"

  def test_exactly_one_hour(self):
    assert format_elapsed(timedelta(hours=1)) == "1h 0m"

  def test_multiple_hours(self):
    assert format_elapsed(timedelta(hours=3, minutes=45)) == "3h 45m"

  def test_days(self):
    assert format_elapsed(timedelta(days=1, hours=2)) == "26h 0m"


class TestGetSessionElapsed:
  def test_returns_elapsed_for_existing_session(self, clock_dir):
    path = os.path.join(clock_dir, "session.json")
    start = datetime.now(timezone.utc) - timedelta(minutes=30)
    write_session_start(path, start)
    elapsed = get_session_elapsed(path)
    assert elapsed is not None
    assert 29 * 60 <= elapsed.total_seconds() <= 31 * 60

  def test_creates_session_if_missing(self, clock_dir):
    path = os.path.join(clock_dir, "session.json")
    elapsed = get_session_elapsed(path)
    assert elapsed is not None
    assert elapsed.total_seconds() < 5
    assert os.path.exists(path)

  def test_resets_stale_session(self, clock_dir):
    """Sessions older than 24h should be reset."""
    path = os.path.join(clock_dir, "session.json")
    old_start = datetime.now(timezone.utc) - timedelta(hours=25)
    write_session_start(path, old_start)
    elapsed = get_session_elapsed(path)
    assert elapsed.total_seconds() < 5
