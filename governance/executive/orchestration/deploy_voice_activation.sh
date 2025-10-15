#!/bin/bash
#
# Deploy Voice Activation for Athena
# ===================================
#
# This script sets up voice activation for Athena's AI Republic.
# Installs dependencies, configures permissions, and starts the service.
#

set -e

echo "🎤 Deploying Athena Voice Activation"
echo "===================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This deployment script is for macOS only"
    echo "   Voice activation requires macOS-specific audio libraries"
    exit 1
fi

# Function to check command success
check_command() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# 1. Install audio dependencies
echo
echo "1️⃣ Installing audio dependencies..."

# Install portaudio (required for PyAudio on macOS)
if ! brew list portaudio &>/dev/null; then
    echo "   Installing portaudio..."
    brew install portaudio
    check_command "PortAudio installation"
else
    echo "   ✅ PortAudio already installed"
fi

# Install Python packages
echo "   Installing Python audio packages..."
pip install SpeechRecognition PyAudio pyobjc
check_command "Python audio packages installation"

# Optional: Install pyttsx3 for voice responses
echo "   Installing text-to-speech (optional)..."
pip install pyttsx3 || echo "   ⚠️ pyttsx3 installation failed - voice responses disabled"

echo "✅ Audio dependencies installed"

# 2. Configure microphone permissions
echo
echo "2️⃣ Configuring microphone permissions..."
echo "   📋 Please ensure microphone access is enabled:"
echo "      System Settings → Privacy & Security → Microphone → ✅ Python"
echo "   Press Enter when complete..."
read -r

# 3. Test voice activation
echo
echo "3️⃣ Testing voice activation..."

# Run basic test
echo "   Running voice activation test..."
python3 demo_voice_activation.py --basic
check_command "Voice activation basic test"

# 4. Start voice activation service
echo
echo "4️⃣ Starting voice activation service..."

# Test the service
echo "   Testing voice activation service..."
python3 voice_activation.py --test
check_command "Voice activation service test"

# 5. Optional: Configure auto-start
echo
echo "5️⃣ Optional auto-start configuration..."

read -p "   Enable auto-start on login? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Configuring auto-start..."

    # Add to .zprofile for login auto-start
    if ! grep -q "voice_activation" ~/.zprofile 2>/dev/null; then
        echo "# Athena Voice Activation" >> ~/.zprofile
        echo "python3 -c \"from athena_notifications import initialize_voice_activation; initialize_voice_activation()\" &" >> ~/.zprofile
        echo "✅ Auto-start configured in ~/.zprofile"
    else
        echo "   ⚠️ Auto-start already configured"
    fi
else
    echo "   Skipping auto-start configuration"
fi

# 6. Create launchd service (optional)
echo
read -p "   Create launchd service for background operation? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Creating launchd service..."

    # Create launchd plist
    cat > ~/Library/LaunchAgents/com.athena.voice.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.voice</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>$(pwd)/voice_activation.py</string>
        <string>--start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/athena_voice.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/athena_voice.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

    # Load the service
    launchctl unload ~/Library/LaunchAgents/com.athena.voice.plist 2>/dev/null || true
    launchctl load ~/Library/LaunchAgents/com.athena.voice.plist

    echo "✅ Launchd service created and loaded"
    echo "   Service: com.athena.voice"
    echo "   Logs: /tmp/athena_voice.{out,err}"
else
    echo "   Skipping launchd service creation"
fi

# 7. Final instructions
echo
echo "🎉 Voice activation deployment complete!"
echo
echo "🚀 Quick start:"
echo "   python3 voice_activation.py --start"
echo
echo "🧪 Test commands:"
echo "   python3 demo_voice_activation.py --full"
echo
echo "🗣️ Voice commands:"
echo "   • 'Hey Athena, status'"
echo "   • 'Hey Athena, meeting mode'"
echo "   • 'Hey Athena, emergency'"
echo
echo "📋 Remember to enable microphone permissions if not done yet"
echo "🔒 Voice commands respect all security and authorization levels"

echo
echo "✅ Athena is now listening! 🎤🤖"
