#!/bin/bash
# Configure Quiet Hours for AI Republic alerts
# Prevents voice alerts and some notifications during specified hours

echo "🌙 AI Republic Quiet Hours Configuration"
echo "========================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Creating basic configuration..."
    cat > .env << 'EOF'
# Apple-native iPhone alerting (FREE - no external services required)
IPHONE_NUMBER="+1YOURIPHONE"
ATHENA_ALERT_PHONE="+1YOURIPHONE"

# Quiet Hours Configuration
QUIET_HOURS_ENABLED="true"
QUIET_HOURS_START="22"
QUIET_HOURS_END="8"
EOF
fi

echo ""
echo "Current Quiet Hours Settings:"
echo "=============================="

if grep -q "QUIET_HOURS_ENABLED" .env 2>/dev/null; then
    ENABLED=$(grep "QUIET_HOURS_ENABLED" .env | cut -d'=' -f2 | tr -d '"')
    START=$(grep "QUIET_HOURS_START" .env | cut -d'=' -f2 | tr -d '"')
    END=$(grep "QUIET_HOURS_END" .env | cut -d'=' -f2 | tr -d '"')

    if [ "$ENABLED" = "true" ]; then
        echo "✅ Quiet Hours: ENABLED"
        echo "🕐 Start Time: ${START}:00 ($(convert_hour $START))"
        echo "🕐 End Time: ${END}:00 ($(convert_hour $END))"
        echo ""
        echo "📋 During quiet hours:"
        echo "  • Info alerts: Suppressed"
        echo "  • Warning alerts: iMessage + notification only (no voice)"
        echo "  • Critical alerts: Full escalation (emergency override)"
    else
        echo "❌ Quiet Hours: DISABLED"
    fi
else
    echo "⚠️  Quiet Hours: Not configured"
fi

echo ""
echo "Options:"
echo "1. Enable quiet hours (10 PM - 8 AM)"
echo "2. Disable quiet hours"
echo "3. Custom time range"
echo "4. Test current settings"
echo "5. Exit"

read -p "Choose option (1-5): " choice

case $choice in
    1)
        echo "Enabling quiet hours: 10 PM - 8 AM..."
        sed -i.bak 's/QUIET_HOURS_ENABLED=.*/QUIET_HOURS_ENABLED="true"/' .env
        sed -i.bak 's/QUIET_HOURS_START=.*/QUIET_HOURS_START="22"/' .env
        sed -i.bak 's/QUIET_HOURS_END=.*/QUIET_HOURS_END="8"/' .env
        echo "✅ Quiet hours enabled!"
        ;;
    2)
        echo "Disabling quiet hours..."
        sed -i.bak 's/QUIET_HOURS_ENABLED=.*/QUIET_HOURS_ENABLED="false"/' .env
        echo "✅ Quiet hours disabled!"
        ;;
    3)
        read -p "Start hour (0-23): " start_hour
        read -p "End hour (0-23): " end_hour
        echo "Setting custom quiet hours: ${start_hour}:00 - ${end_hour}:00..."
        sed -i.bak 's/QUIET_HOURS_ENABLED=.*/QUIET_HOURS_ENABLED="true"/' .env
        sed -i.bak "s/QUIET_HOURS_START=.*/QUIET_HOURS_START=\"$start_hour\"/" .env
        sed -i.bak "s/QUIET_HOURS_END=.*/QUIET_HOURS_END=\"$end_hour\"/" .env
        echo "✅ Custom quiet hours set!"
        ;;
    4)
        echo "Testing current settings..."
        echo "Current time: $(date '+%H:%M')"
        python3 -c "
import os
from athena_notifications import is_quiet_hours, should_send_alert, should_send_voice_alert
print('Quiet hours active:', is_quiet_hours())
print('Info alert would send:', should_send_alert('info'))
print('Warning alert would send:', should_send_alert('warning'))
print('Critical alert would send:', should_send_alert('urgent'))
print('Warning voice would send:', should_send_voice_alert('warning'))
print('Critical voice would send:', should_send_voice_alert('urgent'))
        "
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        ;;
esac

echo ""
echo "Restart AI Republic services to apply changes:"
echo "pkill -f athena && ./quick_launch.sh"

function convert_hour() {
    hour=$1
    if [ $hour -eq 0 ]; then
        echo "12 AM"
    elif [ $hour -lt 12 ]; then
        echo "${hour} AM"
    elif [ $hour -eq 12 ]; then
        echo "12 PM"
    else
        echo "$((hour-12)) PM"
    fi
}
