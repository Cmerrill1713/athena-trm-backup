#!/bin/bash

# ATHENA ALERT SYSTEM DEMO
# Demonstrates multi-channel alert notifications

echo "🚨 ATHENA ALERT SYSTEM DEMO"
echo "==========================="
echo ""

# Check if alert system is available
if [ ! -f "/opt/ai-republic/athena_alert_system.py" ]; then
    echo "❌ Athena alert system not found. Please install Athena first:"
    echo "   sudo ./install_athena_copilot.sh"
    exit 1
fi

echo "✅ Athena alert system detected"
echo ""

# Demo 1: Alert Statistics
echo "📊 DEMO 1: Alert System Status"
echo "------------------------------"
python3 /opt/ai-republic/athena_alert_system.py stats
echo ""

# Demo 2: Test Alert Channels
echo "🧪 DEMO 2: Testing Alert Channels"
echo "----------------------------------"
echo "Testing all enabled alert channels with a test alert..."
echo ""
python3 /opt/ai-republic/athena_alert_system.py test
echo ""

# Demo 3: Manual Alert Examples
echo "📢 DEMO 3: Manual Alert Examples"
echo "---------------------------------"
echo "Sending sample alerts of different severities..."
echo ""

# Info alert
echo "Sending INFO alert..."
python3 /opt/ai-republic/athena_alert_system.py send --type maintenance_success --message "Weekly maintenance completed successfully" --severity info
echo ""

# Warning alert
echo "Sending WARNING alert..."
python3 /opt/ai-republic/athena_alert_system.py send --type backup_failure --message "Memory backup creation failed during maintenance" --severity warning
echo ""

# Critical alert
echo "Sending CRITICAL alert..."
python3 /opt/ai-republic/athena_alert_system.py send --type maintenance_failure --message "Automated memory maintenance cycle failed" --severity critical
echo ""

# Demo 4: Alert Configuration
echo "⚙️ DEMO 4: Alert Configuration"
echo "------------------------------"
echo "Alert system configuration (/etc/ai-republic/athena_alerts.json):"
echo ""

if [ -f "/etc/ai-republic/athena_alerts.json" ]; then
    echo "Enabled channels:"
    python3 -c "
import json
with open('/etc/ai-republic/athena_alerts.json', 'r') as f:
    config = json.load(f)
    for channel, settings in config['channels'].items():
        if settings.get('enabled', False):
            print(f'  ✅ {channel}')
        else:
            print(f'  ❌ {channel} (disabled)')
"
    echo ""
    echo "Alert throttling settings:"
    python3 -c "
import json
with open('/etc/ai-republic/athena_alerts.json', 'r') as f:
    config = json.load(f)
    throttle = config['throttling']
    print(f'  Max alerts per hour: {throttle[\"max_alerts_per_hour\"]}')
    print(f'  Cooldown between duplicates: {throttle[\"cooldown_minutes\"]} minutes')
    print(f'  Duplicate suppression: {throttle[\"duplicate_suppression\"]}')
"
else
    echo "❌ Alert configuration file not found"
fi

echo ""

# Demo 5: Alert History
echo "📜 DEMO 5: Alert History"
echo "------------------------"
echo "Recent alert history:"
echo ""

if [ -f "/var/lib/ai-republic/athena_memory/alert_history.jsonl" ]; then
    echo "Last 3 alerts:"
    tail -3 /var/lib/ai-republic/athena_memory/alert_history.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        alert = json.loads(line.strip())
        print(f'  {alert[\"severity\"].upper()}: {alert[\"alert_type\"]} - {alert[\"message\"][:50]}...')
    except:
        pass
"
else
    echo "  No alert history yet (alerts will appear here after being sent)"
fi

echo ""

# Demo 6: Integration with Maintenance
echo "🔧 DEMO 6: Maintenance Integration"
echo "-----------------------------------"
echo "The alert system automatically integrates with:"
echo ""
echo "• Memory maintenance (success/failure alerts)"
echo "• Backup operations (creation/failure alerts)"
echo "• System health monitoring"
echo "• Conversation processing errors"
echo ""
echo "Example maintenance alerts:"
echo "  INFO: maintenance_success - Weekly maintenance completed"
echo "  WARNING: backup_failure - Memory backup creation failed"
echo "  CRITICAL: maintenance_failure - Automated maintenance cycle failed"
echo ""

# Demo 7: Alert Channel Configuration
echo "🔧 DEMO 7: Configuring Alert Channels"
echo "--------------------------------------"
echo "To configure email alerts, edit /etc/ai-republic/athena_alerts.json:"
echo ""
echo "Enable email alerts:"
echo "  \"email\": {"
echo "    \"enabled\": true,"
echo "    \"smtp_server\": \"smtp.gmail.com\","
echo "    \"smtp_port\": 587,"
echo "    \"sender_email\": \"athena@yourdomain.com\","
echo "    \"recipient_emails\": [\"admin@yourdomain.com\"],"
echo "    \"username\": \"your-email@gmail.com\","
echo "    \"password\": \"your-app-password\""
echo "  }"
echo ""
echo "Enable voice alerts (requires voice integration):"
echo "  \"voice\": {"
echo "    \"enabled\": true,"
echo "    \"speak_alerts\": true"
echo "  }"
echo ""

echo "🎯 ALERT SYSTEM SUMMARY:"
echo "• Multi-channel notifications (terminal, email, voice, log)"
echo "• Severity-based routing (critical, warning, info)"
echo "• Smart throttling and duplicate suppression"
echo "• Automatic escalation for repeated critical alerts"
echo "• Full audit trail and history tracking"
echo "• Integrated with maintenance and monitoring systems"
echo ""

echo "🚀 ACTIVATION:"
echo "1. Configure alert channels in /etc/ai-republic/athena_alerts.json"
echo "2. Test alerts: athena-alerts test"
echo "3. Enable automated maintenance alerts (enabled by default)"
echo "4. Monitor: athena-alerts stats"
echo ""

echo "🔔 Athena Alert System Demo Complete!"
echo "Your AI Republic now notifies you automatically when issues arise! 🚨✨"
