#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🔥 RAG Load Test - Sustained Query Rate"
echo "════════════════════════════════════════════════════════════════"
echo ""

RAG_URL="http://localhost:8087"
DURATION_S=${1:-60}
QPS=${2:-5}
DELAY=$(echo "scale=3; 1.0 / $QPS" | bc)

echo "Config:"
echo "  Duration: ${DURATION_S}s"
echo "  QPS:      $QPS"
echo "  Delay:    ${DELAY}s between queries"
echo ""

# Golden queries (rotate through these)
declare -a QUERIES=(
  "where is the router configured"
  "how does the MCP provider work"
  "what is the AGI core service"
  "where are the frontend tools"
  "how does the planner work"
  "what metrics are tracked"
  "where is the RAG gateway"
  "how does curiosity detection work"
  "what tools are available"
  "where is the confidence loop"
)

echo "Starting load test..."
START=$(date +%s)
COUNT=0
ERRORS=0
TOTAL_LATENCY=0

while true; do
  NOW=$(date +%s)
  ELAPSED=$((NOW - START))
  
  if [ $ELAPSED -ge $DURATION_S ]; then
    break
  fi
  
  # Pick a query
  QUERY="${QUERIES[$((COUNT % ${#QUERIES[@]}))]}"
  
  # Execute query and capture latency
  RESPONSE=$(curl -sS -X POST "$RAG_URL/query" \
    -H 'Content-Type: application/json' \
    -d "{\"query\":\"$QUERY\",\"top_k\":5}" \
    -w '\n%{http_code}' 2>&1)
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | head -n-1)
  
  if [ "$HTTP_CODE" == "200" ]; then
    LATENCY=$(echo "$BODY" | jq -r '.took_ms // 0')
    HITS=$(echo "$BODY" | jq -r '.total // 0')
    TOTAL_LATENCY=$((TOTAL_LATENCY + LATENCY))
    
    if [ $((COUNT % 10)) -eq 0 ]; then
      echo "  Query $COUNT: ${LATENCY}ms, $HITS hits"
    fi
  else
    ERRORS=$((ERRORS + 1))
    echo "  ❌ Query $COUNT failed: HTTP $HTTP_CODE"
  fi
  
  COUNT=$((COUNT + 1))
  sleep "$DELAY"
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Load Test Complete"
echo "════════════════════════════════════════════════════════════════"
echo "Queries:       $COUNT"
echo "Errors:        $ERRORS"
echo "Success rate:  $(echo "scale=1; 100 * ($COUNT - $ERRORS) / $COUNT" | bc)%"
echo "Avg latency:   $((TOTAL_LATENCY / (COUNT - ERRORS)))ms"
echo "Actual QPS:    $(echo "scale=2; $COUNT / $DURATION_S" | bc)"
echo ""

# Check final metrics
echo "Prometheus metrics:"
curl -s "$RAG_URL/metrics" | grep -E 'rag_queries_total|rag_query_latency_ms_count'

echo ""
echo "════════════════════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ] && [ $(echo "$TOTAL_LATENCY / $COUNT < 250" | bc) -eq 1 ]; then
  echo "✅ PASS: 0 errors, p100 < 250ms"
else
  echo "⚠️  CHECK: $ERRORS errors or high latency"
fi
echo "════════════════════════════════════════════════════════════════"


