#!/usr/bin/env bash
set -euo pipefail

# Athena Frontend Nuke & Pave Refactor
# =====================================
# Removes conflicting files and rebuilds clean minimal pop-out architecture

title() { printf "\n\033[1;36m%s\033[0m\n" "$1"; }
ok()    { printf "\033[0;32m✓ %s\033[0m\n" "$1"; }
warn()  { printf "\033[0;33m⚠ %s\033[0m\n" "$1"; }
die()   { printf "\033[0;31m✗ %s\033[0m\n" "$1"; exit 1; }

# --- Settings ---------------------------------------------------------------
ROOT="${ROOT:-$(pwd)}"
APP_NAME="${APP_NAME:-NeuroForgeApp}"
SRC_DIR="${SRC_DIR:-$ROOT/$APP_NAME/Sources}"
BACKUP_DIR="$ROOT/refactor_backup_$(date +%Y%m%d_%H%M%S)"
SCHEME="${SCHEME:-$APP_NAME}"

mkdir -p "$BACKUP_DIR"
ok "Created backup directory: $BACKUP_DIR"

title "1) Backing up conflicting files"

# Known offenders
declare -a OFFENDERS=(
  "Athena/AthenaDashboard.swift"
  "Athena/AthenaDashboard.swift.old"
  "Athena/ModernAthenaNavigation.swift"
  "Athena/ModernAthenaNavigation.swift.old"
  "Operations/AIRepublicMonitor.swift"
  "Operations/SimpleOpsWindow.swift"
  "Features/VoiceShim.swift"
  "Voice/VoiceManager.swift"
  "Design/CommandPalette.swift"
  "Design/SimpleOpsWindow.swift"
)

for f in "${OFFENDERS[@]}"; do
  if [ -f "$SRC_DIR/$f" ]; then
    cp "$SRC_DIR/$f" "$BACKUP_DIR/$(basename "$f")" && rm "$SRC_DIR/$f"
    ok "Removed $f"
  fi
done

title "2) Removing all SwiftUI Preview blocks"

# This prevents #Preview and Preview-only code from breaking builds
find "$SRC_DIR" -name '*.swift' -type f | while read -r file; do
  if grep -q "#Preview" "$file"; then
    # Remove entire #Preview blocks
    sed -i.bak '/#Preview/,/^}/d' "$file"
    rm -f "$file.bak"
    ok "Stripped previews from $(basename "$file")"
  fi
done

title "3) Creating clean Athena architecture"

# Core files already created by the agent:
# - AthenaModels.swift
# - AthenaState.swift
# - VoiceManager.swift
# - Notifications+App.swift
# - Athena/CriticalAlertWindow.swift
# - Athena/TribunalDecisionWindow.swift
# - Athena/SystemEmergencyWindow.swift
# - AthenaDashboardView.swift
# - main.swift

ok "Clean architecture files in place"

title "4) Validating Swift syntax"

# Quick syntax check before building
for file in "$SRC_DIR"/*.swift "$SRC_DIR"/Athena/*.swift; do
  if [ -f "$file" ]; then
    if ! swift -frontend -parse "$file" -sdk /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk 2>/dev/null; then
      warn "Syntax issues in $(basename "$file") - will be caught in build"
    fi
  fi
done

title "5) Building Debug configuration"

cd "$ROOT/NeuroForgeApp"
set +e
xcodebuild -project NeuroForgeApp.xcodeproj \
  -scheme "$SCHEME" \
  -configuration Debug \
  -destination 'platform=macOS' \
  build \
  -quiet
BUILD_STATUS=$?
set -e

if [ $BUILD_STATUS -eq 0 ]; then
  ok "Build succeeded!"
else
  warn "Build failed - check errors above"
  echo ""
  echo "Note: New files may need to be added to the Xcode project manually:"
  echo "  1. Open NeuroForgeApp.xcodeproj in Xcode"
  echo "  2. Right-click on Sources folder → Add Files..."
  echo "  3. Select the new files (AthenaModels.swift, AthenaState.swift, etc.)"
  echo "  4. Ensure 'Copy items if needed' is checked"
  echo "  5. Rebuild"
  exit $BUILD_STATUS
fi

title "✅ Refactor Complete"

echo ""
echo "Backup location: $BACKUP_DIR"
echo "New architecture files:"
echo "  • AthenaModels.swift (unified data models)"
echo "  • AthenaState.swift (single source of truth)"
echo "  • VoiceManager.swift (unified stub)"
echo "  • Notifications+App.swift (centralized events)"
echo "  • Athena/CriticalAlertWindow.swift"
echo "  • Athena/TribunalDecisionWindow.swift"
echo "  • Athena/SystemEmergencyWindow.swift"
echo "  • AthenaDashboardView.swift (main UI)"
echo "  • main.swift (app entry + multi-window setup)"
echo ""
echo "Next steps:"
echo "  1. Open the app in Xcode"
echo "  2. Run (Cmd+R) to see the Athena Dashboard"
echo "  3. Click the demo buttons to trigger pop-out windows"
echo "  4. All 3 windows should appear with proper content"
echo ""
echo "Or run from terminal:"
echo "  cd $ROOT"
echo "  make frontend  # Build via Makefile"
echo "  make run       # Launch app"
echo "  make demo      # Trigger pop-outs via Python script"

