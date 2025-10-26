#!/bin/bash

echo "✅ VERIFYING ALL FIXES"
echo "======================"
echo ""

echo "1️⃣ Security: Port Bindings"
echo "---------------------------"
echo "Checking for exposed ports (should all be 127.0.0.1):"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "athena-proxy|open-webui" | while read line; do
  if echo "$line" | grep -q "0.0.0.0"; then
    echo "  ❌ $line"
  else
    echo "  ✅ $line"
  fi
done

echo ""
echo "2️⃣ Health Checks: Router"
echo "-------------------------"
sleep 15
echo "Waiting for services to stabilize..."

echo ""
echo "Router health check status:"
docker inspect athena-router --format='{{.State.Health.Status}}'

echo ""
echo "Router health check command:"
docker inspect athena-router --format='{{range .Config.Healthcheck.Test}}{{println .}}{{end}}' | head -2

echo ""
echo "3️⃣ Health Checks: Canary Monitor"
echo "----------------------------------"
echo "Canary monitor has curl:"
docker exec governance-canary-monitor which curl > /dev/null 2>&1 && echo "  ✅ curl installed" || echo "  ❌ curl not found"

echo ""
echo "4️⃣ Testing Router Health Endpoint"
echo "-----------------------------------"
curl -s http://localhost:9113/health | jq '{status: .status, uptime: .uptime_seconds}' 2>/dev/null || echo "  ⚠️  Endpoint not responding yet"

echo ""
echo "5️⃣ Testing UAI Health Endpoint"
echo "--------------------------------"
curl -s http://localhost:8080/health | jq '.' 2>/dev/null || echo "  ⚠️  Endpoint not responding yet"

echo ""
echo "6️⃣ Checking All Container Statuses"
echo "------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "athena-router|athena-proxy|open-webui|governance-canary|athena-fastvlm|athena-kokoro" | head -10

echo ""
echo "======================"
echo "✅ Verification Complete!"

