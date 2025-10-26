#!/bin/bash
# Remind Athena of the existing apps we found

ATHENA_URL="http://localhost:8080/v1"

echo "🤔 Reminding Athena about existing apps..."
echo ""

curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:14b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. Context: We already found these existing apps in your codebase:\n\n**Universal AI Tools has:**\n- Task Management API (GET/POST /api/tasks, PUT /api/tasks/{id}/complete)\n- User Management API (GET/POST /api/users)\n- TTS Service (POST /api/tts/synthesize)\n\n**NeuroForge has:**\n- Calendar Monitor (governance/observability/calendar_monitor.py)\n- Syncs with macOS Calendar\n- Quiet hours management\n\n**You already suggested:** Calendar, Task Management, Homework Help, Household Dashboard, Educational Library\n\nBe honest about whether you want to integrate with existing apps or build new ones."
      },
      {
        "role": "user",
        "content": "Athena, you just suggested we build:\n1. Family Calendar\n2. Homework Help Center  \n3. Household Management Dashboard\n4. Parental Controls\n5. Educational Content Library\n\nBut we already found these existing apps in your codebase:\n\n**Already Built:**\n✅ Task Management API (/api/tasks) - create, list, complete tasks\n✅ User Management API (/api/users) - family member profiles\n✅ Calendar Monitor (calendar_monitor.py) - syncs macOS Calendar\n✅ TTS Service (/api/tts/synthesize) - text-to-speech\n\nWe even wired Task Management into your UI already! (The 📋 Tasks sidebar)\n\n**Question:**\nDo you want to BUILD NEW apps for your suggestions, or should we INTEGRATE the existing apps you already have?\n\nFor example:\n- Calendar: Use existing calendar_monitor.py?\n- Tasks: Enhance existing /api/tasks?\n- Homework: Add mode to existing chat?\n\nBe specific - integrate existing or build new?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Athena'\''s response received!"
