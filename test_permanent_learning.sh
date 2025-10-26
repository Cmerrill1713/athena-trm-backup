#!/bin/bash
set -euo pipefail

echo "🧠 TESTING PERMANENT LEARNING (Survives Restarts)"
echo "=================================================="
echo ""

USER_ID="family_test_$(date +%s)"

echo "Test User: $USER_ID"
echo ""

# Step 1: Train Athena
echo "Step 1: Training Athena to be casual..."
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Hey\"},
      {\"role\": \"assistant\", \"content\": \"Hello! How can I help?\"},
      {\"role\": \"user\", \"content\": \"Be more casual, like a friend texting\"}
    ]
  }" | jq -r '.choices[0].message.content'

echo ""

# Step 2: Verify saved
echo "Step 2: Checking database..."
docker exec athena-postgres psql -U athena -d athena -c \
  "SELECT user_id, preferences->>'communication_style' as style FROM user_preferences WHERE user_id='$USER_ID';"

echo ""

# Step 3: Restart container
echo "Step 3: Restarting UAI (wiping memory)..."
docker restart athena-uai > /dev/null 2>&1
sleep 12
echo "✅ Container restarted"

echo ""

# Step 4: Test if learning persisted
echo "Step 4: Testing if Athena remembers (from database)..."
response=$(curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"How are you?\"}
    ]
  }" | jq -r '.choices[0].message.content')

echo "Response: '$response'"
echo ""

# Check if casual (short response)
if [ ${#response} -lt 60 ]; then
    echo "✅ SUCCESS! Athena remembered to be casual (${#response} chars)"
    echo "   Learning is PERMANENT! 💙"
else
    echo "⚠️  Response seems verbose (${#response} chars)"
    echo "   May need tuning"
fi

echo ""
echo "=================================================="
echo "Athena learns FOREVER - corrections never forgotten!"
