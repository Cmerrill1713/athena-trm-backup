#!/bin/bash
echo "🔍 COMPREHENSIVE GAP ANALYSIS"
echo "========================================================================"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. MISSING WIRING BETWEEN SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking if UAI talks to Learning System..."
if grep -q "8098" AI-Projects/universal-ai-tools/api/chat.py 2>/dev/null; then
    echo "  ✅ UAI → Learning wired"
else
    echo "  ❌ UAI not wired to Learning System (port 8098)"
fi

echo ""
echo "Checking if Router talks to Judicial..."
if grep -q "8096\|judicial" services/router/app.py 2>/dev/null; then
    echo "  ✅ Router → Judicial wired"
else
    echo "  ❌ Router not wired to Judicial"
fi

echo ""
echo "Checking if UAI talks to Judicial..."
if grep -q "8096\|judicial" AI-Projects/universal-ai-tools/api/chat.py 2>/dev/null; then
    echo "  ✅ UAI → Judicial wired"
else
    echo "  ❌ UAI not wired to Judicial"
fi

echo ""
echo "Checking if AGI Core talks to Judicial..."
if grep -q "8096\|judicial" agi_core/*.py 2>/dev/null; then
    echo "  ✅ AGI → Judicial wired"
else
    echo "  ❌ AGI not wired to Judicial"
fi

echo ""
echo "Checking if Learning talks to AGI Core..."
if grep -q "8100\|agi" services/learning-agents/*.py 2>/dev/null; then
    echo "  ✅ Learning → AGI wired"
else
    echo "  ❌ Learning not wired to AGI Core"
fi

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. MISSING ENVIRONMENT VARIABLES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking docker-compose environment variables..."
missing_vars=0

# Check if critical env vars are set
if ! grep -q "DATABASE_URL" docker-compose.yml 2>/dev/null; then
    echo "  ⚠️  DATABASE_URL may not be set in some services"
    ((missing_vars++))
fi

if ! grep -q "JUDICIAL_URL" docker-compose.yml 2>/dev/null; then
    echo "  ⚠️  JUDICIAL_URL may not be set in some services"
    ((missing_vars++))
fi

if [ "$missing_vars" -eq 0 ]; then
    echo "  ✅ All critical env vars appear to be set"
else
    echo "  Found $missing_vars potential missing env vars"
fi

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. MISSING ERROR HANDLING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking for bare except blocks..."
bare_excepts=$(grep -r "except:" --include="*.py" services/ agi_core/ ai_republic/ AI-Projects/universal-ai-tools/api/ 2>/dev/null | grep -v "except Exception" | wc -l)
echo "  Found $bare_excepts bare except blocks (should be specific)"

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. MISSING HEALTH CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking all containers for health checks..."
docker ps --format "{{.Names}}: {{.Status}}" | grep -v "healthy" | grep -v "starting"

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. MISSING DOCUMENTATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking for README files..."
readme_count=$(find services/ agi_core/ ai_republic/ -name "README*" 2>/dev/null | wc -l)
service_count=$(find services/ -maxdepth 1 -type d 2>/dev/null | wc -l)
echo "  READMEs found: $readme_count"
echo "  Service directories: $service_count"
if [ "$readme_count" -lt "$service_count" ]; then
    echo "  ⚠️  Some services missing documentation"
else
    echo "  ✅ Good documentation coverage"
fi

echo ""
echo ""
echo "========================================================================"
echo "✅ COMPREHENSIVE GAP ANALYSIS COMPLETE!"
echo "========================================================================"
