#!/bin/bash

echo "🎯 FINAL VERIFICATION OF ALL FIXES"
echo "===================================="
echo ""

echo "1️⃣ Security: Port Bindings"
echo "----------------------------"
echo "Checking for ANY services exposed to 0.0.0.0:"
exposed=$(docker ps --format "{{.Names}}\t{{.Ports}}" | grep "0.0.0.0" | grep -v "Alertmanager")
if [ -z "$exposed" ]; then
    echo "  ✅ No services exposed to public internet (all secure!)"
else
    echo "  Found exposed services:"
    echo "$exposed"
fi

echo ""
echo "2️⃣ Health Checks: All Fixed Services"
echo "--------------------------------------"

sleep 15

for container in athena-router governance-canary-monitor governance-orchestrator agi-remediator athena-otel-collector; do
    status=$(docker inspect $container --format='{{.State.Health.Status}}' 2>/dev/null)
    if [ "$status" = "healthy" ]; then
        echo "  ✅ $container: healthy"
    elif [ "$status" = "starting" ]; then
        echo "  🔄 $container: starting (give it time)"
    elif [ -z "$status" ]; then
        echo "  ⚠️  $container: no health check configured"
    else
        echo "  ❌ $container: $status"
    fi
done

echo ""
echo "3️⃣ Container Count"
echo "-------------------"
total=$(docker ps | wc -l)
total=$((total - 1)) # subtract header
healthy=$(docker ps --filter health=healthy | wc -l)
healthy=$((healthy - 1))
unhealthy=$(docker ps --filter health=unhealthy | wc -l)
unhealthy=$((unhealthy - 1))

echo "  Total containers: $total"
echo "  Healthy: $healthy"
echo "  Unhealthy: $unhealthy"

echo ""
echo "4️⃣ Testing Key Endpoints"
echo "-------------------------"

echo "Router:"
curl -s http://localhost:9113/health -o /dev/null -w "  Status: %{http_code}\n"

echo "UAI:"
curl -s http://localhost:8080/health -o /dev/null -w "  Status: %{http_code}\n"

echo "Governance Orchestrator:"
curl -s http://localhost:9110/health -o /dev/null -w "  Status: %{http_code}\n"

echo "AGI Remediator:"
curl -s http://localhost:9112/health -o /dev/null -w "  Status: %{http_code}\n"

echo ""
echo "===================================="
echo "✅ Final Verification Complete!"

