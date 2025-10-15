#!/usr/bin/env bash
set -euo pipefail
APP_PATH="${1:?path to .app}"
DMG_PATH="$(dirname "$APP_PATH")/$(basename "$APP_PATH" .app).dmg"
hdiutil create -volname "$(basename "$APP_PATH" .app)" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
shasum -a 256 "$DMG_PATH" > "${DMG_PATH}.sha256"
echo "$DMG_PATH"
