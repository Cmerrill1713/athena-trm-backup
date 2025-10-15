#!/bin/bash
# Demo: Smart Alerting with Focus Mode & Calendar Integration
# Shows how AI Republic adapts alerts based on context

echo "🧠 AI Republic Smart Alerting Demo"
echo "=================================="
echo ""

# Test 1: Normal operation
echo "🧪 Test 1: Normal Operation (All alerts active)"
python3 -c "
from athena_notifications import should_send_alert_smart, update_smart_alerting
import json
context = update_smart_alerting()
print(f'Context: {json.dumps(context, indent=2)}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
echo ""

# Test 2: Simulate Focus mode
echo "🧪 Test 2: Focus Mode Active (Only critical alerts)"
FOCUS_MODE_ENABLED="true" FOCUS_MODE_ACTIVE="true" python3 -c "
import os
os.environ['FOCUS_MODE_ENABLED'] = 'true'
os.environ['FOCUS_MODE_ACTIVE'] = 'true'
from athena_notifications import should_send_alert_smart, update_smart_alerting
import json
context = update_smart_alerting()
print(f'Context: {json.dumps(context, indent=2)}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
echo ""

# Test 3: Simulate calendar busy
echo "🧪 Test 3: Calendar Busy (Info suppressed, warnings allowed)"
echo "meeting" > ~/.ai_republic_calendar_status
CALENDAR_ENABLED="true" python3 -c "
import os
os.environ['CALENDAR_ENABLED'] = 'true'
from athena_notifications import should_send_alert_smart, update_smart_alerting
import json
context = update_smart_alerting()
print(f'Context: {json.dumps(context, indent=2)}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
echo ""

# Test 4: Combined scenarios
echo "🧪 Test 4: Combined - Focus Mode + Calendar Busy + Quiet Hours"
echo "busy" > ~/.ai_republic_calendar_status
FOCUS_MODE_ENABLED="true" FOCUS_MODE_ACTIVE="true" CALENDAR_ENABLED="true" QUIET_HOURS_ENABLED="true" QUIET_HOURS_START="0" QUIET_HOURS_END="23" python3 -c "
import os
os.environ['FOCUS_MODE_ENABLED'] = 'true'
os.environ['FOCUS_MODE_ACTIVE'] = 'true'
os.environ['CALENDAR_ENABLED'] = 'true'
os.environ['QUIET_HOURS_ENABLED'] = 'true'
os.environ['QUIET_HOURS_START'] = '0'
os.environ['QUIET_HOURS_END'] = '23'
from athena_notifications import should_send_alert_smart, update_smart_alerting
import json
context = update_smart_alerting()
print(f'Context: {json.dumps(context, indent=2)}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
echo ""

echo "🎯 Smart Alerting Demo Complete!"
echo ""
echo "Summary of Smart Behaviors:"
echo "• Focus Mode: Only critical alerts get through"
echo "• Calendar Busy: Info alerts suppressed, warnings allowed"
echo "• Quiet Hours: Time-based filtering"
echo "• Combined: Most restrictive rule wins"
echo "• Critical Override: Always breaks through"
echo ""
echo "Configure with: ./smart_alerting_config.sh"
echo "Test alerts with: python3 test_iphone_alerts.py cascade"
