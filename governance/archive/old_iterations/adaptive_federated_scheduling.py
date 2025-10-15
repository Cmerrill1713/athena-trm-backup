"""
Adaptive Federated Scheduling
=============================

Autonomous decision-making for federated learning participation.
The system evaluates expected performance uplift vs. privacy cost to decide
when federated learning makes economic sense.

Features:
- Economic cost-benefit analysis for participation decisions
- Privacy budget optimization with ε spending strategies
- Round value estimation using historical performance data
- Autonomous scheduling based on utility maximization
- Self-governing intelligence network behavior
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .federated_training import FederatedConfig, FederatedCoordinator

logger = logging.getLogger(__name__)

@dataclass
class RoundValueEstimate:
    """Estimated value of participating in a federated round."""
    round_id: str
    expected_improvement: float  # Expected judge score improvement
    confidence_interval: Tuple[float, float]  # (lower, upper) bounds
    privacy_cost: float  # ε budget consumption
    computational_cost: float  # Training time/resources
    estimated_value: float  # Net utility (benefit - cost)
    participation_probability: float  # 0-1 recommendation score

@dataclass
class PrivacyBudgetState:
    """Current state of privacy budget."""
    total_budget: float  # Total ε available (e.g., 2.0)
    spent_budget: float  # ε already consumed
    remaining_budget: float  # ε still available
    spending_rate: float  # ε per round average
    last_reset: datetime  # When budget was last reset
    budget_period_days: int  # Budget reset period

    @property
    def utilization_rate(self) -> float:
        """Budget utilization percentage."""
        return self.spent_budget / self.total_budget if self.total_budget > 0 else 0.0

    def can_afford_cost(self, cost: float) -> bool:
        """Check if budget can afford a given cost."""
        return self.remaining_budget >= cost

    def project_exhaustion_date(self) -> Optional[datetime]:
        """Project when budget will be exhausted at current rate."""
        if self.spending_rate <= 0:
            return None
        days_remaining = self.remaining_budget / self.spending_rate
        return datetime.now() + timedelta(days=days_remaining)

class FederatedEconomics:
    """
    Economic analysis for federated learning participation decisions.

    Implements utility theory for cost-benefit analysis:
    - Expected performance improvement vs. privacy cost
    - Computational resource allocation
    - Long-term value optimization
    """

    def __init__(self,
                 value_of_improvement: float = 100.0,  # $ value per 0.1 judge score improvement
                 privacy_cost_per_epsilon: float = 50.0,  # $ cost per ε spent
                 computational_cost_per_round: float = 10.0):  # $ cost per round participation
        self.value_of_improvement = value_of_improvement
        self.privacy_cost_per_epsilon = privacy_cost_per_epsilon
        self.computational_cost_per_round = computational_cost_per_round

        # Historical performance tracking
        self.participation_history: List[Dict] = []
        self.performance_history: List[Dict] = []

    def calculate_participation_utility(self,
                                      expected_improvement: float,
                                      privacy_cost: float,
                                      confidence_level: float = 0.8) -> float:
        """
        Calculate economic utility of participating in a federated round.

        Utility = Expected_Value - Costs
        Where Expected_Value = improvement × value_per_improvement × confidence
        And Costs = privacy_cost + computational_cost
        """
        # Expected value with confidence adjustment
        expected_value = (expected_improvement *
                         self.value_of_improvement *
                         confidence_level)

        # Total costs
        privacy_dollar_cost = privacy_cost * self.privacy_cost_per_epsilon
        total_cost = privacy_dollar_cost + self.computational_cost_per_round

        # Net utility
        utility = expected_value - total_cost

        logger.debug(f"Participation utility: ${utility:.2f} "
                    f"(value: ${expected_value:.2f}, cost: ${total_cost:.2f})")

        return utility

    def estimate_round_value(self,
                           round_info: Dict,
                           deployment_state: Dict,
                           historical_performance: List[Dict]) -> RoundValueEstimate:
        """
        Estimate the value of participating in a specific round.

        Uses historical data and round characteristics to predict:
        - Expected performance improvement
        - Privacy cost estimation
        - Confidence intervals
        """
        round_id = round_info.get('round_id', 'unknown')
        participants = round_info.get('participants', [])
        total_participants = len(participants)

        # Estimate expected improvement based on historical data
        expected_improvement = self._predict_improvement(
            total_participants, historical_performance, deployment_state
        )

        # Estimate privacy cost (simplified - could be more sophisticated)
        privacy_cost = self._estimate_privacy_cost(total_participants, round_info)

        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            expected_improvement, historical_performance
        )

        # Calculate net utility
        avg_confidence = (confidence_interval[0] + confidence_interval[1]) / 2
        utility = self.calculate_participation_utility(
            expected_improvement, privacy_cost, avg_confidence
        )

        # Participation probability based on utility
        participation_prob = self._calculate_participation_probability(utility)

        return RoundValueEstimate(
            round_id=round_id,
            expected_improvement=expected_improvement,
            confidence_interval=confidence_interval,
            privacy_cost=privacy_cost,
            computational_cost=self.computational_cost_per_round,
            estimated_value=utility,
            participation_probability=participation_prob
        )

    def _predict_improvement(self,
                           num_participants: int,
                           historical_perf: List[Dict],
                           deployment_state: Dict) -> float:
        """
        Predict expected improvement from round participation.

        Uses regression on historical data:
        improvement = f(num_participants, current_performance, diversity_score)
        """
        if not historical_perf:
            # Default prediction based on participant count
            base_improvement = min(num_participants * 0.02, 0.15)  # Up to 0.15 max
            return base_improvement

        # Simple linear regression on historical data
        improvements = [p.get('improvement', 0) for p in historical_perf]
        participant_counts = [p.get('participants', 3) for p in historical_perf]

        if len(improvements) < 3:
            return np.mean(improvements) if improvements else 0.05

        # Linear regression: improvement = a * participants + b
        X = np.array(participant_counts).reshape(-1, 1)
        y = np.array(improvements)

        # Add bias term
        X = np.column_stack([X, np.ones(X.shape[0])])

        try:
            # Solve normal equations: (X^T X)^-1 X^T y
            theta = np.linalg.inv(X.T @ X) @ X.T @ y
            predicted = theta[0] * num_participants + theta[1]

            # Bound prediction to reasonable range
            return np.clip(predicted, 0.01, 0.20)

        except np.linalg.LinAlgError:
            # Fallback to mean
            return np.mean(improvements)

    def _estimate_privacy_cost(self, num_participants: int, round_info: Dict) -> float:
        """
        Estimate privacy cost (ε consumption) for a round.

        Cost increases with participant count and decreases with round frequency.
        """
        base_cost = 0.1  # Base ε cost per round

        # Scale with participant count (more participants = more information shared)
        participant_factor = min(num_participants / 5.0, 2.0)  # Max 2x cost

        # Adjust for round frequency (more frequent = lower marginal cost)
        round_frequency = round_info.get('frequency_hours', 24)
        frequency_factor = max(24.0 / round_frequency, 0.5)  # Less frequent = higher cost

        total_cost = base_cost * participant_factor * frequency_factor

        return min(total_cost, 0.5)  # Cap at 0.5ε per round

    def _calculate_confidence_interval(self,
                                    expected_improvement: float,
                                    historical_perf: List[Dict],
                                    confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for improvement prediction.

        Uses historical variance to estimate uncertainty.
        """
        if not historical_perf:
            # Wide interval for unknown rounds
            margin = expected_improvement * 0.5
            return (max(0, expected_improvement - margin),
                   expected_improvement + margin)

        # Calculate standard error from historical data
        improvements = [p.get('improvement', 0) for p in historical_perf]
        if len(improvements) < 2:
            margin = expected_improvement * 0.3
        else:
            std_dev = np.std(improvements)
            n = len(improvements)
            standard_error = std_dev / np.sqrt(n)

            # t-distribution critical value (approximate z for 95%)
            z_score = 1.96
            margin = z_score * standard_error

        return (max(0, expected_improvement - margin),
               expected_improvement + margin)

    def _calculate_participation_probability(self, utility: float) -> float:
        """
        Calculate participation probability based on utility.

        Uses sigmoid function to map utility to probability.
        """
        # Sigmoid parameters (tuned for reasonable behavior)
        # P(participate) = 1 / (1 + exp(-k * (utility - threshold)))
        k = 0.1  # Steepness
        threshold = 25.0  # Utility threshold for 50% participation

        logit = k * (utility - threshold)
        probability = 1 / (1 + np.exp(-logit))

        return np.clip(probability, 0.0, 1.0)

    def record_participation_outcome(self,
                                   round_id: str,
                                   participated: bool,
                                   actual_improvement: float,
                                   privacy_cost: float,
                                   utility: float):
        """Record outcome of participation decision for learning."""
        outcome = {
            'round_id': round_id,
            'participated': participated,
            'actual_improvement': actual_improvement,
            'privacy_cost': privacy_cost,
            'utility': utility,
            'timestamp': datetime.now()
        }

        self.participation_history.append(outcome)

        # Keep only recent history
        cutoff = datetime.now() - timedelta(days=90)
        self.participation_history = [
            p for p in self.participation_history
            if p['timestamp'] > cutoff
        ]

class PrivacyBudgetManager:
    """
    Sophisticated privacy budget management with economic optimization.

    Features:
    - Multi-dimensional budget tracking (ε, δ, queries)
    - Spending rate optimization
    - Budget allocation strategies
    - Economic trade-off analysis
    """

    def __init__(self,
                 total_epsilon_budget: float = 2.0,
                 total_delta_budget: float = 1e-5,
                 budget_period_days: int = 30):
        self.total_epsilon_budget = total_epsilon_budget
        self.total_delta_budget = total_delta_budget
        self.budget_period_days = budget_period_days

        # Current state
        self.spent_epsilon = 0.0
        self.spent_delta = 0.0
        self.last_reset = datetime.now()

        # Spending history for optimization
        self.spending_history: List[Dict] = []

    def get_current_budget_state(self) -> PrivacyBudgetState:
        """Get current privacy budget state."""
        remaining_epsilon = self.total_epsilon_budget - self.spent_epsilon

        # Calculate spending rate (ε per day)
        days_elapsed = (datetime.now() - self.last_reset).total_seconds() / (24 * 3600)
        spending_rate = self.spent_epsilon / max(days_elapsed, 1.0)

        return PrivacyBudgetState(
            total_budget=self.total_epsilon_budget,
            spent_budget=self.spent_epsilon,
            remaining_budget=remaining_epsilon,
            spending_rate=spending_rate,
            last_reset=self.last_reset,
            budget_period_days=self.budget_period_days
        )

    def can_afford_participation(self, privacy_cost: float) -> bool:
        """Check if current budget can afford participation."""
        budget_state = self.get_current_budget_state()
        return budget_state.can_afford_cost(privacy_cost)

    def optimize_participation_decision(self,
                                      round_value: RoundValueEstimate,
                                      economic_utility: float) -> Tuple[bool, str]:
        """
        Make optimal participation decision based on budget and utility.

        Considers:
        - Current budget availability
        - Expected utility vs. cost
        - Budget exhaustion projections
        - Long-term optimization
        """
        budget_state = self.get_current_budget_state()

        # Can't participate if budget exhausted
        if not budget_state.can_afford_cost(round_value.privacy_cost):
            return False, "insufficient_privacy_budget"

        # High utility + available budget = participate
        if economic_utility > 50 and budget_state.remaining_budget > round_value.privacy_cost * 2:
            return True, "high_utility_available_budget"

        # Low utility but budget plentiful = consider saving for better rounds
        if economic_utility < 10 and budget_state.utilization_rate < 0.3:
            return False, "low_utility_conserve_budget"

        # Medium utility with moderate budget = participate but monitor
        if 10 <= economic_utility <= 50:
            exhaustion_date = budget_state.project_exhaustion_date()
            if exhaustion_date and (exhaustion_date - datetime.now()).days > 7:
                return True, "moderate_utility_sustainable_budget"
            else:
                return False, "moderate_utility_budget_pressure"

        # Very high utility = participate regardless of budget level
        if economic_utility > 100:
            return True, "very_high_utility_prioritize"

        # Conservative default
        return False, "conservative_default"

    def record_spending(self,
                       epsilon_spent: float,
                       delta_spent: float,
                       round_id: str,
                       utility_gained: float):
        """Record privacy budget spending for optimization."""
        self.spent_epsilon += epsilon_spent
        self.spent_delta += delta_spent

        spending_record = {
            'round_id': round_id,
            'epsilon_spent': epsilon_spent,
            'delta_spent': delta_spent,
            'utility_gained': utility_gained,
            'timestamp': datetime.now(),
            'budget_state': self.get_current_budget_state()
        }

        self.spending_history.append(spending_record)

        # Check for budget reset
        if (datetime.now() - self.last_reset).days >= self.budget_period_days:
            self._reset_budget()

    def _reset_budget(self):
        """Reset privacy budget at the end of budget period."""
        logger.info(f"Resetting privacy budget: spent {self.spent_epsilon:.3f}ε "
                   f"over {self.budget_period_days} days")

        self.spent_epsilon = 0.0
        self.spent_delta = 0.0
        self.last_reset = datetime.now()

    def get_spending_efficiency(self) -> float:
        """Calculate spending efficiency (utility per ε spent)."""
        if not self.spending_history:
            return 0.0

        total_utility = sum(h['utility_gained'] for h in self.spending_history)
        total_epsilon = sum(h['epsilon_spent'] for h in self.spending_history)

        return total_utility / max(total_epsilon, 0.01)

    def optimize_budget_allocation(self) -> Dict[str, Any]:
        """
        Optimize future budget allocation based on historical performance.

        Returns recommendations for spending strategy.
        """
        if len(self.spending_history) < 5:
            return {'strategy': 'conservative', 'reason': 'insufficient_history'}

        efficiency = self.get_spending_efficiency()
        budget_state = self.get_current_budget_state()

        # High efficiency + available budget = aggressive spending
        if efficiency > 100 and budget_state.remaining_budget > 1.0:
            return {
                'strategy': 'aggressive',
                'reason': 'high_efficiency_available_budget',
                'participation_threshold': 20  # Lower utility threshold
            }

        # Low efficiency = conservative spending
        elif efficiency < 50:
            return {
                'strategy': 'conservative',
                'reason': 'low_efficiency_conserve_budget',
                'participation_threshold': 50  # Higher utility threshold
            }

        # Moderate = balanced approach
        else:
            return {
                'strategy': 'balanced',
                'reason': 'moderate_efficiency_sustainable',
                'participation_threshold': 35
            }

class AdaptiveFederatedScheduler:
    """
    Autonomous federated scheduling with economic optimization.

    The system now makes intelligent decisions about when federated learning
    makes economic sense, creating a self-governing intelligence network.
    """

    def __init__(self, federated_config: FederatedConfig):
        self.config = federated_config
        self.coordinator = FederatedCoordinator(federated_config)

        # Economic decision-making components
        self.economics = FederatedEconomics()
        self.privacy_manager = PrivacyBudgetManager(
            total_epsilon_budget=2.0,  # Configurable
            budget_period_days=30
        )

        # Historical data for decision making
        self.round_history: List[Dict] = []
        self.decision_history: List[Dict] = []

    def evaluate_round_participation(self, round_info: Dict) -> Tuple[bool, str, RoundValueEstimate]:
        """
        Evaluate whether to participate in a federated round.

        Returns: (should_participate, reason, value_estimate)
        """
        # Get current deployment state
        deployment_state = self._get_deployment_state()

        # Estimate round value
        value_estimate = self.economics.estimate_round_value(
            round_info, deployment_state, self.round_history
        )

        # Calculate economic utility
        utility = self.economics.calculate_participation_utility(
            value_estimate.expected_improvement,
            value_estimate.privacy_cost,
            value_estimate.participation_probability
        )

        # Get budget optimization recommendation
        budget_recommendation = self.privacy_manager.optimize_budget_allocation()

        # Make final decision
        should_participate, reason = self.privacy_manager.optimize_participation_decision(
            value_estimate, utility
        )

        # Apply budget recommendation adjustments
        if budget_recommendation['strategy'] == 'conservative':
            if utility < budget_recommendation['participation_threshold']:
                should_participate = False
                reason = f"{reason}_conservative_strategy"
        elif budget_recommendation['strategy'] == 'aggressive':
            if utility > budget_recommendation['participation_threshold']:
                should_participate = True
                reason = f"{reason}_aggressive_strategy"

        # Record decision for learning
        decision_record = {
            'round_id': round_info.get('round_id'),
            'should_participate': should_participate,
            'reason': reason,
            'value_estimate': value_estimate,
            'economic_utility': utility,
            'budget_strategy': budget_recommendation['strategy'],
            'timestamp': datetime.now()
        }
        self.decision_history.append(decision_record)

        logger.info(f"Round participation decision: {should_participate} "
                   f"(reason: {reason}, utility: ${utility:.2f})")

        return should_participate, reason, value_estimate

    def _get_deployment_state(self) -> Dict:
        """Get current deployment state for decision making."""
        # This would gather current performance metrics, available resources, etc.
        return {
            'current_performance': 7.0,  # Example judge score
            'recent_improvements': [0.1, 0.05, 0.08],  # Last few improvements
            'available_resources': 0.8,  # 80% available compute
            'federation_history': len(self.round_history)
        }

    def record_round_outcome(self,
                           round_id: str,
                           participated: bool,
                           actual_improvement: float,
                           privacy_cost: float):
        """Record actual outcome of round participation."""
        # Record in economics engine
        utility = self.economics.calculate_participation_utility(
            actual_improvement, privacy_cost, 1.0  # Actual outcome = 100% confidence
        )

        self.economics.record_participation_outcome(
            round_id, participated, actual_improvement, privacy_cost, utility
        )

        # Record in privacy manager
        if participated:
            self.privacy_manager.record_spending(
                privacy_cost, 1e-6, round_id, utility
            )

        # Add to round history
        round_record = {
            'round_id': round_id,
            'participated': participated,
            'actual_improvement': actual_improvement,
            'privacy_cost': privacy_cost,
            'utility': utility,
            'participants': 5,  # Would be retrieved from round info
            'timestamp': datetime.now()
        }
        self.round_history.append(round_record)

        logger.info(f"Recorded round outcome: {round_id} "
                   f"(participated: {participated}, improvement: {actual_improvement:.3f})")

    def get_scheduler_stats(self) -> Dict:
        """Get comprehensive scheduler statistics."""
        budget_state = self.privacy_manager.get_current_budget_state()

        recent_decisions = self.decision_history[-50:] if self.decision_history else []
        participation_rate = sum(1 for d in recent_decisions if d['should_participate']) / max(len(recent_decisions), 1)

        recent_rounds = self.round_history[-20:] if self.round_history else []
        avg_improvement = np.mean([r['actual_improvement'] for r in recent_rounds]) if recent_rounds else 0.0

        return {
            'budget_state': {
                'remaining_epsilon': budget_state.remaining_budget,
                'utilization_rate': budget_state.utilization_rate,
                'spending_efficiency': self.privacy_manager.get_spending_efficiency()
            },
            'participation_stats': {
                'recent_decisions': len(recent_decisions),
                'participation_rate': participation_rate,
                'total_rounds': len(self.round_history)
            },
            'performance_stats': {
                'avg_improvement': avg_improvement,
                'total_utility_generated': sum(r.get('utility', 0) for r in recent_rounds)
            },
            'economic_strategy': self.privacy_manager.optimize_budget_allocation()
        }

    def run_autonomous_scheduling(self) -> List[Dict]:
        """
        Run autonomous scheduling for available rounds.

        This would be called periodically to evaluate and participate in rounds.
        """
        # This is a placeholder for the autonomous scheduling logic
        # In practice, this would:
        # 1. Query coordinator for available rounds
        # 2. Evaluate each round using evaluate_round_participation
        # 3. Execute participation decisions
        # 4. Monitor outcomes and update models

        decisions = []

        # Example implementation
        available_rounds = self.coordinator.active_rounds

        for round_id, round_obj in available_rounds.items():
            round_info = {
                'round_id': round_id,
                'participants': round_obj.participants,
                'frequency_hours': 24  # Example
            }

            should_participate, reason, value_estimate = self.evaluate_round_participation(round_info)

            decision = {
                'round_id': round_id,
                'decision': should_participate,
                'reason': reason,
                'expected_utility': value_estimate.estimated_value,
                'privacy_cost': value_estimate.privacy_cost
            }

            decisions.append(decision)

            if should_participate:
                logger.info(f"Autonomous scheduler: Participating in round {round_id}")
                # Execute participation logic here
            else:
                logger.info(f"Autonomous scheduler: Skipping round {round_id} ({reason})")

        return decisions

# Global scheduler instance
_adaptive_scheduler = None

def get_adaptive_federated_scheduler(config: Optional[FederatedConfig] = None) -> AdaptiveFederatedScheduler:
    """Get or create global adaptive federated scheduler instance."""
    global _adaptive_scheduler
    if _adaptive_scheduler is None:
        if config is None:
            config = FederatedConfig()
        _adaptive_scheduler = AdaptiveFederatedScheduler(config)
    return _adaptive_scheduler
