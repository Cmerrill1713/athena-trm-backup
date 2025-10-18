#!/bin/bash
# Quick Frontend Test Script
# Launches app clean and provides validation checklist

echo "🎨 Swift Frontend Quick Test"
echo "============================"
echo ""

# Kill any stray instances
echo "🧹 Cleaning up..."
pkill -x NeuroForgeApp || true
sleep 1

# Launch fresh
echo "🚀 Launching NeuroForgeApp..."
/Users/christianmerrill/Library/Developer/Xcode/DerivedData/NeuroForgeApp-*/Build/Products/Debug/NeuroForgeApp &
APP_PID=$!
echo "   PID: $APP_PID"

# Wait for launch
echo "⏳ Waiting for app to initialize (3s)..."
sleep 3

# Check if running
if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✅ App is running"
else
    echo "❌ App failed to launch"
    exit 1
fi

echo ""
echo "================================"
echo "📋 MANUAL VALIDATION CHECKLIST"
echo "================================"
echo ""
echo "Find the NeuroForgeApp window and verify:"
echo ""
echo "1. ⌨️  Can you type immediately? (cursor blinking)"
echo "2. ⏎  Type 'Hello!' and press Enter"
echo "3. 👀 Did focus return to input after send?"
echo "4. ⌨️  Can you type again without clicking?"
echo "5. 🏷️  Do you see a latency badge in the header?"
echo ""
echo "If steps 3-4 work: ✅ FRONTEND IS FIXED!"
echo ""
echo "================================"
echo "📊 CONSOLE LOGS"
echo "================================"
echo ""
echo "To see focus events:"
echo "  open -a Console"
echo "  Filter by: com.neuroforge.athena"
echo "  Category: ui"
echo ""
echo "Expected logs on send:"
echo "  - Send tapped; length=X"
echo "  - Send complete; refocusing input"
echo ""
echo "================================"
echo "App PID: $APP_PID"
echo "To kill: pkill -x NeuroForgeApp"
echo "================================"

