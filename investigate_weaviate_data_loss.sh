#!/bin/bash

echo "🔍 INVESTIGATING WEAVIATE DATA DISCREPANCY"
echo "==========================================="
echo ""

echo "1️⃣ Checking Weaviate Total Objects (Different Methods)"
echo "--------------------------------------------------------"

echo "Method 1: Query all objects with high limit:"
curl -s 'http://localhost:8090/v1/objects?limit=1000' | jq '{total: .objects | length, totalResults: .totalResults}'

echo ""
echo "Method 2: Query each class separately:"
for class in AIAgentLog AIContext AICustomTool AIMemory Docs DocsV2 LearnedPattern; do
  count=$(curl -s "http://localhost:8090/v1/objects?class=$class&limit=1000" 2>/dev/null | jq '.objects | length')
  echo "  $class: $count objects (actual count)"
done

echo ""
echo "Method 3: Using GraphQL aggregate:"
curl -s http://localhost:8090/v1/graphql -H "Content-Type: application/json" -d '{
  "query": "{ Aggregate { DocsV2 { meta { count } } } }"
}' | jq '.data.Aggregate.DocsV2[0].meta.count'
echo "  DocsV2 objects via GraphQL aggregate"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Sampling Object Content"
echo "---------------------------"

echo "Recent DocsV2 objects (first 3):"
curl -s 'http://localhost:8090/v1/objects?class=DocsV2&limit=3' | jq '.objects[] | {
  id: .id[0:20],
  source: .properties.source,
  content: .properties.content[0:50]
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Weaviate Cluster Status"
echo "---------------------------"

curl -s http://localhost:8090/v1/nodes | jq '{
  nodes: .nodes | length,
  status: .nodes[0].status
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Checking Weaviate Logs for Issues"
echo "--------------------------------------"

docker logs athena-weaviate --tail 30 2>&1 | grep -iE "error|warn|fail|delete" || echo "  ✅ No recent errors in logs"

echo ""
echo "==========================================="
echo "✅ Investigation Complete"

