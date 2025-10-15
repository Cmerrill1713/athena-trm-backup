"""
Dynamic Constitutional Weighting
=================================

Adaptive governance that automatically adjusts ethical, business, safety,
and performance priorities based on system state and performance metrics.

Features:
- Context-aware governance weighting based on operational phase
- Performance-based adaptation of constitutional priorities
- Risk-aware policy adjustment during different system states
- Meta-learning for optimal governance weighting strategies
- Automatic constitutional evolution based on system performance
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from .governance_layer import get_governance_engine

logger = logging.getLogger(__name__)

@dataclass
class ConstitutionalWeights:
    """Dynamic weighting for constitutional governance dimensions."""
    ethical_weight: float = 0.25
    business_weight: float = 0.30
    safety_weight: float = 0.25
    compliance_weight: float = 0.20

    def __post_init__(self):
        self._normalize_weights()

    def _normalize_weights(self):
        """Ensure weights sum to 1.0."""
        total = self.ethical_weight + self.business_weight + self.safety_weight + self.compliance_weight
        if total > 0:
            self.ethical_weight /= total
            self.business_weight /= total
            self.safety_weight /= total
            self.compliance_weight /= total

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            'ethical_weight': self.ethical_weight,
            'business_weight': self.business_weight,
            'safety_weight': self.safety_weight,
            'compliance_weight': self.compliance_weight
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'ConstitutionalWeights':
        """Create from dictionary."""
        return cls(
            ethical_weight=data.get('ethical_weight', 0.25),
            business_weight=data.get('business_weight', 0.30),
            safety_weight=data.get('safety_weight', 0.25),
            compliance_weight=data.get('compliance_weight', 0.20)
        )

@dataclass
class SystemState:
    """Current state of the constitutional AI system."""
    timestamp: datetime

    # Performance metrics
    avg_judge_score: float = 0.0
    error_rate: float = 0.0
    latency_p95: float = 0.0
    strategy_failure_rate: float = 0.0

    # Governance metrics
    governance_clearance_rate: float = 1.0
    human_intervention_rate: float = 0.0
    ethical_violation_rate: float = 0.0
    compliance_violation_rate: float = 0.0

    # Operational metrics
    active_strategies: int = 0
    total_queries_processed: int = 0
    system_load: float = 0.0  # 0-1 scale

    # Environmental factors
    deployment_phase: str = "production"  # development, staging, production
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    business_priority: str = "balanced"  # performance, business, safety, innovation

    def get_state_vector(self) -> torch.Tensor:
        """Convert state to feature vector for weighting decisions."""
        return torch.tensor([
            self.avg_judge_score,           # Performance indicator
            self.error_rate,                # Reliability indicator
            self.latency_p95 / 1000,       # Speed indicator (normalized)
            self.strategy_failure_rate,     # Stability indicator
            self.governance_clearance_rate, # Governance health
            self.human_intervention_rate,   # Oversight burden
            self.ethical_violation_rate,    # Ethical risk
            self.compliance_violation_rate, # Compliance risk
            self.active_strategies / 10,    # Complexity indicator (normalized)
            self.total_queries_processed / 10000,  # Scale indicator (normalized)
            self.system_load,               # Load indicator
            # Categorical encodings
            1.0 if self.deployment_phase == "production" else 0.0,
            1.0 if self.deployment_phase == "staging" else 0.0,
            1.0 if self.risk_tolerance == "conservative" else 0.0,
            1.0 if self.risk_tolerance == "aggressive" else 0.0,
            1.0 if self.business_priority == "performance" else 0.0,
            1.0 if self.business_priority == "safety" else 0.0,
            1.0 if self.business_priority == "innovation" else 0.0
        ], dtype=torch.float32)

class ConstitutionalStateEvaluator:
    """
    Evaluates current system state to determine appropriate governance weighting.
    """

    def __init__(self):
        self.state_history: List[SystemState] = []
        self.state_window_hours = 24

    def evaluate_current_state(self, context: Dict[str, Any]) -> SystemState:
        """
        Evaluate the current system state from available metrics and context.
        """
        # Extract metrics from context (would come from monitoring systems)
        performance_metrics = context.get('performance_metrics', {})
        governance_metrics = context.get('governance_metrics', {})
        operational_metrics = context.get('operational_metrics', {})
        environmental_factors = context.get('environmental_factors', {})

        state = SystemState(
            timestamp=datetime.now(),
            avg_judge_score=performance_metrics.get('avg_judge_score', 7.0),
            error_rate=performance_metrics.get('error_rate', 0.01),
            latency_p95=performance_metrics.get('latency_p95', 800),
            strategy_failure_rate=performance_metrics.get('strategy_failure_rate', 0.02),
            governance_clearance_rate=governance_metrics.get('clearance_rate', 0.95),
            human_intervention_rate=governance_metrics.get('human_intervention_rate', 0.03),
            ethical_violation_rate=governance_metrics.get('ethical_violation_rate', 0.005),
            compliance_violation_rate=governance_metrics.get('compliance_violation_rate', 0.01),
            active_strategies=operational_metrics.get('active_strategies', 5),
            total_queries_processed=operational_metrics.get('total_queries_processed', 1000),
            system_load=operational_metrics.get('system_load', 0.3),
            deployment_phase=environmental_factors.get('deployment_phase', 'production'),
            risk_tolerance=environmental_factors.get('risk_tolerance', 'moderate'),
            business_priority=environmental_factors.get('business_priority', 'balanced')
        )

        # Store in history
        self.state_history.append(state)

        # Keep recent history
        cutoff = datetime.now() - timedelta(hours=self.state_window_hours)
        self.state_history = [s for s in self.state_history if s.timestamp > cutoff]

        return state

    def detect_system_phase(self, state: SystemState) -> str:
        """
        Detect the current operational phase based on system state.
        """
        # High-risk indicators
        high_risk = (
            state.error_rate > 0.05 or
            state.strategy_failure_rate > 0.1 or
            state.ethical_violation_rate > 0.02 or
            state.compliance_violation_rate > 0.05
        )

        # High-load indicators
        high_load = (
            state.system_load > 0.8 or
            state.latency_p95 > 2000 or
            state.total_queries_processed > 50000  # High volume
        )

        # Innovation phase (good performance, low risk)
        innovation_phase = (
            state.avg_judge_score > 7.5 and
            state.error_rate < 0.01 and
            state.governance_clearance_rate > 0.98
        )

        if high_risk:
            return "crisis_recovery"
        elif high_load:
            return "high_load"
        elif innovation_phase:
            return "innovation"
        elif state.deployment_phase == "development":
            return "experimental"
        else:
            return "normal_operations"

class DynamicWeightingEngine:
    """
    Engine for calculating optimal constitutional weights based on system state.
    """

    def __init__(self):
        self.phase_weightings = self._define_phase_weightings()
        self.weighting_history: List[Tuple[SystemState, ConstitutionalWeights]] = []
        self.meta_learner = self._create_meta_learner()

    def _define_phase_weightings(self) -> Dict[str, ConstitutionalWeights]:
        """Define standard weightings for different operational phases."""
        return {
            # Crisis: Prioritize safety and ethics
            "crisis_recovery": ConstitutionalWeights(
                ethical_weight=0.40,    # High ethical priority
                business_weight=0.10,   # Low business priority
                safety_weight=0.40,     # High safety priority
                compliance_weight=0.10  # Moderate compliance
            ),

            # High load: Prioritize safety and performance
            "high_load": ConstitutionalWeights(
                ethical_weight=0.20,
                business_weight=0.20,
                safety_weight=0.45,     # Highest safety priority
                compliance_weight=0.15
            ),

            # Innovation: Balanced with performance focus
            "innovation": ConstitutionalWeights(
                ethical_weight=0.20,
                business_weight=0.35,   # Higher business priority
                safety_weight=0.20,
                compliance_weight=0.25
            ),

            # Experimental: Conservative with high governance
            "experimental": ConstitutionalWeights(
                ethical_weight=0.30,
                business_weight=0.15,
                safety_weight=0.30,
                compliance_weight=0.25
            ),

            # Normal operations: Balanced approach
            "normal_operations": ConstitutionalWeights(
                ethical_weight=0.25,
                business_weight=0.30,
                safety_weight=0.25,
                compliance_weight=0.20
            )
        }

    def _create_meta_learner(self) -> nn.Module:
        """Create neural network for meta-learning optimal weightings."""
        return nn.Sequential(
            nn.Linear(19, 32),  # Input: state vector (17 features + 2 padding)
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 4),   # Output: 4 weight values
            nn.Softmax(dim=1)   # Ensure weights sum to 1
        )

    def calculate_optimal_weights(self, state: SystemState) -> ConstitutionalWeights:
        """
        Calculate optimal constitutional weights for the current system state.
        """
        # Detect operational phase
        phase_evaluator = ConstitutionalStateEvaluator()
        phase = phase_evaluator.detect_system_phase(state)

        # Start with phase-based baseline weights
        baseline_weights = self.phase_weightings.get(phase, self.phase_weightings["normal_operations"])

        # Use meta-learner for refinement if available
        if len(self.weighting_history) > 10:
            refined_weights = self._refine_weights_with_meta_learning(state, baseline_weights)
        else:
            refined_weights = baseline_weights

        # Apply risk-based adjustments
        final_weights = self._apply_risk_adjustments(state, refined_weights)

        # Store for learning
        self.weighting_history.append((state, final_weights))

        # Keep recent history
        if len(self.weighting_history) > 100:
            self.weighting_history = self.weighting_history[-100:]

        logger.info(f"Calculated weights for phase '{phase}': "
                   f"E:{final_weights.ethical_weight:.2f}, B:{final_weights.business_weight:.2f}, "
                   f"S:{final_weights.safety_weight:.2f}, C:{final_weights.compliance_weight:.2f}")

        return final_weights

    def _refine_weights_with_meta_learning(self, state: SystemState,
                                         baseline: ConstitutionalWeights) -> ConstitutionalWeights:
        """Use meta-learning to refine baseline weights."""
        try:
            state_vector = state.get_state_vector().unsqueeze(0)  # Add batch dimension

            with torch.no_grad():
                weight_adjustments = self.meta_learner(state_vector).squeeze()

            # Apply adjustments to baseline
            refined = ConstitutionalWeights(
                ethical_weight=baseline.ethical_weight * (0.8 + 0.4 * weight_adjustments[0]),
                business_weight=baseline.business_weight * (0.8 + 0.4 * weight_adjustments[1]),
                safety_weight=baseline.safety_weight * (0.8 + 0.4 * weight_adjustments[2]),
                compliance_weight=baseline.compliance_weight * (0.8 + 0.4 * weight_adjustments[3])
            )

            return refined

        except Exception as e:
            logger.warning(f"Meta-learning refinement failed: {e}. Using baseline weights.")
            return baseline

    def _apply_risk_adjustments(self, state: SystemState,
                               weights: ConstitutionalWeights) -> ConstitutionalWeights:
        """Apply risk-based adjustments to weights."""
        adjusted = ConstitutionalWeights(
            ethical_weight=weights.ethical_weight,
            business_weight=weights.business_weight,
            safety_weight=weights.safety_weight,
            compliance_weight=weights.compliance_weight
        )

        # Increase ethical weighting if ethical violations are rising
        if state.ethical_violation_rate > 0.01:
            ethical_boost = min(state.ethical_violation_rate * 10, 0.2)
            adjusted.ethical_weight += ethical_boost
            adjusted.business_weight -= ethical_boost * 0.5
            adjusted.safety_weight -= ethical_boost * 0.3
            adjusted.compliance_weight -= ethical_boost * 0.2

        # Increase safety weighting if system is unstable
        if state.error_rate > 0.03 or state.strategy_failure_rate > 0.05:
            safety_boost = min((state.error_rate + state.strategy_failure_rate) * 5, 0.25)
            adjusted.safety_weight += safety_boost
            adjusted.business_weight -= safety_boost * 0.6
            adjusted.ethical_weight -= safety_boost * 0.2
            adjusted.compliance_weight -= safety_boost * 0.2

        # Increase compliance weighting if violations are detected
        if state.compliance_violation_rate > 0.02:
            compliance_boost = min(state.compliance_violation_rate * 8, 0.15)
            adjusted.compliance_weight += compliance_boost
            adjusted.business_weight -= compliance_boost

        # Normalize to ensure sum = 1.0
        adjusted._normalize_weights()

        return adjusted

    def update_meta_learner(self, performance_feedback: Dict[str, Any]):
        """
        Update the meta-learner based on performance feedback.

        This allows the weighting system to learn from past decisions.
        """
        if len(self.weighting_history) < 5:
            return  # Need minimum history

        # Simple reinforcement learning: reward good outcomes
        optimizer = torch.optim.Adam(self.meta_learner.parameters(), lr=1e-4)

        # Calculate performance score (would be based on actual system performance)
        performance_score = performance_feedback.get('overall_performance', 0.5)

        # Use recent weightings and their outcomes
        recent_weightings = self.weighting_history[-10:]

        for state, weights in recent_weightings:
            optimizer.zero_grad()

            state_vector = state.get_state_vector().unsqueeze(0)
            predicted_weights = self.meta_learner(state_vector)

            # Target weights (what actually worked well)
            target_weights = torch.tensor([
                weights.ethical_weight,
                weights.business_weight,
                weights.safety_weight,
                weights.compliance_weight
            ]).unsqueeze(0)

            # Loss: how well predictions match good weightings
            loss = nn.functional.mse_loss(predicted_weights, target_weights) * (2.0 - performance_score)

            loss.backward()
            optimizer.step()

        logger.debug(f"Updated meta-learner with performance score: {performance_score:.3f}")

class AdaptiveGovernanceController:
    """
    Controller that applies dynamic constitutional weighting to governance decisions.
    """

    def __init__(self):
        self.state_evaluator = ConstitutionalStateEvaluator()
        self.weighting_engine = DynamicWeightingEngine()
        self.governance_engine = get_governance_engine()

        self.current_weights: Optional[ConstitutionalWeights] = None
        self.weights_history: List[Tuple[datetime, ConstitutionalWeights]] = []

        # Auto-update weights every 15 minutes
        self.weight_update_interval_minutes = 15
        self.last_weight_update = datetime.now() - timedelta(minutes=self.weight_update_interval_minutes + 1)

    def evaluate_strategy_with_dynamic_weighting(self,
                                               strategy_genome,
                                               context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate a strategy using dynamically weighted constitutional governance.
        """
        if context is None:
            context = {}

        # Check if weights need updating
        self._update_weights_if_needed(context)

        # Get standard governance assessment
        assessment = self.governance_engine.evaluate_strategy_governance(strategy_genome, context)

        # Apply dynamic weighting if available
        if self.current_weights:
            weighted_assessment = self._apply_dynamic_weighting(assessment, self.current_weights)
            assessment['weighted_governance_score'] = weighted_assessment['weighted_score']
            assessment['applied_weights'] = self.current_weights.to_dict()
            assessment['weighting_phase'] = getattr(self, '_current_phase', 'normal_operations')

            # Update clearance decision based on weighted score
            weighted_clearance = weighted_assessment['weighted_score'] >= 0.7  # Configurable threshold
            assessment['dynamic_clearance'] = weighted_clearance

            # If weighting changes the decision, log it
            if weighted_clearance != assessment['overall_clearance']:
                logger.info(f"Dynamic weighting changed clearance decision for strategy: "
                           f"original={assessment['overall_clearance']}, "
                           f"weighted={weighted_clearance}, "
                           f"weights={self.current_weights.to_dict()}")

        return assessment

    def _update_weights_if_needed(self, context: Dict[str, Any]):
        """Update constitutional weights if needed."""
        now = datetime.now()
        time_since_update = (now - self.last_weight_update).total_seconds() / 60

        if time_since_update >= self.weight_update_interval_minutes:
            try:
                # Evaluate current system state
                system_state = self.state_evaluator.evaluate_current_state(context)

                # Calculate optimal weights
                optimal_weights = self.weighting_engine.calculate_optimal_weights(system_state)

                # Store current phase for logging
                self._current_phase = self.state_evaluator.detect_system_phase(system_state)

                # Update current weights
                self.current_weights = optimal_weights
                self.weights_history.append((now, optimal_weights))

                # Keep history
                if len(self.weights_history) > 100:
                    self.weights_history = self.weights_history[-100:]

                self.last_weight_update = now

                logger.info(f"Updated constitutional weights: {optimal_weights.to_dict()}")

            except Exception as e:
                logger.error(f"Failed to update constitutional weights: {e}")

    def _apply_dynamic_weighting(self, assessment: Dict[str, Any],
                               weights: ConstitutionalWeights) -> Dict[str, float]:
        """
        Apply dynamic weighting to governance assessment scores.
        """
        # Extract component scores (0-1 scale)
        ethical_score = assessment.get('ethical_assessment', {}).get('severity_score', 0)
        # Invert ethical score (lower severity = higher score)
        ethical_weighted = (1.0 - min(ethical_score, 1.0)) * weights.ethical_weight

        business_score = assessment.get('business_assessment', {}).get('overall_alignment', 0.5)
        business_weighted = business_score * weights.business_weight

        safety_score = assessment.get('safety_assessment', {}).get('safety_score', 0.8)
        safety_weighted = safety_score * weights.safety_weight

        compliance_score = assessment.get('compliance_assessment', {}).get('compliance_score', 0.9)
        compliance_weighted = compliance_score * weights.compliance_weight

        # Calculate weighted total
        weighted_total = ethical_weighted + business_weighted + safety_weighted + compliance_weighted

        return {
            'weighted_score': weighted_total,
            'ethical_weighted': ethical_weighted,
            'business_weighted': business_weighted,
            'safety_weighted': safety_weighted,
            'compliance_weighted': compliance_weighted
        }

    def get_weighting_stats(self) -> Dict[str, Any]:
        """Get statistics about dynamic weighting performance."""
        if not self.weights_history:
            return {'status': 'no_weighting_history'}

        recent_weights = self.weights_history[-10:] if len(self.weights_history) >= 10 else self.weights_history

        # Calculate weight stability
        weight_changes = []
        for i in range(1, len(recent_weights)):
            prev_weights = recent_weights[i-1][1]
            curr_weights = recent_weights[i][1]
            change = abs(curr_weights.ethical_weight - prev_weights.ethical_weight) + \
                    abs(curr_weights.business_weight - prev_weights.business_weight) + \
                    abs(curr_weights.safety_weight - prev_weights.safety_weight) + \
                    abs(curr_weights.compliance_weight - prev_weights.compliance_weight)
            weight_changes.append(change)

        avg_weight_change = np.mean(weight_changes) if weight_changes else 0

        return {
            'current_weights': self.current_weights.to_dict() if self.current_weights else None,
            'weights_updated_at': self.last_weight_update.isoformat(),
            'total_weight_updates': len(self.weights_history),
            'avg_weight_change': avg_weight_change,
            'current_phase': getattr(self, '_current_phase', 'unknown'),
            'weighting_stability': 1.0 - min(avg_weight_change * 10, 1.0)  # Higher stability = lower change
        }

    def force_weight_update(self, context: Dict[str, Any] = None):
        """Force an immediate weight update."""
        if context is None:
            context = {}
        self.last_weight_update = datetime.now() - timedelta(minutes=self.weight_update_interval_minutes + 1)
        self._update_weights_if_needed(context)

    def set_manual_weights(self, weights: ConstitutionalWeights):
        """Manually set constitutional weights (for testing/administration)."""
        self.current_weights = weights
        self.weights_history.append((datetime.now(), weights))
        logger.info(f"Manually set constitutional weights: {weights.to_dict()}")

# Global adaptive governance controller instance
_adaptive_controller = None

def get_adaptive_governance_controller() -> AdaptiveGovernanceController:
    """Get or create global adaptive governance controller instance."""
    global _adaptive_controller
    if _adaptive_controller is None:
        _adaptive_controller = AdaptiveGovernanceController()
    return _adaptive_controller
