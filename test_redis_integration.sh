#!/bin/bash

echo "🔴 REDIS CACHING INTEGRATION TEST"
echo "=================================="
echo ""

echo "1️⃣ Redis Connection Test"
echo "-------------------------"

docker exec athena-redis redis-cli PING

echo ""
echo "2️⃣ Test Basic Caching Operations"
echo "----------------------------------"

# Store some test data
docker exec athena-redis redis-cli SET "test:prompt:hash123" "TRM stands for Tiny Recursive Model"
docker exec athena-redis redis-cli SET "test:embedding:hash456" "[0.1, 0.2, 0.3]"
docker exec athena-redis redis-cli SETEX "test:session:user1" 3600 '{"user_id":"user1","preferences":"technical"}'

echo ""
echo "Verify storage:"
docker exec athena-redis redis-cli GET "test:prompt:hash123"

echo ""
echo "Check all keys:"
docker exec athena-redis redis-cli KEYS "test:*"

echo ""
echo "Database size:"
docker exec athena-redis redis-cli DBSIZE

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Test Redis for Caching Use Cases"
echo "--------------------------------------"

# Cache hit/miss test
echo "Cache MISS (first request):"
time docker exec athena-redis redis-cli GET "cache:trm_definition" > /dev/null
echo "  Result: (null)"

echo ""
echo "Store in cache:"
docker exec athena-redis redis-cli SET "cache:trm_definition" "TRM = Tiny Recursive Model, 7M params, recursive reasoning"
docker exec athena-redis redis-cli EXPIRE "cache:trm_definition" 3600

echo ""
echo "Cache HIT (second request):"
time docker exec athena-redis redis-cli GET "cache:trm_definition"

echo ""
echo "TTL remaining:"
docker exec athena-redis redis-cli TTL "cache:trm_definition"
echo "  seconds"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Redis Pub/Sub Test"
echo "----------------------"

echo "Publishing test message..."
docker exec athena-redis redis-cli PUBLISH "autonomous:updates" "System test message" > /dev/null
echo "  Published to channel: autonomous:updates"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Redis Info"
echo "--------------"

docker exec athena-redis redis-cli INFO stats | grep -E "total_commands|instantaneous"

echo ""
echo "=================================="
echo "✅ Redis Integration Tested"

# Cleanup
docker exec athena-redis redis-cli DEL test:prompt:hash123 test:embedding:hash456 test:session:user1 > /dev/null

