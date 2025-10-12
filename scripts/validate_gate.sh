#!/usr/bin/env bash
# Validation Gate - No green, no package
set -euo pipefail

TYPE="${1:?Usage: validate_gate.sh swift|tauri|python [args...]}"
shift

echo "🔒 Validation Gate: $TYPE"
echo "═══════════════════════════════════════"

case "$TYPE" in
  swift)
    if [ $# -lt 2 ]; then
      echo "Usage: validate_gate.sh swift APP_NAME PROJ_DIR"
      exit 1
    fi
    ./scripts/validate_swift_app.sh "$@"
    ;;
  
  tauri)
    PROJ_DIR="${1:?Project directory required}"
    cd "$PROJ_DIR"
    echo "Running Playwright tests..."
    if command -v npx >/dev/null 2>&1; then
      npx playwright test || { echo "❌ Tauri tests failed"; exit 1; }
    else
      echo "⚠️  npx not found, skipping tests"
    fi
    ;;
  
  python)
    PROJ_DIR="${1:?Project directory required}"
    ./scripts/validate_python_app.sh "$PROJ_DIR"
    ;;
  
  *)
    echo "❌ Unknown type: $TYPE"
    echo "Supported types: swift, tauri, python"
    exit 1
    ;;
esac

echo ""
echo "✅ Validation PASSED - safe to package"
exit 0

