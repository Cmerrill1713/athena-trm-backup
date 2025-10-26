#!/bin/bash
# Go-Live Drill — Final Validation Before Production
# Hard gates - exits 1 on any failure

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

ADAPTER="${ADAPTER:-http://localhost:3000}"
UI="${UI:-http://localhost:8080}"
WEAVIATE="${WEAVIATE_URL:-http://127.0.0.1:8080}"

echo -e "${BOLD}🚀 GO-LIVE DRILL — Final Validation${NC}"
echo "================================================"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

# Helper function for gates
gate() {
  local name="$1"
  local cmd="$2"
  
  echo -e "${BOLD}[$((PASS_COUNT + FAIL_COUNT + 1))] $name${NC}"
  
  if eval "$cmd"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS_COUNT++))
  else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL_COUNT++))
    return 1
  fi
  echo ""
}

# ============================================================================
# Critical Gates (MUST PASS)
# ============================================================================

echo -e "${BOLD}🔴 CRITICAL GATES (Must Pass)${NC}"
echo ""

gate "Adapter /healthz returns 200 with diagnostics" \
  "curl -sf $ADAPTER/healthz | jq -e '.status == \"ok\" and .backends and .config' >/dev/null"

gate "/v1/models lists athena-rag, athena-chat, athena-hybrid" \
  "curl -sf $ADAPTER/v1/models | jq -e '.data[] | select(.id == \"athena-rag\")' >/dev/null && \
   curl -sf $ADAPTER/v1/models | jq -e '.data[] | select(.id == \"athena-chat\")' >/dev/null && \
   curl -sf $ADAPTER/v1/models | jq -e '.data[] | select(.id == \"athena-hybrid\")' >/dev/null"

gate "Non-stream /v1/chat/completions returns valid OpenAI format" \
  "curl -sf $ADAPTER/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{\"model\":\"athena-rag\",\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}' \
    | jq -e '.id and .model and .choices[0].message.content' >/dev/null"

gate "Stream /v1/chat/completions returns SSE format with [DONE]" \
  "timeout 5 curl -NsS $ADAPTER/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{\"model\":\"athena-rag\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}' \
    | grep -q 'data:' && \
   timeout 5 curl -NsS $ADAPTER/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{\"model\":\"athena-rag\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}' \
    | grep -q '\[DONE\]'"

gate "All 3 models route and return non-empty content" \
  "for model in athena-rag athena-chat athena-hybrid; do \
     curl -sf $ADAPTER/v1/chat/completions \
       -H 'content-type: application/json' \
       -d '{\"model\":\"'\$model'\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}' \
       | jq -e '.choices[0].message.content | length > 10' >/dev/null || exit 1; \
   done"

# ============================================================================
# Contract Validation
# ============================================================================

echo -e "${BOLD}📋 CONTRACT VALIDATION${NC}"
echo ""

gate "OpenAI contract: response has id, model, choices, usage" \
  "curl -sf $ADAPTER/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{\"model\":\"athena-rag\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}' \
    | jq -e '.id and .model and .choices and .usage' >/dev/null"

gate "OpenAI contract: message.content is non-empty string" \
  "curl -sf $ADAPTER/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{\"model\":\"athena-rag\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}' \
    | jq -e '.choices[0].message.content | type == \"string\" and length > 0' >/dev/null"

gate "Invalid model returns 400 error" \
  "curl -s $ADAPTER/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{\"model\":\"invalid\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}' \
    | jq -e '.error and (.error.message | contains(\"Invalid model\"))' >/dev/null"

# ============================================================================
# RAG Quality Gates (if data available)
# ============================================================================

echo -e "${BOLD}🎯 RAG QUALITY GATES${NC}"
echo ""

if [ -f "seeds/eval_seed.jsonl" ]; then
  gate "RAG evaluation: hit@5 ≥ 0.97, support@3 ≥ 0.95" \
    "make -s rag-eval WEAVIATE_URL=$WEAVIATE >/dev/null 2>&1" || \
    echo -e "${YELLOW}⚠️  RAG eval failed - check Weaviate data${NC}"
  
  gate "Delta report: semantic ≥ BM25 (Δ hit ≥ 0%, Δ p95 ≤ +10%)" \
    "make -s rag-delta WEAVIATE_URL=$WEAVIATE >/dev/null 2>&1 && \
     ls -t artifacts/delta_*.json | head -1 | xargs cat | \
     jq -e '.delta.\"hit@k\" >= 0 and .delta.latency_sec_p95 <= 0.1' >/dev/null" || \
    echo -e "${YELLOW}⚠️  Delta report unavailable${NC}"
else
  echo -e "${YELLOW}⚠️  No eval seed file - skipping RAG quality gates${NC}"
  echo ""
fi

# ============================================================================
# Infrastructure Validation
# ============================================================================

echo -e "${BOLD}🏗️  INFRASTRUCTURE VALIDATION${NC}"
echo ""

gate "Weaviate schema contains classes" \
  "curl -sf $WEAVIATE/v1/schema | jq -e '.classes | length > 0' >/dev/null" || \
  echo -e "${YELLOW}⚠️  Weaviate has no classes - restore corpus${NC}"

gate "Metrics endpoint exposes Prometheus format" \
  "curl -sf $ADAPTER/metrics | grep -q 'http_requests_total'" || \
  echo -e "${YELLOW}⚠️  Metrics not available${NC}"

gate "Open WebUI reachable (if deployed)" \
  "curl -sfI $UI | head -n1 | grep -q '200\\|301\\|302'" || \
  echo -e "${YELLOW}⚠️  Open WebUI not reachable${NC}"

# ============================================================================
# Performance Baseline
# ============================================================================

echo -e "${BOLD}⚡ PERFORMANCE BASELINE${NC}"
echo ""

echo "Measuring p95 latency (10 requests)..."
LATENCIES=""
for i in {1..10}; do
  START=$(date +%s%N)
  curl -sf $ADAPTER/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{"model":"athena-rag","messages":[{"role":"user","content":"test"}]}' >/dev/null
  END=$(date +%s%N)
  DURATION=$(( (END - START) / 1000000 ))  # Convert to ms
  LATENCIES="$LATENCIES $DURATION"
  echo -n "."
done
echo ""

P95=$(echo "$LATENCIES" | tr ' ' '\n' | sort -n | tail -2 | head -1)
echo "p95 latency: ${P95}ms"

if [ "$P95" -lt 1500 ]; then
  echo -e "${GREEN}✅ Latency acceptable (<1500ms)${NC}"
  ((PASS_COUNT++))
else
  echo -e "${RED}❌ Latency too high (>1500ms)${NC}"
  ((FAIL_COUNT++))
fi
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "================================================"
echo -e "${BOLD}GO-LIVE DRILL SUMMARY${NC}"
echo ""
echo "  Passed: $PASS_COUNT"
echo "  Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
  echo -e "${GREEN}${BOLD}✅ ALL GATES PASSED — READY FOR PRODUCTION${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Configure TLS (nginx.conf)"
  echo "  2. Enable authentication (API_KEY env var)"
  echo "  3. Set CORS_ORIGIN to your UI domain"
  echo "  4. Import Grafana dashboard (grafana-dashboard.json)"
  echo "  5. Load alert rules (prometheus-alerts.yml)"
  echo "  6. Run canary deployment (see PRODUCTION_RUNBOOK.md)"
  echo ""
  echo "  Then flip the switch: expose to users!"
  echo ""
  exit 0
else
  echo -e "${RED}${BOLD}❌ $FAIL_COUNT GATE(S) FAILED — NOT READY${NC}"
  echo ""
  echo "Review failures above and:"
  echo "  1. Check service logs: docker-compose logs"
  echo "  2. Verify Weaviate data restored"
  echo "  3. Re-run: make e2e-full"
  echo ""
  exit 1
fi

