#!/bin/bash

echo "🌐 TESTING SERVICE NETWORK CONNECTIVITY"
echo "========================================"
echo ""

echo "1️⃣ Internal Docker Network Tests"
echo "----------------------------------"

echo "Can Canary Monitor reach Router?"
docker exec governance-canary-monitor curl -s http://athena-router:9113/health 2>&1 | head -3

echo ""
echo "Can Router reach UAI?"
docker exec athena-router curl -s http://athena-uai:8080/health 2>&1 | head -3

echo ""
echo "Can Autonomous reach Router?"
docker exec athena-autonomous curl -s http://athena-router:9113/health 2>&1 | head -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Testing All Knowledge Services Endpoints"
echo "---------------------------------------------"

echo "Knowledge Gateway - Advanced endpoints:"
curl -s http://localhost:8093/status 2>&1 | head -3
curl -s http://localhost:8093/api/documents 2>&1 | head -3

echo ""
echo "Knowledge Context - Context endpoints:"
curl -s http://localhost:8092/api/context 2>&1 | head -3

echo ""
echo "Knowledge Sync - Sync status:"
curl -s http://localhost:8089/api/sync/status 2>&1 | head -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Testing Additional UAI Endpoints"
echo "-------------------------------------"

echo "POST create task:"
curl -s -X POST http://localhost:8080/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Task","description":"Automated test","status":"pending"}' | jq -c '.'

echo ""
echo "GET task list after creation:"
curl -s http://localhost:8080/api/tasks/ | jq '. | length'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Testing Router Load Balancing"
echo "----------------------------------"

echo "Sending 10 routing requests to test load balancing:"
for i in {1..10}; do
  result=$(curl -s -X POST http://localhost:9113/route \
    -H "Content-Type: application/json" \
    -d "{\"prompt\":\"Load balance test $i\"}" | jq -r '.route')
  echo "  Request $i: routed to $result"
done

echo ""
echo "========================================"
echo "✅ Network Connectivity Tests Complete"

