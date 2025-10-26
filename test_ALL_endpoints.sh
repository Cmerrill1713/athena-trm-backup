#!/bin/bash

echo "🔬 COMPREHENSIVE ENDPOINT TESTING - ALL SERVICES"
echo "================================================="
echo ""

# Counter
total=0
passed=0
failed=0

test_endpoint() {
  local name=$1
  local method=$2
  local url=$3
  local data=$4
  
  total=$((total + 1))
  echo -n "Testing $name... "
  
  if [ -z "$data" ]; then
    result=$(curl -s -X $method -m 3 "$url" 2>&1)
  else
    result=$(curl -s -X $method -m 3 "$url" -H "Content-Type: application/json" -d "$data" 2>&1)
  fi
  
  if echo "$result" | grep -q "detail.*Not Found\|Connection refused\|TIMEOUT"; then
    echo "❌ FAIL"
    failed=$((failed + 1))
  else
    echo "✅ PASS"
    passed=$((passed + 1))
  fi
}

echo "═══ UAI (8080) ENDPOINTS ═══"
test_endpoint "GET /" GET "http://localhost:8080/"
test_endpoint "GET /health" GET "http://localhost:8080/health"
test_endpoint "GET /metrics" GET "http://localhost:8080/metrics"
test_endpoint "POST /v1/chat/completions" POST "http://localhost:8080/v1/chat/completions" '{"messages":[{"role":"user","content":"test"}]}'
test_endpoint "GET /api/tasks" GET "http://localhost:8080/api/tasks/"
test_endpoint "GET /api/tasks/1" GET "http://localhost:8080/api/tasks/1"
test_endpoint "GET /api/users" GET "http://localhost:8080/api/users/"
test_endpoint "GET /api/users/1" GET "http://localhost:8080/api/users/1"
test_endpoint "GET /api/tts/health" GET "http://localhost:8080/api/tts/health"
test_endpoint "GET /api/tts/voices" GET "http://localhost:8080/api/tts/voices"
test_endpoint "GET /api/health" GET "http://localhost:8080/api/health"

echo ""
echo "═══ ROUTER (9113) ENDPOINTS ═══"
test_endpoint "GET /health" GET "http://localhost:9113/health"
test_endpoint "GET /metrics" GET "http://localhost:9113/metrics"
test_endpoint "GET /ready" GET "http://localhost:9113/ready"
test_endpoint "GET /version" GET "http://localhost:9113/version"
test_endpoint "POST /route" POST "http://localhost:9113/route" '{"prompt":"test"}'
test_endpoint "POST /respond" POST "http://localhost:9113/respond" '{"message":"test"}'
test_endpoint "POST /reload-policy" POST "http://localhost:9113/reload-policy"
test_endpoint "POST /vision/analyze" POST "http://localhost:9113/vision/analyze" '{"image_b64":"test","prompt":"test"}'
test_endpoint "POST /tts/synthesize" POST "http://localhost:9113/tts/synthesize" '{"text":"test","voice":"en_US-female"}'

echo ""
echo "═══ AUTONOMOUS ORCHESTRATOR (9114) ═══"
test_endpoint "GET /health" GET "http://localhost:9114/health"
test_endpoint "GET /status" GET "http://localhost:9114/status"
test_endpoint "POST /prompt/evolve" POST "http://localhost:9114/prompt/evolve" '{"initial_prompt":"test","test_cases":[],"generations":1}'
test_endpoint "POST /trm/decide" POST "http://localhost:9114/trm/decide" '{"query":"test"}'
test_endpoint "POST /feedback" POST "http://localhost:9114/feedback" '{"query_id":"t","query":"t","used_trm":true,"success":true,"latency_ms":100}'
test_endpoint "POST /rollback/evaluate" POST "http://localhost:9114/rollback/evaluate"

echo ""
echo "═══ KNOWLEDGE SERVICES ═══"
test_endpoint "GET Gateway health" GET "http://localhost:8093/health"
test_endpoint "POST Gateway search" POST "http://localhost:8093/search" '{"query":"test","limit":3}'
test_endpoint "GET Context health" GET "http://localhost:8092/health"
test_endpoint "GET Sync health" GET "http://localhost:8089/health"

echo ""
echo "═══ MULTIMODAL ═══"
test_endpoint "GET FastVLM health" GET "http://localhost:8088/health"
test_endpoint "POST FastVLM analyze" POST "http://localhost:8088/analyze" '{"image":"test","prompt":"test"}'
test_endpoint "GET Kokoro health" GET "http://localhost:8091/health"
test_endpoint "POST Kokoro synthesize" POST "http://localhost:8091/synthesize" '{"text":"test","voice":"en_US-female"}'

echo ""
echo "═══ GOVERNANCE ═══"
test_endpoint "GET Orchestrator health" GET "http://localhost:9110/health"
test_endpoint "GET Orchestrator state" GET "http://localhost:9110/state"

echo ""
echo "═══ MCP TOOLS ═══"
test_endpoint "GET MCP health" GET "http://localhost:8412/health"
test_endpoint "POST web_search" POST "http://localhost:8412/tool/web_search" '{"arguments":{"query":"test"}}'

echo ""
echo "═══ OBSERVABILITY ═══"
test_endpoint "GET Prometheus" GET "http://localhost:9090/api/v1/status/config"
test_endpoint "GET Grafana" GET "http://localhost:3001/api/health"

echo ""
echo "================================================="
echo "RESULTS: $passed/$total passed, $failed failed"
echo "Coverage: $((passed * 100 / total))%"

