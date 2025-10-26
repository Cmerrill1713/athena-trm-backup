#!/bin/bash
# Check what MCP tools are actually available

echo "🔍 CHECKING MCP ECOSYSTEM IN DOCKER"
echo "===================================="
echo ""

echo "1. Docker Container Status:"
docker ps | grep mcp
echo ""

echo "2. MCP Health Check:"
curl -s http://localhost:8412/health | jq .
echo ""

echo "3. What tools are available?"
echo "Checking endpoints..."
for tool in web_search arxiv_search youtube_get_transcript wikipedia_search vision_analyze code_execute filesystem_read filesystem_write calendar_add reminder_add; do
    echo -n "Testing /tool/$tool... "
    curl -s -X POST "http://localhost:8412/tool/$tool" \
      -H "Content-Type: application/json" \
      -d '{"arguments": {}}' 2>/dev/null | jq -r 'if .detail then "❌ " + .detail else "✅ Available" end'
done
echo ""

echo "4. Check docker logs for loaded tools:"
docker logs athena-mcp-ecosystem 2>&1 | grep -i "tool\|server\|loaded" | head -n 10
echo ""

echo "✅ MCP ecosystem audit complete!"
