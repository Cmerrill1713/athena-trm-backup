#!/bin/bash

echo "🔎 TESTING UNDOCUMENTED ENDPOINTS"
echo "=================================="
echo ""

echo "1️⃣ UAI Task Completion Endpoint"
echo "---------------------------------"

echo "Completing task #1:"
curl -s -X PUT http://localhost:8080/api/tasks/1/complete | jq '.'

echo ""
echo "Verifying task status:"
curl -s http://localhost:8080/api/tasks/1 | jq '{id, title, status}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ UAI TTS /speak Endpoint"
echo "----------------------------"

echo "Testing POST /api/tts/speak:"
curl -s -X POST http://localhost:8080/api/tts/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"Testing speech synthesis","voice":"en_US-female"}' | jq '.'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Router Intent Analysis"
echo "--------------------------"

echo "Checking if router has /intent endpoint:"
curl -s -X POST http://localhost:9113/intent \
  -H "Content-Type: application/json" \
  -d '{"prompt":"I want to analyze an image of a cat"}' 2>&1 | head -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Router RAG Capabilities"
echo "---------------------------"

echo "Checking for /rag endpoint:"
curl -s http://localhost:9113/rag 2>&1 | head -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ Router AGI Proxy"
echo "--------------------"

echo "Checking for /agi endpoint:"
curl -s http://localhost:9113/agi 2>&1 | head -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ Prometheus Metrics Analysis"
echo "--------------------------------"

echo "UAI LLM call metrics:"
curl -s http://localhost:8080/metrics | grep "uai_llm_calls_total{" | head -5

echo ""
echo "Router decision metrics:"
curl -s http://localhost:9113/metrics | grep "athena_router_decisions_count_total{" | head -5

echo ""
echo "Router failover metrics:"
curl -s http://localhost:9113/metrics | grep "athena_router_failovers_count_total" | head -3

echo ""
echo "=================================="
echo "✅ Undocumented Endpoint Tests Complete"

