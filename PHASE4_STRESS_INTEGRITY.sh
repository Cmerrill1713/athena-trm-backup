#!/bin/bash

echo "💪 PHASE 4: STRESS TESTING & DATA INTEGRITY"
echo "============================================="
echo ""

echo "1️⃣ Rapid Sequential Requests (Stress Test)"
echo "--------------------------------------------"

echo "Sending 20 rapid requests to UAI:"
start_time=$(date +%s)
success=0
failed=0

for i in {1..20}; do
  status=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Rapid test $i\"}],\"max_tokens\":5}" 2>&1)
  
  if [ "$status" = "200" ]; then
    ((success++))
  else
    ((failed++))
  fi
done

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "  Results: $success success, $failed failed in ${duration}s"
echo "  Rate: $((success / duration)) req/s"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Database Integrity Check"
echo "----------------------------"

echo "PostgreSQL constraints:"
docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT 
  conname as constraint_name,
  contype as constraint_type
FROM pg_constraint
WHERE conrelid = 'routing_outcomes'::regclass;
" 2>/dev/null

echo ""
echo "Checking for duplicate IDs:"
docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT id, COUNT(*) as count
FROM routing_outcomes
GROUP BY id
HAVING COUNT(*) > 1;
" 2>/dev/null | grep -A 1 "count"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Weaviate Data Integrity"
echo "---------------------------"

echo "Checking for schema consistency:"
curl -s http://localhost:8090/v1/schema | jq '.classes | length'
echo "  classes defined"

echo ""
echo "Checking object counts per class:"
for class in AIAgentLog AIContext AICustomTool AIMemory Docs DocsV2 LearnedPattern; do
  count=$(curl -s "http://localhost:8090/v1/objects?class=$class&limit=1" 2>/dev/null | jq -r '.totalResults // 0')
  echo "  $class: $count total objects"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Redis Memory Usage"
echo "----------------------"

docker exec athena-redis redis-cli INFO memory | grep "used_memory_human"
docker exec athena-redis redis-cli INFO stats | grep "total_commands_processed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Testing Router Under Load"
echo "------------------------------"

echo "Sending 10 routing requests simultaneously:"
pids=()
for i in {1..10}; do
  (curl -s -X POST http://localhost:9113/route \
    -H "Content-Type: application/json" \
    -d "{\"prompt\":\"Concurrent load test $i\"}" > /dev/null) &
  pids+=($!)
done

# Wait for all requests
wait_time=0
for pid in "${pids[@]}"; do
  wait $pid
  ((wait_time++))
done

echo "  All 10 requests completed"

echo ""
echo "Router stats after load:"
curl -s http://localhost:9113/health | jq '{
  mlx_requests: .providers.mlx.total_requests,
  uai_requests: .providers.uai.total_requests,
  total_uptime: .uptime_seconds
}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ Long-Running Service Health"
echo "--------------------------------"

echo "Services running > 2 hours:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep "hours"

echo ""
echo "Checking for container restarts:"
docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -i "restart" || echo "  ✅ No containers in restart loop"

echo ""
echo "============================================="
echo "✅ Phase 4 Complete"

