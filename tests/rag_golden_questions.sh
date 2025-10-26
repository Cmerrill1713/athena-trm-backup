#!/bin/bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  ✨ RAG Golden Questions - Correctness Validation"
echo "════════════════════════════════════════════════════════════════"
echo ""

RAG_URL="http://localhost:8087"

# Golden questions and expected patterns (parallel arrays)
QUESTIONS=(
  "Where is the router MCP provider configured?"
  "How does the AGI core service work?"
  "What tools are available for frontend testing?"
  "Where is the curiosity detection implemented?"
  "How does the planner decompose tasks?"
  "What metrics are tracked by AGI Core?"
  "Where is the tool registry defined?"
  "How does the typing probe work?"
  "What is the Scout-Plan-Build workflow?"
  "Where are the agent experts defined?"
)

EXPECTED=(
  "provider"
  "FastAPI|service|agi"
  "frontend|xcode|probe"
  "curiosity|uncertainty|keywords"
  "plan|decompose|workflow"
  "metrics|prometheus|counter"
  "TOOL_REGISTRY|tooling"
  "typing|probe|applescript"
  "scout|plan|build|workflow"
  "agent|expert|ExpertDomain"
)

PASS=0
FAIL=0
TOTAL=${#QUESTIONS[@]}

echo "Testing $TOTAL golden questions..."
echo ""

for i in "${!QUESTIONS[@]}"; do
  question="${QUESTIONS[$i]}"
  expected="${EXPECTED[$i]}"
  
  # Query RAG
  response=$(curl -sS -X POST "$RAG_URL/query" \
    -H 'Content-Type: application/json' \
    -d "{\"query\":\"$question\",\"top_k\":5,\"min_score\":0.3}")
  
  hits=$(echo "$response" | jq -r '.total // 0')
  took_ms=$(echo "$response" | jq -r '.took_ms // 0')
  
  # Check if any hit contains expected substring
  match_found=0
  if [ "$hits" -gt 0 ]; then
    # Get all hit texts and check for expected patterns
    hit_texts=$(echo "$response" | jq -r '.hits[].text' | tr '\n' ' ')
    
    # Split expected by | for OR matching
    IFS='|' read -ra PATTERNS <<< "$expected"
    for pattern in "${PATTERNS[@]}"; do
      if echo "$hit_texts" | grep -iq "$pattern"; then
        match_found=1
        break
      fi
    done
  fi
  
  if [ $match_found -eq 1 ]; then
    PASS=$((PASS + 1))
    echo "✅ $(printf '%-60s' "$question") $hits hits, ${took_ms}ms"
  else
    FAIL=$((FAIL + 1))
    echo "❌ $(printf '%-60s' "$question") $hits hits (expected: $expected)"
  fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Golden Questions Results"
echo "════════════════════════════════════════════════════════════════"
echo "Passed:    $PASS / $TOTAL ($(echo "scale=1; 100 * $PASS / $TOTAL" | bc)%)"
echo "Failed:    $FAIL / $TOTAL"
echo ""

if [ $PASS -ge $((TOTAL * 7 / 10)) ]; then
  echo "✅ PASS: ≥70% correctness threshold met"
else
  echo "❌ FAIL: <70% correctness (need more seeding or better embeddings)"
fi
echo "════════════════════════════════════════════════════════════════"

