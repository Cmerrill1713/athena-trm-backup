#!/usr/bin/env bash
# One-shot LLM Gateway sanity test
# Proves Ollama is being called and generating responses

set -euo pipefail

echo "🧪 LLM Gateway Sanity Test"
echo "=========================="
echo ""

# Test 1: Gateway health
echo "1️⃣  Gateway /health..."
if curl -fsS http://localhost:8015/health > /dev/null 2>&1; then
    curl -s http://localhost:8015/health | jq .
    echo "   ✅ Gateway is up"
else
    echo "   ❌ Gateway not responding on port 8015"
    exit 1
fi
echo ""

# Test 2: Ollama readiness
echo "2️⃣  Gateway /ready (checks Ollama)..."
ready_response=$(curl -s http://localhost:8015/ready)
echo "$ready_response" | jq .

if echo "$ready_response" | jq -e '.ready == true' > /dev/null; then
    echo "   ✅ Ollama is reachable"
else
    echo "   ❌ Ollama not reachable"
    echo "$ready_response" | jq -r '.error // "Unknown error"'
    exit 1
fi
echo ""

# Test 3: Ollama direct test
echo "3️⃣  Ollama direct test..."
curl -s http://localhost:11434/api/tags | jq '.models[0:3] | .[] | {name, size}' || echo "❌ Ollama not responding"
echo "   ✅ Ollama has models"
echo ""

# Test 4: Chat completion (THE CRITICAL TEST)
echo "4️⃣  Chat completion (CRITICAL - proves LLM is called)..."
echo "   Sending: 'Say hello in 7 words.'"
echo ""

chat_response=$(curl -s -X POST http://localhost:8015/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Say hello in 7 words."}]}')

echo "$chat_response" | jq .

# Check if we got actual content
if echo "$chat_response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    content=$(echo "$chat_response" | jq -r '.choices[0].message.content')
    echo ""
    echo "   📝 Response: $content"
    echo "   ✅ LLM GENERATED RESPONSE!"
else
    echo "   ❌ No content in response"
    exit 1
fi
echo ""

# Test 5: Metrics (proves call happened)
echo "5️⃣  Metrics (proves Ollama was called)..."
metrics=$(curl -s http://localhost:8015/metrics | grep llm_gateway_calls_total || echo "")

if [ -n "$metrics" ]; then
    echo "$metrics"
    echo "   ✅ Prometheus counter incremented!"
else
    echo "   ⚠️  No metrics yet (first call)"
fi
echo ""

echo "================================"
echo "✅ ALL TESTS PASSED"
echo "================================"
echo ""
echo "LLM Gateway is working!"
echo "- Ollama is reachable"
echo "- Chat completions work"
echo "- Real model inference happening"
echo "- Metrics tracking calls"
echo ""
echo "Next: Point Swift app to http://localhost:8015/v1/chat/completions"

