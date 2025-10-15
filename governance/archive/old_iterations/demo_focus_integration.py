#!/usr/bin/env python3
"""
Demo: Complete Focus Mode Integration
=====================================

Demonstrates the full iPhone Focus mode → Athena Dashboard integration.
Shows how Focus modes automatically control alert suppression.

Features:
- iPhone Focus mode detection and sync
- Automatic Athena quiet hours management
- Dashboard integration with live status
- Alert queuing and delivery when Focus ends

Usage:
    python3 demo_focus_integration.py --start      # Start full integration demo
    python3 demo_focus_integration.py --dashboard  # Show dashboard integration
    python3 demo_focus_integration.py --test-sync  # Test Focus ↔ Athena sync
    python3 demo_focus_integration.py --simulate   # Simulate Focus mode changes
"""

import time
import subprocess
import sys
import os

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

def check_services():
    """Check if required services are running"""
    print("🔍 Checking service status...")

    services_ok = True

    # Check Athena API
    try:
        import requests
        response = requests.get("http://localhost:8009/health", timeout=2)
        if response.status_code == 200:
            print("✅ Athena API: Running (port 8009)")
        else:
            print("❌ Athena API: Bad response")
            services_ok = False
    except:
        print("❌ Athena API: Not running - start with: python3 athena_local_api.py")
        services_ok = False

    # Check Focus watcher API
    try:
        response = requests.get("http://localhost:8010/status", timeout=2)
        if response.status_code == 200:
            print("✅ Focus Watcher API: Running (port 8010)")
        else:
            print("❌ Focus Watcher API: Bad response")
            services_ok = False
    except:
        print("❌ Focus Watcher API: Not running - start with: python3 focus_mode_watcher.py --start")
        services_ok = False

    # Check launchd services
    result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
    if 'com.athena.' in result.stdout:
        athena_services = [line for line in result.stdout.split('\n') if 'com.athena.' in line]
        print(f"✅ LaunchD: {len(athena_services)} Athena services loaded")
    else:
        print("⚠️ LaunchD: No Athena services loaded")

    return services_ok

def demonstrate_focus_sync():
    """Demonstrate Focus mode syncing with Athena"""
    print("\n🔄 Demonstrating Focus ↔ Athena Sync")
    print("=" * 40)

    try:
        import requests

        print("1️⃣ Checking current Athena quiet hours status...")
        response = requests.get("http://localhost:8009/quiet-hours", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Quiet Hours: {'Enabled' if data['enabled'] else 'Disabled'}")
            print(f"   Time Range: {data['start_hour']:02d}:00 - {data['end_hour']:02d}:00")
            print(f"   Currently Active: {'Yes' if data['is_quiet_hours'] else 'No'}")

        print("\n2️⃣ Simulating Focus mode activation...")
        # Simulate Focus mode becoming active
        sync_payload = {
            'enabled': True,
            'focus_mode': 'Sleep',
            'reason': 'User activated Sleep Focus on iPhone'
        }

        response = requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=5)
        if response.status_code == 200:
            print("   ✅ Focus mode 'Sleep' activated")
            print("   ✅ Athena quiet hours automatically enabled")

        print("\n3️⃣ Checking Focus watcher status...")
        response = requests.get("http://localhost:8010/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Focus Active: {data['focus_active']}")
            print(f"   Focus Mode: {data['focus_mode'] or 'None'}")
            print(f"   Monitoring: {data['monitoring']}")

        print("\n4️⃣ Testing alert queuing during 'quiet hours'...")
        # Send a test alert that should be queued
        alert_payload = {
            'id': f'test-focus-{int(time.time())}',
            'title': 'Test Alert During Focus',
            'message': 'This alert was sent while Focus mode was active and should be queued.',
            'severity': 'warning'
        }

        # Simulate the memory optimizer checking quiet hours
        import athena_memory_optimizer
        optimizer = athena_memory_optimizer.AthenaMemoryOptimizer()
        should_send = optimizer._should_send_alert_now(alert_payload)

        if not should_send:
            print("   ✅ Alert correctly queued (quiet hours active)")
        else:
            print("   ⚠️ Alert would be sent (quiet hours not active)")

        print("\n5️⃣ Simulating Focus mode deactivation...")
        sync_payload = {
            'enabled': False,
            'focus_mode': None,
            'reason': 'Sleep Focus ended automatically'
        }

        response = requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=5)
        if response.status_code == 200:
            print("   ✅ Focus mode deactivated")
            print("   ℹ️ Quiet hours remain enabled (manual control)")

        print("\n✅ Focus ↔ Athena sync demonstration complete!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure both APIs are running:")
        print("   Terminal 1: python3 athena_local_api.py")
        print("   Terminal 2: python3 focus_mode_watcher.py --start")

def show_dashboard_integration():
    """Show how the dashboard integrates with Focus modes"""
    print("\n🖥️ Dashboard Focus Integration")
    print("=" * 35)

    print("The Athena Dashboard (Cmd+Shift+A) now includes:")
    print()

    print("📱 Focus Tab Features:")
    print("• Real-time Focus mode status display")
    print("• Auto-sync toggle with Athena quiet hours")
    print("• Available Focus modes list")
    print("• Manual override buttons (Sleep/Work/Full Alert)")
    print("• Integration status indicators")
    print()

    print("🔄 Live Sync Behavior:")
    print("• iPhone Focus mode changes → Mac detection → Dashboard updates")
    print("• Dashboard shows current Focus status with visual indicators")
    print("• Quiet hours automatically enable/disable based on Focus")
    print("• Queued alerts counter updates in real-time")
    print()

    print("🎛️ Manual Controls:")
    print("• 'Sleep Mode' button → Sets quiet hours 22:00-08:00")
    print("• 'Work Mode' button → Sets quiet hours 09:00-17:00")
    print("• 'Full Alert' button → Disables quiet hours completely")
    print("• Auto-sync toggle → Links Focus modes to quiet hours")
    print()

    print("💡 Dashboard Indicators:")
    print("• Blue dot = Focus mode active (alerts suppressed)")
    print("• Green dot = Focus mode inactive (alerts enabled)")
    print("• Queued alerts count in controls panel")
    print("• Status text shows current suppression state")
    print()

def simulate_focus_lifecycle():
    """Simulate a complete Focus mode lifecycle"""
    print("\n🔄 Simulating Complete Focus Lifecycle")
    print("=" * 45)

    print("This simulation shows a typical daily Focus mode cycle:")
    print()

    try:
        import requests

        # Morning: No Focus
        print("🌅 08:00 - Morning: No Focus mode active")
        sync_payload = {'enabled': False, 'focus_mode': None, 'reason': 'Morning routine'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        print("   ✅ Alerts fully enabled")
        print()

        # Work Focus
        print("💼 09:00 - Work Focus activated")
        sync_payload = {'enabled': True, 'focus_mode': 'Work', 'reason': 'Commute to office'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        print("   🔔 Quiet hours enabled automatically")
        print("   📱 Non-critical alerts suppressed")
        print()

        # Lunch break
        print("🍽️ 12:00 - Lunch Break Focus")
        sync_payload = {'enabled': True, 'focus_mode': 'Lunch Break', 'reason': 'Lunch time'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        print("   🔔 Quiet hours remain active")
        print("   📱 Additional alerts queued")
        print()

        # Work ends
        print("🏠 17:00 - Work Focus ends")
        sync_payload = {'enabled': False, 'focus_mode': None, 'reason': 'End of workday'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        print("   ☀️ Focus mode inactive")
        print("   ℹ️ Quiet hours remain manual")
        print()

        # Sleep Focus
        print("😴 22:00 - Sleep Focus activated")
        sync_payload = {'enabled': True, 'focus_mode': 'Sleep', 'reason': 'Bedtime routine'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        print("   🌙 Quiet hours enabled for night")
        print("   📱 Only critical alerts will wake you")
        print()

        # Morning delivery
        print("🌅 08:00 - Sleep Focus ends, morning delivery")
        sync_payload = {'enabled': False, 'focus_mode': None, 'reason': 'Morning alarm'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        print("   📬 Queued alerts delivered to dashboard")
        print("   📊 Morning summary available for review")
        print()

        print("✅ Complete Focus lifecycle simulation complete!")

    except Exception as e:
        print(f"❌ Simulation failed: {e}")

def main():
    print("🎯 Athena Focus Mode Integration Demo")
    print("=" * 45)
    print()

    if len(sys.argv) < 2:
        print("Complete iPhone Focus mode → Athena Dashboard integration.")
        print()
        print("Commands:")
        print("  --start        Start full integration demo")
        print("  --dashboard    Show dashboard integration guide")
        print("  --test-sync    Test Focus ↔ Athena synchronization")
        print("  --simulate     Simulate daily Focus mode lifecycle")
        print()
        print("Features:")
        print("  • iPhone Focus mode detection and sync")
        print("  • Automatic Athena quiet hours management")
        print("  • Dashboard live status and controls")
        print("  • Alert queuing and morning delivery")
        print("  • Cross-device iCloud synchronization")
        print()
        print("Prerequisites:")
        print("  1. Athena API running: python3 athena_local_api.py")
        print("  2. Focus watcher running: python3 focus_mode_watcher.py --start")
        print("  3. NeuroForge app with Athena dashboard")
        print()
        print("Example: python3 demo_focus_integration.py --start")

        return

    command = sys.argv[1]

    if command == "--start":
        print("🚀 Starting Complete Focus Integration Demo")
        print()

        if not check_services():
            print("\n❌ Required services not running. Please start:")
            print("   Terminal 1: python3 athena_local_api.py")
            print("   Terminal 2: python3 focus_mode_watcher.py --start")
            return

        demonstrate_focus_sync()

    elif command == "--dashboard":
        show_dashboard_integration()

    elif command == "--test-sync":
        if check_services():
            demonstrate_focus_sync()
        else:
            print("❌ Services not running - cannot test sync")

    elif command == "--simulate":
        if check_services():
            simulate_focus_lifecycle()
        else:
            print("❌ Services not running - cannot simulate")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
