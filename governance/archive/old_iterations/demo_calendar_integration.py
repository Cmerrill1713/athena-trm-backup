#!/usr/bin/env python3
"""
Demo: Complete Calendar Integration with Athena
===============================================

Demonstrates calendar-driven quiet hours working alongside Focus mode integration.
Shows how meetings and focus time automatically control alert suppression.

Features:
- Calendar event monitoring and detection
- Automatic quiet hours during meetings
- Integration with existing Focus mode system
- Dashboard controls for calendar sync
- Real-time event status and upcoming events

Usage:
    python3 demo_calendar_integration.py --start     # Start full integration demo
    python3 demo_calendar_integration.py --calendar  # Show calendar integration
    python3 demo_calendar_integration.py --meeting   # Simulate meeting scenario
    python3 demo_calendar_integration.py --focus     # Simulate focus time scenario
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

    # Check Focus watcher
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

    # Check Calendar monitor
    try:
        result = subprocess.run(['pgrep', '-f', 'calendar_monitor'], capture_output=True)
        if result.returncode == 0:
            print("✅ Calendar Monitor: Running")
        else:
            print("❌ Calendar Monitor: Not running - start with: python3 calendar_monitor.py --start")
            services_ok = False
    except:
        print("❌ Calendar Monitor: Cannot check status")
        services_ok = False

    # Check launchd services
    result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
    athena_services = [line for line in result.stdout.split('\n') if 'com.athena.' in line]
    print(f"✅ LaunchD: {len(athena_services)} Athena services loaded")

    return services_ok

def demonstrate_calendar_sync():
    """Demonstrate Calendar event syncing with Athena"""
    print("\n📅 Demonstrating Calendar ↔ Athena Sync")
    print("=" * 45)

    try:
        import requests

        print("1️⃣ Checking current Athena calendar status...")
        response = requests.get("http://localhost:8009/calendar-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Calendar Event: {data['calendar_event'] or 'None'}")
            print(f"   Focus Mode: {data['focus_mode'] or 'None'}")
            print(f"   Quiet Hours: {'Active' if data['is_quiet_hours'] else 'Inactive'}")

        print("\n2️⃣ Simulating meeting start...")
        # Simulate calendar event starting
        sync_payload = {
            'calendar_event': 'Team Standup Meeting',
            'source': 'demo'
        }

        response = requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=5)
        if response.status_code == 200:
            print("   ✅ Calendar event 'Team Standup' detected")
            print("   ✅ Athena quiet hours automatically enabled")

        print("\n3️⃣ Checking calendar monitor status...")
        # Test calendar monitor directly
        result = subprocess.run([sys.executable, 'calendar_monitor.py', '--status'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Calendar monitor operational")
            # Print last few lines of status output
            lines = result.stdout.strip().split('\n')[-3:]
            for line in lines:
                print(f"   {line}")

        print("\n4️⃣ Simulating meeting end...")
        sync_payload = {
            'calendar_event': None,  # Meeting ended
            'source': 'demo'
        }

        response = requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=5)
        if response.status_code == 200:
            print("   ✅ Meeting ended")
            print("   ☀️ Athena quiet hours remain manual")

        print("\n✅ Calendar ↔ Athena sync demonstration complete!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure APIs are running:")
        print("   Terminal 1: python3 athena_local_api.py")
        print("   Terminal 2: python3 focus_mode_watcher.py --start")
        print("   Terminal 3: python3 calendar_monitor.py --start")

def show_focus_calendar_integration():
    """Show how Focus and Calendar work together"""
    print("\n🔄 Focus + Calendar Integration")
    print("=" * 40)

    print("Athena now intelligently combines multiple signals:")
    print()

    print("🎯 Integration Logic:")
    print("IF Focus Mode Active OR Calendar Event Active THEN")
    print("   → Enable quiet hours")
    print("   → Suppress non-critical alerts")
    print("   → Critical alerts still break through")
    print("ELSE")
    print("   → Normal alert behavior")
    print("   → Manual quiet hours control")
    print()

    print("📊 Real-World Scenarios:")
    print()

    print("Scenario 1: Focus Mode During Meeting")
    print("→ iPhone: Sleep Focus activated")
    print("→ Mac: Focus detected, quiet hours enabled")
    print("→ Calendar: Team meeting starts")
    print("→ Result: Double confirmation of quiet hours")
    print()

    print("Scenario 2: Calendar Event Without Focus")
    print("→ Calendar: 'Client Presentation' starts")
    print("→ Athena: Auto-detects meeting, enables quiet hours")
    print("→ Result: Automatic meeting mode")
    print()

    print("Scenario 3: Focus Without Calendar")
    print("→ iPhone: Work Focus activated (no meeting)")
    print("→ Mac: Focus detected, quiet hours enabled")
    print("→ Result: Manual focus time protection")
    print()

    print("Scenario 4: Normal Operation")
    print("→ No Focus, no calendar events")
    print("→ Athena: Normal alert delivery")
    print("→ Result: Full awareness of all alerts")
    print()

    print("🎛️ Dashboard Integration:")
    print("• Focus Tab: iPhone Focus mode status")
    print("• Calendar Tab: macOS Calendar event status")
    print("• Combined Status: Shows active quiet hours source")
    print("• Manual Override: Force modes when needed")

def simulate_workday_scenario():
    """Simulate a complete workday with calendar and focus events"""
    print("\n💼 Simulating Complete Workday Scenario")
    print("=" * 50)

    try:
        import requests

        print("🌅 8:00 AM - Morning routine, no Focus/calendar events")
        sync_payload = {'calendar_event': None}
        requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=2)
        print("   ☀️ Normal alert delivery")
        print()

        time.sleep(1)

        print("💼 9:00 AM - Work Focus activated for focused work")
        sync_payload = {'enabled': True, 'focus_mode': 'Work', 'reason': 'Start of workday'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        print("   🔔 Quiet hours enabled via Focus mode")
        print()

        time.sleep(1)

        print("👥 10:00 AM - Team standup meeting starts")
        sync_payload = {'calendar_event': 'Team Standup Meeting'}
        requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=2)
        print("   🔔 Quiet hours remain active (meeting)")
        print("   📱 Non-critical alerts suppressed")
        print()

        time.sleep(1)

        print("🏁 10:15 AM - Standup ends, back to focused work")
        sync_payload = {'calendar_event': None}
        requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=2)
        print("   🔔 Quiet hours remain active (Work Focus still on)")
        print()

        time.sleep(1)

        print("🍽️ 12:00 PM - Lunch break (excluded from auto-quiet)")
        sync_payload = {'calendar_event': 'Lunch Break'}
        requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=2)
        print("   ☀️ Lunch break detected - no quiet hours change")
        print("   🔔 Alerts remain normal during break")
        print()

        time.sleep(1)

        print("🎯 1:00 PM - Deep focus session starts")
        sync_payload = {'calendar_event': 'Deep Focus Session'}
        requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=2)
        print("   🔔 Quiet hours enabled for focus time")
        print()

        time.sleep(1)

        print("📞 2:00 PM - Client presentation starts")
        sync_payload = {'calendar_event': 'Client Presentation'}
        requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=2)
        print("   🔔 Quiet hours remain active (presentation)")
        print()

        time.sleep(1)

        print("🏠 5:00 PM - Work Focus ends, back to normal")
        sync_payload = {'enabled': False, 'focus_mode': None, 'reason': 'End of workday'}
        requests.post("http://localhost:8009/focus-sync", json=sync_payload, timeout=2)
        sync_payload = {'calendar_event': None}
        requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=2)
        print("   ☀️ Focus and calendar events cleared")
        print("   🔔 Normal alert delivery restored")
        print()

        print("✅ Complete workday scenario simulation complete!")
        print()
        print("💡 Key Insights:")
        print("• Multiple signals (Focus + Calendar) work together")
        print("• Exclusions (lunch) prevent false positives")
        print("• Critical alerts always break through")
        print("• Manual override always available")

    except Exception as e:
        print(f"❌ Scenario simulation failed: {e}")

def main():
    print("📅 Athena Calendar Integration Demo")
    print("=" * 45)
    print()

    if len(sys.argv) < 2:
        print("Complete calendar-driven quiet hours with Focus integration.")
        print()
        print("Commands:")
        print("  --start      Start full integration demo")
        print("  --calendar   Show calendar integration guide")
        print("  --meeting    Simulate meeting scenario")
        print("  --focus      Simulate focus time scenario")
        print("  --workday    Simulate complete workday")
        print()
        print("Features:")
        print("  • Calendar event monitoring and detection")
        print("  • Automatic quiet hours during meetings")
        print("  • Integration with Focus mode system")
        print("  • Dashboard controls and status")
        print("  • Smart event filtering and exclusions")
        print()
        print("Prerequisites:")
        print("  1. Athena API running: python3 athena_local_api.py")
        print("  2. Focus watcher running: python3 focus_mode_watcher.py --start")
        print("  3. Calendar monitor running: python3 calendar_monitor.py --start")
        print("  4. NeuroForge app with Athena dashboard")
        print()
        print("Example: python3 demo_calendar_integration.py --start")

        return

    command = sys.argv[1]

    if command == "--start":
        print("🚀 Starting Complete Calendar Integration Demo")
        print()

        if not check_services():
            print("\n❌ Required services not running. Please start:")
            print("   Terminal 1: python3 athena_local_api.py")
            print("   Terminal 2: python3 focus_mode_watcher.py --start")
            print("   Terminal 3: python3 calendar_monitor.py --start")
            return

        demonstrate_calendar_sync()

    elif command == "--calendar":
        show_focus_calendar_integration()

    elif command == "--meeting":
        if check_services():
            print("\n👥 Simulating Meeting Scenario")
            print("=" * 35)
            demonstrate_calendar_sync()
        else:
            print("❌ Services not running - cannot simulate meeting")

    elif command == "--focus":
        if check_services():
            print("\n🎯 Simulating Focus Time Scenario")
            print("=" * 35)
            # Similar to meeting but with focus event
            try:
                import requests
                print("Starting focus session...")
                sync_payload = {'calendar_event': 'Deep Focus Session'}
                response = requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=5)
                if response.status_code == 200:
                    print("✅ Focus session started - quiet hours enabled")
                time.sleep(2)
                sync_payload = {'calendar_event': None}
                requests.post("http://localhost:8009/calendar-sync", json=sync_payload, timeout=5)
                print("✅ Focus session ended")
            except Exception as e:
                print(f"❌ Focus simulation failed: {e}")
        else:
            print("❌ Services not running - cannot simulate focus time")

    elif command == "--workday":
        if check_services():
            simulate_workday_scenario()
        else:
            print("❌ Services not running - cannot simulate workday")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
