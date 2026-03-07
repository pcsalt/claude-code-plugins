# Claude Code Plugins

A marketplace of plugins for Claude Code — status line widgets, tools, and utilities.

## Available Plugins

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| [claude-reset](plugins/claude-reset/) | Rate limit usage bars and countdown timers in your status line | Python 3 (stdlib only) |

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/pcsalt/claude-code-plugins.git ~/.claude-code-plugins
```

### 2. Pick a plugin

Browse the [plugins/](plugins/) directory and follow the plugin's own README for setup.

### 3. Configure Claude Code

Each plugin provides a `statusLine` config snippet. Add it to your `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "PYTHONPATH=~/.claude-code-plugins/plugins/claude-reset python3 -m claude_reset.main --detail"
  }
}
```

### 4. Stay updated

```bash
cd ~/.claude-code-plugins && git pull
```

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
