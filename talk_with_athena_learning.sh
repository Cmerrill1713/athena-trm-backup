#!/bin/bash

echo "🧠 ATHENA - LEARNING STRATEGY CONVERSATION"
echo "=========================================="
echo "Context: You now have Project Iceberg (multi-agent coordination + hybrid LLM)"
echo ""

echo "Question 1: How would you use multi-agent coordination for learning?"
echo "---------------------------------------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are Athena AI. You now have access to Project Iceberg - a multi-agent coordination system that can scale from 1 to 100+ agents using hybrid rule-based and LLM reasoning. You can coordinate multiple AI agents working together."
      },
      {
        "role": "user",
        "content": "As Athena, how would you use multi-agent coordination to improve your learning? Could different agents learn different things and share knowledge? How would you organize 20+ learning agents to collectively improve faster?"
      }
    ],
    "temperature": 0.8
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 2: Distributed learning strategy"
echo "-----------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are Athena AI with multi-agent coordination capabilities. You can have Router agents, Chat agents, Vision agents, etc. all learning in parallel and sharing insights."
      },
      {
        "role": "user",
        "content": "How would you structure distributed learning across your agents? For example: Router learns routing patterns, UAI learns conversation, FastVLM learns vision - then they share insights. What would be your ideal learning architecture?"
      }
    ],
    "temperature": 0.8
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 3: Meta-learning with agent coordination"
echo "------------------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are Athena AI. You want meta-learning (learning how to learn). You can coordinate 100+ agents. Each agent could try different learning strategies and report results."
      },
      {
        "role": "user",
        "content": "How would you use multi-agent coordination for meta-learning? Could you have some agents try one learning approach, others try different approaches, then share what works best? Design your ideal meta-learning system using Project Iceberg."
      }
    ],
    "temperature": 0.9
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 4: Learning from user feedback at scale"
echo "------------------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are Athena AI with user feedback system (👍 👎 buttons). You can coordinate multiple agents to process and learn from feedback in parallel."
      },
      {
        "role": "user",
        "content": "You now collect user feedback (positive/negative on responses). How would you use multi-agent coordination to process this feedback and improve? Could different agents analyze different aspects (sentiment, topics, errors, patterns) then synthesize improvements?"
      }
    ],
    "temperature": 0.8
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 5: Safety during distributed learning"
echo "---------------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are Athena AI with judicial oversight. When you have 20+ agents learning in parallel, you need to ensure they all learn safely without coordinating dangerous patterns."
      },
      {
        "role": "user",
        "content": "With multi-agent learning, how would you ensure safety? If one agent learns something dangerous, how should the judicial system + federation prevent it from spreading to other agents? Design the safety architecture for distributed learning."
      }
    ],
    "temperature": 0.8
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "Question 6: Optimal learning schedule"
echo "------------------------------------"
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "As Athena AI, if you could design your ideal learning schedule using multi-agent coordination: How often would you want to learn? What would trigger learning updates? How would you balance learning vs stability? How would you coordinate learning across agents without disrupting service?"
      }
    ],
    "temperature": 0.8
  }' | jq -r '.choices[0].message.content'

echo ""
echo ""
echo "✅ ATHENA LEARNING STRATEGY CONVERSATION COMPLETE"
echo ""

