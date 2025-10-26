#!/bin/bash

echo "🔍 DEEP AUDIT - Finding Missing Tests & Functions"
echo "==================================================="
echo ""

echo "1️⃣ Discovering All API Endpoints"
echo "----------------------------------"
echo ""

ports=(8080 8088 8091 8412 8888 8014 9110 9113 9114 8093 8092 8089)

for port in "${ports[@]}"; do
  echo "Port $port:"
  # Try to get OpenAPI/Swagger docs
  curl -s -m 2 "http://localhost:$port/docs" 2>/dev/null | grep -o "operationId.*" | head -3 || \
  curl -s -m 2 "http://localhost:$port/openapi.json" 2>/dev/null | jq -r '.paths | keys[]' 2>/dev/null | head -5 || \
  echo "  No OpenAPI docs found"
  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Checking for Undiscovered Endpoints"
echo "----------------------------------------"
echo ""

# UAI (8080) - check for routes we haven't tested
echo "UAI (8080) endpoints:"
curl -s http://localhost:8080/openapi.json 2>/dev/null | jq -r '.paths | keys[]' 2>/dev/null || echo "Checking source..."
grep "@router\|@app\." AI-Projects/universal-ai-tools/api/*.py 2>/dev/null | grep -v "^Binary" | cut -d: -f2 | sort -u | head -10

echo ""
echo "Router (9113) endpoints:"
grep "@app\.(get|post|put|delete)" services/router/app.py | sed 's/@app\.//' | sed 's/(.*$//' | sort -u

echo ""
echo "Autonomous (9114) endpoints:"
grep "@app\.(get|post)" services/autonomous-orchestrator/app.py | sed 's/@app\.//' | sed 's/(.*$//' | sort -u

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Finding Untested Database Operations"
echo "-----------------------------------------"
echo ""

echo "PostgreSQL schemas:"
docker exec athena-postgres psql -U postgres -d knowledge_base -c "\dt" 2>/dev/null | head -15 || echo "⚠️ No direct access or empty"

echo ""
echo "Redis keys:"
docker exec athena-redis redis-cli DBSIZE 2>/dev/null || echo "⚠️ Redis check failed"

echo ""
echo "Weaviate classes:"
curl -s http://localhost:8090/v1/schema | jq -r '.classes[].class' | head -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Checking for Unused Services"
echo "---------------------------------"
echo ""

echo "Services in docker-compose but not tested:"
grep "container_name:" docker-compose.yml | awk '{print $2}' | while read container; do
  if ! grep -q "$container" COMPREHENSIVE_TEST_REPORT.md TESTING_COMPLETE_SUMMARY.md 2>/dev/null; then
    echo "  ⚠️ $container - Not mentioned in test reports"
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Finding Hidden Features in Source Code"
echo "-------------------------------------------"
echo ""

echo "Searching for 'TODO', 'FIXME', 'HACK' comments:"
grep -r "TODO\|FIXME\|HACK" services/ --include="*.py" 2>/dev/null | wc -l | xargs echo "  Found comments:"

echo ""
echo "Searching for experimental features:"
grep -r "experimental\|beta\|alpha" services/ --include="*.py" -i 2>/dev/null | grep -v "Binary" | head -5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ Integration Points Not Tested"
echo "----------------------------------"
echo ""

echo "Checking service-to-service calls:"
echo ""
echo "Router → Other Services:"
grep -o "http://[a-z-]*:[0-9]*" services/router/app.py 2>/dev/null | sort -u | head -10

echo ""
echo "UAI → Other Services:"
grep -o "http://[a-z-]*:[0-9]*" AI-Projects/universal-ai-tools/api/*.py 2>/dev/null | sort -u

echo ""
echo "==================================================="
echo "Audit Complete - Check output for gaps"

