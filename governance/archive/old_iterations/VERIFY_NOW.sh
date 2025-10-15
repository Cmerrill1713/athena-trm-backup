#!/bin/bash
# 5-Minute End-to-End Verification

set -e

echo "🧪 Athena Complete System Verification"
echo "======================================"
echo ""

# Step 1: Backend with meta enabled
echo "1️⃣  Starting backend with meta features..."
cd /Users/christianmerrill/Documents/GitHub
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
export META_SELFCRITIQUE=1
make stack-up

echo ""
echo "2️⃣  Verifying backend health..."
sleep 2
make truth

echo ""
echo "3️⃣  Testing meta headers..."
curl -si http://127.0.0.1:8014/health | head -20

echo ""
echo "4️⃣  Checking Kokoro TTS..."
if curl -sf http://127.0.0.1:8020/health > /dev/null 2>&1; then
    echo "✅ Kokoro running at :8020"
else
    echo "⚠️  Kokoro not running (optional - will use system voice)"
    echo "   Start with: python3 scripts/kokoro_server.py"
fi

echo ""
echo "======================================"
echo "✅ Backend ready!"
echo ""
echo "5️⃣  Now start frontend:"
echo "   cd NeuroForgeApp"
echo "   # Edit Sources/main.swift: ChatView() → ChatViewEnhanced()"
echo "   API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run"
echo ""
echo "6️⃣  In the app:"
echo "   • Click mic, say: 'run smoke tests and summarize failures'"
echo "   • You should hear: 'I'm X% confident. Plan: ...'"
echo "   • You should see meta panel with confidence + plan"
echo ""
echo "7️⃣  Test debug overlay:"
echo "   • Press Cmd+Shift+P to see prompt rewrites"
echo ""
echo "8️⃣  Test CLI voice (parallel):"
echo "   • ./athena_voice.sh"
echo "   • Say: 'run tests'"
echo ""

