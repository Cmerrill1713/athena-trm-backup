#!/bin/bash
# Demo: Local Voice Processing Setup Test
# Tests if all components for offline voice processing are available

echo "🏠 AI Republic Local Voice Processing Setup Test"
echo "==============================================="
echo ""

# Test 1: Check component availability
echo "🧪 Test 1: Component Availability Check"
echo "Testing if all local voice processing components are installed..."
echo ""

python3 -c "
from athena_notifications import test_local_voice_setup
test_local_voice_setup()
"

echo ""

# Test 2: Configuration verification
echo "🧪 Test 2: Configuration Verification"
echo "Checking current voice processing configuration..."
echo ""

python3 -c "
import os

# Check environment variables
local_stt = os.getenv('USE_LOCAL_STT', 'false')
porcupine = os.getenv('USE_PORCUPINE_WAKE', 'false')
whisper_model = os.getenv('WHISPER_MODEL_SIZE', 'tiny')
voice_activation = os.getenv('VOICE_ACTIVATION_ENABLED', 'false')
wake_word = os.getenv('WAKE_WORD', 'hey athena')

print('🔧 Current Configuration:')
print('========================')
print(f'Voice Activation: {\"✅ Enabled\" if voice_activation == \"true\" else \"❌ Disabled\"}')
print(f'Local STT: {\"✅ Enabled\" if local_stt == \"true\" else \"❌ Disabled\"}')
print(f'Porcupine Wake: {\"✅ Enabled\" if porcupine == \"true\" else \"❌ Disabled\"}')
print(f'Whisper Model: {whisper_model}')
print(f'Wake Word: \"{wake_word}\"')
print()

if local_stt == 'true' and porcupine == 'true':
    print('🎉 Local voice processing is fully configured!')
    print('💡 Voice activation will use Porcupine + Whisper (offline)')
elif voice_activation == 'true':
    print('☁️ Voice activation will use cloud services (Google STT)')
    print('💡 To enable local processing: USE_LOCAL_STT=true USE_PORCUPINE_WAKE=true')
else:
    print('❌ Voice activation is disabled')
    print('💡 Enable with: VOICE_ACTIVATION_ENABLED=true')
"

echo ""

# Test 3: Installation instructions
echo "🧪 Test 3: Installation Guide"
echo "If components are missing, here's how to install them..."
echo ""

python3 -c "
from athena_notifications import test_local_voice_setup
all_available = test_local_voice_setup()

if not all_available:
    print()
    print('📦 Installation Instructions:')
    print('=============================')
    print('1. Install PyAudio (audio capture):')
    print('   pip install pyaudio')
    print('   # On macOS: brew install portaudio && pip install pyaudio')
    print()
    print('2. Install Porcupine (wake word detection):')
    print('   pip install pvporcupine')
    print()
    print('3. Install Whisper (local STT):')
    print('   pip install openai-whisper')
    print('   # Note: First run will download model (~150MB)')
    print()
    print('4. Install PyTorch (ML framework):')
    print('   pip install torch')
    print('   # Or: pip install torch torchvision torchaudio')
    print()
    print('5. Enable local processing:')
    print('   echo \"USE_LOCAL_STT=true\" >> .env')
    print('   echo \"USE_PORCUPINE_WAKE=true\" >> .env')
    print()
    print('6. Test setup:')
    print('   python3 -c \"from athena_notifications import test_local_voice_setup; test_local_voice_setup()\"')
"

echo ""

# Test 4: Performance comparison
echo "🧪 Test 4: Performance Comparison"
echo "Comparing local vs cloud voice processing..."
echo ""

python3 -c "
print('⚡ Performance Comparison:')
print('=========================')
print()
print('🌐 Cloud Processing (Google STT):')
print('  ✅ Always available (internet required)')
print('  ✅ High accuracy')
print('  ✅ No local setup')
print('  ❌ Requires internet')
print('  ❌ Privacy concerns')
print('  ❌ May have usage limits')
print()
print('🏠 Local Processing (Porcupine + Whisper):')
print('  ✅ Fully offline')
print('  ✅ Privacy-focused')
print('  ✅ No usage limits')
print('  ✅ Low latency (after model load)')
print('  ❌ Requires setup (~150MB download)')
print('  ❌ Higher CPU usage')
print('  ❌ Slightly lower accuracy than cloud')
print()
print('💡 Recommendation:')
print('  • Use cloud for testing/prototyping')
print('  • Use local for production/privacy-critical deployments')
"

echo ""

# Test 5: Quick start guide
echo "🧪 Test 5: Quick Start Guide"
echo "How to enable local voice processing..."
echo ""

echo "🚀 Quick Start Commands:"
echo "======================="
echo ""
echo "# 1. Install required packages"
echo "pip install pvporcupine pyaudio numpy openai-whisper torch"
echo ""
echo "# 2. Enable local processing in .env"
echo "echo 'VOICE_ACTIVATION_ENABLED=true' >> .env"
echo "echo 'USE_LOCAL_STT=true' >> .env"
echo "echo 'USE_PORCUPINE_WAKE=true' >> .env"
echo "echo 'WAKE_WORD=\"hey athena\"' >> .env"
echo ""
echo "# 3. Test setup"
echo "python3 -c 'from athena_notifications import test_local_voice_setup; test_local_voice_setup()'"
echo ""
echo "# 4. Start voice activation"
echo "python3 -c 'from athena_notifications import initialize_voice_activation; initialize_voice_activation()'"
echo ""
echo "# 5. Test commands"
echo "# Say: 'Hey Athena, check system status'"
echo "# Say: 'Hey Athena, acknowledge alerts'"
echo ""

echo "🎯 Local Voice Processing Demo Complete!"
echo ""
echo "Key Takeaways:"
echo "🏠 Local processing provides offline, privacy-focused voice control"
echo "⚡ Porcupine offers low-latency wake word detection"
echo "🧠 Whisper provides accurate local speech-to-text"
echo "🔧 Setup requires ~150MB download for Whisper model"
echo "🎪 Cloud fallback ensures reliability if local fails"
echo ""
echo "Next Steps:"
echo "• Install missing packages if needed"
echo "• Enable local processing: USE_LOCAL_STT=true USE_PORCUPINE_WAKE=true"
echo "• Test setup with the commands above"
echo "• Start voice activation and try commands"
