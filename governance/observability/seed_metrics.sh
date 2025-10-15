#!/usr/bin/env bash
set -euo pipefail

# Seed TRM metrics with realistic routing traffic
API_URL="${API_URL:-http://127.0.0.1:8888}"
COUNT="${1:-100}"

echo "🌱 Seeding TRM metrics with $COUNT routing decisions..."
echo ""

SUCCESS=0
FAILED=0

for i in $(seq 1 $COUNT); do
  # Vary prompts for realistic diversity
  PROMPTS=(
    "Write a Python function to parse JSON"
    "Explain how async/await works"
    "Debug this Swift code snippet"
    "What's the best way to optimize SQL queries?"
    "Refactor this React component"
    "How do I deploy a Docker container?"
    "Write unit tests for this class"
    "Explain the CAP theorem"
  )
  
  PROMPT="${PROMPTS[$((i % ${#PROMPTS[@]}))]}"
  
  RESPONSE=$(curl -sS -X POST "$API_URL/trm/route" \
    -H 'Content-Type: application/json' \
    -d "{\"prompt\":\"$PROMPT (seed $i)\",\"meta\":{}}" \
    -w "\n%{http_code}" 2>/dev/null || echo "000")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  
  if [ "$HTTP_CODE" = "200" ]; then
    SUCCESS=$((SUCCESS + 1))
    [ $((i % 10)) -eq 0 ] && echo "✅ $i/$COUNT requests sent..."
  else
    FAILED=$((FAILED + 1))
    [ $((i % 10)) -eq 0 ] && echo "⚠️  $i/$COUNT ($FAILED failures)..."
  fi
  
  # Small delay to avoid overwhelming the API
  sleep 0.05
done

echo ""
echo "✅ Seeding complete!"
echo "   Success: $SUCCESS"
echo "   Failed:  $FAILED"
echo "   Rate:    $(awk "BEGIN {printf \"%.1f\", ($SUCCESS/$COUNT)*100}")%"
echo ""
echo "📊 Check metrics:"
echo "   curl http://127.0.0.1:8888/metrics/ | grep routing_"
echo ""
echo "📈 View dashboard:"
echo "   open http://localhost:3001/d/trm-evolution"

