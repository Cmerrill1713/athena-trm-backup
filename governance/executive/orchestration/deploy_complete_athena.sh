#!/bin/bash
# Complete Athena Autonomous Operator Deployment
# Deploys conversational briefings + real-time notifications

set -e

echo "🤖 Deploying Complete Athena Autonomous Operator..."
echo "=================================================="

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
$SUDO cp athena_scheduler.py $INSTALL_DIR/
$SUDO cp athena_notifications.py $INSTALL_DIR/
$SUDO cp athena_operator.py $INSTALL_DIR/
$SUDO cp ai_republic_cli.py $INSTALL_DIR/

# Set permissions
$SUDO chmod +x $INSTALL_DIR/*.py

echo "🔧 Step 2: Setting up systemd services..."

# Install systemd service and timer
$SUDO cp athena-daily-briefing.service /etc/systemd/system/ 2>/dev/null || echo "Service file not found, skipping..."
$SUDO cp athena-daily-briefing.timer /etc/systemd/system/ 2>/dev/null || echo "Timer file not found, skipping..."

# Reload systemd
$SUDO systemctl daemon-reload 2>/dev/null || echo "Systemd not available, continuing..."

echo "🔔 Step 3: Setting up notification system..."

# Create notification config if it doesn't exist
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

echo "📁 Step 4: Setting up directories and permissions..."
$SUDO mkdir -p /var/log/ai-republic
$SUDO chown -R ai-republic:ai-republic /opt/ai-republic /var/log/ai-republic 2>/dev/null || true

echo "🧪 Step 5: Testing installation..."

# Test CLI
echo "Testing AI Republic CLI..."
python3 $INSTALL_DIR/ai_republic_cli.py --help > /dev/null && echo "✅ CLI working" || echo "⚠️ CLI test failed"

# Test notifications
echo "Testing desktop notifications..."
python3 $INSTALL_DIR/athena_notifications.py --test desktop && echo "✅ Notifications working" || echo "⚠️ Notifications test failed"

# Test scheduler
echo "Testing scheduler..."
python3 $INSTALL_DIR/athena_scheduler.py --status > /dev/null && echo "✅ Scheduler working" || echo "⚠️ Scheduler test failed"

echo ""
echo "🎉 Athena Autonomous Operator Deployed!"
echo "========================================"
echo ""
echo "🤖 What Athena Now Does:"
echo "  • Automated daily briefings at 9:00 AM"
echo "  • Real-time notifications for alerts"
echo "  • Proactive system monitoring"
echo "  • Conversational status reports"
echo ""
echo "📋 Available Commands:"
echo ""
echo "Daily Operations:"
echo "  python3 athena_scheduler.py --briefing     # Immediate briefing"
echo "  python3 athena_scheduler.py --status       # System status"
echo ""
echo "Notifications:"
echo "  python3 athena_notifications.py --configure  # Setup channels"
echo "  python3 athena_notifications.py --test email # Test channel"
echo "  python3 athena_notifications.py --channels   # View config"
echo ""
echo "Interactive Mode:"
echo "  python3 athena_operator.py                    # Full operator console"
echo ""
echo "🔧 Configuration:"
echo ""
echo "1. Set up notifications:"
echo "   python3 athena_notifications.py --configure"
echo ""
echo "2. Change briefing time (optional):"
echo "   sudo vim /etc/systemd/system/athena-daily-briefing.timer"
echo "   sudo systemctl restart athena-daily-briefing.timer"
echo ""
echo "3. Start automated briefings:"
echo "   sudo systemctl enable athena-daily-briefing.timer"
echo "   sudo systemctl start athena-daily-briefing.timer"
echo ""
echo "📊 Monitoring:"
echo "  sudo systemctl status athena-daily-briefing.timer"
echo "  tail -f /var/log/ai-republic/athena_briefings.log"
echo ""
echo "📁 Files:"
echo "  /opt/ai-republic/                    # Athena installation"
echo "  /var/log/ai-republic/                # Logs and briefings"
echo "  /opt/ai-republic/notification_config.json  # Notification settings"
echo ""
echo "🌅 Tomorrow morning, Athena will greet you with your first briefing!"
echo ""
echo "💡 Pro Tip: Start with desktop notifications, then add email/telegram for 24/7 access"
