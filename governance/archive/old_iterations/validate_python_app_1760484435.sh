#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:?Usage: validate_python_app.sh /path/to/python-project}"

echo "🧪 Validating Python app: $(basename "$APP_DIR")"
echo "   Project: $APP_DIR"

pushd "$APP_DIR" >/dev/null

# Activate venv if present
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Run pytest
echo "▶️  Running pytest..."
if command -v pytest >/dev/null 2>&1; then
  pytest -q --tb=short
  RESULT=$?
else
  echo "⚠️  pytest not found, skipping tests"
  RESULT=0
fi

# Run ruff if available
if command -v ruff >/dev/null 2>&1; then
  echo "▶️  Running ruff..."
  ruff check .
fi

popd >/dev/null

if [ $RESULT -ne 0 ]; then
  echo "❌ Tests failed" >&2
  exit 1
fi

echo "✅ Validation passed"

