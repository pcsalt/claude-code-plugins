import pytest
from unittest.mock import patch, MagicMock
from claude_reset.git_info import (
  get_git_info,
  format_git_compact,
  format_git_detail,
)


def _mock_run(results):
  """Create a mock for subprocess.run that returns different results per call."""
  side_effects = []
  for stdout, returncode in results:
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    side_effects.append(mock)
  return side_effects


class TestGetGitInfo:
  @patch("claude_reset.git_info.subprocess.run")
  def test_returns_branch_and_changes(self, mock_run):
    mock_run.side_effect = _mock_run([
      ("feat/context\n", 0),       # branch
      (" M file1.py\n?? file2.py\n", 0),  # status
      ("1\t2\n", 0),               # behind/ahead
    ])
    info = get_git_info()
    assert info["branch"] == "feat/context"
    assert info["changes"] == 2
    assert info["ahead"] == 2
    assert info["behind"] == 1

  @patch("claude_reset.git_info.subprocess.run")
  def test_no_upstream(self, mock_run):
    mock_run.side_effect = _mock_run([
      ("main\n", 0),
      ("", 0),
      ("", 128),  # no upstream
    ])
    info = get_git_info()
    assert info["branch"] == "main"
    assert info["changes"] == 0
    assert info["ahead"] == 0
    assert info["behind"] == 0

  @patch("claude_reset.git_info.subprocess.run")
  def test_not_a_git_repo(self, mock_run):
    mock_run.side_effect = _mock_run([
      ("", 128),
    ])
    info = get_git_info()
    assert info is None

  @patch("claude_reset.git_info.subprocess.run")
  def test_detached_head(self, mock_run):
    mock_run.side_effect = _mock_run([
      ("HEAD\n", 0),
      ("", 0),
      ("", 128),
    ])
    info = get_git_info()
    assert info["branch"] == "HEAD"

  @patch("claude_reset.git_info.subprocess.run")
  def test_only_modified_files(self, mock_run):
    mock_run.side_effect = _mock_run([
      ("main\n", 0),
      (" M a.py\nM  b.py\nMM c.py\n", 0),
      ("0\t0\n", 0),
    ])
    info = get_git_info()
    assert info["changes"] == 3


class TestFormatGitCompact:
  def test_basic_format(self):
    info = {"branch": "main", "changes": 0, "ahead": 0, "behind": 0}
    result = format_git_compact(info)
    assert "main" in result

  def test_with_changes(self):
    info = {"branch": "feat/x", "changes": 3, "ahead": 0, "behind": 0}
    result = format_git_compact(info)
    assert "3" in result

  def test_with_ahead(self):
    info = {"branch": "main", "changes": 0, "ahead": 2, "behind": 0}
    result = format_git_compact(info)
    assert "2" in result

  def test_with_behind(self):
    info = {"branch": "main", "changes": 0, "ahead": 0, "behind": 1}
    result = format_git_compact(info)
    assert "1" in result

  def test_none_returns_empty(self):
    assert format_git_compact(None) == ""


class TestFormatGitDetail:
  def test_basic_format(self):
    info = {"branch": "main", "changes": 0, "ahead": 0, "behind": 0}
    result = format_git_detail(info)
    assert "main" in result

  def test_with_changes_and_ahead(self):
    info = {"branch": "feat/y", "changes": 2, "ahead": 1, "behind": 0}
    result = format_git_detail(info)
    assert "feat/y" in result
    assert "2" in result
    assert "1" in result

  def test_none_returns_empty(self):
    assert format_git_detail(None) == ""
