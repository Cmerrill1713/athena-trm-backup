#!/usr/bin/env python3
"""
Test Alert Escalation System
============================

Test the three-tier alert escalation for critical notifications.

Features:
- Instant alerts (Telegram/Desktop)
- Follow-up alerts (Email/Slack) 2 seconds later
- Escalation alerts (All channels) if no acknowledgment after 5 minutes
- Alert acknowledgment system

Usage:
    python3 test_alert_escalation.py --test-critical    # Test full escalation chain
    python3 test_alert_escalation.py --test-warning     # Test warning (no escalation)
    python3 test_alert_escalation.py --acknowledge-all  # Acknowledge all pending alerts
    python3 test_alert_escalation.py --status           # Show escalation status
"""

import time
import argparse
import sys
import os

# Add system paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

def test_critical_alert_escalation():
    """Test the full critical alert escalation chain"""
    print("🚨 Testing Critical Alert Escalation Chain")
    print("=" * 50)
    print()

    print("🔔 Phase 1: Sending CRITICAL alert with cascade + escalation...")
    print("Expected behavior:")
    print("  [0s] 📱 Telegram/Desktop: Instant notification")
    print("  [+2s] 📧 Email/Slack: Follow-up with details")
    print("  [+5min] 🚨🚨 ALL CHANNELS: Escalation if not acknowledged")
    print()

    try:
        from athena_notifications import AthenaNotifications
        notifications = AthenaNotifications()

        # Send critical test alert with escalation
        results = notifications.send_notification(
            title="🚨 ESCALATION TEST: Critical Memory Alert",
            message="""CRITICAL ESCALATION TEST

This is a test of the three-tier alert escalation system:

🎯 Testing cascade delivery (instant → follow-up)
🎯 Testing escalation monitoring (5-minute timeout)
🎯 Testing acknowledgment system

If you see this alert, the cascade system is working!

To prevent escalation, acknowledge within 5 minutes:
  python3 test_alert_escalation.py --acknowledge-all

Or acknowledge specific alert ID when provided in escalation message.""",
            priority="urgent",
            cascade_priority=True,      # Enable cascade (Telegram first, then email)
            escalation_enabled=True,    # Enable escalation monitoring
            escalation_minutes=5        # 5-minute timeout
        )

        print("📤 Initial alert delivery results:")
        for channel, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {channel}")

        successful_channels = sum(1 for success in results.values() if success)
        print(f"\n🎯 Initial delivery: {successful_channels}/{len(results)} channels")
        print()

        if successful_channels > 0:
            print("⏱️ Escalation monitoring started...")
            print("• System will wait 5 minutes for acknowledgment")
            print("• If not acknowledged, escalation alert will be sent to ALL channels")
            print("• Escalation includes system beep and urgent messaging")
            print()
            print("To acknowledge and prevent escalation:")
            print("  python3 test_alert_escalation.py --acknowledge-all")
            print()
            print("To check escalation status:")
            print("  python3 test_alert_escalation.py --status")
            print()
            print("💡 Tip: Run --status in another terminal to monitor the countdown!")

        else:
            print("❌ No channels delivered successfully - check configuration")

    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_warning_alert():
    """Test warning alert (no escalation)"""
    print("⚠️ Testing Warning Alert (No Escalation)")
    print("=" * 40)
    print()

    try:
        from athena_notifications import AthenaNotifications
        notifications = AthenaNotifications()

        results = notifications.send_notification(
            title="⚠️ WARNING TEST: Memory Performance Alert",
            message="""WARNING TEST - NO ESCALATION

This warning alert should be delivered to all channels simultaneously.
No escalation monitoring is enabled for warnings.

This tests that warnings work normally without the escalation overhead.""",
            priority="warning",
            cascade_priority=False,     # No cascade for warnings
            escalation_enabled=False    # No escalation for warnings
        )

        print("📤 Warning alert delivery results:")
        for channel, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {channel}")

        successful_channels = sum(1 for success in results.values() if success)
        print(f"\n🎯 Delivery: {successful_channels}/{len(results)} channels")
        print("✅ No escalation monitoring (warnings don't escalate)")

    except Exception as e:
        print(f"❌ Warning test failed: {e}")

def acknowledge_alerts():
    """Acknowledge all pending alerts"""
    print("✅ Acknowledging All Pending Alerts")
    print("=" * 35)
    print()

    try:
        from athena_notifications import AthenaNotifications
        notifications = AthenaNotifications()

        acknowledged = notifications.acknowledge_alert()

        if acknowledged:
            print(f"✅ Successfully acknowledged {acknowledged} pending alert(s)")
            print("🎯 Escalation will be prevented for these alerts")
        else:
            print("ℹ️ No pending alerts found to acknowledge")

    except Exception as e:
        print(f"❌ Acknowledgment failed: {e}")

def show_escalation_status():
    """Show current escalation monitoring status"""
    print("📊 Alert Escalation Status")
    print("=" * 30)
    print()

    # Check for pending acknowledgment files
    import glob
    ack_files = glob.glob("/tmp/athena_alert_ack_*")

    if not ack_files:
        print("✅ No pending alerts - escalation monitoring inactive")
        return

    print(f"⏱️ Found {len(ack_files)} pending alert(s) being monitored:")
    print()

    import os
    current_time = time.time()

    for ack_file in sorted(ack_files):
        try:
            # Extract alert ID from filename
            alert_id = ack_file.replace("/tmp/athena_alert_ack_", "")

            # Check file modification time
            file_time = os.path.getmtime(ack_file)
            age_minutes = (current_time - file_time) / 60

            if age_minutes < 5:
                remaining = 5 - age_minutes
                print(f"🔔 Alert {alert_id}:")
                print(".1f")
                print("   💡 Run: python3 test_alert_escalation.py --acknowledge-all")
                print()
            else:
                print(f"🚨 Alert {alert_id}:")
                print(".1f")
                print("   ⚠️ ESCALATION MAY HAVE TRIGGERED!")
                print("   💡 Check logs: journalctl -u athena-memory-monitor -n 10")
                print()

        except Exception as e:
            print(f"❌ Error checking alert {ack_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test Alert Escalation System')
    parser.add_argument('--test-critical', action='store_true',
                       help='Test full critical alert escalation chain')
    parser.add_argument('--test-warning', action='store_true',
                       help='Test warning alert (no escalation)')
    parser.add_argument('--acknowledge-all', action='store_true',
                       help='Acknowledge all pending alerts to prevent escalation')
    parser.add_argument('--status', action='store_true',
                       help='Show escalation monitoring status')

    args = parser.parse_args()

    if args.test_critical:
        test_critical_alert_escalation()
    elif args.test_warning:
        test_warning_alert()
    elif args.acknowledge_all:
        acknowledge_alerts()
    elif args.status:
        show_escalation_status()
    else:
        print("🚨 Athena Alert Escalation Test System")
        print("=" * 45)
        print()
        print("Test the three-tier alert escalation:")
        print("1️⃣ Instant alerts (Telegram/Desktop)")
        print("2️⃣ Follow-up alerts (Email/Slack) +2s")
        print("3️⃣ Escalation alerts (All) if no ack after 5min")
        print()
        print("Commands:")
        print("  --test-critical     Test full escalation chain (5min wait)")
        print("  --test-warning      Test warning alert (no escalation)")
        print("  --acknowledge-all   Acknowledge pending alerts")
        print("  --status           Show escalation monitoring status")
        print()
        print("Example:")
        print("  python3 test_alert_escalation.py --test-critical")
        print("  # In another terminal:")
        print("  python3 test_alert_escalation.py --status  # Monitor countdown")
        print("  python3 test_alert_escalation.py --acknowledge-all  # Prevent escalation")

if __name__ == '__main__':
    main()
