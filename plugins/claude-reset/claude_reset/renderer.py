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


def _is_expired(resets_at_str):
  """Check if a resets_at timestamp is in the past."""
  reset_dt = iso_to_datetime(resets_at_str)
  now = datetime.now(timezone.utc)
  return reset_dt <= now


def _format_countdown_and_time(resets_at_str):
  """Format countdown and local time from a resets_at ISO string."""
  reset_dt = iso_to_datetime(resets_at_str)
  now = datetime.now(timezone.utc)
  delta = reset_dt - now
  countdown = format_countdown(delta)
  local_time = format_local_time(reset_dt)
  return f"{countdown} ({local_time})"


def _fmt_tokens(n):
  """Format token count: 200000 -> '200k', 1000000 -> '1M'."""
  if n >= 1000000:
    return f"{n / 1000000:.0f}M"
  if n >= 1000:
    return f"{n / 1000:.0f}k"
  return str(n)


def render_compact_line(usage_data, context_data=None, elapsed=None, git_info=None, cwd=None):
  """Render single-line compact view (Option E)."""
  parts = []

  # Context window
  if context_data and context_data.get("context_pct") is not None:
    ctx_pct = context_data["context_pct"]
    color = get_color_for_utilization(ctx_pct)
    bar = build_progress_bar(ctx_pct)
    out_tok = context_data.get("output_tokens")
    out_label = f" {ANSI_DIM}\u2191{_fmt_tokens(out_tok)}{ANSI_RESET}" if out_tok else ""
    parts.append(f"\U0001f4d0 {bar} {color}{ctx_pct:2.0f}%{ANSI_RESET}{out_label}")

  # Session
  bucket = usage_data.get("five_hour")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    parts.append(f"\u26a1 {bar} {color}{util:2.0f}%{ANSI_RESET} {countdown_str}")

  # Weekly
  bucket = usage_data.get("seven_day")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    parts.append(f"\U0001f4c5 {bar} {color}{util:2.0f}%{ANSI_RESET} {countdown_str}")

  # Opus
  bucket = usage_data.get("seven_day_opus")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    parts.append(f"\U0001f52e {bar} {color}{util:2.0f}%{ANSI_RESET}")

  # Sonnet
  bucket = usage_data.get("seven_day_sonnet")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    parts.append(f"\u2728 {bar} {color}{util:2.0f}%{ANSI_RESET}")

  # Overage
  extra = usage_data.get("extra_usage")
  if extra and extra.get("is_enabled"):
    used = (extra.get("used_credits") or 0) / 100
    limit = (extra.get("monthly_limit") or 0) / 100
    bar = build_progress_bar(extra.get("utilization") or 0)
    parts.append(f"\U0001f4b0 {bar} ${used:.2f}/${limit:.2f}")
  elif extra:
    parts.append(f"\U0001f4b0 off")

  # Clock
  if elapsed is not None:
    from claude_reset.clock import format_elapsed
    parts.append(f"\U0001f551 {format_elapsed(elapsed)}")

  # CWD + Git
  if cwd or git_info is not None:
    from claude_reset.git_info import format_git_compact
    git_str = format_git_compact(git_info, cwd=cwd)
    if git_str:
      parts.append(git_str)

  return f" {ANSI_DIM}\u2502{ANSI_RESET} ".join(parts)


def render_detail_lines(usage_data, context_data=None, elapsed=None, git_info=None, cwd=None):
  """Render multi-line detailed view (Option F)."""
  lines = []

  # Context window
  if context_data and context_data.get("context_pct") is not None:
    ctx_pct = context_data["context_pct"]
    color = get_color_for_utilization(ctx_pct)
    bar = build_progress_bar(ctx_pct)
    ctx_used = context_data.get("context_used")
    ctx_limit = context_data.get("context_limit")
    if ctx_used is not None and ctx_limit is not None:
      token_label = f"  {_fmt_tokens(ctx_used)}/{_fmt_tokens(ctx_limit)}"
    else:
      token_label = ""
    lines.append(
      f"\U0001f4d0 Context  [{bar}]  {color}{ctx_pct:2.0f}%{ANSI_RESET}{token_label}"
    )
    out_tok = context_data.get("output_tokens")
    if out_tok:
      lines.append(
        f"\U0001f4e4 Output   {ANSI_DIM}{_fmt_tokens(out_tok)} tokens{ANSI_RESET}"
      )

  # Session
  bucket = usage_data.get("five_hour")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\u26a1 Session  [{bar}]  {color}{util:2.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
    )

  # Weekly
  bucket = usage_data.get("seven_day")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\U0001f4c5 Weekly   [{bar}]  {color}{util:2.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
    )

  # Opus
  bucket = usage_data.get("seven_day_opus")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\U0001f52e Opus     [{bar}]  {color}{util:2.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
    )

  # Sonnet
  bucket = usage_data.get("seven_day_sonnet")
  if bucket:
    util = 0 if _is_expired(bucket["resets_at"]) else bucket["utilization"]
    color = get_color_for_utilization(util)
    bar = build_progress_bar(util)
    countdown_str = _format_countdown_and_time(bucket["resets_at"])
    lines.append(
      f"\u2728 Sonnet   [{bar}]  {color}{util:2.0f}%{ANSI_RESET}  \u21bb {countdown_str}"
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

  # Clock
  if elapsed is not None:
    from claude_reset.clock import format_elapsed
    lines.append(f"\U0001f551 Elapsed  {format_elapsed(elapsed)}")

  # CWD + Git
  if cwd or git_info is not None:
    from claude_reset.git_info import format_git_detail
    git_str = format_git_detail(git_info, cwd=cwd)
    if git_str:
      lines.append(git_str)

  return lines
