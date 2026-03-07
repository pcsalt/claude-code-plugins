import json
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from claude_reset.api import (
  read_oauth_token,
  fetch_usage_data,
  refresh_oauth_token,
  USAGE_API_URL,
  TOKEN_REFRESH_URL,
  OAUTH_BETA_HEADER,
)


@pytest.fixture
def credentials_dir():
  with tempfile.TemporaryDirectory() as tmpdir:
    yield tmpdir


@pytest.fixture
def valid_credentials(credentials_dir):
  creds = {
    "claudeAiOauth": {
      "accessToken": "test-access-token-123",
      "refreshToken": "test-refresh-token-456",
      "expiresAt": 9999999999000,
      "rateLimitTier": "default_claude_max_5x",
      "scopes": ["user:profile", "user:inference"],
    }
  }
  creds_path = os.path.join(credentials_dir, ".credentials.json")
  with open(creds_path, "w") as f:
    json.dump(creds, f)
  return creds_path


@pytest.fixture
def expired_credentials(credentials_dir):
  creds = {
    "claudeAiOauth": {
      "accessToken": "expired-token",
      "refreshToken": "test-refresh-token-456",
      "expiresAt": 1000000000000,  # far in the past
      "rateLimitTier": "default_claude_max_5x",
      "scopes": ["user:profile", "user:inference"],
    }
  }
  creds_path = os.path.join(credentials_dir, ".credentials.json")
  with open(creds_path, "w") as f:
    json.dump(creds, f)
  return creds_path


class TestReadOAuthToken:
  def test_reads_valid_token(self, valid_credentials):
    token_info = read_oauth_token(valid_credentials)
    assert token_info["access_token"] == "test-access-token-123"
    assert token_info["refresh_token"] == "test-refresh-token-456"

  @patch("claude_reset.api.subprocess")
  def test_missing_file_and_no_keychain_raises(self, mock_subprocess):
    mock_subprocess.run.return_value = MagicMock(returncode=1, stdout="")
    with pytest.raises(FileNotFoundError):
      read_oauth_token("/nonexistent/path/.credentials.json")

  @patch("claude_reset.api.subprocess")
  def test_missing_oauth_key_falls_to_keychain(self, mock_subprocess, credentials_dir):
    creds_path = os.path.join(credentials_dir, ".credentials.json")
    with open(creds_path, "w") as f:
      json.dump({"someOtherKey": {}}, f)
    mock_subprocess.run.return_value = MagicMock(returncode=1, stdout="")
    with pytest.raises(FileNotFoundError):
      read_oauth_token(creds_path)

  @patch("claude_reset.api.subprocess")
  def test_malformed_json_falls_to_keychain(self, mock_subprocess, credentials_dir):
    creds_path = os.path.join(credentials_dir, ".credentials.json")
    with open(creds_path, "w") as f:
      f.write("not json{{{")
    mock_subprocess.run.return_value = MagicMock(returncode=1, stdout="")
    with pytest.raises(FileNotFoundError):
      read_oauth_token(creds_path)

  def test_detects_expired_token(self, expired_credentials):
    token_info = read_oauth_token(expired_credentials)
    assert token_info["is_expired"] is True

  def test_detects_valid_token(self, valid_credentials):
    token_info = read_oauth_token(valid_credentials)
    assert token_info["is_expired"] is False

  def test_extracts_rate_limit_tier(self, valid_credentials):
    token_info = read_oauth_token(valid_credentials)
    assert token_info["rate_limit_tier"] == "default_claude_max_5x"


class TestFetchUsageData:
  @patch("claude_reset.api.urlopen")
  def test_successful_fetch(self, mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
      "five_hour": {"utilization": 42, "resets_at": "2026-03-07T16:00:00Z"},
      "seven_day": {"utilization": 35, "resets_at": "2026-03-10T18:00:00Z"},
    }).encode()
    mock_response.status = 200
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response

    result = fetch_usage_data("test-token")
    assert result["five_hour"]["utilization"] == 42

  @patch("claude_reset.api.urlopen")
  def test_sends_correct_headers(self, mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"five_hour": {}}'
    mock_response.status = 200
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response

    fetch_usage_data("my-token")

    call_args = mock_urlopen.call_args
    request = call_args[0][0]
    assert request.get_header("Authorization") == "Bearer my-token"
    assert request.get_header("Anthropic-beta") == OAUTH_BETA_HEADER

  @patch("claude_reset.api.urlopen")
  def test_api_error_raises(self, mock_urlopen):
    from urllib.error import HTTPError
    mock_urlopen.side_effect = HTTPError(
      url=USAGE_API_URL, code=401, msg="Unauthorized", hdrs={}, fp=None
    )
    with pytest.raises(HTTPError):
      fetch_usage_data("bad-token")

  @patch("claude_reset.api.urlopen")
  def test_network_error_raises(self, mock_urlopen):
    from urllib.error import URLError
    mock_urlopen.side_effect = URLError("Network unreachable")
    with pytest.raises(URLError):
      fetch_usage_data("any-token")


class TestRefreshOAuthToken:
  @patch("claude_reset.api.urlopen")
  def test_successful_refresh(self, mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
      "access_token": "new-access-token",
      "refresh_token": "new-refresh-token",
      "expires_in": 3600,
    }).encode()
    mock_response.status = 200
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response

    result = refresh_oauth_token("old-refresh-token")
    assert result["access_token"] == "new-access-token"

  @patch("claude_reset.api.urlopen")
  def test_refresh_failure_raises(self, mock_urlopen):
    from urllib.error import HTTPError
    mock_urlopen.side_effect = HTTPError(
      url=TOKEN_REFRESH_URL, code=400, msg="Bad Request", hdrs={}, fp=None
    )
    with pytest.raises(HTTPError):
      refresh_oauth_token("invalid-refresh-token")
