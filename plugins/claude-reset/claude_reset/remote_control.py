"""Detect whether Claude Code remote control is active."""

import subprocess


def is_remote_control_active():
  """Check if a claude remote-control process is running.

  Returns dict with 'active' key (bool).
  """
  try:
    result = subprocess.run(
      ["pgrep", "-f", "claude remote-control"],
      capture_output=True,
      timeout=3,
    )
    return {"active": result.returncode == 0}
  except (subprocess.TimeoutExpired, OSError):
    return {"active": False}
