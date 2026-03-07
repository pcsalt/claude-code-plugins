import json
import os
import pytest
import tempfile
from claude_log.logger import (
  parse_hook_input,
  format_log_entry,
  append_log_entry,
  get_log_path,
)


class TestParseHookInput:
  def test_parses_edit_tool(self):
    raw = json.dumps({
      "tool_name": "Edit",
      "tool_input": {
        "file_path": "/src/app.py",
        "old_string": "foo",
        "new_string": "bar",
      },
    })
    result = parse_hook_input(raw)
    assert result["tool"] == "Edit"
    assert result["file"] == "/src/app.py"

  def test_parses_write_tool(self):
    raw = json.dumps({
      "tool_name": "Write",
      "tool_input": {
        "file_path": "/src/new_file.py",
        "content": "print('hello')",
      },
    })
    result = parse_hook_input(raw)
    assert result["tool"] == "Write"
    assert result["file"] == "/src/new_file.py"

  def test_parses_read_tool(self):
    raw = json.dumps({
      "tool_name": "Read",
      "tool_input": {
        "file_path": "/src/utils.py",
      },
    })
    result = parse_hook_input(raw)
    assert result["tool"] == "Read"
    assert result["file"] == "/src/utils.py"

  def test_parses_bash_tool(self):
    raw = json.dumps({
      "tool_name": "Bash",
      "tool_input": {
        "command": "git commit -m 'fix bug'",
      },
    })
    result = parse_hook_input(raw)
    assert result["tool"] == "Bash"
    assert result["command"] == "git commit -m 'fix bug'"

  def test_parses_grep_tool(self):
    raw = json.dumps({
      "tool_name": "Grep",
      "tool_input": {
        "pattern": "def main",
        "path": "/src",
      },
    })
    result = parse_hook_input(raw)
    assert result["tool"] == "Grep"
    assert result["pattern"] == "def main"

  def test_parses_glob_tool(self):
    raw = json.dumps({
      "tool_name": "Glob",
      "tool_input": {
        "pattern": "**/*.py",
      },
    })
    result = parse_hook_input(raw)
    assert result["tool"] == "Glob"
    assert result["pattern"] == "**/*.py"

  def test_unknown_tool(self):
    raw = json.dumps({
      "tool_name": "SomeOtherTool",
      "tool_input": {"key": "value"},
    })
    result = parse_hook_input(raw)
    assert result["tool"] == "SomeOtherTool"

  def test_empty_input(self):
    assert parse_hook_input("") is None

  def test_invalid_json(self):
    assert parse_hook_input("not json{") is None

  def test_missing_tool_name(self):
    raw = json.dumps({"tool_input": {}})
    assert parse_hook_input(raw) is None


class TestFormatLogEntry:
  def test_edit_entry(self):
    entry = {"tool": "Edit", "file": "/src/app.py"}
    result = format_log_entry(entry, "2026-03-08T10:30:00")
    assert "10:30:00" in result
    assert "Edit" in result
    assert "/src/app.py" in result

  def test_bash_entry(self):
    entry = {"tool": "Bash", "command": "git status"}
    result = format_log_entry(entry, "2026-03-08T10:30:00")
    assert "Bash" in result
    assert "git status" in result

  def test_grep_entry(self):
    entry = {"tool": "Grep", "pattern": "TODO"}
    result = format_log_entry(entry, "2026-03-08T10:30:00")
    assert "Grep" in result
    assert "TODO" in result

  def test_unknown_tool_entry(self):
    entry = {"tool": "WebSearch"}
    result = format_log_entry(entry, "2026-03-08T10:30:00")
    assert "WebSearch" in result

  def test_long_command_truncated(self):
    entry = {"tool": "Bash", "command": "x" * 200}
    result = format_log_entry(entry, "2026-03-08T10:30:00")
    assert len(result) < 250


class TestAppendLogEntry:
  def test_creates_file_if_missing(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      log_path = os.path.join(tmpdir, "session-log.md")
      append_log_entry(log_path, "- 10:30:00 | Edit | /src/app.py")
      assert os.path.exists(log_path)
      with open(log_path) as f:
        content = f.read()
      assert "Edit" in content

  def test_appends_to_existing(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      log_path = os.path.join(tmpdir, "session-log.md")
      append_log_entry(log_path, "- 10:30:00 | Edit | file1.py")
      append_log_entry(log_path, "- 10:31:00 | Write | file2.py")
      with open(log_path) as f:
        content = f.read()
      assert "file1.py" in content
      assert "file2.py" in content

  def test_adds_date_header_for_new_file(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      log_path = os.path.join(tmpdir, "session-log.md")
      append_log_entry(log_path, "- 10:30:00 | Edit | file.py")
      with open(log_path) as f:
        content = f.read()
      assert content.startswith("## ")


class TestGetLogPath:
  def test_returns_path_in_project_dir(self):
    path = get_log_path("/home/user/project")
    assert path == "/home/user/project/.claude/session-log.md"

  def test_uses_cwd_when_none(self):
    path = get_log_path(None)
    assert path.endswith(".claude/session-log.md")
