#!/bin/bash
# Athena Daily Briefing Deployment Script
# Sets up automated daily conversational briefings

set -e

echo "🤖 Deploying Athena Daily Briefing System..."
echo "=========================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Configuration
INSTALL_DIR="/opt/ai-republic"
SERVICE_NAME="athena-daily-briefing"
USER_NAME="ai-republic"

echo "📁 Step 1: Setting up directories..."
$SUDO mkdir -p $INSTALL_DIR
$SUDO mkdir -p /var/log/ai-republic
$SUDO chown -R $USER_NAME:$USER_NAME $INSTALL_DIR /var/log/ai-republic 2>/dev/null || true

echo "📋 Step 2: Installing Python dependencies..."
pip3 install --user schedule || $SUDO pip3 install schedule

echo "🔧 Step 3: Installing service files..."

# Copy service files
$SUDO cp athena-daily-briefing.service /etc/systemd/system/
$SUDO cp athena-daily-briefing.timer /etc/systemd/system/

# Copy Python files
$SUDO cp athena_scheduler.py $INSTALL_DIR/
$SUDO cp ai_republic_cli.py $INSTALL_DIR/
$SUDO cp athena_operator.py $INSTALL_DIR/

# Set permissions
$SUDO chown root:root /etc/systemd/system/athena-daily-briefing.*
$SUDO chmod 644 /etc/systemd/system/athena-daily-briefing.*
$SUDO chown -R $USER_NAME:$USER_NAME $INSTALL_DIR/*.py

echo "🔄 Step 4: Reloading systemd..."
$SUDO systemctl daemon-reload

echo "⏰ Step 5: Enabling and starting timer..."
$SUDO systemctl enable athena-daily-briefing.timer
$SUDO systemctl start athena-daily-briefing.timer

echo "✅ Step 6: Verifying installation..."
$SUDO systemctl status athena-daily-briefing.timer --no-pager
$SUDO systemctl list-timers | grep athena

echo ""
echo "🎉 Athena Daily Briefing System Deployed!"
echo "=========================================="
echo ""
echo "📋 What happens now:"
echo "  • Daily briefings at 9:00 AM (configurable)"
echo "  • Conversational status reports"
echo "  • Proactive issue detection"
echo "  • Automatic service monitoring"
echo ""
echo "📊 Check status:"
echo "  sudo systemctl status athena-daily-briefing.timer"
echo ""
echo "🧪 Test immediately:"
echo "  python3 athena_scheduler.py --briefing"
echo ""
echo "⚙️ Configure briefing time:"
echo "  Edit /etc/systemd/system/athena-daily-briefing.timer"
echo "  Change 'OnCalendar=*-*-* 09:00:00' to desired time"
echo "  Then: sudo systemctl restart athena-daily-briefing.timer"
echo ""
echo "📁 Logs location:"
echo "  /var/log/ai-republic/athena_briefings.log"
echo "  /var/log/ai-republic/daily_briefing_YYYYMMDD.md"
echo ""
echo "🤖 Athena will now greet you every morning with your AI Republic status!"
