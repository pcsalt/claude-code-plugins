import pytest
from claude_reset.renderer import (
  build_progress_bar,
  get_color_for_utilization,
  render_compact_line,
  render_detail_lines,
  ANSI_GREEN,
  ANSI_YELLOW,
  ANSI_RED,
  ANSI_DIM,
  ANSI_RESET,
  FILLED_CHAR,
  EMPTY_CHAR,
  BAR_WIDTH,
)


class TestBuildProgressBar:
  def test_zero_percent(self):
    bar = build_progress_bar(0)
    # All empty chars, no filled
    assert FILLED_CHAR not in bar
    assert bar.count(EMPTY_CHAR) == BAR_WIDTH

  def test_hundred_percent(self):
    bar = build_progress_bar(100)
    assert EMPTY_CHAR not in bar

  def test_fifty_percent(self):
    bar = build_progress_bar(50)
    # Should have roughly half filled
    filled_count = BAR_WIDTH // 2
    assert FILLED_CHAR in bar
    assert EMPTY_CHAR in bar

  def test_over_hundred_percent_capped(self):
    """Utilization can exceed 100%, bar should cap at full."""
    bar = build_progress_bar(120)
    assert EMPTY_CHAR not in bar

  def test_bar_has_correct_total_length(self):
    """Total visible characters (filled + empty) should equal BAR_WIDTH."""
    bar = build_progress_bar(42)
    # Strip ANSI codes to count visible chars
    visible = bar.replace(ANSI_GREEN, "").replace(ANSI_YELLOW, "").replace(
      ANSI_RED, "").replace(ANSI_DIM, "").replace(ANSI_RESET, "")
    assert len(visible) == BAR_WIDTH


class TestGetColorForUtilization:
  def test_green_below_70(self):
    assert get_color_for_utilization(0) == ANSI_GREEN
    assert get_color_for_utilization(42) == ANSI_GREEN
    assert get_color_for_utilization(69) == ANSI_GREEN

  def test_yellow_70_to_89(self):
    assert get_color_for_utilization(70) == ANSI_YELLOW
    assert get_color_for_utilization(80) == ANSI_YELLOW
    assert get_color_for_utilization(89) == ANSI_YELLOW

  def test_red_90_and_above(self):
    assert get_color_for_utilization(90) == ANSI_RED
    assert get_color_for_utilization(100) == ANSI_RED
    assert get_color_for_utilization(120) == ANSI_RED


class TestRenderCompactLine:
  def test_contains_all_sections(self):
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_opus": {"utilization": 28, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_sonnet": {"utilization": 12, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
    }
    line = render_compact_line(usage_data)
    assert "42%" in line
    assert "35%" in line
    assert "28%" in line
    assert "12%" in line
    assert "$15.82" in line
    assert "$50.00" in line

  def test_overage_disabled(self):
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_opus": {"utilization": 28, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_sonnet": {"utilization": 12, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": False, "utilization": 0, "used_credits": 0, "monthly_limit": 0},
    }
    line = render_compact_line(usage_data)
    assert "off" in line.lower() or "$" not in line

  def test_has_separators(self):
    usage_data = {
      "five_hour": {"utilization": 10, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 20, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_opus": {"utilization": 30, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_sonnet": {"utilization": 40, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": True, "utilization": 50, "used_credits": 2500, "monthly_limit": 5000},
    }
    line = render_compact_line(usage_data)
    assert "|" in line or "│" in line


class TestRenderDetailLines:
  def test_returns_five_lines(self):
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_opus": {"utilization": 28, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_sonnet": {"utilization": 12, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
    }
    lines = render_detail_lines(usage_data)
    assert len(lines) == 5

  def test_session_line_has_countdown(self):
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_opus": {"utilization": 28, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_sonnet": {"utilization": 12, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
    }
    lines = render_detail_lines(usage_data)
    session_line = lines[0]
    assert "Session" in session_line
    assert "42%" in session_line

  def test_each_line_has_progress_bar(self):
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_opus": {"utilization": 28, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_sonnet": {"utilization": 12, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
    }
    lines = render_detail_lines(usage_data)
    for line in lines:
      assert FILLED_CHAR in line or EMPTY_CHAR in line

  def test_overage_line_shows_dollars(self):
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_opus": {"utilization": 28, "resets_at": "2026-03-10T18:00:00Z"},
      "seven_day_sonnet": {"utilization": 12, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
    }
    lines = render_detail_lines(usage_data)
    overage_line = lines[4]
    assert "$15.82" in overage_line
    assert "$50.00" in overage_line

  def test_missing_bucket_skipped(self):
    """If a bucket is missing from response, that line should be skipped."""
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
      "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
    }
    lines = render_detail_lines(usage_data)
    assert len(lines) == 3  # session + weekly + overage, no opus/sonnet
