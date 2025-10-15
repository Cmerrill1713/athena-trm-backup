#!/usr/bin/env python3
"""
ATHENA SENSITIVITY CONFIGURATION
Configure wake-word sensitivity for different environments
"""

import os
import json
import sys
from typing import Dict, Any

class AthenaSensitivityConfig:
    """Manages wake-word sensitivity configuration for Athena"""

    def __init__(self):
        self.config_file = "/etc/ai-republic/athena_sensitivity.json"
        self.default_config = {
            "current_sensitivity": "medium",
            "profiles": {
                "low": {
                    "name": "Quiet Environment",
                    "description": "For quiet rooms, libraries, or focused work spaces",
                    "energy_threshold": 100,
                    "wake_word_threshold": 0.3,
                    "pause_threshold": 0.5,
                    "phrase_threshold": 0.3,
                    "non_speaking_duration": 0.3,
                    "recommended_for": "Quiet offices, libraries, focused work"
                },
                "medium": {
                    "name": "Balanced Environment",
                    "description": "Default setting for general office or home use",
                    "energy_threshold": 200,
                    "wake_word_threshold": 0.4,
                    "pause_threshold": 0.6,
                    "phrase_threshold": 0.4,
                    "non_speaking_duration": 0.5,
                    "recommended_for": "General offices, homes, balanced noise levels"
                },
                "high": {
                    "name": "Noisy Environment",
                    "description": "For loud spaces, open offices, or busy environments",
                    "energy_threshold": 400,
                    "wake_word_threshold": 0.6,
                    "pause_threshold": 0.8,
                    "phrase_threshold": 0.6,
                    "non_speaking_duration": 0.8,
                    "recommended_for": "Open offices, busy spaces, high background noise"
                }
            },
            "auto_adjust": {
                "enabled": False,
                "noise_samples": 10,
                "adjustment_interval": 300  # 5 minutes
            }
        }
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load sensitivity configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    merged = self.default_config.copy()
                    merged.update(loaded)
                    return merged
        except Exception as e:
            print(f"Warning: Could not load config: {e}")

        return self.default_config.copy()

    def _save_config(self):
        """Save current configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def set_sensitivity(self, level: str) -> bool:
        """Set the current sensitivity level"""
        if level not in self.config['profiles']:
            print(f"❌ Invalid sensitivity level: {level}")
            print(f"   Available: {', '.join(self.config['profiles'].keys())}")
            return False

        self.config['current_sensitivity'] = level
        self._save_config()

        profile = self.config['profiles'][level]
        print(f"✅ Wake-word sensitivity set to: {level.upper()}")
        print(f"   Profile: {profile['name']}")
        print(f"   Environment: {profile['recommended_for']}")
        print(f"   Energy threshold: {profile['energy_threshold']}")

        return True

    def get_current_sensitivity(self) -> str:
        """Get current sensitivity level"""
        return self.config['current_sensitivity']

    def get_sensitivity_info(self, level: str = None) -> str:
        """Get detailed information about a sensitivity level"""
        if level is None:
            level = self.config['current_sensitivity']

        if level not in self.config['profiles']:
            return f"Unknown sensitivity level: {level}"

        profile = self.config['profiles'][level]
        current_marker = " (CURRENT)" if level == self.config['current_sensitivity'] else ""

        info = f"""
🎚️ SENSITIVITY PROFILE: {level.upper()}{current_marker}
{'=' * (25 + len(level))}

Name: {profile['name']}
Description: {profile['description']}
Recommended For: {profile['recommended_for']}

Technical Settings:
• Energy Threshold: {profile['energy_threshold']} (higher = less sensitive to noise)
• Wake Word Confidence: {profile['wake_word_threshold']} (higher = fewer false activations)
• Pause Threshold: {profile['pause_threshold']}
• Phrase Threshold: {profile['phrase_threshold']}
• Non-speaking Duration: {profile['non_speaking_duration']}
"""
        return info.strip()

    def list_sensitivity_levels(self) -> str:
        """List all available sensitivity levels"""
        output = ["🎚️ AVAILABLE SENSITIVITY LEVELS", "=" * 35]

        current = self.config['current_sensitivity']

        for level, profile in self.config['profiles'].items():
            marker = " ← CURRENT" if level == current else ""
            output.append(f"\n{level.upper()}{marker}")
            output.append(f"  {profile['name']}")
            output.append(f"  {profile['recommended_for']}")
            output.append(f"  Energy threshold: {profile['energy_threshold']}")

        return "\n".join(output)

    def recommend_sensitivity(self, environment: str = None) -> str:
        """Recommend sensitivity based on environment description"""
        if not environment:
            return """To get a recommendation, describe your environment:
• "quiet office" or "library"
• "busy open office" or "loud workspace"
• "home office" or "quiet room"
• "noisy cafe" or "busy environment"

Example: python3 athena_sensitivity_config.py recommend "busy open office\""""

        env_lower = environment.lower()

        # Environment-based recommendations
        if any(word in env_lower for word in ['quiet', 'library', 'focused', 'silent']):
            recommended = 'low'
            reason = "quiet environment detected"
        elif any(word in env_lower for word in ['noisy', 'loud', 'busy', 'open office', 'cafe', 'crowded']):
            recommended = 'high'
            reason = "noisy environment detected"
        else:
            recommended = 'medium'
            reason = "general environment - using balanced default"

        profile = self.config['profiles'][recommended]

        recommendation = f"""
🎯 RECOMMENDED SENSITIVITY: {recommended.upper()}
Based on: {reason}

Profile Details:
• Name: {profile['name']}
• Recommended For: {profile['recommended_for']}
• Energy Threshold: {profile['energy_threshold']}

To apply: athena-voice --set-sensitivity {recommended}
"""

        return recommendation.strip()

    def test_sensitivity(self, level: str = None) -> str:
        """Test wake word detection with current sensitivity"""
        if level and level != self.config['current_sensitivity']:
            if not self.set_sensitivity(level):
                return "Failed to set sensitivity level"

        current = self.config['current_sensitivity']
        profile = self.config['profiles'][current]

        test_info = f"""
🧪 SENSITIVITY TEST: {current.upper()}

Current Settings:
• Energy Threshold: {profile['energy_threshold']}
• Wake Word Confidence: {profile['wake_word_threshold']}
• Environment: {profile['recommended_for']}

To test wake word detection:
1. Run: athena-voice --mode continuous --sensitivity {current}
2. Say: "Hey Athena, what is the status?"
3. Check if wake word is detected reliably
4. Adjust sensitivity if needed: --sensitivity low/medium/high

Expected behavior for {current} sensitivity:
• {'Fewer false activations, may miss quiet speech' if current == 'low' else 'Balanced detection, good for general use' if current == 'medium' else 'More tolerant of noise, may have false activations'}
"""
        return test_info.strip()

def main():
    """Main entry point for sensitivity configuration"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena Wake-Word Sensitivity Configuration')
    parser.add_argument('action', choices=['set', 'get', 'list', 'info', 'recommend', 'test'],
                       help='Configuration action')
    parser.add_argument('value', nargs='?', help='Value for the action (level, environment, etc.)')
    parser.add_argument('--quiet', action='store_true', help='Quiet output')

    args = parser.parse_args()

    config = AthenaSensitivityConfig()

    if args.action == 'set':
        if not args.value:
            print("❌ Please specify sensitivity level: low, medium, or high")
            sys.exit(1)
        success = config.set_sensitivity(args.value)
        sys.exit(0 if success else 1)

    elif args.action == 'get':
        level = config.get_current_sensitivity()
        if args.quiet:
            print(level)
        else:
            print(f"Current sensitivity: {level}")
        sys.exit(0)

    elif args.action == 'list':
        output = config.list_sensitivity_levels()
        print(output)
        sys.exit(0)

    elif args.action == 'info':
        level = args.value or config.get_current_sensitivity()
        output = config.get_sensitivity_info(level)
        print(output)
        sys.exit(0)

    elif args.action == 'recommend':
        if not args.value:
            print("❌ Please describe your environment")
            print("Example: 'busy open office' or 'quiet library'")
            sys.exit(1)
        output = config.recommend_sensitivity(args.value)
        print(output)
        sys.exit(0)

    elif args.action == 'test':
        level = args.value or config.get_current_sensitivity()
        output = config.test_sensitivity(level)
        print(output)
        sys.exit(0)

if __name__ == '__main__':
    main()
