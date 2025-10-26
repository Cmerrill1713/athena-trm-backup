#!/usr/bin/env bash
set -euo pipefail

SCHEME="${SCHEME:-NeuroForgeApp}"
WORKSPACE="${WORKSPACE:-NeuroForgeApp.xcworkspace}"
PROJECT="${PROJECT:-Package.swift}"

echo "🔎 Preflight: Xcode / Schemes / Deps"
xcodebuild -version || { echo "❌ Xcode not found"; exit 1; }

# Check if we have workspace or project
if [ -f "$WORKSPACE/contents.xcworkspacedata" ]; then
  echo "📋 Using workspace: $WORKSPACE"
  xcodebuild -list -workspace "$WORKSPACE" || { echo "❌ Cannot list schemes"; exit 1; }
  
  if ! xcodebuild -list -workspace "$WORKSPACE" 2>/dev/null | grep -q "$SCHEME"; then
    echo "❌ Scheme '$SCHEME' not found in $WORKSPACE"
    exit 1
  fi
  
  echo "📦 Resolving SPM dependencies…"
  xcodebuild -resolvePackageDependencies -workspace "$WORKSPACE" -scheme "$SCHEME" -quiet || {
    echo "❌ Package resolution failed"; exit 1;
  }
elif [ -f "$PROJECT" ]; then
  echo "📋 Using SwiftPM: $PROJECT"
  swift package resolve || { echo "❌ SPM resolution failed"; exit 1; }
else
  echo "❌ No workspace or Package.swift found"
  exit 1
fi

echo "✅ Preflight OK"

