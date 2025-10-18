#!/bin/bash
# Ultimate validation - proves LLM + Frontend both work
# Run this to verify the complete system

echo "🎯 ULTIMATE VALIDATION - LLM + FRONTEND"
echo "========================================"
echo ""

# Kill old instances
echo "🧹 Cleaning up..."
pkill -x NeuroForgeApp || true
sleep 1

# Ensure gateway is running
echo "🚀 Starting LLM Gateway..."
if ! curl -sf http://localhost:8015/health > /dev/null 2>&1; then
    python3 services/llm_gateway/app.py > /tmp/llm-gateway.log 2>&1 &
    sleep 3
fi

if curl -sf http://localhost:8015/health > /dev/null 2>&1; then
    echo "   ✅ Gateway running on 8015"
else
    echo "   ❌ Gateway failed to start"
    exit 1
fi
echo ""

# Launch app
echo "🎨 Launching NeuroForgeApp..."
/Users/christianmerrill/Library/Developer/Xcode/DerivedData/NeuroForgeApp-*/Build/Products/Debug/NeuroForgeApp &
APP_PID=$!
sleep 3

if ps -p $APP_PID > /dev/null 2>&1; then
    echo "   ✅ App running (PID: $APP_PID)"
else
    echo "   ❌ App failed to launch"
    exit 1
fi
echo ""

# Instructions
echo "================================"
echo "📋 VALIDATION INSTRUCTIONS"
echo "================================"
echo ""
echo "STEP 1: Watch metrics in another terminal:"
echo "  watch -n 1 'curl -s localhost:8015/metrics | grep llm_gateway_calls_total'"
echo ""
echo "STEP 2: In the app window:"
echo "  Press: Cmd+Shift+P (Ping LLM Gateway)"
echo "  OR type a message and press Enter"
echo ""
echo "STEP 3: Watch this terminal for:"
echo "  🚀🚀🚀 LLMGatewayService initialized"
echo "  📍 Gateway URL: http://127.0.0.1:8015"
echo "  🔑 keyDown events when you type"
echo "  📨 ChatInputVM.submit() when you press Enter"
echo "  📤 SEND from inputVM"
echo "  🌐 Calling gateway"
echo "  ✅ LLM reply received"
echo ""
echo "STEP 4: Watch metrics terminal:"
echo "  Counter should increment from 1.0 → 2.0 → 3.0"
echo ""
echo "================================"
echo "🔍 DIAGNOSTIC TRUTH TABLE"
echo "================================"
echo ""
echo "IF YOU SEE:"
echo ""
echo "✅ 🔑 keyDown events → Keys reach window"
echo "❌ No 🔑 → Window not key, run: NSApp.windows.first?.makeKeyAndOrderFront(nil)"
echo ""
echo "✅ 📨 ChatInputVM.submit() → Input submit() called"
echo "❌ No 📨 → StickyTextField not forwarding Enter, check delegate"
echo ""
echo "✅ 📤 SEND from inputVM → Wire-up working"
echo "❌ No 📤 → onSend handler not set, check .onAppear"
echo ""
echo "✅ 🌐 Calling gateway → Network call made"
echo "❌ No 🌐 → sendMessage() not awaiting, check async chain"
echo ""
echo "✅ Metrics increment → Gateway received request"
echo "❌ Metrics stuck → Wrong URL or ATS blocking"
echo ""
echo "================================"
echo "App PID: $APP_PID"
echo "Gateway: http://localhost:8015/metrics"
echo "Logs: tail -f /tmp/llm-gateway.log"
echo "================================"

