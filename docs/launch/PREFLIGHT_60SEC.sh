#!/bin/bash
# 60-Second Preflight - Meta UX Launch

set -e

echo "🚀 60-SECOND PREFLIGHT - META UX"
echo "================================="
echo ""

# Backend with meta
echo "1️⃣  Starting backend with meta features..."
cd /Users/christianmerrill/Documents/GitHub
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
export META_SELFCRITIQUE=1
export META_CHAINING=1

make stack-up
sleep 2

echo ""
echo "2️⃣  Truth check..."
make truth

echo ""
echo "3️⃣  Health check..."
curl -sf http://127.0.0.1:8014/health > /dev/null && echo "   ✅ Bridge healthy" || echo "   ⚠️  Bridge starting..."
curl -sf http://127.0.0.1:8090/health > /dev/null && echo "   ✅ Athena healthy" || echo "   ⚠️  Athena starting..."
curl -sf http://127.0.0.1:8181/health > /dev/null && echo "   ✅ UAT healthy" || echo "   ⚠️  UAT starting..."

echo ""
echo "4️⃣  Kokoro check..."
if curl -sf http://127.0.0.1:8020/health > /dev/null 2>&1; then
    echo "   ✅ Kokoro running"
else
    echo "   ⚠️  Kokoro not running (optional - will use system voice)"
    echo "   Start: python3 scripts/kokoro_server.py"
fi

echo ""
echo "================================="
echo "✅ BACKEND READY!"
echo ""
echo "5️⃣  NEXT STEPS:"
echo ""
echo "   A. Edit main.swift (ONE TIME):"
echo "      File: NeuroForgeApp/Sources/main.swift"
echo "      Line ~20:"
echo "      Change: ChatView() → ChatViewEnhanced()"
echo ""
echo "   B. Run frontend:"
echo "      cd NeuroForgeApp"
echo "      API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run"
echo ""
echo "   C. Test:"
echo "      • Say: 'logs?' → 🔴 low confidence"
echo "      • Say: 'backend errors' → 🟡 medium"
echo "      • Say: 'top 3' → 🟢 high"
echo "      • Press Cmd+Shift+P → debug overlay"
echo ""
echo "   D. Ship:"
echo "      git add -A"
echo "      git commit -m 'Meta Dashboard + Adaptive UX'"
echo "      git tag -a v0.9.4-meta-ux -m 'Meta UX end-to-end'"
echo "      git push && git push origin v0.9.4-meta-ux"
echo ""

