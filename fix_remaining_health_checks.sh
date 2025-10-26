#!/bin/bash

echo "🔧 FIXING ALL REMAINING HEALTH CHECKS"
echo "======================================"
echo ""

echo "Phase 1: Add curl to Remaining Governance Containers"
echo "------------------------------------------------------"

# Find all governance Dockerfiles
echo "1. Fixing governance-orchestrator..."
if [ -f "governance/executive/Dockerfile.governance" ]; then
    if ! grep -q "curl" governance/executive/Dockerfile.governance; then
        sed -i '' '/^FROM/a\
\
# Install curl for health checks\
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
' governance/executive/Dockerfile.governance
        echo "   ✅ Added curl"
    else
        echo "   ✅ Already has curl"
    fi
else
    echo "   ⚠️  Dockerfile not found"
fi

echo ""
echo "2. Fixing AGI remediator..."
if [ -f "agi_core/Dockerfile.remediator" ]; then
    if ! grep -q "curl" agi_core/Dockerfile.remediator; then
        sed -i '' '/^FROM/a\
\
# Install curl for health checks\
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
' agi_core/Dockerfile.remediator
        echo "   ✅ Added curl"
    else
        echo "   ✅ Already has curl"
    fi
else
    echo "   ⚠️  Dockerfile not found, searching..."
    find . -name "*remediator*" -type f 2>/dev/null | grep -i docker | head -5
fi

echo ""
echo "3. Fixing governance-metrics-exporter..."
if [ -f "governance/observability/Dockerfile.metrics" ]; then
    if ! grep -q "curl" governance/observability/Dockerfile.metrics; then
        sed -i '' '/^FROM/a\
\
# Install curl for health checks\
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
' governance/observability/Dockerfile.metrics
        echo "   ✅ Added curl"
    else
        echo "   ✅ Already has curl"
    fi
else
    echo "   ⚠️  Dockerfile not found"
fi

echo ""
echo "======================================"
echo "✅ Phase 1 Complete"
echo ""
echo "Next: Find actual Dockerfile locations"

