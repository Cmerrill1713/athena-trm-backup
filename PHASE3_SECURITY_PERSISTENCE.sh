#!/bin/bash

echo "🔒 PHASE 3: SECURITY & DATA PERSISTENCE AUDIT"
echo "=============================================="
echo ""

echo "1️⃣ Security Configuration Audit"
echo "---------------------------------"

echo "Checking for exposed ports (should be 127.0.0.1 only):"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -v "127.0.0.1" | grep -v "PORTS" || echo "  ✅ All ports properly bound to localhost"

echo ""
echo "Checking for secrets in environment variables:"
docker exec athena-uai env | grep -iE "password|secret|key|token" || echo "  ✅ No obvious secrets in UAI env"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Data Persistence Testing"
echo "-----------------------------"

echo "Testing PostgreSQL data persistence:"
echo "  Current routing_outcomes count:"
docker exec athena-postgres psql -U postgres -d athena_db -c "SELECT COUNT(*) FROM routing_outcomes;" 2>/dev/null | grep -A 1 "count"

echo ""
echo "  Inserting test record:"
docker exec athena-postgres psql -U postgres -d athena_db -c "
INSERT INTO routing_outcomes (prompt, policy, selected_model, latency_ms, success, created_at)
VALUES ('Test audit query', '{}', 'test', 100, true, NOW())
RETURNING id, prompt;
" 2>/dev/null | grep -A 2 "Test audit"

echo ""
echo "  Verifying insert:"
docker exec athena-postgres psql -U postgres -d athena_db -c "SELECT COUNT(*) FROM routing_outcomes;" 2>/dev/null | grep -A 1 "count"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Weaviate Data Persistence Testing"
echo "--------------------------------------"

echo "Current object count:"
curl -s 'http://localhost:8090/v1/objects?limit=1' | jq '.totalResults // "unknown"'

echo ""
echo "Storing test object:"
test_id=$(curl -s -X POST http://localhost:8090/v1/objects \
  -H "Content-Type: application/json" \
  -d '{
    "class": "AIAgentLog",
    "properties": {
      "action": "phase3_audit",
      "result": "testing_persistence",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "metadata": "{\"audit\":\"phase3\"}"
    }
  }' | jq -r '.id' | cut -d'-' -f1)

echo "  Stored object ID prefix: $test_id"

echo ""
echo "Verifying storage:"
curl -s "http://localhost:8090/v1/objects?class=AIAgentLog&limit=1" | jq '.objects[0].properties | {action, result}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Redis Persistence Testing"
echo "------------------------------"

echo "Setting test key with TTL:"
docker exec athena-redis redis-cli SETEX "audit:phase3:test" 3600 "persistence_test_value" > /dev/null

echo "  Verifying:"
docker exec athena-redis redis-cli GET "audit:phase3:test"

echo ""
echo "Testing Redis persistence mode:"
docker exec athena-redis redis-cli CONFIG GET save | tail -1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Volume Mount Audit"
echo "----------------------"

echo "Checking for persistent volumes:"
docker volume ls | grep athena || echo "  ℹ️  No named athena volumes (using bind mounts?)"

echo ""
echo "Checking bind mounts in docker-compose:"
grep -A 1 "volumes:" docker-compose.yml | grep "/" | head -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ API Authentication Audit"
echo "----------------------------"

echo "Testing if APIs require authentication:"
echo "  UAI (should allow anonymous):"
curl -s http://localhost:8080/health -o /dev/null -w "  Status: %{http_code}\n"

echo ""
echo "  Router (should allow anonymous):"
curl -s http://localhost:9113/health -o /dev/null -w "  Status: %{http_code}\n"

echo ""
echo "  Prometheus (should allow anonymous):"
curl -s http://localhost:9090/api/v1/status/config -o /dev/null -w "  Status: %{http_code}\n"

echo ""
echo "  Grafana (may require auth):"
curl -s http://localhost:3001/api/health -o /dev/null -w "  Status: %{http_code}\n"

echo ""
echo "=============================================="
echo "✅ Phase 3 Audit Complete"

