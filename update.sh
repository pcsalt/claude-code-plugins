#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$HOME/.claude-code-plugins"

GREEN='\033[32m'
RED='\033[31m'
DIM='\033[2m'
RESET='\033[0m'

info()  { echo -e "${GREEN}[+]${RESET} $1"; }
error() { echo -e "${RED}[x]${RESET} $1"; exit 1; }

if [ ! -d "$INSTALL_DIR" ]; then
  error "No installation found at $INSTALL_DIR — run install.sh first"
fi

info "Checking for updates..."
git -C "$INSTALL_DIR" fetch --quiet

LOCAL=$(git -C "$INSTALL_DIR" rev-parse HEAD)
REMOTE=$(git -C "$INSTALL_DIR" rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  info "Already up to date."
else
  BEHIND=$(git -C "$INSTALL_DIR" rev-list HEAD..origin/main --count)
  info "Pulling $BEHIND new commit(s)..."
  git -C "$INSTALL_DIR" pull --quiet
  info "Updated successfully."
  echo -e "  ${DIM}Restart Claude Code to pick up changes.${RESET}"
fi
