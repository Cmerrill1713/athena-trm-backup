#!/bin/bash
# Demo: Context-Reactive Macros - Automatic Operational Mode Switching
# Shows how Athena automatically adapts behavior based on context triggers

echo "🎯 AI Republic Context-Reactive Macros Demo"
echo "=========================================="
echo ""

# Test 1: List available macros
echo "🧪 Test 1: Available Macros"
echo "Testing macro template listing..."
echo ""

python3 -c "
from athena_notifications import list_available_macros
list_available_macros()
"

echo ""

# Test 2: Manual macro execution
echo "🧪 Test 2: Manual Macro Execution"
echo "Testing manual execution of macros..."
echo ""

python3 -c "
from athena_notifications import execute_macro, list_active_macros

print('Testing manual macro execution:')
print('===============================')

macros_to_test = ['meeting_mode', 'travel_mode', 'focus_mode']

for macro in macros_to_test:
    print(f'\\n🎯 Executing macro: {macro}')
    result = execute_macro(macro, 'manual_test')
    print(f'Result: {\"✅ Success\" if result else \"❌ Failed\"}')

print('\\n📋 Active Macros After Execution:')
list_active_macros()
"

echo ""

# Test 3: Macro deactivation
echo "🧪 Test 3: Macro Deactivation"
echo "Testing deactivation of active macros..."
echo ""

python3 -c "
from athena_notifications import deactivate_macro, list_active_macros

print('Testing macro deactivation:')
print('===========================')

# Try to deactivate some macros
macros_to_deactivate = ['meeting_mode', 'travel_mode']

for macro in macros_to_deactivate:
    print(f'\\n🛑 Deactivating macro: {macro}')
    result = deactivate_macro(macro)
    print(f'Result: {\"✅ Success\" if result else \"❌ Failed\"}')

print('\\n📋 Active Macros After Deactivation:')
list_active_macros()
"

echo ""

# Test 4: Trigger condition checking
echo "🧪 Test 4: Trigger Condition Testing"
echo "Testing how macro triggers evaluate conditions..."
echo ""

CONTEXT_MACROS_ENABLED="true" python3 -c "
import os
os.environ['CONTEXT_MACROS_ENABLED'] = 'true'

from athena_notifications import check_macro_triggers, MACRO_TRIGGERS, should_activate_macro, update_smart_alerting
import time

print('Testing macro trigger conditions:')
print('=================================')

# Test different trigger scenarios
scenarios = [
    {'name': 'Calendar Meeting Trigger', 'context': {'calendar_busy': True}},
    {'name': 'Location Travel Trigger', 'context': {'location': 'travel'}},
    {'name': 'Location Home Trigger', 'context': {'location': 'home'}},
    {'name': 'Time Maintenance Trigger', 'context': {}, 'time_override': True}
]

for scenario in scenarios:
    print(f'\\n🧪 Testing: {scenario[\"name\"]}')
    
    # Mock the context
    if 'time_override' in scenario:
        # Test maintenance time (2:00-4:00)
        current_time = time.mktime(time.strptime('02:30', '%H:%M'))
    else:
        current_time = time.time()
    
    # Check each trigger
    for trigger_name, trigger_config in MACRO_TRIGGERS.items():
        try:
            activated = should_activate_macro(trigger_name, trigger_config, scenario['context'], current_time)
            macro_name = trigger_config.get('macro', 'unknown')
            print(f'  {trigger_name} → {macro_name}: {\"✅ WOULD ACTIVATE\" if activated else \"❌ Would not activate\"}')
        except Exception as e:
            print(f'  {trigger_name} → Error: {e}')
"

echo ""

# Test 5: Macro history and monitoring
echo "🧪 Test 5: Macro History & Monitoring"
echo "Testing macro execution tracking and history..."
echo ""

python3 -c "
from athena_notifications import MACRO_HISTORY, execute_macro

print('Testing macro history tracking:')
print('===============================')

# Execute a few macros to build history
test_macros = ['emergency_mode', 'maintenance_mode']
for macro in test_macros:
    execute_macro(macro, 'history_test')

print(f'\\n📊 Macro Execution History:')
print(f'Total executions: {len(MACRO_HISTORY)}')

for i, entry in enumerate(MACRO_HISTORY[-3:], 1):  # Show last 3
    timestamp = time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))
    success_rate = f\"{entry['success_count']}/{entry['total_commands']}\"
    print(f'{i}. {entry[\"macro\"]} ({timestamp}) - {success_rate} commands successful')
"

echo ""

# Test 6: Integration with smart alerting
echo "🧪 Test 6: Integration with Smart Alerting"
echo "Testing how macros work with the broader alerting context..."
echo ""

CONTEXT_MACROS_ENABLED="true" python3 -c "
import os
os.environ['CONTEXT_MACROS_ENABLED'] = 'true'

from athena_notifications import update_smart_alerting, initialize_context_macros

print('Testing macro integration with smart alerting:')
print('=============================================')

# Get current context
context = update_smart_alerting()
print('Current Context Summary:')
print(f'• Location: {context.get(\"location\", \"unknown\")}')
print(f'• Calendar busy: {context.get(\"calendar_busy\", False)}')
print(f'• Focus mode: {context.get(\"focus_mode\", False)}')
print(f'• Quiet hours: {context.get(\"quiet_hours\", False)}')
print()

# Test macro initialization
print('🎯 Initializing context macro monitoring...')
result = initialize_context_macros()
print(f'Macro monitoring: {\"✅ Started\" if result else \"❌ Failed\"}')
print()

print('💡 In production, macros would automatically trigger based on:')
print('   • Calendar events starting (meeting_mode)')
print('   • GPS detecting travel (travel_mode)')
print('   • Time windows (maintenance_mode)')
print('   • Alert volume spikes (emergency_mode)')
"

echo ""

echo "🎯 Context-Reactive Macros Demo Complete!"
echo ""
echo "Macro System Features:"
echo "🎯 Template-Based: Pre-defined operational modes"
echo "🎪 Trigger-Aware: Auto-activation based on context"
echo "⚙️ Command Sequencing: Multi-step operations"
echo "📊 Execution Tracking: Full audit trail"
echo "🔄 State Management: Active macro monitoring"
echo "🧠 Context Integration: Works with smart alerting"
echo ""
echo "Available Macros:"
echo "• meeting_mode - Auto-quiet for calendar meetings"
echo "• emergency_mode - High alert escalation"
echo "• maintenance_mode - Controlled silence for maintenance"
echo "• travel_mode - Travel-optimized settings"
echo "• focus_mode - Deep work minimal interruptions"
echo ""
echo "Trigger Types:"
echo "• Calendar: Auto-activate when meetings start"
echo "• Location: GPS-based mode switching"
echo "• Time: Scheduled operational windows"
echo "• Alerts: Volume-based emergency activation"
echo ""
echo "Configuration:"
echo "• Enable: CONTEXT_MACROS_ENABLED=true"
echo "• Interval: MACRO_CHECK_INTERVAL=60"
echo "• Custom: Add triggers to MACRO_TRIGGERS"
echo "• Extend: Add commands to MACRO_TEMPLATES"
echo ""
echo "Usage Examples:"
echo "• Manual: execute_macro('meeting_mode')"
echo "• List: list_available_macros()"
echo "• Active: list_active_macros()"
echo "• Deactivate: deactivate_macro('meeting_mode')"
echo "• Monitor: initialize_context_macros()"
