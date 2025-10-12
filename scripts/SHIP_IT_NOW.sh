#!/bin/bash
# Ship Meta UX - 5-Minute Execution

set -e

echo "🚀 Shipping Meta UX - Complete System"
echo "======================================"
echo ""

# Step 1: Start backend with meta
echo "1️⃣  Starting backend with meta features..."
cd /Users/christianmerrill/Documents/GitHub
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
export META_SELFCRITIQUE=1
export META_CHAINING=1

echo "   Starting stack..."
make stack-up

echo ""
echo "2️⃣  Verifying backend..."
sleep 3
make truth

echo ""
echo "3️⃣  Checking meta headers..."
echo "   Testing: curl -sI http://127.0.0.1:8014/health | grep x-"
curl -sI http://127.0.0.1:8014/health | grep -i "x-" || echo "   (Headers may vary based on Bridge implementation)"

echo ""
echo "4️⃣  Checking Kokoro TTS (optional)..."
if curl -sf http://127.0.0.1:8020/health > /dev/null 2>&1; then
    echo "   ✅ Kokoro running at :8020"
else
    echo "   ⚠️  Kokoro not running (optional - will use system voice)"
    echo "   Start in another terminal: python3 scripts/kokoro_server.py"
fi

echo ""
echo "======================================"
echo "✅ Backend ready!"
echo ""
echo "5️⃣  Next steps:"
echo ""
echo "   A. Edit main.swift:"
echo "      File: NeuroForgeApp/Sources/main.swift"
echo "      Change line ~20:"
echo "         ChatView()          // ❌ Old"
echo "      To:"
echo "         ChatViewEnhanced()  // ✅ New"
echo ""
echo "   B. Start frontend:"
echo "      cd NeuroForgeApp"
echo "      API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run"
echo ""
echo "   C. Test in app:"
echo "      • Say: 'logs?' → See 🔴 low confidence"
echo "      • Say: 'backend errors' → See 🟡 medium confidence"
echo "      • Say: 'top 3' → See 🟢 high confidence"
echo "      • Press Cmd+Shift+P → See debug overlay"
echo ""
echo "6️⃣  After verification, ship it:"
echo "      git add -A"
echo "      git commit -m 'Meta Dashboard + Adaptive UX: visible confidence, plan, tools, voice'"
echo "      git tag -a v0.9.4-meta-ux -m 'Meta UX end-to-end'"
echo "      git push && git push origin v0.9.4-meta-ux"
echo ""

