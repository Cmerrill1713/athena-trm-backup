#!/usr/bin/env bash
set -euo pipefail
SCHEME="${SCHEME:-NeuroForgeApp}"
DEST="${DEST:-platform=macOS}"
WORKSPACE="${WORKSPACE:-NeuroForgeApp.xcworkspace}"
PROJECT="${PROJECT:-Package.swift}"

echo "🧪 Tests for $SCHEME…"

# Check if we have xcbeautify
if command -v xcbeautify &> /dev/null; then
  BEAUTIFY="xcbeautify"
else
  BEAUTIFY="cat"
fi

if [ -f "$WORKSPACE/contents.xcworkspacedata" ]; then
  xcodebuild test \
    -workspace "$WORKSPACE" \
    -scheme "$SCHEME" \
    -destination "$DEST" \
    -enableCodeCoverage YES | $BEAUTIFY
elif [ -f "$PROJECT" ]; then
  swift test
else
  echo "❌ No workspace or Package.swift found"
  exit 1
fi

echo "✅ Tests OK"

