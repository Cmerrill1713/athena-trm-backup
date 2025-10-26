#!/bin/bash

echo "🧪 TESTING JUDICIAL INTEGRATION WITH AI AGENTS"
echo "=============================================="
echo ""

echo "Step 1: Make a routing request (should trigger judicial oversight)"
echo "-------------------------------------------------------------------"
curl -s -X POST http://localhost:9113/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test routing with judicial oversight",
    "max_tokens": 50
  }' | jq -r '.route, .text' | head -5

echo ""
echo ""
echo "Step 2: Check Router logs for judicial submission"
echo "--------------------------------------------------"
docker logs athena-router --since 1m 2>&1 | grep -i "judicial" | tail -5

echo ""
echo ""
echo "Step 3: Check Judicial service logs for received events"
echo "--------------------------------------------------------"
docker logs ai-republic-judicial --since 1m 2>&1 | grep -E "POST|adjudicate|verdict" | tail -10

echo ""
echo ""
echo "Step 4: Query judicial service directly"
echo "----------------------------------------"
curl -s http://localhost:8096/v2/health | jq '.'

echo ""
echo ""
echo "✅ JUDICIAL INTEGRATION TEST COMPLETE"

