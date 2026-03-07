"""Git info — shows branch, changes, and ahead/behind in status line."""

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


def format_git_compact(info):
  """Format git info for compact view."""
  if info is None:
    return ""

  parts = [f"\U0001f500 {info['branch']}"]
  indicators = []
  if info["ahead"] > 0:
    indicators.append(f"{info['ahead']}\u2191")
  if info["behind"] > 0:
    indicators.append(f"{info['behind']}\u2193")
  if info["changes"] > 0:
    indicators.append(f"{info['changes']}\u270e")
  if indicators:
    parts.append(" ".join(indicators))

  return " ".join(parts)


def format_git_detail(info):
  """Format git info for detail view."""
  if info is None:
    return ""

  label = f"\U0001f500 Git      {info['branch']}"
  indicators = []
  if info["ahead"] > 0:
    indicators.append(f"{info['ahead']}\u2191")
  if info["behind"] > 0:
    indicators.append(f"{info['behind']}\u2193")
  if info["changes"] > 0:
    indicators.append(f"{info['changes']}\u270e")
  if indicators:
    label += f"  {' '.join(indicators)}"

  return label
