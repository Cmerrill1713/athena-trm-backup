#!/bin/bash

echo "🏥 FIXING ALL CONTAINER HEALTH CHECKS"
echo "======================================"
echo ""

echo "Phase 1: Fix Health Check URLs"
echo "-------------------------------"

# Backup
cp docker-compose.yml docker-compose.yml.healthcheck_backup

# Fix FastVLM health check (missing port)
echo "1. Fixing FastVLM health check..."
sed -i '' 's|curl -fsS http://localhost:${FASTVLM_PORT}/health|curl -fsS http://localhost:8088/health|' docker-compose.yml
echo "   ✅ Fixed"

# Fix Kokoro health check (missing port)  
echo "2. Fixing Kokoro health check..."
sed -i '' 's|curl -fsS http://localhost:${KOKORO_PORT}/health|curl -fsS http://localhost:8091/health|' docker-compose.yml
echo "   ✅ Fixed"

echo ""
echo "Phase 2: Update Dockerfiles to Install curl"
echo "--------------------------------------------"

# Fix governance canary monitor
echo "3. Adding curl to governance-canary-monitor Dockerfile..."
if [ -f "governance/executive/Dockerfile.canary" ]; then
    if ! grep -q "curl" governance/executive/Dockerfile.canary; then
        # Add curl installation after FROM line
        sed -i '' '/^FROM/a\
\
# Install curl for health checks\
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
' governance/executive/Dockerfile.canary
        echo "   ✅ Added curl to canary monitor"
    else
        echo "   ✅ Already has curl"
    fi
else
    echo "   ⚠️  File not found, skipping"
fi

# Fix governance orchestrator  
echo "4. Adding curl to governance-orchestrator Dockerfile..."
if [ -f "governance/executive/Dockerfile.governance" ]; then
    if ! grep -q "curl" governance/executive/Dockerfile.governance; then
        sed -i '' '/^FROM/a\
\
# Install curl for health checks\
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
' governance/executive/Dockerfile.governance
        echo "   ✅ Added curl to orchestrator"
    else
        echo "   ✅ Already has curl"
    fi
else
    echo "   ⚠️  File not found, skipping"
fi

echo ""
echo "======================================"
echo "✅ Health check fixes applied!"
echo ""
echo "Next: Restart services to apply fixes"

