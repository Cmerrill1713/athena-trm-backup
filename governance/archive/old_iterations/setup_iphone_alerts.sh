#!/bin/bash
# Complete setup for FREE iPhone alerts using Apple Messages & macOS notifications
# No Twilio required - uses your Mac and iPhone ecosystem

set -euo pipefail

echo "📱 Setting up FREE iPhone alerts for AI Republic (Apple-native)"
echo "=" * 70

# 1) Check system requirements
echo "🔍 Checking system requirements..."
if ! command -v osascript &> /dev/null; then
    echo "❌ osascript not found - this requires macOS"
    exit 1
fi

if ! pgrep -x "Messages" &> /dev/null; then
    echo "⚠️  Messages app not running - iMessage alerts won't work"
    echo "   Start Messages.app and sign in with iCloud for full functionality"
fi

echo "✅ macOS and Messages app detected"

# 2) Create environment file
echo "🔐 Setting up environment file..."
cat > .env << 'EOF'
# Apple-native iPhone alerting (FREE - no external services required)
# Your iPhone number for iMessage alerts (leave blank to disable iMessage)
IPHONE_NUMBER="+1YOURIPHONE"     # e.g., +15551234567

# Alternative env var for backward compatibility
ATHENA_ALERT_PHONE="+1YOURIPHONE"
EOF

echo "✅ Environment file created"
echo "⚠️  IMPORTANT: Edit .env with your actual iPhone number!"

# 3) Test notification functionality
echo ""
echo "🧪 Testing notification functionality..."

python3 - <<'PY'
import os, sys
sys.path.insert(0, '.')

try:
    from athena_notifications import _send_system_notification
    result = _send_system_notification("AI Republic Setup Test", "Testing macOS notifications", "Ping")
    print(f"Notification test result: {result}")
    if result:
        print("✅ macOS notifications working!")
    else:
        print("⚠️  macOS notifications may not work - check terminal-notifier")
except Exception as e:
    print(f"❌ Notification test error: {e}")
PY

# 4) Test iMessage (if number provided)
echo ""
echo "🧪 Testing iMessage functionality..."

python3 - <<'PY'
import os
phone = os.getenv("IPHONE_NUMBER", os.getenv("ATHENA_ALERT_PHONE", ""))
if phone and phone != "+1YOURIPHONE":
    print(f"Testing iMessage to {phone}...")
    from athena_notifications import _send_imessage
    result = _send_imessage(phone, "Test: AI Republic iMessage alerts working! ✅")
    print(f"iMessage test result: {result}")
    if result:
        print("✅ iMessage working! Check your iPhone")
    else:
        print("⚠️  iMessage failed - check Messages app and phone number")
else:
    print("⚠️  No phone number configured - iMessage alerts disabled")
    print("   Edit .env with your iPhone number to enable iMessage alerts")
PY

echo ""
echo "🎯 Setup complete!"
echo ""
echo "Your AI Republic now has FREE iPhone alerting:"
echo ""
echo "📱 Alert Types:"
echo "  • macOS notifications (always work)"
echo "  • iMessage to iPhone (if number configured)"
echo "  • Voice alerts via macOS text-to-speech"
echo ""
echo "🧪 Test Commands:"
echo "  python3 test_iphone_alerts.py notification  # Test macOS notifications"
echo "  python3 test_iphone_alerts.py imessage     # Test iMessage alerts"
echo "  python3 test_iphone_alerts.py cascade      # Test full cascade"
echo ""
echo "⚙️  Configuration:"
echo "  • Edit .env to add your iPhone number"
echo "  • iMessages require Messages.app running and iCloud signed in"
echo "  • macOS notifications work without additional setup"
echo ""
echo "🚨 How it works:"
echo "  • Critical alerts: iMessage + macOS notification + voice escalation"
echo "  • Warning alerts: iMessage + macOS notification"
echo "  • All alerts sync to iPhone via iCloud notifications"
