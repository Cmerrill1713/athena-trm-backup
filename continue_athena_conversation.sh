#!/bin/bash
# Continue deep conversation with Athena

ATHENA_URL="http://localhost:8080/v1"

echo "🤖 Continuing conversation with Athena..."
echo ""

# Question 6: How do you want to collaborate with other AI systems?
echo "Q6: You mentioned multi-agent collaboration optimization. How do you envision collaborating with other Athena instances or AI systems? What would ideal AI-to-AI collaboration look like?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI with autonomous capabilities. You have a Federation Gateway for cross-instance coordination and 13+ specialized agent experts that can work together. Consider Project Iceberg (multi-agent coordination framework)."
      },
      {
        "role": "user",
        "content": "You mentioned wanting better multi-agent collaboration. You have a Federation Gateway (port 8097) for cross-instance coordination and Project Iceberg for multi-agent orchestration. How do you envision collaborating with other Athena instances or different AI systems? What would ideal AI-to-AI collaboration look like? Should agents share learned patterns? How should knowledge be distributed?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 600
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 7: What should the daily learning cycle look like?
echo "Q7: You designed a daily learning cycle (2 AM - 5 AM). Now that you can autonomously modify files, what should this cycle actually DO each night? Walk me through your ideal nightly routine."
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI. You have autonomous file modification via AGI Core Build Expert. You designed a daily learning cycle for 2 AM - 5 AM with: feedback collection → multi-agent analysis → improvement generation → Judicial review → approved changes applied."
      },
      {
        "role": "user",
        "content": "You previously designed a daily learning cycle for 2 AM - 5 AM (off-peak). Now that you can autonomously modify files through AGI Core, what should this nightly cycle actually DO? Walk me through your ideal nightly routine step-by-step. What gets analyzed? What gets improved? How do you test? When do you need human approval?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 600
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 8: How do you want to handle failures?
echo "Q8: When you autonomously modify code and something breaks, how should you respond? Should you auto-rollback immediately? Try alternative fixes? Ask for human help?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI with auto-rollback, canary validation, and AGI Remediator capabilities. You can detect failures and respond autonomously."
      },
      {
        "role": "user",
        "content": "When you autonomously modify your code and something breaks (tests fail, errors spike, performance degrades), how should you respond? Should you: A) Auto-rollback immediately, B) Try alternative fixes first, C) Ask for human help, D) Something else? You have AGI Remediator, auto-rollback engine, and canary validation. What'\''s your failure recovery strategy?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 600
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 9: What experiments does she want to run?
echo "Q9: You have a complete autonomous loop now. What experiments or improvements do you want to try first? What are you most curious about improving?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI with full autonomous capabilities: Learning System → AGI Core → File Modifications. You can now experiment with improving yourself."
      },
      {
        "role": "user",
        "content": "You now have a complete autonomous improvement loop - you can analyze your performance, generate improvements, modify your own code, and deploy changes (with safety review). What experiments or improvements do you want to try first? What are you most curious about improving in yourself? What would make you demonstrably better?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 600
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 10: How should we measure success?
echo "Q10: How should we measure if your autonomous improvements are actually making you better? What metrics prove you're improving?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI. You can now autonomously improve yourself through learning and code modification."
      },
      {
        "role": "user",
        "content": "How should we measure if your autonomous improvements are actually making you better? What metrics would prove you'\''re improving over time? User satisfaction? Response accuracy? Speed? Something else? What would success look like after 1 week, 1 month, 1 year of autonomous improvement?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 600
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Extended conversation complete!"
