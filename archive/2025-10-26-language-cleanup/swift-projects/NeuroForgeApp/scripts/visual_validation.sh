#!/usr/bin/env bash
# NeuroForge Visual Validation
# Runs UI tests with visual playback and screenshot capture
set -euo pipefail

cd "$(dirname "$0")/.."

echo "👁️  NeuroForge Visual Validation"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
pass() { echo -e "${GREEN}✅ $1${NC}"; }

info "Running visual playback tests..."
info "Watch the app execute user flows automatically!"
echo ""

# Clean previous screenshots
rm -rf DerivedData/Logs/Test/Attachments 2>/dev/null || true
mkdir -p artifacts/visual-validation

# Run visual tests with verbose output
xcodebuild -project NeuroForgeApp.xcodeproj \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -derivedDataPath DerivedData \
  -only-testing:NeuroForgeAppUITests/VisualPlaybackTests \
  test 2>&1 | tee artifacts/visual-validation.log

echo ""
echo "===================================="
echo "📸 Visual Validation Complete"
echo "===================================="
echo ""

# Extract screenshots from xcresult
RESULT_PATH="DerivedData/Logs/Test/*.xcresult"
if ls $RESULT_PATH 1> /dev/null 2>&1; then
    LATEST_RESULT=$(ls -t DerivedData/Logs/Test/*.xcresult | head -1)
    pass "Results: $LATEST_RESULT"

    # Open results to view screenshots
    info "Opening test results with screenshots..."
    open "$LATEST_RESULT"

    # Copy screenshots to artifacts
    find "$LATEST_RESULT" -name "*.png" -exec cp {} artifacts/visual-validation/ \; 2>/dev/null || true
    SCREENSHOT_COUNT=$(ls -1 artifacts/visual-validation/*.png 2>/dev/null | wc -l | tr -d ' ')

    if [[ $SCREENSHOT_COUNT -gt 0 ]]; then
        pass "Captured $SCREENSHOT_COUNT screenshots"
        info "Screenshots saved to: artifacts/visual-validation/"
    fi
else
    echo "⚠️  No xcresult bundle found"
fi

echo ""
echo "Next steps:"
echo "  1. Review screenshots in Xcode result bundle"
echo "  2. Verify all UI flows worked correctly"
echo "  3. If green, proceed with DMG build"
echo ""
