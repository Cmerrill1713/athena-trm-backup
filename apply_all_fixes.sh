#!/bin/bash

echo "🚀 APPLYING ALL FIXES"
echo "====================="
echo ""

echo "Step 1: Rebuild services with updated Dockerfiles"
echo "---------------------------------------------------"
echo "Building governance-canary-monitor (now with curl)..."
docker-compose build governance-canary-monitor

echo ""
echo "Step 2: Restart services with fixed health checks"
echo "--------------------------------------------------"
echo "Restarting athena-router (fixed health check)..."
docker-compose up -d athena-router

echo ""
echo "Restarting athena-fastvlm (fixed health check)..."
docker-compose up -d athena-fastvlm

echo ""
echo "Restarting athena-kokoro (fixed health check)..."
docker-compose up -d athena-kokoro

echo ""
echo "Restarting governance-canary-monitor (added curl)..."
docker-compose up -d governance-canary-monitor

echo ""
echo "Recreating athena-proxy (fixed port binding)..."
docker-compose up -d --force-recreate athena-proxy

echo ""
echo "Step 3: Fix open-webui port binding"
echo "------------------------------------"
echo "Stopping open-webui..."
docker stop open-webui 2>/dev/null || echo "  (not running)"

echo ""
echo "Removing old open-webui container..."
docker rm open-webui 2>/dev/null || echo "  (already removed)"

echo ""
echo "Starting open-webui with secure port binding..."
docker run -d \
  -p 127.0.0.1:3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name open-webui \
  --restart unless-stopped \
  --network athena_athena-network \
  ghcr.io/open-webui/open-webui:main

echo ""
echo "====================="
echo "✅ All fixes applied!"
echo ""
echo "Waiting 10 seconds for health checks..."
sleep 10

