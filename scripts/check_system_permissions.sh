#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       🔍 SYSTEM-LEVEL DIAGNOSTIC - macOS PERMISSIONS 🔍        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check 1: Input Monitoring Permission
echo "1️⃣  INPUT MONITORING PERMISSION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "SELECT * FROM access WHERE service='kTCCServiceListenEvent'" 2>/dev/null | grep -q NeuroForge; then
    echo "✅ NeuroForgeApp has Input Monitoring permission"
else
    echo "❌ NeuroForgeApp DOES NOT have Input Monitoring permission"
    echo "   → This would block keyboard input!"
    echo "   → Fix: System Settings → Privacy & Security → Input Monitoring"
fi

echo ""

# Check 2: Accessibility Permission
echo "2️⃣  ACCESSIBILITY PERMISSION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "SELECT * FROM access WHERE service='kTCCServiceAccessibility'" 2>/dev/null | grep -q NeuroForge; then
    echo "✅ NeuroForgeApp has Accessibility permission"
else
    echo "⚠️  NeuroForgeApp may not have Accessibility permission"
    echo "   → This could interfere with keyboard input"
fi

echo ""

# Check 3: Other apps that might intercept keyboard
echo "3️⃣  POTENTIAL KEYBOARD INTERCEPTORS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

interceptors=(
    "Karabiner"
    "BetterTouchTool"
    "Alfred"
    "TextExpander"
    "Keyboard Maestro"
    "Hammerspoon"
)

for app in "${interceptors[@]}"; do
    if ps aux | grep -i "$app" | grep -v grep > /dev/null; then
        echo "⚠️  $app is running (may intercept keyboard)"
    fi
done

echo ""

# Check 4: Current app status
echo "4️⃣  NEUROFORGEAPP STATUS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ps aux | grep NeuroForgeApp | grep -v grep | grep -v tee > /dev/null; then
    echo "✅ NeuroForgeApp is running"
    ps aux | grep NeuroForgeApp | grep -v grep | grep -v tee | head -1
else
    echo "❌ NeuroForgeApp is NOT running"
fi

echo ""

# Check 5: Window Manager
echo "5️⃣  WINDOW MANAGEMENT:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null | grep -q "NeuroForgeApp"; then
    echo "✅ NeuroForgeApp is the frontmost app"
else
    echo "⚠️  NeuroForgeApp is NOT the frontmost app"
    echo "   Current frontmost:"
    osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null
fi

echo ""

# Check 6: Swift/Xcode version
echo "6️⃣  DEVELOPMENT ENVIRONMENT:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "macOS version: $(sw_vers -productVersion)"
echo "Xcode version: $(xcodebuild -version 2>/dev/null | head -1)"
echo "Swift version: $(swift --version | head -1)"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                       🎯 RECOMMENDATIONS                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "IF INPUT MONITORING = ❌:"
echo "  1. Open: System Settings → Privacy & Security → Input Monitoring"
echo "  2. Add NeuroForgeApp"
echo "  3. Toggle it ON"
echo "  4. Restart the app"
echo ""
echo "IF KEYBOARD INTERCEPTORS FOUND:"
echo "  1. Quit those apps temporarily"
echo "  2. Test NeuroForgeApp again"
echo ""
echo "IF APP NOT FRONTMOST:"
echo "  1. Click on the NeuroForgeApp window"
echo "  2. Make sure it's the active window"
echo "  3. Try typing again"
echo ""
echo "═══════════════════════════════════════════════════════════════════"

