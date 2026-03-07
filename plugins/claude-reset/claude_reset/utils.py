from datetime import datetime, timezone, timedelta


def format_countdown(delta):
  """Format a timedelta as human-readable countdown string."""
  if delta.total_seconds() < 0:
    return "expired"

  total_seconds = int(delta.total_seconds())
  if total_seconds < 60:
    return "< 1m"

  days = total_seconds // 86400
  hours = (total_seconds % 86400) // 3600
  minutes = (total_seconds % 3600) // 60

  if days > 0:
    return f"{days}d {hours}h"
  if hours > 0:
    return f"{hours}h {minutes}m"
  return f"{minutes}m"


def format_local_time(dt):
  """Format a UTC datetime as local time string.

  If more than 24h away, includes day abbreviation.
  """
  local_dt = dt.astimezone()
  now = datetime.now(timezone.utc).astimezone()
  diff = dt - datetime.now(timezone.utc)

  if diff.total_seconds() > 86400:
    return local_dt.strftime("%a %H:%M")
  return local_dt.strftime("%H:%M")


def iso_to_datetime(iso_string):
  """Parse an ISO 8601 datetime string to a timezone-aware datetime."""
  if not iso_string:
    raise ValueError("Empty string")

  iso_string = iso_string.replace("Z", "+00:00")
  return datetime.fromisoformat(iso_string)
