#!/bin/bash
# Switch AI Republic back to test cadence (frequent checks for development)

echo "🧪 Switching AI Republic to Test Mode"
echo "====================================="

# Unload production agents
launchctl unload ~/Library/LaunchAgents/com.athena.memory.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.athena.voice.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.athena.briefing.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.athena.tribunal.plist 2>/dev/null || true

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# Memory monitoring - TEST: every 10 minutes
cat > "$LAUNCH_AGENTS_DIR/com.athena.memory.plist" << TEST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.memory</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 athena_memory_optimizer.py --analyze</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/athena_memory_test.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/athena_memory_test_error.log</string>
</dict>
</plist>
TEST_EOF

# Voice integration - TEST: continuous
cat > "$LAUNCH_AGENTS_DIR/com.athena.voice.plist" << TEST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.voice</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 athena_voice_integration.py --mode continuous --set-sensitivity medium</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/athena_voice_test.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/athena_voice_test_error.log</string>
</dict>
</plist>
TEST_EOF

# Tribunal monitoring - TEST: every 30 minutes
cat > "$LAUNCH_AGENTS_DIR/com.athena.tribunal.plist" << TEST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.tribunal</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 phase2_config.json --tribunal-sweep</string>
    </array>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/athena_tribunal_test.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/athena_tribunal_test_error.log</string>
</dict>
</plist>
TEST_EOF

# Load test agents
echo "📦 Loading test launch agents..."
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.memory.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.voice.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.tribunal.plist"

echo ""
echo "🧪 TEST MODE ACTIVE"
echo ""
echo "📊 Test Cadences:"
echo "  • Memory checks: Every 10 minutes"
echo "  • Tribunal sweeps: Every 30 minutes"
echo "  • Voice listener: Always on"
echo ""
echo "📈 You'll see regular CPU activity"
echo "🚨 Alerts still work normally"
echo ""
echo "🔄 Switch to production:"
echo "  ./production_cadence.sh"
