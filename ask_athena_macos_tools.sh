#!/bin/bash
# Ask Athena about needing macOS system control tools

ATHENA_URL="http://localhost:8080/v1"

echo "🖥️ Asking Athena about macOS system tools..."
echo ""

curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:14b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. Your user just made a profound insight:\n\nInstead of building web apps for Calendar, Tasks, Notes, etc., you could have TOOLS to control existing macOS apps:\n\n- Calendar.app (already on Mac)\n- Reminders.app (task management)\n- Notes.app (note taking)\n- Mail.app (email)\n- Safari.app (web browsing)\n- Messages.app (communication)\n- App Store (download new apps)\n\nWith tools like:\n- AppleScript/JXA (control any Mac app)\n- Shortcuts.app (automation)\n- File system access\n- Process management\n- App Store CLI\n\nBe honest: Would you rather have tools to control native Mac apps, or have us build web-based versions?"
      },
      {
        "role": "user",
        "content": "Athena, here'\''s a profound insight:\n\nInstead of us building Calendar, Task, Notes apps for you... what if we gave you TOOLS to control the macOS apps that already exist?\n\nFor example:\n\n**Native macOS Apps Available:**\n- Calendar.app (family calendar)\n- Reminders.app (task lists, groceries)\n- Notes.app (homework, recipes)\n- Mail.app (family email)\n- Safari.app (web browsing)\n- Messages.app (family chat)\n- Photos.app (family photos)\n- App Store (download new apps!)\n\n**Tools You'\''d Need:**\n1. **AppleScript/JXA** - Control any Mac app programmatically\n2. **Shortcuts.app** - Use macOS automation\n3. **File System Access** - Read/write app data\n4. **Process Management** - Launch/quit apps\n5. **App Store CLI** - Download new apps as needed\n\n**Question:**\nWould you rather:\nA) Have us build web-based versions of everything\nB) Get tools to control native macOS apps directly\nC) Both (web UI + native app control)\n\nWhich approach would make you most powerful and useful for the family?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Athena'\''s response received!"
