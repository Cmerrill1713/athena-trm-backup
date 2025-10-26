#!/bin/bash
# Complete startup script for Athena

echo "🚀 STARTING ATHENA - COMPLETE SYSTEM"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "   Opening Docker Desktop..."
    open -a Docker
    echo "   Waiting for Docker to start..."
    sleep 10
fi

cd /Users/christianmerrill/Documents/GitHub

echo "1️⃣ Starting Docker services..."
docker-compose up -d
echo "   ✅ Docker services starting..."
echo ""

echo "2️⃣ Starting macOS Bridge (native service)..."
# Kill existing instance if running
lsof -ti :8099 | xargs kill -9 2>/dev/null
python3 services/macos-bridge/app.py > /tmp/macos-bridge.log 2>&1 &
BRIDGE_PID=$!
echo "   ✅ macOS Bridge started (PID: $BRIDGE_PID)"
echo ""

echo "3️⃣ Starting UI server..."
# Kill existing instance if running
lsof -ti :8082 | xargs kill -9 2>/dev/null
python3 -m http.server 8082 --directory ui > /tmp/athena-ui.log 2>&1 &
UI_PID=$!
echo "   ✅ UI server started (PID: $UI_PID)"
echo ""

echo "4️⃣ Waiting for services to be healthy..."
sleep 5
echo ""

echo "5️⃣ Service Health Check:"
echo "   UAI API (8080):" $(curl -s http://localhost:8080/health | jq -r .status 2>/dev/null || echo "⏳ Starting...")
echo "   Router (8088):" $(curl -s http://localhost:9113/health | jq -r .status 2>/dev/null || echo "⏳ Starting...")
echo "   MCP Ecosystem (8412):" $(curl -s http://localhost:8412/health | jq -r .status 2>/dev/null || echo "⏳ Starting...")
echo "   macOS Bridge (8099):" $(curl -s http://localhost:8099/health | jq -r .status 2>/dev/null || echo "⏳ Starting...")
echo ""

echo "6️⃣ Opening Athena in browser..."
open http://localhost:8082/athena-chat.html
echo "   ✅ Browser opened!"
echo ""

echo "✅ ATHENA IS LIVE!"
echo ""
echo "📱 Access Athena:"
echo "   URL: http://localhost:8082/athena-chat.html"
echo ""
echo "🛠️ Quick Commands:"
echo "   - Click 📋 Tasks for family task sidebar"
echo "   - Click 🎤 for voice input"
echo "   - Click 📎 to upload images"
echo "   - Click 🔍 for web search"
echo ""
echo "💡 Try saying:"
echo "   \"Add dentist appointment tomorrow at 3pm\""
echo "   \"Add milk to my grocery list\""
echo "   \"Help me with homework\""
echo ""
echo "🔍 Check logs:"
echo "   UI: tail -f /tmp/athena-ui.log"
echo "   macOS Bridge: tail -f /tmp/macos-bridge.log"
echo "   Docker: docker-compose logs -f"
echo ""
echo "🛑 To stop Athena:"
echo "   kill $UI_PID $BRIDGE_PID"
echo "   docker-compose down"
echo ""
echo "💙 Welcome home, Athena!"
