#!/bin/bash
set -e

cd NeuroForgeApp

echo "🔧 Opening Xcode with project and all new files..."

# Open project
open NeuroForgeApp.xcodeproj
sleep 2

# Open all new files in Xcode
xed -p NeuroForgeApp.xcodeproj \
  Sources/AthenaModels.swift \
  Sources/AthenaState.swift \
  Sources/VoiceManager.swift \
  Sources/Notifications+App.swift \
  Sources/AthenaDashboardView.swift \
  Sources/Athena/CriticalAlertWindow.swift \
  Sources/Athena/TribunalDecisionWindow.swift \
  Sources/Athena/SystemEmergencyWindow.swift

echo ""
echo "✅ All files opened in Xcode!"
echo ""
echo "📝 IN XCODE NOW:"
echo "  1. You should see 8 file tabs open"
echo "  2. For each file, it may prompt to add to target"
echo "  3. OR: Select all 8 files in project navigator"
echo "  4. Right-click → Add to Target → NeuroForgeApp"
echo ""
echo "  Then:"
echo "  5. Clean: Shift+Cmd+K"
echo "  6. Build: Cmd+B (should be ZERO errors)"
echo "  7. Run: Cmd+R"
echo "  8. Click demo buttons to see pop-outs!"
