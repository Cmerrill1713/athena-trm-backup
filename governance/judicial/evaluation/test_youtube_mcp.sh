#!/bin/bash
# Test YouTube Transcript MCP

echo "🧪 Testing YouTube Transcript MCP..."
echo ""

# Check if container is running
echo "1️⃣ Checking container status..."
if docker ps | grep -q youtube-transcript-mcp; then
    echo "✅ Container is running"
else
    echo "❌ Container is not running"
    echo "   Start with: docker compose -f AI-Projects/universal-ai-tools/docker-compose.youtube-mcp.yml up -d"
    exit 1
fi

echo ""
echo "2️⃣ Container info:"
docker ps --filter name=youtube-transcript-mcp --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "3️⃣ Recent logs:"
docker logs youtube-transcript-mcp --tail 5

echo ""
echo "✅ YouTube Transcript MCP is set up!"
echo "   Port: 8412"
echo "   Tools: get_transcript, get_timed_transcript, get_video_info"
echo ""
echo "📝 Usage example:"
echo "   # From Python/MCP client:"
echo "   mcp.call_tool('get_transcript', url='https://www.youtube.com/watch?v=VIDEO_ID')"
