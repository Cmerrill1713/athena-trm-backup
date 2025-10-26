#!/bin/bash

echo "⚠️  INVESTIGATING MLX PROVIDER FAILURES"
echo "========================================"
echo ""

echo "1️⃣ MLX Service Status"
echo "----------------------"

echo "MLX container status:"
docker ps | grep "mlx\|api" | head -5

echo ""
echo "Checking if Athena API (MLX endpoint) is running:"
curl -s http://localhost:8888/health 2>&1 | head -5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Router's View of MLX"
echo "------------------------"

echo "MLX provider stats from router:"
curl -s http://localhost:9113/health | jq '.providers.mlx'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Testing MLX Direct Connection"
echo "----------------------------------"

echo "Router thinks MLX is at: http://athena-api:8000"
echo "Testing from host:"
curl -s -m 2 http://localhost:8000/health 2>&1 || echo "  ❌ Not accessible from host"

echo ""
echo "Testing from router container:"
docker exec athena-router python3 -c "
import requests
try:
    r = requests.get('http://athena-api:8000/health', timeout=2)
    print(f'  Status: {r.status_code}')
    print(f'  Response: {r.text[:100]}')
except Exception as e:
    print(f'  ❌ Error: {e}')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Checking Available API Services"
echo "------------------------------------"

echo "All running services with 'api' in name:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -i api

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Router Failover Analysis"
echo "-----------------------------"

echo "All failover metrics:"
curl -s http://localhost:9113/metrics | grep "failover"

echo ""
echo "All provider error rates:"
curl -s http://localhost:9113/health | jq '.providers | to_entries[] | {name: .key, error_rate: .value.error_rate, failures: .value.total_failures}'

echo ""
echo "========================================"
echo "✅ MLX Investigation Complete"

