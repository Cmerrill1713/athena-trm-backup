#!/usr/bin/env python3
"""
ATHENA COPILOT SCHEDULER
Automated scheduling system for AI Republic operational briefings

Integrates with system startup and cron for regular health monitoring.
"""

import time
import schedule
import threading
from datetime import datetime
import json
import os

from athena_ops_copilot import AthenaOpsCopilot

class AthenaScheduler:
    """Scheduler for automated Athena briefings"""

    def __init__(self):
        self.copilot = AthenaOpsCopilot()
        self.running = False
        self.schedule_config = self._load_schedule_config()

    def _load_schedule_config(self) -> dict:
        """Load scheduling configuration"""
        config_file = "/etc/ai-republic/athena_schedule.json"
        default_config = {
            "daily_briefing": "09:00",
            "startup_delay": 60,  # seconds after boot
            "health_check_interval": 3600,  # every hour
            "briefing_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "timezone": "UTC"
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            print(f"Warning: Could not load schedule config: {e}")

        return default_config

    def schedule_daily_briefing(self):
        """Schedule daily operational briefing"""
        briefing_time = self.schedule_config["daily_briefing"]
        briefing_days = self.schedule_config["briefing_days"]

        # Schedule for each day of the week
        days_map = {
            "monday": schedule.every().monday,
            "tuesday": schedule.every().tuesday,
            "wednesday": schedule.every().wednesday,
            "thursday": schedule.every().thursday,
            "friday": schedule.every().friday,
            "saturday": schedule.every().saturday,
            "sunday": schedule.every().sunday
        }

        for day_name in briefing_days:
            if day_name in days_map:
                days_map[day_name].at(briefing_time).do(self._deliver_daily_briefing)

        print(f"🤖 Daily briefings scheduled for {briefing_time} on {', '.join(briefing_days)}")

    def schedule_startup_briefing(self):
        """Schedule briefing after system startup"""
        delay = self.schedule_config["startup_delay"]

        def startup_job():
            time.sleep(delay)
            self._deliver_startup_briefing()

        # Run in background thread
        startup_thread = threading.Thread(target=startup_job, daemon=True)
        startup_thread.start()

        print(f"🤖 Startup briefing scheduled for {delay} seconds after launch")

    def schedule_health_checks(self):
        """Schedule regular health checks (without full briefings)"""
        interval = self.schedule_config["health_check_interval"]

        def health_check_job():
            try:
                status = self.copilot.perform_health_check()
                if status.get('overall_status') != 'HEALTHY':
                    # Only alert if not healthy
                    briefing = self.copilot.analyze_status(status)
                    if briefing.priority.value in ['urgent', 'critical']:
                        message = self.copilot.generate_briefing_message(briefing)
                        self.copilot._deliver_briefing(message, briefing, startup=False)
            except Exception as e:
                print(f"🤖 Health check error: {e}")

        schedule.every(interval).seconds.do(health_check_job)
        print(f"🤖 Health checks scheduled every {interval} seconds")

    def _deliver_daily_briefing(self):
        """Deliver scheduled daily briefing"""
        try:
            status = self.copilot.perform_health_check()
            if 'error' not in status:
                briefing = self.copilot.analyze_status(status)
                message = self.copilot.generate_briefing_message(briefing)
                self.copilot._deliver_briefing(message, briefing, startup=False)
                self._log_scheduled_briefing("daily", briefing)
        except Exception as e:
            print(f"🤖 Daily briefing error: {e}")

    def _deliver_startup_briefing(self):
        """Deliver system startup briefing"""
        try:
            status = self.copilot.perform_health_check()
            if 'error' not in status:
                briefing = self.copilot.analyze_status(status)
                message = self.copilot.generate_briefing_message(briefing)
                self.copilot._deliver_briefing(message, briefing, startup=True)
                self._log_scheduled_briefing("startup", briefing)
        except Exception as e:
            print(f"🤖 Startup briefing error: {e}")

    def _log_scheduled_briefing(self, briefing_type: str, briefing):
        """Log scheduled briefing delivery"""
        log_entry = {
            "type": "scheduled_briefing",
            "briefing_type": briefing_type,
            "timestamp": datetime.now().isoformat(),
            "priority": briefing.priority.value,
            "status": "delivered"
        }

        log_file = f"/var/log/ai-republic/athena_scheduler_{datetime.now().date()}.jsonl"
        try:
            with open(log_file, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
        except Exception as e:
            print(f"Warning: Could not log scheduled briefing: {e}")

    def start(self):
        """Start the scheduler"""
        self.running = True

        # Schedule all briefings
        self.schedule_daily_briefing()
        self.schedule_startup_briefing()
        self.schedule_health_checks()

        print("🤖 Athena Ops Co-Pilot scheduler started")
        print("Briefings will be delivered automatically according to schedule")

        # Keep running
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🤖 Scheduler stopped by user")
        except Exception as e:
            print(f"🤖 Scheduler error: {e}")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        print("🤖 Scheduler stopping...")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena Ops Co-Pilot Scheduler')
    parser.add_argument('--mode', choices=['start', 'test-daily', 'test-startup'],
                       default='start', help='Scheduler mode')
    parser.add_argument('--config', help='Path to schedule configuration file')

    args = parser.parse_args()

    if args.config:
        # Override config file path
        os.environ['ATHENA_SCHEDULE_CONFIG'] = args.config

    scheduler = AthenaScheduler()

    if args.mode == 'start':
        scheduler.start()
    elif args.mode == 'test-daily':
        print("🧪 Testing daily briefing...")
        scheduler._deliver_daily_briefing()
    elif args.mode == 'test-startup':
        print("🧪 Testing startup briefing...")
        scheduler._deliver_startup_briefing()

if __name__ == '__main__':
    main()
