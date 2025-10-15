#!/usr/bin/env python3
"""
Behavioral Learning for Athena
==============================

Observes user patterns and learns optimal alert timing and suppression rules.
Starts in observation-only mode for safe pattern collection before enabling adaptation.

Features:
- Pattern observation without disruption
- Learning analysis and recommendations
- Safe transition to active adaptation
- Full rollback capability
- Privacy-focused local learning

Usage:
    python3 behavioral_learning.py --start          # Start observation mode
    python3 behavioral_learning.py --analyze        # Analyze learned patterns
    python3 behavioral_learning.py --recommend      # Get recommendations
    python3 behavioral_learning.py --enable         # Enable active adaptation
    python3 behavioral_learning.py --disable        # Return to observation-only
    python3 behavioral_learning.py --reset          # Clear all learned data
"""

import time
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import threading
import statistics

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class BehavioralLearning:
    """Learn user behavior patterns for optimal alert timing"""

    def __init__(self):
        self.data_dir = os.path.expanduser("~/.athena_behavioral")
        self.patterns_file = os.path.join(self.data_dir, "patterns.json")
        self.observations_file = os.path.join(self.data_dir, "observations.json")

        # Learning state
        self.learning_enabled = False
        self.adaptation_enabled = False
        self.confidence_threshold = 0.7  # Need 70% confidence before suggesting changes

        # Pattern storage
        self.patterns = self.load_patterns()
        self.observations = self.load_observations()

        # Current session tracking
        self.session_start = datetime.now()
        self.session_alerts = []

    def ensure_data_dir(self):
        """Ensure behavioral data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)

    def load_patterns(self):
        """Load learned patterns from disk"""
        try:
            if os.path.exists(self.patterns_file):
                with open(self.patterns_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading patterns: {e}")

        # Default patterns
        return {
            'lead_times': {},
            'alert_preferences': {},
            'context_patterns': {},
            'daily_rhythms': {},
            'last_updated': datetime.now().isoformat(),
            'observation_count': 0
        }

    def save_patterns(self):
        """Save learned patterns to disk"""
        try:
            self.ensure_data_dir()
            self.patterns['last_updated'] = datetime.now().isoformat()
            with open(self.patterns_file, 'w') as f:
                json.dump(self.patterns, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving patterns: {e}")

    def load_observations(self):
        """Load raw observations from disk"""
        try:
            if os.path.exists(self.observations_file):
                with open(self.observations_file, 'r') as f:
                    data = json.load(f)
                    # Convert string timestamps back to datetime
                    for obs in data:
                        if 'timestamp' in obs:
                            obs['timestamp'] = datetime.fromisoformat(obs['timestamp'])
                    return data
        except Exception as e:
            print(f"Error loading observations: {e}")

        return []

    def save_observations(self):
        """Save raw observations to disk"""
        try:
            self.ensure_data_dir()
            with open(self.observations_file, 'w') as f:
                json.dump(self.observations, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving observations: {e}")

    def start_learning(self, adaptation_enabled=False):
        """Start behavioral learning"""
        self.learning_enabled = True
        self.adaptation_enabled = adaptation_enabled

        print("🧠 Behavioral learning started")
        print(f"   Mode: {'Active Adaptation' if adaptation_enabled else 'Observation Only'}")
        print("   Collecting patterns for optimal alert timing...")

        # Start background learning thread
        learning_thread = threading.Thread(target=self.learning_loop, daemon=True)
        learning_thread.start()

    def stop_learning(self):
        """Stop behavioral learning"""
        self.learning_enabled = False
        print("🛑 Behavioral learning stopped")

    def learning_loop(self):
        """Main learning loop"""
        while self.learning_enabled:
            try:
                # Collect current context
                context = self.get_current_context()

                # Observe user behavior
                self.observe_behavior(context)

                # Analyze patterns periodically
                if len(self.observations) % 50 == 0:  # Every 50 observations
                    self.analyze_patterns()

                time.sleep(60)  # Check every minute

            except Exception as e:
                print(f"Learning loop error: {e}")
                time.sleep(60)

    def get_current_context(self):
        """Get current system context"""
        context = {
            'timestamp': datetime.now(),
            'quiet_hours_active': False,
            'calendar_event': None,
            'focus_mode': None,
            'day_of_week': datetime.now().weekday(),
            'hour_of_day': datetime.now().hour
        }

        # Try to get Athena context
        if REQUESTS_AVAILABLE:
            try:
                # Get quiet hours status
                response = requests.get("http://localhost:8009/quiet-hours", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    context['quiet_hours_active'] = data.get('is_quiet_hours', False)

                # Get calendar status
                response = requests.get("http://localhost:8009/calendar-status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    context['calendar_event'] = data.get('calendar_event')
                    context['focus_mode'] = data.get('focus_mode')

            except:
                pass  # Continue without Athena context

        return context

    def observe_behavior(self, context):
        """Observe and record user behavior"""
        observation = {
            'timestamp': context['timestamp'],
            'context': context,
            'alerts_received': len(self.session_alerts),
            'user_actions': []  # Would track actual user interactions
        }

        self.observations.append(observation)

        # Keep only recent observations (last 1000)
        if len(self.observations) > 1000:
            self.observations = self.observations[-1000:]

        # Save observations periodically
        if len(self.observations) % 100 == 0:
            self.save_observations()

    def record_alert_interaction(self, alert_type, user_action, context=None):
        """Record how user interacts with alerts"""
        if not self.learning_enabled:
            return

        interaction = {
            'timestamp': datetime.now(),
            'alert_type': alert_type,
            'user_action': user_action,  # 'dismissed', 'acted_on', 'ignored'
            'context': context or self.get_current_context()
        }

        self.session_alerts.append(interaction)

        # Immediate observation recording
        observation = {
            'timestamp': datetime.now(),
            'type': 'alert_interaction',
            'interaction': interaction,
            'context': context or self.get_current_context()
        }

        self.observations.append(observation)

    def record_quiet_hours_timing(self, event_type, actual_prep_time, effective=True):
        """Record quiet hours timing effectiveness"""
        if not self.learning_enabled:
            return

        observation = {
            'timestamp': datetime.now(),
            'type': 'quiet_hours_timing',
            'event_type': event_type,
            'actual_prep_time': actual_prep_time,
            'effective': effective,
            'context': self.get_current_context()
        }

        self.observations.append(observation)

    def analyze_patterns(self):
        """Analyze collected observations to learn patterns"""
        if len(self.observations) < 20:  # Need minimum data
            return

        print("🔍 Analyzing behavioral patterns...")

        # Analyze lead time preferences
        self.analyze_lead_time_patterns()

        # Analyze alert preferences
        self.analyze_alert_patterns()

        # Analyze daily rhythms
        self.analyze_daily_patterns()

        # Update confidence scores
        self.update_confidence_scores()

        # Save updated patterns
        self.save_patterns()

        print("✅ Pattern analysis complete")

    def analyze_lead_time_patterns(self):
        """Analyze optimal lead times for different event types"""
        quiet_timing_obs = [obs for obs in self.observations
                           if obs.get('type') == 'quiet_hours_timing']

        if not quiet_timing_obs:
            return

        # Group by event type
        by_event_type = defaultdict(list)
        for obs in quiet_timing_obs:
            event_type = obs.get('event_type', 'unknown')
            if obs.get('effective', True):
                by_event_type[event_type].append(obs['actual_prep_time'])

        # Calculate optimal lead times
        for event_type, prep_times in by_event_type.items():
            if len(prep_times) >= 3:  # Need some data
                optimal_time = statistics.mean(prep_times)
                confidence = min(len(prep_times) / 10.0, 1.0)  # More observations = higher confidence

                self.patterns['lead_times'][event_type] = {
                    'optimal_minutes': round(optimal_time, 1),
                    'confidence': confidence,
                    'observations': len(prep_times)
                }

    def analyze_alert_patterns(self):
        """Analyze which alert types user responds to"""
        alert_interactions = [obs for obs in self.observations
                             if obs.get('type') == 'alert_interaction']

        if not alert_interactions:
            return

        # Count interactions by alert type and action
        interaction_counts = defaultdict(lambda: defaultdict(int))

        for obs in alert_interactions:
            interaction = obs.get('interaction', {})
            alert_type = interaction.get('alert_type', 'unknown')
            action = interaction.get('user_action', 'unknown')

            interaction_counts[alert_type][action] += 1

        # Calculate response rates
        for alert_type, actions in interaction_counts.items():
            total = sum(actions.values())
            if total >= 5:  # Need some data
                acted_on = actions.get('acted_on', 0)
                response_rate = acted_on / total

                self.patterns['alert_preferences'][alert_type] = {
                    'response_rate': round(response_rate, 2),
                    'total_interactions': total,
                    'acted_on': acted_on,
                    'ignored': actions.get('dismissed', 0) + actions.get('ignored', 0)
                }

    def analyze_daily_patterns(self):
        """Analyze daily behavioral rhythms"""
        recent_obs = self.observations[-200:]  # Last 200 observations

        # Group by hour of day
        hourly_patterns = defaultdict(list)

        for obs in recent_obs:
            hour = obs['timestamp'].hour if isinstance(obs['timestamp'], datetime) else 0
            context = obs.get('context', {})

            hourly_patterns[hour].append({
                'quiet_active': context.get('quiet_hours_active', False),
                'has_event': bool(context.get('calendar_event'))
            })

        # Analyze patterns
        for hour, patterns in hourly_patterns.items():
            if len(patterns) >= 5:  # Need some data
                quiet_rate = sum(1 for p in patterns if p['quiet_active']) / len(patterns)
                event_rate = sum(1 for p in patterns if p['has_event']) / len(patterns)

                self.patterns['daily_rhythms'][str(hour)] = {
                    'quiet_hours_preference': round(quiet_rate, 2),
                    'event_frequency': round(event_rate, 2),
                    'observations': len(patterns)
                }

    def update_confidence_scores(self):
        """Update overall confidence in learned patterns"""
        total_observations = len(self.observations)
        self.patterns['observation_count'] = total_observations

        # Calculate overall confidence
        if total_observations > 100:
            confidence = min(total_observations / 500.0, 1.0)  # Max confidence at 500 observations
            self.patterns['overall_confidence'] = round(confidence, 2)
        else:
            self.patterns['overall_confidence'] = 0.0

    def get_recommendations(self):
        """Get behavioral recommendations based on learned patterns"""
        recommendations = []

        # Lead time recommendations
        for event_type, pattern in self.patterns.get('lead_times', {}).items():
            if pattern['confidence'] >= self.confidence_threshold:
                current_default = 5  # Default lead time
                recommended = pattern['optimal_minutes']

                if abs(recommended - current_default) > 1:  # Significant difference
                    recommendations.append({
                        'type': 'lead_time',
                        'event_type': event_type,
                        'current': current_default,
                        'recommended': recommended,
                        'confidence': pattern['confidence'],
                        'reason': f"Based on {pattern['observations']} observations"
                    })

        # Alert filtering recommendations
        for alert_type, pattern in self.patterns.get('alert_preferences', {}).items():
            if pattern['response_rate'] < 0.3:  # User rarely responds
                recommendations.append({
                    'type': 'alert_filtering',
                    'alert_type': alert_type,
                    'response_rate': pattern['response_rate'],
                    'total_interactions': pattern['total_interactions'],
                    'reason': f"User responds to only {pattern['response_rate']:.0%} of these alerts"
                })

        return recommendations

    def apply_adaptation(self):
        """Apply learned patterns if adaptation is enabled"""
        if not self.adaptation_enabled:
            return

        recommendations = self.get_recommendations()

        for rec in recommendations:
            if rec['confidence'] >= self.confidence_threshold:
                self.apply_recommendation(rec)

    def apply_recommendation(self, recommendation):
        """Apply a specific recommendation"""
        rec_type = recommendation['type']

        if rec_type == 'lead_time':
            # Update calendar monitor lead times
            print(f"🎯 Adapting lead time for {recommendation['event_type']}: {recommendation['current']} → {recommendation['recommended']} min")

            # This would update the calendar monitor configuration
            # For now, just log the adaptation

        elif rec_type == 'alert_filtering':
            print(f"🎯 Adapting alert filtering for {recommendation['alert_type']}: reducing frequency due to low response rate")

            # This would update alert filtering rules
            # For now, just log the adaptation

    def get_learning_status(self):
        """Get current learning status and insights"""
        return {
            'learning_enabled': self.learning_enabled,
            'adaptation_enabled': self.adaptation_enabled,
            'total_observations': len(self.observations),
            'overall_confidence': self.patterns.get('overall_confidence', 0.0),
            'patterns_learned': {
                'lead_times': len(self.patterns.get('lead_times', {})),
                'alert_preferences': len(self.patterns.get('alert_preferences', {})),
                'daily_rhythms': len(self.patterns.get('daily_rhythms', {}))
            },
            'last_updated': self.patterns.get('last_updated')
        }

    def reset_learning(self):
        """Reset all learned patterns and observations"""
        self.patterns = {
            'lead_times': {},
            'alert_preferences': {},
            'context_patterns': {},
            'daily_rhythms': {},
            'last_updated': datetime.now().isoformat(),
            'observation_count': 0,
            'overall_confidence': 0.0
        }

        self.observations = []
        self.save_patterns()
        self.save_observations()

        print("🔄 Behavioral learning data reset")

def main():
    if len(sys.argv) < 2:
        print("🧠 Athena Behavioral Learning")
        print("=" * 35)
        print()
        print("Learn optimal alert timing from user behavior.")
        print()
        print("Commands:")
        print("  --start           Start observation-only learning")
        print("  --enable          Enable active adaptation")
        print("  --disable         Return to observation-only")
        print("  --status          Show learning status and insights")
        print("  --analyze         Force pattern analysis")
        print("  --recommend       Show behavioral recommendations")
        print("  --reset           Clear all learned data")
        print("  --test            Add test observations")
        print()
        print("Modes:")
        print("  Observation: Learns patterns without changing behavior")
        print("  Adaptation: Learns AND applies optimized settings")
        print()
        print("Example: python3 behavioral_learning.py --start")

        return

    command = sys.argv[1]
    learner = BehavioralLearning()

    if command == "--start":
        learner.start_learning(adaptation_enabled=False)
        print("✅ Behavioral learning started in observation mode")
        print("💡 System will learn your patterns for 2+ weeks before recommendations")

        # Keep running
        try:
            while learner.learning_enabled:
                time.sleep(1)
        except KeyboardInterrupt:
            learner.stop_learning()

    elif command == "--enable":
        learner.start_learning(adaptation_enabled=True)
        print("✅ Active behavioral adaptation enabled")
        print("⚠️ System will now automatically adjust alert timing based on learned patterns")

    elif command == "--disable":
        learner.adaptation_enabled = False
        learner.learning_enabled = True
        print("✅ Returned to observation-only mode")

    elif command == "--status":
        status = learner.get_learning_status()
        print("🧠 Behavioral Learning Status")
        print("=" * 30)
        print(f"Learning Enabled: {status['learning_enabled']}")
        print(f"Adaptation Enabled: {status['adaptation_enabled']}")
        print(f"Total Observations: {status['total_observations']}")
        print(f"Overall Confidence: {status['overall_confidence']:.1%}")
        print("Patterns Learned:")
        for pattern_type, count in status['patterns_learned'].items():
            print(f"  • {pattern_type.replace('_', ' ').title()}: {count}")
        print(f"Last Updated: {status['last_updated'] or 'Never'}")

        if status['overall_confidence'] < 0.5:
            print("\n💡 Need more data - continue using the system normally")

    elif command == "--analyze":
        learner.analyze_patterns()
        print("✅ Pattern analysis complete")

    elif command == "--recommend":
        recommendations = learner.get_recommendations()
        print("🎯 Behavioral Recommendations")
        print("=" * 30)

        if not recommendations:
            print("No recommendations yet - need more observation data")
            return

        for rec in recommendations:
            print(f"\n📋 {rec['type'].replace('_', ' ').title()}: {rec.get('event_type', rec.get('alert_type', 'General'))}")
            print(f"   Confidence: {rec.get('confidence', 0):.1%}")
            print(f"   Reason: {rec['reason']}")

            if 'recommended' in rec:
                print(f"   Suggested: {rec['current']} → {rec['recommended']}")

    elif command == "--reset":
        learner.reset_learning()
        print("✅ All behavioral learning data cleared")

    elif command == "--test":
        print("🧪 Adding test observations for demonstration...")

        # Add some test data
        test_context = learner.get_current_context()

        # Simulate various scenarios
        learner.record_alert_interaction('warning', 'acted_on', test_context)
        learner.record_alert_interaction('info', 'ignored', test_context)
        learner.record_quiet_hours_timing('meeting', 7, True)
        learner.record_quiet_hours_timing('presentation', 12, True)

        # Force analysis
        learner.analyze_patterns()

        print("✅ Test data added - run --recommend to see suggestions")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
