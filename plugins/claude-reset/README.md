# claude-reset

A lightweight Claude Code status line plugin that displays rate limits, context window, git status, and session clock.

## What it shows

- **Context window** — current conversation's context usage with token counts (no API call — read from Claude Code's stdin)
- **Session (5h)** — utilization bar + countdown + local reset time
- **Weekly (7d)** — all models combined
- **Opus / Sonnet** — model-specific weekly limits (shown only when available)
- **Overage** — monthly spend vs budget
- **Elapsed** — how long the current coding session has been active (see [Session clock](#session-clock) below)
- **Git** — current branch, modified file count, ahead/behind remote

## Views

### Detail view (multi-line)

```
📐 Context  [▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱]  42%  85k/200k
⚡ Session  [▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱]  42%  ↻ 2h 15m (14:30)
📅 Weekly   [▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱]  35%  ↻ 3d 4h (Wed 18:00)
🔮 Opus     [▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱]  28%  ↻ 3d 4h (Wed 18:00)
✨ Sonnet   [▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱]  12%  ↻ 3d 4h (Wed 18:00)
💰 Overage  [▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱]  $15.82 / $50.00
🕑 Elapsed  1h 23m
🔀 Git      feat/context  2↑ 3✎
```

### Compact view (single line)

```
📐 ▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱ 42% │ ⚡ ▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱ 42% 2h15m │ 📅 ... │ 🕑 1h23m │ 🔀 feat/context 2↑ 3✎
```

### Color coding

- Green — below 70%
- Yellow — 70% to 89%
- Red — 90% and above

## Installation

### 1. Clone the marketplace repo

```bash
git clone https://github.com/pcsalt/claude-code-plugins.git ~/.claude-code-plugins
```

### 2. Add to Claude Code settings

Edit `~/.claude/settings.json` and add the `statusLine` block:

**Detail view (recommended):**

```json
{
  "statusLine": {
    "type": "command",
    "command": "PYTHONPATH=~/.claude-code-plugins/plugins/claude-reset python3 -m claude_reset.main --detail"
  }
}
```

**Compact view:**

```json
{
  "statusLine": {
    "type": "command",
    "command": "PYTHONPATH=~/.claude-code-plugins/plugins/claude-reset python3 -m claude_reset.main --compact"
  }
}
```

### 3. Restart Claude Code

The status line will appear after the next assistant message.

## How it works

**Context window** (no API call):
1. Claude Code pipes session JSON to the status line command via stdin
2. Parses `context_window.used_percentage` and token counts from stdin
3. Persists context data to `~/.claude/claude-reset-stdin-ctx.json` so it survives refreshes

**Rate limits** (smart caching):
1. Reads your OAuth token from `~/.claude/.credentials.json` or macOS Keychain
2. Calls `https://api.anthropic.com/api/oauth/usage` to fetch rate limit data
3. Caches the response locally at `~/.claude/claude-reset-cache.json`
4. On subsequent runs, serves from cache if no reset window has expired
5. Only makes a new API call when a `resets_at` timestamp is in the past

### Session clock

The elapsed timer tracks how long you've been working in Claude Code. No API call — purely local.

- The **first time** the status line runs in a session, it records the current time to `~/.claude/claude-reset-session.json`
- On **every subsequent refresh**, it calculates the difference and displays it (e.g., `23m`, `1h 15m`, `3h 45m`)
- If the last recorded start time is **older than 24 hours**, the clock treats it as a stale session and **automatically resets** — it writes a new start time and the timer restarts from `< 1m`
- The clock **persists across conversation restarts** within the same day. If you close Claude Code and reopen it a few hours later, the timer continues from where it was (since the start time is on disk)
- To **manually reset** the clock, delete the file: `rm ~/.claude/claude-reset-session.json`

### Git status

No API call — runs local `git` commands only.

1. `git rev-parse --abbrev-ref HEAD` — current branch name
2. `git status --porcelain` — count of modified/untracked files (shown as `3✎`)
3. `git rev-list --count --left-right @{u}...HEAD` — commits ahead/behind remote (shown as `2↑ 1↓`)
4. If not inside a git repo, the git line is hidden

**Zero polling. Zero unnecessary API calls.**

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)
- Claude Code with an active session (Pro / Max plan)

## Running tests

```bash
cd ~/.claude-code-plugins
python3 -m venv .venv && source .venv/bin/activate
pip install pytest
PYTHONPATH=plugins/claude-reset pytest plugins/claude-reset/tests/ -v
```

## Running standalone

You can also run it directly in your terminal:

```bash
PYTHONPATH=~/.claude-code-plugins/plugins/claude-reset python3 -m claude_reset.main --detail
```
