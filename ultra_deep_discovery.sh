#!/bin/bash
echo "🔬 ULTRA DEEP DISCOVERY - Configuration & System Level"
echo "========================================================================"
echo ""

echo "1️⃣  Checking Docker volumes for stored features..."
echo "--------------------------------------------------------------------"
docker volume ls --format "{{.Name}}" | grep athena | head -15

echo ""
echo "2️⃣  Checking environment variables across all services..."
echo "--------------------------------------------------------------------"
docker-compose config | grep -E "^\s+- [A-Z_]+=.+" | sort -u | head -30

echo ""
echo "3️⃣  Checking for initialization scripts..."
echo "--------------------------------------------------------------------"
find . -name "init*.py" -o -name "init*.sh" -o -name "init*.sql" -o -name "setup*.py" 2>/dev/null | \
  grep -v node_modules | grep -v ".git" | grep -v archive | head -20

echo ""
echo "4️⃣  Checking for migration/schema files..."
echo "--------------------------------------------------------------------"
find . -name "*migration*" -o -name "*schema*" -o -name "*.sql" 2>/dev/null | \
  grep -v node_modules | grep -v ".git" | grep -v archive | grep -v governance/legislative | head -15

echo ""
echo "5️⃣  Checking for configuration YAML/JSON files..."
echo "--------------------------------------------------------------------"
find services/ agi_core/ ai_republic/ governance/ -name "*.yaml" -o -name "*.yml" -o -name "config.json" 2>/dev/null | \
  grep -v node_modules | head -15

echo ""
echo "6️⃣  Checking for Makefile targets (automation)..."
echo "--------------------------------------------------------------------"
if [ -f "Makefile" ]; then
    grep "^[a-z][a-z-]*:" Makefile | head -20
else
    echo "  No Makefile found"
fi

echo ""
echo "✅ Ultra deep discovery complete!"
