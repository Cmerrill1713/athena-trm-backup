#!/usr/bin/env bash
set -euo pipefail
echo "🧹 swiftformat + swiftlint…"

# Check for tools
HAS_FORMAT=false
HAS_LINT=false

if command -v swiftformat &> /dev/null; then
  HAS_FORMAT=true
else
  echo "ℹ️  swiftformat not found (brew install swiftformat)"
fi

if command -v swiftlint &> /dev/null; then
  HAS_LINT=true
else
  echo "ℹ️  swiftlint not found (brew install swiftlint)"
fi

# Format
if [ "$HAS_FORMAT" = true ]; then
  swiftformat Sources --swiftversion 6.0
fi

# Lint
if [ "$HAS_LINT" = true ]; then
  swiftlint --fix || true
  swiftlint
fi

if [ "$HAS_FORMAT" = true ] || [ "$HAS_LINT" = true ]; then
  echo "✅ Lint/Format OK"
else
  echo "⚠️  No lint/format tools installed"
fi

