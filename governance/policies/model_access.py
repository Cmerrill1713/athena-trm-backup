"""
Governance Policy Enforcement for Model Access

Enforces local-first policies and prevents unauthorized cloud usage.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ModelAccessPolicy:
    """Enforces model access governance policies."""

    def __init__(self, policy_file: Optional[Path] = None):
        self.policy_file = policy_file or Path(__file__).parent / "model_access.yaml"
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict[str, Any]:
        """Load policy from YAML file."""
        try:
            with open(self.policy_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            return {"rules": []}

    def check_access(self, target: str, model_hint: Optional[str] = None) -> bool:
        """
        Check if access to target is allowed under current policy.

        Args:
            target: Target backend ("local_mlx", "local_ollama", "cloud_frontier", etc.)
            model_hint: Optional model hint for context

        Returns:
            True if access is allowed, False if denied
        """
        rules = self.policy.get("rules", [])

        for rule in rules:
            if self._rule_matches(rule, target, model_hint):
                action = rule.get("action_on_violation", "BLOCK")
                if action in ["BLOCK", "ROLLBACK"]:
                    logger.warning(f"Policy violation: {rule['id']} blocks {target}")
                    return False

        return True

    def _rule_matches(self, rule: Dict[str, Any], target: str, model_hint: Optional[str]) -> bool:
        """Check if a rule matches the current request."""
        forbid_targets = rule.get("forbid_targets", [])
        if target not in forbid_targets:
            return False

        # Check conditions
        conditions = rule.get("when", [])
        for condition in conditions:
            if not self._check_condition(condition):
                return False

        return True

    def _check_condition(self, condition: Dict[str, Any]) -> bool:
        """Check if a condition is met."""
        condition_type = list(condition.keys())[0]
        condition_value = condition[condition_type]

        if condition_type == "env":
            # Environment variable check
            for env_condition in condition_value:
                key = env_condition.get("key")
                expected = env_condition.get("equals")
                actual = os.getenv(key)
                if actual != expected:
                    return False
            return True

        elif condition_type == "metric":
            # Metric check (placeholder - would integrate with Prometheus)
            # For now, assume metrics are available via environment or config
            return True

        elif condition_type == "duration":
            # Time-based conditions (placeholder)
            return True

        return False

    def get_violations(self) -> list:
        """Get list of policy violations (for monitoring)."""
        # Placeholder - would track actual violations
        return []

# Global policy enforcer
policy_enforcer = ModelAccessPolicy()

def check_access_policy(target: str, model_hint: Optional[str] = None) -> bool:
    """Convenience function to check model access policy."""
    return policy_enforcer.check_access(target, model_hint)
