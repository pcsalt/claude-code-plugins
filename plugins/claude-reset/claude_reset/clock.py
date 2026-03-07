"""Session clock — tracks how long the current Claude Code session has been active."""

import json
import os
from datetime import datetime, timezone, timedelta

STALE_THRESHOLD_HOURS = 24


def write_session_start(path, start_time):
  """Write session start time to file."""
  with open(path, "w", encoding="utf-8") as f:
    json.dump({"started_at": start_time.isoformat()}, f)


def read_session_start(path):
  """Read session start time from file. Returns datetime or None."""
  try:
    with open(path, "r", encoding="utf-8") as f:
      data = json.load(f)
    iso_str = data["started_at"].replace("Z", "+00:00")
    return datetime.fromisoformat(iso_str)
  except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError, OSError):
    return None


def format_elapsed(delta):
  """Format elapsed timedelta as human-readable string."""
  total_seconds = int(delta.total_seconds())
  if total_seconds < 60:
    return "< 1m"

  total_minutes = total_seconds // 60
  hours = total_minutes // 60
  minutes = total_minutes % 60

  if hours > 0:
    return f"{hours}h {minutes}m"
  return f"{minutes}m"


def get_session_elapsed(path):
  """Get elapsed time for current session.

  Creates a new session if none exists or if the existing one is stale (>24h).
  Returns timedelta.
  """
  now = datetime.now(timezone.utc)
  start = read_session_start(path)

  if start is None or (now - start) > timedelta(hours=STALE_THRESHOLD_HOURS):
    write_session_start(path, now)
    return now - now

  return now - start
