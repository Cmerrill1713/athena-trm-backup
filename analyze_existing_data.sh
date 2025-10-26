#!/bin/bash

echo "📦 ANALYZING EXISTING DATA IN SYSTEM"
echo "====================================="
echo ""

echo "1️⃣ Weaviate Object Breakdown by Class"
echo "---------------------------------------"

for class in AIAgentLog AIContext AICustomTool AIMemory Docs DocsV2 LearnedPattern; do
  count=$(curl -s "http://localhost:8090/v1/objects?class=$class&limit=1000" 2>/dev/null | jq '.objects | length' 2>/dev/null)
  if [ "$count" != "null" ] && [ -n "$count" ] && [ "$count" != "0" ]; then
    echo "  ✅ $class: $count objects"
    
    # Show sample
    curl -s "http://localhost:8090/v1/objects?class=$class&limit=1" 2>/dev/null \
      | jq -r ".objects[0].properties | to_entries | map(\"\(.key): \(.value)\") | join(\", \")" 2>/dev/null \
      | head -c 100
    echo "..."
    echo ""
  else
    echo "  ❌ $class: empty"
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ PostgreSQL Database athena_db"
echo "----------------------------------"

echo "Switching to athena_db:"
docker exec athena-postgres psql -U postgres -d athena_db -c "\dt" 2>/dev/null

echo ""
echo "Checking knowledge_base database:"
docker exec athena-postgres psql -U postgres -d knowledge_base -c "
CREATE TABLE IF NOT EXISTS query_history (
  id SERIAL PRIMARY KEY,
  query TEXT,
  response TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Finding ALL Router Capabilities"
echo "------------------------------------"

echo "Extracting all router functions:"
grep "^async def\|^def" services/router/app.py | grep -v "^    " | head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ UAI Router Definitions Deep Dive"
echo "-------------------------------------"

echo "All routers included in UAI:"
grep "include_router\|router\." AI-Projects/universal-ai-tools/api/app.py | head -15

echo ""
echo "Finding all router files:"
find AI-Projects/universal-ai-tools/api/routers -name "*.py" -type f 2>/dev/null

echo ""
echo "====================================="
echo "Existing Data Analysis Complete"

