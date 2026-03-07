from datetime import datetime, timezone
from claude_reset.utils import format_countdown, format_local_time, iso_to_datetime

ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_DIM = "\033[2m"
ANSI_RESET = "\033[0m"

FILLED_CHAR = "\u25b0"  # ▰
EMPTY_CHAR = "\u25b1"   # ▱

BAR_WIDTH = 20


def get_color_for_utilization(utilization):
  """Return ANSI color code based on utilization percentage."""
  if utilization >= 90:
    return ANSI_RED
  if utilization >= 70:
    return ANSI_YELLOW
  return ANSI_GREEN


def build_progress_bar(utilization):
  """Build a colored progress bar string using ▰▱ characters."""
  capped = min(utilization, 100)
  filled = round(BAR_WIDTH * capped / 100)
  empty = BAR_WIDTH - filled
  color = get_color_for_utilization(utilization)

  return (
    f"{color}{FILLED_CHAR * filled}{ANSI_RESET}"
    f"{ANSI_DIM}{EMPTY_CHAR * empty}{ANSI_RESET}"
  )


def _format_countdown_and_time(resets_at_str):
  """Format countdown and local time from a resets_at ISO string."""
  reset_dt = iso_to_datetime(resets_at_str)
  now = datetime.now(timezone.utc)
  delta = reset_dt - now
  countdown = format_countdown(delta)
  local_time = format_local_time(reset_dt)
  return f"{countdown} ({local_time})"


def render_compact_line(usage_data):
  """Render single-line compact view (Option E)."""
  parts = []

  # Session
  bucket = usage_data.get("five_hour")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    parts.append(f"\u23f1 {bar} {color}{util:.0f}%{ANSI_RESET} {countdown_str}")

  # Weekly
  bucket = usage_data.get("seven_day")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    parts.append(f"\U0001f4c5 {bar} {color}{util:.0f}%{ANSI_RESET} {countdown_str}")

  # Opus
  bucket = usage_data.get("seven_day_opus")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    parts.append(f"\U0001f52e {bar} {color}{util:.0f}%{ANSI_RESET}")

  # Sonnet
  bucket = usage_data.get("seven_day_sonnet")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    parts.append(f"\u2728 {bar} {color}{util:.0f}%{ANSI_RESET}")

  # Overage
  extra = usage_data.get("extra_usage")
  if extra and extra.get("is_enabled"):
    used = (extra.get("used_credits") or 0) / 100
    limit = (extra.get("monthly_limit") or 0) / 100
    bar = build_progress_bar(extra.get("utilization") or 0)
    parts.append(f"\U0001f4b0 {bar} ${used:.2f}/${limit:.2f}")
  elif extra:
    parts.append(f"\U0001f4b0 off")

  return f" {ANSI_DIM}\u2502{ANSI_RESET} ".join(parts)


def render_detail_lines(usage_data):
  """Render multi-line detailed view (Option F)."""
  lines = []

  # Session
  bucket = usage_data.get("five_hour")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\u23f1 Session  [{bar}]  {color}{util:.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
    )

  # Weekly
  bucket = usage_data.get("seven_day")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\U0001f4c5 Weekly   [{bar}]  {color}{util:.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
    )

  # Opus
  bucket = usage_data.get("seven_day_opus")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\U0001f52e Opus     [{bar}]  {color}{util:.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
    )

  # Sonnet
  bucket = usage_data.get("seven_day_sonnet")
  if bucket:
    util = bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\u2728 Sonnet   [{bar}]  {color}{util:.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
    )

  # Overage
  extra = usage_data.get("extra_usage")
  if extra and extra.get("is_enabled"):
    util = extra.get("utilization") or 0
    used = (extra.get("used_credits") or 0) / 100
    limit = (extra.get("monthly_limit") or 0) / 100
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    lines.append(
      f"\U0001f4b0 Overage  [{bar}]  ${used:.2f} / ${limit:.2f}"
    )
  elif extra:
    lines.append(f"\U0001f4b0 Overage  off")

  return lines
