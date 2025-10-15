#!/bin/bash
# Demo: Voice Notifications for Weekly Summaries
# Shows how Athena speaks weekly learning summaries in different contexts

echo "🗣️ AI Republic Voice Notifications Demo"
echo "======================================"
echo ""

# Test 1: Voice notification during focus mode
echo "🧪 Test 1: Voice Notification During Focus Mode"
echo "Simulating Focus mode context where voice notifications are enabled..."
echo ""

FOCUS_MODE_ENABLED="true" FOCUS_MODE_ACTIVE="true" VOICE_NOTIFICATIONS_ENABLED="true" VOICE_NOTIFICATION_CONTEXTS="focus" VOICE_SUMMARY_LENGTH="normal" python3 -c "
import os
# Set focus mode and voice notifications
os.environ['FOCUS_MODE_ENABLED'] = 'true'
os.environ['FOCUS_MODE_ACTIVE'] = 'true'
os.environ['VOICE_NOTIFICATIONS_ENABLED'] = 'true'
os.environ['VOICE_NOTIFICATION_CONTEXTS'] = 'focus'
os.environ['VOICE_SUMMARY_LENGTH'] = 'normal'

from athena_notifications import should_use_voice_notifications, generate_voice_summary

# Sample weekly data
weekly_data = {
    'overall_confidence': 78,
    'patterns_found': 7,
    'preferred_prep_time': 8,
    'recommendations': ['Increase coffee break frequency', 'Try new learning approach', 'Adjust meeting schedule']
}

print('🎯 Focus Mode Voice Context:')
print(f'Use voice notifications: {should_use_voice_notifications()}')
print()
print('📢 Generated Voice Summary:')
voice_text = generate_voice_summary(weekly_data)
print(f'\"{voice_text}\"')
print()

# Note: We won't actually play the audio in demo to avoid spamming
print('💡 In production, this would speak aloud using macOS text-to-speech')
print('💡 Command used: say \"[voice_text]\"')
"

echo ""

# Test 2: Voice notification during travel/driving
echo "🧪 Test 2: Voice Notification During Travel"
echo "Simulating travel context with voice notifications..."
echo ""

LOCATION_ENABLED="true" LOCATION_OVERRIDE="travel" VOICE_NOTIFICATION_CONTEXTS="driving" python3 -c "
import os
os.environ['LOCATION_ENABLED'] = 'true'
os.environ['LOCATION_OVERRIDE'] = 'travel'
os.environ['VOICE_NOTIFICATIONS_ENABLED'] = 'true'
os.environ['VOICE_NOTIFICATION_CONTEXTS'] = 'driving'
os.environ['VOICE_SUMMARY_LENGTH'] = 'brief'

from athena_notifications import should_use_voice_notifications, generate_voice_summary

weekly_data = {
    'overall_confidence': 82,
    'patterns_found': 9,
    'preferred_prep_time': 12,
    'recommendations': ['Optimize travel schedule', 'Plan ahead for meetings']
}

print('🚗 Travel/Driving Voice Context:')
print(f'Use voice notifications: {should_use_voice_notifications()}')
print()
print('📢 Brief Voice Summary for Travel:')
voice_text = generate_voice_summary(weekly_data)
print(f'\"{voice_text}\"')
print()
print('💡 Brief summaries are perfect for driving - less distraction')
"

echo ""

# Test 3: Different summary lengths
echo "🧪 Test 3: Voice Summary Length Options"
echo "Comparing brief, normal, and detailed voice summaries..."
echo ""

VOICE_SUMMARY_LENGTH="brief" python3 -c "
import os
os.environ['VOICE_SUMMARY_LENGTH'] = 'brief'
from athena_notifications import generate_voice_summary

weekly_data = {
    'overall_confidence': 75,
    'patterns_found': 6,
    'preferred_prep_time': 10,
    'recommendations': ['Focus on key priorities', 'Take regular breaks']
}

print('📝 Brief Summary (30 seconds):')
print(f'\"{generate_voice_summary(weekly_data)}\"')
print(f'Length: {len(generate_voice_summary(weekly_data))} characters')
"

echo ""

VOICE_SUMMARY_LENGTH="normal" python3 -c "
import os
os.environ['VOICE_SUMMARY_LENGTH'] = 'normal'
from athena_notifications import generate_voice_summary

weekly_data = {
    'overall_confidence': 75,
    'patterns_found': 6,
    'preferred_prep_time': 10,
    'recommendations': ['Focus on key priorities', 'Take regular breaks']
}

print('📝 Normal Summary (45 seconds):')
print(f'\"{generate_voice_summary(weekly_data)}\"')
print(f'Length: {len(generate_voice_summary(weekly_data))} characters')
"

echo ""

VOICE_SUMMARY_LENGTH="detailed" python3 -c "
import os
os.environ['VOICE_SUMMARY_LENGTH'] = 'detailed'
from athena_notifications import generate_voice_summary

weekly_data = {
    'overall_confidence': 75,
    'patterns_found': 6,
    'preferred_prep_time': 10,
    'recommendations': ['Focus on key priorities', 'Take regular breaks']
}

print('📝 Detailed Summary (60+ seconds):')
print(f'\"{generate_voice_summary(weekly_data)}\"')
print(f'Length: {len(generate_voice_summary(weekly_data))} characters')
"

echo ""

# Test 4: Context combinations
echo "🧪 Test 4: Context Combination Logic"
echo "Testing how multiple contexts interact..."
echo ""

# Test different context combinations
contexts=(
    "FOCUS_MODE_ACTIVE=true:VOICE_NOTIFICATION_CONTEXTS=focus:focus mode"
    "LOCATION_OVERRIDE=travel:VOICE_NOTIFICATION_CONTEXTS=driving:travel mode"
    "QUIET_HOURS_ENABLED=true:VOICE_NOTIFICATION_CONTEXTS=quiet:quiet hours"
    "FOCUS_MODE_ACTIVE=true:LOCATION_OVERRIDE=travel:VOICE_NOTIFICATION_CONTEXTS=focus,driving:combined focus+travel"
)

for context_config in "${contexts[@]}"; do
    IFS=':' read -r env_var context_name description <<< "$context_config"
    echo "🔄 Testing: $description"

    # Set environment variables dynamically
    export $env_var

    FOCUS_MODE_ENABLED="true" LOCATION_ENABLED="true" VOICE_NOTIFICATIONS_ENABLED="true" python3 -c "
import os
from athena_notifications import should_use_voice_notifications

result = should_use_voice_notifications()
print(f'   Voice enabled: {result}')
"
done

# Reset environment
unset FOCUS_MODE_ACTIVE LOCATION_OVERRIDE QUIET_HOURS_ENABLED

echo ""

echo "🎯 Voice Notifications Demo Complete!"
echo ""
echo "Voice Notification Features:"
echo "🗣️ macOS Text-to-Speech: Uses built-in 'say' command"
echo "🎯 Smart Context Triggering: Focus mode, travel, quiet hours"
echo "📏 Adjustable Length: Brief (30s), Normal (45s), Detailed (60s)"
echo "🎪 Context Combinations: Multiple triggers can activate voice"
echo "🔇 Respects Alert Rules: Voice follows same smart filtering as text"
echo ""
echo "Real-World Use Cases:"
echo "• 🎯 Focus Mode: Hands-free updates during deep work"
echo "• 🚗 Driving: Audio summaries while commuting"
echo "• 🌙 Quiet Hours: Voice complements muted text notifications"
echo "• ✈️ Travel: Brief updates without screen distraction"
echo ""
echo "Configuration:"
echo "• Enable: VOICE_NOTIFICATIONS_ENABLED=true"
echo "• Contexts: VOICE_NOTIFICATION_CONTEXTS=\"focus,driving,quiet\""
echo "• Length: VOICE_SUMMARY_LENGTH=\"brief|normal|detailed\""
echo ""
echo "Test with: ./demo_voice_notifications.sh"
echo "Configure with: Edit .env file or use setup scripts"
