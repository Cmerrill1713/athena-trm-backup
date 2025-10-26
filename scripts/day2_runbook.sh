#!/bin/bash
# Day-2 Runbook - Daily operational checks for AGI+RAG+TRM integration
#
# Run this daily (or add to cron) to monitor system health

set -eo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

section() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
}

# ============================================================================
# DAY-2 CHECKS
# ============================================================================

section "DAY-2 OPERATIONAL RUNBOOK - $(date)"

# 1. Service Health
section "1. SERVICE HEALTH"

SERVICES=(
    "8088:RAG Gateway"
    "8089:TRM Service"
    "9113:Router"
    "8090:Weaviate"
    "8092:Unified Metrics"
    "11434:Ollama"
)

for service in "${SERVICES[@]}"; do
    PORT="${service%%:*}"
    NAME="${service##*:}"
    
    if curl -sf http://localhost:$PORT/health > /dev/null 2>&1 || \
       curl -sf http://localhost:$PORT/v1/meta > /dev/null 2>&1 || \
       curl -sf http://localhost:$PORT/api/tags > /dev/null 2>&1; then
        pass "$NAME ($PORT) healthy"
    else
        fail "$NAME ($PORT) not responding"
    fi
done

# 2. Route Mix Trend
section "2. ROUTE MIX TREND"

info "Checking if router is distributing traffic correctly..."

SNAPSHOT=$(curl -s http://localhost:8092/snapshot 2>/dev/null || echo '{}')

RAG_PCT=$(echo "$SNAPSHOT" | jq -r '.router_rag_pct // 0')
LLM_PCT=$(echo "$SNAPSHOT" | jq -r '.router_llm_pct // 0')
HYBRID_PCT=$(echo "$SNAPSHOT" | jq -r '.router_hybrid_pct // 0')
TRM_PCT=$(echo "$SNAPSHOT" | jq -r '.router_trm_pct // 0')

info "  RAG:    ${RAG_PCT}%"
info "  LLM:    ${LLM_PCT}%"
info "  Hybrid: ${HYBRID_PCT}%"
info "  TRM:    ${TRM_PCT}%"

# Check for drift (all routes going to one backend)
if (( $(echo "$RAG_PCT > 90" | bc -l) )) || (( $(echo "$LLM_PCT > 90" | bc -l) )); then
    warn "Route mix showing heavy skew (>90% to one backend)"
else
    pass "Route mix looks balanced"
fi

# 3. Latency by Route
section "3. LATENCY BY ROUTE (p95)"

info "Checking latency metrics..."

RAG_LAT=$(echo "$SNAPSHOT" | jq -r '.rag_avg_latency_ms // 0')
TRM_LAT=$(echo "$SNAPSHOT" | jq -r '.trm_avg_latency_ms // 0')
AGI_LAT=$(echo "$SNAPSHOT" | jq -r '.agi_avg_latency_ms // 0')

info "  RAG: ${RAG_LAT}ms"
info "  TRM: ${TRM_LAT}ms"
info "  AGI: ${AGI_LAT}ms"

# Check latency SLOs
if [ "$RAG_LAT" != "0" ]; then
    if (( $(echo "$RAG_LAT <= 300" | bc -l) )); then
        pass "RAG latency (${RAG_LAT}ms) within SLO (≤300ms)"
    else
        fail "RAG latency (${RAG_LAT}ms) exceeds SLO (≤300ms)"
    fi
fi

# 4. RAG Quality Gates
section "4. RAG QUALITY GATES"

info "Checking RAG hit rates..."

HIT_AT_5=$(echo "$SNAPSHOT" | jq -r '.rag_hit_at_5 // 0')
SUPPORT_AT_3=$(echo "$SNAPSHOT" | jq -r '.rag_support_at_3 // 0')

info "  Hit@5:     $HIT_AT_5"
info "  Support@3: $SUPPORT_AT_3"

# Check gates
if (( $(echo "$HIT_AT_5 >= 0.97" | bc -l) )); then
    pass "Hit@5 ($HIT_AT_5) meets gate (≥0.97)"
else
    fail "Hit@5 ($HIT_AT_5) below gate (≥0.97)"
fi

if (( $(echo "$SUPPORT_AT_3 >= 0.95" | bc -l) )); then
    pass "Support@3 ($SUPPORT_AT_3) meets gate (≥0.95)"
else
    fail "Support@3 ($SUPPORT_AT_3) below gate (≥0.95)"
fi

# 5. Error Budget
section "5. ERROR BUDGET"

info "Checking error rates..."

TOTAL_REQ=$(echo "$SNAPSHOT" | jq -r '.total_requests // 1')
TOTAL_ERR=$(echo "$SNAPSHOT" | jq -r '.total_errors // 0')
ADAPTER_ERR=$(echo "$SNAPSHOT" | jq -r '.adapter_errors // 0')

ERROR_RATE=$(echo "scale=4; $TOTAL_ERR * 100 / $TOTAL_REQ" | bc 2>/dev/null || echo "0")

info "  Total requests: $TOTAL_REQ"
info "  Total errors: $TOTAL_ERR"
info "  Error rate: ${ERROR_RATE}%"
info "  Adapter errors: $ADAPTER_ERR"

# Check error budget (< 1%)
if (( $(echo "$ERROR_RATE < 1.0" | bc -l) )); then
    pass "Error rate (${ERROR_RATE}%) within budget (<1%)"
else
    fail "Error rate (${ERROR_RATE}%) exceeds budget (<1%)"
fi

# 6. Recent Papers Ingest
section "6. RECENT PAPERS INGEST (OPTIONAL)"

if [ -f "data/papers_queue/approved.jsonl" ]; then
    QUEUE_COUNT=$(wc -l < data/papers_queue/approved.jsonl)
    info "Papers in approved queue: $QUEUE_COUNT"
    
    if [ "$QUEUE_COUNT" -gt 0 ]; then
        warn "Approved papers in queue ready for ingestion (run 'make papers-fetch')"
    fi
else
    info "No papers queue found (feature not in use)"
fi

# 7. Disk Usage
section "7. DISK USAGE"

info "Checking disk usage for Weaviate and Ollama..."

if [ -d "./volumes/weaviate_data" ]; then
    WEAVIATE_SIZE=$(du -sh ./volumes/weaviate_data 2>/dev/null | cut -f1 || echo "unknown")
    info "  Weaviate data: $WEAVIATE_SIZE"
fi

if [ -d "./volumes/ollama" ]; then
    OLLAMA_SIZE=$(du -sh ./volumes/ollama 2>/dev/null | cut -f1 || echo "unknown")
    info "  Ollama models: $OLLAMA_SIZE"
fi

# 8. Docker Container Status
section "8. DOCKER CONTAINER STATUS"

info "Checking Docker containers..."

CONTAINERS=$(docker ps --format "{{.Names}}" 2>/dev/null | grep -E "(weaviate|ollama|rag-gateway|smart-chat|router)" || echo "")

if [ -n "$CONTAINERS" ]; then
    for container in $CONTAINERS; do
        STATUS=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
        if [ "$STATUS" = "running" ]; then
            pass "$container: running"
        else
            fail "$container: $STATUS"
        fi
    done
else
    warn "No Docker containers found (running in native mode?)"
fi

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================

section "SUMMARY & RECOMMENDATIONS"

echo "Date: $(date)"
echo ""
echo "Actions:"
echo "  - If errors high: Check logs with 'docker logs <service>'"
echo "  - If latency high: Run 'make rag-eval' to identify slow queries"
echo "  - If route mix skewed: Tune RAG_PROBE_THRESHOLD"
echo "  - If gates failing: Run 'make rag-delta' to compare modes"
echo ""
echo "Regular maintenance:"
echo "  - Weekly: make trm-train (refresh training data)"
echo "  - Monthly: make trm-finetune (retrain TRM on corpus)"
echo "  - Nightly: make nightly (automated in CI)"
echo ""
echo "✓ Day-2 runbook complete"

