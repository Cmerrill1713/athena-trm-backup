#!/bin/bash
echo "💾 CHECKING DATABASE FEATURES"
echo "========================================================================"
echo ""

echo "1️⃣  PostgreSQL - Tables and Features..."
echo "--------------------------------------------------------------------"
docker exec athena-postgres psql -U athena -d athena -c "\dt" 2>/dev/null | head -20

echo ""
echo "2️⃣  PostgreSQL - Checking for stored procedures..."
echo "--------------------------------------------------------------------"
docker exec athena-postgres psql -U athena -d athena -c "\df" 2>/dev/null | head -15

echo ""
echo "3️⃣  Weaviate - Checking schemas..."
echo "--------------------------------------------------------------------"
curl -s http://localhost:8090/v1/schema 2>/dev/null | jq -r '.classes[].class' 2>/dev/null | head -10

echo ""
echo "4️⃣  Weaviate - Object count..."
echo "--------------------------------------------------------------------"
curl -s http://localhost:8090/v1/objects 2>/dev/null | jq -r '.objects | length' 2>/dev/null

echo ""
echo "5️⃣  Redis - Checking keys..."
echo "--------------------------------------------------------------------"
docker exec athena-redis redis-cli DBSIZE 2>/dev/null || echo "  Redis check failed"

echo ""
echo "✅ Database feature check complete!"
