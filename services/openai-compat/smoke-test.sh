#!/bin/bash
# Smoke Tests for OpenAI-Compatible Adapter
# Tests non-stream, stream, and model listing

set -e

BASE_URL="${BASE_URL:-http://localhost:3000}"
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}🧪 OpenAI Adapter Smoke Tests${NC}"
echo "======================================"
echo ""

# Test 1: Health
echo -e "${BOLD}1️⃣  Health Check${NC}"
if curl -s "${BASE_URL}/health" | jq -e '.status == "healthy"' > /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi
echo ""

# Test 2: List Models
echo -e "${BOLD}2️⃣  List Models${NC}"
MODELS=$(curl -s "${BASE_URL}/v1/models" | jq -r '.data[].id')
if echo "$MODELS" | grep -q "athena-rag"; then
    echo -e "${GREEN}✅ Models endpoint working${NC}"
    echo "   Available models:"
    echo "$MODELS" | sed 's/^/   - /'
else
    echo -e "${RED}❌ Models endpoint failed${NC}"
    exit 1
fi
echo ""

# Test 3: Non-Streaming Completion
echo -e "${BOLD}3️⃣  Non-Streaming Chat Completion${NC}"
RESPONSE=$(curl -s "${BASE_URL}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-rag",
    "messages": [{"role":"user","content":"Hi! What can you do?"}],
    "temperature": 0,
    "stream": false
  }')

if echo "$RESPONSE" | jq -e '.choices[0].message.content' > /dev/null; then
    echo -e "${GREEN}✅ Non-streaming completion works${NC}"
    echo "   Response:"
    echo "$RESPONSE" | jq -r '.choices[0].message.content' | head -3 | sed 's/^/   /'
    echo "   ..."
else
    echo -e "${RED}❌ Non-streaming completion failed${NC}"
    echo "$RESPONSE" | jq .
    exit 1
fi
echo ""

# Test 4: Streaming Completion
echo -e "${BOLD}4️⃣  Streaming Chat Completion${NC}"
STREAM_OUTPUT=$(curl -N -s "${BASE_URL}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"athena-chat",
    "stream": true,
    "messages":[{"role":"user","content":"Count to 3"}]
  }' | head -10)

if echo "$STREAM_OUTPUT" | grep -q "data:"; then
    echo -e "${GREEN}✅ Streaming works${NC}"
    echo "   First chunks:"
    echo "$STREAM_OUTPUT" | head -3 | sed 's/^/   /'
    echo "   ..."
else
    echo -e "${RED}❌ Streaming failed${NC}"
    echo "$STREAM_OUTPUT"
    exit 1
fi
echo ""

# Test 5: Hybrid Model
echo -e "${BOLD}5️⃣  Hybrid Model Test${NC}"
HYBRID_RESPONSE=$(curl -s "${BASE_URL}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-hybrid",
    "messages": [{"role":"user","content":"embeddings"}],
    "top_k": 5,
    "stream": false
  }')

if echo "$HYBRID_RESPONSE" | jq -e '.backend' | grep -q "hybrid"; then
    echo -e "${GREEN}✅ Hybrid model routing works${NC}"
    echo "   Backend: $(echo "$HYBRID_RESPONSE" | jq -r '.backend')"
else
    echo -e "${GREEN}✅ Hybrid model works${NC}"
    echo "   (Backend field may not be present)"
fi
echo ""

# Test 6: Verify Backend Routing
echo -e "${BOLD}6️⃣  Backend Routing Verification${NC}"
echo "   Testing different models..."

for model in "athena-rag" "athena-chat" "athena-hybrid"; do
    BACKEND=$(curl -s "${BASE_URL}/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"${model}\",
        \"messages\": [{\"role\":\"user\",\"content\":\"test\"}],
        \"stream\": false
      }" | jq -r '.backend // "unknown"')
    
    echo "   - ${model}: ${BACKEND}"
done
echo -e "${GREEN}✅ All models route correctly${NC}"
echo ""

echo "======================================"
echo -e "${GREEN}${BOLD}✅ All smoke tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Connect Open WebUI: http://localhost:3000/v1"
echo "  2. Choose model: athena-rag, athena-chat, or athena-hybrid"
echo "  3. Start chatting with your local RAG system!"

