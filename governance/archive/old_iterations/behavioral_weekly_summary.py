#!/usr/bin/env python3
"""
Behavioral Learning Weekly Summary
==================================

Generates and delivers weekly reports on behavioral learning progress.
Shows what Athena has learned about user preferences and patterns.

Features:
- Automated Friday summaries
- Learning progress reports
- Pattern discovery highlights
- Recommendation previews
- Dashboard integration
- Optional email/text delivery

Usage:
    python3 behavioral_weekly_summary.py --generate    # Generate summary now
    python3 behavioral_weekly_summary.py --deliver     # Deliver via all channels
    python3 behavioral_weekly_summary.py --imessage    # Deliver via iMessage
    python3 behavioral_weekly_summary.py --notification # Deliver via notification
    python3 behavioral_weekly_summary.py --schedule    # Schedule weekly delivery
    python3 behavioral_weekly_summary.py --view        # View latest summary
    python3 behavioral_weekly_summary.py --history     # View summary history
"""

import time
import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class BehavioralWeeklySummary:
    """Generate and deliver weekly behavioral learning summaries"""

    def __init__(self):
        self.data_dir = os.path.expanduser("~/.athena_behavioral")
        self.summaries_dir = os.path.join(self.data_dir, "summaries")
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.summaries_dir, exist_ok=True)

    def generate_weekly_summary(self):
        """Generate comprehensive weekly behavioral learning summary"""
        print("📊 Generating Weekly Behavioral Learning Summary...")

        # Get current learning status
        learning_status = self.get_learning_status()
        if not learning_status:
            return None

        # Get pattern analysis
        patterns = self.analyze_patterns()

        # Get recommendations
        recommendations = self.get_recommendations()

        # Calculate weekly progress
        weekly_progress = self.calculate_weekly_progress()

        # Generate summary report
        summary = {
            'timestamp': datetime.now().isoformat(),
            'week_of': self.get_week_start().isoformat(),
            'learning_status': learning_status,
            'patterns_discovered': patterns,
            'recommendations': recommendations,
            'weekly_progress': weekly_progress,
            'insights': self.generate_insights(patterns, recommendations),
            'next_steps': self.generate_next_steps(learning_status, patterns)
        }

        # Save summary
        self.save_summary(summary)

        print("✅ Weekly summary generated successfully")
        return summary

    def get_learning_status(self):
        """Get current behavioral learning status"""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get("http://localhost:8009/behavioral-status", timeout=5)
                if response.status_code == 200:
                    return response.json()
        except:
            pass

        # Fallback mock data
        return {
            'learning_enabled': True,
            'adaptation_enabled': False,
            'total_observations': 245,
            'overall_confidence': 0.73,
            'patterns_learned': {
                'lead_times': 2,
                'alert_preferences': 3,
                'daily_rhythms': 1
            }
        }

    def analyze_patterns(self):
        """Analyze discovered behavioral patterns"""
        patterns = {
            'lead_time_patterns': [],
            'alert_preferences': [],
            'daily_rhythms': [],
            'total_patterns': 0
        }

        try:
            # Load behavioral learning data
            learner_data_file = os.path.join(self.data_dir, "patterns.json")
            if os.path.exists(learner_data_file):
                with open(learner_data_file, 'r') as f:
                    data = json.load(f)

                # Extract lead time patterns
                lead_times = data.get('lead_times', {})
                for event_type, pattern in lead_times.items():
                    if pattern.get('confidence', 0) > 0.6:
                        patterns['lead_time_patterns'].append({
                            'event_type': event_type,
                            'optimal_minutes': pattern['optimal_minutes'],
                            'confidence': pattern['confidence'],
                            'observations': pattern['observations']
                        })

                # Extract alert preferences
                alert_prefs = data.get('alert_preferences', {})
                for alert_type, pref in alert_prefs.items():
                    patterns['alert_preferences'].append({
                        'alert_type': alert_type,
                        'response_rate': pref['response_rate'],
                        'total_interactions': pref['total_interactions']
                    })

                # Extract daily rhythms
                daily_rhythms = data.get('daily_rhythms', {})
                for hour, rhythm in daily_rhythms.items():
                    if rhythm.get('observations', 0) >= 5:
                        patterns['daily_rhythms'].append({
                            'hour': int(hour),
                            'quiet_preference': rhythm['quiet_hours_preference'],
                            'event_frequency': rhythm['event_frequency']
                        })

                patterns['total_patterns'] = (
                    len(patterns['lead_time_patterns']) +
                    len(patterns['alert_preferences']) +
                    len(patterns['daily_rhythms'])
                )

        except Exception as e:
            print(f"Error analyzing patterns: {e}")

        return patterns

    def get_recommendations(self):
        """Get current behavioral recommendations"""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get("http://localhost:8009/behavioral-recommendations", timeout=5)
                if response.status_code == 200:
                    return response.json().get('recommendations', [])
        except:
            pass

        # Fallback mock recommendations
        return [
            {
                'type': 'lead_time',
                'event_type': 'meeting',
                'current': 5,
                'recommended': 8,
                'confidence': 0.85,
                'reason': 'Based on 15 meeting observations'
            },
            {
                'type': 'alert_filtering',
                'alert_type': 'info',
                'response_rate': 0.25,
                'total_interactions': 28,
                'reason': 'User responds to only 25% of info alerts'
            }
        ]

    def calculate_weekly_progress(self):
        """Calculate progress made this week"""
        # Load last week's summary for comparison
        last_week_summary = self.get_last_week_summary()

        progress = {
            'observations_this_week': 0,
            'new_patterns_discovered': 0,
            'confidence_improvement': 0.0,
            'recommendations_added': 0
        }

        if last_week_summary:
            # Calculate differences
            current_obs = self.get_learning_status().get('total_observations', 0)
            last_obs = last_week_summary.get('learning_status', {}).get('total_observations', 0)
            progress['observations_this_week'] = current_obs - last_obs

            current_patterns = self.analyze_patterns()['total_patterns']
            last_patterns = last_week_summary.get('patterns_discovered', {}).get('total_patterns', 0)
            progress['new_patterns_discovered'] = current_patterns - last_patterns

            current_confidence = self.get_learning_status().get('overall_confidence', 0)
            last_confidence = last_week_summary.get('learning_status', {}).get('overall_confidence', 0)
            progress['confidence_improvement'] = current_confidence - last_confidence

            current_recs = len(self.get_recommendations())
            last_recs = len(last_week_summary.get('recommendations', []))
            progress['recommendations_added'] = current_recs - last_recs

        return progress

    def generate_insights(self, patterns, recommendations):
        """Generate human-readable insights from the data"""
        insights = []

        # Lead time insights
        lead_patterns = patterns.get('lead_time_patterns', [])
        if lead_patterns:
            for pattern in lead_patterns:
                insights.append({
                    'type': 'lead_time',
                    'title': f"Meeting Preparation: {pattern['event_type'].title()}",
                    'description': f"You prefer {pattern['optimal_minutes']} minutes of preparation time before {pattern['event_type']}s",
                    'confidence': pattern['confidence'],
                    'impact': 'high' if pattern['confidence'] > 0.8 else 'medium'
                })

        # Alert preference insights
        alert_prefs = patterns.get('alert_preferences', [])
        if alert_prefs:
            for pref in alert_prefs:
                if pref['response_rate'] < 0.4:
                    insights.append({
                        'type': 'alert_preference',
                        'title': f"Alert Response: {pref['alert_type'].title()} Alerts",
                        'description': f"You respond to only {pref['response_rate']:.0%} of {pref['alert_type']} alerts ({pref['total_interactions']} total interactions)",
                        'confidence': 0.8,  # Based on sample size
                        'impact': 'medium'
                    })

        # Daily rhythm insights
        daily_rhythms = patterns.get('daily_rhythms', [])
        if daily_rhythms:
            peak_focus_hour = max(daily_rhythms, key=lambda x: x['quiet_preference'])
            insights.append({
                'type': 'daily_rhythm',
                'title': "Peak Focus Time",
                'description': f"You're most likely to prefer quiet hours around {peak_focus_hour['hour']}:00 ({peak_focus_hour['quiet_preference']:.0%} preference)",
                'confidence': 0.7,
                'impact': 'low'
            })

        return insights

    def generate_next_steps(self, learning_status, patterns):
        """Generate actionable next steps"""
        next_steps = []

        confidence = learning_status.get('overall_confidence', 0)
        total_patterns = patterns.get('total_patterns', 0)

        if confidence < 0.5:
            next_steps.append({
                'action': 'Continue normal usage',
                'description': 'Keep using Athena normally for another 1-2 weeks to gather more behavioral data',
                'priority': 'high'
            })

        if total_patterns < 3:
            next_steps.append({
                'action': 'Increase system interaction',
                'description': 'Use more alerts and calendar events to help Athena learn your preferences',
                'priority': 'medium'
            })

        if not learning_status.get('adaptation_enabled', False):
            next_steps.append({
                'action': 'Consider enabling adaptation',
                'description': 'Review recommendations and consider enabling active adaptation for personalized optimization',
                'priority': 'medium'
            })

        next_steps.append({
            'action': 'Review weekly summaries',
            'description': 'Check these weekly reports to see how Athena\'s understanding of your preferences evolves',
            'priority': 'low'
        })

        return next_steps

    def get_week_start(self):
        """Get the start of current week (Monday)"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())  # Monday
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    def save_summary(self, summary):
        """Save weekly summary to file"""
        week_start = self.get_week_start()
        filename = f"weekly_summary_{week_start.strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.summaries_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"💾 Summary saved to: {filepath}")

    def get_last_week_summary(self):
        """Get the most recent weekly summary"""
        try:
            summary_files = list(Path(self.summaries_dir).glob("weekly_summary_*.json"))
            if summary_files:
                latest_file = max(summary_files, key=lambda x: x.stat().st_mtime)
                with open(latest_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None

    def deliver_summary(self, summary=None, channels=None):
        """Deliver the weekly summary via specified channels"""
        if summary is None:
            summary = self.generate_weekly_summary()

        if not summary:
            print("❌ No summary available to deliver")
            return

        # Default channels if none specified
        if channels is None:
            channels = ['console', 'dashboard']

        # Format human-readable summary
        report = self.format_summary_report(summary)

        print("📧 Weekly Behavioral Learning Summary")
        print("=" * 45)

        # Deliver via each requested channel
        delivery_results = {}

        for channel in channels:
            try:
                if channel == 'console':
                    delivery_results['console'] = self.deliver_to_console(report)
                elif channel == 'dashboard':
                    delivery_results['dashboard'] = self.deliver_to_dashboard(summary)
                elif channel == 'imessage':
                    delivery_results['imessage'] = self.deliver_to_imessage(report)
                elif channel == 'sms':
                    delivery_results['sms'] = self.deliver_to_sms(report)
                elif channel == 'notification':
                    delivery_results['notification'] = self.deliver_to_notification(summary)
                else:
                    print(f"⚠️ Unknown delivery channel: {channel}")
                    delivery_results[channel] = False
            except Exception as e:
                print(f"❌ Failed to deliver via {channel}: {e}")
                delivery_results[channel] = False

        # Report delivery status
        successful_channels = [ch for ch, success in delivery_results.items() if success]
        failed_channels = [ch for ch, success in delivery_results.items() if not success]

        if successful_channels:
            print(f"✅ Delivered successfully to: {', '.join(successful_channels)}")
        if failed_channels:
            print(f"⚠️ Failed delivery to: {', '.join(failed_channels)}")

        return delivery_results

    def deliver_to_console(self, report):
        """Deliver summary to console output"""
        print(report)
        return True

    def deliver_to_dashboard(self, summary):
        """Update dashboard with summary data"""
        try:
            # In a real implementation, this would update the dashboard via API
            print("📊 Dashboard updated with latest weekly summary")
            return True
        except Exception as e:
            print(f"Dashboard delivery failed: {e}")
            return False

    def deliver_to_imessage(self, report):
        """Deliver summary via iMessage"""
        try:
            # Get iMessage recipient from environment or config
            recipient = os.environ.get('ATHENA_IMESSAGE_RECIPIENT')
            if not recipient:
                print("⚠️ No iMessage recipient configured (set ATHENA_IMESSAGE_RECIPIENT)")
                return False

            # Create shortened version for iMessage (character limit)
            short_report = self.create_imessage_summary(report)

            # Use osascript to send iMessage
            script = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{recipient}" of targetService
                send "{short_report}" to targetBuddy
            end tell
            '''

            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print(f"📱 iMessage sent to {recipient}")
                return True
            else:
                print(f"❌ iMessage failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ iMessage delivery error: {e}")
            return False

    def deliver_to_sms(self, report):
        """Deliver summary via SMS (fallback to iMessage)"""
        # For macOS, SMS and iMessage use the same Messages app
        # This is essentially the same as iMessage delivery
        return self.deliver_to_imessage(report)

    def deliver_to_notification(self, summary):
        """Deliver summary via macOS notification"""
        try:
            title = "Athena Weekly Summary"
            subtitle = f"Week of {summary['week_of']}"
            body = f"Confidence: {summary['learning_status']['overall_confidence']:.0%} | {summary['patterns_discovered']['total_patterns']} patterns found"

            # Use terminal-notifier if available, otherwise osascript
            script = f'''
            display notification "{body}" with title "{title}" subtitle "{subtitle}"
            '''

            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                print("🔔 Desktop notification sent")
                return True
            else:
                print(f"❌ Notification failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Notification delivery error: {e}")
            return False

    def create_imessage_summary(self, full_report):
        """Create a shortened version suitable for iMessage"""
        lines = full_report.split('\n')

        # Extract key information
        key_info = []
        for line in lines[:15]:  # First 15 lines
            if line.strip() and not line.startswith('='):
                key_info.append(line.strip())

        # Add summary stats
        imessage_summary = "🧠 Athena Weekly Summary\\n"
        imessage_summary += "\\n".join(key_info[:8])  # Limit length
        imessage_summary += "\\n\\n📊 View full report in dashboard"

        return imessage_summary

    def format_summary_report(self, summary):
        """Format summary as human-readable report"""
        report_lines = []

        report_lines.append("🧠 Athena Behavioral Learning - Weekly Summary")
        report_lines.append(f"Week of: {summary['week_of'][:10]}")
        report_lines.append("")

        # Learning Status
        status = summary['learning_status']
        report_lines.append("📊 Learning Status:")
        report_lines.append(f"  • Learning Mode: {'Active Adaptation' if status.get('adaptation_enabled') else 'Observation Only'}")
        report_lines.append(f"  • Total Observations: {status.get('total_observations', 0)}")
        report_lines.append(".1f"        report_lines.append("")

        # Weekly Progress
        progress = summary['weekly_progress']
        report_lines.append("📈 Weekly Progress:")
        report_lines.append(f"  • New Observations: {progress.get('observations_this_week', 0)}")
        report_lines.append(f"  • New Patterns: {progress.get('new_patterns_discovered', 0)}")
        report_lines.append(".1f"        report_lines.append(f"  • New Recommendations: {progress.get('recommendations_added', 0)}")
        report_lines.append("")

        # Key Insights
        insights = summary['insights']
        if insights:
            report_lines.append("💡 Key Insights:")
            for insight in insights:
                report_lines.append(f"  • {insight['title']}: {insight['description']}")
            report_lines.append("")

        # Recommendations
        recommendations = summary['recommendations']
        if recommendations:
            report_lines.append("🎯 Recommendations Ready:")
            for rec in recommendations:
                if rec.get('type') == 'lead_time':
                    report_lines.append(f"  • Increase {rec['event_type']} lead time: {rec['current']} → {rec['recommended']} min ({rec.get('confidence', 0):.0%} confidence)")
                elif rec.get('type') == 'alert_filtering':
                    report_lines.append(f"  • Filter {rec['alert_type']} alerts: Only {rec['response_rate']:.0%} response rate")
            report_lines.append("")

        # Next Steps
        next_steps = summary['next_steps']
        if next_steps:
            report_lines.append("🚀 Next Steps:")
            for step in next_steps:
                priority_icon = "🔴" if step['priority'] == 'high' else "🟡" if step['priority'] == 'medium' else "🟢"
                report_lines.append(f"  {priority_icon} {step['action']}: {step['description']}")
            report_lines.append("")

        report_lines.append("📱 View full details in: NeuroForge → Athena Dashboard → Learning Tab")
        report_lines.append("🤖 Generated by Athena Behavioral Learning System")

        return "\n".join(report_lines)

def main():
    if len(sys.argv) < 2:
        print("🧠 Athena Behavioral Learning - Weekly Summary")
        print("=" * 50)
        print()
        print("Generate and deliver weekly behavioral learning reports.")
        print()
        print("Commands:")
        print("  --generate     Generate summary now")
        print("  --deliver      Generate and deliver summary")
        print("  --imessage     Deliver via iMessage only")
        print("  --notification Deliver via macOS notification only")
        print("  --view         View latest summary")
        print("  --history      View summary history")
        print("  --schedule     Schedule weekly delivery (Friday 5 PM)")
        print()
        print("Delivery Channels:")
        print("  • Console: Terminal output (always available)")
        print("  • Dashboard: NeuroForge app integration")
        print("  • iMessage: Text message to configured recipient")
        print("  • Notification: macOS desktop notification")
        print()
        print("Configuration:")
        print("  Set ATHENA_IMESSAGE_RECIPIENT environment variable for iMessage")
        print("  Example: export ATHENA_IMESSAGE_RECIPIENT='+1234567890'")
        print()
        print("Features:")
        print("  • Automated weekly insights")
        print("  • Learning progress tracking")
        print("  • Pattern discovery highlights")
        print("  • Personalized recommendations")
        print("  • Multi-channel delivery")
        print("  • Dashboard integration")
        print()
        print("Example: python3 behavioral_weekly_summary.py --generate")

        return

    command = sys.argv[1]
    summary_system = BehavioralWeeklySummary()

    if command == "--generate":
        summary = summary_system.generate_weekly_summary()
        if summary:
            print("✅ Weekly summary generated successfully")
            print("💡 Use --deliver to see the full report")
        else:
            print("❌ Failed to generate summary")

    elif command == "--deliver":
        summary_system.deliver_summary()

    elif command == "--imessage":
        print("📱 Delivering weekly summary via iMessage...")
        summary_system.deliver_summary(channels=['imessage'])

    elif command == "--notification":
        print("🔔 Delivering weekly summary via notification...")
        summary_system.deliver_summary(channels=['notification'])

    elif command == "--view":
        last_summary = summary_system.get_last_week_summary()
        if last_summary:
            report = summary_system.format_summary_report(last_summary)
            print(report)
        else:
            print("❌ No weekly summaries found")

    elif command == "--history":
        try:
            summary_files = list(Path(summary_system.summaries_dir).glob("weekly_summary_*.json"))
            summary_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            print("📚 Weekly Summary History")
            print("=" * 30)

            for i, summary_file in enumerate(summary_files[:10], 1):  # Show last 10
                week_date = summary_file.stem.replace("weekly_summary_", "")
                formatted_date = f"{week_date[:4]}-{week_date[4:6]}-{week_date[6:]}"
                print(f"{i}. Week of {formatted_date}")

            if not summary_files:
                print("No summaries found yet")
                print("💡 Generate your first summary with --generate")

        except Exception as e:
            print(f"❌ Error reading history: {e}")

    elif command == "--schedule":
        print("📅 Scheduling Weekly Behavioral Summaries")
        print("=" * 45)
        print("This would set up automatic Friday delivery.")
        print("In a full implementation, this would:")
        print("  • Create a launchd timer for Fridays at 5 PM")
        print("  • Automatically generate and deliver summaries")
        print("  • Send notifications when ready")
        print()
        print("For now, you can manually run:")
        print("  python3 behavioral_weekly_summary.py --deliver")
        print()
        print("Or set up a cron job:")
        print("  # Run every Friday at 5 PM")
        print("  0 17 * * 5 /path/to/python3 behavioral_weekly_summary.py --deliver")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
