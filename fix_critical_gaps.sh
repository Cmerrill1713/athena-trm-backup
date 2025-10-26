#!/bin/bash
echo "🔧 FIXING CRITICAL GAPS"
echo "========================================================================"
echo ""

echo "1️⃣  Checking UAI → Learning wiring..."
echo "--------------------------------------------------------------------"

# Check if feedback.py exists and what it does
if [ -f "AI-Projects/universal-ai-tools/api/feedback.py" ]; then
    echo "  Found feedback.py"
    if grep -q "8098\|learning" AI-Projects/universal-ai-tools/api/feedback.py; then
        echo "  ✅ Already wired to Learning!"
    else
        echo "  ❌ NOT wired to Learning - needs fix"
    fi
else
    echo "  ❌ feedback.py not found"
fi

echo ""
echo "2️⃣  Checking which containers need health checks..."
echo "--------------------------------------------------------------------"

containers_needing_health="athena-weaviate athena-knowledge-gateway athena-proxy"

for container in $containers_needing_health; do
    if docker ps --filter "name=$container" --format "{{.Status}}" | grep -q "healthy"; then
        echo "  ✅ $container: has health check"
    else
        echo "  ❌ $container: needs health check"
    fi
done

echo ""
echo "3️⃣  Creating fixes..."
echo "--------------------------------------------------------------------"
echo "  Will create fix scripts for critical gaps"

echo ""
echo "✅ Gap analysis complete!"
echo "   Preparing fixes..."
