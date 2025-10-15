#!/usr/bin/env bash
# One-Liner App Delivery: Prompt → Deliver
# Usage: deliver_app.sh NAME TYPE PROJECT_PATH

set -euo pipefail

NAME="${1:?Usage: deliver_app.sh NAME TYPE PROJECT_PATH}"
TYPE="${2:?Usage: deliver_app.sh NAME TYPE PROJECT_PATH (TYPE: swift|tauri|python)}"
PROJ="${3:?Usage: deliver_app.sh NAME TYPE PROJECT_PATH}"

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
TOKEN=$(cat ~/.assistant-broker-token 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "❌ No token found at ~/.assistant-broker-token"
    echo "   Run: cd ~/Documents/GitHub/assistant-broker && make install-agent"
    exit 1
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  App Delivery Pipeline: $NAME"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Validate
echo "━━━ Step 1/4: Validation ━━━"
if [ "$TYPE" = "swift" ]; then
    "$SCRIPTS_DIR/validate_gate.sh" swift "$NAME" "$PROJ"
elif [ "$TYPE" = "python" ]; then
    "$SCRIPTS_DIR/validate_gate.sh" python "$PROJ"
elif [ "$TYPE" = "tauri" ]; then
    "$SCRIPTS_DIR/validate_gate.sh" tauri "$PROJ"
else
    echo "❌ Unknown type: $TYPE"
    exit 1
fi
echo "✅ Validation passed"
echo ""

# Step 2: Build
echo "━━━ Step 2/4: Build ━━━"
if [ "$TYPE" = "swift" ]; then
    APP_PATH=$("$SCRIPTS_DIR/build_swift_app.sh" "$NAME" "$PROJ" | tail -1)
elif [ "$TYPE" = "tauri" ]; then
    APP_PATH=$("$SCRIPTS_DIR/build_tauri_app.sh" "$PROJ" | tail -1)
else
    echo "⚠️  No build step for type: $TYPE"
    echo "✅ Delivery complete (validation only)"
    exit 0
fi
echo "✅ Built: $APP_PATH"
echo ""

# Step 3: Package
echo "━━━ Step 3/4: Package ━━━"
DMG_PATH=$("$SCRIPTS_DIR/package_dmg.sh" "$APP_PATH" | tail -1)
echo "✅ Packaged: $DMG_PATH"
echo ""

# Step 4: Reveal
echo "━━━ Step 4/4: Reveal ━━━"
curl -sf -X POST http://127.0.0.1:8080/v1/run \
    -H "X-Assistant-Token: $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"cmd\":\"open\",\"args\":[\"-R\",\"$DMG_PATH\"]}" >/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Revealed in Finder"
else
    echo "⚠️  Failed to reveal (broker may not be running)"
    echo "   Artifact at: $DMG_PATH"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Delivery Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Artifacts:"
echo "   APP: $APP_PATH"
echo "   DMG: $DMG_PATH"
echo ""

