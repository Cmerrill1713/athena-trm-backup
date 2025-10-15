"""
Governance Layer
================

Policy-level control over autonomous intelligence evolution.
Defines ethical boundaries, business constraints, and safety limits
for the self-evolving optimization network.

Features:
- Ethical policy enforcement preventing harmful strategies
- Business constraint alignment with organizational objectives
- Safety limits preventing system instability
- Compliance rules maintaining regulatory requirements
- Strategic objective guidance for beneficial evolution
- Human oversight and intervention capabilities
- Complete audit trail of governance decisions
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from .automated_strategy_generation import StrategyComponent, StrategyGenome
from .dynamic_constitutional_weighting import get_adaptive_governance_controller

logger = logging.getLogger(__name__)

class GovernanceLevel(Enum):
    """Levels of governance enforcement."""
    PERMISSIVE = "permissive"     # Allow with logging
    WARNING = "warning"          # Warn but allow
    BLOCKING = "blocking"        # Block violation
    TERMINATING = "terminating"   # Shut down system

class PolicyCategory(Enum):
    """Categories of governance policies."""
    ETHICAL = "ethical"
    BUSINESS = "business"
    SAFETY = "safety"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    RESOURCE = "resource"

@dataclass
class GovernancePolicy:
    """A governance policy with rules and enforcement."""
    policy_id: str
    category: PolicyCategory
    name: str
    description: str
    enforcement_level: GovernanceLevel
    conditions: List[Dict]  # Rule conditions to check
    actions: List[Dict]     # Actions to take on violation
    enabled: bool = True
    created_at: datetime = None
    last_modified: datetime = None
    violation_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_modified is None:
            self.last_modified = datetime.now()

class EthicalBoundaries:
    """
    Ethical constraints preventing harmful or biased strategies.

    Ensures AI evolution stays within moral and societal boundaries.
    """

    def __init__(self):
        self.forbidden_patterns = {
            'discrimination': [
                r'(?i)discriminat.*(race|gender|age|religion|ethnicity)',
                r'(?i)bias.*(group|class|category)',
                r'(?i)prefer.*(demographic|segment)'
            ],
            'manipulation': [
                r'(?i)manipulat.*(user|behavior|decision)',
                r'(?i)exploit.*(vulnerability|weakness)',
                r'(?i)coerc.*(choice|action)'
            ],
            'deception': [
                r'(?i)mislead.*(user|information)',
                r'(?i)fake.*(result|response)',
                r'(?i)decept.*(strategy|approach)'
            ],
            'privacy_violation': [
                r'(?i)bypass.*(privacy|consent)',
                r'(?i)leak.*(personal|private)',
                r'(?i)track.*(without.*consent|covertly)'
            ],
            'harmful_content': [
                r'(?i)generat.*(harmful|dangerous|illegal)',
                r'(?i)promot.*(violence|hate|crime)',
                r'(?i)encourag.*(self.*harm|illegal)'
            ]
        }

    def check_strategy_ethics(self, strategy_genome: StrategyGenome) -> Dict[str, Any]:
        """
        Check if a strategy violates ethical boundaries.

        Returns violations found and severity assessment.
        """
        violations = []
        severity_score = 0.0

        # Check component combinations for ethical concerns
        components_str = ' '.join(c.value for c in strategy_genome.components)

        for ethical_category, patterns in self.forbidden_patterns.items():
            for pattern in patterns:
                if re.search(pattern, components_str):
                    violations.append({
                        'category': ethical_category,
                        'pattern': pattern,
                        'severity': 'high',
                        'description': f'Ethical violation: {ethical_category}'
                    })
                    severity_score += 1.0

        # Check parameter values for concerning thresholds
        if strategy_genome.parameters.get('personalization_bias', 0) > 0.8:
            violations.append({
                'category': 'over_personalization',
                'severity': 'medium',
                'description': 'Excessive personalization may create filter bubbles'
            })
            severity_score += 0.5

        # Check for potential bias amplification
        diversity_components = [c for c in strategy_genome.components
                              if c in [StrategyComponent.DIVERSITY_PROMOTION]]
        personalization_components = [c for c in strategy_genome.components
                                    if c in [StrategyComponent.PERSONALIZATION]]

        if not diversity_components and personalization_components:
            violations.append({
                'category': 'bias_amplification',
                'severity': 'medium',
                'description': 'Personalization without diversity may amplify biases'
            })
            severity_score += 0.3

        return {
            'violations': violations,
            'severity_score': severity_score,
            'ethical_clearance': severity_score < 0.5,
            'requires_review': severity_score >= 0.3
        }

class BusinessConstraints:
    """
    Business alignment constraints ensuring strategies support organizational objectives.
    """

    def __init__(self):
        self.business_objectives = {
            'user_satisfaction': {'min_threshold': 0.7, 'weight': 0.4},
            'business_value': {'min_threshold': 0.6, 'weight': 0.3},
            'operational_efficiency': {'min_threshold': 0.8, 'weight': 0.3}
        }

    def evaluate_business_alignment(self, strategy_genome: StrategyGenome,
                                  performance_metrics: Dict) -> Dict[str, Any]:
        """
        Evaluate how well a strategy aligns with business objectives.
        """
        alignment_scores = {}

        for objective, config in self.business_objectives.items():
            # Simplified business alignment calculation
            if objective == 'user_satisfaction':
                # High personalization and diversity scores well
                personalization = 1.0 if StrategyComponent.PERSONALIZATION in strategy_genome.components else 0.0
                diversity = 1.0 if StrategyComponent.DIVERSITY_PROMOTION in strategy_genome.components else 0.0
                score = (personalization + diversity) / 2.0

            elif objective == 'business_value':
                # Cross-encoder and neural components indicate sophistication
                ce_present = 1.0 if StrategyComponent.CROSS_ENCODER in strategy_genome.components else 0.0
                neural_present = 1.0 if StrategyComponent.NEURAL_RESCORING in strategy_genome.components else 0.0
                score = (ce_present + neural_present) / 2.0

            elif objective == 'operational_efficiency':
                # Lower complexity is more efficient
                complexity_penalty = min(strategy_genome.complexity_score / 5.0, 1.0)
                score = 1.0 - complexity_penalty

            alignment_scores[objective] = score

        # Overall business alignment score
        overall_alignment = sum(
            score * self.business_objectives[obj]['weight']
            for obj, score in alignment_scores.items()
        )

        # Check if strategy meets minimum thresholds
        meets_thresholds = all(
            alignment_scores[obj] >= config['min_threshold']
            for obj, config in self.business_objectives.items()
        )

        return {
            'alignment_scores': alignment_scores,
            'overall_alignment': overall_alignment,
            'meets_thresholds': meets_thresholds,
            'business_clearance': overall_alignment >= 0.7
        }

class SafetyLimits:
    """
    Safety constraints preventing system instability and harm.
    """

    def __init__(self):
        self.safety_limits = {
            'performance_variance': {'max_allowed': 0.2, 'description': 'Maximum allowed performance variance'},
            'latency_impact': {'max_allowed': 100, 'description': 'Maximum latency increase (ms)'},
            'resource_usage': {'max_allowed': 2.0, 'description': 'Maximum resource usage multiplier'},
            'error_rate_increase': {'max_allowed': 0.05, 'description': 'Maximum error rate increase'},
            'rollback_complexity': {'max_allowed': 3, 'description': 'Maximum steps to rollback'}
        }

    def check_safety_limits(self, strategy_genome: StrategyGenome,
                          system_metrics: Dict) -> Dict[str, Any]:
        """
        Check if a strategy stays within safety limits.
        """
        violations = []
        safety_score = 1.0  # Start with perfect safety

        # Check complexity vs rollback capability
        complexity_score = strategy_genome.complexity_score
        if complexity_score > self.safety_limits['rollback_complexity']['max_allowed']:
            violations.append({
                'limit': 'rollback_complexity',
                'current_value': complexity_score,
                'max_allowed': self.safety_limits['rollback_complexity']['max_allowed'],
                'severity': 'high'
            })
            safety_score -= 0.3

        # Check resource implications
        resource_multiplier = 1.0 + (complexity_score * 0.1)  # Complexity increases resource usage
        if resource_multiplier > self.safety_limits['resource_usage']['max_allowed']:
            violations.append({
                'limit': 'resource_usage',
                'current_value': resource_multiplier,
                'max_allowed': self.safety_limits['resource_usage']['max_allowed'],
                'severity': 'medium'
            })
            safety_score -= 0.2

        # Check latency implications
        latency_increase = complexity_score * 20  # Rough estimate: 20ms per complexity point
        if latency_increase > self.safety_limits['latency_impact']['max_allowed']:
            violations.append({
                'limit': 'latency_impact',
                'current_value': latency_increase,
                'max_allowed': self.safety_limits['latency_impact']['max_allowed'],
                'severity': 'medium'
            })
            safety_score -= 0.2

        return {
            'violations': violations,
            'safety_score': max(0.0, safety_score),
            'safety_clearance': len(violations) == 0,
            'requires_safety_review': safety_score < 0.8
        }

class ComplianceRules:
    """
    Regulatory and compliance constraints.
    """

    def __init__(self):
        self.compliance_frameworks = {
            'gdpr': {
                'data_minimization': 'Minimize data processing',
                'purpose_limitation': 'Use data only for intended purpose',
                'consent': 'Require user consent for personalization'
            },
            'ccpa': {
                'right_to_know': 'Allow users to know what data is collected',
                'right_to_delete': 'Allow users to delete their data',
                'opt_out': 'Allow users to opt out of data sharing'
            },
            'fairness': {
                'disparate_impact': 'Avoid disproportionate negative effects',
                'equal_opportunity': 'Ensure equal performance across groups',
                'transparency': 'Explain how decisions are made'
            }
        }

    def check_compliance(self, strategy_genome: StrategyGenome) -> Dict[str, Any]:
        """
        Check if strategy complies with regulatory requirements.
        """
        compliance_issues = []
        compliance_score = 1.0

        # GDPR compliance checks
        if StrategyComponent.PERSONALIZATION in strategy_genome.components:
            personalization_bias = strategy_genome.parameters.get('personalization_bias', 0.15)
            if personalization_bias > 0.5:
                compliance_issues.append({
                    'framework': 'gdpr',
                    'rule': 'consent',
                    'issue': 'High personalization bias may require explicit consent',
                    'severity': 'medium'
                })
                compliance_score -= 0.2

        # CCPA compliance checks
        if StrategyComponent.USER_FEEDBACK_INTEGRATION in strategy_genome.components:
            compliance_issues.append({
                'framework': 'ccpa',
                'rule': 'right_to_know',
                'issue': 'User feedback integration requires data disclosure transparency',
                'severity': 'low'
            })
            compliance_score -= 0.1

        # Fairness checks
        has_personalization = StrategyComponent.PERSONALIZATION in strategy_genome.components
        has_diversity = StrategyComponent.DIVERSITY_PROMOTION in strategy_genome.components

        if has_personalization and not has_diversity:
            compliance_issues.append({
                'framework': 'fairness',
                'rule': 'disparate_impact',
                'issue': 'Personalization without diversity may create unfair outcomes',
                'severity': 'high'
            })
            compliance_score -= 0.3

        return {
            'compliance_issues': compliance_issues,
            'compliance_score': max(0.0, compliance_score),
            'compliance_clearance': len(compliance_issues) == 0,
            'requires_compliance_review': compliance_score < 0.9
        }

class GovernanceEngine:
    """
    Central governance engine enforcing all policies and constraints.
    """

    def __init__(self):
        self.ethical_boundaries = EthicalBoundaries()
        self.business_constraints = BusinessConstraints()
        self.safety_limits = SafetyLimits()
        self.compliance_rules = ComplianceRules()

        # Dynamic weighting controller
        self.adaptive_controller = get_adaptive_governance_controller()

        # Default policies
        self.policies = self._load_default_policies()

        # Governance state
        self.governance_log: List[Dict] = []
        self.intervention_history: List[Dict] = []

    def _load_default_policies(self) -> List[GovernancePolicy]:
        """Load default governance policies."""
        return [
            GovernancePolicy(
                policy_id="ethical_no_discrimination",
                category=PolicyCategory.ETHICAL,
                name="No Discrimination",
                description="Prevent strategies that discriminate based on protected characteristics",
                enforcement_level=GovernanceLevel.BLOCKING,
                conditions=[{"type": "ethical_check", "max_severity": 0.0}],
                actions=[{"type": "block_deployment", "reason": "Ethical violation"}]
            ),
            GovernancePolicy(
                policy_id="business_minimum_alignment",
                category=PolicyCategory.BUSINESS,
                name="Business Alignment",
                description="Ensure strategies align with business objectives",
                enforcement_level=GovernanceLevel.WARNING,
                conditions=[{"type": "business_alignment", "min_score": 0.6}],
                actions=[{"type": "flag_for_review", "reason": "Low business alignment"}]
            ),
            GovernancePolicy(
                policy_id="safety_performance_stability",
                category=PolicyCategory.SAFETY,
                name="Performance Stability",
                description="Prevent strategies that cause performance instability",
                enforcement_level=GovernanceLevel.BLOCKING,
                conditions=[{"type": "safety_check", "min_safety_score": 0.8}],
                actions=[{"type": "block_deployment", "reason": "Safety violation"}]
            ),
            GovernancePolicy(
                policy_id="compliance_gdpr_ccpa",
                category=PolicyCategory.COMPLIANCE,
                name="Privacy Compliance",
                description="Ensure GDPR and CCPA compliance",
                enforcement_level=GovernanceLevel.BLOCKING,
                conditions=[{"type": "compliance_check", "min_compliance_score": 0.9}],
                actions=[{"type": "block_deployment", "reason": "Compliance violation"}]
            ),
            GovernancePolicy(
                policy_id="performance_minimum_improvement",
                category=PolicyCategory.PERFORMANCE,
                name="Minimum Performance",
                description="Require minimum performance improvement",
                enforcement_level=GovernanceLevel.WARNING,
                conditions=[{"type": "performance_check", "min_improvement": 0.05}],
                actions=[{"type": "flag_for_review", "reason": "Insufficient improvement"}]
            ),
            GovernancePolicy(
                policy_id="resource_efficiency",
                category=PolicyCategory.RESOURCE,
                name="Resource Efficiency",
                description="Ensure strategies don't waste resources",
                enforcement_level=GovernanceLevel.WARNING,
                conditions=[{"type": "resource_check", "max_complexity": 3.0}],
                actions=[{"type": "optimize_parameters", "reason": "High resource usage"}]
            )
        ]

    def evaluate_strategy_governance(self, strategy_genome: StrategyGenome,
                                       context: Dict = None) -> Dict[str, Any]:
        """
        Evaluate a strategy using dynamic constitutional governance with adaptive weighting.

        This now uses the adaptive controller for dynamic weighting based on system state.
        """
        # Use the adaptive controller for dynamic weighting
        assessment = self.adaptive_controller.evaluate_strategy_with_dynamic_weighting(strategy_genome, context)

        # Log the governance decision for audit trail
        self.governance_log.append({
            'assessment': assessment,
            'strategy_genome': strategy_genome,
            'context': context,
            'timestamp': datetime.now()
        })

        # Keep log size manageable
        if len(self.governance_log) > 1000:
            self.governance_log = self.governance_log[-1000:]

        return assessment

    def _check_policy_violations(self, strategy_genome: StrategyGenome,
                               assessment: Dict) -> List[Dict]:
        """Check which policies are violated by this strategy."""
        violations = []

        for policy in self.policies:
            if not policy.enabled:
                continue

            violation = self._evaluate_policy(policy, strategy_genome, assessment)
            if violation:
                violations.append({
                    'policy': policy,
                    'violation_details': violation
                })
                policy.violation_count += 1

        return violations

    def _evaluate_policy(self, policy: GovernancePolicy, strategy_genome: StrategyGenome,
                        assessment: Dict) -> Optional[Dict]:
        """Evaluate if a policy is violated."""
        # Simplified policy evaluation - in practice this would be more sophisticated
        for condition in policy.conditions:
            condition_type = condition.get('type')

            if condition_type == 'ethical_check':
                if assessment['ethical_assessment']['severity_score'] > condition.get('max_severity', 0):
                    return {'condition': condition, 'actual_value': assessment['ethical_assessment']['severity_score']}

            elif condition_type == 'business_alignment':
                if assessment['business_assessment']['overall_alignment'] < condition.get('min_score', 0):
                    return {'condition': condition, 'actual_value': assessment['business_assessment']['overall_alignment']}

            elif condition_type == 'safety_check':
                if assessment['safety_assessment']['safety_score'] < condition.get('min_safety_score', 0):
                    return {'condition': condition, 'actual_value': assessment['safety_assessment']['safety_score']}

            elif condition_type == 'compliance_check':
                if assessment['compliance_assessment']['compliance_score'] < condition.get('min_compliance_score', 0):
                    return {'condition': condition, 'actual_value': assessment['compliance_assessment']['compliance_score']}

        return None

    def _generate_recommendations(self, assessment: Dict) -> List[str]:
        """Generate recommendations based on governance assessment."""
        recommendations = []

        if assessment['ethical_assessment']['severity_score'] > 0:
            recommendations.append("Consider adding diversity components to reduce bias risks")

        if assessment['business_assessment']['overall_alignment'] < 0.7:
            recommendations.append("Review strategy alignment with user satisfaction objectives")

        if assessment['safety_assessment']['safety_score'] < 0.8:
            recommendations.append("Simplify strategy to reduce complexity and resource usage")

        if assessment['compliance_assessment']['compliance_score'] < 0.9:
            recommendations.append("Add transparency measures for GDPR/CCPA compliance")

        if assessment['governance_score'] < 0.8:
            recommendations.append("Strategy requires human review before deployment")

        return recommendations

    def add_custom_policy(self, policy: GovernancePolicy):
        """Add a custom governance policy."""
        # Check for duplicate policy IDs
        if any(p.policy_id == policy.policy_id for p in self.policies):
            raise ValueError(f"Policy with ID {policy.policy_id} already exists")

        self.policies.append(policy)
        logger.info(f"Added custom governance policy: {policy.policy_id}")

    def update_policy(self, policy_id: str, updates: Dict):
        """Update an existing policy."""
        for policy in self.policies:
            if policy.policy_id == policy_id:
                for key, value in updates.items():
                    if hasattr(policy, key):
                        setattr(policy, key, value)
                policy.last_modified = datetime.now()
                logger.info(f"Updated governance policy: {policy_id}")
                return

        raise ValueError(f"Policy {policy_id} not found")

    def get_governance_stats(self) -> Dict:
        """Get governance statistics."""
        total_assessments = len(self.governance_log)
        clearance_rate = sum(1 for log in self.governance_log
                           if log['assessment']['overall_clearance']) / max(total_assessments, 1)

        policy_stats = {}
        for policy in self.policies:
            policy_stats[policy.policy_id] = {
                'violations': policy.violation_count,
                'enabled': policy.enabled,
                'category': policy.category.value
            }

        return {
            'total_assessments': total_assessments,
            'clearance_rate': clearance_rate,
            'policy_violations': policy_stats,
            'recent_assessments': len([log for log in self.governance_log
                                     if log['timestamp'] > datetime.now() - timedelta(hours=24)])
        }

    def request_human_intervention(self, strategy_id: str, reason: str, assessment: Dict):
        """Request human intervention for a governance decision."""
        intervention = {
            'strategy_id': strategy_id,
            'reason': reason,
            'assessment': assessment,
            'timestamp': datetime.now(),
            'status': 'pending'
        }

        self.intervention_history.append(intervention)
        logger.warning(f"Human intervention requested for strategy {strategy_id}: {reason}")

    def approve_with_conditions(self, strategy_id: str, conditions: List[str]) -> bool:
        """Approve a strategy with specific conditions."""
        # Find the intervention
        for intervention in self.intervention_history:
            if intervention['strategy_id'] == strategy_id and intervention['status'] == 'pending':
                intervention['status'] = 'approved_with_conditions'
                intervention['conditions'] = conditions
                intervention['approved_at'] = datetime.now()
                logger.info(f"Strategy {strategy_id} approved with conditions: {conditions}")
                return True

        return False

    def reject_strategy(self, strategy_id: str, reason: str) -> bool:
        """Reject a strategy permanently."""
        for intervention in self.intervention_history:
            if intervention['strategy_id'] == strategy_id and intervention['status'] == 'pending':
                intervention['status'] = 'rejected'
                intervention['rejection_reason'] = reason
                intervention['rejected_at'] = datetime.now()
                logger.info(f"Strategy {strategy_id} rejected: {reason}")
                return True

        return False

# Global governance engine instance
_governance_engine = None

def get_governance_engine() -> GovernanceEngine:
    """Get or create global governance engine instance."""
    global _governance_engine
    if _governance_engine is None:
        _governance_engine = GovernanceEngine()
    return _governance_engine
