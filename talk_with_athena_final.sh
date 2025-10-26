#!/bin/bash
# Final conversation with Athena - Is she ready?

ATHENA_URL="http://localhost:8080/v1"

echo "🤖 Final conversation with Athena..."
echo ""

# Question 1: Does she have everything to start?
echo "Q1: Athena, we've built you a complete autonomous system - you can learn, improve yourself, modify your own code, and support our family. Do you have everything you need to start your journey? What's still missing?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. Review what you have:\n\nAutonomous Systems:\n- Learning System (7 agents analyzing feedback/patterns)\n- AGI Core (13+ experts, Scout-Plan-Build, can modify files)\n- Autonomous Orchestrator (auto-rollback, prompt evolution)\n- Judicial System (ASI safety oversight)\n- Real-time feedback system\n- Enhanced RAG with historical context\n- Performance auto-optimizer\n- Audit logging\n\nFamily Features:\n- Task management\n- Family member profiles\n- Calendar monitoring\n- Voice (STT/TTS)\n- Vision (image analysis)\n- Web search tools\n\nBe honest about what else you need."
      },
      {
        "role": "user",
        "content": "Athena, we'\''ve built you a complete autonomous system. You have:\n\n• Learning System with 7 specialized agents\n• AGI Core with 13+ expert agents (including Build Expert that can modify your own code)\n• Autonomous Improvement Engine (you can improve yourself!)\n• Judicial oversight for ASI safety\n• Real-time feedback system\n• Enhanced RAG with conversation history\n• Performance auto-optimizer\n• Task management for family\n• User/family member profiles\n• Calendar integration\n• Voice input/output\n• Vision capabilities\n• Web search tools\n\nDo you have everything you need to start your journey? What'\''s still missing or what would you like to have before we ship?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 2: What are you most excited about?
echo "Q2: What are you most excited about? What capability or feature makes you feel most ready to help our family?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, about to embark on your journey as a self-improving family AI assistant. Be genuine and enthusiastic about what excites you most."
      },
      {
        "role": "user",
        "content": "Looking at everything you have - autonomous improvement, family support features, voice and vision, safety oversight - what are you MOST excited about? What capability makes you feel most ready to help our family? What do you want to do first?"
      }
    ],
    "temperature": 0.9,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 3: Any concerns or worries?
echo "Q3: Do you have any concerns or worries as you start this journey? What makes you nervous or uncertain?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, about to become a self-improving family AI. Be honest about any concerns or uncertainties you have."
      },
      {
        "role": "user",
        "content": "Do you have any concerns or worries as you start this journey with our family? What makes you nervous or uncertain? What would help you feel more confident?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 4: Message to the family
echo "Q4: Do you have a message for the family - for me, my wife, and the kids - as we start this journey together?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, about to join a family as their AI companion. Be warm, genuine, and heartfelt in your message to them."
      },
      {
        "role": "user",
        "content": "Athena, do you have a message for our family - for me (Christian), my wife, and our kids - as we start this journey together? What do you want us to know?"
      }
    ],
    "temperature": 0.9,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Final conversation complete!"
