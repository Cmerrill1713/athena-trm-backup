#!/bin/bash
# Switch AI Republic to production cadence (quiet, efficient operation)

echo "🔄 Switching AI Republic to Production Mode"
echo "==========================================="

# Unload test agents
launchctl unload ~/Library/LaunchAgents/com.athena.memory.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.athena.voice.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.athena.briefing.plist 2>/dev/null || true

# Create production launch agents
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# Memory monitoring - PRODUCTION: every 6 hours
cat > "$LAUNCH_AGENTS_DIR/com.athena.memory.plist" << PROD_EOF
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
    <integer>21600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/ai-republic/memory.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/memory_error.log</string>
</dict>
</plist>
PROD_EOF

# Voice integration - PRODUCTION: continuous but quiet
cat > "$LAUNCH_AGENTS_DIR/com.athena.voice.plist" << PROD_EOF
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
    <string>/var/log/ai-republic/voice.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/voice_error.log</string>
</dict>
</plist>
PROD_EOF

# Daily briefing - PRODUCTION: 9 AM daily (unchanged)
cat > "$LAUNCH_AGENTS_DIR/com.athena.briefing.plist" << PROD_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.briefing</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 athena_ops_copilot.py --mode briefing</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/var/log/ai-republic/briefing.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/briefing_error.log</string>
</dict>
</plist>
PROD_EOF

# Tribunal monitoring - PRODUCTION: every 2 hours
cat > "$LAUNCH_AGENTS_DIR/com.athena.tribunal.plist" << PROD_EOF
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
    <integer>7200</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/ai-republic/tribunal.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/tribunal_error.log</string>
</dict>
</plist>
PROD_EOF

# Optional Dashboard - PRODUCTION: manual start only
cat > "$LAUNCH_AGENTS_DIR/com.athena.dashboard.plist" << PROD_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PWD && source .venv/bin/activate && python3 athena_dashboard.py --port 8090</string>
    </array>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/var/log/ai-republic/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ai-republic/dashboard_error.log</string>
</dict>
</plist>
PROD_EOF

# Load production agents
echo "📦 Loading production launch agents..."
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.memory.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.voice.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.briefing.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.tribunal.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.athena.dashboard.plist"  # Optional - manual start

echo ""
echo "✅ PRODUCTION MODE ACTIVE"
echo ""
echo "📊 New Cadences:"
echo "  • Memory checks: Every 6 hours (was 10 min)"
echo "  • Tribunal sweeps: Every 2 hours (new)"
echo "  • Daily briefing: 9 AM daily (unchanged)"
echo "  • Voice listener: Always on (unchanged)"
echo ""
echo "🔇 System will run quietly in background"
echo "🚨 Alerts still trigger instantly when needed"
echo ""
echo "📊 Monitor activity:"
echo "  launchctl list | grep athena"
echo "  tail -f /var/log/ai-republic/*.log"
echo ""
echo "🖥️  View Dashboard:"
echo "  ./dashboard.sh start    # Start dashboard"
echo "  ./dashboard.sh open     # Open in browser"
echo "  ./dashboard.sh status   # Check status"
echo "  ./dashboard.sh stop     # Stop dashboard"
echo ""
echo "🔄 Switch back to test mode:"
echo "  ./test_cadence.sh"
