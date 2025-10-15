#!/bin/bash
# Demo: Command Routing - Natural Language Command Processing
# Shows how Athena understands and acts on voice/text commands

echo "🧠 AI Republic Command Routing Demo"
echo "==================================="
echo ""

# Test 1: Status queries
echo "🧪 Test 1: Status Command Classification"
echo "Testing how Athena understands status-related commands..."
echo ""

COMMAND_ROUTING_ENABLED="true" python3 -c "
import os
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'
from athena_notifications import classify_command_intent, execute_command_action

test_commands = [
    'What is the system status?',
    'Check system health',
    'Show me the dashboard',
    'How is everything running?',
    'System status please'
]

print('Status Command Classification:')
print('=============================')
for cmd in test_commands:
    classification = classify_command_intent(cmd)
    response = execute_command_action(classification['action'])
    print(f'Command: \"{cmd}\"')
    print(f'Intent: {classification[\"intent\"]} (confidence: {classification[\"confidence\"]:.2f})')
    print(f'Response: \"{response}\"')
    print()
"

echo ""

# Test 2: Alert management
echo "🧪 Test 2: Alert Management Commands"
echo "Testing alert acknowledgment and queries..."
echo ""

python3 -c "
import os
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'
from athena_notifications import classify_command_intent, execute_command_action

test_commands = [
    'Acknowledge the alert',
    'Dismiss all notifications',
    'Show me active alerts',
    'Are there any warnings?',
    'Clear the alerts'
]

print('Alert Management Classification:')
print('===============================')
for cmd in test_commands:
    classification = classify_command_intent(cmd)
    response = execute_command_action(classification['action'])
    print(f'Command: \"{cmd}\"')
    print(f'Intent: {classification[\"intent\"]} (confidence: {classification[\"confidence\"]:.2f})')
    print(f'Response: \"{response}\"')
    print()
"

echo ""

# Test 3: Service control
echo "🧪 Test 3: Service Control Commands"
echo "Testing system control and configuration commands..."
echo ""

python3 -c "
import os
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'
from athena_notifications import classify_command_intent, execute_command_action

test_commands = [
    'Start the monitoring service',
    'Stop voice notifications',
    'Restart the alerting system',
    'Enable location tracking',
    'Disable the dashboard'
]

print('Service Control Classification:')
print('==============================')
for cmd in test_commands:
    classification = classify_command_intent(cmd)
    response = execute_command_action(classification['action'])
    print(f'Command: \"{cmd}\"')
    print(f'Intent: {classification[\"intent\"]} (confidence: {classification[\"confidence\"]:.2f})')
    print(f'Response: \"{response}\"')
    print()
"

echo ""

# Test 4: Information queries
echo "🧪 Test 4: Information Query Commands"
echo "Testing how Athena handles questions and analysis requests..."
echo ""

python3 -c "
import os
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'
from athena_notifications import classify_command_intent, execute_command_action

test_commands = [
    'What is my performance like?',
    'How does the learning system work?',
    'When was the last alert?',
    'Why are there warnings?',
    'Analyze the system status'
]

print('Information Query Classification:')
print('================================')
for cmd in test_commands:
    classification = classify_command_intent(cmd)
    response = execute_command_action(classification['action'])
    print(f'Command: \"{cmd}\"')
    print(f'Intent: {classification[\"intent\"]} (confidence: {classification[\"confidence\"]:.2f})')
    print(f'Response: \"{response}\"')
    print()
"

echo ""

# Test 5: Voice command processing
echo "🧪 Test 5: Full Voice Command Processing"
echo "Testing the complete voice command pipeline..."
echo ""

python3 -c "
import os
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'
from athena_notifications import process_voice_command

test_commands = [
    'Check system status',
    'Acknowledge alerts',
    'Start monitoring',
    'What is the performance?',
    'Stop voice service'
]

print('Complete Voice Command Processing:')
print('==================================')
for cmd in test_commands:
    print(f'Input: \"{cmd}\"')
    response = process_voice_command(cmd)
    print(f'Output: \"{response}\"')
    print()
"

echo ""

# Test 6: Low confidence handling
echo "🧪 Test 6: Low Confidence Command Handling"
echo "Testing how Athena handles unclear or ambiguous commands..."
echo ""

python3 -c "
import os
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'
from athena_notifications import classify_command_intent, execute_command_action

test_commands = [
    'Do the thing',
    'Make it work',
    'Fix everything',
    'Hello computer',
    'xyz123abc'
]

print('Low Confidence Command Handling:')
print('===============================')
for cmd in test_commands:
    classification = classify_command_intent(cmd)
    response = execute_command_action(classification['action'])
    print(f'Command: \"{cmd}\"')
    print(f'Intent: {classification[\"intent\"]} (confidence: {classification[\"confidence\"]:.2f})')
    print(f'Response: \"{response}\"')
    print()
"

echo ""

echo "🎯 Command Routing Demo Complete!"
echo ""
echo "Command Routing Features:"
echo "🧠 Intent Classification: Keyword-based command understanding"
echo "🎯 Action Determination: Context-aware command execution"
echo "💬 Natural Language: Support for conversational commands"
echo "🔄 Confidence Scoring: Handles ambiguous inputs gracefully"
echo "⚡ Real-time Processing: Instant command execution"
echo ""
echo "Supported Command Types:"
echo "• Status: 'system status', 'check health', 'show dashboard'"
echo "• Alerts: 'acknowledge alerts', 'show warnings', 'dismiss notifications'"
echo "• Controls: 'start monitoring', 'stop voice', 'restart alerting'"
echo "• Queries: 'what is performance?', 'how does it work?', 'analyze status'"
echo "• Actions: 'acknowledge', 'dismiss', 'escalate'"
echo ""
echo "Configuration:"
echo "• Enable: COMMAND_ROUTING_ENABLED=true"
echo "• Extend: Add keywords to COMMAND_INTENT_SCHEMA"
echo "• Customize: Modify action handlers for specific behaviors"
echo ""
echo "Integration Points:"
echo "• Voice Commands: process_voice_command(text)"
echo "• Intent Classification: classify_command_intent(text)"
echo "• Action Execution: execute_command_action(action_dict)"
echo ""
echo "Next Steps:"
echo "• Add more sophisticated NLP (spaCy, BERT)"
echo "• Implement command history and context"
echo "• Add multi-step command chains"
echo "• Integrate with external APIs and services"
