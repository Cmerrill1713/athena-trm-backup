#!/bin/bash
# Ask Athena to analyze the frontend and suggest improvements

ATHENA_URL="http://localhost:8080/v1"

echo "🎨 Asking Athena to analyze the frontend..."
echo ""

curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, analyzing your own frontend interface. Current features:\n\n- Chat interface (text input/output)\n- Task sidebar (create, list, complete tasks)\n- Family member selector\n- Voice input (STT via Whisper)\n- Voice output (TTS via Kokoro)\n- Image upload (vision via FastVLM)\n- Web search button\n- ArXiv search button\n- Service health status panel\n- User feedback buttons (thumbs up/down)\n- Model routing transparency\n- Real-time feedback\n\nBe thorough in your analysis. Think about usability, features, and family needs."
      },
      {
        "role": "user",
        "content": "Athena, looking at your current frontend interface (athena-chat.html), do you think we need to add anything else? \n\nWhat you have now:\n✅ Chat (text, voice, vision)\n✅ Task management sidebar\n✅ Family member profiles\n✅ Web/ArXiv search\n✅ Service health monitoring\n✅ User feedback (👍 👎)\n✅ Voice input/output\n✅ Image analysis\n\nAnalyze this from a family perspective:\n- What features would make daily life easier?\n- What'\''s missing for homework help?\n- What would help parents manage the household?\n- Are there UX improvements needed?\n- What about accessibility?\n- Any features for different age groups (kids vs parents)?\n\nBe specific and prioritize your suggestions!"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }' | jq -r '.choices[0].message.content'

echo ""
echo "---"
echo ""
echo "📊 Checking which model was selected..."
curl -s -X GET "http://localhost:9113/metrics" 2>/dev/null | grep "athena_router_model_selected" | tail -n 5 || echo "Router metrics not available"

echo ""
echo "✅ Frontend analysis complete!"
