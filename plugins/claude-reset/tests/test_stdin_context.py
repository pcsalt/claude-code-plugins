import json
import os
import pytest
import tempfile
from claude_reset.stdin_context import (
  parse_stdin_context,
  persist_context,
  load_persisted_context,
)


class TestParseStdinContext:
  def test_parses_full_context_data(self):
    raw = json.dumps({
      "data": {
        "context_window": {
          "used_percentage": 42.5,
          "total_input_tokens": 85000,
          "total_output_tokens": 5000,
          "context_window_size": 200000,
        },
        "model": {
          "display_name": "Claude Opus 4.6",
          "id": "claude-opus-4-6",
        },
        "cost": {
          "total_cost_usd": 0.15,
        },
      }
    })
    result = parse_stdin_context(raw)
    # context_pct is recalculated from input tokens only: (85000/200000)*100 = 42.5
    assert result["context_pct"] == 42.5
    assert result["context_used"] == 85000
    assert result["context_limit"] == 200000
    assert result["output_tokens"] == 5000
    assert result["model_name"] == "Opus 4.6"
    assert result["cost_usd"] == 0.15

  def test_parses_flat_structure(self):
    """Handle JSON without 'data' wrapper."""
    raw = json.dumps({
      "context_window": {
        "used_percentage": 30.0,
        "total_input_tokens": 50000,
        "total_output_tokens": 10000,
        "context_window_size": 200000,
      },
    })
    result = parse_stdin_context(raw)
    # context_pct recalculated from input tokens: (50000/200000)*100 = 25.0
    assert result["context_pct"] == 25.0
    assert result["context_used"] == 50000
    assert result["output_tokens"] == 10000
    assert result["context_limit"] == 200000

  def test_parses_percentage_only(self):
    """When only used_percentage is provided, no token counts."""
    raw = json.dumps({
      "data": {
        "context_window": {
          "used_percentage": 55.0,
        },
      }
    })
    result = parse_stdin_context(raw)
    assert result["context_pct"] == 55.0
    assert "context_used" not in result
    assert "context_limit" not in result

  def test_empty_string_returns_empty_dict(self):
    assert parse_stdin_context("") == {}

  def test_none_returns_empty_dict(self):
    assert parse_stdin_context(None) == {}

  def test_whitespace_only_returns_empty_dict(self):
    assert parse_stdin_context("   ") == {}

  def test_invalid_json_returns_empty_dict(self):
    assert parse_stdin_context("not json{{{") == {}

  def test_no_context_window_returns_empty_dict(self):
    raw = json.dumps({"data": {"model": {"display_name": "Claude"}}})
    result = parse_stdin_context(raw)
    assert "context_pct" not in result
    assert "model_name" in result

  def test_model_name_strips_claude_prefix(self):
    raw = json.dumps({
      "data": {
        "model": {"display_name": "Claude Sonnet 4.6"},
      }
    })
    result = parse_stdin_context(raw)
    assert result["model_name"] == "Sonnet 4.6"

  def test_model_name_from_id_fallback(self):
    raw = json.dumps({
      "data": {
        "model": {"id": "claude-opus-4-6"},
      }
    })
    result = parse_stdin_context(raw)
    assert "model_name" in result

  def test_cost_parsed(self):
    raw = json.dumps({
      "data": {
        "cost": {"total_cost_usd": 1.23},
      }
    })
    result = parse_stdin_context(raw)
    assert result["cost_usd"] == 1.23


class TestPersistContext:
  def test_writes_and_reads_back(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      path = os.path.join(tmpdir, "ctx.json")
      data = {"context_pct": 42.5, "model_name": "Opus 4.6"}
      persist_context(data, path)
      loaded = load_persisted_context(path)
      assert loaded["context_pct"] == 42.5
      assert loaded["model_name"] == "Opus 4.6"

  def test_merges_with_existing(self):
    """New data should merge into existing, not replace it."""
    with tempfile.TemporaryDirectory() as tmpdir:
      path = os.path.join(tmpdir, "ctx.json")
      persist_context({"model_name": "Opus 4.6", "context_pct": 30.0}, path)
      persist_context({"context_pct": 50.0}, path)
      loaded = load_persisted_context(path)
      assert loaded["context_pct"] == 50.0
      assert loaded["model_name"] == "Opus 4.6"

  def test_empty_data_preserves_existing(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      path = os.path.join(tmpdir, "ctx.json")
      persist_context({"context_pct": 42.5}, path)
      persist_context({}, path)
      loaded = load_persisted_context(path)
      assert loaded["context_pct"] == 42.5

  def test_load_missing_file_returns_empty(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      path = os.path.join(tmpdir, "nonexistent.json")
      assert load_persisted_context(path) == {}

  def test_load_corrupted_file_returns_empty(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      path = os.path.join(tmpdir, "ctx.json")
      with open(path, "w") as f:
        f.write("not valid json")
      assert load_persisted_context(path) == {}

  def test_recalculates_context_pct_from_input_tokens_only(self):
    """When tokens are available, context_pct should be derived from input
    tokens only, not input+output, to avoid exceeding 100%."""
    raw = json.dumps({
      "data": {
        "context_window": {
          "used_percentage": 60.0,
          "total_input_tokens": 1000,
          "total_output_tokens": 500,
          "context_window_size": 200000,
        },
      }
    })
    result = parse_stdin_context(raw)
    # Should be recalculated from input only: (1000/200000)*100 = 0.5, not 60.0
    assert result["context_pct"] == pytest.approx(0.5)
    assert result["context_used"] == 1000
    assert result["output_tokens"] == 500
    assert result["context_limit"] == 200000

  def test_output_tokens_stored_separately(self):
    """Output tokens should be stored as a separate field, not added to context_used."""
    raw = json.dumps({
      "data": {
        "context_window": {
          "total_input_tokens": 160000,
          "total_output_tokens": 50000,
          "context_window_size": 200000,
        },
      }
    })
    result = parse_stdin_context(raw)
    assert result["context_used"] == 160000
    assert result["output_tokens"] == 50000
    assert result["context_pct"] == pytest.approx(80.0)

  def test_no_output_tokens_field_when_missing(self):
    """When output tokens are not in stdin, output_tokens should not be in result."""
    raw = json.dumps({
      "data": {
        "context_window": {
          "total_input_tokens": 50000,
          "context_window_size": 200000,
        },
      }
    })
    result = parse_stdin_context(raw)
    assert result["context_used"] == 50000
    assert "output_tokens" not in result

  def test_only_persists_known_keys(self):
    """Unknown keys should not be persisted."""
    with tempfile.TemporaryDirectory() as tmpdir:
      path = os.path.join(tmpdir, "ctx.json")
      persist_context({"context_pct": 42.5, "unknown_key": "value"}, path)
      loaded = load_persisted_context(path)
      assert "unknown_key" not in loaded
