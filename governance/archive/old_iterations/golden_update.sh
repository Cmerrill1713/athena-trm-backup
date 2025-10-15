#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "🔄 Updating golden baselines..."

# Update baselines by re-running tests with GOLDEN_UPDATE=1
GOLDEN_UPDATE=1 xcodebuild \
  -project NeuroForgeApp.xcodeproj \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -derivedDataPath DerivedData \
  test 2>&1 | tee artifacts/xcodebuild-golden-update.log

echo ""
echo "✅ Golden baselines updated!"
echo "📁 See: UITests/Golden/Baseline/"
echo ""
echo "Next steps:"
echo "  1. Review the updated baselines visually"
echo "  2. git add UITests/Golden/Baseline/*.png"
echo "  3. git commit -m 'test(ui): update golden baselines'"
