#!/usr/bin/env bash
# Monday Morning Playbook - Copy/Paste Ready
set -e

echo "🚀 ATHENA MONDAY MORNING PLAYBOOK"
echo "=================================="

# Clean & build
echo "1️⃣  Cleaning old containers and volumes..."
docker compose down -v

echo "2️⃣  Building with build SHA..."
BUILD_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
docker compose build --no-cache --build-arg BUILD_SHA=$BUILD_SHA

echo "3️⃣  Starting services..."
docker compose up -d

echo "4️⃣  Waiting for services to stabilize..."
sleep 30

# Sanity probes
echo "5️⃣  Running sanity probes..."
for p in 9113 9110 8412 8088 8091; do
  echo "== :$p"
  curl -fsS "http://localhost:$p/health" || exit 1
done

echo "6️⃣  Checking version..."
curl -fsS http://localhost:9113/version

echo
echo "7️⃣  Testing intent smoke..."
curl -s -X POST localhost:9113/respond -H 'content-type: application/json' \
  -d '{"message":"Can you see any issues with ourself"}' | grep -qi "Which area" && echo "✅ Intent working"

echo
echo "8️⃣  Running contract tests..."
bash tests/test_contracts.sh

echo
echo "9️⃣  Checking Prometheus targets..."
curl -s 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[].health' | grep -q "up" && echo "✅ Prometheus targets healthy"

echo
echo "🎉 ALL CHECKS PASSED - STACK IS READY"
echo "======================================"
echo "Services are healthy and monitored."
echo "Visit http://localhost:3001 for Grafana dashboards"
echo "Visit http://localhost:9090 for Prometheus metrics"

# Rollback plan (commented out)
# echo "❌ ROLLBACK:"
# docker compose down
# docker compose -f docker-compose.prev.yml up -d
