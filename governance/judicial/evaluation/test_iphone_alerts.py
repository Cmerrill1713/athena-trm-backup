#!/usr/bin/env python3
"""
Test script for iPhone alerts using Apple Messages & macOS notifications
Run this to test the tiered alerting system (FREE - no Twilio required).
"""

import time
import uuid
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import the tiered alerting functions
from athena_notifications import send_tier1_immediate, send_tier2_followup, send_tier3_escalation

def test_imessage_only():
    """Test iMessage-only (warning level)"""
    print("🧪 Testing iMessage + notification alert...")
    result = send_tier1_immediate("WARNING: Synthetic test (no action needed)")
    print(f"Alert test result: {result}")
    print("Check your iPhone for iMessage and macOS notification")
    return result

def test_full_cascade():
    """Test full cascade (critical level): iMessage → iMessage → Voice (+30s unless ACK)"""
    print("🧪 Testing full cascade alert...")

    ack_id = str(uuid.uuid4())
    print(f"ACK ID: {ack_id}")
    print(f"To prevent voice alerts, run: touch /tmp/athena_alert_ack_{ack_id}")

    # Send immediate iMessage + notification
    send_tier1_immediate("CRITICAL: Full cascade test")

    # Send detailed iMessage + notification after 2 seconds
    send_tier2_followup("Details: This is a comprehensive test of the Apple-native alerting system. Tier 1 iMessage sent immediately. Tier 2 iMessage sent after 2 seconds. Tier 3 voice alerts will happen every 30 seconds unless acknowledged.")

    # Start escalation monitor (30 seconds for demo)
    send_tier3_escalation(
        tts_text="Athena escalation alert. Critical system issue detected. Immediate action required.",
        minutes_to_escalate=0.5,  # 30 seconds for demo
        ack_id=ack_id
    )

    print("✅ Cascade test initiated!")
    print("Watch for iMessages on iPhone + macOS notifications, and voice alerts in ~30s unless ACKed")
    return True

def test_acknowledgment():
    """Test acknowledgment mechanism"""
    print("🧪 Testing acknowledgment...")

    # Create a fake ack file to test the mechanism
    ack_id = str(uuid.uuid4())
    ack_path = f"/tmp/athena_alert_ack_{ack_id}"

    print(f"Creating ACK file: {ack_path}")
    with open(ack_path, 'w') as f:
        f.write(f"acknowledged_{int(time.time())}")

    print("✅ ACK file created - this would prevent escalation")
    return True

def test_notification_only():
    """Test macOS notifications only (no iMessage)"""
    print("🧪 Testing macOS notifications...")
    from athena_notifications import _send_system_notification
    result = _send_system_notification("AI Republic Test", "This is a macOS notification test", "Ping")
    print(f"Notification test result: {result}")
    return result

def test_voice_acknowledgment():
    """Test voice acknowledgment functionality"""
    print("🧪 Testing voice acknowledgment...")

    # First create a fake alert to acknowledge
    ack_id = str(uuid.uuid4())
    ack_path = f"/tmp/athena_alert_ack_{ack_id}"

    # Create the alert file (simulating an active alert)
    with open(ack_path, 'w') as f:
        f.write(f"alert_active_{int(time.time())}")

    print(f"Created test alert: {ack_id}")
    print("Testing acknowledgment...")

    # Test acknowledgment
    from athena_notifications import acknowledge_alert_by_voice
    result = acknowledge_alert_by_voice(ack_id)

    if result:
        print("✅ Voice acknowledgment successful")
        # Check if alert was acknowledged
        try:
            with open(ack_path, 'r') as f:
                content = f.read()
                if "acknowledged_by_voice" in content:
                    print("✅ Alert file properly updated")
                    return True
        except:
            pass

    print("❌ Voice acknowledgment failed")
    return False

if __name__ == "__main__":
    print("📱 Apple iPhone Alert Test Suite (FREE)")
    print("=" * 50)

    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "imessage":
            test_imessage_only()
        elif test_type == "cascade":
            test_full_cascade()
        elif test_type == "ack":
            test_acknowledgment()
        elif test_type == "notification":
            test_notification_only()
        elif test_type == "voice_ack":
            test_voice_acknowledgment()
        else:
            print("Usage: python test_iphone_alerts.py [imessage|cascade|ack|notification|voice_ack]")
    else:
        print("Available tests:")
        print("  imessage    - Test iMessage + notification alert")
        print("  cascade     - Test full tiered cascade (30s demo)")
        print("  ack         - Test acknowledgment mechanism")
        print("  notification- Test macOS notifications only")
        print("  voice_ack   - Test voice acknowledgment")
        print("\nExample: python test_iphone_alerts.py cascade")
