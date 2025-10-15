#!/usr/bin/env python3
"""
Athena Alert Priority Configuration
==================================

Configure alert priority levels for Athena's memory optimization system.

Usage:
    python3 athena_alert_config.py --set-priority all
    python3 athena_alert_config.py --set-priority critical_warning
    python3 athena_alert_config.py --set-priority critical_only

    python3 athena_alert_config.py --show-current
    python3 athena_alert_config.py --preview [priority_level]
"""

import json
import os
import sys
import argparse
from typing import Dict

# Add AI Republic paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

class AthenaAlertConfig:
    """Configure alert priority levels for Athena's memory system"""

    def __init__(self, config_file: str = None):
        # Use local config for development, system config for production
        if config_file is None:
            if os.path.exists('/opt/ai-republic'):
                config_file = '/opt/ai-republic/notification_config.json'
            else:
                config_file = './notification_config.json'
        self.config_file = config_file
        self.config = self._load_config()

        # Define alert priority levels
        self.priority_levels = {
            'all': {
                'name': 'All Alerts (Critical + Warning + Normal)',
                'description': 'Maximum visibility - get notified of all memory events',
                'alerts_enabled': ['critical_health', 'optimization_failed', 'corruption_detected',
                                 'performance_degraded', 'optimization_complete'],
                'channels': ['desktop', 'email', 'telegram', 'slack'],
                'recommended_for': 'Active monitoring, development environments'
            },
            'critical_warning': {
                'name': 'Critical + Warning Only',
                'description': 'Balanced approach - important issues plus optimization problems',
                'alerts_enabled': ['critical_health', 'optimization_failed', 'corruption_detected',
                                 'performance_degraded'],
                'channels': ['desktop', 'email', 'telegram', 'slack'],
                'recommended_for': 'Production environments, daily operations'
            },
            'critical_only': {
                'name': 'Critical Only',
                'description': 'Minimal alerts - only urgent issues requiring immediate action',
                'alerts_enabled': ['critical_health', 'corruption_detected'],
                'channels': ['desktop', 'email', 'telegram', 'slack'],
                'recommended_for': 'Low-maintenance setups, minimal notification preference'
            }
        }

    def _load_config(self) -> Dict:
        """Load notification configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                return self._get_default_config()
        else:
            print("Creating default notification configuration...")
            config = self._get_default_config()
            self._save_config(config)
            return config

    def _get_default_config(self) -> Dict:
        """Get default notification configuration"""
        return {
            "enabled_channels": ["desktop"],
            "alert_priority": "critical_warning",  # Default to balanced approach
            "alert_settings": {
                "critical_health": {"enabled": True, "channels": ["desktop", "email", "telegram", "slack"]},
                "optimization_failed": {"enabled": True, "channels": ["desktop", "email"]},
                "corruption_detected": {"enabled": True, "channels": ["desktop", "email", "telegram", "slack"]},
                "performance_degraded": {"enabled": True, "channels": ["desktop"]},
                "optimization_complete": {"enabled": False, "channels": ["desktop"]}
            },
            "email": {"enabled": False, "smtp_server": "", "username": "", "password": "", "from_email": "", "to_emails": []},
            "telegram": {"enabled": False, "bot_token": "", "chat_ids": []},
            "slack": {"enabled": False, "webhook_url": "", "channel": "#ai-republic"},
            "desktop": {"enabled": True, "urgency_levels": {"daily": "normal", "warning": "normal", "urgent": "critical"}},
            "retry_attempts": 3,
            "retry_delay": 5
        }

    def _save_config(self, config: Dict):
        """Save notification configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def set_alert_priority(self, priority_level: str) -> bool:
        """Set alert priority level and update configuration"""
        if priority_level not in self.priority_levels:
            print(f"❌ Invalid priority level: {priority_level}")
            print(f"Available levels: {', '.join(self.priority_levels.keys())}")
            return False

        # Update configuration
        self.config['alert_priority'] = priority_level

        # Update individual alert settings based on priority level
        level_config = self.priority_levels[priority_level]

        for alert_type in ['critical_health', 'optimization_failed', 'corruption_detected',
                          'performance_degraded', 'optimization_complete']:
            is_enabled = alert_type in level_config['alerts_enabled']
            if alert_type in self.config['alert_settings']:
                self.config['alert_settings'][alert_type]['enabled'] = is_enabled

        # Save configuration
        self._save_config(self.config)

        print(f"✅ Alert priority set to: {priority_level}")
        print(f"📝 {level_config['name']}")
        print(f"ℹ️  {level_config['description']}")
        print(f"🎯 Recommended for: {level_config['recommended_for']}")

        # Show which alerts will be enabled
        enabled_alerts = [k for k, v in self.config['alert_settings'].items() if v.get('enabled', False)]
        print(f"🔔 Alerts enabled: {', '.join(enabled_alerts)}")

        return True

    def show_current_config(self):
        """Show current alert configuration"""
        current_priority = self.config.get('alert_priority', 'unknown')
        enabled_channels = self.config.get('enabled_channels', [])

        print("🎛️  Current Athena Alert Configuration")
        print("=" * 50)

        if current_priority in self.priority_levels:
            level_config = self.priority_levels[current_priority]
            print(f"🔧 Priority Level: {current_priority}")
            print(f"📝 Name: {level_config['name']}")
            print(f"ℹ️  Description: {level_config['description']}")
        else:
            print(f"🔧 Priority Level: {current_priority} (custom)")

        print(f"\n📱 Enabled Channels: {', '.join(enabled_channels) if enabled_channels else 'None'}")

        print("\n🔔 Alert Settings:")
        for alert_type, settings in self.config.get('alert_settings', {}).items():
            enabled = settings.get('enabled', False)
            channels = settings.get('channels', [])
            status = "✅" if enabled else "❌"
            print(f"  {status} {alert_type}: {', '.join(channels) if channels else 'no channels'}")

    def preview_priority_level(self, priority_level: str):
        """Preview what a priority level would enable"""
        if priority_level not in self.priority_levels:
            print(f"❌ Invalid priority level: {priority_level}")
            return

        level_config = self.priority_levels[priority_level]

        print(f"🔍 Preview: {priority_level.upper()} Priority Level")
        print("=" * 50)
        print(f"📝 Name: {level_config['name']}")
        print(f"ℹ️  Description: {level_config['description']}")
        print(f"🎯 Recommended for: {level_config['recommended_for']}")

        print("\n🔔 Alerts that will be ENABLED:")
        for alert in level_config['alerts_enabled']:
            print(f"  ✅ {alert}")

        disabled_alerts = [a for a in ['critical_health', 'optimization_failed', 'corruption_detected',
                                     'performance_degraded', 'optimization_complete']
                          if a not in level_config['alerts_enabled']]
        if disabled_alerts:
            print("\n🔕 Alerts that will be DISABLED:")
            for alert in disabled_alerts:
                print(f"  ❌ {alert}")

        print(f"\n📱 Channels: {', '.join(level_config['channels'])}")

        # Estimate alert frequency
        self._estimate_alert_frequency(priority_level)

    def _estimate_alert_frequency(self, priority_level: str):
        """Estimate alert frequency for different priority levels"""
        frequency_estimates = {
            'all': {'daily': '2-5', 'weekly': '10-20', 'monthly': '40-80'},
            'critical_warning': {'daily': '0-2', 'weekly': '3-8', 'monthly': '10-30'},
            'critical_only': {'daily': '0-1', 'weekly': '0-3', 'monthly': '1-10'}
        }

        if priority_level in frequency_estimates:
            est = frequency_estimates[priority_level]
            print("\n📊 Estimated Alert Frequency:")
            print(f"  📅 Daily: ~{est['daily']} alerts")
            print(f"  📆 Weekly: ~{est['weekly']} alerts")
            print(f"  📊 Monthly: ~{est['monthly']} alerts")
            print("  💡 Most alerts occur during optimization weeks")

    def recommend_priority_level(self) -> str:
        """Recommend a priority level based on current setup"""
        # Check if this is a development/production environment
        # Check current channel configuration
        enabled_channels = len(self.config.get('enabled_channels', []))

        # Simple recommendation logic
        if enabled_channels >= 3:  # Multiple channels configured
            return 'critical_warning'  # Balanced for active monitoring
        elif enabled_channels == 1 and 'desktop' in self.config.get('enabled_channels', []):
            return 'critical_only'  # Minimal for basic desktop setup
        else:
            return 'all'  # Maximum visibility for comprehensive setup

def main():
    parser = argparse.ArgumentParser(description='Configure Athena Alert Priority Levels')
    parser.add_argument('--set-priority', choices=['all', 'critical_warning', 'critical_only'],
                       help='Set alert priority level')
    parser.add_argument('--show-current', action='store_true',
                       help='Show current alert configuration')
    parser.add_argument('--preview', choices=['all', 'critical_warning', 'critical_only'],
                       help='Preview what a priority level would enable')
    parser.add_argument('--recommend', action='store_true',
                       help='Get priority level recommendation')

    args = parser.parse_args()

    config = AthenaAlertConfig()

    if args.set_priority:
        success = config.set_alert_priority(args.set_priority)
        if success:
            print(f"\n✅ Configuration saved to: {config.config_file}")
            print("🔄 Restart any running Athena services to apply changes")

    elif args.show_current:
        config.show_current_config()

    elif args.preview:
        config.preview_priority_level(args.preview)

    elif args.recommend:
        recommendation = config.recommend_priority_level()
        print(f"🎯 Recommended Priority Level: {recommendation}")
        print()
        config.preview_priority_level(recommendation)
        print()
        print("💡 To apply this recommendation, run:")
        print(f"   python3 athena_alert_config.py --set-priority {recommendation}")

    else:
        print("🤖 Athena Alert Priority Configuration")
        print("=" * 50)
        print()
        print("Available commands:")
        print("  --set-priority [level]    Set alert priority (all/critical_warning/critical_only)")
        print("  --show-current           Show current configuration")
        print("  --preview [level]        Preview what a priority level enables")
        print("  --recommend              Get personalized recommendation")
        print()
        print("Quick examples:")
        print("  python3 athena_alert_config.py --set-priority critical_warning")
        print("  python3 athena_alert_config.py --preview all")
        print("  python3 athena_alert_config.py --recommend")

if __name__ == '__main__':
    main()
