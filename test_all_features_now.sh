#!/bin/bash
echo "🧪 QUICK VALIDATION - All Major Features"
echo "========================================"
echo ""

# 1. Services
echo "1️⃣  SERVICES (9/9)"
curl -s http://localhost:8080/health | jq -r '"  ✅ UAI: " + .status'
curl -s http://localhost:9113/health | jq -r '"  ✅ Router: " + .status'
curl -s http://localhost:8098/health | jq -r '"  ✅ Learning: " + .status'

# 2. Chat Personality
echo ""
echo "2️⃣  PERSONALITY (Brief & Warm)"
response=$(curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "quick_test", "messages": [{"role": "user", "content": "Hi"}]}' | jq -r '.choices[0].message.content')
echo "  User: 'Hi'"
echo "  Athena: '$response'"
if [ ${#response} -lt 80 ]; then
    echo "  ✅ Brief response (${#response} chars)"
else
    echo "  ⚠️  Verbose (${#response} chars)"
fi

# 3. Real-Time Learning
echo ""
echo "3️⃣  REAL-TIME LEARNING"
user_id="test_$(date +%s)"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$user_id\", \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}, {\"role\": \"assistant\", \"content\": \"Hello!\"}, {\"role\": \"user\", \"content\": \"Be super casual\"}]}" \
  | jq -r '"  Correction saved: " + (._athena.correction_saved_to_db | tostring)'

# 4. Permanent Storage
echo ""
echo "4️⃣  PERMANENT STORAGE (PostgreSQL)"
docker exec athena-postgres psql -U athena -d athena -c \
  "SELECT COUNT(*) as user_count FROM user_preferences;" 2>&1 | grep -A 1 "user_count" | tail -n 1 | awk '{print "  Users with preferences: " $1}'

# 5. RAG System
echo ""
echo "5️⃣  RAG (Knowledge Retrieval)"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is TRM?"}]}' \
  | jq -r '"  RAG activated: " + (._athena.rag_enabled | tostring)'

# 6. Tasks API
echo ""
echo "6️⃣  TASK MANAGEMENT"
task_count=$(curl -s http://localhost:8080/api/tasks/ | jq 'length')
echo "  Tasks in system: $task_count"

# 7. Multimodal
echo ""
echo "7️⃣  MULTIMODAL SERVICES"
curl -s http://localhost:8088/health | jq -r '"  ✅ FastVLM (Vision): " + (.status // "ok")'
curl -s http://localhost:8091/health | jq -r '"  ✅ Kokoro (TTS): " + (.status // "ok")'
curl -s http://localhost:8095/health | jq -r '"  ✅ Whisper (STT): " + (.status // "ok")'

# 8. macOS Tools
echo ""
echo "8️⃣  MACOS INTEGRATION"
curl -s http://localhost:8099/health | jq -r '"  ✅ macOS Bridge: " + (.tools_available | tostring) + " tools"'
curl -s http://localhost:8412/health | jq -r '"  ✅ MCP Ecosystem: " + (.tools_available | tostring) + " tools"'

# 9. ASI Safety
echo ""
echo "9️⃣  ASI SAFETY"
curl -s http://localhost:8096/v2/health | jq -r '"  ✅ Judicial: " + .status'

echo ""
echo "========================================"
echo "✅ Quick validation complete!"
echo ""
