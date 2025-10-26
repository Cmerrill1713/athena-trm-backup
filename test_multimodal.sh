#!/bin/bash

echo "🎨 Testing Multimodal Services"
echo "==============================="
echo ""

# Test 1: FastVLM Vision
echo "1️⃣ Testing FastVLM (Vision Analysis)"
echo "-----------------------------------"

# Create a tiny test image (1x1 red pixel PNG in base64)
TEST_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

curl -s http://localhost:8088/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"image\": \"$TEST_IMAGE\",
    \"prompt\": \"What do you see in this image?\",
    \"max_tokens\": 100
  }" | jq '.'

echo ""
echo "2️⃣ Testing Kokoro TTS (Text-to-Speech)"
echo "---------------------------------------"

# Read Kokoro server to find endpoints
if [ -f services/kokoro/server.py ]; then
  echo "📄 Kokoro endpoints:"
  grep -E "@app\.(get|post)" services/kokoro/server.py | head -5
else
  echo "⚠️  Kokoro source not found, trying API discovery..."
fi

curl -s http://localhost:8091/health | jq '.'

echo ""
echo "3️⃣ Testing Available Kokoro Endpoints"
echo "--------------------------------------"

# Try common TTS endpoints
for endpoint in "/synthesize" "/tts" "/speak" "/generate"; do
  echo -n "Testing $endpoint: "
  result=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8091$endpoint 2>/dev/null)
  if [ "$result" != "404" ]; then
    echo "✅ Exists (HTTP $result)"
  else
    echo "❌ Not found"
  fi
done

echo ""
echo "================================="
echo "✅ Multimodal services test complete"
