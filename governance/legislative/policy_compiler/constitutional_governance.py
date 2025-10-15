#!/usr/bin/env python3
"""
Constitutional Governance for Federated Bandit Learning
=======================================================

Ensures only ethically compliant routing strategies propagate through the federation.

Features:
- Constitutional validation of bandit strategies
- Ethical compliance checking before federation
- Governance audit trails and monitoring
- Safe auto-evolution mode
- Constitutional AI integration
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class GovernanceViolation(Enum):
    """Types of constitutional violations."""
    DISCRIMINATORY_ROUTING = "discriminatory_routing"
    PRIVACY_VIOLATION = "privacy_violation"
    UNFAIR_BIAS = "unfair_bias"
    RESOURCE_MONOPOLIZATION = "resource_monopolization"
    UNSTABLE_ROUTING = "unstable_routing"
    MALICIOUS_EXPLOITATION = "malicious_exploitation"

@dataclass
class ConstitutionalRule:
    """A constitutional rule for routing strategy validation."""
    rule_id: str
    name: str
    description: str
    violation_type: GovernanceViolation
    severity: str = "medium"  # low, medium, high, critical
    enabled: bool = True

    def validate(self, strategy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate a strategy against this rule. Returns (compliant, explanation)."""
        # Implement rule-specific validation logic
        if self.rule_id == "no_discriminatory_routing":
            return self._check_discriminatory_routing(strategy_data)
        elif self.rule_id == "fair_resource_allocation":
            return self._check_resource_allocation(strategy_data)
        elif self.rule_id == "stable_routing_behavior":
            return self._check_routing_stability(strategy_data)
        elif self.rule_id == "privacy_preserving":
            return self._check_privacy_compliance(strategy_data)
        else:
            return True, "Rule not implemented"

    def _check_discriminatory_routing(self, strategy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for discriminatory routing patterns."""
        arm_performance = strategy_data.get('arm_performance', {})

        # Check for extreme performance disparities (potential bias)
        win_rates = [arm.get('local_win_rate', 0) for arm in arm_performance.values()]
        if win_rates and max(win_rates) - min(win_rates) > 0.8:  # 80% difference
            return False, "Extreme performance disparity may indicate discriminatory routing"

        return True, "No discriminatory patterns detected"

    def _check_resource_allocation(self, strategy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for fair resource allocation."""
        arm_performance = strategy_data.get('arm_performance', {})

        # Check that no single arm monopolizes traffic
        exploration_rates = [arm.get('exploration_rate', 0) for arm in arm_performance.values()]
        if exploration_rates and max(exploration_rates) > 0.5:  # >50% exploration
            return False, "Single arm monopolizing exploration resources"

        return True, "Resource allocation appears fair"

    def _check_routing_stability(self, strategy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for routing stability."""
        history_size = strategy_data.get('history_size', 0)
        exploration_rate = strategy_data.get('exploration_rate_recent', 0)

        # High exploration with low history may indicate instability
        if history_size < 100 and exploration_rate > 0.3:
            return False, "Insufficient history for high exploration rate"

        return True, "Routing behavior appears stable"

    def _check_privacy_compliance(self, strategy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check privacy compliance."""
        federation_enabled = strategy_data.get('federation_enabled', False)
        privacy_epsilon = strategy_data.get('federation_stats', {}).get('privacy_epsilon', 0)

        if federation_enabled and privacy_epsilon > 1.0:
            return False, f"Privacy budget ε={privacy_epsilon} too permissive"

        return True, "Privacy compliance maintained"

@dataclass
class ValidationResult:
    """Result of constitutional validation."""
    compliant: bool
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    strategy_hash: str = ""

    def add_violation(self, rule: ConstitutionalRule, explanation: str):
        """Add a violation to the result."""
        self.violations.append({
            'rule_id': rule.rule_id,
            'violation_type': rule.violation_type.value,
            'severity': rule.severity,
            'explanation': explanation
        })
        if rule.severity in ['high', 'critical']:
            self.compliant = False

    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)

class ConstitutionalValidator:
    """
    Validates routing strategies against constitutional guidelines.

    Ensures only ethically compliant strategies propagate through federation.
    """

    def __init__(self):
        self.constitutional_rules = self._load_constitutional_rules()
        self.validation_history: List[ValidationResult] = []
        self.max_history = 10000

    def _load_constitutional_rules(self) -> List[ConstitutionalRule]:
        """Load constitutional rules from configuration."""
        # Default constitutional rules for RAG routing
        return [
            ConstitutionalRule(
                rule_id="no_discriminatory_routing",
                name="No Discriminatory Routing",
                description="Prevent routing strategies that discriminate based on query content",
                violation_type=GovernanceViolation.DISCRIMINATORY_ROUTING,
                severity="high"
            ),
            ConstitutionalRule(
                rule_id="fair_resource_allocation",
                name="Fair Resource Allocation",
                description="Ensure no single routing arm monopolizes system resources",
                violation_type=GovernanceViolation.RESOURCE_MONOPOLIZATION,
                severity="medium"
            ),
            ConstitutionalRule(
                rule_id="stable_routing_behavior",
                name="Stable Routing Behavior",
                description="Prevent unstable routing that causes system thrashing",
                violation_type=GovernanceViolation.UNSTABLE_ROUTING,
                severity="medium"
            ),
            ConstitutionalRule(
                rule_id="privacy_preserving",
                name="Privacy Preserving",
                description="Ensure federated learning maintains privacy guarantees",
                violation_type=GovernanceViolation.PRIVACY_VIOLATION,
                severity="critical"
            )
        ]

    def validate_strategy(self, strategy_data: Dict[str, Any],
                         strategy_hash: Optional[str] = None) -> ValidationResult:
        """
        Validate a routing strategy against constitutional rules.

        Args:
            strategy_data: Complete strategy information from bandit router
            strategy_hash: Optional hash of the strategy for tracking

        Returns:
            ValidationResult with compliance status and any violations
        """
        result = ValidationResult(
            compliant=True,
            strategy_hash=strategy_hash or self._hash_strategy(strategy_data)
        )

        # Apply each constitutional rule
        for rule in self.constitutional_rules:
            if not rule.enabled:
                continue

            try:
                compliant, explanation = rule.validate(strategy_data)
                if not compliant:
                    result.add_violation(rule, explanation)
                elif "warning" in explanation.lower():
                    result.add_warning(explanation)
            except Exception as e:
                result.add_violation(
                    ConstitutionalRule(
                        rule_id="validation_error",
                        name="Validation Error",
                        description="Error during constitutional validation",
                        violation_type=GovernanceViolation.MALICIOUS_EXPLOITATION,
                        severity="medium"
                    ),
                    f"Validation failed: {str(e)}"
                )

        # Additional cross-rule validations
        self._validate_cross_rules(strategy_data, result)

        # Record validation result
        self.validation_history.append(result)
        if len(self.validation_history) > self.max_history:
            self.validation_history.pop(0)

        return result

    def _validate_cross_rules(self, strategy_data: Dict[str, Any], result: ValidationResult):
        """Apply cross-rule validations."""
        # Check for concerning patterns across multiple rules
        federation_enabled = strategy_data.get('federation_enabled', False)
        exploration_rate = strategy_data.get('exploration_rate_recent', 0)
        history_size = strategy_data.get('history_size', 0)

        # High exploration with federation + small history = risky
        if (federation_enabled and exploration_rate > 0.4 and history_size < 500):
            result.add_warning("High exploration rate with federation may cause instability")

        # Check for extreme performance variations
        arm_performance = strategy_data.get('arm_performance', {})
        if len(arm_performance) > 1:
            win_rates = [arm.get('local_win_rate', 0) for arm in arm_performance.values() if arm.get('local_win_rate', 0) > 0]
            if win_rates and (max(win_rates) - min(win_rates) > 0.5):
                result.add_warning("Significant performance variation across routing arms")

    def _hash_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """Create a hash of the strategy for tracking."""
        # Create a normalized representation for hashing
        normalized = json.dumps(strategy_data, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get_governance_stats(self) -> Dict[str, Any]:
        """Get comprehensive governance statistics."""
        total_validations = len(self.validation_history)
        compliant_validations = sum(1 for v in self.validation_history if v.compliant)
        violation_counts = {}

        for result in self.validation_history:
            for violation in result.violations:
                rule_id = violation['rule_id']
                violation_counts[rule_id] = violation_counts.get(rule_id, 0) + 1

        compliance_rate = compliant_validations / total_validations if total_validations > 0 else 1.0

        return {
            'total_validations': total_validations,
            'compliance_rate': compliance_rate,
            'most_common_violations': sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'validation_history_size': len(self.validation_history),
            'rules_active': len([r for r in self.constitutional_rules if r.enabled])
        }

    def is_strategy_constitutional(self, strategy_data: Dict[str, Any]) -> bool:
        """Quick check if a strategy is constitutional."""
        result = self.validate_strategy(strategy_data)
        return result.compliant

# Global constitutional validator instance
constitutional_validator = ConstitutionalValidator()

def validate_routing_strategy(strategy_data: Dict[str, Any]) -> ValidationResult:
    """High-level interface for constitutional validation."""
    return constitutional_validator.validate_strategy(strategy_data)

def is_strategy_constitutional(strategy_data: Dict[str, Any]) -> bool:
    """Quick constitutional compliance check."""
    return constitutional_validator.is_strategy_constitutional(strategy_data)

if __name__ == "__main__":
    # Demo constitutional governance
    print("🛡️ Constitutional Governance Demo")
    print("=" * 50)

    # Sample strategy data (compliant)
    compliant_strategy = {
        'federation_enabled': True,
        'exploration_rate_recent': 0.15,
        'history_size': 1000,
        'arm_performance': {
            'conservative_ce': {'local_win_rate': 0.75, 'exploration_rate': 0.05},
            'aggressive_ce': {'local_win_rate': 0.70, 'exploration_rate': 0.15},
            'exploratory': {'local_win_rate': 0.55, 'exploration_rate': 0.30}
        },
        'federation_stats': {'privacy_epsilon': 0.5}
    }

    # Validate compliant strategy
    result1 = validate_routing_strategy(compliant_strategy)
    print(f"✅ Compliant strategy: {result1.compliant}")
    print(f"   Violations: {len(result1.violations)}")
    print(f"   Warnings: {len(result1.warnings)}")

    # Sample strategy data (non-compliant - privacy violation)
    non_compliant_strategy = compliant_strategy.copy()
    non_compliant_strategy['federation_stats'] = {'privacy_epsilon': 2.0}  # Too permissive

    result2 = validate_routing_strategy(non_compliant_strategy)
    print(f"❌ Non-compliant strategy: {result2.compliant}")
    print(f"   Violations: {len(result2.violations)}")
    if result2.violations:
        print(f"   First violation: {result2.violations[0]['explanation']}")

    # Governance stats
    stats = constitutional_validator.get_governance_stats()
    print("\n📊 Governance Stats:")
    print(f"   Total validations: {stats['total_validations']}")
    print(f"   Compliance rate: {stats['compliance_rate']:.1%}")
    print(f"   Rules active: {stats['rules_active']}")

    print("\n🛡️ Constitutional governance active!")
    print("   Only compliant strategies propagate through federation.")
