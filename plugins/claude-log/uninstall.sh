#!/usr/bin/env bash
set -euo pipefail

SETTINGS_FILE="$HOME/.claude/settings.json"

# Colors
GREEN='\033[32m'
YELLOW='\033[33m'
DIM='\033[2m'
RESET='\033[0m'

info()  { echo -e "${GREEN}[+]${RESET} $1"; }
warn()  { echo -e "${YELLOW}[!]${RESET} $1"; }

# Remove claude-log hook from settings.json
if [ -f "$SETTINGS_FILE" ]; then
  if python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    s = json.load(f)
entries = s.get('hooks', {}).get('PostToolUse', [])
found = any('claude_log' in h.get('command', '') for entry in entries for h in entry.get('hooks', []))
if not found:
    sys.exit(1)
" 2>/dev/null; then
    python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    settings = json.load(f)
hooks = settings.get('hooks', {})
post_hooks = hooks.get('PostToolUse', [])
post_hooks = [entry for entry in post_hooks if not any('claude_log' in h.get('command', '') for h in entry.get('hooks', []))]
if post_hooks:
    hooks['PostToolUse'] = post_hooks
else:
    hooks.pop('PostToolUse', None)
if not hooks:
    settings.pop('hooks', None)
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
"
    info "Removed claude-log hook from $SETTINGS_FILE"
  else
    warn "No claude-log hook found in $SETTINGS_FILE"
  fi
else
  warn "Settings file not found: $SETTINGS_FILE"
fi

echo ""
info "Uninstall complete!"
echo -e "  ${DIM}Note: session-log.md files in your projects are preserved.${RESET}"
echo -e "  ${DIM}Restart Claude Code to apply changes.${RESET}"
