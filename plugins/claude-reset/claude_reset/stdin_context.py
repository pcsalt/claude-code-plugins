"""Parse and persist context window data from Claude Code's stdin JSON."""

import json
import os

_KNOWN_KEYS = {"model_name", "context_pct", "context_used", "context_limit", "cost_usd"}


def parse_stdin_context(raw_stdin):
  """Parse Claude Code's stdin JSON for session context.

  Extracts model name, context window usage, and cost.
  Returns dict with available keys, or empty dict on error.
  """
  if not raw_stdin or not raw_stdin.strip():
    return {}
  try:
    data = json.loads(raw_stdin)
  except (json.JSONDecodeError, TypeError):
    return {}

  result = {}

  # Model name
  try:
    model = data.get("data", data).get("model", {})
    display_name = model.get("display_name", "")
    if display_name:
      short = display_name.replace("Claude ", "").strip()
      result["model_name"] = short if short else display_name
    else:
      model_id = model.get("id", "")
      if model_id:
        result["model_name"] = model_id.split("-")[-1].title()
  except (AttributeError, KeyError):
    pass

  # Context window usage
  try:
    ctx = data.get("data", data).get("context_window", {})
    used_pct = ctx.get("used_percentage")
    if used_pct is not None:
      result["context_pct"] = float(used_pct)
    input_tok = ctx.get("total_input_tokens")
    output_tok = ctx.get("total_output_tokens")
    ctx_size = ctx.get("context_window_size")
    if input_tok is not None and ctx_size is not None:
      result["context_used"] = int(input_tok) + int(output_tok or 0)
      result["context_limit"] = int(ctx_size)
  except (AttributeError, KeyError, ValueError, TypeError):
    pass

  # Cost
  try:
    cost = data.get("data", data).get("cost", {})
    total = cost.get("total_cost_usd")
    if total is not None:
      result["cost_usd"] = float(total)
  except (AttributeError, KeyError, ValueError, TypeError):
    pass

  # Recalculate context_pct from tokens only when API didn't provide used_percentage
  if "context_pct" not in result and "context_used" in result and "context_limit" in result and result["context_limit"] > 0:
    result["context_pct"] = (result["context_used"] / result["context_limit"]) * 100

  return result


def load_persisted_context(path):
  """Load persisted context from file. Returns empty dict on error."""
  try:
    with open(path, "r", encoding="utf-8") as f:
      data = json.load(f)
      return {k: v for k, v in data.items() if k in _KNOWN_KEYS}
  except (FileNotFoundError, json.JSONDecodeError, OSError):
    return {}


def persist_context(data, path):
  """Merge new context data into persisted file.

  Only known keys are persisted. New data merges into existing,
  so partial updates don't wipe previously known fields.
  """
  existing = load_persisted_context(path)
  filtered = {k: v for k, v in data.items() if k in _KNOWN_KEYS}
  if filtered:
    existing.update(filtered)
  with open(path, "w", encoding="utf-8") as f:
    json.dump(existing, f)
