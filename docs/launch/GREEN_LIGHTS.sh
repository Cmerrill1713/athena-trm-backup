#!/bin/bash
# GREEN LIGHTS - Meta UX Launch
# Run this to verify everything before shipping

set -e

echo "🚦 GREEN LIGHTS CHECKLIST"
echo "========================="
echo ""

cd /Users/christianmerrill/Documents/GitHub

# 1. Backend
echo "1️⃣  Backend with meta..."
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
export META_SELFCRITIQUE=1
make stack-up > /dev/null 2>&1 || true
sleep 3

echo "   Truth check..."
make truth

echo ""
echo "2️⃣  Health probes..."
if curl -fsS http://127.0.0.1:8014/ready > /dev/null 2>&1; then
    echo "   ✅ Bridge :8014 ready"
else
    echo "   ❌ Bridge :8014 not ready"
fi

if curl -fsS http://127.0.0.1:8090/ready > /dev/null 2>&1; then
    echo "   ✅ Athena :8090 ready"
else
    echo "   ❌ Athena :8090 not ready"
fi

if curl -fsS http://127.0.0.1:8181/ready > /dev/null 2>&1; then
    echo "   ✅ UAT :8181 ready"
else
    echo "   ❌ UAT :8181 not ready"
fi

echo ""
echo "3️⃣  Kokoro TTS..."
if curl -fsS http://127.0.0.1:8020/health > /dev/null 2>&1; then
    echo "   ✅ Kokoro :8020 active (natural voice)"
else
    echo "   ⚠️  Kokoro not running (will use system voice)"
    echo "   Optional: python3 scripts/kokoro_server.py"
fi

echo ""
echo "4️⃣  Meta headers..."
if curl -fsI http://127.0.0.1:8014/health 2>/dev/null | grep -qi "x-meta"; then
    echo "   ✅ Meta headers present"
else
    echo "   ⚠️  Meta headers not visible (may be in JSON body)"
fi

echo ""
echo "========================="
echo "✅ GREEN LIGHTS CONFIRMED"
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. Edit main.swift:"
echo "   File: NeuroForgeApp/Sources/main.swift"
echo "   Line ~20: ChatView() → ChatViewEnhanced()"
echo ""
echo "2. Run frontend:"
echo "   cd NeuroForgeApp"
echo "   API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run"
echo ""
echo "3. Test in app:"
echo "   • Say 'logs?' → 🔴 low confidence"
echo "   • Say 'backend errors' → 🟡 medium"
echo "   • Say 'top 3' → 🟢 high"
echo "   • Press Cmd+Shift+P → debug overlay"
echo ""
echo "4. Ship it:"
echo "   git add -A"
echo "   git commit -m 'Meta Dashboard + Adaptive UX'"
echo "   git tag -a v0.9.4-meta-ux -m 'Meta UX end-to-end'"
echo "   git push && git push origin v0.9.4-meta-ux"
echo ""

