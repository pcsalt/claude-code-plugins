#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$HOME/.claude-code-plugins"
SETTINGS_FILE="$HOME/.claude/settings.json"
CACHE_FILE="$HOME/.claude/claude-reset-cache.json"

GREEN='\033[32m'
YELLOW='\033[33m'
DIM='\033[2m'
RESET='\033[0m'

info() { echo -e "${GREEN}[+]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }

# Remove statusLine from settings
if [ -f "$SETTINGS_FILE" ]; then
  if python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    s = json.load(f)
if 'statusLine' in s and 'claude_reset' in s['statusLine'].get('command', ''):
    del s['statusLine']
    with open('$SETTINGS_FILE', 'w') as f:
        json.dump(s, f, indent=2)
        f.write('\n')
    raise SystemExit(0)
raise SystemExit(1)
" 2>/dev/null; then
    info "Removed statusLine config from settings.json"
  else
    warn "No claude-reset statusLine found in settings.json"
  fi
fi

# Remove cache
if [ -f "$CACHE_FILE" ]; then
  rm "$CACHE_FILE"
  info "Removed cache file"
fi

# Remove installation
if [ -d "$INSTALL_DIR" ]; then
  rm -rf "$INSTALL_DIR"
  info "Removed $INSTALL_DIR"
else
  warn "No installation found at $INSTALL_DIR"
fi

echo ""
info "Uninstall complete. Restart Claude Code to apply."
