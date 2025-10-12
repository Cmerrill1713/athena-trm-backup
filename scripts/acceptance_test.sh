#!/bin/bash
set -e

echo "🧪 Acceptance Test Suite"
echo "========================="
echo ""

# Configuration
BRIDGE_BASE=${BRIDGE_BASE:-http://127.0.0.1:8014}
UAT_BASE=${UAT_BASE:-http://127.0.0.1:8181}
ATHENA_BASE=${ATHENA_BASE:-http://127.0.0.1:8090}
UAT_TOKEN=${UAT_TOKEN:-supersecret}
ATH_TOKEN=${ATH_TOKEN:-supersecret}

PASSED=0
FAILED=0

# Test helper
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    local headers=$4

    echo -n "Testing $name... "

    if [ -n "$headers" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -H "$headers" "$url" 2>/dev/null || echo "000")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    fi

    if [ "$status" = "$expected_status" ]; then
        echo "✅ PASS (${status})"
        ((PASSED++))
    else
        echo "❌ FAIL (expected ${expected_status}, got ${status})"
        ((FAILED++))
    fi
}

# Test headers
test_headers() {
    local name=$1
    local url=$2
    local expected_header=$3
    local expected_value=$4

    echo -n "Testing $name... "

    value=$(curl -s -I "$url" 2>/dev/null | grep -i "^${expected_header}:" | cut -d: -f2- | tr -d '[:space:]')

    if [ "$value" = "$expected_value" ]; then
        echo "✅ PASS (${expected_header}: ${value})"
        ((PASSED++))
    else
        echo "❌ FAIL (expected ${expected_value}, got ${value})"
        ((FAILED++))
    fi
}

echo "🔍 1. Bridge Endpoints"
echo "----------------------"
test_endpoint "Bridge health" "$BRIDGE_BASE/health" "200"
test_endpoint "Bridge traces" "$BRIDGE_BASE/traces" "200"
test_endpoint "Bridge root" "$BRIDGE_BASE/" "200"

echo ""
echo "🔍 2. UAT Endpoints"
echo "-------------------"
test_endpoint "UAT health" "$UAT_BASE/health" "200" "Authorization: Bearer $UAT_TOKEN"
test_endpoint "UAT traces" "$UAT_BASE/traces" "200" "Authorization: Bearer $UAT_TOKEN"
test_endpoint "UAT auth required" "$UAT_BASE/traces" "401"

echo ""
echo "🔍 3. Athena Endpoints"
echo "----------------------"
test_endpoint "Athena health" "$ATHENA_BASE/health" "200" "Authorization: Bearer $ATH_TOKEN"
test_endpoint "Athena agents" "$ATHENA_BASE/agents" "200" "Authorization: Bearer $ATH_TOKEN"
test_endpoint "Athena auth required" "$ATHENA_BASE/agents" "401"

echo ""
echo "🔍 4. Observability Headers"
echo "---------------------------"
test_headers "Mode header" "$BRIDGE_BASE/health" "X-Mode" "real"
test_headers "Breaker header" "$BRIDGE_BASE/health" "X-Breaker" "closed"

echo ""
echo "🔍 5. Latency SLO"
echo "-----------------"
echo -n "Testing latency < 250ms... "
start=$(date +%s%N)
curl -s "$BRIDGE_BASE/traces" > /dev/null
end=$(date +%s%N)
latency_ms=$(( (end - start) / 1000000 ))

if [ $latency_ms -lt 250 ]; then
    echo "✅ PASS (${latency_ms}ms)"
    ((PASSED++))
else
    echo "❌ FAIL (${latency_ms}ms exceeds 250ms SLA)"
    ((FAILED++))
fi

echo ""
echo "🔍 6. Data Integrity"
echo "--------------------"
echo -n "Testing trace count... "
count=$(curl -s -H "Authorization: Bearer $UAT_TOKEN" "$UAT_BASE/traces" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")

if [ "$count" = "170" ]; then
    echo "✅ PASS (170 traces)"
    ((PASSED++))
else
    echo "⚠️  WARN (expected 170, got $count)"
fi

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║          Test Results                      ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "  Passed: $PASSED"
echo "  Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
