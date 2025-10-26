#!/bin/bash

echo "🔍 INVESTIGATING FINAL 3 UNHEALTHY CONTAINERS"
echo "==============================================="
echo ""

echo "1️⃣ Governance Canary Monitor"
echo "------------------------------"

echo "Health check command:"
docker inspect governance-canary-monitor --format='{{range .Config.Healthcheck.Test}}{{.}} {{end}}'

echo ""
echo "Testing health check manually:"
docker exec governance-canary-monitor curl -f http://localhost:9111/health 2>&1 || echo "  ❌ Failed"

echo ""
echo "Checking if service exposes /health endpoint:"
docker exec governance-canary-monitor cat /app/governance/executive/canary_monitor.py 2>/dev/null | grep -E "def.*health|@app.get.*health" | head -5 || echo "  ℹ️  No /health endpoint found in code"

echo ""
echo "Service type:"
docker exec governance-canary-monitor ps aux 2>/dev/null | grep python

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Governance Metrics Exporter"
echo "--------------------------------"

echo "Health check command:"
docker inspect governance-metrics-exporter --format='{{range .Config.Healthcheck.Test}}{{.}} {{end}}'

echo ""
echo "Testing health check manually:"
docker exec -u 0 governance-metrics-exporter curl -f http://localhost:8000/health 2>&1 || echo "  Testing failed"

echo ""
echo "Checking actual port:"
docker exec governance-metrics-exporter netstat -tlnp 2>/dev/null | grep LISTEN || docker exec governance-metrics-exporter ss -tlnp 2>/dev/null | grep LISTEN || echo "  ℹ️  netstat/ss not available"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ OTEL Collector"
echo "------------------"

echo "Health check command:"
docker inspect athena-otel-collector --format='{{range .Config.Healthcheck.Test}}{{.}} {{end}}'

echo ""
echo "Testing health endpoint:"
curl -s http://localhost:13133 2>&1 | head -5 || echo "  External test"

echo ""
echo "Testing from inside container:"
docker exec athena-otel-collector wget --quiet --tries=1 --spider http://localhost:13133 2>&1 && echo "  ✅ wget successful" || echo "  ❌ wget failed"

echo ""
echo "==============================================="
echo "✅ Investigation Complete"

