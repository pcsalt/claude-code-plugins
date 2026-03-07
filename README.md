# Claude Code Plugins

A marketplace of plugins for Claude Code — status line widgets, tools, and utilities.

## Available Plugins

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| [claude-reset](plugins/claude-reset/) | Rate limit usage bars and countdown timers in your status line | Python 3 (stdlib only) |

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
