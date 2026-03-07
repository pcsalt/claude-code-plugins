#!/usr/bin/env python3
"""Claude Reset — Claude Code status line plugin for rate limit display.

Usage:
  As status line (compact):  python3 main.py --compact
  As status line (detail):   python3 main.py --detail
  Default:                   python3 main.py (same as --detail)

Configure in ~/.claude/settings.json:
  {
    "statusLine": {
      "type": "command",
      "command": "python3 /path/to/claude_reset/main.py --compact"
    }
  }
"""

import os
import sys
import argparse

from claude_reset.api import read_oauth_token, fetch_usage_data, refresh_oauth_token
from claude_reset.cache import read_cache, write_cache, is_cache_valid
from claude_reset.renderer import render_compact_line, render_detail_lines


CREDENTIALS_PATH = os.path.expanduser("~/.claude/.credentials.json")
CACHE_PATH = os.path.expanduser("~/.claude/claude-reset-cache.json")


def get_usage_data():
  """Get usage data from cache or API. Returns usage dict or None on error."""
  cached = read_cache(CACHE_PATH)
  if cached is not None and is_cache_valid(cached):
    return cached["usage_data"]

  try:
    token_info = read_oauth_token(CREDENTIALS_PATH)
  except (FileNotFoundError, KeyError):
    if cached is not None:
      return cached["usage_data"]
    return None

  access_token = token_info["access_token"]

  if token_info["is_expired"]:
    try:
      refreshed = refresh_oauth_token(token_info["refresh_token"])
      access_token = refreshed["access_token"]
    except Exception:
      if cached is not None:
        return cached["usage_data"]
      return None

  try:
    usage_data = fetch_usage_data(access_token)
    write_cache(CACHE_PATH, usage_data)
    return usage_data
  except Exception:
    if cached is not None:
      return cached["usage_data"]
    return None


def main():
  parser = argparse.ArgumentParser(description="Claude Code rate limit status")
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--compact", action="store_true", help="Single-line compact view")
  group.add_argument("--detail", action="store_true", help="Multi-line detailed view")
  args = parser.parse_args()

  usage_data = get_usage_data()
  if usage_data is None:
    print("\033[2mNo usage data\033[0m")
    return

  if args.compact:
    print(render_compact_line(usage_data))
  else:
    for line in render_detail_lines(usage_data):
      print(line)


if __name__ == "__main__":
  main()
