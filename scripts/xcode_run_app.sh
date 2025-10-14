#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-NeuroForgeApp}"
echo "🚀 Launching $APP_NAME..."

# Find the built app
APP_PATH=$(find build/Build/Products -name "$APP_NAME.app" -type d 2>/dev/null | head -1)

if [ -z "$APP_PATH" ]; then
  echo "❌ App not found. Run 'bash scripts/xcode_build_debug.sh' first."
  exit 1
fi

# Launch with environment controls
POPUPS_ENABLED="${POPUPS_ENABLED:-1}" \
AUTOEXEC_GUARD="${AUTOEXEC_GUARD:-1}" \
open "$APP_PATH"

echo "✅ $APP_NAME launched"

