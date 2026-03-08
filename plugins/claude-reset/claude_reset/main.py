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
from claude_reset.cache import read_cache, write_cache, is_cache_valid, has_expired_buckets
from claude_reset.renderer import render_compact_line, render_detail_lines
from claude_reset.stdin_context import parse_stdin_context, persist_context, load_persisted_context
from claude_reset.clock import get_session_elapsed
from claude_reset.git_info import get_git_info


CREDENTIALS_PATH = os.path.expanduser("~/.claude/.credentials.json")
CACHE_PATH = os.path.expanduser("~/.claude/claude-reset-cache.json")
STDIN_CTX_PATH = os.path.expanduser("~/.claude/claude-reset-stdin-ctx.json")
CLOCK_PATH = os.path.expanduser("~/.claude/claude-reset-session.json")


def _fallback_cache(cached):
  """Return cached usage data only if no buckets have expired."""
  if cached is None:
    return None
  usage_data = cached["usage_data"]
  if has_expired_buckets(usage_data):
    return None
  return usage_data


def get_usage_data():
  """Get usage data from cache or API. Returns usage dict or None on error."""
  cached = read_cache(CACHE_PATH)
  if cached is not None and is_cache_valid(cached):
    return cached["usage_data"]

  try:
    token_info = read_oauth_token(CREDENTIALS_PATH)
  except (FileNotFoundError, KeyError):
    return _fallback_cache(cached)

  access_token = token_info["access_token"]

  if token_info["is_expired"]:
    try:
      refreshed = refresh_oauth_token(token_info["refresh_token"])
      access_token = refreshed["access_token"]
    except Exception:
      return _fallback_cache(cached)

  try:
    usage_data = fetch_usage_data(access_token)
    write_cache(CACHE_PATH, usage_data)
    return usage_data
  except Exception:
    return _fallback_cache(cached)


def get_context_data():
  """Read context data from stdin and merge with persisted data."""
  raw_stdin = ""
  if not sys.stdin.isatty():
    try:
      raw_stdin = sys.stdin.read(65536)
    except Exception:
      pass

  stdin_ctx = parse_stdin_context(raw_stdin)

  if stdin_ctx:
    persist_context(stdin_ctx, STDIN_CTX_PATH)

  persisted = load_persisted_context(STDIN_CTX_PATH)
  if stdin_ctx:
    persisted.update(stdin_ctx)

  return persisted if persisted else None


def main():
  parser = argparse.ArgumentParser(description="Claude Code rate limit status")
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--compact", action="store_true", help="Single-line compact view")
  group.add_argument("--detail", action="store_true", help="Multi-line detailed view")
  args = parser.parse_args()

  context_data = get_context_data()
  usage_data = get_usage_data()
  elapsed = get_session_elapsed(CLOCK_PATH)
  git = get_git_info()
  cwd = os.getcwd()

  if usage_data is None:
    print("\033[2mNo usage data\033[0m")
    return

  if args.compact:
    print(render_compact_line(usage_data, context_data=context_data, elapsed=elapsed, git_info=git, cwd=cwd))
  else:
    for line in render_detail_lines(usage_data, context_data=context_data, elapsed=elapsed, git_info=git, cwd=cwd):
      print(line)


if __name__ == "__main__":
  main()
