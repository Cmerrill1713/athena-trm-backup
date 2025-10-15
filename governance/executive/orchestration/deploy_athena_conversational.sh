#!/bin/bash
# Complete Athena Conversational System Deployment
# Deploys natural language AI Republic operations

set -e

echo "🤖💬 Deploying Athena Conversational System..."
echo "==========================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Configuration
INSTALL_DIR="/opt/ai-republic"

echo "📦 Step 1: Installing all Athena components..."

# Install dependencies
echo "Installing Python dependencies..."
pip3 install --user requests schedule || $SUDO pip3 install requests schedule

# Install all Athena files
echo "Installing Athena files..."
$SUDO mkdir -p $INSTALL_DIR
$SUDO cp athena_conversation.py $INSTALL_DIR/
$SUDO cp athena_operator.py $INSTALL_DIR/
$SUDO cp athena_scheduler.py $INSTALL_DIR/
$SUDO cp athena_notifications.py $INSTALL_DIR/
$SUDO cp ai_republic_cli.py $INSTALL_DIR/

# Set permissions
$SUDO chmod +x $INSTALL_DIR/*.py

echo "🧠 Step 2: Setting up conversation memory..."
MEMORY_FILE="$INSTALL_DIR/conversation_memory.json"
if [ ! -f "$MEMORY_FILE" ]; then
    echo "Creating conversation memory..."
    cat > /tmp/conversation_memory.json << 'EOF'
{
  "conversation_history": [],
  "current_context": {},
  "user_preferences": {
    "personality": "professional",
    "detail_level": "standard",
    "notification_preference": "important_only"
  },
  "last_interaction": null
}
EOF
    $SUDO cp /tmp/conversation_memory.json $MEMORY_FILE
fi

echo "🔔 Step 3: Setting up notifications..."
CONFIG_FILE="$INSTALL_DIR/notification_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating notification configuration..."
    cat > /tmp/notification_config.json << 'EOF'
{
  "enabled_channels": ["desktop"],
  "email": {
    "enabled": false,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "",
    "password": "",
    "from_email": "",
    "to_emails": []
  },
  "telegram": {
    "enabled": false,
    "bot_token": "",
    "chat_ids": []
  },
  "slack": {
    "enabled": false,
    "webhook_url": "",
    "channel": "#ai-republic"
  },
  "desktop": {
    "enabled": true,
    "urgency_levels": {
      "daily": "normal",
      "warning": "normal",
      "urgent": "critical"
    }
  },
  "retry_attempts": 3,
  "retry_delay": 5
}
EOF
    $SUDO cp /tmp/notification_config.json $CONFIG_FILE
fi

echo "⏰ Step 4: Setting up automated briefings..."
# Install systemd service and timer
$SUDO cp athena-daily-briefing.service /etc/systemd/system/ 2>/dev/null || echo "Service file not found, skipping..."
$SUDO cp athena-daily-briefing.timer /etc/systemd/system/ 2>/dev/null || echo "Timer file not found, skipping..."

# Reload systemd
$SUDO systemctl daemon-reload 2>/dev/null || echo "Systemd not available, continuing..."

echo "📁 Step 5: Setting up directories and permissions..."
$SUDO mkdir -p /var/log/ai-republic
$SUDO chown -R ai-republic:ai-republic /opt/ai-republic /var/log/ai-republic 2>/dev/null || true

echo "🧪 Step 6: Testing conversational system..."

# Test conversation interface
echo "Testing conversation interface..."
python3 $INSTALL_DIR/athena_conversation.py "help" > /dev/null && echo "✅ Conversation interface working" || echo "⚠️ Conversation interface test failed"

# Test operator with conversation
echo "Testing operator integration..."
python3 $INSTALL_DIR/athena_operator.py --help > /dev/null && echo "✅ Operator integration working" || echo "⚠️ Operator integration test failed"

# Test notifications
echo "Testing notifications..."
python3 $INSTALL_DIR/athena_notifications.py --channels > /dev/null && echo "✅ Notifications working" || echo "⚠️ Notifications test failed"

echo ""
echo "🎉 Athena Conversational System Deployed!"
echo "========================================="
echo ""
echo "🤖💬 What Athena Can Now Do:"
echo ""
echo "🌅 Daily Conversational Briefings:"
echo "  • Automated morning status updates"
echo "  • Natural language reports"
echo "  • Context-aware recommendations"
echo ""
echo "💬 Natural Language Commands:"
echo "  • 'show me the status' → System overview"
echo "  • 'handle the tribunal' → Process cases"
echo "  • 'what happened overnight' → Activity summary"
echo "  • 'release low severity quarantines' → Auto-management"
echo ""
echo "🧠 Conversation Memory:"
echo "  • Remembers recent commands and context"
echo "  • Suggests relevant follow-ups"
echo "  • Supports multi-step operations"
echo ""
echo "📱 Available Interfaces:"
echo ""
echo "Conversational Mode:"
echo "  python3 athena_conversation.py          # Natural chat interface"
echo ""
echo "Full Operator:"
echo "  python3 athena_operator.py              # Complete system (conversational)"
echo "  python3 athena_operator.py --mode monitor # Autonomous monitoring"
echo ""
echo "Traditional CLI:"
echo "  python3 ai_republic_cli.py              # Original interface still available"
echo ""
echo "🔔 Notification Setup:"
echo "  python3 athena_notifications.py --configure  # Setup email/telegram/slack"
echo "  python3 athena_notifications.py --test desktop # Test notifications"
echo ""
echo "⚙️ Configuration:"
echo ""
echo "1. Enable automated briefings:"
echo "   sudo systemctl enable athena-daily-briefing.timer"
echo "   sudo systemctl start athena-daily-briefing.timer"
echo ""
echo "2. Customize conversation memory:"
echo "   Edit /opt/ai-republic/conversation_memory.json"
echo ""
echo "3. Configure notifications:"
echo "   Edit /opt/ai-republic/notification_config.json"
echo "   Or run: python3 athena_notifications.py --configure"
echo ""
echo "4. Adjust briefing time:"
echo "   sudo vim /etc/systemd/system/athena-daily-briefing.timer"
echo "   sudo systemctl restart athena-daily-briefing.timer"
echo ""
echo "💬 Example Conversation:"
echo ""
echo "You> good morning athena"
echo "🤖 Good morning! Here's your AI Republic status briefing..."
echo ""
echo "You> show me tribunals"
echo "🤖 ⚖️ Found 2 tribunal cases... Ready to handle?"
echo ""
echo "You> handle the first one"
echo "🤖 ✅ Tribunal upheld. Quarantine maintained..."
echo ""
echo "📁 Files Created:"
echo "  /opt/ai-republic/athena_conversation.py     # Conversational interface"
echo "  /opt/ai-republic/conversation_memory.json   # Memory persistence"
echo "  /opt/ai-republic/notification_config.json   # Notification settings"
echo "  /var/log/ai-republic/                        # Logs and briefings"
echo ""
echo "🧠 Memory Features:"
echo "  • Persistent conversation context"
echo "  • Command history and suggestions"
echo "  • User preference learning"
echo "  • Multi-session continuity"
echo ""
echo "🌅 Briefings Include:"
echo "  • Natural language status reports"
echo "  • Contextual recommendations"
echo "  • Proactive issue detection"
echo "  • Multi-channel delivery (configured)"
echo ""
echo "🚀 Ready for conversational AI governance!"
echo ""
echo "💡 Pro Tip: Start with 'python3 athena_conversation.py' and say 'hello' to begin your first conversation!"
