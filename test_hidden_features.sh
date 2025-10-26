#!/bin/bash

echo "🎁 TESTING HIDDEN FEATURES (Proper Parameters)"
echo "==============================================="
echo ""

echo "1️⃣ Router /respond (Complete Chat Endpoint)"
echo "--------------------------------------------"
curl -s -X POST http://localhost:9113/respond \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is TRM?",
    "max_tokens": 100
  }' | jq '{
  response: .text[:200],
  route: .route,
  latency_ms: .latency_ms
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Knowledge Gateway Advanced Search"
echo "--------------------------------------"
curl -s -X POST http://localhost:8093/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to train machine learning models?",
    "limit": 5,
    "include_scores": true
  }' | jq '{
  results_count: (.results | length),
  top_result: .results[0]
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Knowledge Context - Context Retrieval"
echo "-----------------------------------------"
curl -s -X POST http://localhost:8092/retrieve \
  -H "Content-Type: application/json" \
  -d '{"key": "recent_conversation", "limit": 5}' \
  | jq '.' || echo "Endpoint exists but needs proper schema"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Athena API (8888) - Detailed Exploration"
echo "--------------------------------------------"

echo "Health with details:"
curl -s http://localhost:8888/health | jq '.'

echo ""
echo "API info:"
curl -s http://localhost:8888/api | jq '.'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ PostgreSQL Database Content"
echo "--------------------------------"

echo "Checking database tables:"
docker exec athena-postgres psql -U postgres -d knowledge_base -c "
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;" 2>/dev/null || echo "No tables or access issue"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ Weaviate Classes & Objects"
echo "------------------------------"

echo "All classes:"
curl -s http://localhost:8090/v1/schema | jq -r '.classes[].class'

echo ""
echo "Objects per class:"
for class in AIAgentLog AIContext AICustomTool AIMemory Docs DocsV2 LearnedPattern; do
  count=$(curl -s "http://localhost:8090/v1/objects?class=$class" | jq '.objects | length' 2>/dev/null)
  if [ "$count" != "null" ] && [ -n "$count" ]; then
    echo "  $class: $count objects"
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "7️⃣ Router Policy Reload"
echo "------------------------"
curl -s -X POST http://localhost:9113/reload-policy | jq '.'

echo ""
echo "==============================================="
echo "✅ Hidden Features Discovery Complete"

