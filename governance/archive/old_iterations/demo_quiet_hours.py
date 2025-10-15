#!/usr/bin/env python3
"""
Demo Quiet Hours Alert Suppression
==================================

Demonstrate Athena's quiet hours feature - alerts are suppressed during
specified hours but critical issues still break through.

Usage:
    python3 demo_quiet_hours.py --status        # Check quiet hours status
    python3 demo_quiet_hours.py --test-normal   # Test normal alert during quiet hours
    python3 demo_quiet_hours.py --test-critical # Test critical alert (always goes through)
    python3 demo_quiet_hours.py --simulate      # Simulate quiet hours on/off
"""

import time
import sys
import os

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

def check_quiet_hours_status():
    """Check current quiet hours configuration and status"""
    print("🌙 Athena Quiet Hours Status")
    print("=" * 35)
    print()

    try:
        import requests
        response = requests.get("http://localhost:8009/quiet-hours", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Connected to Athena API")
            print()
            print(f"Status: {data['description']}")
            print(f"Enabled: {'Yes' if data['enabled'] else 'No'}")
            print(f"Time Range: {data['start_hour']:02d}:00 - {data['end_hour']:02d}:00")
            print(f"Currently Active: {'Yes' if data['is_quiet_hours'] else 'No'}")
            print()

            if data['is_quiet_hours']:
                print("🔕 ALERTS CURRENTLY SUPPRESSED")
                print("• Warning alerts will be queued")
                print("• Critical alerts will still notify")
                print("• Queued alerts deliver when quiet hours end")
            else:
                print("🔔 ALERTS CURRENTLY ENABLED")
                print("• All alerts will notify immediately")
                print("• No suppression active")

            return data
        else:
            print("❌ API connection failed")
            return None

    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure Athena API server is running:")
        print("   python3 athena_local_api.py")
        return None

def test_normal_alert():
    """Test a normal (warning) alert during quiet hours"""
    print("⚠️ Testing Normal Alert During Quiet Hours")
    print("=" * 45)

    # Simulate a warning alert that would normally be suppressed
    alert_data = {
        "id": f"test-normal-{int(time.time())}",
        "title": "High Memory Usage Detected",
        "message": "Memory utilization at 85%. This is a normal warning that would be suppressed during quiet hours.",
        "severity": "warning",
        "timestamp": time.time()
    }

    print(f"Alert: {alert_data['title']}")
    print(f"Severity: {alert_data['severity']}")
    print()

    try:
        import requests
        response = requests.post("http://localhost:8009/queue-alert", json=alert_data, timeout=5)
        if response.status_code == 200:
            print("✅ Alert queued successfully")
            print("📋 This alert will appear in dashboard when quiet hours end")
            print("💡 In real operation, this would be sent by the memory optimizer")
        else:
            print("❌ Alert queuing failed")
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_critical_alert():
    """Test a critical alert (always goes through)"""
    print("🚨 Testing Critical Alert (Always Goes Through)")
    print("=" * 50)

    # Simulate a critical alert that always breaks through
    alert_data = {
        "id": f"test-critical-{int(time.time())}",
        "title": "Memory Corruption Detected",
        "message": "CRITICAL: Memory corruption detected in core files. Immediate action required.",
        "severity": "critical",
        "timestamp": time.time()
    }

    print(f"Alert: {alert_data['title']}")
    print(f"Severity: {alert_data['severity']}")
    print("🚨 This alert ALWAYS goes through, even during quiet hours")
    print()

    try:
        import requests
        response = requests.post("http://localhost:8009/queue-alert", json=alert_data, timeout=5)
        if response.status_code == 200:
            print("✅ Critical alert queued successfully")
            print("🚨 In real operation, this would trigger immediate notifications")
            print("💡 Critical alerts bypass quiet hours suppression")
        else:
            print("❌ Critical alert queuing failed")
    except Exception as e:
        print(f"❌ Request failed: {e}")

def simulate_quiet_hours_cycle():
    """Simulate a quiet hours on/off cycle"""
    print("🔄 Simulating Quiet Hours Cycle")
    print("=" * 35)
    print()

    print("This simulation shows how alerts are handled:")
    print("1. Normal alerts get queued during quiet hours")
    print("2. Critical alerts always go through immediately")
    print("3. Queued alerts are delivered when quiet hours end")
    print()

    # Check current status
    print("📊 Current Status:")
    status = check_quiet_hours_status()
    if not status:
        print("❌ Cannot simulate without API connection")
        return

    print()
    print("🧪 Simulation Steps:")
    print("1. Send normal alert (should be queued if quiet hours active)")
    test_normal_alert()

    print()
    time.sleep(2)

    print("2. Send critical alert (should always go through)")
    test_critical_alert()

    print()
    print("3. Check queued alerts in dashboard")
    print("   → Open Athena Dashboard (Cmd+Shift+A)")
    print("   → Go to Alerts tab")
    print("   → Look for queued alerts with orange indicator")

def show_quiet_hours_guide():
    """Show comprehensive quiet hours guide"""
    print("🌙 Athena Quiet Hours - Complete Guide")
    print("=" * 40)
    print()

    print("🎯 WHAT IT DOES:")
    print("• Suppresses non-critical alerts during specified hours")
    print("• Critical alerts always break through immediately")
    print("• Queued alerts delivered when quiet hours end")
    print("• Perfect for overnight peace without missing emergencies")
    print()

    print("⏰ DEFAULT SETTINGS:")
    print("• Enabled: Yes")
    print("• Time Range: 10:00 PM - 8:00 AM")
    print("• Critical Override: Always active")
    print()

    print("🚨 ALERT BEHAVIOR:")
    print("• 🔴 Critical: Always notify (memory corruption, system failures)")
    print("• 🟡 Warning: Suppressed during quiet hours, queued for later")
    print("• 🟢 Info: Suppressed during quiet hours, queued for later")
    print()

    print("🎛️ CONFIGURATION:")
    print("• Open Athena Dashboard (Cmd+Shift+A)")
    print("• Go to Controls tab")
    print("• Toggle 'Enable Quiet Hours'")
    print("• Set custom start/end times")
    print()

    print("📱 MONITORING:")
    print("• Blue indicator shows when quiet hours are active")
    print("• Queued alerts count shows in controls panel")
    print("• Status description updates in real-time")
    print()

    print("🧪 TESTING:")
    print("• python3 demo_quiet_hours.py --test-normal")
    print("• python3 demo_quiet_hours.py --test-critical")
    print("• python3 demo_quiet_hours.py --simulate")
    print()

    print("💡 PRO TIPS:")
    print("• Critical alerts still wake you for real emergencies")
    print("• Review queued alerts each morning")
    print("• Adjust times based on your sleep schedule")
    print("• Use dashboard acknowledge button for bulk clearing")
    print()

def main():
    if len(sys.argv) < 2:
        show_quiet_hours_guide()
        return

    command = sys.argv[1]

    if command == "--status":
        check_quiet_hours_status()
    elif command == "--test-normal":
        test_normal_alert()
    elif command == "--test-critical":
        test_critical_alert()
    elif command == "--simulate":
        simulate_quiet_hours_cycle()
    else:
        print("❌ Unknown command")
        print("Available: --status, --test-normal, --test-critical, --simulate")
        print("Or run without arguments for the full guide")

if __name__ == "__main__":
    main()
