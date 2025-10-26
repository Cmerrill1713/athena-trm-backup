#!/bin/bash

echo "🔍 INVESTIGATING UNHEALTHY CONTAINERS"
echo "======================================"
echo ""

echo "1️⃣ Router (unhealthy but responding)"
echo "--------------------------------------"
docker logs athena-router --tail 20 2>&1 | tail -10

echo ""
echo "Health check config:"
docker inspect athena-router | jq '.[0].Config.Healthcheck'

echo ""
echo "Testing router health endpoint:"
curl -s http://localhost:9113/health | jq '{status: .status, providers: [.providers[].name]}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ OTEL Collector (unhealthy)"
echo "-------------------------------"
docker logs athena-otel-collector --tail 20 2>&1 | tail -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Governance Services (unhealthy)"
echo "------------------------------------"
echo "Governance Orchestrator:"
curl -s http://localhost:9110/health 2>&1 | head -3

echo ""
echo "Canary Monitor:"
docker logs governance-canary-monitor --tail 10 2>&1 | tail -5

echo ""
echo "AGI Remediator:"
curl -s http://localhost:9112/health 2>&1 | head -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Multimodal Services (unhealthy)"
echo "------------------------------------"
echo "FastVLM:"
curl -s http://localhost:8088/health 2>&1 | head -3

echo ""
echo "Kokoro TTS:"
curl -s http://localhost:8091/health 2>&1 | head -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Checking Health Check Scripts"
echo "----------------------------------"

echo "Looking for health check endpoints in docker-compose.yml:"
grep -A 2 "healthcheck:" docker-compose.yml | head -20

echo ""
echo "======================================"
echo "✅ Investigation Complete"

