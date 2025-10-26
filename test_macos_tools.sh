#!/bin/bash
# Test all new macOS tools in MCP ecosystem

MCP_URL="http://localhost:8412"

echo "🧪 TESTING MCP MACOS TOOLS"
echo "=========================="
echo ""

echo "1️⃣ Testing Filesystem Tools..."
echo "---"

# Test filesystem_write
echo "Writing test file..."
curl -s -X POST "$MCP_URL/tool/filesystem_write" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "path": "~/athena_test.txt",
      "content": "Hello from Athena MCP! Test at '$(date)'"
    }
  }' | jq .

# Test filesystem_read
echo "Reading test file..."
curl -s -X POST "$MCP_URL/tool/filesystem_read" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "path": "~/athena_test.txt"
    }
  }' | jq .

# Test filesystem_list
echo "Listing home directory..."
curl -s -X POST "$MCP_URL/tool/filesystem_list" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "path": "~"
    }
  }' | jq '.entries | length'

echo ""
echo "2️⃣ Testing Calendar Tools..."
echo "---"

# Test calendar_add
echo "Adding calendar event..."
curl -s -X POST "$MCP_URL/tool/calendar_add" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "title": "Athena Test Event",
      "date": "tomorrow",
      "duration_hours": 1,
      "calendar": "Home"
    }
  }' | jq .

echo ""
echo "3️⃣ Testing Reminders Tools..."
echo "---"

# Test reminder_add
echo "Adding reminder..."
curl -s -X POST "$MCP_URL/tool/reminder_add" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "name": "Test Athena MCP tools",
      "list": "Reminders"
    }
  }' | jq .

# Test reminder_list
echo "Listing reminders..."
curl -s -X POST "$MCP_URL/tool/reminder_list" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "list": "Reminders"
    }
  }' | jq '.reminders | length'

echo ""
echo "4️⃣ Testing App Launch..."
echo "---"

# Test app_launch
echo "Launching Calculator app..."
curl -s -X POST "$MCP_URL/tool/app_launch" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "app_name": "Calculator"
    }
  }' | jq .

echo ""
echo "5️⃣ Testing Notes Tool..."
echo "---"

# Test notes_create
echo "Creating note..."
curl -s -X POST "$MCP_URL/tool/notes_create" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "title": "Athena MCP Test Note",
      "body": "This note was created by Athena'\''s MCP ecosystem tools!",
      "folder": "Notes"
    }
  }' | jq .

echo ""
echo "✅ MCP macOS tools test complete!"
echo ""
echo "Cleanup test file..."
rm ~/athena_test.txt 2>/dev/null
