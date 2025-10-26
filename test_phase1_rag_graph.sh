#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 Phase 1: RAG + Graph Integration Test"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "== 1. Check Services =="
echo "AGI Core (8000):"
curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo "  ✅ Healthy" || echo "  ❌ Down"

echo "RAG Gateway (8088):"
curl -sf http://localhost:8088/health >/dev/null 2>&1 && echo "  ✅ Healthy" || echo "  ❌ Down (run: python3 services/rag-gateway/app.py &)"

echo "Weaviate (8090):"
curl -sf http://localhost:8090/v1/.well-known/ready >/dev/null 2>&1 && echo "  ✅ Ready" || echo "  ❌ Down"

echo ""

echo "== 2. Test RAG Query Endpoint =="
if curl -sf http://localhost:8088/health >/dev/null 2>&1; then
  echo "Testing: POST /query with 'router configuration'"
  RAG_RESPONSE=$(curl -sS -X POST http://localhost:8088/query \
    -H 'Content-Type: application/json' \
    -d '{"query":"router configuration","top_k":3,"min_score":0.5}' 2>&1)
  
  if echo "$RAG_RESPONSE" | jq -e '.hits' >/dev/null 2>&1; then
    HIT_COUNT=$(echo "$RAG_RESPONSE" | jq '.hits | length')
    TOOK_MS=$(echo "$RAG_RESPONSE" | jq '.took_ms')
    echo "  ✅ RAG query succeeded: $HIT_COUNT hits in ${TOOK_MS}ms"
    if [ "$HIT_COUNT" -gt 0 ]; then
      echo "  Sample hit:"
      echo "$RAG_RESPONSE" | jq -r '.hits[0].text' | head -c 100
      echo "..."
    else
      echo "  ⚠️  No hits (need to seed Weaviate)"
    fi
  else
    echo "  ❌ RAG query failed:"
    echo "$RAG_RESPONSE" | head -c 200
  fi
else
  echo "  ⚠️  RAG Gateway offline, skipping"
fi
echo ""

echo "== 3. Test AGI Curiosity with RAG =="
echo "Asking: 'Where is the router MCP provider configured?'"
AGI_RESPONSE=$(curl -sS -X POST http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "objective": "Where is the router MCP provider configured?",
    "tools": [],
    "max_steps": 5
  }')

echo "Task ID: $(echo "$AGI_RESPONSE" | jq -r '.task_id')"
echo "Status: $(echo "$AGI_RESPONSE" | jq -r '.status')"
echo ""

echo "Trace (curiosity steps):"
echo "$AGI_RESPONSE" | jq -C '.trace[] | select(.agent == "curiosity" or .agent == "guardian")' || true
echo ""

echo "== 4. Check Metrics =="
echo "Curiosity actions:"
curl -s http://localhost:8000/metrics | grep 'agi_curiosity_actions_total' | grep -v '^#' || echo "  (none yet)"

echo ""
echo "RAG queries:"
curl -s http://localhost:8088/metrics 2>/dev/null | grep 'rag_queries_total' | grep -v '^#' || echo "  (RAG gateway offline)"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Phase 1 Status:"
echo "  RAG Gateway:     $(curl -sf http://localhost:8088/health >/dev/null 2>&1 && echo '✅' || echo '❌')"
echo "  Weaviate:        $(curl -sf http://localhost:8090/v1/.well-known/ready >/dev/null 2>&1 && echo '✅' || echo '❌')"
echo "  AGI Curiosity:   $(echo "$AGI_RESPONSE" | jq -r '.trace[] | select(.agent == "curiosity")' | wc -l | xargs) actions"
echo ""
echo "Next Steps:"
echo "  • Start RAG Gateway: python3 services/rag-gateway/app.py &"
echo "  • Seed Weaviate (if hits = 0)"
echo "  • Add Graph service (optional)"
echo "════════════════════════════════════════════════════════════════"


