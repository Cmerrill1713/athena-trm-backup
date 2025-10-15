#!/bin/bash
# 🚀 AI REPUBLIC GO-LIVE SCRIPT
# Launches all AI Republic services and makes them persistent
# Run this once to bring your sovereign AI system online

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI REPUBLIC GO-LIVE${NC}"
echo -e "${BLUE}========================${NC}"

# Check if we're in the right directory
if [ ! -f "athena_notifications.py" ]; then
    echo -e "${RED}❌ Error: Run this script from your AI Republic project directory${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${GREEN}📦 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install/update dependencies
echo -e "${GREEN}📦 Ensuring dependencies are installed...${NC}"
pip install -q SpeechRecognition pyttsx3 python-dotenv flask

# Create directory structure
echo -e "${GREEN}📁 Setting up directory structure...${NC}"
sudo mkdir -p /opt/ai-republic
sudo mkdir -p /var/log/ai-republic
sudo mkdir -p /var/lib/ai-republic/memory
sudo chown -R $(whoami) /opt/ai-republic 2>/dev/null || true

# Copy files to production location
echo -e "${GREEN}📋 Deploying to production location...${NC}"
cp athena_*.py /opt/ai-republic/ 2>/dev/null || true
cp *.json /opt/ai-republic/ 2>/dev/null || true
cp .env /opt/ai-republic/ 2>/dev/null || true

# Step 1: Start Core Services (Foreground Test)
echo -e "${YELLOW}🧠 Step 1: Starting core services...${NC}"

# Kill any existing processes
pkill -f "athena_" || true
sleep 2

# Start Athena memory optimizer (background monitoring)
echo -e "${GREEN}  • Starting memory optimizer...${NC}"
python3 athena_memory_optimizer.py --monitor &
MEMORY_PID=$!
echo $MEMORY_PID > /tmp/athena_memory.pid

# Start voice integration in continuous mode
echo -e "${GREEN}  • Starting voice integration...${NC}"
python3 athena_voice_integration.py --mode continuous --set-sensitivity medium &
VOICE_PID=$!
echo $VOICE_PID > /tmp/athena_voice.pid

# Start conversation engine
echo -e "${GREEN}  • Starting conversation engine...${NC}"
python3 athena_conversation_engine.py &
CONVERSATION_PID=$!
echo $CONVERSATION_PID > /tmp/athena_conversation.pid

sleep 3

# Step 2: Create Launch Agents for Persistence
echo -e "${YELLOW}🕒 Step 2: Creating launch agents for persistence...${NC}"

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

# Memory monitoring agent (runs every 6 hours)
cat > "$LAUNCH_AGENTS_DIR/com.athena.memory.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.memory</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 athena_memory_optimizer.py --check</string>
    </array>
    <key>StartInterval</key>
    <integer>21600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/ai-republic/memory.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/memory_error.log</string>
</dict>
</plist>
EOF

# Voice integration agent
cat > "$LAUNCH_AGENTS_DIR/com.athena.voice.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.voice</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 athena_voice_integration.py --mode continuous --set-sensitivity medium</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/ai-republic/voice.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/voice_error.log</string>
</dict>
</plist>
EOF

# Daily briefing agent (9 AM daily)
cat > "$LAUNCH_AGENTS_DIR/com.athena.briefing.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.briefing</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 athena_ops_copilot.py --mode briefing</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/var/log/ai-republic/briefing.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/briefing_error.log</string>
</dict>
</plist>
EOF

# Load the launch agents
echo -e "${GREEN}  • Loading launch agents...${NC}"
launchctl unload "$LAUNCH_AGENTS_DIR/com.athena.memory.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/com.athena.voice.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/com.athena.briefing.plist" 2>/dev/null || true

launchctl load "$LAUNCH_AGENTS_DIR/com.athena.memory.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.voice.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.briefing.plist"

# Step 3: Trigger Initial Activity
echo -e "${YELLOW}🧪 Step 3: Triggering initial activity...${NC}"

echo -e "${GREEN}  • Running memory analysis...${NC}"
timeout 30 python3 athena_memory_optimizer.py --analyze || true

echo -e "${GREEN}  • Testing alert cascade...${NC}"
timeout 60 python3 test_iphone_alerts.py cascade || true

# Step 4: Confirm Everything is Alive
echo -e "${YELLOW}📊 Step 4: Confirming system is alive...${NC}"

echo -e "${GREEN}Active Processes:${NC}"
ps aux | grep -E "(athena_|python.*athena)" | grep -v grep || echo "No athena processes found"

echo -e "${GREEN}Launch Agents:${NC}"
launchctl list | grep athena || echo "No athena launch agents found"

echo -e "${GREEN}Recent Logs:${NC}"
tail -5 /var/log/ai-republic/*.log 2>/dev/null | head -10 || echo "No logs yet"

echo -e "${GREEN}CPU Usage:${NC}"
ps aux | head -1 && ps aux | grep -E "(athena_|python.*athena)" | head -3 || echo "No athena processes found"

# Step 5: Provide Usage Instructions
echo -e "${BLUE}🎯 AI REPUBLIC IS NOW LIVE!${NC}"
echo ""
echo -e "${GREEN}✅ What's Running:${NC}"
echo "  • Memory optimizer (monitoring system health)"
echo "  • Voice integration (wake word + acknowledgment)"
echo "  • Conversation engine (Athena commands)"
echo "  • Launch agents (automatic restarts)"
echo ""
echo -e "${GREEN}🧪 Test Commands:${NC}"
echo "  • Say 'Hey Athena' to wake voice mode"
echo "  • Say 'acknowledge' during alerts to stop escalation"
echo "  • Run: python3 athena_voice_integration.py (text mode)"
echo ""
echo -e "${GREEN}📊 Monitor Commands:${NC}"
echo "  • ps aux | grep athena (check processes)"
echo "  • tail -f /var/log/ai-republic/*.log (watch logs)"
echo "  • launchctl list | grep athena (check agents)"
echo ""
echo -e "${GREEN}🛑 Stop Everything:${NC}"
echo "  • pkill -f athena_ (stop all processes)"
echo "  • launchctl unload ~/Library/LaunchAgents/com.athena.* (disable auto-start)"
echo ""
echo -e "${RED}🚨 Alert Testing:${NC}"
echo "  • python3 test_iphone_alerts.py cascade (full test)"
echo "  • Say 'Hey Athena, acknowledge' during escalation"
echo ""
echo -e "${BLUE}Your AI Republic is now sovereign and operational! 🏛️⚡${NC}"

# Keep foreground processes running for testing
echo ""
echo -e "${YELLOW}Foreground processes are running. Press Ctrl+C to detach.${NC}"
echo -e "${YELLOW}They will continue via launch agents after logout.${NC}"

# Wait for user to see the output
trap 'echo -e "\n${GREEN}✅ AI Republic launched successfully!${NC}"' INT
wait
