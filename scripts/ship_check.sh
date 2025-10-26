#!/bin/bash
# Ship Check - Comprehensive acceptance test for AGI+RAG+TRM integration
# Runs steps 0-4 from acceptance plan: Preflight, Bridge, Router, Metrics, Gates
#
# Usage:
#   bash scripts/ship_check.sh
#
# Exit codes:
#   0 = PASS (safe to ship)
#   1 = FAIL (do not ship)

set -eo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

START_TIME=$(date +%s)

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC} $1"
    ((WARNINGS++))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

section() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
}

# ============================================================================
# STEP 0: PREFLIGHT (60 seconds)
# ============================================================================

section "STEP 0: PREFLIGHT CHECKS"

info "Checking if services are running..."

# RAG Gateway (8088)
if curl -sf http://localhost:8088/health > /dev/null 2>&1; then
    pass "RAG Gateway (8088) responding"
else
    fail "RAG Gateway (8088) not responding - run 'make integration-up'"
    exit 1
fi

# Router (9113)
if curl -sf http://localhost:9113/health > /dev/null 2>&1; then
    pass "Router (9113) responding"
else
    fail "Router (9113) not responding - run 'make integration-up'"
    exit 1
fi

# Unified Metrics (8092)
if curl -sf http://localhost:8092/health > /dev/null 2>&1; then
    pass "Unified Metrics (8092) responding"
else
    warn "Unified Metrics (8092) not responding - start with 'make unified-metrics'"
fi

# OpenAI Adapter (3000)
if curl -sf http://localhost:3000/v1/models > /dev/null 2>&1; then
    pass "OpenAI Adapter (3000) responding"
else
    warn "OpenAI Adapter (3000) not responding (optional)"
fi

# Weaviate (8090)
if curl -sf http://localhost:8090/v1/meta > /dev/null 2>&1; then
    pass "Weaviate (8090) responding"
else
    fail "Weaviate (8090) not responding"
    exit 1
fi

# ============================================================================
# STEP 1: BRIDGE ACCEPTANCE (AGI → /kb/search → DocsV2)
# ============================================================================

section "STEP 1: BRIDGE ACCEPTANCE TEST"

info "Testing /kb/search endpoint (latency < 300ms, hits > 0)..."

# Run KB search and capture output
KB_RESPONSE=$(curl -s http://localhost:8088/kb/search \
    -H "Content-Type: application/json" \
    -d '{"query":"reset token policy","mode":"nearText","topK":5,"semanticEnabled":true}')

# Parse response
HITS_COUNT=$(echo "$KB_RESPONSE" | jq -r '.hits | length' 2>/dev/null || echo "0")
LATENCY_MS=$(echo "$KB_RESPONSE" | jq -r '.metrics.latency_ms' 2>/dev/null || echo "999")
MODE=$(echo "$KB_RESPONSE" | jq -r '.metrics.mode' 2>/dev/null || echo "unknown")

info "Results: hits=$HITS_COUNT, latency=${LATENCY_MS}ms, mode=$MODE"

# Check hits count
if [ "$HITS_COUNT" -ge 1 ]; then
    pass "KB search returned $HITS_COUNT hits"
else
    fail "KB search returned 0 hits (DocsV2 empty? Check Weaviate schema)"
fi

# Check latency
if [ "$LATENCY_MS" -le 300 ]; then
    pass "KB search latency ${LATENCY_MS}ms ≤ 300ms"
elif [ "$LATENCY_MS" -le 500 ]; then
    warn "KB search latency ${LATENCY_MS}ms > 300ms (acceptable for cold cache)"
else
    fail "KB search latency ${LATENCY_MS}ms > 500ms (too slow)"
fi

# ============================================================================
# STEP 2: ROUTER ACCEPTANCE (Policy + Relevance)
# ============================================================================

section "STEP 2: ROUTER ACCEPTANCE TEST"

info "Testing routing decisions for different query types..."

# Test 1: Factual query → RAG/Hybrid
info "Test 1: Factual query (should route to RAG/Hybrid)"
ROUTE_1=$(python3 scripts/router_probe.py --q "What is our refund policy?" 2>&1 | grep "Route:" | awk '{print $3}' || echo "unknown")
info "  Routed to: $ROUTE_1"

if [[ "$ROUTE_1" == "rag" || "$ROUTE_1" == "hybrid" || "$ROUTE_1" == "trm_rag" ]]; then
    pass "Factual query routed to $ROUTE_1 (correct)"
else
    fail "Factual query routed to $ROUTE_1 (expected RAG/Hybrid/TRM+RAG)"
fi

# Test 2: Creative query → LLM
info "Test 2: Creative query (should route to LLM)"
ROUTE_2=$(python3 scripts/router_probe.py --q "Brainstorm 10 creative tagline options" 2>&1 | grep "Route:" | awk '{print $3}' || echo "unknown")
info "  Routed to: $ROUTE_2"

if [[ "$ROUTE_2" == "llm" ]]; then
    pass "Creative query routed to $ROUTE_2 (correct)"
else
    warn "Creative query routed to $ROUTE_2 (expected LLM, but acceptable)"
fi

# Test 3: Reasoning query → TRM/TRM+RAG
info "Test 3: Reasoning query (should route to TRM/TRM+RAG)"
ROUTE_3=$(python3 scripts/router_probe.py --q "Compare solutions A vs B with tradeoffs" 2>&1 | grep "Route:" | awk '{print $3}' || echo "unknown")
info "  Routed to: $ROUTE_3"

if [[ "$ROUTE_3" == "trm" || "$ROUTE_3" == "trm_rag" ]]; then
    pass "Reasoning query routed to $ROUTE_3 (correct)"
else
    warn "Reasoning query routed to $ROUTE_3 (expected TRM/TRM+RAG)"
fi

# ============================================================================
# STEP 3: UNIFIED METRICS SANITY (1 minute)
# ============================================================================

section "STEP 3: UNIFIED METRICS SANITY CHECK"

info "Checking unified metrics snapshot..."

if curl -sf http://localhost:8092/snapshot > /dev/null 2>&1; then
    SNAPSHOT=$(curl -s http://localhost:8092/snapshot)
    
    TOTAL_REQUESTS=$(echo "$SNAPSHOT" | jq -r '.total_requests' 2>/dev/null || echo "0")
    RAG_HIT_5=$(echo "$SNAPSHOT" | jq -r '.rag_hit_at_5' 2>/dev/null || echo "0")
    AGI_UTILITY=$(echo "$SNAPSHOT" | jq -r '.agi_utility_score' 2>/dev/null || echo "0")
    
    info "  Total requests: $TOTAL_REQUESTS"
    info "  RAG hit@5: $RAG_HIT_5"
    info "  AGI utility: $AGI_UTILITY"
    
    # Check for valid numbers (not NaN or null)
    if [[ "$TOTAL_REQUESTS" =~ ^[0-9]+$ ]]; then
        pass "Unified metrics returning valid data"
    else
        warn "Unified metrics returning invalid data (may need warm-up)"
    fi
else
    warn "Unified metrics service not available (optional for initial ship)"
fi

# ============================================================================
# STEP 4: QUALITY GATES (Hard fail rules)
# ============================================================================

section "STEP 4: QUALITY GATES CHECK"

# Check if rag-eval artifacts exist
if [ -f "artifacts/rag_eval_results.json" ]; then
    info "Using existing RAG eval results from artifacts/"
    
    HIT_AT_5=$(jq -r '.hit_at_5 // 0' artifacts/rag_eval_results.json 2>/dev/null || echo "0")
    SUPPORT_AT_3=$(jq -r '.support_at_3 // 0' artifacts/rag_eval_results.json 2>/dev/null || echo "0")
    
    info "  RAG hit@5: $HIT_AT_5"
    info "  RAG support@3: $SUPPORT_AT_3"
    
    # Check hit@5 gate
    if (( $(echo "$HIT_AT_5 >= 0.97" | bc -l) )); then
        pass "RAG hit@5 ($HIT_AT_5) ≥ 0.97"
    else
        fail "RAG hit@5 ($HIT_AT_5) < 0.97 (quality gate violated)"
    fi
    
    # Check support@3 gate
    if (( $(echo "$SUPPORT_AT_3 >= 0.95" | bc -l) )); then
        pass "RAG support@3 ($SUPPORT_AT_3) ≥ 0.95"
    else
        fail "RAG support@3 ($SUPPORT_AT_3) < 0.95 (quality gate violated)"
    fi
else
    warn "No RAG eval results found - run 'make rag-eval' to establish baseline"
fi

# Check if delta report exists
if [ -f "artifacts/delta_report.json" ]; then
    info "Delta report exists"
    
    DELTA_HIT=$(jq -r '.delta.hit_at_5 // 0' artifacts/delta_report.json 2>/dev/null || echo "0")
    info "  Delta hit@5: $DELTA_HIT"
    
    # Ensure no major regression (delta shouldn't be < -0.05)
    if (( $(echo "$DELTA_HIT >= -0.05" | bc -l) )); then
        pass "Delta report shows no major regression (Δ=$DELTA_HIT)"
    else
        fail "Delta report shows regression (Δ=$DELTA_HIT)"
    fi
else
    warn "No delta report found - run 'make rag-delta' for baseline comparison"
fi

# Run integration smoke tests
info "Running integration smoke tests..."
if bash scripts/integration_smoke_tests.sh > /tmp/ship_check_smoke.log 2>&1; then
    pass "Integration smoke tests passed"
else
    fail "Integration smoke tests failed (see /tmp/ship_check_smoke.log)"
    cat /tmp/ship_check_smoke.log
fi

# ============================================================================
# SUMMARY
# ============================================================================

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "  SHIP CHECK SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "Elapsed time: ${ELAPSED}s"
echo ""
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "═══════════════════════════════════════════════════════════════════════"
    echo -e "  ${GREEN}✓ SHIP IT!${NC} All critical checks passed."
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Next steps:"
    echo "  1. Run canary deployment: make canary-start"
    echo "  2. Monitor for 30 minutes: make canary-watch"
    echo "  3. Promote if green: make canary-promote"
    echo "  4. Rollback if issues: make canary-rollback"
    echo ""
    exit 0
else
    echo "═══════════════════════════════════════════════════════════════════════"
    echo -e "  ${RED}✗ DO NOT SHIP${NC} - $FAILED critical check(s) failed"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Fix the failures above before shipping."
    echo ""
    exit 1
fi

