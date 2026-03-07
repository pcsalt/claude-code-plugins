#!/usr/bin/env python3
"""Claude Log hook — logs tool usage to .claude/session-log.md.

Configure as a PostToolUse hook in ~/.claude/settings.json:
  {
    "hooks": {
      "PostToolUse": [{
        "type": "command",
        "command": "PYTHONPATH=~/.claude-code-plugins/plugins/claude-log python3 -m claude_log.hook"
      }]
    }
  }
"""

import sys
from datetime import datetime, timezone

from claude_log.logger import parse_hook_input, format_log_entry, append_log_entry, get_log_path


def main():
  raw_stdin = ""
  if not sys.stdin.isatty():
    try:
      raw_stdin = sys.stdin.read(65536)
    except Exception:
      return

  entry = parse_hook_input(raw_stdin)
  if entry is None:
    return

  timestamp = datetime.now(timezone.utc).isoformat()
  formatted = format_log_entry(entry, timestamp)
  log_path = get_log_path(None)

  try:
    append_log_entry(log_path, formatted)
  except OSError:
    pass


if __name__ == "__main__":
  main()
