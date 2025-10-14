#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-NeuroForgeApp}"
echo "🚀 Launching $APP_NAME..."

# Navigate to NeuroForgeApp if not there
if [[ ! -f "Package.swift" ]] && [[ -d "NeuroForgeApp" ]]; then
  cd NeuroForgeApp
fi

# Find the built app in multiple possible locations
APP_PATH=$(find . -name "$APP_NAME.app" -type d 2>/dev/null | grep -E "(build|Build|DerivedData)" | head -1)

if [ -z "$APP_PATH" ]; then
  echo "❌ App not found. Run 'bash scripts/xcode_build_debug.sh' first."
  echo "   Searched in: $(pwd)"
  exit 1
fi

echo "   Found app: $APP_PATH"

# Launch with environment controls
POPUPS_ENABLED="${POPUPS_ENABLED:-1}" \
AUTOEXEC_GUARD="${AUTOEXEC_GUARD:-1}" \
open "$APP_PATH"

echo "✅ $APP_NAME launched"
