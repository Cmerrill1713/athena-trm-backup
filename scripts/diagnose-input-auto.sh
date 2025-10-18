#!/usr/bin/env bash
set -euo pipefail

echo "🔍 AUTOMATED INPUT DIAGNOSTIC"
echo "=============================="
echo ""

# Clean slate
echo "1. Killing any running instances..."
pkill -9 -x NeuroForgeApp 2>/dev/null || true
sleep 2

# Start log capture in background
echo "2. Starting log capture..."
LOG_FILE="/tmp/neuroforge-diagnostic-$(date +%s).log"
log stream --predicate 'subsystem == "com.neuroforge.athena"' --level info > "$LOG_FILE" 2>&1 &
LOG_PID=$!
echo "   Log capture PID: $LOG_PID"
sleep 1

# Launch app
echo "3. Launching app..."
APP_PATH="/Users/christianmerrill/Library/Developer/Xcode/DerivedData/NeuroForgeApp-dylmcxgesfnrnxcdddijrrdsznam/Build/Products/Debug/NeuroForgeApp"
if [ ! -f "$APP_PATH" ]; then
    echo "❌ App not found at: $APP_PATH"
    echo "   Did you build it? Run: cd NeuroForgeApp && xcodebuild -scheme NeuroForgeApp build"
    exit 1
fi

"$APP_PATH" > /dev/null 2>&1 &
APP_PID=$!
echo "   App PID: $APP_PID"

# Wait for app to initialize
echo "4. Waiting for app to initialize (10 seconds)..."
sleep 10

# Check if window opened
echo "5. Checking if floating window exists..."
WINDOWS=$(osascript -e 'tell application "System Events" to get name of every window of process "NeuroForgeApp"' 2>/dev/null || echo "")
if [[ "$WINDOWS" == *"Floating Chat"* ]]; then
    echo "   ✅ Floating window detected!"
else
    echo "   ⚠️  Floating window NOT detected"
    echo "      Windows found: $WINDOWS"
fi

# Stop log capture
echo "6. Stopping log capture..."
kill $LOG_PID 2>/dev/null || true
sleep 1

# Analyze logs
echo ""
echo "=============================="
echo "📊 DIAGNOSTIC RESULTS"
echo "=============================="
echo ""

if [ ! -s "$LOG_FILE" ]; then
    echo "❌ NO LOGS CAPTURED"
    echo ""
    echo "This means OSLog isn't working or the subsystem is wrong."
    echo ""
    echo "FALLBACK: Check Console.app manually:"
    echo "  1. Open /Applications/Utilities/Console.app"
    echo "  2. Filter: com.neuroforge.athena"
    echo "  3. Look for logs with 🪟 👆 ✏️ emojis"
    echo ""
else
    echo "✅ Logs captured: $LOG_FILE"
    echo ""
    
    # Check key indicators
    WINDOW_CREATED=$(grep -c "🪟 Window created" "$LOG_FILE" 2>/dev/null || echo "0")
    IS_KEY_WINDOW=$(grep "isKeyWindow: true" "$LOG_FILE" 2>/dev/null || echo "NOT FOUND")
    CAN_BECOME_KEY=$(grep "canBecomeKey: true" "$LOG_FILE" 2>/dev/null || echo "NOT FOUND")
    MAKE_FIRST_RESPONDER=$(grep "makeFirstResponder: true" "$LOG_FILE" 2>/dev/null || echo "NOT FOUND")
    FIELD_CLICKED=$(grep -c "👆 Field clicked" "$LOG_FILE" 2>/dev/null || echo "0")
    TEXT_CHANGED=$(grep -c "✏️ Text changed" "$LOG_FILE" 2>/dev/null || echo "0")
    
    echo "Window Creation:"
    if [ "$WINDOW_CREATED" -gt 0 ]; then
        echo "  ✅ Window created ($WINDOW_CREATED times)"
    else
        echo "  ❌ Window NOT created"
    fi
    
    echo ""
    echo "Window State:"
    if [[ "$IS_KEY_WINDOW" == *"true"* ]]; then
        echo "  ✅ isKeyWindow: true"
    else
        echo "  ❌ isKeyWindow: false or not found"
    fi
    
    if [[ "$CAN_BECOME_KEY" == *"true"* ]]; then
        echo "  ✅ canBecomeKey: true"
    else
        echo "  ❌ canBecomeKey: false or not found"
    fi
    
    if [[ "$MAKE_FIRST_RESPONDER" == *"true"* ]]; then
        echo "  ✅ makeFirstResponder: true"
    else
        echo "  ❌ makeFirstResponder: false or not found"
    fi
    
    echo ""
    echo "User Interaction (Did YOU interact?):"
    if [ "$FIELD_CLICKED" -gt 0 ]; then
        echo "  ✅ Field was clicked ($FIELD_CLICKED times)"
    else
        echo "  ⚠️  Field NOT clicked (you need to click it!)"
    fi
    
    if [ "$TEXT_CHANGED" -gt 0 ]; then
        echo "  ✅ Typing worked! ($TEXT_CHANGED characters typed)"
    else
        echo "  ❌ NO typing detected"
    fi
    
    echo ""
    echo "=============================="
    echo ""
    
    # Diagnosis
    if [ "$TEXT_CHANGED" -gt 0 ]; then
        echo "🎉 SUCCESS! Typing is working!"
        echo ""
        echo "The input issue is FIXED. You can type in the floating window."
        echo ""
    elif [ "$FIELD_CLICKED" -eq 0 ]; then
        echo "⚠️  INCONCLUSIVE - No interaction detected"
        echo ""
        echo "The window opened but you didn't interact with it."
        echo ""
        echo "NEXT STEPS:"
        echo "  1. The app is still running (PID: $APP_PID)"
        echo "  2. Press Cmd+Shift+F to open floating window"
        echo "  3. Click in the text field"
        echo "  4. Try typing 'hello'"
        echo "  5. Run this script again to see if it captured the typing"
        echo ""
    else
        echo "❌ PROBLEM IDENTIFIED: Can click but can't type"
        echo ""
        echo "This is a keyboard input blocker."
        echo ""
        echo "MOST LIKELY FIX:"
        echo "  System Preferences → Security & Privacy → Privacy → Accessibility"
        echo "  Add 'NeuroForgeApp' and enable it"
        echo ""
        echo "ALSO CHECK:"
        echo "  - Input Monitoring permission"
        echo "  - Close any keyboard remapper apps (Karabiner, BTT, etc.)"
        echo "  - Close any screen recorders"
        echo ""
    fi
fi

echo "Full logs saved to: $LOG_FILE"
echo ""
echo "App is still running. To stop:"
echo "  kill $APP_PID"
echo ""

