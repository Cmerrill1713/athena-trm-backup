#!/usr/bin/env bash
set -euo pipefail

# Quick script to add new files to Xcode project using command line

echo "🔧 Adding new Swift files to Xcode project..."

cd "$(dirname "$0")/.."

# Use PBXProj manipulation (requires Xcode installed)
# This creates a simpler approach - just rebuild the file list

PROJ_DIR="NeuroForgeApp"
PROJ_FILE="$PROJ_DIR/NeuroForgeApp.xcodeproj"

echo "📝 Project: $PROJ_FILE"

# List all new files
NEW_FILES=(
  "$PROJ_DIR/Sources/AthenaModels.swift"
  "$PROJ_DIR/Sources/AthenaState.swift"
  "$PROJ_DIR/Sources/VoiceManager.swift"
  "$PROJ_DIR/Sources/Notifications+App.swift"
  "$PROJ_DIR/Sources/AthenaDashboardView.swift"
  "$PROJ_DIR/Sources/Athena/CriticalAlertWindow.swift"
  "$PROJ_DIR/Sources/Athena/TribunalDecisionWindow.swift"
  "$PROJ_DIR/Sources/Athena/SystemEmergencyWindow.swift"
)

echo "📂 Files to add:"
for f in "${NEW_FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f (missing!)"
  fi
done

echo ""
echo "⚠️  MANUAL STEP REQUIRED:"
echo ""
echo "1. Open Xcode:"
echo "   open $PROJ_FILE"
echo ""
echo "2. In Xcode project navigator:"
echo "   - Right-click 'Sources' folder"
echo "   - Select 'Add Files to \"NeuroForgeApp\"...'"
echo "   - Navigate to NeuroForgeApp/Sources/"
echo "   - Select these files (Cmd+Click for multiple):"
for f in "${NEW_FILES[@]}"; do
  basename "$f"
done
echo "   - Check '✓ Copy items if needed'"
echo "   - Check '✓ Add to targets: NeuroForgeApp'"
echo "   - Click 'Add'"
echo ""
echo "3. Clean build folder:"
echo "   Shift+Cmd+K in Xcode"
echo ""
echo "4. Build:"
echo "   Cmd+B"
echo ""
echo "5. Run:"
echo "   Cmd+R"
echo ""
echo "6. Test pop-outs:"
echo "   - Click 'Demo Critical Alert' button"
echo "   - Click 'Demo Tribunal Decision' button"
echo "   - Click 'Demo System Emergency' button"
echo ""
echo "Expected: All 3 windows should appear with proper content!"
