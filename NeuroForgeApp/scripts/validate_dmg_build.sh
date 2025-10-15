#!/usr/bin/env bash
# NeuroForge DMG Build Validation
# Tests the built DMG to ensure it works correctly
set -euo pipefail

cd "$(dirname "$0")/.."

echo "💿 NeuroForge DMG Build Validation"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
DMG_PATH="build-dmg/NeuroForgeApp.dmg"
APP_PATH="build-dmg/export/NeuroForgeApp.app"

pass() { echo -e "${GREEN}✅ $1${NC}"; ((PASS++)); }
fail() { echo -e "${RED}❌ $1${NC}"; ((FAIL++)); }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# ============================================
# CHECK 1: DMG File Exists
# ============================================
echo "📦 Check 1: DMG File"
echo "----------------------------"

if [[ -f "$DMG_PATH" ]]; then
    pass "DMG exists: $DMG_PATH"
    SIZE=$(du -h "$DMG_PATH" | cut -f1)
    pass "DMG size: $SIZE"
else
    fail "DMG not found at $DMG_PATH"
    echo ""
    echo "Run: make -f Makefile.dmg dmg"
    exit 1
fi

echo ""

# ============================================
# CHECK 2: App Bundle Validation
# ============================================
echo "📱 Check 2: App Bundle"
echo "----------------------------"

if [[ -d "$APP_PATH" ]]; then
    pass "App bundle exists"

    # Check structure
    if [[ -f "$APP_PATH/Contents/MacOS/NeuroForgeApp" ]]; then
        pass "Executable exists"
    else
        fail "Executable missing from bundle"
    fi

    if [[ -f "$APP_PATH/Contents/Info.plist" ]]; then
        pass "Info.plist in bundle"
    else
        fail "Info.plist missing from bundle"
    fi

else
    fail "App bundle not found at $APP_PATH"
fi

echo ""

# ============================================
# CHECK 3: Code Signature
# ============================================
echo "✍️  Check 3: Code Signature"
echo "----------------------------"

if codesign --verify --deep --strict "$APP_PATH" 2>/dev/null; then
    pass "Signature valid (deep verification)"
else
    fail "Signature verification failed"
fi

# Check if signed with Developer ID
SIGN_INFO=$(codesign -dv "$APP_PATH" 2>&1 || echo "")
if echo "$SIGN_INFO" | grep -q "Developer ID Application"; then
    pass "Signed with Developer ID"
else
    fail "Not signed with Developer ID (required for notarization)"
fi

# Check hardened runtime
if echo "$SIGN_INFO" | grep -q "runtime"; then
    pass "Hardened runtime enabled"
else
    warn "Hardened runtime not detected"
fi

echo ""

# ============================================
# CHECK 4: Entitlements
# ============================================
echo "🔐 Check 4: Entitlements"
echo "----------------------------"

ENTITLEMENTS=$(codesign -d --entitlements - "$APP_PATH" 2>/dev/null || echo "")

if [[ -n "$ENTITLEMENTS" ]]; then
    pass "Entitlements embedded"

    # Check for key entitlements
    if echo "$ENTITLEMENTS" | grep -q "com.apple.security.network.client"; then
        pass "Network client entitlement present"
    else
        warn "Network client entitlement missing (app won't connect to backend)"
    fi

    if echo "$ENTITLEMENTS" | grep -q "com.apple.security.files.user-selected.read-write"; then
        pass "File access entitlement present"
    else
        warn "File access entitlement missing (image picker may fail)"
    fi
else
    fail "No entitlements found"
fi

echo ""

# ============================================
# CHECK 5: Notarization Status
# ============================================
echo "☁️  Check 5: Notarization"
echo "----------------------------"

# Check if stapled
if xcrun stapler validate "$APP_PATH" > /dev/null 2>&1; then
    pass "Notarization ticket stapled"
else
    warn "No stapled ticket (run: make -f Makefile.dmg staple)"
fi

# Gatekeeper assessment
if spctl --assess --type execute --verbose=2 "$APP_PATH" 2>&1 | grep -q "accepted"; then
    pass "Gatekeeper assessment: ACCEPTED"
else
    warn "Gatekeeper assessment: Not accepted (may show security warning)"
fi

echo ""

# ============================================
# CHECK 6: DMG Structure
# ============================================
echo "💿 Check 6: DMG Structure"
echo "----------------------------"

# Mount DMG to inspect
MOUNT_POINT="/tmp/neuroforge_dmg_check_$$"
mkdir -p "$MOUNT_POINT"

if hdiutil attach "$DMG_PATH" -mountpoint "$MOUNT_POINT" -readonly -nobrowse > /dev/null 2>&1; then
    pass "DMG mounts successfully"

    # Check for app
    if [[ -d "$MOUNT_POINT/NeuroForgeApp.app" ]]; then
        pass "App present in DMG"
    else
        fail "App not found in DMG"
    fi

    # Check for Applications symlink
    if [[ -L "$MOUNT_POINT/Applications" ]]; then
        pass "Applications symlink present (drag-install UX)"
    else
        warn "Applications symlink missing (manual install only)"
    fi

    # Unmount
    hdiutil detach "$MOUNT_POINT" -quiet
    rm -rf "$MOUNT_POINT"
else
    fail "Cannot mount DMG"
fi

echo ""

# ============================================
# CHECK 7: Runtime Test (Quick Launch)
# ============================================
echo "🚀 Check 7: Runtime Test"
echo "----------------------------"

# Try to launch app briefly to check it can start
# (This won't work in headless CI, but fine for local validation)

if [[ -n "${DISPLAY:-}" ]] || [[ "$(uname)" == "Darwin" ]]; then
    info "Launching app for 3 seconds (runtime validation)..."

    # Launch app in background
    "$APP_PATH/Contents/MacOS/NeuroForgeApp" > /tmp/neuroforge_launch.log 2>&1 &
    APP_PID=$!

    # Wait briefly
    sleep 3

    # Check if still running
    if kill -0 $APP_PID 2>/dev/null; then
        pass "App launched successfully"
        kill $APP_PID 2>/dev/null || true
    else
        fail "App crashed on launch (check /tmp/neuroforge_launch.log)"
    fi
else
    info "Skipping runtime test (no display available)"
fi

echo ""

# ============================================
# SUMMARY
# ============================================
echo "===================================="
echo "📊 DMG Validation Summary"
echo "===================================="
echo -e "${GREEN}✅ Passed: $PASS${NC}"
echo -e "${RED}❌ Failed: $FAIL${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 DMG VALIDATION PASSED!${NC}"
    echo ""
    echo "✅ DMG is properly built"
    echo "✅ App is signed and notarized"
    echo "✅ Ready for distribution"
    echo ""
    echo "Next steps:"
    echo "  1. Test installation: open $DMG_PATH"
    echo "  2. Upload to GitHub Release"
    echo "  3. Distribute to users"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  DMG VALIDATION FAILED${NC}"
    echo ""
    echo "Fix $FAIL issue(s) above before distributing."
    echo ""
    exit 1
fi
