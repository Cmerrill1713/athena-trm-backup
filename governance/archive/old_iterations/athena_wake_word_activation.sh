#!/bin/bash

# ATHENA WAKE-WORD ACTIVATION
# Enable hands-free "Hey Athena" voice control

set -e

echo "🎤 ACTIVATING ATHENA WAKE-WORD CONTROL"
echo "======================================"
echo ""

# Check if Athena is installed
if [ ! -f "/opt/ai-republic/athena_voice_integration.py" ]; then
    echo "❌ Athena voice integration not found. Please install Athena first:"
    echo "   sudo ./install_athena_copilot.sh"
    exit 1
fi

# Check voice capabilities
echo "🔍 Checking voice capabilities..."
if python3 -c "import speech_recognition, pyttsx3" 2>/dev/null; then
    echo "✅ Voice libraries detected"
else
    echo "❌ Voice libraries not found. Installing..."
    pip3 install SpeechRecognition pyttsx3 pyaudio
    echo "✅ Voice libraries installed"
fi

# Test voice setup
echo ""
echo "🧪 Testing voice environment..."
python3 /opt/ai-republic/athena_voice_integration.py --setup

# Create wake-word service
echo ""
echo "🔧 Creating wake-word systemd service..."

sudo tee /etc/systemd/system/athena-wake-word.service > /dev/null << 'EOF'
[Unit]
Description=Athena Wake-Word Voice Control
After=ai-republic-constitutional.service ai-republic-judicial.service
Wants=ai-republic-constitutional.service ai-republic-judicial.service

[Service]
Type=simple
User=ai-republic
Group=ai-republic
WorkingDirectory=/opt/ai-republic
ExecStart=/usr/bin/env python3 athena_voice_integration.py --mode continuous
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-republic-athena-voice

[Install]
WantedBy=multi-user.target
EOF

# Create desktop launcher for manual wake-word activation
if [ -d ~/Desktop ]; then
    cat > ~/Desktop/Athena-Wake-Word.desktop << 'EOF'
[Desktop Entry]
Name=Athena Wake Word
Comment=Hands-free Athena voice control
Exec=gnome-terminal --title="Athena Wake Word" --command "python3 /opt/ai-republic/athena_voice_integration.py --mode continuous"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=System;Monitor;
EOF
    chmod +x ~/Desktop/Athena-Wake-Word.desktop
    echo "✅ Desktop launcher created"
fi

# Copy sensitivity config tool
sudo cp athena_sensitivity_config.py /opt/ai-republic/
sudo chmod +x /opt/ai-republic/athena_sensitivity_config.py

# Add convenience aliases
if ! grep -q "alias athena-wake=" ~/.bashrc 2>/dev/null; then
    echo "alias athena-wake='python3 /opt/ai-republic/athena_voice_integration.py --mode continuous'" >> ~/.bashrc
    echo "alias athena-voice-on='sudo systemctl start athena-wake-word'" >> ~/.bashrc
    echo "alias athena-voice-off='sudo systemctl stop athena-wake-word'" >> ~/.bashrc
    echo "alias athena-sensitivity='python3 /opt/ai-republic/athena_sensitivity_config.py'" >> ~/.bashrc
    echo "alias athena-sens-low='python3 /opt/ai-republic/athena_sensitivity_config.py set low'" >> ~/.bashrc
    echo "alias athena-sens-med='python3 /opt/ai-republic/athena_sensitivity_config.py set medium'" >> ~/.bashrc
    echo "alias athena-sens-high='python3 /opt/ai-republic/athena_sensitivity_config.py set high'" >> ~/.bashrc
fi

echo ""
echo "🎉 WAKE-WORD CONTROL ACTIVATED!"
echo ""
echo "📡 How to use:"
echo ""
echo "1. MANUAL ACTIVATION:"
echo "   athena-wake"
echo "   # Or click the desktop icon"
echo ""
echo "2. BACKGROUND SERVICE:"
echo "   sudo systemctl enable athena-wake-word"
echo "   sudo systemctl start athena-wake-word"
echo ""
echo "3. SERVICE CONTROL:"
echo "   athena-voice-on   # Start wake-word service"
echo "   athena-voice-off  # Stop wake-word service"
echo ""
echo "🎤 WAKE WORDS:"
echo "   • 'Athena' or 'Hey Athena'"
echo "   • 'AI Republic' or 'System'"
echo ""
echo "🎚️ SENSITIVITY CONTROL:"
echo "   athena-sensitivity list          # Show all levels"
echo "   athena-sensitivity recommend 'busy office'  # Get recommendation"
echo "   athena-sens-low                  # Quiet environment"
echo "   athena-sens-med                  # Balanced (default)"
echo "   athena-sens-high                 # Noisy environment"
echo ""
echo "💬 USAGE EXAMPLES:"
echo "   'Hey Athena, check system status'"
echo "   'Athena, show tribunal alerts'"
echo "   'AI Republic, restart services'"
echo "   'System, what are the metrics?'"
echo ""
echo "🎚️ SENSITIVITY EXAMPLES:"
echo "   For quiet office: athena-sens-low"
echo "   For busy workspace: athena-sens-high"
echo "   For home office: athena-sens-med (default)"
echo ""
echo "🛑 To stop listening:"
echo "   Say 'stop listening' or use Ctrl+C"
echo ""
echo "🔊 Athena will respond with voice when activated by wake words"
echo ""
echo "📝 NOTES:"
echo "   • Keep microphone clear and speak clearly"
echo "   • Background noise may affect recognition"
echo "   • Adjust sensitivity for your environment"
echo "   • Test with: athena-sensitivity test"
echo ""
echo "Run 'source ~/.bashrc' to activate new aliases"
echo ""
echo "🎯 Athena Wake-Word Control is now ready for hands-free operation!"
