#!/bin/bash

echo "🔎 EXAMINING HIDDEN DATA STORES"
echo "================================="
echo ""

echo "1️⃣ PostgreSQL: learned_patterns Table"
echo "---------------------------------------"
docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT * FROM learned_patterns LIMIT 5;" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ PostgreSQL: routing_outcomes Table"
echo "---------------------------------------"
docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT * FROM routing_outcomes ORDER BY id DESC LIMIT 5;" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ PostgreSQL: trm_training_runs Table"
echo "---------------------------------------"
docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT * FROM trm_training_runs LIMIT 5;" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Weaviate: AIMemory Objects"
echo "-------------------------------"
curl -s 'http://localhost:8090/v1/objects?class=AIMemory&limit=10' \
  | jq '.objects[] | {
  content: .properties.content[:100],
  type: .properties.memoryType,
  timestamp: .properties.timestamp
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Weaviate: AIContext (User Preferences)"
echo "------------------------------------------"
curl -s 'http://localhost:8090/v1/objects?class=AIContext&limit=10' \
  | jq '.objects[] | {
  content: .properties.content,
  contextKey: .properties.contextKey
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ Weaviate: AICustomTool"
echo "--------------------------"
curl -s 'http://localhost:8090/v1/objects?class=AICustomTool&limit=10' \
  | jq '.objects[] | {
  description: .properties.description,
  createdBy: .properties.createdBy,
  createdAt: .properties.createdAt
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "7️⃣ DocsV2 Distribution"
echo "-----------------------"
curl -s 'http://localhost:8090/v1/objects?class=DocsV2&limit=100' \
  | jq '[.objects[].properties.source] | group_by(.) | map({source: .[0], count: length}) | sort_by(.count) | reverse'

echo ""
echo "================================="
echo "Hidden Data Analysis Complete"

