#!/bin/bash

echo "🗄️ COMPLETE DATABASE SCHEMA MAPPING"
echo "====================================="
echo ""

echo "1️⃣ PostgreSQL: athena_db"
echo "-------------------------"

docker exec athena-postgres psql -U postgres -d athena_db -c "
-- Full schema for routing_outcomes
SELECT 
  column_name, 
  data_type, 
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'routing_outcomes'
ORDER BY ordinal_position;
" 2>/dev/null

echo ""
echo "Sample routing_outcomes data:"
docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT 
  id,
  LEFT(prompt, 30) as prompt,
  selected_model,
  latency_ms,
  success
FROM routing_outcomes
ORDER BY id DESC
LIMIT 3;
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ PostgreSQL: learned_patterns schema"
echo "----------------------------------------"

docker exec athena-postgres psql -U postgres -d athena_db -c "
\d learned_patterns
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ PostgreSQL: trm_training_runs schema"
echo "-----------------------------------------"

docker exec athena-postgres psql -U postgres -d athena_db -c "
\d trm_training_runs
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ All Databases in PostgreSQL"
echo "--------------------------------"

docker exec athena-postgres psql -U postgres -c "
SELECT 
  datname as database,
  pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datname NOT IN ('template0', 'template1')
ORDER BY pg_database_size(datname) DESC;
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Weaviate Complete Schema"
echo "-----------------------------"

curl -s http://localhost:8090/v1/schema | jq '.classes[] | {
  class: .class,
  properties: [.properties[].name],
  vectorizer: .vectorizer,
  distance: .vectorIndexConfig.distance
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ Object Count by Class (Updated)"
echo "------------------------------------"

for class in AIAgentLog AIContext AICustomTool AIMemory Docs DocsV2 LearnedPattern; do
  count=$(curl -s "http://localhost:8090/v1/objects?class=$class&limit=1000" 2>/dev/null | jq '.objects | length' 2>/dev/null)
  echo "  $class: $count objects"
done

echo ""
echo "Total objects:"
curl -s 'http://localhost:8090/v1/objects?limit=1000' | jq '.objects | length'

echo ""
echo "====================================="
echo "✅ Database Schema Mapping Complete"

