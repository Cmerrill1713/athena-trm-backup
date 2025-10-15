#!/bin/bash
# Demo: Location-Based Alerting - Home, Work, Travel Context
# Shows how AI Republic adapts alerts based on your physical location

echo "🛰️ AI Republic Location-Based Alerting Demo"
echo "==========================================="
echo ""

# Test 1: At Home (permissive)
echo "🧪 Test 1: At Home (Permissive - all alerts welcome)"
LOCATION_OVERRIDE="home" LOCATION_ENABLED="true" python3 -c "
import os
os.environ['LOCATION_OVERRIDE'] = 'home'
os.environ['LOCATION_ENABLED'] = 'true'
from athena_notifications import should_send_alert_smart, update_smart_alerting, get_current_location
import json

print('🏠 At Home Context')
print('=================')
context = update_smart_alerting()
print(f'Location: {get_current_location()}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
echo ""

# Test 2: At Work (restrictive)
echo "🧪 Test 2: At Work (Restrictive - focus on important alerts)"
LOCATION_OVERRIDE="work" python3 -c "
import os
os.environ['LOCATION_OVERRIDE'] = 'work'
from athena_notifications import should_send_alert_smart, update_smart_alerting, get_current_location

print('🏢 At Work Context')
print('==================')
context = update_smart_alerting()
print(f'Location: {get_current_location()}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
echo ""

# Test 3: Traveling (minimal)
echo "🧪 Test 3: Traveling (Minimal - only essentials)"
LOCATION_OVERRIDE="travel" python3 -c "
import os
os.environ['LOCATION_OVERRIDE'] = 'travel'
from athena_notifications import should_send_alert_smart, update_smart_alerting, get_current_location

print('✈️ Traveling Context')
print('===================')
context = update_smart_alerting()
print(f'Location: {get_current_location()}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
echo ""

# Test 4: WiFi-based detection (if configured)
echo "🧪 Test 4: WiFi Network Detection"
echo "Current WiFi network:"
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep "SSID:" | head -1
echo ""
echo "To test WiFi detection:"
echo "1. Configure networks: ./smart_alerting_config.sh (option 8)"
echo "2. Connect to your home/work WiFi"
echo "3. Run: python3 -c \"from athena_notifications import get_current_location; print('Detected location:', get_current_location())\""
echo ""

# Test 5: Location status file override
echo "🧪 Test 5: Travel Status File Override"
echo "travel,remote" > ~/.ai_republic_location_status
unset LOCATION_OVERRIDE
python3 -c "
import os
# Clear override to test file-based detection
if 'LOCATION_OVERRIDE' in os.environ:
    del os.environ['LOCATION_OVERRIDE']
from athena_notifications import should_send_alert_smart, update_smart_alerting, get_current_location

print('📍 Travel Status File Context')
print('============================')
context = update_smart_alerting()
print(f'Location: {get_current_location()}')
print(f'Info alert: {should_send_alert_smart(\"info\")}')
print(f'Warning alert: {should_send_alert_smart(\"warning\")}')
print(f'Critical alert: {should_send_alert_smart(\"urgent\")}')
"
rm -f ~/.ai_republic_location_status
unset LOCATION_ENABLED
echo ""

echo "🎯 Location-Based Alerting Demo Complete!"
echo ""
echo "Location Behavior Matrix:"
echo "Location  | Info | Warning | Critical | Rationale"
echo "----------|------|---------|---------|----------"
echo "Home      | ✅    | ✅+🎤    | ✅+ESC   | Relaxed environment"
echo "Work      | ❌    | ✅+🎤    | ✅+ESC   | Professional focus"
echo "Travel    | ❌    | ✅       | ✅+ESC   | Limited connectivity"
echo ""
echo "Configuration:"
echo "• WiFi networks: ./smart_alerting_config.sh (option 8)"
echo "• Travel status: echo 'travel' > ~/.ai_republic_location_status"
echo "• Override: LOCATION_OVERRIDE=home python3 script.py"
echo ""
echo "Real-world scenarios:"
echo "🏠 Home: Routine maintenance alerts OK, full notifications"
echo "🏢 Work: Suppress distracting info, allow important warnings"
echo "✈️ Travel: Minimal alerts, focus on critical issues only"
