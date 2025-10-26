#!/bin/bash

echo "🏥 Service Health Check"
echo "======================="
echo ""

services=(
  "8080:UAI Chat"
  "8088:FastVLM (Vision)"
  "8091:Kokoro TTS"
  "8412:MCP Ecosystem"
  "9110:Governance Orchestrator"
  "9111:Canary Monitor"
  "9113:Router"
  "8093:Knowledge Gateway"
  "8092:Knowledge Context"
  "8089:Knowledge Sync"
  "8014:Evolutionary API"
  "9112:AGI Remediator"
  "8888:Athena API"
)

for svc in "${services[@]}"; do
  IFS=':' read -r port name <<< "$svc"
  result=$(curl -s -m 2 "http://localhost:$port/health" 2>/dev/null | jq -r '.status // "TIMEOUT"' 2>/dev/null)
  
  if [ "$result" = "healthy" ] || [ "$result" = "ok" ]; then
    echo "✅ $name ($port): $result"
  else
    echo "❌ $name ($port): ${result:-FAIL}"
  fi
done

echo ""
echo "🐳 Docker Container Health:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "unhealthy|starting" || echo "✅ All containers healthy or running"

