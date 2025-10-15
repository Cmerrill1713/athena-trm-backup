#!/bin/bash
# Demo: Voice Activation - Wake Word Detection and Command Processing
# Shows how Athena listens for wake words and executes voice commands

echo "🎤 AI Republic Voice Activation Demo"
echo "==================================="
echo ""

# Test 1: Voice activation configuration
echo "🧪 Test 1: Voice Activation Setup"
echo "Testing voice activation configuration and initialization..."
echo ""

VOICE_ACTIVATION_ENABLED="true" COMMAND_ROUTING_ENABLED="true" python3 -c "
import os
os.environ['VOICE_ACTIVATION_ENABLED'] = 'true'
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'

from athena_notifications import test_voice_activation
test_voice_activation()
"

echo ""

# Test 2: Wake word detection
echo "🧪 Test 2: Wake Word Detection"
echo "Testing wake word parsing and command extraction..."
echo ""

WAKE_WORD="hey athena" python3 -c "
import os
os.environ['WAKE_WORD'] = 'hey athena'
os.environ['VOICE_ACTIVATION_ENABLED'] = 'true'
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'

from athena_notifications import WAKE_WORD, process_voice_command

test_phrases = [
    'hey athena check system status',
    'hey athena acknowledge alerts',
    'hey athena start monitoring',
    'hey athena stop voice notifications',
    'hey athena what is the performance',
    'hello computer',  # Should be ignored
    'hey athena',      # Wake word only, no command
]

print('Wake Word Detection Test:')
print('=========================')
print(f'Configured Wake Word: \"{WAKE_WORD}\"')
print()

for phrase in test_phrases:
    print(f'Input: \"{phrase}\"')
    if phrase.startswith(WAKE_WORD):
        command = phrase[len(WAKE_WORD):].strip()
        if command:
            print(f'✓ Wake word detected, command: \"{command}\"')
            response = process_voice_command(command)
            print(f'✓ Response: \"{response}\"')
        else:
            print('✓ Wake word detected, but no command given')
    else:
        print('✗ Not our wake word - ignored')
    print()
"

echo ""

# Test 3: Voice activation configuration
echo "🧪 Test 3: Configuration Options"
echo "Testing different wake word and timeout configurations..."
echo ""

python3 -c "
import os
from athena_notifications import configure_voice_activation

print('Voice Activation Configuration Test:')
print('===================================')
print()

# Test different wake words
wake_words = ['hey athena', 'computer', 'ai assistant', 'athena']

for wake_word in wake_words:
    print(f'Testing wake word: \"{wake_word}\"')
    configure_voice_activation(wake_word=wake_word)
    print()

# Test different timeouts
timeouts = [5, 10, 15, 30]

print('Testing timeout configurations:')
for timeout in timeouts:
    configure_voice_activation(timeout=timeout)
    print()
"

echo ""

# Test 4: Integration test
echo "🧪 Test 4: Full Voice Command Pipeline"
echo "Testing the complete wake word → command processing → response pipeline..."
echo ""

WAKE_WORD="hey athena" VOICE_ACTIVATION_ENABLED="true" COMMAND_ROUTING_ENABLED="true" python3 -c "
import os
os.environ['WAKE_WORD'] = 'hey athena'
os.environ['VOICE_ACTIVATION_ENABLED'] = 'true'
os.environ['COMMAND_ROUTING_ENABLED'] = 'true'

from athena_notifications import WAKE_WORD, process_voice_command

print('Full Voice Command Pipeline Test:')
print('=================================')
print()

# Simulate voice input with wake word
voice_inputs = [
    'hey athena check system status',
    'hey athena acknowledge all alerts',
    'hey athena start the monitoring service',
    'hey athena stop voice notifications',
    'hey athena what is my performance like',
    'hey athena enable location tracking',
    'hey athena show me active alerts'
]

for voice_input in voice_inputs:
    print(f'🎤 Heard: \"{voice_input}\"')

    if voice_input.startswith(WAKE_WORD):
        command = voice_input[len(WAKE_WORD):].strip()
        print(f'🎯 Extracted command: \"{command}\"')

        # Process through command routing
        response = process_voice_command(command)
        print(f'🤖 Athena responds: \"{response}\"')

        # Simulate voice feedback
        voice_feedback = f'Command executed: {response}'
        print(f'🔊 Voice feedback: \"{voice_feedback}\"')
    else:
        print('❌ Not our wake word')

    print('─' * 50)
"

echo ""

# Test 5: Error handling
echo "🧪 Test 5: Error Handling and Edge Cases"
echo "Testing voice activation error handling..."
echo ""

VOICE_ACTIVATION_ENABLED="false" python3 -c "
import os
os.environ['VOICE_ACTIVATION_ENABLED'] = 'false'

from athena_notifications import initialize_voice_activation, test_voice_activation

print('Error Handling Test:')
print('====================')
print()

print('Testing disabled voice activation:')
result = initialize_voice_activation()
print(f'Initialize result: {result}')
print()

print('Testing disabled voice activation test:')
test_voice_activation()
print()
"

echo ""

echo "🎯 Voice Activation Demo Complete!"
echo ""
echo "Voice Activation Features:"
echo "🎤 Wake Word Detection: Configurable wake phrases"
echo "⏰ Timeout Management: Configurable listening periods"
echo "🎯 Command Extraction: Intelligent command parsing"
echo "🔄 Full Pipeline: Wake word → command → execution → feedback"
echo "🛡️ Error Handling: Graceful failure and recovery"
echo "⚙️ Configuration: Customizable wake words and timeouts"
echo ""
echo "Real-World Voice Commands:"
echo "• 'Hey Athena, check system status'"
echo "• 'Hey Athena, acknowledge alerts'"
echo "• 'Hey Athena, start monitoring'"
echo "• 'Hey Athena, stop voice notifications'"
echo "• 'Hey Athena, enable location tracking'"
echo "• 'Hey Athena, what is the performance'"
echo ""
echo "Configuration:"
echo "• Enable: VOICE_ACTIVATION_ENABLED=true"
echo "• Wake Word: WAKE_WORD=\"hey athena\""
echo "• Timeout: VOICE_ACTIVATION_TIMEOUT=10"
echo "• Dependencies: pip install SpeechRecognition"
echo ""
echo "Usage Examples:"
echo "• Background: initialize_voice_activation()"
echo "• Test: test_voice_activation()"
echo "• Configure: configure_voice_activation(wake_word='computer')"
echo ""
echo "Production Setup:"
echo "1. Enable voice activation in .env"
echo "2. Install SpeechRecognition: pip install SpeechRecognition"
echo "3. Initialize: python3 -c 'from athena_notifications import initialize_voice_activation; initialize_voice_activation()'"
echo "4. Test: ./demo_voice_activation.sh"
echo "5. Use: Say 'Hey Athena' + command"
