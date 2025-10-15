#!/usr/bin/env python3
"""
Additional macOS LaunchD Configurations for Athena
==================================================

Alternative cadences and configurations for different operational needs.

Usage:
    python3 macos_launchd_configs.py --list        # Show all available configs
    python3 macos_launchd_configs.py --generate [name]  # Generate specific plist
    python3 macos_launchd_configs.py --custom-cadence [minutes]  # Custom health check interval
"""

import argparse

class MacOSLaunchDConfigs:
    """Generate various launchd configurations for Athena"""

    def __init__(self):
        self.athena_dir = "/opt/ai-republic"

    def get_configs(self):
        """Return all available launchd configurations"""
        return {
            # Memory monitoring variants
            'memmonitor_10min': {
                'label': 'com.athena.memmonitor.10min',
                'description': 'Memory health monitoring every 10 minutes (testing/debugging)',
                'interval': 600,  # 10 minutes
                'run_at_load': True,
                'command': 'python3 athena_memory_optimizer.py --monitor'
            },
            'memmonitor_1hour': {
                'label': 'com.athena.memmonitor.1hour',
                'description': 'Memory health monitoring every hour (active monitoring)',
                'interval': 3600,  # 1 hour
                'run_at_load': True,
                'command': 'python3 athena_memory_optimizer.py --monitor'
            },
            'memmonitor_12hour': {
                'label': 'com.athena.memmonitor.12hour',
                'description': 'Memory health monitoring every 12 hours (minimal monitoring)',
                'interval': 43200,  # 12 hours
                'run_at_load': True,
                'command': 'python3 athena_memory_optimizer.py --monitor'
            },

            # Tribunal monitoring variants
            'tribunal_15min': {
                'label': 'com.athena.tribunal.15min',
                'description': 'Tribunal alert monitoring every 15 minutes (high frequency)',
                'interval': 900,  # 15 minutes
                'run_at_load': True,
                'command': 'python3 ai_republic_cli.py --monitor-tribunals'
            },
            'tribunal_1hour': {
                'label': 'com.athena.tribunal.1hour',
                'description': 'Tribunal alert monitoring every hour (standard)',
                'interval': 3600,  # 1 hour
                'run_at_load': True,
                'command': 'python3 ai_republic_cli.py --monitor-tribunals'
            },

            # Daily briefing variants
            'dailybrief_0800': {
                'label': 'com.athena.dailybrief.0800',
                'description': 'Daily status briefing at 08:00 (early morning)',
                'schedule': {'hour': 8, 'minute': 0},
                'command': 'python3 athena_scheduler.py --briefing'
            },
            'dailybrief_1700': {
                'label': 'com.athena.dailybrief.1700',
                'description': 'Daily status briefing at 17:00 (end of day)',
                'schedule': {'hour': 17, 'minute': 0},
                'command': 'python3 athena_scheduler.py --briefing'
            },

            # Weekly maintenance
            'weekly_maintenance': {
                'label': 'com.athena.weekly',
                'description': 'Weekly system maintenance on Sunday at 02:00',
                'schedule': {'weekday': 0, 'hour': 2, 'minute': 0},  # Sunday 2 AM
                'command': 'python3 athena_maintenance.py --full-system-check'
            },

            # Alert testing
            'alert_test_hourly': {
                'label': 'com.athena.alerttest',
                'description': 'Hourly alert system test (for testing notification channels)',
                'interval': 3600,  # 1 hour
                'run_at_load': False,  # Don't run on login
                'command': 'python3 test_iphone_alerts.py cascade'
            },

            # Voice monitoring variants
            'voice_low_sensitivity': {
                'label': 'com.athena.voice.lowsens',
                'description': 'Voice wake-word listener (low sensitivity, fewer false positives)',
                'run_at_load': True,
                'keep_alive': True,
                'command': 'python3 athena_voice_integration.py --mode continuous --set-sensitivity low'
            },
            'voice_high_sensitivity': {
                'label': 'com.athena.voice.highsens',
                'description': 'Voice wake-word listener (high sensitivity, more responsive)',
                'run_at_load': True,
                'keep_alive': True,
                'command': 'python3 athena_voice_integration.py --mode continuous --set-sensitivity high'
            },

            # System health dashboard
            'dashboard_updater': {
                'label': 'com.athena.dashboard',
                'description': 'Update system health dashboard every 30 minutes',
                'interval': 1800,  # 30 minutes
                'run_at_load': True,
                'command': 'python3 athena_dashboard.py --update'
            },

            # Log rotation
            'log_maintenance': {
                'label': 'com.athena.logs',
                'description': 'Log rotation and cleanup daily at 03:00',
                'schedule': {'hour': 3, 'minute': 0},
                'command': 'python3 athena_maintenance.py --rotate-logs'
            }
        }

    def generate_plist(self, config_name: str) -> str:
        """Generate plist content for a configuration"""
        configs = self.get_configs()
        if config_name not in configs:
            raise ValueError(f"Unknown configuration: {config_name}")

        config = configs[config_name]

        plist = '<?xml version="1.0" encoding="UTF-8"?>\n'
        plist += '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        plist += '<plist version="1.0">\n<dict>\n'

        # Basic metadata
        plist += f'\t<key>Label</key>\n\t<string>{config["label"]}</string>\n'
        plist += '\t<key>ProgramArguments</key>\n\t<array>\n\t\t<string>/bin/zsh</string>\n\t\t<string>-lc</string>\n'
        plist += f'\t\t<string>cd {self.athena_dir} && source .venv/bin/activate && {config["command"]}</string>\n\t</array>\n'

        # Scheduling
        if 'schedule' in config:
            sched = config['schedule']
            plist += '\t<key>StartCalendarInterval</key>\n\t<dict>\n'
            if 'weekday' in sched:
                plist += f'\t\t<key>Weekday</key>\n\t\t<integer>{sched["weekday"]}</integer>\n'
            if 'hour' in sched:
                plist += f'\t\t<key>Hour</key>\n\t\t<integer>{sched["hour"]}</integer>\n'
            if 'minute' in sched:
                plist += f'\t\t<key>Minute</key>\n\t\t<integer>{sched["minute"]}</integer>\n'
            plist += '\t</dict>\n'

        if 'interval' in config:
            plist += f'\t<key>StartInterval</key>\n\t<integer>{config["interval"]}</integer>\n'

        if config.get('run_at_load', False):
            plist += '\t<key>RunAtLoad</key>\n\t<true/>\n'

        if config.get('keep_alive', False):
            plist += '\t<key>KeepAlive</key>\n\t<true/>\n'

        # Logging
        service_name = config_name
        plist += f'\t<key>StandardOutPath</key>\n\t<string>/tmp/athena_{service_name}.out</string>\n'
        plist += f'\t<key>StandardErrorPath</key>\n\t<string>/tmp/athena_{service_name}.err</string>\n'

        plist += '</dict>\n</plist>\n'
        return plist

    def generate_custom_cadence(self, interval_minutes: int) -> str:
        """Generate a custom cadence plist for memory monitoring"""
        interval_seconds = interval_minutes * 60
        label = f'com.athena.memmonitor.custom.{interval_minutes}min'

        plist = '<?xml version="1.0" encoding="UTF-8"?>\n'
        plist += '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        plist += '<plist version="1.0">\n<dict>\n'

        plist += f'\t<key>Label</key>\n\t<string>{label}</string>\n'
        plist += '\t<key>ProgramArguments</key>\n\t<array>\n\t\t<string>/bin/zsh</string>\n\t\t<string>-lc</string>\n'
        plist += f'\t\t<string>cd {self.athena_dir} && source .venv/bin/activate && python3 athena_memory_optimizer.py --monitor</string>\n\t</array>\n'
        plist += f'\t<key>StartInterval</key>\n\t<integer>{interval_seconds}</integer>\n'
        plist += '\t<key>RunAtLoad</key>\n\t<true/>\n'
        plist += '\t<key>StandardOutPath</key>\n\t<string>/tmp/athena_memmonitor_custom.out</string>\n'
        plist += '\t<key>StandardErrorPath</key>\n\t<string>/tmp/athena_memmonitor_custom.err</string>\n'

        plist += '</dict>\n</plist>\n'
        return plist

    def list_configs(self):
        """List all available configurations"""
        configs = self.get_configs()

        print("🚀 Available Athena LaunchD Configurations")
        print("=" * 50)
        print()

        categories = {
            'Memory Monitoring': [k for k in configs.keys() if k.startswith('memmonitor')],
            'Tribunal Monitoring': [k for k in configs.keys() if k.startswith('tribunal')],
            'Daily Briefings': [k for k in configs.keys() if k.startswith('dailybrief')],
            'Voice & Audio': [k for k in configs.keys() if k.startswith('voice')],
            'Maintenance': [k for k in configs.keys() if 'maintenance' in k or 'logs' in k],
            'Testing & Dashboard': [k for k in configs.keys() if 'test' in k or 'dashboard' in k],
            'Weekly Tasks': [k for k in configs.keys() if 'weekly' in k]
        }

        for category, config_list in categories.items():
            if config_list:
                print(f"📁 {category}:")
                for config_name in config_list:
                    config = configs[config_name]
                    print(f"  • {config_name}: {config['description']}")
                print()

        print("💡 Generate any config:")
        print("  python3 macos_launchd_configs.py --generate memmonitor_10min")
        print()
        print("🔧 Custom cadence:")
        print("  python3 macos_launchd_configs.py --custom-cadence 15")

def main():
    parser = argparse.ArgumentParser(description='Additional macOS LaunchD Configurations')
    parser.add_argument('--list', action='store_true', help='List all available configurations')
    parser.add_argument('--generate', help='Generate plist for specific configuration')
    parser.add_argument('--custom-cadence', type=int, help='Generate custom memory monitor cadence (minutes)')
    parser.add_argument('--output', help='Output file for generated plist (default: stdout)')

    args = parser.parse_args()

    configs = MacOSLaunchDConfigs()

    if args.list:
        configs.list_configs()

    elif args.generate:
        try:
            plist_content = configs.generate_plist(args.generate)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(plist_content)
                print(f"✅ Generated plist: {args.output}")
            else:
                print(plist_content)
        except ValueError as e:
            print(f"❌ {e}")
            print("Use --list to see available configurations")

    elif args.custom_cadence:
        if args.custom_cadence < 1 or args.custom_cadence > 1440:  # Max 24 hours
            print("❌ Cadence must be between 1 and 1440 minutes (24 hours)")
            return

        plist_content = configs.generate_custom_cadence(args.custom_cadence)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(plist_content)
            print(f"✅ Generated custom {args.custom_cadence}-minute cadence plist: {args.output}")
        else:
            print(plist_content)

    else:
        print("🔧 Athena macOS LaunchD Configuration Generator")
        print("=" * 50)
        print()
        print("Generate launchd plist configurations for different cadences:")
        print()
        print("Commands:")
        print("  --list                    List all available configurations")
        print("  --generate [name]         Generate plist for specific config")
        print("  --custom-cadence [min]    Generate custom memory monitor cadence")
        print("  --output [file]           Save plist to file instead of stdout")
        print()
        print("Examples:")
        print("  python3 macos_launchd_configs.py --list")
        print("  python3 macos_launchd_configs.py --generate memmonitor_10min")
        print("  python3 macos_launchd_configs.py --custom-cadence 15 --output ~/Library/LaunchAgents/com.athena.memmonitor.15min.plist")

if __name__ == '__main__':
    main()
