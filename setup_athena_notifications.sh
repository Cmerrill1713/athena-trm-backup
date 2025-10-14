#!/bin/bash
# Athena Notification System Setup
# Configure real-time notifications for AI Republic operations

set -e

echo "🔔 Setting up Athena Notification System..."
echo "=========================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Configuration
INSTALL_DIR="/opt/ai-republic"
CONFIG_FILE="$INSTALL_DIR/notification_config.json"

echo "📁 Step 1: Installing Python dependencies..."
pip3 install --user requests || $SUDO pip3 install requests

echo "📋 Step 2: Installing notification script..."
$SUDO cp athena_notifications.py $INSTALL_DIR/
$SUDO chmod +x $INSTALL_DIR/athena_notifications.py

echo "🔧 Step 3: Setting up notification configuration..."
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default notification configuration..."
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
    $SUDO chown ai-republic:ai-republic $CONFIG_FILE 2>/dev/null || true
fi

echo "🧪 Step 4: Testing desktop notifications..."
python3 athena_notifications.py --test desktop

echo ""
echo "✅ Athena Notification System Setup Complete!"
echo "=============================================="
echo ""
echo "📡 Next Steps:"
echo ""
echo "1. Configure notification channels:"
echo "   python3 athena_notifications.py --configure"
echo ""
echo "2. Test your configured channels:"
echo "   python3 athena_notifications.py --test email"
echo "   python3 athena_notifications.py --test telegram"
echo "   python3 athena_notifications.py --test slack"
echo ""
echo "3. View current configuration:"
echo "   python3 athena_notifications.py --channels"
echo ""
echo "4. Send test notifications:"
echo "   python3 athena_notifications.py --send-warning \"Test warning message\""
echo "   python3 athena_notifications.py --send-alert \"Test urgent alert\""
echo ""
echo "📧 Daily briefings will now be sent via configured channels!"
echo ""
echo "🔧 Configuration File: $CONFIG_FILE"
echo "📁 Log Files: /var/log/ai-republic/athena_notifications.log"
echo ""
echo "💡 Pro Tip: Start with desktop notifications, then add email/telegram for remote access"
