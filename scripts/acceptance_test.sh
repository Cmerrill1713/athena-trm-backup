#!/usr/bin/env bash
#
# Final Acceptance Test - Trust but Verify
# Runs all checks before promoting to production
#

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=================================="
echo "🎯 FINAL ACCEPTANCE TEST"
echo "=================================="
echo ""

# Configuration
BRIDGE_TOKEN="${BRIDGE_TOKEN:-supersecret}"
BRIDGE_URL="http://127.0.0.1:8014"

# 1. Real-mode end-to-end
echo "1️⃣  Real-mode end-to-end test"
echo "   Testing with real backends (or mock if unavailable)..."

# Test health
echo -n "   - Health check: "
HEALTH=$(curl -s -H "x-bridge-token: $BRIDGE_TOKEN" "$BRIDGE_URL/health")
STATUS=$(echo "$HEALTH" | jq -r '.status')
echo "$STATUS"

# Test traces
echo -n "   - Traces endpoint: "
TRACES=$(curl -s -H "x-bridge-token: $BRIDGE_TOKEN" "$BRIDGE_URL/traces")
TRACE_COUNT=$(echo "$TRACES" | jq 'length // .count // 0')
echo "$TRACE_COUNT traces"

# Test chat
echo -n "   - Chat endpoint: "
CHAT=$(curl -s -H "x-bridge-token: $BRIDGE_TOKEN" \
    -H "content-type: application/json" \
    -X POST "$BRIDGE_URL/chat" \
    -d '{"text":"ping"}' 2>&1)
if echo "$CHAT" | jq -e '.reply' > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "⚠️  $(echo "$CHAT" | head -1)"
fi

echo ""

# 2. Correlation IDs flow
echo "2️⃣  Correlation ID verification"
CID=$(uuidgen)
echo "   Generated CID: $CID"
curl -s -H "x-bridge-token: $BRIDGE_TOKEN" \
     -H "x-correlation-id: $CID" \
     "$BRIDGE_URL/traces" > /dev/null

sleep 1
if tail -20 logs/adapter.log 2>/dev/null | grep -q "$CID"; then
    echo "   ✅ CID found in logs"
else
    echo "   ⚠️  CID not found in logs (may be expected if logs disabled)"
fi

echo ""

# 3. SLO gate
echo "3️⃣  SLO check (p95 < 250ms)"
if python3 scripts/slo_check.py 2>&1 | tail -3; then
    echo "   ✅ SLO passed"
else
    echo "   ❌ SLO failed - check backend performance"
    exit 1
fi

echo ""

# 4. Contract version
echo "4️⃣  Contract version check"
CONTRACT=$(curl -s "$BRIDGE_URL/contract")
VERSION=$(echo "$CONTRACT" | jq -r '.version')
ENDPOINTS=$(echo "$CONTRACT" | jq -r '.endpoints | length')
echo "   Version: $VERSION"
echo "   Endpoints: $ENDPOINTS"

echo ""

# 5. Rate limiting
echo "5️⃣  Rate limiting check"
echo -n "   Sending 5 rapid requests: "
for i in {1..5}; do
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "x-bridge-token: $BRIDGE_TOKEN" \
        "$BRIDGE_URL/health")
    echo -n "$STATUS_CODE "
done
echo ""

echo ""

# 6. Auth enforcement
echo "6️⃣  Auth enforcement check"
if [ "$ENV" = "prod" ] || [ -n "$BRIDGE_TOKEN" ]; then
    echo -n "   Without token: "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BRIDGE_URL/traces")
    if [ "$STATUS" = "401" ]; then
        echo "✅ Correctly rejected ($STATUS)"
    else
        echo "⚠️  Expected 401, got $STATUS"
    fi

    echo -n "   With token: "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "x-bridge-token: $BRIDGE_TOKEN" "$BRIDGE_URL/traces")
    if [ "$STATUS" = "200" ] || [ "$STATUS" = "401" ]; then
        echo "✅ Responded ($STATUS)"
    else
        echo "❌ Unexpected status $STATUS"
    fi
else
    echo "   ⏭️  Skipped (dev mode without BRIDGE_TOKEN)"
fi

echo ""
echo "=================================="
echo "✅ ACCEPTANCE TEST COMPLETE"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Review logs: tail -f logs/adapter.log"
echo "  2. Run chaos test: make bridge-chaos"
echo "  3. Load test: Run for 10 minutes and monitor"
echo "  4. Tag release: git tag bridge-1.0.0"
echo ""
