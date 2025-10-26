#!/bin/bash
# Integration Smoke Tests - Quick sanity checks for AGI + RAG + TRM integration

set -e

echo "════════════════════════════════════════════════════════════════════════"
echo "  INTEGRATION SMOKE TESTS"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

PASSED=0
FAILED=0

# Helper functions
test_pass() {
    echo "✓ $1"
    ((PASSED++))
}

test_fail() {
    echo "✗ $1"
    ((FAILED++))
}

# Test 1: RAG Gateway /kb/search endpoint
echo "1. Testing RAG Gateway /kb/search..."
if curl -sf http://localhost:8088/kb/search \
    -H "Content-Type: application/json" \
    -d '{"query":"test","topK":1,"mode":"nearText"}' > /dev/null 2>&1; then
    test_pass "RAG Gateway /kb/search responding"
else
    test_fail "RAG Gateway /kb/search not responding"
fi

# Test 2: KB Search returns valid JSON
echo "2. Testing KB Search response format..."
RESPONSE=$(curl -s http://localhost:8088/kb/search \
    -H "Content-Type: application/json" \
    -d '{"query":"test","topK":1,"mode":"nearText"}')

if echo "$RESPONSE" | jq -e '.hits' > /dev/null 2>&1; then
    test_pass "KB Search returns valid JSON with hits"
else
    test_fail "KB Search response invalid"
fi

# Test 3: RAG Router service accessible
echo "3. Testing RAG Router..."
if python3 -c "from services.router.rag_router import RAGRouter; print('OK')" 2>/dev/null | grep -q "OK"; then
    test_pass "RAG Router module loads"
else
    test_fail "RAG Router module failed to load"
fi

# Test 4: AGI Tools module accessible
echo "4. Testing AGI Tools (KB Search)..."
if python3 -c "from agi_core.tools import kb_search; print('OK')" 2>/dev/null | grep -q "OK"; then
    test_pass "AGI KB Search tool loads"
else
    test_fail "AGI KB Search tool failed to load"
fi

# Test 5: Unified Metrics service
echo "5. Testing Unified Metrics..."
if curl -sf http://localhost:8092/health > /dev/null 2>&1; then
    test_pass "Unified Metrics service responding"
else
    test_fail "Unified Metrics service not responding (start with 'make unified-metrics')"
fi

# Test 6: Training pipeline script exists
echo "6. Testing TRM Training Pipeline..."
if [ -f "scripts/trm_rag_training_pipeline.py" ]; then
    test_pass "TRM Training Pipeline script exists"
else
    test_fail "TRM Training Pipeline script not found"
fi

# Test 7: Integration Makefile targets
echo "7. Testing Integration Makefile..."
if make -n bridge-smoke > /dev/null 2>&1; then
    test_pass "Integration Makefile targets available"
else
    test_fail "Integration Makefile not loaded"
fi

# Test 8: Demo script exists and runs
echo "8. Testing AGI-RAG Bridge Demo..."
if [ -f "scripts/demo_agi_rag_bridge.py" ]; then
    test_pass "AGI-RAG Bridge Demo script exists"
else
    test_fail "AGI-RAG Bridge Demo script not found"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "  RESULTS"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "✓ All smoke tests passed!"
    exit 0
else
    echo "✗ Some tests failed. Check output above."
    exit 1
fi

