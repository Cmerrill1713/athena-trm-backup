#!/usr/bin/env bash
# NeuroForge Release Build Test
# Build and launch Release configuration locally (pre-DMG validation)
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🔥 NeuroForge Release Build Test"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
pass() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# ============================================
# Build Release Configuration
# ============================================
info "Building Release configuration..."
echo ""

xcodebuild -project NeuroForgeApp.xcodeproj \
  -scheme NeuroForgeApp \
  -configuration Release \
  -derivedDataPath DerivedData \
  build

if [[ $? -eq 0 ]]; then
    pass "Release build succeeded"
else
    echo "❌ Release build failed"
    exit 1
fi

echo ""

# ============================================
# Locate Release App
# ============================================
APP_PATH="DerivedData/Build/Products/Release/NeuroForgeApp.app"

if [[ -d "$APP_PATH" ]]; then
    pass "Release app bundle: $APP_PATH"
else
    echo "❌ Release app not found at $APP_PATH"
    exit 1
fi

# Check bundle structure
if [[ -f "$APP_PATH/Contents/MacOS/NeuroForgeApp" ]]; then
    pass "Executable exists"
else
    echo "❌ Executable missing from bundle"
    exit 1
fi

echo ""

# ============================================
# Launch Release Build
# ============================================
info "Launching Release build..."
info "This is what users will see (no dev environment)"
echo ""

warn "App will launch in 3 seconds..."
warn "Manually test these features:"
warn "  1. App window appears"
warn "  2. Health banner shows status"
warn "  3. Type 'ping' and get response"
warn "  4. Press ⌘⌥I → Provider Inspector"
warn "  5. Press ⌘⇧T → Prompt Sidebar"
warn "  6. All features work"
echo ""

sleep 3

# Launch the release build
info "Launching: $APP_PATH"
API_BASE="${API_BASE:-http://localhost:8014}" \
QA_MODE="${QA_MODE:-1}" \
open "$APP_PATH"

echo ""
pass "Release build launched successfully"
echo ""
echo "👁️  WATCH THE APP NOW!"
echo "===================================="
echo ""
echo "Manual verification checklist:"
echo "  [ ] App window appears (no Terminal noise)"
echo "  [ ] Health banner shows 'Connected'"
echo "  [ ] Type message → Response appears"
echo "  [ ] ⌘⌥I → Provider Inspector works"
echo "  [ ] ⌘⇧T → Prompt Sidebar works"
echo "  [ ] Console logs show API calls"
echo "  [ ] No errors or crashes"
echo ""
echo "If all ✅ → You're ready for DMG build!"
echo ""
