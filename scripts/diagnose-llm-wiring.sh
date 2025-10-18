#!/bin/bash
# LLM Wiring Diagnostic - Find why Swift app isn't calling Ollama

echo "🔍 LLM Wiring Diagnostic"
echo "======================="
echo ""

# 1. Check if LLM Gateway is running
echo "1️⃣  LLM Gateway (8015)..."
if curl -sf http://localhost:8015/health > /dev/null 2>&1; then
    echo "   ✅ Running"
    curl -s http://localhost:8015/health | jq .
else
    echo "   ❌ NOT RUNNING - Starting..."
    cd /Users/christianmerrill/Documents/GitHub
    python3 services/llm_gateway/app.py > /tmp/llm-gateway.log 2>&1 &
    sleep 3
fi
echo ""

# 2. Check if Ollama is reachable
echo "2️⃣  Ollama (11434)..."
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    models=$(curl -s http://localhost:11434/api/tags | jq -r '.models | length')
    echo "   ✅ Reachable ($models models)"
else
    echo "   ❌ NOT REACHABLE"
    echo "   Start with: ollama serve"
    exit 1
fi
echo ""

# 3. Test gateway → Ollama (prove it works)
echo "3️⃣  Gateway → Ollama test..."
response=$(curl -s -X POST http://localhost:8015/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Say TEST in one word."}]}')

if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    content=$(echo "$response" | jq -r '.choices[0].message.content')
    echo "   ✅ Response: $content"
    echo "   ✅ Gateway → Ollama chain WORKING"
else
    echo "   ❌ No response from gateway"
    echo "$response" | jq .
    exit 1
fi
echo ""

# 4. Check metrics (how many calls?)
echo "4️⃣  Gateway call count..."
calls=$(curl -s http://localhost:8015/metrics | grep llm_gateway_calls_total | grep -o '[0-9]\+\.[0-9]\+' | tail -1)
echo "   Total calls: $calls"
if [ "$calls" == "1.0" ]; then
    echo "   ⚠️  Only 1 call (from this script)"
    echo "   ❌ Swift app has NOT called gateway yet"
elif [ -z "$calls" ]; then
    echo "   ⚠️  No calls recorded"
else
    echo "   ✅ Multiple calls - Swift app may be calling"
fi
echo ""

# 5. Check if Swift app is running
echo "5️⃣  Swift app..."
app_count=$(ps aux | grep NeuroForgeApp | grep -v grep | wc -l | tr -d ' ')
if [ "$app_count" -gt 0 ]; then
    echo "   ✅ Running ($app_count instances)"
else
    echo "   ❌ NOT RUNNING"
    exit 1
fi
echo ""

# 6. Watch for incoming calls (live monitor)
echo "6️⃣  Live monitoring..."
echo "   Watching gateway logs for 10 seconds..."
echo "   Try typing in the Swift app NOW!"
echo ""
echo "   (Ctrl+C to stop)"
echo ""

timeout 10 tail -f /tmp/llm-gateway.log | grep --line-buffered "Chat request" || echo "   ⏱️  Timeout - no calls in 10 seconds"

echo ""
echo "================================"
echo "📊 Diagnostic Summary"
echo "================================"
echo "✅ LLM Gateway: Running on 8015"
echo "✅ Ollama: Reachable with $models models"
echo "✅ Gateway→Ollama: PROVEN WORKING"
echo "⚠️  Swift App: Running but NOT calling gateway"
echo ""
echo "🔧 Likely causes:"
echo "1. Swift app using old ChatService (not LLMGatewayService)"
echo "2. Swift app not rebuilt properly"
echo "3. Swift app crashed on startup"
echo "4. Swift app calling different endpoint"
echo ""
echo "🎯 Next steps:"
echo "1. Rebuild Swift app from scratch"
echo "2. Kill ALL instances and launch fresh"
echo "3. Check Swift Console for errors"
echo "4. Verify LLMGatewayService is being instantiated"

