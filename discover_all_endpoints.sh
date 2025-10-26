#!/bin/bash

echo "🔎 DISCOVERING ALL UNTESTED ENDPOINTS"
echo "======================================"
echo ""

echo "📍 UAI (8080) - UNEXPLORED ENDPOINTS"
echo "------------------------------------"

# Test task management
echo "Testing /api/tasks/..."
curl -s http://localhost:8080/api/tasks/ | jq '.' || echo "Not found or requires data"

echo ""
echo "Testing /api/users/..."
curl -s http://localhost:8080/api/users/ | jq '.' || echo "Not found or requires data"

echo ""
echo "Testing /api/tts/..."
curl -s http://localhost:8080/api/tts/health | jq '.'

echo ""
echo "Testing /api/tts/voices..."
curl -s http://localhost:8080/api/tts/voices | jq '.'

echo ""
echo "Testing /metrics..."
curl -s http://localhost:8080/metrics | head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📍 ROUTER (9113) - COMPLETE ENDPOINT LIST"
echo "------------------------------------------"

endpoints=(
  "/health"
  "/route"
  "/vision/analyze"
  "/tts/synthesize"
  "/respond"
  "/reload-policy"
  "/metrics"
)

for ep in "${endpoints[@]}"; do
  echo -n "  $ep: "
  if curl -s -m 2 "http://localhost:9113$ep" 2>/dev/null | head -c 50 >/dev/null 2>&1; then
    echo "✅ Exists"
  else
    echo "⚠️ Needs testing"
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📍 ATHENA API (8888) - UNEXPLORED"
echo "----------------------------------"

curl -s http://localhost:8888/ | head -10 || echo "Root endpoint check"

echo ""
echo "Testing common endpoints:"
for ep in "/health" "/api" "/models" "/tasks" "/agents"; do
  echo -n "  $ep: "
  curl -s -m 2 "http://localhost:8888$ep" 2>/dev/null >/dev/null && echo "✅" || echo "❌"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📍 KNOWLEDGE SERVICES - DEEP DIVE"
echo "----------------------------------"

echo "Knowledge Gateway (8093):"
for ep in "/" "/search" "/query" "/documents" "/index"; do
  echo -n "  $ep: "
  curl -s -m 2 "http://localhost:8093$ep" 2>/dev/null >/dev/null && echo "✅" || echo "❌"
done

echo ""
echo "Knowledge Context (8092):"
for ep in "/" "/context" "/retrieve" "/store"; do
  echo -n "  $ep: "
  curl -s -m 2 "http://localhost:8092$ep" 2>/dev/null >/dev/null && echo "✅" || echo "❌"
done

echo ""
echo "Knowledge Sync (8089):"
for ep in "/" "/sync" "/upload" "/status"; do
  echo -n "  $ep: "
  curl -s -m 2 "http://localhost:8089$ep" 2>/dev/null >/dev/null && echo "✅" || echo "❌"
done

echo ""
echo "======================================"
echo "Endpoint Discovery Complete"

