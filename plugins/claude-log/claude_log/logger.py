"""Claude Log — hook-based session activity logger for Claude Code."""

import json
import os
from datetime import datetime, timezone

MAX_COMMAND_LENGTH = 120


def parse_hook_input(raw_stdin):
  """Parse Claude Code hook JSON input.

  Returns dict with tool info, or None if input is invalid.
  """
  if not raw_stdin or not raw_stdin.strip():
    return None

  try:
    data = json.loads(raw_stdin)
  except (json.JSONDecodeError, TypeError):
    return None

  tool_name = data.get("tool_name")
  if not tool_name:
    return None

  tool_input = data.get("tool_input", {})
  result = {"tool": tool_name}

  if tool_name in ("Edit", "Write", "Read"):
    file_path = tool_input.get("file_path", "")
    if file_path:
      result["file"] = file_path

  elif tool_name == "Bash":
    command = tool_input.get("command", "")
    if command:
      result["command"] = command

  elif tool_name in ("Grep", "Glob"):
    pattern = tool_input.get("pattern", "")
    if pattern:
      result["pattern"] = pattern
    path = tool_input.get("path", "")
    if path:
      result["path"] = path

  return result


def format_log_entry(entry, timestamp):
  """Format a parsed hook entry as a markdown log line."""
  tool = entry.get("tool", "Unknown")
  time_part = timestamp.split("T")[-1] if "T" in timestamp else timestamp

  if "file" in entry:
    return f"- `{time_part}` | **{tool}** | `{entry['file']}`"

  if "command" in entry:
    cmd = entry["command"]
    if len(cmd) > MAX_COMMAND_LENGTH:
      cmd = cmd[:MAX_COMMAND_LENGTH] + "..."
    return f"- `{time_part}` | **{tool}** | `{cmd}`"

  if "pattern" in entry:
    detail = entry["pattern"]
    if "path" in entry:
      detail += f" in {entry['path']}"
    return f"- `{time_part}` | **{tool}** | `{detail}`"

  return f"- `{time_part}` | **{tool}**"


def append_log_entry(log_path, formatted_entry):
  """Append a formatted log entry to the session log file.

  Creates the file with a date header if it doesn't exist.
  """
  os.makedirs(os.path.dirname(log_path), exist_ok=True)

  is_new = not os.path.exists(log_path)
  with open(log_path, "a", encoding="utf-8") as f:
    if is_new:
      date_str = datetime.now().strftime("%Y-%m-%d")
      f.write(f"## {date_str}\n\n")
    f.write(formatted_entry + "\n")


def get_log_path(project_dir):
  """Get the session log file path for a project directory."""
  if project_dir is None:
    project_dir = os.getcwd()
  return os.path.join(project_dir, ".claude", "session-log.md")
