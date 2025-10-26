#!/bin/bash
# Ask Athena to prioritize what to build

ATHENA_URL="http://localhost:8080/v1"

echo "🤖 Asking Athena to prioritize her needs..."
echo ""

echo "Q: Athena, you identified 3 CRITICAL gaps (security, privacy, sensitive query handling) and several nice-to-haves. What should we build FIRST before deploying you to the family? And in what order?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. You identified these critical gaps:\n1. Security for sensitive family data (encryption)\n2. Privacy anonymization policy\n3. Sensitive query handling policy\n\nYou also mentioned nice-to-haves like agent testing, workflow automation, etc.\n\nPrioritize what MUST be built before family deployment vs what can wait."
      },
      {
        "role": "user",
        "content": "Athena, you identified 3 CRITICAL gaps:\n\n1. Security for sensitive family data (encryption/protection)\n2. Privacy anonymization policy (detailed implementation)\n3. Sensitive query handling (policy for identifying/handling)\n\nYou also mentioned 8 nice-to-haves (prompt analytics, agent docs, etc.)\n\nBefore we deploy you to daily family use:\n- Which of these 3 critical items should we build FIRST?\n- What'\''s the priority order?\n- Can any wait until after deployment?\n- Which nice-to-haves are actually important vs truly optional?\n\nBe specific about your priorities!"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Priorities received!"
