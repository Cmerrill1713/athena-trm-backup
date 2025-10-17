#!/bin/bash
# Pre-commit hook for UI snapshot validation
# Install: ln -s ../../scripts/pre-commit-ui-check.sh .git/hooks/pre-commit

set -euo pipefail

echo "🔍 Running UI snapshot pre-commit check..."

# Check if we're in the right directory
if [ ! -d "NeuroForgeApp" ]; then
    echo "❌ NeuroForgeApp directory not found. Run from repo root."
    exit 1
fi

cd NeuroForgeApp

# Quick snapshot test (non-blocking)
echo "📸 Running quick UI snapshot check..."
if swift test --filter PromptViewSnapshotTests --quiet 2>/dev/null; then
    echo "✅ UI snapshots generated successfully"
else
    echo "⚠️  UI snapshot test failed, but allowing commit (fix in CI)"
    # Don't block commit, just warn
fi

echo "🎯 Pre-commit UI check complete"
