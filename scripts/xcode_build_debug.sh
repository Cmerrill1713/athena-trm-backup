#!/usr/bin/env bash
set -euo pipefail

SCHEME="${SCHEME:-NeuroForgeApp}"
echo "🔨 Building $SCHEME (Debug)..."

# Navigate to NeuroForgeApp directory if not already there
if [[ ! -f "Package.swift" ]] && [[ -d "NeuroForgeApp" ]]; then
  cd NeuroForgeApp
fi

xcodebuild \
  -scheme "$SCHEME" \
  -configuration Debug \
  -destination 'platform=macOS' \
  -derivedDataPath build \
  -quiet \
  build

echo "✅ Build complete: build/Build/Products/Debug/$SCHEME.app"

