#!/bin/bash

echo "🔍 DIAGNOSING REMAINING UNHEALTHY CONTAINERS"
echo "=============================================="
echo ""

echo "1️⃣ governance-canary-monitor"
echo "------------------------------"
echo "Issue: No HTTP server, it's a background monitoring script"
echo ""
echo "Checking if process is running:"
docker exec governance-canary-monitor ps aux | grep python

echo ""
echo "Current health check:"
docker inspect governance-canary-monitor --format='{{range .Config.Healthcheck.Test}}{{.}} {{end}}'

echo ""
echo "Testing process check:"
docker exec governance-canary-monitor pgrep -f python && echo "  ✅ Process running" || echo "  ❌ No process found"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ athena-otel-collector"
echo "-------------------------"
echo "Issue: wget not found in container"
echo ""
echo "Testing if wget exists:"
docker exec athena-otel-collector which wget 2>&1 || echo "  ❌ wget not installed"

echo ""
echo "Testing health endpoint directly:"
curl -s http://localhost:13133 | jq '.status' || echo "External check"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ athena-fastvlm"
echo "------------------"
echo "Checking if curl exists:"
docker exec athena-fastvlm which curl 2>&1 || echo "  ❌ curl not installed"

echo ""
echo "Testing endpoint:"
curl -s http://localhost:8088/health | jq '.'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ athena-kokoro"
echo "-----------------"
echo "Checking if curl exists:"
docker exec athena-kokoro which curl 2>&1 || echo "  ❌ curl not installed"

echo ""
echo "Testing endpoint:"
curl -s http://localhost:8091/health | jq '.'

echo ""
echo "=============================================="
echo "✅ Diagnosis Complete"

