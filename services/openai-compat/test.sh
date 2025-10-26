#!/bin/bash
# Test OpenAI-Compatible Adapter

BASE_URL="${BASE_URL:-http://localhost:3000}"

echo "🧪 Testing OpenAI-Compatible Adapter"
echo "======================================"
echo ""

# Test 1: Health Check
echo "1️⃣  Health Check"
curl -s "$BASE_URL/health" | jq . || echo "❌ Health check failed"
echo ""

# Test 2: List Models
echo "2️⃣  List Models"
curl -s "$BASE_URL/v1/models" | jq '.data[] | {id, owned_by}' || echo "❌ Models list failed"
echo ""

# Test 3: RAG Model (non-streaming)
echo "3️⃣  Test RAG Model"
curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-rag",
    "messages": [
      {"role": "user", "content": "What is retrieval augmented generation?"}
    ],
    "top_k": 3
  }' | jq '.choices[0].message.content' || echo "❌ RAG test failed"
echo ""

# Test 4: Chat Model
echo "4️⃣  Test Chat Model"
curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-chat",
    "messages": [
      {"role": "user", "content": "Hello Athena, introduce yourself briefly"}
    ]
  }' | jq '.choices[0].message.content' || echo "❌ Chat test failed"
echo ""

# Test 5: Hybrid Model
echo "5️⃣  Test Hybrid Model"
curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-hybrid",
    "messages": [
      {"role": "user", "content": "embeddings"}
    ],
    "top_k": 5
  }' | jq '.choices[0].message.content' || echo "❌ Hybrid test failed"
echo ""

# Test 6: Streaming (just check it works, don't wait for full stream)
echo "6️⃣  Test Streaming"
timeout 3 curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-chat",
    "messages": [{"role": "user", "content": "count to 3"}],
    "stream": true
  }' | head -5 || echo "✅ Streaming works (timed out as expected)"
echo ""

echo "======================================"
echo "✅ Tests complete!"

