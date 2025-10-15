#!/bin/bash
# Pin Samantha as Athena's voice

echo "🎤 Pinning Samantha as Athena's voice"
echo "======================================"
echo ""

# Create directory
mkdir -p ~/.athena

# Set voice ID and name
echo "com.apple.ttsbundle.Samantha-compact" > ~/.athena/voice.id
echo "Samantha" > ~/.athena/voice.name

# Also set in UserDefaults for the app
defaults write build.AthenaReporter athena.voiceId "com.apple.ttsbundle.Samantha-compact"
defaults write build.AthenaReporter athena.voice.name "Samantha"

echo "✅ Voice pinned:"
echo "   ID: $(cat ~/.athena/voice.id)"
echo "   Name: $(cat ~/.athena/voice.name)"
echo ""

echo "🧪 Testing voice:"
say -v "Samantha" "Voice successfully pinned. This is Athena speaking with Samantha's voice."
echo ""

echo "🔄 Next steps:"
echo "   1. Restart the AthenaReporter app if it's running"
echo "   2. Run: make report-health"
echo "   3. Listen for Samantha's voice (should NOT be generic)"

