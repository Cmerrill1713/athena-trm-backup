"""
Feature Flags for Athena Router

Provides runtime feature toggling and configuration management.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlag:
    """Feature flag configuration."""
    name: str
    enabled: bool = False
    value: Any = None
    description: str = ""
    rollout_percentage: float = 100.0

    def is_enabled_for(self, user_id: Optional[str] = None) -> bool:
        """Check if feature is enabled for a specific user."""
        if not self.enabled:
            return False

        if self.rollout_percentage >= 100.0:
            return True

        if not user_id:
            return False

        # Simple rollout based on user ID hash
        user_hash = hash(user_id) % 100
        return user_hash < (self.rollout_percentage * 100)


class FeatureFlagManager:
    """Manages feature flags."""

    def __init__(self, config_path: Optional[Path] = None):
        self.flags: Dict[str, FeatureFlag] = {}
        self.config_path = config_path or Path(__file__).parent / "feature_flags.json"
        self.load_flags()

    def load_flags(self):
        """Load feature flags from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)

                for flag_data in data.get('flags', []):
                    flag = FeatureFlag(
                        name=flag_data['name'],
                        enabled=flag_data.get('enabled', False),
                        value=flag_data.get('value'),
                        description=flag_data.get('description', ''),
                        rollout_percentage=flag_data.get('rollout_percentage', 100.0)
                    )
                    self.flags[flag.name] = flag

                logger.info(f"Loaded {len(self.flags)} feature flags from {self.config_path}")

            except Exception as e:
                logger.error(f"Failed to load feature flags: {e}")

    def save_flags(self):
        """Save feature flags to file."""
        try:
            data = {
                'flags': [
                    {
                        'name': flag.name,
                        'enabled': flag.enabled,
                        'value': flag.value,
                        'description': flag.description,
                        'rollout_percentage': flag.rollout_percentage
                    }
                    for flag in self.flags.values()
                ]
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag."""
        return self.flags.get(name)

    def is_enabled(self, name: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature flag is enabled."""
        flag = self.get_flag(name)
        return flag.is_enabled_for(user_id) if flag else False

    def get_value(self, name: str, default: Any = None) -> Any:
        """Get the value of a feature flag."""
        flag = self.get_flag(name)
        return flag.value if flag else default

    def set_flag(self, name: str, enabled: bool = True, value: Any = None,
                 description: str = "", rollout_percentage: float = 100.0):
        """Set or update a feature flag."""
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            value=value,
            description=description,
            rollout_percentage=rollout_percentage
        )
        self.flags[name] = flag
        self.save_flags()
        logger.info(f"Set feature flag {name}: enabled={enabled}, rollout={rollout_percentage}%")

    def delete_flag(self, name: str):
        """Delete a feature flag."""
        if name in self.flags:
            del self.flags[name]
            self.save_flags()
            logger.info(f"Deleted feature flag {name}")

    def list_flags(self) -> Dict[str, Dict]:
        """List all feature flags."""
        return {
            name: {
                'enabled': flag.enabled,
                'value': flag.value,
                'description': flag.description,
                'rollout_percentage': flag.rollout_percentage
            }
            for name, flag in self.flags.items()
        }


# Pre-defined feature flags
DEFAULT_FLAGS = {
    'contrastive_routing': {
        'enabled': True,
        'description': 'Use contrastive domain embeddings for routing',
        'rollout_percentage': 100.0
    },
    'ab_testing': {
        'enabled': False,
        'description': 'Enable A/B testing framework',
        'rollout_percentage': 0.0
    },
    'cost_optimization': {
        'enabled': True,
        'description': 'Optimize for cost-efficiency over pure quality',
        'rollout_percentage': 100.0
    },
    'latency_monitoring': {
        'enabled': True,
        'description': 'Enhanced latency tracking and alerting',
        'rollout_percentage': 100.0
    },
    'fallback_caching': {
        'enabled': True,
        'description': 'Cache fallback router results',
        'rollout_percentage': 100.0
    }
}


def initialize_default_flags(manager: FeatureFlagManager):
    """Initialize default feature flags."""
    for flag_name, config in DEFAULT_FLAGS.items():
        if flag_name not in manager.flags:
            manager.set_flag(
                name=flag_name,
                enabled=config['enabled'],
                description=config['description'],
                rollout_percentage=config['rollout_percentage']
            )


# Global feature flag manager
feature_flag_manager = FeatureFlagManager()
initialize_default_flags(feature_flag_manager)

