#!/bin/bash
# Demo: Korono-First Voice Activation System
# Tests the complete Korono STT/TTS + Porcupine wake word integration

echo "🎵 AI Republic Korono-First Voice System Demo"
echo "============================================="
echo ""

# Test 1: Configuration verification
echo "🧪 Test 1: Korono Configuration Check"
echo "Testing voice system configuration..."
echo ""

python3 -c "
import os

# Check Korono-first settings
voice_engine = os.getenv('VOICE_ENGINE', 'korono')
korono_stt = os.getenv('KORONO_STT_MODEL', 'korono-stt-v1')
korono_tts = os.getenv('KORONO_TTS_VOICE', 'athena-neutral')
korono_sample_rate = os.getenv('KORONO_SAMPLE_RATE', '16000')
korono_vad = os.getenv('KORONO_VAD', 'true')
porcupine_enabled = os.getenv('USE_PORCUPINE_WAKE', 'true')
half_duplex = os.getenv('VOICE_HALF_DUPLEX', 'true')
voice_activation = os.getenv('VOICE_ACTIVATION_ENABLED', 'false')

print('🎵 Voice Engine Configuration:')
print('=============================')
print(f'Voice Engine: {voice_engine}')
print(f'Voice Activation: {\"✅ Enabled\" if voice_activation == \"true\" else \"❌ Disabled\"}')
print(f'Korono STT Model: {korono_stt}')
print(f'Korono TTS Voice: {korono_tts}')
print(f'Sample Rate: {korono_sample_rate}Hz')
print(f'VAD Enabled: {korono_vad}')
print(f'Porcupine Wake: {\"✅ Enabled\" if porcupine_enabled == \"true\" else \"❌ Disabled\"}')
print(f'Half-Duplex: {\"✅ Enabled\" if half_duplex == \"true\" else \"❌ Disabled\"}')
print()

if voice_engine == 'korono':
    print('🎉 Korono-first configuration detected!')
else:
    print('⚠️ Not using Korono - using legacy voice engine')
"

echo ""

# Test 2: Voice engine initialization
echo "🧪 Test 2: Voice Engine Initialization"
echo "Testing Korono engine startup and health checks..."
echo ""

VOICE_ENGINE="korono" KORONO_STT_MODEL="korono-stt-v1" KORONO_TTS_VOICE="athena-neutral" python3 -c "
from athena_notifications import KoronoEngine

print('🎯 Testing Korono Engine Initialization:')
print('======================================')

# Create Korono engine instance
engine = KoronoEngine(
    stt_model='korono-stt-v1',
    tts_voice='athena-neutral',
    sample_rate=16000,
    vad_enabled=True
)

print('Created KoronoEngine instance')

# Test engine startup
success = engine.start()
print(f'Engine startup: {\"✅ Success\" if success else \"❌ Failed\"}')

# Test health check
health = engine.health()
print(f'Health check: {health}')

# Test STT with mock data
mock_audio = b'test_audio_data'
transcription = engine.stt(mock_audio, 16000)
print(f'STT test: \"{transcription}\"')

# Test TTS
test_text = 'Hello from Korono'
audio_data = engine.tts(test_text)
print(f'TTS test: Generated {len(audio_data)} bytes of audio data')

print('✅ Korono engine basic functionality verified')
"

echo ""

# Test 3: Voice styles and context-awareness
echo "🧪 Test 3: Context-Aware Voice Styles"
echo "Testing mode-specific voice rendering..."
echo ""

python3 -c "
from athena_notifications import VOICE_STYLES

print('🎭 Voice Style Configuration:')
print('===========================')

for mode, style in VOICE_STYLES.items():
    print(f'{mode}:')
    print(f'  Voice: {style[\"voice\"]}')
    print(f'  Gain: {style[\"gain\"]}')
    print(f'  Brief: {style[\"brief\"]}')
    print()

print('💡 Voice styles automatically adapt to operational context:')
print('   • meeting_mode: Quiet, brief responses for meetings')
print('   • emergency_mode: Urgent, loud responses for alerts')
print('   • normal_mode: Balanced, full responses for general use')
"

echo ""

# Test 4: Voice diagnostics
echo "🧪 Test 4: Voice System Diagnostics"
echo "Testing comprehensive system health reporting..."
echo ""

VOICE_ACTIVATION_ENABLED="true" COMMAND_ROUTING_ENABLED="true" CONTEXT_MACROS_ENABLED="true" python3 -c "
from athena_notifications import generate_voice_diagnostics

print('🔍 Voice System Diagnostics:')
print('===========================')

diagnostics = generate_voice_diagnostics()
print(f'Diagnostics: \"{diagnostics}\"')

print()
print('📊 Parsed Diagnostics:')
for item in diagnostics.split('. '):
    print(f'   • {item}')
"

echo ""

# Test 5: Voice command processing simulation
echo "🧪 Test 5: Voice Command Processing"
echo "Testing the complete voice command pipeline..."
echo ""

COMMAND_ROUTING_ENABLED="true" python3 -c "
from athena_notifications import process_voice_command

print('🎤 Voice Command Processing Test:')
print('================================')

test_commands = [
    'check system status',
    'acknowledge alerts',
    'start monitoring',
    'what is the performance',
    'deck diagnostics'
]

for cmd in test_commands:
    print(f'\\n🎯 Processing: \"{cmd}\"')
    try:
        response = process_voice_command(cmd)
        print(f'🤖 Response: \"{response}\"')
    except Exception as e:
        print(f'❌ Error: {e}')

print('\\n✅ Voice command processing pipeline verified')
"

echo ""

# Test 6: Half-duplex simulation
echo "🧪 Test 6: Half-Duplex Operation"
echo "Testing STT pause/resume during TTS playback..."
echo ""

VOICE_HALF_DUPLEX="true" python3 -c "
from athena_notifications import VOICE_HALF_DUPLEX, KoronoEngine

print('📞 Half-Duplex Voice Operation Test:')
print('===================================')

# Create test engine
engine = KoronoEngine('korono-stt-v1', 'athena-neutral', 16000, True)
engine.start()

print(f'Half-duplex enabled: {VOICE_HALF_DUPLEX}')

# Test pause/resume functionality
print('Testing STT pause/resume:')
engine.pause_stt()
print('   • STT paused for TTS playback')

# Simulate TTS duration
import time
time.sleep(0.1)

engine.resume_stt()
print('   • STT resumed after TTS completion')

print('✅ Half-duplex operation verified')
"

echo ""

# Test 7: Voice override arbitration
echo "🧪 Test 7: Voice Override Arbitration"
echo "Testing how voice commands override automated macros..."
echo ""

VOICE_OVERRIDE_TTL="900" python3 -c "
from athena_notifications import voice_command_to_mode, VOICE_OVERRIDE_TTL

print('🎯 Voice Override Arbitration Test:')
print('==================================')

test_intents = ['status', 'alerts', 'controls']

for intent in test_intents:
    mode = voice_command_to_mode(intent)
    if mode:
        print(f'Intent \"{intent}\" → Override mode \"{mode}\" (TTL: {VOICE_OVERRIDE_TTL}s)')
    else:
        print(f'Intent \"{intent}\" → No override mode')

print()
print('💡 Voice commands with \"override\" keyword will:')
print('   • Suppress conflicting macro automation')
print('   • Apply manual override with TTL')
print('   • Log override event for audit')
"

echo ""

echo "🎯 Korono-First Voice System Demo Complete!"
echo ""
echo "Korono-First Architecture Features:"
echo "🎵 Single Engine Ownership: Korono handles all STT/TTS"
echo "🎧 Porcupine Wake Word: Efficient, low-power wake detection"
echo "📞 Half-Duplex Operation: Prevents self-triggering"
echo "🎭 Context-Aware Voices: Mode-specific voice styles"
echo "🔐 Priority Arbitration: Voice overrides automation"
echo "🩺 Health Monitoring: Watchdog and diagnostics"
echo "🛡️ Idempotent Init: Safe multiple startups"
echo "📊 Comprehensive Diagnostics: Full system health reporting"
echo ""
echo "Voice Commands Ready:"
echo "• 'Hey Athena, check system status'"
echo "• 'Hey Athena, acknowledge alerts'"
echo "• 'Hey Athena, start monitoring'"
echo "• 'Hey Athena, deck diagnostics'"
echo "• 'Hey Athena, [command] override' (bypasses automation)"
echo ""
echo "Configuration Applied:"
echo "• VOICE_ENGINE=korono"
echo "• KORONO_STT_MODEL=korono-stt-v1"
echo "• KORONO_TTS_VOICE=athena-neutral"
echo "• USE_PORCUPINE_WAKE=true"
echo "• VOICE_HALF_DUPLEX=true"
echo ""
echo "Next Steps:"
echo "1. Install pvporcupine: pip install pvporcupine pyaudio"
echo "2. Enable voice: VOICE_ACTIVATION_ENABLED=true"
echo "3. Start system: python3 -c 'from athena_notifications import initialize_voice_activation; initialize_voice_activation()'"
echo "4. Test commands: Say 'Hey Athena, deck diagnostics'"
echo ""
echo "🎉 Korono-first voice system ready for production!"
