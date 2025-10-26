#!/bin/bash

echo "⚙️  CONFIGURATION & POLICY AUDIT"
echo "=================================="
echo ""

echo "1️⃣ Router Policy Analysis"
echo "--------------------------"

echo "Current routing policy:"
docker exec athena-router cat /app/policies/local_first.yaml 2>/dev/null | head -30

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Environment Variables Audit"
echo "--------------------------------"

echo "Router environment:"
docker exec athena-router env | grep -E "ENDPOINT|HOST|MODEL|PORT" | sort

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Discovering All Service APIs"
echo "----------------------------------"

echo "UAI API structure:"
docker exec athena-uai ls -la /app/api/ 2>/dev/null | grep "\.py$" | awk '{print "  " $NF}'

echo ""
echo "Router API structure:"
docker exec athena-router ls -la /app/ 2>/dev/null | grep "\.py$" | awk '{print "  " $NF}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Checking for Undocumented Endpoints"
echo "----------------------------------------"

echo "Searching for @router or @app decorators in UAI:"
docker exec athena-uai grep -r "@router\|@app\." /app/api/ 2>/dev/null | grep -v "pyc" | cut -d: -f2 | sort -u | head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Prometheus Metrics Discovery"
echo "---------------------------------"

echo "All registered metrics in UAI:"
curl -s http://localhost:8080/metrics | grep "^# TYPE" | head -15

echo ""
echo "All registered metrics in Router:"
curl -s http://localhost:9113/metrics | grep "^# TYPE" | head -15

echo ""
echo "=================================="
echo "✅ Configuration Audit Complete"

