#!/bin/bash
# Contract Tests - Golden Path Validation
# Ensures all critical endpoints are operational
# Exit code 0 = all pass, non-zero = failure

set -e

echo "🧪 Running Contract Tests (Golden Path)"
echo "========================================"

PASS=0
FAIL=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    if response=$(curl -s -w "\n%{http_code}" "$url" 2>&1); then
        status_code=$(echo "$response" | tail -n 1)
        body=$(echo "$response" | sed '$d')
        
        if [ "$status_code" = "$expected_code" ]; then
            echo "✅ PASS (HTTP $status_code)"
            ((PASS++))
            return 0
        else
            echo "❌ FAIL (Expected $expected_code, got $status_code)"
            echo "   Response: $body"
            ((FAIL++))
            return 1
        fi
    else
        echo "❌ FAIL (Connection failed)"
        ((FAIL++))
        return 1
    fi
}

test_health_contains() {
    local name=$1
    local url=$2
    local expected_key=$3
    
    echo -n "Testing $name health... "
    
    if response=$(curl -s "$url" 2>&1); then
        if echo "$response" | jq -e ".$expected_key" > /dev/null 2>&1; then
            echo "✅ PASS (Contains .$expected_key)"
            ((PASS++))
            return 0
        else
            echo "❌ FAIL (Missing .$expected_key)"
            echo "   Response: $response"
            ((FAIL++))
            return 1
        fi
    else
        echo "❌ FAIL (Connection failed)"
        ((FAIL++))
        return 1
    fi
}

test_router_decision() {
    echo -n "Testing Router routing decision... "
    
    response=$(curl -s -X POST http://localhost:9113/route \
        -H 'Content-Type: application/json' \
        -d '{"query": "test routing", "max_tokens": 50}' 2>&1)
    
    if echo "$response" | jq -e '.model' > /dev/null 2>&1; then
        model=$(echo "$response" | jq -r '.model')
        echo "✅ PASS (Routed to: $model)"
        ((PASS++))
        return 0
    else
        echo "❌ FAIL (No model in response)"
        echo "   Response: $response"
        ((FAIL++))
        return 1
    fi
}

test_verdict_flow() {
    echo -n "Testing Verdict→ECE flow... "
    
    response=$(curl -s -X POST http://localhost:9110/verdict \
        -H 'Content-Type: application/json' \
        -d '{"task_id": "contract-test", "verdict": "PASS", "confidence": 0.95}' 2>&1)
    
    if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
        status=$(echo "$response" | jq -r '.status')
        if [ "$status" = "applied" ]; then
            echo "✅ PASS (Verdict applied)"
            ((PASS++))
            return 0
        else
            echo "❌ FAIL (Status: $status)"
            ((FAIL++))
            return 1
        fi
    else
        echo "❌ FAIL (No status in response)"
        echo "   Response: $response"
        ((FAIL++))
        return 1
    fi
}

# Core Service Health Checks
test_health_contains "Router" "http://localhost:9113/health" "status"
test_health_contains "AGI Core" "http://localhost:8000/health" "overall"
test_health_contains "Orchestrator" "http://localhost:9110/health" "status"
test_health_contains "MCP UI" "http://localhost:8412/health" "status"
test_health_contains "Bridge" "http://localhost:8014/health" "status"

# Monitoring Stack
test_endpoint "Prometheus" "http://localhost:9090/-/healthy" 200
test_endpoint "Grafana" "http://localhost:3001/api/health" 200

# Functional Tests
test_router_decision
test_verdict_flow

# Summary
echo ""
echo "========================================"
echo "📊 Test Results: $PASS passed, $FAIL failed"
echo "========================================"

if [ $FAIL -eq 0 ]; then
    echo "✅ All contract tests PASSED"
    exit 0
else
    echo "❌ $FAIL contract test(s) FAILED"
    exit 1
fi
