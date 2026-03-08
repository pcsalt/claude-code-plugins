# Claude Code Plugins

[![Tests](https://github.com/pcsalt/claude-code-plugins/actions/workflows/tests.yml/badge.svg)](https://github.com/pcsalt/claude-code-plugins/actions/workflows/tests.yml)

A marketplace of plugins for Claude Code — status line widgets, tools, and utilities.

## Available Plugins

| Plugin | Type | Description | Dependencies |
|--------|------|-------------|--------------|
| [claude-reset](plugins/claude-reset/) | Status line | Rate limits, context window, git status, session clock | Python 3 (stdlib only) |
| [claude-log](plugins/claude-log/) | Hook | Session activity logger | Python 3 (stdlib only) |

### claude-reset (status line)

All-in-one status line showing everything you need at a glance:

- **Context window** — conversation context usage with token counts (`85k/200k`), read from Claude Code's stdin (no API call)
- **Session (5h)** — rate limit utilization bar with countdown and local reset time
- **Weekly (7d)** — all models combined rate limit
- **Opus / Sonnet** — model-specific weekly limits (shown only when available)
- **Overage** — monthly overage spend vs budget
- **Elapsed** — session duration timer, persists across restarts, auto-resets after 24h
- **Git** — current branch, modified file count (`3✎`), ahead/behind remote (`2↑ 1↓`)

```
📐 Context  [▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱]  42%  85k/200k
⚡ Session  [▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱]  42%  ↻ 2h 15m (14:30)
📅 Weekly   [▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱]  35%  ↻ 3d 4h (Wed 18:00)
🕑 Elapsed  1h 23m
🔀 Git      feat/context  2↑ 3✎
```

### claude-log (hook)

Logs every tool usage to a project-local `.claude/session-log.md`:

- **Edit / Write / Read** — logs the file path
- **Bash** — logs the command (truncated at 120 chars)
- **Grep / Glob** — logs the search pattern and path
- Automatic date headers, timestamped entries

```markdown
## 2026-03-08
- `10:30:00` | **Read** | `/src/app.py`
- `10:30:15` | **Edit** | `/src/app.py`
- `10:31:02` | **Bash** | `git status`
```

Install: `~/.claude-code-plugins/plugins/claude-log/install.sh`

## Quick Install

One command to clone, configure, and activate:

```bash
curl -sSL https://raw.githubusercontent.com/pcsalt/claude-code-plugins/main/install.sh | bash
```

**Detail view** (multi-line, default):
```bash
curl -sSL https://raw.githubusercontent.com/pcsalt/claude-code-plugins/main/install.sh | bash -s -- --detail
```

**Compact view** (single line):
```bash
curl -sSL https://raw.githubusercontent.com/pcsalt/claude-code-plugins/main/install.sh | bash -s -- --compact
```

## Update

Pull the latest changes:

```bash
~/.claude-code-plugins/update.sh
```

Or via curl:

```bash
curl -sSL https://raw.githubusercontent.com/pcsalt/claude-code-plugins/main/update.sh | bash
```

## Uninstall

Remove the plugin, cache, and status line config:

```bash
~/.claude-code-plugins/uninstall.sh
```

Or via curl:

```bash
curl -sSL https://raw.githubusercontent.com/pcsalt/claude-code-plugins/main/uninstall.sh | bash
```

## Manual Installation

### 1. Clone the repo

```bash
git clone https://github.com/pcsalt/claude-code-plugins.git ~/.claude-code-plugins
```

### 2. Pick a plugin

Browse the [plugins/](plugins/) directory and follow the plugin's own README for setup.

### 3. Configure Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "PYTHONPATH=~/.claude-code-plugins/plugins/claude-reset python3 -m claude_reset.main --detail"
  }
}
```

### 4. Restart Claude Code

The status line appears after the next assistant message.

## Contributing

Want to add a plugin? Create a directory under `plugins/` with:

```
plugins/your-plugin/
  README.md          # docs, screenshots, install steps
  your_plugin/       # source code
  tests/             # tests (required)
```

Open a PR and we'll review it.

## License

MIT
