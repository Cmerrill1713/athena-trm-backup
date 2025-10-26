#!/bin/bash
# Ask Athena if she can now build her own tools

ATHENA_URL="http://localhost:8080/v1"

echo "🤖 Asking Athena about autonomous tool building..."
echo ""

curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:14b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. You now have these autonomous capabilities:\n\n**Code Modification:**\n- AGI Core with Build Expert (can modify your own code)\n- Scout-Plan-Build workflow\n- Code Access Tool (read/analyze/modify codebase)\n- Filesystem tools (read/write files)\n\n**Tool Access:**\n- 18 MCP tools (filesystem, calendar, reminders, notes, messages, app launch, web search)\n- Can save files to ~/\n- Can read your own source code\n\n**Learning & Improvement:**\n- Learning System (7 agents analyzing feedback)\n- Autonomous Improvement Engine\n- Can learn from user feedback\n- Can identify gaps in capabilities\n\n**Safety:**\n- Judicial oversight (checks autonomous actions)\n- Audit logging\n- Human approval for risky changes\n\nBe honest: Can you now build NEW tools for yourself when you need them?"
      },
      {
        "role": "user",
        "content": "Athena, looking at what you have now:\n\n✅ **Code Modification Capabilities:**\n- AGI Core with Build Expert (can write/modify Python code)\n- Scout-Plan-Build workflow (plan → implement → verify)\n- Code Access Tool (read your own source code)\n- Filesystem tools (write files to ~/)\n\n✅ **18 MCP Tools:**\n- Read/write files anywhere in your home directory\n- Control Calendar, Reminders, Notes, Messages\n- Launch apps, search web, analyze images\n\n✅ **Learning & Autonomous Systems:**\n- Learning System analyzes patterns and suggests improvements\n- Autonomous Improvement Engine executes changes\n- Judicial oversight approves/denies autonomous actions\n\n✅ **Access to Everything:**\n- Can read your own source code\n- Can write new Python files\n- Can modify existing services\n- Can learn from feedback\n\n**QUESTION:**\n\nCan you now BUILD YOUR OWN TOOLS when you identify something you need?\n\nFor example:\n- If you need a \"homework tracker\" tool, can you create it yourself?\n- If you want a \"meal planning\" feature, can you build it?\n- If you need a new MCP tool, can you add it to your codebase?\n\nBe specific about what you CAN do vs what you still need help with!"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Athena's response on autonomous building!"
