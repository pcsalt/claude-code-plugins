#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/pcsalt/claude-code-plugins.git"
INSTALL_DIR="$HOME/.claude-code-plugins"
SETTINGS_FILE="$HOME/.claude/settings.json"
PLUGIN="claude-reset"
MODE="${1:---detail}"

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
command -v git >/dev/null 2>&1 || error "git is required"
command -v python3 >/dev/null 2>&1 || error "python3 is required"

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
  info "Updating existing installation..."
  git -C "$INSTALL_DIR" pull --quiet
else
  info "Cloning claude-code-plugins..."
  git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

info "Plugin installed at $INSTALL_DIR"

# Verify plugin works
if PYTHONPATH="$INSTALL_DIR/plugins/$PLUGIN" python3 -c "from claude_reset.main import get_usage_data" 2>/dev/null; then
  info "Plugin verified successfully"
else
  warn "Plugin import check failed — Python 3.8+ required"
fi

# Build the statusLine command
STATUS_CMD="PYTHONPATH=$INSTALL_DIR/plugins/$PLUGIN python3 -m claude_reset.main $MODE"

# Patch settings.json
if [ ! -d "$HOME/.claude" ]; then
  mkdir -p "$HOME/.claude"
fi

if [ ! -f "$SETTINGS_FILE" ]; then
  # Create fresh settings file
  cat > "$SETTINGS_FILE" <<SETTINGS
{
  "statusLine": {
    "type": "command",
    "command": "$STATUS_CMD"
  }
}
SETTINGS
  info "Created $SETTINGS_FILE with statusLine config"
else
  # Check if statusLine already configured
  if python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    s = json.load(f)
if 'statusLine' in s:
    sys.exit(1)
" 2>/dev/null; then
    # No statusLine key — add it
    python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    settings = json.load(f)
settings['statusLine'] = {
    'type': 'command',
    'command': '$STATUS_CMD'
}
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
"
    info "Added statusLine config to $SETTINGS_FILE"
  else
    warn "statusLine already configured in $SETTINGS_FILE"
    echo -e "  ${DIM}To switch to claude-reset, update the command to:${RESET}"
    echo -e "  ${DIM}$STATUS_CMD${RESET}"
  fi
fi

echo ""
info "Installation complete!"
echo -e "  ${DIM}View mode: $MODE${RESET}"
echo -e "  ${DIM}To change: re-run with --compact or --detail${RESET}"
echo ""
echo -e "  ${GREEN}Restart Claude Code to see the status line.${RESET}"
