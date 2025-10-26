#!/bin/bash
# ============================================================================
# SETUP AUTO-VALIDATION
# Configure nightly/boot validation for Athena
# ============================================================================

set -euo pipefail

REPO_ROOT=$(pwd)
SCRIPT_PATH="$REPO_ROOT/validate_and_recover.sh"

echo "🔧 Setting up auto-validation for Athena"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Make scripts executable
chmod +x "$REPO_ROOT/validate_and_recover.sh"
chmod +x "$REPO_ROOT/QUICK_SHIP_CHECK.sh"
chmod +x "$REPO_ROOT/create_baseline_snapshot.sh"

echo "✅ Scripts made executable"
echo ""

# ============================================================================
# OPTION 1: macOS LaunchAgent (Boot + Nightly)
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Option 1: macOS LaunchAgent (Recommended)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PLIST_PATH="$HOME/Library/LaunchAgents/dev.athena.validation.plist"

cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.athena.validation</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_PATH</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$REPO_ROOT</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>ATHENA_NO_CLOUD</key>
        <string>1</string>
        <key>ATHENA_ENV</key>
        <string>production</string>
        <key>RECOVERY_MODE</key>
        <string>auto</string>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$REPO_ROOT/artifacts/validation_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$REPO_ROOT/artifacts/validation_stderr.log</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
PLIST

echo "Created LaunchAgent: $PLIST_PATH"
echo ""
echo "This will:"
echo "  - Run at boot (RunAtLoad)"
echo "  - Run nightly at 3:00 AM"
echo "  - Auto-recover issues"
echo "  - Log to artifacts/"
echo ""

# Load the agent
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "✅ LaunchAgent loaded!"
echo ""

# ============================================================================
# OPTION 2: Cron (Alternative)
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Option 2: Cron (Alternative)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

CRON_LINE="0 3 * * * cd $REPO_ROOT && ATHENA_NO_CLOUD=1 RECOVERY_MODE=auto $SCRIPT_PATH >> $REPO_ROOT/artifacts/validation_cron.log 2>&1"

echo "To use cron instead, run:"
echo ""
echo "  crontab -e"
echo ""
echo "And add this line:"
echo ""
echo "  $CRON_LINE"
echo ""

# ============================================================================
# VALIDATION
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing validation now..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run validation once to test
RECOVERY_MODE=manual "$SCRIPT_PATH"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ AUTO-VALIDATION SETUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Athena will now:"
echo "  ✅ Validate at boot"
echo "  ✅ Validate nightly at 3:00 AM"
echo "  ✅ Auto-recover common issues"
echo "  ✅ Log all validation runs"
echo ""
echo "Check logs:"
echo "  tail -f artifacts/validation_stdout.log"
echo ""
echo "Manual run:"
echo "  ./validate_and_recover.sh"
echo ""
echo "💙 Athena is protected!"

