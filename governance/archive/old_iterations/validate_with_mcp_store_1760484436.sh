#!/bin/bash
#
# Enhanced Validation Script with MCP Store Integration
# This validates all core services and stores results in MCP Store
#

set -e

MCPSTORE_URL=${MCPSTORE_URL:-"http://localhost:8411"}
CORRELATION_ID=${CORRELATION_ID:-"validate-$(date +%Y%m%d-%H%M%S)"}
GIT_COMMIT=${GIT_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")}

echo "🔍 NeuroForge Platform Validation"
echo "===================================="
echo "Correlation ID: $CORRELATION_ID"
echo "Git Commit:     $GIT_COMMIT"
echo "MCP Store:      $MCPSTORE_URL"
echo ""

# Check if MCP Store is available
if ! curl -sf "$MCPSTORE_URL/health" > /dev/null 2>&1; then
    echo "⚠️  MCP Store is not reachable - results will not be stored"
    echo "   Start with: make mcp-store-up"
    STORE_AVAILABLE=false
else
    echo "✅ MCP Store is available"
    STORE_AVAILABLE=true
fi
echo ""

# Function to store result
store_result() {
    local agent=$1
    local service=$2
    local status=$3
    local summary=$4
    local details=$5

    if [ "$STORE_AVAILABLE" = true ]; then
        curl -sS -X POST "$MCPSTORE_URL/v1/store/results" \
            -H "Content-Type: application/json" \
            -d "{
                \"agent\": \"$agent\",
                \"service\": \"$service\",
                \"status\": \"$status\",
                \"summary\": \"$summary\",
                \"details\": $details,
                \"commit\": \"$GIT_COMMIT\",
                \"correlation_id\": \"$CORRELATION_ID\"
            }" > /dev/null 2>&1 || true
    fi
}

# Test function
test_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}
    local expected_status=${4:-200}

    echo -n "Testing $service_name:$port... "

    start=$(date +%s%3N)
    status_code=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:$port$endpoint" 2>/dev/null || echo "000")
    latency=$(($(date +%s%3N) - start))

    if [ "$status_code" = "$expected_status" ]; then
        echo "✅ PASS (${latency}ms)"
        store_result "validation-script" "$service_name" "PASS" \
            "Health check passed" \
            "{\"port\": $port, \"endpoint\": \"$endpoint\", \"latency_ms\": $latency, \"status_code\": $status_code}"
        return 0
    else
        echo "❌ FAIL (expected $expected_status, got $status_code)"
        store_result "validation-script" "$service_name" "FAIL" \
            "Health check failed: expected $expected_status, got $status_code" \
            "{\"port\": $port, \"endpoint\": \"$endpoint\", \"latency_ms\": $latency, \"status_code\": $status_code}"
        return 1
    fi
}

# Track pass/fail counts
TOTAL=0
PASSED=0
FAILED=0

# Core Services
echo "📦 Core Services"
echo "----------------"

test_service "bridge" 8014 && ((PASSED++)) || ((FAILED++))
((TOTAL++))

test_service "athena" 8090 && ((PASSED++)) || ((FAILED++))
((TOTAL++))

test_service "uat" 8181 && ((PASSED++)) || ((FAILED++))
((TOTAL++))

echo ""

# Enhanced Services (optional)
echo "🚀 Enhanced Services (optional)"
echo "--------------------------------"

if lsof -i tcp:8020 -sTCP:LISTEN -t >/dev/null 2>&1; then
    test_service "kokoro-tts" 8020 && ((PASSED++)) || ((FAILED++))
    ((TOTAL++))
else
    echo "⏭️  kokoro-tts:8020 not running (optional)"
fi

if lsof -i tcp:8015 -sTCP:LISTEN -t >/dev/null 2>&1; then
    test_service "rag-service" 8015 && ((PASSED++)) || ((FAILED++))
    ((TOTAL++))
else
    echo "⏭️  rag-service:8015 not running (optional)"
fi

if lsof -i tcp:8016 -sTCP:LISTEN -t >/dev/null 2>&1; then
    test_service "vision-rag" 8016 && ((PASSED++)) || ((FAILED++))
    ((TOTAL++))
else
    echo "⏭️  vision-rag:8016 not running (optional)"
fi

echo ""

# Infrastructure Services
echo "🗄️  Infrastructure Services"
echo "----------------------------"

test_service "postgres" 5432 "/" 503 && ((PASSED++)) || ((FAILED++))
((TOTAL++))

test_service "redis" 6379 "/" 400 && ((PASSED++)) || ((FAILED++))
((TOTAL++))

if [ "$STORE_AVAILABLE" = true ]; then
    test_service "mcp-store" 8411 "/health" && ((PASSED++)) || ((FAILED++))
    ((TOTAL++))
fi

echo ""

# Summary
echo "===================================="
echo "📊 Validation Summary"
echo "===================================="
echo "Total Tests:  $TOTAL"
echo "Passed:       $PASSED ✅"
echo "Failed:       $FAILED ❌"
echo ""

# Store summary result
if [ "$STORE_AVAILABLE" = true ]; then
    summary_status="PASS"
    if [ $FAILED -gt 0 ]; then
        summary_status="FAIL"
    fi

    store_result "validation-script" "platform-overall" "$summary_status" \
        "Validation completed: $PASSED/$TOTAL passed" \
        "{\"total\": $TOTAL, \"passed\": $PASSED, \"failed\": $FAILED}"

    echo "📝 Results stored in MCP Store"
    echo "   View at: curl \"$MCPSTORE_URL/v1/store/results?correlation_id=$CORRELATION_ID\" | jq"
    echo ""
fi

# Exit code
if [ $FAILED -gt 0 ]; then
    echo "❌ Validation FAILED"
    exit 1
else
    echo "✅ Validation PASSED"
    exit 0
fi
