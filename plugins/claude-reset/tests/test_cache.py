import json
import os
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from claude_reset.cache import (
  read_cache,
  write_cache,
  is_cache_valid,
  has_expired_buckets,
)


@pytest.fixture
def cache_dir():
  with tempfile.TemporaryDirectory() as tmpdir:
    yield tmpdir


@pytest.fixture
def sample_usage_data():
  future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
  return {
    "five_hour": {"utilization": 42, "resets_at": future},
    "seven_day": {"utilization": 35, "resets_at": future},
    "seven_day_opus": {"utilization": 28, "resets_at": future},
    "seven_day_sonnet": {"utilization": 12, "resets_at": future},
    "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
  }


class TestWriteCache:
  def test_creates_cache_file(self, cache_dir, sample_usage_data):
    cache_path = os.path.join(cache_dir, "cache.json")
    write_cache(cache_path, sample_usage_data)
    assert os.path.exists(cache_path)

  def test_cache_contains_usage_data(self, cache_dir, sample_usage_data):
    cache_path = os.path.join(cache_dir, "cache.json")
    write_cache(cache_path, sample_usage_data)
    with open(cache_path) as f:
      cached = json.load(f)
    assert cached["usage_data"]["five_hour"]["utilization"] == 42

  def test_cache_contains_fetched_at(self, cache_dir, sample_usage_data):
    cache_path = os.path.join(cache_dir, "cache.json")
    write_cache(cache_path, sample_usage_data)
    with open(cache_path) as f:
      cached = json.load(f)
    assert "fetched_at" in cached


class TestReadCache:
  def test_returns_none_when_no_file(self, cache_dir):
    cache_path = os.path.join(cache_dir, "nonexistent.json")
    assert read_cache(cache_path) is None

  def test_returns_data_when_file_exists(self, cache_dir, sample_usage_data):
    cache_path = os.path.join(cache_dir, "cache.json")
    write_cache(cache_path, sample_usage_data)
    result = read_cache(cache_path)
    assert result is not None
    assert result["usage_data"]["five_hour"]["utilization"] == 42

  def test_returns_none_on_corrupted_file(self, cache_dir):
    cache_path = os.path.join(cache_dir, "cache.json")
    with open(cache_path, "w") as f:
      f.write("not valid json{{{")
    assert read_cache(cache_path) is None

  def test_returns_none_on_empty_file(self, cache_dir):
    cache_path = os.path.join(cache_dir, "cache.json")
    with open(cache_path, "w") as f:
      f.write("")
    assert read_cache(cache_path) is None


class TestIsCacheValid:
  def test_valid_when_all_resets_in_future(self, sample_usage_data):
    cache_entry = {
      "usage_data": sample_usage_data,
      "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    assert is_cache_valid(cache_entry) is True

  def test_invalid_when_five_hour_expired(self):
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    cache_entry = {
      "usage_data": {
        "five_hour": {"utilization": 42, "resets_at": past},
        "seven_day": {"utilization": 35, "resets_at": future},
        "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
      },
      "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    assert is_cache_valid(cache_entry) is False

  def test_invalid_when_seven_day_expired(self):
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    cache_entry = {
      "usage_data": {
        "five_hour": {"utilization": 42, "resets_at": future},
        "seven_day": {"utilization": 35, "resets_at": past},
        "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
      },
      "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    assert is_cache_valid(cache_entry) is False

  def test_valid_without_optional_buckets(self):
    """Cache is valid even if opus/sonnet buckets are missing."""
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    cache_entry = {
      "usage_data": {
        "five_hour": {"utilization": 42, "resets_at": future},
        "seven_day": {"utilization": 35, "resets_at": future},
        "extra_usage": {"is_enabled": True, "utilization": 31, "used_credits": 1582, "monthly_limit": 5000},
      },
      "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    assert is_cache_valid(cache_entry) is True

  def test_invalid_when_missing_usage_data_key(self):
    cache_entry = {"fetched_at": datetime.now(timezone.utc).isoformat()}
    assert is_cache_valid(cache_entry) is False

  def test_invalid_when_ttl_expired(self, sample_usage_data):
    """Cache older than TTL should be invalid even if resets are in future."""
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=90)).isoformat()
    cache_entry = {
      "usage_data": sample_usage_data,
      "fetched_at": old_time,
    }
    assert is_cache_valid(cache_entry) is False

  def test_valid_when_within_ttl(self, sample_usage_data):
    """Cache within TTL and resets in future should be valid."""
    recent_time = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    cache_entry = {
      "usage_data": sample_usage_data,
      "fetched_at": recent_time,
    }
    assert is_cache_valid(cache_entry) is True

  def test_invalid_when_missing_fetched_at(self, sample_usage_data):
    """Cache without fetched_at should be invalid."""
    cache_entry = {
      "usage_data": sample_usage_data,
    }
    assert is_cache_valid(cache_entry) is False


class TestHasExpiredBuckets:
  def test_no_expired_buckets(self):
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": future},
      "seven_day": {"utilization": 35, "resets_at": future},
    }
    assert has_expired_buckets(usage_data) is False

  def test_one_expired_bucket(self):
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": past},
      "seven_day": {"utilization": 35, "resets_at": future},
    }
    assert has_expired_buckets(usage_data) is True

  def test_all_expired_buckets(self):
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": past},
      "seven_day": {"utilization": 35, "resets_at": past},
    }
    assert has_expired_buckets(usage_data) is True

  def test_none_usage_data(self):
    assert has_expired_buckets(None) is False

  def test_missing_buckets(self):
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    usage_data = {
      "five_hour": {"utilization": 42, "resets_at": future},
    }
    assert has_expired_buckets(usage_data) is False
