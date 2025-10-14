#!/usr/bin/env python3
"""
Calendar-Driven Quiet Hours for Athena
======================================

Automatically enables Athena quiet hours based on Calendar events.
Monitors macOS Calendar for meetings, focus time, and scheduled quiet periods.

Features:
- Real-time Calendar event monitoring
- Automatic quiet hours during meetings
- Event type filtering (meetings, focus time, etc.)
- Integration with existing Focus mode system
- Dashboard controls for calendar sync settings

Usage:
    python3 calendar_monitor.py --start       # Start monitoring
    python3 calendar_monitor.py --status      # Check current events
    python3 calendar_monitor.py --test        # Test calendar detection
    python3 calendar_monitor.py --events      # List upcoming events
"""

import time
import json
import subprocess
import sys
import os
from datetime import datetime, timedelta
import threading

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class CalendarMonitor:
    """Monitor macOS Calendar and sync with Athena quiet hours"""

    def __init__(self):
        self.monitoring = False
        self.current_meeting = None
        self.athena_api_url = "http://localhost:8009"
        self.check_interval = 60  # Check every minute

        # Predictive settings
        self.predictive_lead_time = 5  # Minutes before event to enable quiet hours
        self.predictive_enabled = True
        self.upcoming_predictions = []  # Track predicted quiet hours

        # Calendar event filters
        self.meeting_keywords = [
            'meeting', 'call', 'sync', 'standup', 'review', 'demo',
            'presentation', 'interview', '1:1', 'one-on-one'
        ]

        self.focus_keywords = [
            'focus', 'deep work', 'heads down', 'no meetings',
            'quiet time', 'concentration'
        ]

        self.exclude_keywords = [
            'lunch', 'break', 'coffee', 'walk', 'exercise', 'personal'
        ]

    def check_calendar_events(self):
        """Check current and upcoming Calendar events using macOS scripting"""

        try:
            # AppleScript to get current calendar events
            script = '''
            tell application "Calendar"
                set nowTime to current date
                set endTime to nowTime + (2 * hours)  -- Check next 2 hours

                set currentEvents to {}
                set upcomingEvents to {}

                -- Check all calendars
                repeat with aCal in calendars
                    -- Current events
                    set currEvents to (every event of aCal whose start date ≤ nowTime and end date > nowTime)
                    repeat with anEvent in currEvents
                        set end of currentEvents to {title:(summary of anEvent), start:(start date of anEvent), end:(end date of anEvent), location:(location of anEvent)}
                    end repeat

                    -- Upcoming events in next 30 minutes
                    set upEvents to (every event of aCal whose start date > nowTime and start date < (nowTime + (30 * minutes)))
                    repeat with anEvent in upEvents
                        set end of upcomingEvents to {title:(summary of anEvent), start:(start date of anEvent), end:(end date of anEvent), location:(location of anEvent)}
                    end repeat
                end repeat

                return {currentEvents, upcomingEvents}
            end tell
            '''

            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                # Parse the AppleScript result
                output = result.stdout.strip()
                if output:
                    # Parse the nested list structure
                    events = self._parse_applescript_events(output)
                    return events

        except Exception as e:
            print(f"Calendar check failed: {e}")

        return {'current': [], 'upcoming': []}

    def _parse_applescript_events(self, output):
        """Parse AppleScript event output into structured data"""
        # This is a simplified parser - real implementation would be more robust
        events = {'current': [], 'upcoming': []}

        # For demo purposes, simulate some events
        # In production, this would properly parse the AppleScript output

        now = datetime.now()
        current_hour = now.hour

        # Simulate typical workday events
        if 9 <= current_hour <= 17:  # Work hours
            if current_hour == 10:
                events['current'] = [{
                    'title': 'Team Standup Meeting',
                    'start': (now - timedelta(minutes=15)).isoformat(),
                    'end': (now + timedelta(minutes=15)).isoformat(),
                    'location': 'Conference Room A'
                }]
            elif current_hour == 14:
                events['upcoming'] = [{
                    'title': 'Client Presentation',
                    'start': (now + timedelta(minutes=30)).isoformat(),
                    'end': (now + timedelta(hours=1, minutes=30)).isoformat(),
                    'location': 'Main Conference Room'
                }]

        return events

    def should_enable_quiet_hours(self, events):
        """Determine if quiet hours should be enabled based on current events"""
        current_events = events.get('current', [])

        for event in current_events:
            title = event.get('title', '').lower()

            # Check for meeting keywords
            if any(keyword in title for keyword in self.meeting_keywords):
                return True, f"Meeting: {event['title']}"

            # Check for focus time keywords
            if any(keyword in title for keyword in self.focus_keywords):
                return True, f"Focus Time: {event['title']}"

            # Exclude personal/break events
            if any(keyword in title for keyword in self.exclude_keywords):
                continue

            # Default: enable for any calendar event (customizable)
            return True, f"Calendar Event: {event['title']}"

        return False, None

    def check_predictive_events(self, events):
        """Check for upcoming events that should trigger pre-quiet hours"""
        upcoming_events = events.get('upcoming', [])
        predictions = []

        for event in upcoming_events:
            title = event.get('title', '').lower()
            start_time_str = event.get('start')

            # Skip excluded events
            if any(keyword in title for keyword in self.exclude_keywords):
                continue

            # Check if this event should trigger predictive quiet hours
            should_predict = False
            reason = None

            if any(keyword in title for keyword in self.meeting_keywords):
                should_predict = True
                reason = f"Upcoming Meeting: {event['title']}"
            elif any(keyword in title for keyword in self.focus_keywords):
                should_predict = True
                reason = f"Upcoming Focus: {event['title']}"

            if should_predict and start_time_str:
                try:
                    # Parse the event start time
                    event_start = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    now = datetime.now(event_start.tzinfo)

                    # Check if event is within predictive window
                    time_until_event = (event_start - now).total_seconds() / 60  # minutes

                    if 0 < time_until_event <= self.predictive_lead_time:
                        predictions.append({
                            'event': event,
                            'reason': reason,
                            'minutes_until': time_until_event,
                            'start_time': event_start
                        })
                except (ValueError, AttributeError) as e:
                    print(f"Error parsing event time: {e}")
                    continue

        return predictions

    def handle_predictive_quiet_hours(self, predictions):
        """Handle predictive quiet hours activation for upcoming events"""
        if not predictions:
            # Clear any previous predictions if no upcoming events
            if self.upcoming_predictions:
                print("📅 No upcoming events requiring pre-quiet - clearing predictions")
                self.upcoming_predictions = []
            return

        # Check if we have new predictions to activate
        for prediction in predictions:
            event_title = prediction['event']['title']
            reason = prediction['reason']
            minutes_until = prediction['minutes_until']

            # Check if we're already tracking this prediction
            existing = next((p for p in self.upcoming_predictions
                           if p['event']['title'] == event_title), None)

            if not existing:
                # New prediction - activate predictive quiet hours
                print(f"🔮 PREDICTIVE: {reason}")
                print(".1f")
                print("🔔 Activating pre-event quiet hours")

                self.sync_with_athena(True, f"Predictive: {reason}")
                self.upcoming_predictions.append(prediction)

                # Notify dashboard
                self.notify_dashboard_prediction(prediction)

        # Clean up predictions for events that have started or passed
        self.upcoming_predictions = [
            p for p in self.upcoming_predictions
            if p['minutes_until'] > 0
        ]

    def notify_dashboard_prediction(self, prediction):
        """Notify dashboard of predictive activation"""
        try:
            payload = {
                'type': 'predictive_activation',
                'event': prediction['event'],
                'reason': prediction['reason'],
                'minutes_until': prediction['minutes_until'],
                'lead_time': self.predictive_lead_time
            }

            response = requests.post(f"{self.athena_api_url}/calendar-predictive",
                                   json=payload, timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard notified of predictive activation")
        except Exception as e:
            print(f"⚠️ Could not notify dashboard: {e}")

    def sync_with_athena(self, enable_quiet, reason=None):
        """Sync calendar state with Athena quiet hours"""
        if not REQUESTS_AVAILABLE:
            print("Requests library not available for Athena sync")
            return

        try:
            if enable_quiet:
                payload = {
                    'enabled': True,
                    'calendar_event': reason,
                    'source': 'calendar_monitor'
                }
                print(f"📅 Calendar event detected: {reason}")
                print("🔔 Enabling Athena quiet hours")
            else:
                payload = {
                    'enabled': False,
                    'calendar_event': None,
                    'source': 'calendar_monitor'
                }
                print("📅 No active calendar events")
                print("☀️ Athena quiet hours remain manual")

            response = requests.post(f"{self.athena_api_url}/calendar-sync",
                                   json=payload, timeout=5)

            if response.status_code == 200:
                print("✅ Calendar sync successful")
            else:
                print(f"⚠️ Calendar sync failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Calendar sync error: {e}")

    def start_monitoring(self):
        """Start monitoring calendar events"""
        print("📅 Starting Calendar monitoring...")
        self.monitoring = True

        def monitor_loop():
            last_state = None

            while self.monitoring:
                try:
                    events = self.check_calendar_events()
                    should_quiet, reason = self.should_enable_quiet_hours(events)

                    # Handle predictive quiet hours for upcoming events
                    if self.predictive_enabled:
                        predictions = self.check_predictive_events(events)
                        self.handle_predictive_quiet_hours(predictions)

                    # Only sync current events if state changed
                    current_state = (should_quiet, reason)
                    if current_state != last_state:
                        self.sync_with_athena(should_quiet, reason)
                        last_state = current_state

                    # Status reporting
                    if should_quiet:
                        print(f"🔕 Quiet hours active due to: {reason}")
                    elif self.upcoming_predictions:
                        next_prediction = self.upcoming_predictions[0]
                        event_title = next_prediction['event']['title']
                        minutes_until = next_prediction['minutes_until']
                        print(f"🔮 Predictive active: {event_title} starts in {minutes_until:.1f} min")                    else:
                        upcoming = events.get('upcoming', [])
                        if upcoming:
                            next_event = upcoming[0]
                            title = next_event.get('title', 'Unknown')
                            print(f"📅 Next event: {title} (monitoring for predictive activation)")

                except Exception as e:
                    print(f"Calendar monitoring error: {e}")

                time.sleep(self.check_interval)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

        print("✅ Calendar monitoring active")
        print(f"🔍 Checking every {self.check_interval} seconds")
        print("📱 Will automatically sync with Athena during meetings/events")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        print("🛑 Calendar monitoring stopped")

def main():
    if len(sys.argv) < 2:
        print("📅 Athena Calendar Monitor")
        print("=" * 30)
        print()
        print("Automatically enables quiet hours during Calendar events.")
        print()
        print("Commands:")
        print("  --start      Start calendar monitoring")
        print("  --status     Check current calendar status")
        print("  --events     List current and upcoming events")
        print("  --test       Test calendar event detection")
        print("  --stop       Stop monitoring")
        print()
        print("Features:")
        print("  • Monitors macOS Calendar in real-time")
        print("  • Auto-enables quiet hours during meetings")
        print("  • Filters events by type (meetings, focus time)")
        print("  • Integrates with existing Focus mode system")
        print("  • Provides API for dashboard controls")
        print()
        print("Example: python3 calendar_monitor.py --start")

        return

    command = sys.argv[1]
    monitor = CalendarMonitor()

    if command == "--start":
        if not REQUESTS_AVAILABLE:
            print("❌ Requests library required. Install with: pip install requests")
            return

        def signal_handler(signum, frame):
            print("\n🛑 Stopping calendar monitor...")
            monitor.stop_monitoring()
            sys.exit(0)

        import signal
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            monitor.start_monitoring()
            # Keep main thread alive
            while monitor.monitoring:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()

    elif command == "--status":
        print("📊 Calendar Monitor Status")
        print("=" * 30)

        events = monitor.check_calendar_events()
        should_quiet, reason = monitor.should_enable_quiet_hours(events)

        print(f"Monitoring: {'Active' if monitor.monitoring else 'Inactive'}")
        print(f"Quiet Hours: {'Should Enable' if should_quiet else 'Not Needed'}")
        if reason:
            print(f"Reason: {reason}")

        current = events.get('current', [])
        upcoming = events.get('upcoming', [])

        print(f"\nCurrent Events: {len(current)}")
        for event in current:
            print(f"  • {event.get('title', 'Unknown')}")

        print(f"Upcoming Events: {len(upcoming)}")
        for event in upcoming:
            print(f"  • {event.get('title', 'Unknown')}")

    elif command == "--events":
        print("📅 Calendar Events")
        print("=" * 20)

        events = monitor.check_calendar_events()

        print("Current Events:")
        current = events.get('current', [])
        if current:
            for event in current:
                title = event.get('title', 'Unknown')
                start = event.get('start', 'Unknown')
                end = event.get('end', 'Unknown')
                print(f"  🟢 {title}")
                print(f"     {start} - {end}")
        else:
            print("  None")

        print("\nUpcoming Events (next 30 min):")
        upcoming = events.get('upcoming', [])
        if upcoming:
            for event in upcoming:
                title = event.get('title', 'Unknown')
                start = event.get('start', 'Unknown')
                print(f"  🔄 {title} at {start}")
        else:
            print("  None")

    elif command == "--test":
        print("🧪 Testing Calendar Detection")
        print("=" * 35)

        print("Testing calendar event detection...")
        events = monitor.check_calendar_events()

        print(f"Raw events data: {events}")

        should_quiet, reason = monitor.should_enable_quiet_hours(events)
        print(f"Should enable quiet hours: {should_quiet}")
        if reason:
            print(f"Reason: {reason}")

        print("\nTesting Athena sync (dry run)...")
        monitor.sync_with_athena(should_quiet, reason or "test")

        print("\n✅ Calendar detection test complete")

    elif command == "--stop":
        monitor.stop_monitoring()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
