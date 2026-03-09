import json
import os
from datetime import datetime, timezone, timedelta
from claude_reset.utils import iso_to_datetime


RESET_BUCKETS = ["five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet"]
CACHE_TTL_SECONDS = 180
LOCK_MAX_AGE_SECONDS = 30


def write_cache(cache_path, usage_data):
  """Write usage data to cache file with timestamp."""
  cache_entry = {
    "fetched_at": datetime.now(timezone.utc).isoformat(),
    "usage_data": usage_data,
  }
  with open(cache_path, "w") as f:
    json.dump(cache_entry, f, indent=2)


def read_cache(cache_path):
  """Read cache file. Returns None if missing or corrupted."""
  if not os.path.exists(cache_path):
    return None
  try:
    with open(cache_path) as f:
      content = f.read()
      if not content.strip():
        return None
      return json.loads(content)
  except (json.JSONDecodeError, OSError):
    return None


def is_cache_valid(cache_entry):
  """Check if cache is still valid (within TTL and no reset times have passed)."""
  if cache_entry is None:
    return False

  usage_data = cache_entry.get("usage_data")
  if usage_data is None:
    return False

  fetched_at_str = cache_entry.get("fetched_at")
  if fetched_at_str is None:
    return False

  now = datetime.now(timezone.utc)

  # TTL check — invalidate if older than CACHE_TTL_SECONDS
  fetched_at = iso_to_datetime(fetched_at_str)
  if (now - fetched_at) > timedelta(seconds=CACHE_TTL_SECONDS):
    return False

  # Reset window check — invalidate if any bucket has reset
  for bucket_key in RESET_BUCKETS:
    bucket = usage_data.get(bucket_key)
    if bucket is None:
      continue
    resets_at = bucket.get("resets_at")
    if resets_at is None:
      continue
    reset_dt = iso_to_datetime(resets_at)
    if reset_dt <= now:
      return False

  return True


def acquire_fetch_lock(lock_path):
  """Try to acquire fetch lock. Returns True if acquired, False if already locked."""
  if is_fetch_locked(lock_path):
    return False
  try:
    with open(lock_path, "w") as f:
      f.write(datetime.now(timezone.utc).isoformat())
    return True
  except OSError:
    return False


def release_fetch_lock(lock_path):
  """Release fetch lock by removing the lock file."""
  try:
    os.remove(lock_path)
  except FileNotFoundError:
    pass


def is_fetch_locked(lock_path):
  """Check if fetch lock is held and not stale."""
  if not os.path.exists(lock_path):
    return False
  try:
    with open(lock_path) as f:
      lock_time_str = f.read().strip()
    if not lock_time_str:
      return False
    lock_time = iso_to_datetime(lock_time_str)
    age = (datetime.now(timezone.utc) - lock_time).total_seconds()
    return age < LOCK_MAX_AGE_SECONDS
  except (OSError, ValueError):
    return False


def has_expired_buckets(usage_data):
  """Check if any rate limit bucket has a resets_at in the past."""
  if usage_data is None:
    return False

  now = datetime.now(timezone.utc)
  for bucket_key in RESET_BUCKETS:
    bucket = usage_data.get(bucket_key)
    if bucket is None:
      continue
    resets_at = bucket.get("resets_at")
    if resets_at is None:
      continue
    reset_dt = iso_to_datetime(resets_at)
    if reset_dt <= now:
      return True

  return False
