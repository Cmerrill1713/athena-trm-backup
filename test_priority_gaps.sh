#!/bin/bash

echo "🎯 TESTING PRIORITY 1 GAPS"
echo "==========================="
echo ""

echo "TEST 1: Router /respond (Complete Chat Through Router)"
echo "------------------------------------------------------"

# Check router source for proper schema
echo "Finding proper parameters..."
grep -A 20 "class.*Respond\|def respond" services/router/app.py | head -25

echo ""
echo "Testing with message parameter:"
curl -s -X POST http://localhost:9113/respond \
  -H "Content-Type: application/json" \
  -d '{"message": "What is TRM? Be brief.", "max_tokens": 100}' \
  | jq '{
  text: .text[:200],
  route: .route,
  latency_ms: .latency_ms
}' 2>/dev/null || echo "Schema mismatch, checking source..."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "TEST 2: Knowledge Gateway Search (Advanced RAG)"
echo "------------------------------------------------"

echo "Test A: Simple search"
curl -s -X POST http://localhost:8093/search \
  -H "Content-Type: application/json" \
  -d '{"query": "TRM", "limit": 3}' \
  2>&1 | jq '.' || echo "Endpoint may need different schema"

echo ""
echo "Test B: GET request (if POST doesn't work)"
curl -s "http://localhost:8093/search?q=TRM&limit=3" 2>&1 | jq '.' || echo "Checking alternate methods..."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "TEST 3: PostgreSQL Content"
echo "--------------------------"

echo "Checking if database has any data:"
docker exec athena-postgres psql -U postgres -d knowledge_base -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;" 2>/dev/null

echo ""
echo "Checking all databases:"
docker exec athena-postgres psql -U postgres -c "\l" 2>/dev/null | grep -E "knowledge|athena"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "TEST 4: Redis Content"
echo "---------------------"

echo "Redis database size:"
docker exec athena-redis redis-cli DBSIZE

echo ""
echo "Sample keys (if any):"
docker exec athena-redis redis-cli KEYS "*" | head -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "TEST 5: Weaviate Object Distribution"
echo "-------------------------------------"

echo "Total objects in Weaviate:"
curl -s 'http://localhost:8090/v1/objects?limit=1000' | jq '.objects | length'

echo ""
echo "Sample object:"
curl -s 'http://localhost:8090/v1/objects?limit=1' | jq '.objects[0] | {
  class: .class,
  properties: .properties | keys,
  id: .id[:20]
}'

echo ""
echo "==========================="
echo "Priority Gap Testing Complete"

