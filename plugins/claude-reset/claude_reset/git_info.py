"""Git info — shows branch, changes, CWD, and ahead/behind in status line."""

import os
import subprocess

ANSI_DIM = "\033[2m"
ANSI_RESET = "\033[0m"


def _run_git(args):
  """Run a git command and return (stdout, returncode)."""
  try:
    result = subprocess.run(
      ["git"] + args,
      capture_output=True, text=True, timeout=5,
    )
    return result.stdout.strip(), result.returncode
  except (subprocess.TimeoutExpired, OSError):
    return "", 128


def get_git_info():
  """Get current git branch, change count, and ahead/behind.

  Returns dict with branch, changes, ahead, behind. Returns None if not in a git repo.
  """
  branch_out, rc = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
  if rc != 0:
    return None

  branch = branch_out or "HEAD"

  status_out, _ = _run_git(["status", "--porcelain"])
  changes = len([l for l in status_out.splitlines() if l.strip()]) if status_out else 0

  ahead = 0
  behind = 0
  revlist_out, rc = _run_git(["rev-list", "--count", "--left-right", "@{u}...HEAD"])
  if rc == 0 and revlist_out:
    parts = revlist_out.split("\t")
    if len(parts) == 2:
      behind = int(parts[0])
      ahead = int(parts[1])

  return {
    "branch": branch,
    "changes": changes,
    "ahead": ahead,
    "behind": behind,
  }


MAX_PATH_LEN = 65


def shorten_path(path):
  """Shorten a path by replacing home with ~ and truncating intermediate segments.

  Intermediate segments are shortened to 3 chars, last segment kept full.
  If the result with ~ substitution fits within MAX_PATH_LEN, returns as-is.
  """
  home = os.path.expanduser("~")
  if path.startswith(home):
    path = "~" + path[len(home):]

  if len(path) <= MAX_PATH_LEN:
    return path

  parts = path.split(os.sep)
  if len(parts) <= 2:
    return path

  # Shorten all intermediate segments (keep first and last)
  shortened = [parts[0]]
  for segment in parts[1:-1]:
    shortened.append(segment[:3])
  shortened.append(parts[-1])

  return os.sep.join(shortened)


def _format_git_indicators(info):
  """Build git status indicators (ahead/behind/changes)."""
  indicators = []
  if info["ahead"] > 0:
    indicators.append(f"{info['ahead']}\u2191")
  if info["behind"] > 0:
    indicators.append(f"{info['behind']}\u2193")
  if info["changes"] > 0:
    indicators.append(f"{info['changes']}\u270e")
  return " ".join(indicators)


def format_git_compact(info, cwd=None):
  """Format CWD + git info for compact view."""
  parts = []

  if cwd:
    parts.append(f"\U0001f4c2 {shorten_path(cwd)}")

  if info is not None:
    parts.append(info["branch"])
    indicators = _format_git_indicators(info)
    if indicators:
      parts.append(indicators)
  elif not cwd:
    return ""

  return " ".join(parts)


def format_git_detail(info, cwd=None):
  """Format CWD + git info for detail view."""
  parts = []

  if cwd:
    parts.append(shorten_path(cwd))

  if info is not None:
    parts.append(info["branch"])
    indicators = _format_git_indicators(info)
    if indicators:
      parts.append(indicators)
  elif not cwd:
    return ""

  return f"\U0001f4c2 {'  '.join(parts)}"
