#!/bin/bash
#
# Quick integration test for MCP Store
# This verifies the full stack is working end-to-end
#

set -e

MCPSTORE_URL=${MCPSTORE_URL:-"http://localhost:8411"}
CORRELATION_ID="test-$(date +%s)"

echo "🧪 MCP Store Integration Test"
echo "================================"
echo ""

# 1. Health check
echo "1️⃣  Testing health endpoint..."
curl -sf "$MCPSTORE_URL/health" > /dev/null || {
    echo "❌ MCP Store is not reachable at $MCPSTORE_URL"
    echo "   Start it with: make mcp-store-up"
    exit 1
}
echo "✅ Health check passed"
echo ""

# 2. Write a PASS result
echo "2️⃣  Writing PASS result..."
PASS_RESULT=$(curl -sS -X POST "$MCPSTORE_URL/v1/store/results" \
    -H "Content-Type: application/json" \
    -d "{
        \"agent\": \"integration-test\",
        \"service\": \"test-service\",
        \"status\": \"PASS\",
        \"summary\": \"Test passed successfully\",
        \"details\": {\"test\": \"integration\", \"duration_ms\": 123},
        \"commit\": \"v0.1.0\",
        \"correlation_id\": \"$CORRELATION_ID\"
    }")

PASS_ID=$(echo "$PASS_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✅ Created result with ID: $PASS_ID"
echo ""

# 3. Write a FAIL result
echo "3️⃣  Writing FAIL result..."
FAIL_RESULT=$(curl -sS -X POST "$MCPSTORE_URL/v1/store/results" \
    -H "Content-Type: application/json" \
    -d "{
        \"agent\": \"integration-test\",
        \"service\": \"test-service\",
        \"status\": \"FAIL\",
        \"summary\": \"Test failed\",
        \"details\": {\"error\": \"Connection timeout\", \"duration_ms\": 5000},
        \"commit\": \"v0.1.0\",
        \"correlation_id\": \"$CORRELATION_ID\"
    }")

FAIL_ID=$(echo "$FAIL_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✅ Created result with ID: $FAIL_ID"
echo ""

# 4. Retrieve by ID
echo "4️⃣  Retrieving result by ID..."
RETRIEVED=$(curl -sS "$MCPSTORE_URL/v1/store/results/$PASS_ID")
RETRIEVED_STATUS=$(echo "$RETRIEVED" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")

if [ "$RETRIEVED_STATUS" = "PASS" ]; then
    echo "✅ Retrieved result matches: $RETRIEVED_STATUS"
else
    echo "❌ Retrieved result mismatch: expected PASS, got $RETRIEVED_STATUS"
    exit 1
fi
echo ""

# 5. List results
echo "5️⃣  Listing recent results..."
LIST_RESULT=$(curl -sS "$MCPSTORE_URL/v1/store/results?limit=10")
COUNT=$(echo "$LIST_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "✅ Found $COUNT results"
echo ""

# 6. Filter by status
echo "6️⃣  Filtering by status=FAIL..."
FAIL_LIST=$(curl -sS "$MCPSTORE_URL/v1/store/results?status=FAIL&limit=5")
FAIL_COUNT=$(echo "$FAIL_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "✅ Found $FAIL_COUNT failures"
echo ""

# 7. Filter by service
echo "7️⃣  Filtering by service=test-service..."
SERVICE_LIST=$(curl -sS "$MCPSTORE_URL/v1/store/results?service=test-service&limit=5")
SERVICE_COUNT=$(echo "$SERVICE_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "✅ Found $SERVICE_COUNT results for test-service"
echo ""

# Summary
echo "================================"
echo "✅ All integration tests passed!"
echo ""
echo "📊 View results:"
echo "   curl \"$MCPSTORE_URL/v1/store/results?correlation_id=$CORRELATION_ID\" | jq"
echo ""
echo "🎉 MCP Store is fully operational!"

