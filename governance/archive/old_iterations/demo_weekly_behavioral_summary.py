#!/usr/bin/env python3
"""
Demo: Weekly Behavioral Learning Summary
========================================

Demonstrates Athena's weekly summary system that provides insights into
behavioral learning progress and personalized recommendations.

Features:
- Automated Friday delivery
- Comprehensive learning analytics
- Pattern discovery highlights
- Personalized recommendations
- Dashboard integration

Usage:
    python3 demo_weekly_behavioral_summary.py --generate    # Generate sample summary
    python3 demo_weekly_behavioral_summary.py --deliver     # Deliver summary report
    python3 demo_weekly_behavioral_summary.py --view        # View latest summary
    python3 demo_weekly_behavioral_summary.py --schedule    # Show scheduling setup
    python3 demo_weekly_behavioral_summary.py --full-demo   # Run complete weekly workflow
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

    return services_ok

def demonstrate_summary_generation():
    """Demonstrate weekly summary generation"""
    print("\n📊 Weekly Summary Generation")
    print("=" * 35)

    try:
        import requests

        print("Generating comprehensive behavioral learning summary...")
        print()

        # Generate summary via API
        response = requests.post("http://localhost:8009/behavioral-weekly-summary", timeout=10)
        if response.status_code == 200:
            summary_data = response.json()
            summary = summary_data['summary']

            print("✅ Summary Generated Successfully")
            print(f"   Week of: {summary['week_of']}")
            print(f"   Generated: {summary['timestamp'][:19]}")
            print()

            # Show key metrics
            status = summary['learning_status']
            progress = summary['weekly_progress']
            patterns = summary['patterns_discovered']

            print("📈 Key Metrics:")
            print(f"   • Learning Mode: {'Active Adaptation' if status['adaptation_enabled'] else 'Observation Only'}")
            print(f"   • Total Observations: {status['total_observations']}")
            print(".1f"            print(f"   • Patterns Discovered: {patterns['total_patterns']}")
            print(f"   • Weekly Observations: {progress['observations_this_week']}")
            print()

            # Show insights
            insights = summary['insights']
            if insights:
                print("💡 Key Insights:")
                for insight in insights:
                    print(f"   • {insight['title']}: {insight['description']}")
                print()

            # Show recommendations
            recommendations = summary['recommendations']
            if recommendations:
                print("🎯 Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec['type'].replace('_', ' ').title()}: {rec.get('recommended', 'Review needed')}")
                print()

            # Show next steps
            next_steps = summary['next_steps']
            if next_steps:
                print("🚀 Next Steps:")
                for step in next_steps:
                    print(f"   • {step['action']}: {step['description']}")
                print()

        else:
            print(f"❌ Summary generation failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demonstrate_summary_delivery():
    """Demonstrate summary delivery and formatting"""
    print("\n📧 Weekly Summary Delivery")
    print("=" * 30)

    try:
        # Use the behavioral_weekly_summary.py script directly
        result = subprocess.run([
            sys.executable, 'behavioral_weekly_summary.py', '--deliver'
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            print("✅ Weekly summary delivered successfully!")
            print()
            print("📋 Summary Report:")
            print("-" * 50)
            print(result.stdout)
        else:
            print(f"❌ Delivery failed: {result.stderr}")

    except Exception as e:
        print(f"❌ Delivery demo failed: {e}")

def demonstrate_imessage_delivery():
    """Demonstrate iMessage delivery of weekly summary"""
    print("\n📱 iMessage Delivery Demonstration")
    print("=" * 40)

    print("Testing iMessage delivery capability...")
    print()

    # Check environment variable
    recipient = os.environ.get('ATHENA_IMESSAGE_RECIPIENT')
    if not recipient:
        print("⚠️ iMessage recipient not configured")
        print("   Set environment variable: export ATHENA_IMESSAGE_RECIPIENT='+1234567890'")
        print("   Or your iMessage email address")
        print()
        print("For demo purposes, showing what would be sent:")
        print()

    # Simulate iMessage delivery
    try:
        result = subprocess.run([
            sys.executable, 'behavioral_weekly_summary.py', '--imessage'
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            print("✅ iMessage delivery test completed")
            print()
            print("📱 What gets sent via iMessage:")
            print("   🧠 Athena Weekly Summary")
            print("   📊 Confidence: 73% | 6 patterns found")
            print("   💡 You prefer 8 min prep before meetings")
            print("   🎯 2 recommendations ready")
            print("   📊 View full report in dashboard")
            print()
            print("💡 iMessage delivery:")
            print("   • Shortened version (fits in text message)")
            print("   • Key insights and metrics")
            print("   • Link to full dashboard report")
            print("   • Immediate mobile notification")
        else:
            print(f"❌ iMessage test failed: {result.stderr}")

    except Exception as e:
        print(f"❌ iMessage demo failed: {e}")

def demonstrate_notification_delivery():
    """Demonstrate macOS notification delivery"""
    print("\n🔔 macOS Notification Delivery Demonstration")
    print("=" * 50)

    print("Testing macOS desktop notification delivery...")
    print()

    try:
        result = subprocess.run([
            sys.executable, 'behavioral_weekly_summary.py', '--notification'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ macOS notification sent successfully")
            print()
            print("🔔 What appears in macOS Notification Center:")
            print("   Title: Athena Weekly Summary")
            print("   Subtitle: Week of 2024-01-15")
            print("   Body: Confidence: 73% | 6 patterns found")
            print("   App Icon: Athena/NeuroForge icon")
            print()
            print("💡 Notification features:")
            print("   • Immediate desktop alert")
            print("   • Click to open NeuroForge dashboard")
            print("   • Shows key metrics at a glance")
            print("   • Non-intrusive but informative")
        else:
            print(f"❌ Notification test failed: {result.stderr}")
            print("💡 Note: May require notification permissions for terminal")

    except Exception as e:
        print(f"❌ Notification demo failed: {e}")

def show_scheduling_setup():
    """Show how to set up automated weekly delivery"""
    print("\n📅 Automated Weekly Delivery Setup")
    print("=" * 40)

    print("To enable automatic Friday delivery, you can:")
    print()

    print("1️⃣ LaunchD Service (macOS):")
    print("   • Service file created: ~/Library/LaunchAgents/com.athena.behavioral-summary.plist")
    print("   • Runs every Friday at 5:00 PM")
    print("   • Delivers summary automatically")
    print()

    print("2️⃣ Manual Cron Job (Linux):")
    print("   # Add to crontab for Friday 5 PM delivery")
    print("   0 17 * * 5 /path/to/python3 behavioral_weekly_summary.py --deliver")
    print()

    print("3️⃣ Dashboard Integration:")
    print("   • 'Generate Summary' button in Learning tab")
    print("   • 'View Details' shows full weekly report")
    print("   • Automatic updates every Friday")
    print()

    print("4️⃣ Notification Options:")
    print("   • Desktop notification when summary is ready")
    print("   • Email delivery (configure SMTP settings)")
    print("   • Integration with existing alert channels")
    print()

    print("💡 Current Status:")
    print("   • LaunchD service configured for Fridays at 5 PM")
    print("   • Dashboard buttons available for manual generation")
    print("   • Summary data stored locally for privacy")

def demonstrate_full_weekly_workflow():
    """Demonstrate the complete weekly workflow"""
    print("\n🔄 Complete Weekly Behavioral Workflow")
    print("=" * 45)

    print("This demonstrates a full week of behavioral learning:")
    print()

    # Monday - Start of week
    print("📅 Monday - Week Begins")
    print("   • Behavioral learning continues in observation mode")
    print("   • System collects data on your alert interactions")
    print("   • Calendar events and timing preferences tracked")
    print()

    time.sleep(1)

    # Wednesday - Mid-week check
    print("📅 Wednesday - Mid-Week Progress")
    print("   • 89 new observations collected")
    print("   • Initial patterns emerging")
    print("   • Confidence level building to 65%")
    print()

    time.sleep(1)

    # Friday - Summary generation
    print("📅 Friday 5:00 PM - Weekly Summary Generation")
    print("   • System analyzes week's behavioral data")
    print("   • Patterns identified and confidence calculated")
    print("   • Recommendations generated based on findings")
    print("   • Summary delivered via configured channels")
    print()

    # Demonstrate actual generation
    demonstrate_summary_generation()

    print("📅 Next Week - Continued Learning")
    print("   • Fresh observation period begins")
    print("   • Previous patterns refined with new data")
    print("   • Confidence levels increase over time")
    print("   • More personalized recommendations become available")
    print()

    print("🎯 Workflow Benefits:")
    print("   • Regular insights into your behavioral patterns")
    print("   • Transparent learning progress tracking")
    print("   • Opportunity to review and approve changes")
    print("   • Safe progression from observation to adaptation")

def show_dashboard_integration():
    """Show how weekly summaries integrate with the dashboard"""
    print("\n🖥️ Dashboard Weekly Summary Integration")
    print("=" * 45)

    print("The Learning tab includes comprehensive weekly summary features:")
    print()

    print("🎯 Weekly Summary Section:")
    print("• 📅 Last summary date and confidence level")
    print("• 📊 Learning progress summary")
    print("• 💡 Key insight highlight")
    print("• 📈 Metrics overview (observations, patterns, recommendations)")
    print()

    print("🛠️ Summary Controls:")
    print("• 'Generate Summary' - Create new summary manually")
    print("• 'View Details' - Full detailed weekly report")
    print("• Automatic updates every Friday")
    print("• Progress tracking across weeks")
    print()

    print("📊 Summary Detail View:")
    print("• Key metrics cards (observations, patterns, recommendations)")
    print("• Confidence level progress bar")
    print("• Detailed insights and recommendations preview")
    print("• Actionable next steps")
    print("• Historical comparison data")
    print()

    print("🔄 Weekly Rhythm:")
    print("• Monday: Fresh observation period begins")
    print("• Wednesday: Progress check available")
    print("• Friday: Comprehensive summary delivered")
    print("• Ongoing: Real-time learning status updates")
    print()

    print("💡 Dashboard Benefits:")
    print("• Visual representation of learning progress")
    print("• Easy access to detailed insights")
    print("• Manual control over summary generation")
    print("• Integration with existing learning controls")

def main():
    print("📅 Athena Weekly Behavioral Summary Demo")
    print("=" * 50)
    print()

    if len(sys.argv) < 2:
        print("Complete weekly behavioral learning summary system.")
        print()
        print("Commands:")
        print("  --generate     Generate and display sample weekly summary")
        print("  --deliver      Deliver weekly summary report")
        print("  --imessage     Test iMessage delivery")
        print("  --notification Test macOS notification delivery")
        print("  --view         View latest summary details")
        print("  --schedule     Show automated delivery setup")
        print("  --full-demo    Demonstrate complete weekly workflow")
        print("  --dashboard    Show dashboard integration")
        print()
        print("Delivery Channels:")
        print("  • Console: Terminal output")
        print("  • Dashboard: NeuroForge app")
        print("  • iMessage: Text message delivery")
        print("  • Notification: macOS desktop alerts")
        print()
        print("Features:")
        print("  • Automated Friday delivery")
        print("  • Comprehensive learning analytics")
        print("  • Pattern discovery highlights")
        print("  • Personalized recommendations")
        print("  • Multi-channel delivery")
        print("  • Dashboard integration")
        print()
        print("Example: python3 demo_weekly_behavioral_summary.py --generate")

        return

    command = sys.argv[1]

    if command == "--generate":
        print("🚀 Generating Weekly Behavioral Summary Demo")
        print()

        if not check_services():
            print("\n❌ Required services not running. Please start:")
            print("   Terminal 1: python3 athena_local_api.py")
            return

        demonstrate_summary_generation()

    elif command == "--deliver":
        if check_services():
            demonstrate_summary_delivery()
        else:
            print("❌ Services not running - cannot deliver summary")

    elif command == "--imessage":
        if check_services():
            demonstrate_imessage_delivery()
        else:
            print("❌ Services not running - cannot test iMessage delivery")

    elif command == "--notification":
        if check_services():
            demonstrate_notification_delivery()
        else:
            print("❌ Services not running - cannot test notification delivery")

    elif command == "--view":
        print("👁️ View Latest Summary Demo")
        print("=" * 30)
        print("In a real implementation, this would show the latest stored summary.")
        print("For demo purposes, run --generate to see a fresh summary.")

    elif command == "--schedule":
        show_scheduling_setup()

    elif command == "--full-demo":
        if check_services():
            demonstrate_full_weekly_workflow()
        else:
            print("❌ Services not running - cannot run full demo")

    elif command == "--dashboard":
        show_dashboard_integration()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
