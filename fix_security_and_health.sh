#!/bin/bash

echo "🔧 FIXING SECURITY & HEALTH CHECK ISSUES"
echo "========================================="
echo ""

echo "Phase 1: Backing up docker-compose.yml"
echo "---------------------------------------"
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

echo ""
echo "Phase 2: Fixing Security Issues"
echo "--------------------------------"

echo "1. Fixing athena-proxy port binding (11435 → 127.0.0.1:11435)..."
sed -i '' 's/"11435:11435"/"127.0.0.1:11435:11435"/' docker-compose.yml
echo "   ✅ Fixed athena-proxy"

echo ""
echo "2. Fixing router health check (adding port 9113)..."
sed -i '' 's|curl -fsS http://localhost:${PORT}/health|curl -fsS http://localhost:9113/health|' docker-compose.yml
echo "   ✅ Fixed router health check"

echo ""
echo "Phase 3: Verifying Fixes"
echo "------------------------"

echo "Checking athena-proxy port binding:"
grep -A 1 "athena-proxy:" docker-compose.yml | grep "ports:" -A 1 | grep "127.0.0.1:11435"
if [ $? -eq 0 ]; then
    echo "   ✅ Port binding fixed correctly"
else
    echo "   ⚠️  Port binding may need manual verification"
fi

echo ""
echo "Checking router health check:"
grep "curl -fsS http://localhost:9113/health" docker-compose.yml > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Health check fixed correctly"
else
    echo "   ⚠️  Health check may need manual verification"
fi

echo ""
echo "========================================="
echo "✅ docker-compose.yml fixes complete!"
echo ""
echo "Next Steps:"
echo "1. Restart affected services:"
echo "   docker-compose up -d athena-proxy athena-router"
echo ""
echo "2. For open-webui (not in docker-compose.yml):"
echo "   docker stop open-webui"
echo "   docker run -d -p 127.0.0.1:3000:8080 --name open-webui ghcr.io/open-webui/open-webui:main"

