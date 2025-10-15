#!/usr/bin/env bash
# Setup Athena Voice Control
# Creates global alias and installs dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          🗣️  ATHENA VOICE CONTROL SETUP                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Detect shell
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo "⚠️  Unknown shell. Defaulting to .bashrc"
    SHELL_RC="$HOME/.bashrc"
    SHELL_NAME="bash"
fi

echo "Detected shell: $SHELL_NAME"
echo "Config file: $SHELL_RC"
echo ""

# Add alias to shell config
ALIAS_LINE="alias athena='cd $WORKSPACE_ROOT && ./athena-voice-control/athena_voice.sh'"

if grep -q "alias athena=" "$SHELL_RC" 2>/dev/null; then
    echo "✅ Athena alias already exists in $SHELL_RC"
else
    echo "📝 Adding athena alias to $SHELL_RC..."
    echo "" >> "$SHELL_RC"
    echo "# Athena Voice Control" >> "$SHELL_RC"
    echo "$ALIAS_LINE" >> "$SHELL_RC"
    echo "✅ Alias added"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ SETUP COMPLETE ✅                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Usage:"
echo "  1. Reload your shell: source $SHELL_RC"
echo "  2. Talk to Athena: athena \"bring everything online\""
echo "  3. Interactive mode: athena"
echo ""
echo "Examples:"
echo "  athena \"run smoke tests\""
echo "  athena \"what's running\""
echo "  athena \"ship it\""
echo ""
echo "Help:"
echo "  athena help"
echo ""

