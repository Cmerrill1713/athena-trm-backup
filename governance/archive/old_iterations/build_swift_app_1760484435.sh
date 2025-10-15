#!/usr/bin/env bash
set -euo pipefail
APP_NAME="${1:?app name}"
PROJ_DIR="${2:?xcodeproj or swift package dir}"
OUT="$HOME/Desktop/Builds/$APP_NAME/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
pushd "$PROJ_DIR" >/dev/null
if [ -f "Package.swift" ]; then
  swift build -c release
  APP_PATH=".build/release/$APP_NAME.app"
else
  xcodebuild -scheme "$APP_NAME" -configuration Release -derivedDataPath .derived | xcpretty || true
  APP_PATH=".derived/Build/Products/Release/$APP_NAME.app"
fi
test -d "$APP_PATH" || { echo "Build failed: $APP_PATH missing" >&2; exit 1; }
cp -R "$APP_PATH" "$OUT/"
echo "$OUT/$APP_NAME.app"
