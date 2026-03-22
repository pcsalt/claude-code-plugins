import subprocess
from unittest.mock import patch
from claude_reset.remote_control import is_remote_control_active


class TestIsRemoteControlActive:
  @patch("claude_reset.remote_control.subprocess.run")
  def test_active_when_process_found(self, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    result = is_remote_control_active()
    assert result == {"active": True}

  @patch("claude_reset.remote_control.subprocess.run")
  def test_inactive_when_no_process(self, mock_run):
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
    result = is_remote_control_active()
    assert result == {"active": False}

  @patch("claude_reset.remote_control.subprocess.run")
  def test_inactive_on_timeout(self, mock_run):
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="pgrep", timeout=3)
    result = is_remote_control_active()
    assert result == {"active": False}

  @patch("claude_reset.remote_control.subprocess.run")
  def test_inactive_on_os_error(self, mock_run):
    mock_run.side_effect = OSError("pgrep not found")
    result = is_remote_control_active()
    assert result == {"active": False}
