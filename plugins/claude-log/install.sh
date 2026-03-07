#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$HOME/.claude-code-plugins"
SETTINGS_FILE="$HOME/.claude/settings.json"
PLUGIN="claude-log"

# Colors
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
DIM='\033[2m'
RESET='\033[0m'

info()  { echo -e "${GREEN}[+]${RESET} $1"; }
warn()  { echo -e "${YELLOW}[!]${RESET} $1"; }
error() { echo -e "${RED}[x]${RESET} $1"; exit 1; }

# Check dependencies
command -v python3 >/dev/null 2>&1 || error "python3 is required"

# Verify plugin directory exists
if [ ! -d "$INSTALL_DIR/plugins/$PLUGIN" ]; then
  error "Plugin not found at $INSTALL_DIR/plugins/$PLUGIN. Run the main install.sh first."
fi

# Verify plugin works
if PYTHONPATH="$INSTALL_DIR/plugins/$PLUGIN" python3 -c "from claude_log.logger import parse_hook_input" 2>/dev/null; then
  info "Plugin verified successfully"
else
  warn "Plugin import check failed — Python 3.8+ required"
fi

# Build the hook command
HOOK_CMD="PYTHONPATH=$INSTALL_DIR/plugins/$PLUGIN python3 -m claude_log.hook"

# Patch settings.json
if [ ! -d "$HOME/.claude" ]; then
  mkdir -p "$HOME/.claude"
fi

if [ ! -f "$SETTINGS_FILE" ]; then
  cat > "$SETTINGS_FILE" <<SETTINGS
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "$HOOK_CMD"
      }
    ]
  }
}
SETTINGS
  info "Created $SETTINGS_FILE with PostToolUse hook"
else
  # Check if PostToolUse hook with claude-log is already configured
  if python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    s = json.load(f)
hooks = s.get('hooks', {}).get('PostToolUse', [])
for h in hooks:
    if 'claude_log' in h.get('command', ''):
        sys.exit(1)
" 2>/dev/null; then
    # No claude-log hook — add it
    python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    settings = json.load(f)
hooks = settings.setdefault('hooks', {})
post_hooks = hooks.setdefault('PostToolUse', [])
post_hooks.append({
    'type': 'command',
    'command': '$HOOK_CMD'
})
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
"
    info "Added PostToolUse hook to $SETTINGS_FILE"
  else
    warn "claude-log hook already configured in $SETTINGS_FILE"
  fi
fi

echo ""
info "Installation complete!"
echo -e "  ${DIM}Logs will be written to .claude/session-log.md in each project.${RESET}"
echo ""
echo -e "  ${GREEN}Restart Claude Code to activate the hook.${RESET}"
