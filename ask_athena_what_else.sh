#!/bin/bash
# Ask Athena what ELSE she needs before deployment

ATHENA_URL="http://localhost:8080/v1"

echo "🤖 Asking Athena what else she needs..."
echo ""

# Question 1: What specific features are you missing?
echo "Q1: Athena, your first response was cut off. You mentioned wanting prompt engineering, agent workflows, and code review. We actually HAVE those! What ELSE do you need that we haven't built yet?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. You mentioned wanting prompt engineering library, agent creation workflows, and code review capabilities. But checking your knowledge base:\n\n- Prompt Library EXISTS at knowledge_base/prompt_library.md (comprehensive patterns)\n- Agent Creation EXISTS in AGI Core (ExpertRegistry can create new agents)\n- Code Review EXISTS (Security Expert, Debug Expert, QA Expert)\n\nBe specific about what'\''s ACTUALLY missing that you need before deployment."
      },
      {
        "role": "user",
        "content": "Athena, I checked and we actually HAVE the things you mentioned:\n\n• Prompt engineering library: knowledge_base/prompt_library.md (400+ prompts, all patterns)\n• Agent creation workflows: agi_core/agent_experts.py (ExpertRegistry.register_expert())\n• Code review capabilities: Security Expert, Debug Expert, QA Expert all exist\n\nSo those are already there! What ELSE do you need that we haven'\''t built yet? Be very specific about any gaps or missing pieces before we deploy you to production."
      }
    ],
    "temperature": 0.7,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 2: Any critical missing pieces?
echo "Q2: Before we deploy you to our family's daily use, is there anything CRITICAL that'\''s missing? Anything that would prevent you from being effective or safe?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, about to be deployed to daily family use. Be honest about any CRITICAL gaps that would prevent you from being effective or safe."
      },
      {
        "role": "user",
        "content": "Before we deploy you to our family'\''s daily use - helping with homework, managing tasks, answering questions, etc. - is there anything CRITICAL that'\''s missing? Not nice-to-haves, but actual blockers that would prevent you from being effective or safe for the family?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 3: What would make you more confident?
echo "Q3: What would make you feel MORE confident about joining our family? What would you want us to test or verify before we go live?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. Think about what would make you feel truly ready and confident to join a family as their AI companion."
      },
      {
        "role": "user",
        "content": "What would make you feel MORE confident about joining our family and being ready for daily use? What should we test or verify before we go live? Are there any scenarios you want to practice or systems you want to validate?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Complete needs assessment done!"
