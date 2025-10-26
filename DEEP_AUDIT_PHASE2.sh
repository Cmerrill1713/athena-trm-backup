#!/bin/bash

echo "🔍 DEEP AUDIT PHASE 2 - Edge Cases & Hidden Features"
echo "======================================================"
echo ""

echo "1️⃣ Testing Error Handling & Edge Cases"
echo "----------------------------------------"

# Test invalid inputs
echo "Testing invalid chat request (empty messages):"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": []}' | jq -c '{status: .error // "OK", detail: .detail // "passed"}'

echo ""
echo "Testing malformed JSON:"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{invalid json}' 2>&1 | head -1

echo ""
echo "Testing missing required fields:"
curl -s -X POST http://localhost:9113/route \
  -H "Content-Type: application/json" \
  -d '{}' | jq -c '{status: .error // "OK", detail: .detail // "passed"}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Testing Rate Limits & Concurrent Requests"
echo "----------------------------------------------"

echo "Sending 5 concurrent requests to UAI:"
for i in {1..5}; do
  (curl -s -X POST http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"Test '"$i"'"}],"max_tokens":5}' \
    -w " - Request $i: %{http_code}\n") &
done
wait

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Checking Docker Container Health"
echo "-------------------------------------"

echo "Container status (last 10):"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -11

echo ""
echo "Unhealthy or restarting containers:"
docker ps -a | grep -E "unhealthy|Restarting" || echo "  ✅ All containers healthy"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Checking Resource Usage"
echo "---------------------------"

echo "Top 5 containers by CPU:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -6

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Analyzing Logs for Errors"
echo "------------------------------"

echo "Recent errors in UAI:"
docker logs athena-uai --tail 50 2>&1 | grep -i "error\|exception\|fail" | tail -3 || echo "  ✅ No recent errors"

echo ""
echo "Recent errors in Router:"
docker logs athena-router --tail 50 2>&1 | grep -i "error\|exception\|fail" | tail -3 || echo "  ✅ No recent errors"

echo ""
echo "Recent errors in Autonomous:"
docker logs athena-autonomous --tail 50 2>&1 | grep -i "error\|exception\|fail" | tail -3 || echo "  ✅ No recent errors"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ Testing Database Persistence"
echo "---------------------------------"

echo "Testing PostgreSQL connection pool:"
docker exec athena-postgres psql -U postgres -d athena_db -c "SELECT count(*) as total_connections FROM pg_stat_activity;" 2>/dev/null

echo ""
echo "Testing data persistence (routing_outcomes):"
docker exec athena-postgres psql -U postgres -d athena_db -c "SELECT COUNT(*) as total_records, MAX(created_at) as latest FROM routing_outcomes;" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "7️⃣ Testing Service Dependencies"
echo "---------------------------------"

echo "UAI → Weaviate connectivity:"
docker exec athena-uai curl -s http://athena-weaviate:8080/v1/meta > /dev/null && echo "  ✅ Connected" || echo "  ❌ Failed"

echo ""
echo "Router → Ollama connectivity:"
curl -s http://localhost:9113/health | jq -r '.providers[] | select(.name=="ollama") | "  " + .status'

echo ""
echo "Autonomous → UAI connectivity:"
docker exec athena-autonomous curl -s http://athena-uai:8080/health > /dev/null && echo "  ✅ Connected" || echo "  ❌ Failed"

echo ""
echo "======================================================"
echo "✅ Deep Audit Phase 2 Complete"

