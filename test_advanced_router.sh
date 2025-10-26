#!/bin/bash

echo "🚦 Testing Advanced Router Features"
echo "===================================="
echo ""

# Test 1: Check current routing policy
echo "1️⃣ Routing Policy Check"
echo "-----------------------"
curl -s http://localhost:9113/health | jq '.policy'

echo ""
echo "2️⃣ Test MLX Provider (if available)"
echo "------------------------------------"
curl -s http://localhost:9113/health | jq '{
  mlx_available: .providers.mlx.available,
  mlx_requests: .providers.mlx.total_requests,
  mlx_failures: .providers.mlx.total_failures,
  mlx_latency_p95: .providers.mlx.p95_latency_ms
}'

echo ""
echo "3️⃣ Fallback Behavior Test"
echo "--------------------------"
echo "Note: Would need to simulate provider failure for full fallback test"
echo "Checking fallback configuration in policy..."
curl -s http://localhost:9113/health | jq '.policy.order'

echo ""
echo "4️⃣ Load Distribution Check"
echo "---------------------------"
echo "Current request distribution across providers:"
curl -s http://localhost:9113/health | jq '.providers | to_entries | map({provider: .key, requests: .value.total_requests, failures: .value.total_failures, error_rate: .value.error_rate}) | .[]' | jq -s '.'

echo ""
echo "5️⃣ Circuit Breaker Status"
echo "--------------------------"
curl -s http://localhost:9113/health | jq '.providers | to_entries | map({provider: .key, in_backoff: .value.in_backoff, consecutive_failures: .value.consecutive_failures}) | .[]' | jq -s '.'

echo ""
echo "===================================="
echo "Advanced Router Test Complete"
