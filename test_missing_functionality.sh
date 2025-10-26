#!/bin/bash

echo "🔬 TESTING ALL MISSING FUNCTIONALITY"
echo "====================================="
echo ""

echo "1️⃣ UAI TASK MANAGEMENT"
echo "----------------------"
echo "Get all tasks:"
curl -s http://localhost:8080/api/tasks/ | jq '.[] | {id, title, completed}'

echo ""
echo "Get specific task:"
curl -s http://localhost:8080/api/tasks/1 | jq '.'

echo ""
echo "Complete a task:"
curl -s -X POST http://localhost:8080/api/tasks/1/complete | jq '.'

echo ""
echo "Verify completion:"
curl -s http://localhost:8080/api/tasks/1 | jq '{id, title, completed}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ UAI USER MANAGEMENT"
echo "-----------------------"
echo "All users:"
curl -s http://localhost:8080/api/users/ | jq '.[] | {id, name, email, active}'

echo ""
echo "Get specific user:"
curl -s http://localhost:8080/api/users/1 | jq '.'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ UAI TTS INTEGRATION"
echo "-----------------------"
echo "TTS voices available:"
curl -s http://localhost:8080/api/tts/voices | jq '.available_voices'

echo ""
echo "Test TTS speak endpoint:"
curl -s -X POST http://localhost:8080/api/tts/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from UAI TTS", "voice": "sarah", "speed": "normal"}' \
  | jq 'if .audio then {audio_length: (.audio | length), format: "base64"} else . end'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ ATHENA API (8888) - COMPLETE EXPLORATION"
echo "--------------------------------------------"
curl -s http://localhost:8888/ | jq '.'

echo ""
echo "Models endpoint:"
curl -s http://localhost:8888/models | jq '.' | head -20

echo ""
echo "Tasks endpoint:"
curl -s http://localhost:8888/tasks | jq '.' | head -20

echo ""
echo "Agents endpoint:"
curl -s http://localhost:8888/agents | jq '.' | head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "5️⃣ KNOWLEDGE GATEWAY (8093) - ADVANCED RAG"
echo "-------------------------------------------"

echo "Testing search endpoint:"
curl -s -X POST http://localhost:8093/search \
  -H "Content-Type: application/json" \
  -d '{"query": "TRM training", "limit": 3}' \
  | jq '.' | head -30

echo ""
echo "Testing query endpoint:"
curl -s -X POST http://localhost:8093/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is TRM?"}' \
  | jq '.' | head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "6️⃣ ROUTER /respond ENDPOINT"
echo "----------------------------"

curl -s -X POST http://localhost:9113/respond \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?", "max_tokens": 50}' \
  | jq '.' | head -20

echo ""
echo "====================================="
echo "Missing Functionality Test Complete"

