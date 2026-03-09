import json
import subprocess
import sys
import time
from urllib.request import Request, urlopen


class RateLimitError(Exception):
  """Raised when the API returns 429 Too Many Requests."""
  pass


USAGE_API_URL = "https://api.anthropic.com/api/oauth/usage"
TOKEN_REFRESH_URL = "https://console.anthropic.com/v1/oauth/token"
OAUTH_BETA_HEADER = "oauth-2025-04-20"
KEYCHAIN_SERVICE = "Claude Code-credentials"


def _read_credentials_raw(credentials_path):
  """Read raw credentials dict from file or macOS Keychain."""
  # 1. File-based
  try:
    with open(credentials_path) as f:
      data = json.load(f)
    if data.get("claudeAiOauth", {}).get("accessToken"):
      return data
  except (FileNotFoundError, json.JSONDecodeError, KeyError):
    pass

  # 2. macOS Keychain fallback
  if sys.platform == "darwin":
    try:
      result = subprocess.run(
        ["/usr/bin/security", "find-generic-password",
         "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True, timeout=5,
      )
      if result.returncode == 0 and result.stdout.strip():
        data = json.loads(result.stdout.strip())
        if data.get("claudeAiOauth", {}).get("accessToken"):
          return data
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
      pass

  raise FileNotFoundError("No credentials found in file or Keychain")


def read_oauth_token(credentials_path):
  """Read OAuth token info from Claude Code credentials file or Keychain.

  Returns dict with access_token, refresh_token, is_expired, rate_limit_tier.
  Raises FileNotFoundError if not found, KeyError if structure invalid.
  """
  creds = _read_credentials_raw(credentials_path)

  oauth_data = creds["claudeAiOauth"]
  expires_at_ms = oauth_data.get("expiresAt", 0)
  now_ms = int(time.time() * 1000)

  return {
    "access_token": oauth_data["accessToken"],
    "refresh_token": oauth_data["refreshToken"],
    "is_expired": now_ms >= expires_at_ms,
    "rate_limit_tier": oauth_data.get("rateLimitTier", "unknown"),
  }


def fetch_usage_data(access_token):
  """Fetch usage/rate limit data from Anthropic OAuth usage API.

  Returns parsed JSON response dict.
  Raises RateLimitError on 429, HTTPError on other API errors, URLError on network errors.
  """
  from urllib.error import HTTPError

  request = Request(USAGE_API_URL)
  request.add_header("Authorization", f"Bearer {access_token}")
  request.add_header("Anthropic-beta", OAUTH_BETA_HEADER)
  request.add_header("Accept", "application/json")

  try:
    with urlopen(request) as response:
      return json.loads(response.read())
  except HTTPError as e:
    if e.code == 429:
      raise RateLimitError("Rate limited by API") from e
    raise


def refresh_oauth_token(refresh_token):
  """Refresh an expired OAuth token.

  Returns dict with access_token, refresh_token, expires_in.
  Raises HTTPError on failure.
  """
  body = json.dumps({
    "grant_type": "refresh_token",
    "refresh_token": refresh_token,
  }).encode()

  request = Request(TOKEN_REFRESH_URL, data=body)
  request.add_header("Content-Type", "application/json")

  with urlopen(request) as response:
    return json.loads(response.read())
