#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${1:?Usage: validate_swift_app.sh APP_NAME PROJ_DIR}"
PROJ_DIR="${2:?Usage: validate_swift_app.sh APP_NAME PROJ_DIR}"

echo "🧪 Validating Swift app: $APP_NAME"
echo "   Project: $PROJ_DIR"

pushd "$PROJ_DIR" >/dev/null

# Run tests
echo "▶️  Running tests..."
if command -v xcpretty >/dev/null 2>&1; then
  xcodebuild test -scheme "$APP_NAME" -destination 'platform=macOS' 2>&1 | xcpretty
  RESULT=${PIPESTATUS[0]}
else
  xcodebuild test -scheme "$APP_NAME" -destination 'platform=macOS'
  RESULT=$?
fi

popd >/dev/null

if [ $RESULT -ne 0 ]; then
  echo "❌ Tests failed for $APP_NAME" >&2
  exit 1
fi

echo "✅ All tests passed"

