#!/usr/bin/env python3
"""
macOS LaunchD Setup for Athena AI Republic
==========================================

Creates and manages launchd agents for Athena's autonomous operation.
Handles daily briefings, health monitoring, voice wake-word, and tribunal alerts.

Usage:
    python3 setup_macos_launchd.py --install-all     # Install all services
    python3 setup_macos_launchd.py --install-daily   # Daily briefing only
    python3 setup_macos_launchd.py --install-health  # Health monitor only
    python3 setup_macos_launchd.py --install-voice   # Voice wake-word only
    python3 setup_macos_launchd.py --status          # Check service status
    python3 setup_macos_launchd.py --logs            # Tail service logs
    python3 setup_macos_launchd.py --uninstall       # Remove all services
"""

import os
import subprocess
import argparse
from pathlib import Path
from typing import List

class MacOSLaunchDSetup:
    """Manage launchd agents for Athena's autonomous operation"""

    def __init__(self):
        self.launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        self.athena_dir = Path("/opt/ai-republic")  # Default; can be overridden
        self.services = {
            'dailybrief': {
                'label': 'com.athena.dailybrief',
                'description': 'Daily status briefing at 09:00',
                'filename': 'com.athena.dailybrief.plist',
                'schedule': {'hour': 9, 'minute': 0},
                'command': 'python3 athena_scheduler.py --briefing'
            },
            'memmonitor': {
                'label': 'com.athena.memmonitor',
                'description': 'Memory health monitoring every 6 hours',
                'filename': 'com.athena.memmonitor.plist',
                'interval': 21600,  # 6 hours
                'run_at_load': True,
                'command': 'python3 athena_memory_optimizer.py --monitor'
            },
            'tribunal': {
                'label': 'com.athena.tribunal',
                'description': 'Tribunal alert monitoring every 30 minutes',
                'filename': 'com.athena.tribunal.plist',
                'interval': 1800,  # 30 minutes
                'run_at_load': True,
                'command': 'python3 ai_republic_cli.py --monitor-tribunals'
            },
            'voice': {
                'label': 'com.athena.wakeword',
                'description': 'Voice wake-word listener (continuous)',
                'filename': 'com.athena.wakeword.plist',
                'run_at_load': True,
                'keep_alive': True,
                'command': 'python3 athena_voice_integration.py --mode continuous --set-sensitivity low'
            },
            'federation': {
                'label': 'com.athena.federation',
                'description': 'Federation status monitoring every 2 hours',
                'filename': 'com.athena.federation.plist',
                'interval': 7200,  # 2 hours
                'run_at_load': True,
                'command': 'python3 phase3_federation_api.py --monitor'
            }
        }

    def create_plist_content(self, service_key: str) -> str:
        """Generate plist content for a service"""
        service = self.services[service_key]

        plist = '<?xml version="1.0" encoding="UTF-8"?>\n'
        plist += '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        plist += '<plist version="1.0">\n<dict>\n'

        # Basic metadata
        plist += f'\t<key>Label</key>\n\t<string>{service["label"]}</string>\n'
        plist += '\t<key>ProgramArguments</key>\n\t<array>\n\t\t<string>/bin/zsh</string>\n\t\t<string>-lc</string>\n'
        plist += f'\t\t<string>cd {self.athena_dir} && source .venv/bin/activate && {service["command"]}</string>\n\t</array>\n'

        # Scheduling
        if 'schedule' in service:
            sched = service['schedule']
            plist += '\t<key>StartCalendarInterval</key>\n\t<dict>\n'
            if 'hour' in sched:
                plist += f'\t\t<key>Hour</key>\n\t\t<integer>{sched["hour"]}</integer>\n'
            if 'minute' in sched:
                plist += f'\t\t<key>Minute</key>\n\t\t<integer>{sched["minute"]}</integer>\n'
            plist += '\t</dict>\n'

        if 'interval' in service:
            plist += f'\t<key>StartInterval</key>\n\t<integer>{service["interval"]}</integer>\n'

        if service.get('run_at_load', False):
            plist += '\t<key>RunAtLoad</key>\n\t<true/>\n'

        if service.get('keep_alive', False):
            plist += '\t<key>KeepAlive</key>\n\t<true/>\n'

        # Logging
        service_name = service_key
        plist += f'\t<key>StandardOutPath</key>\n\t<string>/tmp/athena_{service_name}.out</string>\n'
        plist += f'\t<key>StandardErrorPath</key>\n\t<string>/tmp/athena_{service_name}.err</string>\n'

        plist += '</dict>\n</plist>\n'
        return plist

    def install_service(self, service_key: str) -> bool:
        """Install a launchd service"""
        if service_key not in self.services:
            print(f"❌ Unknown service: {service_key}")
            return False

        service = self.services[service_key]
        plist_path = self.launch_agents_dir / service['filename']

        try:
            # Create plist content
            plist_content = self.create_plist_content(service_key)

            # Write plist file
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(plist_path, 'w') as f:
                f.write(plist_content)

            # Unload existing service if running
            self._run_launchctl(['unload', str(plist_path)], check=False)

            # Load new service
            result = self._run_launchctl(['load', str(plist_path)])

            if result:
                print(f"✅ Installed: {service['description']}")
                print(f"   📄 {plist_path}")
                return True
            else:
                print(f"❌ Failed to load: {service['label']}")
                return False

        except Exception as e:
            print(f"❌ Install failed for {service_key}: {e}")
            return False

    def uninstall_service(self, service_key: str) -> bool:
        """Uninstall a launchd service"""
        if service_key not in self.services:
            print(f"❌ Unknown service: {service_key}")
            return False

        service = self.services[service_key]
        plist_path = self.launch_agents_dir / service['filename']

        try:
            # Unload service
            self._run_launchctl(['unload', str(plist_path)], check=False)

            # Remove plist file
            if plist_path.exists():
                plist_path.unlink()
                print(f"✅ Uninstalled: {service['label']}")
                return True
            else:
                print(f"ℹ️  Service not installed: {service['label']}")
                return True

        except Exception as e:
            print(f"❌ Uninstall failed for {service_key}: {e}")
            return False

    def install_all_services(self) -> bool:
        """Install all available services"""
        print("🚀 Installing all Athena launchd services...")
        print()

        success_count = 0
        for service_key in self.services.keys():
            if self.install_service(service_key):
                success_count += 1

        print()
        print(f"✅ Installed {success_count}/{len(self.services)} services")
        return success_count == len(self.services)

    def uninstall_all_services(self) -> bool:
        """Uninstall all services"""
        print("🛑 Uninstalling all Athena launchd services...")
        print()

        success_count = 0
        for service_key in self.services.keys():
            if self.uninstall_service(service_key):
                success_count += 1

        print()
        print(f"✅ Uninstalled {success_count}/{len(self.services)} services")
        return success_count == len(self.services)

    def check_service_status(self):
        """Check status of all Athena services"""
        print("📊 Athena LaunchD Service Status")
        print("=" * 40)
        print()

        for service_key, service in self.services.items():
            label = service['label']

            # Check if plist exists
            plist_path = self.launch_agents_dir / service['filename']
            plist_exists = plist_path.exists()

            # Check launchctl status
            result = self._run_launchctl(['list', label], capture_output=True, check=False)
            if result and 'PID' in str(result):
                status = "🟢 Running"
            elif result and 'Could not find service' not in str(result):
                status = "🟡 Loaded"
            else:
                status = "🔴 Not loaded"

            print(f"{status} {service['description']}")
            print(f"   Label: {label}")
            print(f"   Plist: {'✅' if plist_exists else '❌'} {plist_path}")
            print()

    def tail_service_logs(self):
        """Tail logs from all services"""
        print("📋 Tailing Athena Service Logs")
        print("Press Ctrl+C to stop")
        print()

        log_files = []
        for service in self.services.values():
            service_name = service['filename'].replace('com.athena.', '').replace('.plist', '')
            out_log = f"/tmp/athena_{service_name}.out"
            err_log = f"/tmp/athena_{service_name}.err"

            if os.path.exists(out_log):
                log_files.append(out_log)
            if os.path.exists(err_log):
                log_files.append(err_log)

        if not log_files:
            print("❌ No log files found. Services may not have run yet.")
            return

        # Use tail -f on all log files
        cmd = ['tail', '-f'] + log_files
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n✅ Stopped log tailing")

    def _run_launchctl(self, args: List[str], capture_output: bool = False, check: bool = True):
        """Run launchctl command"""
        try:
            if capture_output:
                result = subprocess.run(['launchctl'] + args, capture_output=True, text=True, check=check)
                return result.stdout if result.returncode == 0 else None
            else:
                result = subprocess.run(['launchctl'] + args, check=check)
                return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            print("❌ launchctl not found. Are you on macOS?")
            return False

def main():
    parser = argparse.ArgumentParser(description='macOS LaunchD Setup for Athena')
    parser.add_argument('--install-all', action='store_true', help='Install all launchd services')
    parser.add_argument('--install-daily', action='store_true', help='Install daily briefing service')
    parser.add_argument('--install-health', action='store_true', help='Install health monitoring service')
    parser.add_argument('--install-voice', action='store_true', help='Install voice wake-word service')
    parser.add_argument('--install-tribunal', action='store_true', help='Install tribunal monitoring service')
    parser.add_argument('--install-federation', action='store_true', help='Install federation monitoring service')
    parser.add_argument('--status', action='store_true', help='Check service status')
    parser.add_argument('--logs', action='store_true', help='Tail service logs')
    parser.add_argument('--uninstall', action='store_true', help='Uninstall all services')
    parser.add_argument('--athena-dir', help='Path to Athena directory (default: /opt/ai-republic)')

    args = parser.parse_args()

    setup = MacOSLaunchDSetup()
    if args.athena_dir:
        setup.athena_dir = Path(args.athena_dir)

    if args.install_all:
        setup.install_all_services()
    elif args.install_daily:
        setup.install_service('dailybrief')
    elif args.install_health:
        setup.install_service('memmonitor')
    elif args.install_voice:
        setup.install_service('voice')
    elif args.install_tribunal:
        setup.install_service('tribunal')
    elif args.install_federation:
        setup.install_service('federation')
    elif args.status:
        setup.check_service_status()
    elif args.logs:
        setup.tail_service_logs()
    elif args.uninstall:
        setup.uninstall_all_services()
    else:
        print("🤖 Athena macOS LaunchD Setup")
        print("=" * 35)
        print()
        print("Install launchd agents for autonomous Athena operation:")
        print()
        print("Quick install:")
        print("  python3 setup_macos_launchd.py --install-all")
        print()
        print("Individual services:")
        print("  --install-daily     Daily briefing at 09:00")
        print("  --install-health    Memory health every 6 hours")
        print("  --install-voice     Voice wake-word listener")
        print("  --install-tribunal  Tribunal alerts every 30 min")
        print("  --install-federation Federation status every 2 hours")
        print()
        print("Management:")
        print("  --status            Check service status")
        print("  --logs              Tail service logs")
        print("  --uninstall         Remove all services")
        print()
        print("Example:")
        print("  python3 setup_macos_launchd.py --install-all --athena-dir /path/to/athena")

if __name__ == '__main__':
    main()
