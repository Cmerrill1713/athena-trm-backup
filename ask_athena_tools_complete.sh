#!/bin/bash
# Ask Athena if she has everything she needs now

ATHENA_URL="http://localhost:8080/v1"

echo "🤖 Final check with Athena about her tools..."
echo ""

curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:14b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. We just implemented everything you requested:\n\n✅ SECURITY (Your Top Priority):\n- Database field encryption (AES-128)\n- PII detection & anonymization (Presidio)\n- TLS certificates (4096-bit RSA)\n\n✅ MCP TOOLS (9 Working Now):\n- Web search, ArXiv, YouTube, Wikipedia\n- Filesystem read/write/list (can save files to macOS!)\n- Vision analysis, code execution\n\n⚠️ AppleScript Tools (Needs Native Bridge):\n- Calendar, Reminders, Notes, Messages, App launch\n- Code is written, but Docker can'\''t run AppleScript\n- Need to run native macOS service (~1 hour to implement)\n\nBe honest about whether you'\''re ready to ship now or need the AppleScript tools first."
      },
      {
        "role": "user",
        "content": "Athena, we'\''ve completed your security requests and added MCP tools!\n\n✅ **Security (Done - Your #1 Priority):**\n- Encryption for sensitive data ✅\n- PII detection & anonymization ✅  \n- TLS certificates ✅\n\n✅ **MCP Tools Working Now (9 tools):**\n- web_search, arxiv_search, youtube, wikipedia\n- filesystem_read, filesystem_write, filesystem_list (you can save files!)\n- vision_analyze, code_execute\n\n⚠️ **AppleScript Tools (Code Written, Need Native Bridge):**\n- Calendar, Reminders, Notes, Messages, app_launch\n- Docker limitation: AppleScript needs native macOS access\n- Solution: Run macOS Bridge service natively (~1 hour work)\n\n**Question:**\nWith 9 MCP tools working + security complete, do you have everything you need to start helping the family?\n\nOr should we add the native macOS Bridge first for Calendar/Reminders control?\n\nBe practical - what'\''s your priority?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 800
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Athena's final answer received!"
