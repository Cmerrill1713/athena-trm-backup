#!/usr/bin/env python3
"""
Demo: Behavioral Learning Integration
====================================

Demonstrates Athena's behavioral learning system that adapts alert timing
and preferences based on observed user behavior patterns.

Features:
- Safe observation-only mode to start
- Pattern analysis and recommendations
- Optional active adaptation
- Dashboard integration with learning insights
- Complete rollback capability

Usage:
    python3 demo_behavioral_learning.py --start         # Start observation mode
    python3 demo_behavioral_learning.py --analyze       # Analyze current patterns
    python3 demo_behavioral_learning.py --recommend     # Show recommendations
    python3 demo_behavioral_learning.py --simulate      # Simulate learning scenarios
    python3 demo_behavioral_learning.py --dashboard     # Show dashboard integration
"""

import time
import subprocess
import sys
import os
from datetime import datetime

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

    # Check Behavioral Learning
    try:
        result = subprocess.run(['pgrep', '-f', 'behavioral_learning'], capture_output=True)
        if result.returncode == 0:
            print("✅ Behavioral Learning: Running")
        else:
            print("❌ Behavioral Learning: Not running - start with: python3 behavioral_learning.py --start")
            services_ok = False
    except:
        print("❌ Behavioral Learning: Cannot check status")
        services_ok = False

    return services_ok

def demonstrate_observation_mode():
    """Demonstrate safe observation-only learning"""
    print("\n👁️ Behavioral Learning - Observation Mode")
    print("=" * 45)

    try:
        import requests

        print("1️⃣ Starting behavioral learning in observation mode...")
        print("   📊 System will collect data without changing behavior")
        print()

        # Check learning status
        response = requests.get("http://localhost:8009/behavioral-status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ Learning Status:")
            print(f"   Learning Enabled: {status['learning_enabled']}")
            print(f"   Adaptation Enabled: {status['adaptation_enabled']}")
            print(f"   Total Observations: {status['total_observations']}")
            print(".1f")
            print(f"   Patterns Learned: {sum(status['patterns_learned'].values())}")
            print()

        print("2️⃣ Recording sample behavioral data...")
        # Simulate recording some behavioral interactions
        test_data = [
            {"type": "alert_interaction", "alert_type": "warning", "action": "acted_on"},
            {"type": "alert_interaction", "alert_type": "info", "action": "ignored"},
            {"type": "quiet_hours_timing", "event_type": "meeting", "prep_time": 7, "effective": True},
            {"type": "quiet_hours_timing", "event_type": "presentation", "prep_time": 12, "effective": True}
        ]

        for data in test_data:
            response = requests.post("http://localhost:8009/behavioral-record", json=data, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Recorded: {data['type']}")
            time.sleep(0.5)

        print()
        print("3️⃣ Checking current recommendations...")
        response = requests.get("http://localhost:8009/behavioral-recommendations", timeout=5)
        if response.status_code == 200:
            recs = response.json()
            print(f"   Recommendations Available: {len(recs['recommendations'])}")
            print(f"   Message: {recs['message']}")
            print()

        print("✅ Observation mode demonstration complete!")
        print("💡 System is safely learning your patterns without making changes")

    except Exception as e:
        print(f"❌ Demo failed: {e}")

def simulate_learning_scenarios():
    """Simulate various learning scenarios and adaptations"""
    print("\n🎭 Simulating Behavioral Learning Scenarios")
    print("=" * 50)

    scenarios = [
        {
            'name': 'Lead Time Learning',
            'description': 'System learns you need more prep time before meetings',
            'pattern': 'Lead time increased from 5 to 8 minutes for meetings',
            'confidence': 0.85
        },
        {
            'name': 'Alert Preference Learning',
            'description': 'System learns you rarely respond to info alerts',
            'pattern': 'Info alert frequency reduced during work hours',
            'confidence': 0.78
        },
        {
            'name': 'Daily Rhythm Learning',
            'description': 'System learns your natural work/life balance',
            'pattern': 'Automatic quiet hours aligned with your schedule',
            'confidence': 0.92
        },
        {
            'name': 'Context Awareness',
            'description': 'System learns different behaviors for different situations',
            'pattern': 'Meeting alerts get priority, email alerts get filtered',
            'confidence': 0.71
        }
    ]

    print("These are the types of patterns Athena learns over time:")
    print()

    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   {scenario['description']}")
        print(".1f"        print(f"   Result: {scenario['pattern']}")
        print()

    print("🎯 Key Learning Principles:")
    print("• Takes 2+ weeks of normal usage to build meaningful patterns")
    print("• Requires 70%+ confidence before making recommendations")
    print("• Starts with observation-only mode for safety")
    print("• You can disable or reset learning anytime")
    print("• All data stays local on your device")

def demonstrate_adaptation_transition():
    """Demonstrate the transition from observation to adaptation"""
    print("\n🔄 Learning Mode Transition")
    print("=" * 35)

    try:
        import requests

        print("Phase 1: Observation Mode (Current)")
        print("   👁️ System watches your behavior")
        print("   📊 Collects data on preferences")
        print("   🤐 Makes no changes to alert timing")
        print()

        response = requests.post("http://localhost:8009/behavioral-disable-adaptation", timeout=5)
        if response.status_code == 200:
            print("   ✅ Currently in observation mode")
        print()

        print("Phase 2: Analysis & Recommendations")
        print("   🔍 System analyzes collected data")
        print("   🎯 Generates personalized recommendations")
        print("   📋 Shows suggestions but doesn't implement")
        print()

        # Check recommendations
        response = requests.get("http://localhost:8009/behavioral-recommendations", timeout=5)
        if response.status_code == 200:
            recs = response.json()
            print(f"   📋 Current recommendations: {len(recs['recommendations'])}")
        print()

        print("Phase 3: Active Adaptation (Optional)")
        print("   🤖 System automatically applies learned patterns")
        print("   ⚙️ Adjusts lead times, alert filtering, etc.")
        print("   📈 Continuously improves based on feedback")
        print()

        # Don't actually enable adaptation in demo
        print("   ⚠️ Adaptation not enabled in this demo")
        print("   💡 Use --enable-adaptation when ready for auto-adjustments")
        print()

        print("✅ Safe transition demonstration complete!")

    except Exception as e:
        print(f"❌ Transition demo failed: {e}")

def show_dashboard_integration():
    """Show how behavioral learning integrates with the dashboard"""
    print("\n🖥️ Dashboard Behavioral Learning Integration")
    print("=" * 50)

    print("The new 'Learning' tab provides complete behavioral insights:")
    print()

    print("🎯 Learning Status Section:")
    print("• 🧠 Brain icon showing learning mode (observation vs adaptation)")
    print("• Progress bar for learning confidence (0-100%)")
    print("• Total observations counter")
    print("• Patterns identified count")
    print("• Recommendations available indicator")
    print()

    print("📊 Learning Progress:")
    print("• Real-time confidence meter")
    print("• Pattern discovery progress")
    print("• Time until meaningful recommendations")
    print("• Learning effectiveness indicators")
    print()

    print("🎛️ Control Panel:")
    print("• Learning on/off toggle")
    print("• Adaptation enable/disable switch")
    print("• Manual pattern analysis button")
    print("• Data reset option")
    print("• Safety warnings and explanations")
    print()

    print("💡 Recommendation Display:")
    print("• Confidence levels for each suggestion")
    print("• Detailed explanations of learned patterns")
    print("• Implementation suggestions")
    print("• Accept/reject options (future feature)")
    print()

    print("🔒 Privacy & Safety:")
    print("• All data stays local on device")
    print("• No cloud sync or external sharing")
    print("• Complete data reset capability")
    print("• Easy rollback to manual control")
    print()

    print("📈 Learning Timeline:")
    print("• Week 1: Initial data collection")
    print("• Week 2: Basic pattern emergence")
    print("• Week 3+: Confident recommendations")
    print("• Ongoing: Continuous optimization")

def main():
    print("🧠 Athena Behavioral Learning Demo")
    print("=" * 45)
    print()

    if len(sys.argv) < 2:
        print("Complete behavioral learning system with safe observation mode.")
        print()
        print("Commands:")
        print("  --start        Start observation-only learning demo")
        print("  --analyze      Show pattern analysis capabilities")
        print("  --recommend    Demonstrate recommendation system")
        print("  --simulate     Show learning scenario examples")
        print("  --dashboard    Show dashboard integration")
        print("  --transition   Demonstrate observation → adaptation flow")
        print()
        print("Safety First:")
        print("  • Starts in observation-only mode")
        print("  • No behavior changes without explicit permission")
        print("  • All data stays local on your device")
        print("  • Complete rollback capability")
        print()
        print("Example: python3 demo_behavioral_learning.py --start")

        return

    command = sys.argv[1]

    if command == "--start":
        print("🚀 Starting Behavioral Learning Demo")
        print()

        if not check_services():
            print("\n❌ Required services not running. Please start:")
            print("   Terminal 1: python3 athena_local_api.py")
            print("   Terminal 2: python3 behavioral_learning.py --start")
            return

        demonstrate_observation_mode()

    elif command == "--analyze":
        if check_services():
            print("🔍 Pattern Analysis Demo")
            print("=" * 30)
            # Would integrate with actual analysis
            print("✅ Pattern analysis would run here")
            print("💡 In real usage, this analyzes your behavioral data")
        else:
            print("❌ Services not running - cannot analyze patterns")

    elif command == "--recommend":
        if check_services():
            print("🎯 Recommendations Demo")
            print("=" * 25)
            # Would show actual recommendations
            print("✅ Recommendations would display here")
            print("💡 In real usage, this shows personalized suggestions")
        else:
            print("❌ Services not running - cannot show recommendations")

    elif command == "--simulate":
        simulate_learning_scenarios()

    elif command == "--dashboard":
        show_dashboard_integration()

    elif command == "--transition":
        if check_services():
            demonstrate_adaptation_transition()
        else:
            print("❌ Services not running - cannot demonstrate transition")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
