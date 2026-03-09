import os
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from claude_reset.api import RateLimitError
from claude_reset.main import get_usage_data, CACHE_PATH


@pytest.fixture
def sample_usage_data():
  future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
  return {
    "five_hour": {"utilization": 42, "resets_at": future},
    "seven_day": {"utilization": 35, "resets_at": future},
    "seven_day_sonnet": {"utilization": 12, "resets_at": future},
  }


@pytest.fixture
def expired_usage_data():
  past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
  future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
  return {
    "five_hour": {"utilization": 42, "resets_at": past},
    "seven_day": {"utilization": 35, "resets_at": future},
    "seven_day_sonnet": {"utilization": 12, "resets_at": future},
  }


class TestGetUsageDataRateLimitFallback:
  """On 429, stale cache should be returned even with expired buckets."""

  @patch("claude_reset.main.release_fetch_lock")
  @patch("claude_reset.main.acquire_fetch_lock", return_value=True)
  @patch("claude_reset.main.is_fetch_locked", return_value=False)
  @patch("claude_reset.main.fetch_usage_data")
  @patch("claude_reset.main.read_oauth_token")
  @patch("claude_reset.main.read_cache")
  @patch("claude_reset.main.is_cache_valid", return_value=False)
  def test_429_returns_stale_cache_with_expired_buckets(
    self, mock_valid, mock_read_cache, mock_token, mock_fetch,
    mock_locked, mock_acquire, mock_release, expired_usage_data
  ):
    mock_read_cache.return_value = {
      "usage_data": expired_usage_data,
      "fetched_at": (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat(),
    }
    mock_token.return_value = {
      "access_token": "tok", "refresh_token": "ref", "is_expired": False,
    }
    mock_fetch.side_effect = RateLimitError()

    result = get_usage_data()
    assert result is not None
    assert result["five_hour"]["utilization"] == 42

  @patch("claude_reset.main.release_fetch_lock")
  @patch("claude_reset.main.acquire_fetch_lock", return_value=True)
  @patch("claude_reset.main.is_fetch_locked", return_value=False)
  @patch("claude_reset.main.fetch_usage_data")
  @patch("claude_reset.main.read_oauth_token")
  @patch("claude_reset.main.read_cache")
  @patch("claude_reset.main.is_cache_valid", return_value=False)
  def test_non_429_error_rejects_stale_cache_with_expired_buckets(
    self, mock_valid, mock_read_cache, mock_token, mock_fetch,
    mock_locked, mock_acquire, mock_release, expired_usage_data
  ):
    mock_read_cache.return_value = {
      "usage_data": expired_usage_data,
      "fetched_at": (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat(),
    }
    mock_token.return_value = {
      "access_token": "tok", "refresh_token": "ref", "is_expired": False,
    }
    mock_fetch.side_effect = Exception("network error")

    result = get_usage_data()
    assert result is None


class TestGetUsageDataFetchLock:
  """When another process is fetching, serve stale cache."""

  @patch("claude_reset.main.is_fetch_locked", return_value=True)
  @patch("claude_reset.main.read_cache")
  @patch("claude_reset.main.is_cache_valid", return_value=False)
  def test_locked_returns_stale_cache(
    self, mock_valid, mock_read_cache, mock_locked, sample_usage_data
  ):
    mock_read_cache.return_value = {
      "usage_data": sample_usage_data,
      "fetched_at": (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat(),
    }
    result = get_usage_data()
    assert result is not None
    assert result["five_hour"]["utilization"] == 42

  @patch("claude_reset.main.is_fetch_locked", return_value=True)
  @patch("claude_reset.main.read_cache")
  @patch("claude_reset.main.is_cache_valid", return_value=False)
  def test_locked_returns_none_when_no_cache(
    self, mock_valid, mock_read_cache, mock_locked
  ):
    mock_read_cache.return_value = None
    result = get_usage_data()
    assert result is None
