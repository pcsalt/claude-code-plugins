# claude-log

A hook-based session activity logger for Claude Code. Logs every tool usage to a project-local `.claude/session-log.md`.

## What it logs

- **Edit / Write / Read** — file path
- **Bash** — command executed (truncated at 120 chars)
- **Grep / Glob** — search pattern and path
- **Other tools** — tool name with timestamp

## Sample output

```markdown
## 2026-03-08

- `10:30:00` | **Read** | `/src/app.py`
- `10:30:15` | **Edit** | `/src/app.py`
- `10:31:02` | **Bash** | `git status`
- `10:31:45` | **Grep** | `def main in /src`
- `10:32:10` | **Write** | `/src/utils.py`
```

## Quick Install

Requires the main repo to be cloned first (via `install.sh` or manually):

```bash
~/.claude-code-plugins/plugins/claude-log/install.sh
```

## Uninstall

```bash
~/.claude-code-plugins/plugins/claude-log/uninstall.sh
```

## Manual Installation

### 1. Clone the marketplace repo (if not already done)

```bash
git clone https://github.com/pcsalt/claude-code-plugins.git ~/.claude-code-plugins
```

### 2. Add the hook to Claude Code settings

Edit `~/.claude/settings.json` and add the `hooks` block:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "PYTHONPATH=~/.claude-code-plugins/plugins/claude-log python3 -m claude_log.hook"
          }
        ]
      }
    ]
  }
}
```

### 3. Restart Claude Code

The log file will be created at `.claude/session-log.md` in your project directory on the next tool use.

## How it works

1. Claude Code fires the `PostToolUse` hook after every tool call
2. The hook receives tool name and input as JSON on stdin
3. It parses the relevant details (file path, command, pattern)
4. Appends a timestamped markdown entry to `.claude/session-log.md`
5. New date headers are added automatically

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)
- Claude Code with hooks support

## Running tests

```bash
cd ~/.claude-code-plugins
python3 -m venv .venv && source .venv/bin/activate
pip install pytest
PYTHONPATH=plugins/claude-log pytest plugins/claude-log/tests/ -v
```
