#!/usr/bin/env bash
set -euo pipefail
SCHEME="${SCHEME:-NeuroForgeApp}"
CONFIG="${CONFIG:-Debug}"
DEST="${DEST:-platform=macOS}"
WORKSPACE="${WORKSPACE:-NeuroForgeApp.xcworkspace}"
PROJECT="${PROJECT:-Package.swift}"

echo "🧱 Building $SCHEME ($CONFIG)…"

# Check if we have xcbeautify
if command -v xcbeautify &> /dev/null; then
  BEAUTIFY="xcbeautify"
else
  echo "ℹ️  xcbeautify not found (brew install xcbeautify for prettier output)"
  BEAUTIFY="cat"
fi

if [ -f "$WORKSPACE/contents.xcworkspacedata" ]; then
  xcodebuild \
    -workspace "$WORKSPACE" \
    -scheme "$SCHEME" \
    -configuration "$CONFIG" \
    -destination "$DEST" \
    -enableCodeCoverage YES \
    OTHER_SWIFT_FLAGS="-warn-concurrency -enable-actor-data-race-checks -strict-concurrency=complete" \
    build | $BEAUTIFY
elif [ -f "$PROJECT" ]; then
  swift build -c debug \
    -Xswiftc -warn-concurrency \
    -Xswiftc -enable-actor-data-race-checks \
    -Xswiftc -strict-concurrency=complete
else
  echo "❌ No workspace or Package.swift found"
  exit 1
fi

echo "✅ Build OK"

