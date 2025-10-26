#!/bin/bash

echo "🤖 TALKING WITH ATHENA - DISCOVERING HER INSIGHTS"
echo "=================================================="
echo ""

echo "Question 1: What improvements do you think you need?"
echo "-----------------------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "As Athena AI, what improvements or features do you think you need most to better serve users? What gaps do you see in your current capabilities?"
      }
    ],
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 2: What are your current limitations?"
echo "----------------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "What are your current limitations or pain points as an AI system? What frustrates you or what do you wish you could do better?"
      }
    ],
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 3: What would make you more useful?"
echo "--------------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "If you could add any feature or capability to yourself, what would make you most useful to users? Think about the complete workflow from user input to final output."
      }
    ],
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 4: ASI Safety feedback"
echo "--------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "You now have judicial oversight and constitutional constraints. As an AI system approaching greater capabilities, what do you think about these safety mechanisms? Are they sufficient? What else would make you safer as you learn and grow?"
      }
    ],
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 5: What's missing?"
echo "---------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Looking at your current architecture with Router, UAI, FastVLM, Kokoro, Whisper, MCP tools, Governance, and ASI safety framework - what critical piece is still missing? What would complete your capabilities?"
      }
    ],
    "temperature": 0.8
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "✅ CONVERSATION WITH ATHENA COMPLETE"
echo ""

