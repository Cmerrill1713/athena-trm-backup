#!/usr/bin/env bash
# Rotate Assistant Broker Token
# Safe rotation with automatic reload

set -euo pipefail

PLIST_PATH="$HOME/Library/LaunchAgents/com.neuroforge.assistant-broker.plist"
TOKEN_FILE="$HOME/.assistant-broker-token"

echo "🔄 Rotating Assistant Broker Token"
echo "==================================="

# Check if LaunchAgent exists
if [ ! -f "$PLIST_PATH" ]; then
    echo "❌ LaunchAgent not found at: $PLIST_PATH"
    echo "   Run: cd ~/Documents/GitHub/assistant-broker && make install-agent"
    exit 1
fi

# Generate new token
NEW_TOKEN=$(openssl rand -hex 32)
echo "🔑 Generated new token: ${NEW_TOKEN:0:16}... (64 chars)"

# Backup old plist
cp "$PLIST_PATH" "${PLIST_PATH}.backup"
echo "💾 Backed up plist to: ${PLIST_PATH}.backup"

# Update plist using plutil
if command -v plutil >/dev/null 2>&1; then
    plutil -replace EnvironmentVariables.ASSISTANT_BROKER_TOKEN -string "$NEW_TOKEN" "$PLIST_PATH"
    echo "✅ Updated LaunchAgent plist"
else
    # Fallback to sed
    sed -i '' "s|<key>ASSISTANT_BROKER_TOKEN</key><string>.*</string>|<key>ASSISTANT_BROKER_TOKEN</key><string>$NEW_TOKEN</string>|" "$PLIST_PATH"
    echo "✅ Updated LaunchAgent plist (via sed)"
fi

# Save token to file
printf "%s\n" "$NEW_TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
echo "✅ Saved token to: $TOKEN_FILE"

# Reload LaunchAgent
echo "🔄 Reloading LaunchAgent..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true
sleep 1
launchctl load "$PLIST_PATH"
echo "✅ LaunchAgent reloaded"

# Wait for broker to start
echo "⏳ Waiting for broker to start..."
sleep 2

# Test health
if curl -sf http://127.0.0.1:8080/v1/health >/dev/null; then
    echo "✅ Broker is healthy"
else
    echo "⚠️  Broker not responding yet (may take a few more seconds)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Token rotation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Update ASSISTANT_BROKER_TOKEN in your assistant's environment"
echo "   2. Or ensure it reads from: $TOKEN_FILE"
echo ""
echo "🔑 New token: $NEW_TOKEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

