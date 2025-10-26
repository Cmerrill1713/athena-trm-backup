#!/bin/bash
echo "🔍 DEEP VALIDATION - Searching for Missed Features"
echo "========================================================================"
echo ""

echo "1️⃣  Checking ALL running containers for undiscovered endpoints..."
echo "--------------------------------------------------------------------"

# Get all container ports
docker ps --format "{{.Names}}:{{.Ports}}" | while read line; do
    container=$(echo $line | cut -d: -f1)
    ports=$(echo $line | grep -o "127.0.0.1:[0-9]*" | cut -d: -f2 | head -1)
    
    if [ ! -z "$ports" ]; then
        echo "  Checking $container on port $ports..."
        
        # Try common endpoints
        for endpoint in "/health" "/docs" "/openapi.json" "/api/docs" "/metrics" "/status" "/info" "/v1" ""; do
            response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$ports$endpoint 2>/dev/null)
            if [ "$response" = "200" ] || [ "$response" = "307" ]; then
                echo "    ✅ Found: http://localhost:$ports$endpoint ($response)"
            fi
        done
    fi
done | head -50

echo ""
echo "2️⃣  Checking for services in docker-compose not running..."
echo "--------------------------------------------------------------------"

# Get services from docker-compose
services_defined=$(docker-compose config --services 2>/dev/null | wc -l)
services_running=$(docker-compose ps --services 2>/dev/null | wc -l)

echo "  Services defined: $services_defined"
echo "  Services running: $services_running"

if [ "$services_running" -lt "$services_defined" ]; then
    echo "  ⚠️  Some services not running:"
    docker-compose ps --services --filter "status=exited" 2>/dev/null || echo "    None exited"
fi

echo ""
echo "3️⃣  Searching for Python services we haven't tested..."
echo "--------------------------------------------------------------------"

# Find all main.py, app.py, server.py files
find services/ agi_core/ ai_republic/ -name "app.py" -o -name "main.py" -o -name "server.py" 2>/dev/null | \
  while read file; do
    echo "  Found: $file"
    # Check if it has endpoints
    endpoint_count=$(grep -E "@app\.(get|post)" "$file" 2>/dev/null | wc -l)
    if [ "$endpoint_count" -gt 0 ]; then
        echo "    → Has $endpoint_count endpoints"
    fi
done | head -30

echo ""
echo "✅ Deep search complete!"
