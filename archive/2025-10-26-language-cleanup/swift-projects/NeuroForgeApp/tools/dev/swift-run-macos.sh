#!/usr/bin/env bash
set -euo pipefail
APP="${APP:-NeuroForgeApp}"
BUILD_DIR="${BUILD_DIR:-.build/debug}"

echo "🚀 Launching $APP…"

# Try SwiftPM build first
if [ -f "$BUILD_DIR/$APP" ]; then
  echo "📦 Running SPM build: $BUILD_DIR/$APP"
  "$BUILD_DIR/$APP" &
  APP_PID=$!
  echo "✅ Launched PID: $APP_PID"
  echo "   Logs: tail -f /tmp/neuroforge.log"
  echo "   Kill: kill $APP_PID"
  exit 0
fi

# Try opening as macOS app
if open -a "$APP" 2>/dev/null; then
  echo "✅ Opened $APP.app"
  exit 0
fi

echo "❌ Could not find or launch $APP"
echo "   Tried: $BUILD_DIR/$APP"
echo "   Tried: /Applications/$APP.app"
exit 1

