#!/usr/bin/env bash
# Contract Tests - Catch config drift immediately
set -e

echo "🔍 ATHENA CONTRACT TESTS"
echo "========================"

check() { 
    name=$1 
    url=$2 
    expect=$3
    echo "[$name] $url"
    if curl -fsS "$url" | grep -qi "$expect"; then
        echo "✅ $name: OK"
    else
        echo "❌ $name: FAIL"
        exit 1
    fi
}

# Health checks
check "health_router"   "http://localhost:9113/health" "healthy"
check "health_gov"      "http://localhost:9110/health" "healthy"
check "health_mcp"      "http://localhost:8412/health" "healthy"
check "health_vlm"      "http://localhost:8088/health" "healthy"
check "health_tts"      "http://localhost:8091/health" "healthy"

echo
echo "🧪 FUNCTIONAL TESTS"
echo "==================="

# Intent smoke
echo "[intent] Testing deterministic responses..."
response=$(curl -s -X POST localhost:9113/respond -H 'content-type: application/json' \
  -d '{"message":"Can you see any issues with ourself"}' | jq -r '.response')
if echo "$response" | grep -qi "Which area"; then
    echo "✅ Intent routing: OK"
else
    echo "❌ Intent routing: FAIL (got: $response)"
    exit 1
fi

# Golden test cases
echo "[golden] Testing 'How are you?' response..."
response=$(curl -s -X POST localhost:9113/respond -H 'content-type: application/json' \
  -d '{"message":"How are you?"}' | jq -r '.response')
if echo "$response" | grep -qi "Running fine"; then
    echo "✅ Golden case 1: OK"
else
    echo "❌ Golden case 1: FAIL (got: $response)"
    exit 1
fi

echo "[golden] Testing 'Can you see any issues with ourself' response..."
response=$(curl -s -X POST localhost:9113/respond -H 'content-type: application/json' \
  -d '{"message":"Can you see any issues with ourself"}' | jq -r '.response')
if echo "$response" | grep -qi "Which area—infra"; then
    echo "✅ Golden case 2: OK"
else
    echo "❌ Golden case 2: FAIL (got: $response)"
    exit 1
fi

# Bridge to UAT test
echo "[bridge] Testing Bridge → UAT flow..."
response=$(curl -s -X POST localhost:8098/api/chat -H 'content-type: application/json' \
  -d '{"session_id":"test","messages":[{"role":"user","content":"test"}]}' | jq -r '.reply')
if [ -n "$response" ] && [ "$response" != "null" ]; then
    echo "✅ Bridge → UAT: OK"
else
    echo "❌ Bridge → UAT: FAIL (got: $response)"
    exit 1
fi

# Multimodal tests
echo "[vision] Testing vision service..."
vision_response=$(curl -s -X POST localhost:9113/vision/analyze -H 'content-type: application/json' \
  -d '{"image_b64":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==","prompt":"test"}' | jq -r '.result.caption')
if [ -n "$vision_response" ] && [ "$vision_response" != "null" ]; then
    echo "✅ Vision: OK"
else
    echo "❌ Vision: FAIL (got: $vision_response)"
    exit 1
fi

echo "[tts] Testing TTS service..."
tts_response=$(curl -s -X POST localhost:9113/tts/synthesize -H 'content-type: application/json' \
  -d '{"text":"test"}' | jq -r '.audio_b64')
if [ -n "$tts_response" ] && [ "$tts_response" != "null" ]; then
    echo "✅ TTS: OK"
else
    echo "❌ TTS: FAIL (got: $tts_response)"
    exit 1
fi

echo
echo "🎉 ALL CONTRACT TESTS PASSED"
echo "============================="
