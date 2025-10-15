#!/usr/bin/env python3
"""
Setup Cascade Alert Priority for Critical Notifications
======================================================

Configure critical alerts to go to Telegram first (instant mobile ping)
then to email/Slack (for follow-up), creating a prioritized notification cascade.

This ensures you get immediate mobile notifications for urgent issues while
still receiving comprehensive alerts via slower channels.

Usage:
    python3 setup_cascade_alerts.py --enable
    python3 setup_cascade_alerts.py --disable
    python3 setup_cascade_alerts.py --test
    python3 setup_cascade_alerts.py --status
"""

import json
import os
import sys
import argparse

# Add system paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

def load_config():
    """Load notification configuration"""
    config_paths = ['/opt/ai-republic/notification_config.json', './notification_config.json']
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f), path
            except Exception as e:
                print(f"Warning: Could not load {path}: {e}")
    return None, None

def save_config(config, path):
    """Save notification configuration"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def enable_cascade_alerts():
    """Enable cascade priority for critical alerts"""
    config, config_path = load_config()
    if not config:
        print("❌ No notification configuration found")
        return False

    # Add cascade priority settings
    config['cascade_priority'] = {
        'enabled': True,
        'urgent_channels_first': ['telegram', 'desktop'],  # Instant channels
        'delayed_channels': ['email', 'slack'],           # Follow-up channels
        'cascade_delay_seconds': 2,                       # Delay between cascades
        'description': 'Critical alerts go to Telegram first, then email'
    }

    # Update alert settings to use cascade for urgent alerts
    if 'alert_settings' not in config:
        config['alert_settings'] = {}

    for alert_type in ['critical_health', 'corruption_detected']:
        if alert_type in config['alert_settings']:
            config['alert_settings'][alert_type]['cascade_priority'] = True

    if save_config(config, config_path):
        print("✅ Cascade alert priority enabled!")
        print("🎯 Critical alerts will now:")
        print("  📱 Telegram/Desktop: Immediate notification")
        print("  📧 Email/Slack: 2-second delayed follow-up")
        print("  ⚡ Result: Instant mobile ping + comprehensive alert")
        return True
    return False

def disable_cascade_alerts():
    """Disable cascade priority (all channels simultaneous)"""
    config, config_path = load_config()
    if not config:
        print("❌ No notification configuration found")
        return False

    # Disable cascade priority
    if 'cascade_priority' in config:
        config['cascade_priority']['enabled'] = False

    # Remove cascade settings from individual alerts
    if 'alert_settings' in config:
        for alert_settings in config['alert_settings'].values():
            if 'cascade_priority' in alert_settings:
                alert_settings['cascade_priority'] = False

    if save_config(config, config_path):
        print("✅ Cascade alert priority disabled!")
        print("📤 All channels will now receive alerts simultaneously")
        return True
    return False

def test_cascade_alerts():
    """Test cascade alert delivery"""
    print("🧪 Testing cascade alert delivery...")
    print("This will send a test critical alert with cascade priority")
    print()

    try:
        from athena_notifications import AthenaNotifications
        notifications = AthenaNotifications()

        # Test cascade delivery
        print("📤 Sending cascade test alert...")
        results = notifications.send_notification(
            title="🚨 CASCADE TEST: Critical Alert Priority",
            message="""This is a test of cascade alert delivery!

If cascade priority is working:
📱 You should see this on Telegram/Desktop FIRST
📧 Then on Email/Slack 2 seconds later

This tests the critical alert prioritization system.""",
            priority="urgent",
            cascade_priority=True
        )

        print("📊 Delivery Results:")
        for channel, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {channel}")

        successful_channels = sum(1 for success in results.values() if success)
        print(f"\n🎯 Cascade test complete: {successful_channels}/{len(results)} channels delivered")

        if successful_channels > 0:
            print("💡 If you received Telegram/Desktop first, then Email/Slack - cascade is working!")
        else:
            print("⚠️ No channels delivered successfully - check your configuration")

    except Exception as e:
        print(f"❌ Test failed: {e}")

def show_cascade_status():
    """Show current cascade priority status"""
    config, config_path = load_config()
    if not config:
        print("❌ No notification configuration found")
        return

    print("🎛️ Cascade Alert Priority Status")
    print("=" * 40)

    cascade_enabled = config.get('cascade_priority', {}).get('enabled', False)

    if cascade_enabled:
        print("✅ CASCADE PRIORITY: ENABLED")
        print()
        print("📱 Instant Channels (Immediate):")
        instant = config['cascade_priority'].get('urgent_channels_first', [])
        for channel in instant:
            print(f"  ⚡ {channel}")
        print()
        print("📧 Follow-up Channels (2s delay):")
        delayed = config['cascade_priority'].get('delayed_channels', [])
        for channel in delayed:
            print(f"  ⏱️ {channel}")
        print()
        print("🎯 Critical alerts using cascade:")
        alert_settings = config.get('alert_settings', {})
        cascade_alerts = [k for k, v in alert_settings.items() if v.get('cascade_priority', False)]
        for alert in cascade_alerts:
            print(f"  🚨 {alert}")
    else:
        print("❌ CASCADE PRIORITY: DISABLED")
        print("📤 All channels receive alerts simultaneously")

    print()
    print(f"📁 Config file: {config_path}")

def main():
    parser = argparse.ArgumentParser(description='Configure Cascade Alert Priority')
    parser.add_argument('--enable', action='store_true',
                       help='Enable cascade priority for critical alerts')
    parser.add_argument('--disable', action='store_true',
                       help='Disable cascade priority (simultaneous delivery)')
    parser.add_argument('--test', action='store_true',
                       help='Test cascade alert delivery')
    parser.add_argument('--status', action='store_true',
                       help='Show current cascade priority status')

    args = parser.parse_args()

    if args.enable:
        enable_cascade_alerts()
    elif args.disable:
        disable_cascade_alerts()
    elif args.test:
        test_cascade_alerts()
    elif args.status:
        show_cascade_status()
    else:
        print("🤖 Cascade Alert Priority Configuration")
        print("=" * 50)
        print()
        print("Configure how critical alerts are delivered:")
        print("• CASCADE: Telegram first (instant), then email (follow-up)")
        print("• NORMAL: All channels simultaneously")
        print()
        print("Commands:")
        print("  --enable     Enable cascade priority for critical alerts")
        print("  --disable    Disable cascade (all channels simultaneous)")
        print("  --test       Test cascade delivery with sample alert")
        print("  --status     Show current cascade configuration")
        print()
        print("Example:")
        print("  python3 setup_cascade_alerts.py --enable")
        print("  python3 setup_cascade_alerts.py --test")

if __name__ == '__main__':
    main()
