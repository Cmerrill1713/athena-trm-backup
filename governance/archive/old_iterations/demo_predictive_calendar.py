#!/usr/bin/env python3
"""
Demo: Predictive Pre-Quieting with Calendar Integration
======================================================

Demonstrates Athena's ability to anticipate calendar events and enable quiet hours
before meetings start. Shows the complete predictive workflow from scheduling to execution.

Features:
- Predictive event detection (5-10 minute lead time)
- Pre-event quiet hours activation
- Dashboard predictive status updates
- Real-time countdown to events
- Smart event filtering and prioritization

Usage:
    python3 demo_predictive_calendar.py --start      # Start predictive demo
    python3 demo_predictive_calendar.py --simulate   # Simulate predictive scenario
    python3 demo_predictive_calendar.py --lead-time  # Test different lead times
    python3 demo_predictive_calendar.py --dashboard  # Show dashboard integration
"""

import time
import subprocess
import sys
import os
from datetime import datetime, timedelta

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

    return services_ok

def demonstrate_predictive_workflow():
    """Demonstrate the complete predictive workflow"""
    print("\n🔮 Demonstrating Predictive Pre-Quieting")
    print("=" * 50)

    try:
        import requests

        print("📅 Simulating calendar event scheduling...")
        print("   Meeting: 'Client Presentation' at 2:00 PM")
        print("   Current time: 1:55 PM (5 minutes before)")
        print()

        # Simulate predictive activation
        predictive_payload = {
            'type': 'predictive_activation',
            'event': {
                'title': 'Client Presentation',
                'start': (datetime.now() + timedelta(minutes=5)).isoformat(),
                'end': (datetime.now() + timedelta(minutes=65)).isoformat()
            },
            'reason': 'Upcoming Meeting: Client Presentation',
            'minutes_until': 5.0,
            'lead_time': 5
        }

        print("🔮 PREDICTIVE ACTIVATION:")
        print(f"   Event: {predictive_payload['event']['title']}")
        print(".1f"        print(f"   Reason: {predictive_payload['reason']}")
        print()

        # Send to Athena API
        response = requests.post("http://localhost:8009/calendar-predictive", json=predictive_payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Athena API received predictive activation")
            print(f"   Status: {data['status']}")
            print(f"   Lead time: {data['lead_time']} minutes")
            print()

        # Check predictive status
        print("📊 Checking predictive status...")
        response = requests.get("http://localhost:8009/calendar-predictive-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Predictive enabled: {data['predictive_enabled']}")
            print(f"   Lead time: {data['lead_time_minutes']} minutes")
            print(f"   Current prediction: {data.get('current_predictions', 'None')}")
            if data.get('minutes_until'):
                print(".1f"        print()

        # Simulate countdown
        print("⏰ Simulating countdown to event...")
        for minutes_left in [4.5, 3.0, 1.5, 0.5]:
            print(".1f"            time.sleep(0.5)

        print()
        print("🎯 Event starts now!")
        print("   Predictive quiet hours remain active during meeting")
        print()

        # Simulate meeting end
        print("🏁 Meeting ends (1 hour later)")
        end_payload = {'calendar_event': None}
        requests.post("http://localhost:8009/calendar-sync", json=end_payload, timeout=5)
        print("✅ Predictive quiet hours cleared")
        print("✅ Normal alert behavior restored")

        print("\n✅ Predictive workflow demonstration complete!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")

def simulate_predictive_scenarios():
    """Simulate various predictive scenarios"""
    print("\n🎭 Simulating Predictive Scenarios")
    print("=" * 40)

    scenarios = [
        {
            'name': 'Team Standup',
            'lead_time': 5,
            'description': 'Quick daily sync - predictive activation 5 min before'
        },
        {
            'name': 'Client Presentation',
            'lead_time': 10,
            'description': 'Important meeting - predictive activation 10 min before'
        },
        {
            'name': 'Deep Focus Session',
            'lead_time': 15,
            'description': 'Extended focus time - predictive activation 15 min before'
        },
        {
            'name': 'Lunch Break',
            'lead_time': 0,
            'description': 'Excluded event - no predictive activation'
        }
    ]

    try:
        import requests

        for scenario in scenarios:
            print(f"\n📅 Scenario: {scenario['name']}")
            print(f"   {scenario['description']}")

            if scenario['lead_time'] > 0:
                # Simulate predictive activation
                predictive_payload = {
                    'type': 'predictive_activation',
                    'event': {
                        'title': scenario['name'],
                        'start': (datetime.now() + timedelta(minutes=scenario['lead_time'])).isoformat()
                    },
                    'reason': f'Upcoming: {scenario["name"]}',
                    'minutes_until': float(scenario['lead_time']),
                    'lead_time': scenario['lead_time']
                }

                response = requests.post("http://localhost:8009/calendar-predictive", json=predictive_payload, timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ Predictive activated {scenario['lead_time']}min before")
                else:
                    print(f"   ❌ Predictive activation failed")
            else:
                print(f"   ℹ️ Event excluded from predictive activation")

            time.sleep(0.5)

        print("\n🎯 All scenarios simulated successfully!")

    except Exception as e:
        print(f"❌ Scenario simulation failed: {e}")

def test_lead_time_variations():
    """Test different predictive lead times"""
    print("\n⏱️ Testing Predictive Lead Time Variations")
    print("=" * 45)

    lead_times = [1, 3, 5, 10, 15]  # minutes

    try:
        import requests

        test_event = {
            'title': 'Test Meeting',
            'start': (datetime.now() + timedelta(minutes=10)).isoformat()
        }

        for lead_time in lead_times:
            print(f"\n🧪 Testing {lead_time}-minute lead time:")

            # Clear previous
            requests.post("http://localhost:8009/calendar-sync", json={'calendar_event': None}, timeout=2)

            # Simulate event within lead time window
            minutes_until = lead_time - 0.5  # Slightly within window

            predictive_payload = {
                'type': 'predictive_activation',
                'event': test_event,
                'reason': f'Test: {lead_time}min lead time',
                'minutes_until': minutes_until,
                'lead_time': lead_time
            }

            response = requests.post("http://localhost:8009/calendar-predictive", json=predictive_payload, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Activated at {minutes_until:.1f}min before event")
                print(f"   📊 Lead time: {lead_time}min")
            else:
                print(f"   ❌ Failed at {lead_time}min lead time")

            time.sleep(0.3)

        print("\n🎯 Lead time testing complete!")

    except Exception as e:
        print(f"❌ Lead time testing failed: {e}")

def show_dashboard_predictive_features():
    """Show dashboard predictive features"""
    print("\n🖥️ Dashboard Predictive Features")
    print("=" * 35)

    print("The Calendar tab now includes predictive indicators:")
    print()

    print("🎯 Predictive Status Section:")
    print("• 🟠 Orange crystal ball icon for predictive features")
    print("• Lead time display (default: 5 minutes)")
    print("• Current predictive event name")
    print("• Countdown timer to event start")
    print("• Visual indicators for active predictions")
    print()

    print("📊 Real-Time Updates:")
    print("• Predictive activation notifications")
    print("• Countdown updates every minute")
    print("• Event start/end status changes")
    print("• Integration with existing calendar sync")
    print()

    print("🎛️ Configuration Options:")
    print("• Lead time adjustment (1-15 minutes)")
    print("• Predictive enable/disable toggle")
    print("• Per-event type lead time settings")
    print("• Manual override for special cases")
    print()

    print("🔄 Status Indicators:")
    print("• 🔮 Orange dot = Predictive active")
    print("• ⏰ Countdown display = Time until event")
    print("• 📅 Event name = What's coming up")
    print("• ✅ Confirmation = Predictive activated successfully")
    print()

def main():
    print("🔮 Athena Predictive Calendar Demo")
    print("=" * 45)
    print()

    if len(sys.argv) < 2:
        print("Complete predictive pre-quieting with calendar integration.")
        print()
        print("Commands:")
        print("  --start        Start full predictive demo")
        print("  --simulate     Simulate various predictive scenarios")
        print("  --lead-time    Test different lead time configurations")
        print("  --dashboard    Show dashboard predictive features")
        print()
        print("Features:")
        print("  • Predictive event detection (5-10 minute lead time)")
        print("  • Pre-event quiet hours activation")
        print("  • Dashboard predictive status and countdown")
        print("  • Smart event filtering and prioritization")
        print("  • Configurable lead times per event type")
        print()
        print("Prerequisites:")
        print("  1. Athena API running: python3 athena_local_api.py")
        print("  2. Calendar monitor running: python3 calendar_monitor.py --start")
        print("  3. NeuroForge app with Athena dashboard")
        print()
        print("Example: python3 demo_predictive_calendar.py --start")

        return

    command = sys.argv[1]

    if command == "--start":
        print("🚀 Starting Complete Predictive Demo")
        print()

        if not check_services():
            print("\n❌ Required services not running. Please start:")
            print("   Terminal 1: python3 athena_local_api.py")
            print("   Terminal 2: python3 calendar_monitor.py --start")
            return

        demonstrate_predictive_workflow()

    elif command == "--simulate":
        if check_services():
            simulate_predictive_scenarios()
        else:
            print("❌ Services not running - cannot simulate scenarios")

    elif command == "--lead-time":
        if check_services():
            test_lead_time_variations()
        else:
            print("❌ Services not running - cannot test lead times")

    elif command == "--dashboard":
        show_dashboard_predictive_features()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
