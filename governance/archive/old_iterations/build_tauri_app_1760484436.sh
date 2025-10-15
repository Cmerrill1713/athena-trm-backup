#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:?Usage: build_tauri_app.sh /path/to/tauri-project}"
OUT="$HOME/Desktop/Builds/$(basename "$APP_DIR")/$(date +%Y%m%d-%H%M%S)"

echo "🔨 Building Tauri app from: $APP_DIR"
echo "   Output: $OUT"

pushd "$APP_DIR" >/dev/null

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "pnpm-lock.yaml" ]; then
  pnpm i --silent
elif [ -f "package-lock.json" ]; then
  npm ci --silent
else
  npm install --silent
fi

# Build Tauri app
echo "🦀 Building Tauri app..."
if command -v pnpm >/dev/null 2>&1 && [ -f "pnpm-lock.yaml" ]; then
  pnpm tauri build
else
  npm run tauri build
fi

# Find the built .app
APP=$(find src-tauri/target/release/bundle/macos -name "*.app" 2>/dev/null | head -n1)

if [ -z "$APP" ] || [ ! -d "$APP" ]; then
  echo "❌ No .app found in src-tauri/target/release/bundle/macos" >&2
  exit 1
fi

echo "✅ Build succeeded"
echo "📦 Copying app to output..."
mkdir -p "$OUT"
cp -R "$APP" "$OUT/"
popd >/dev/null

FINAL_PATH="$OUT/$(basename "$APP")"
echo "✓ App ready: $FINAL_PATH"
echo "$FINAL_PATH"

