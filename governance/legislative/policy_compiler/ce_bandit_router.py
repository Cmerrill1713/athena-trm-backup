#!/usr/bin/env python3
"""
CE Bandit Router: Exploration + Exploitation for CE Routing
==========================================================

Integrates Thompson sampling with neural CE routing for optimal explore/exploit balance.

Combines:
- Neural context analysis (what we know works)
- Bandit exploration (what we might discover)
- Confidence-based decisions (when to trust vs explore)
"""

import os
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

# Federated learning integration
from federated_bandit_coordinator import (
    get_federated_priors,
    sync_federated_knowledge,
)

from ce_neural_router import CENeuralRouter, CERoutingDecision


@dataclass
class BanditRoutingDecision:
    """Enhanced routing decision with exploration metadata."""
    use_ce: bool
    confidence: float
    reasoning: str
    expected_improvement: float
    exploration_used: bool = False
    bandit_arm: Optional[str] = None
    neural_prediction: Optional[CERoutingDecision] = None
    bandit_adjustment: Optional[str] = None

@dataclass
class RoutingArm:
    """Bandit arm for routing decisions."""
    name: str
    description: str
    ce_preference: float  # 0.0 = always cosine, 1.0 = always CE
    exploration_rate: float = 0.1  # ε-greedy exploration

    def decide_ce(self, neural_decision: CERoutingDecision) -> bool:
        """Decide whether to use CE based on arm preference and exploration."""
        if random.random() < self.exploration_rate:
            # Pure exploration - random choice
            return random.choice([True, False])

        # Exploitation - follow arm preference modulated by neural confidence
        base_preference = self.ce_preference
        confidence_boost = neural_decision.confidence - 0.5  # Center around 0.5
        adjusted_preference = base_preference + confidence_boost * 0.3  # Small modulation
        adjusted_preference = np.clip(adjusted_preference, 0.0, 1.0)

        return random.random() < adjusted_preference

class CEBanditRouter:
    """
    Bandit-enhanced CE router with explore/exploit balancing.

    Uses Thompson sampling to balance:
    - Exploitation: Use neural predictions for known patterns
    - Exploration: Try different routing for unknown patterns
    """

    def __init__(self):
        self.neural_router = CENeuralRouter()

        # Bandit arms for different routing strategies
        self.routing_arms = {
            'conservative_ce': RoutingArm(
                name='conservative_ce',
                description='CE for high-confidence neural predictions only',
                ce_preference=0.3,
                exploration_rate=0.05
            ),
            'aggressive_ce': RoutingArm(
                name='aggressive_ce',
                description='CE for medium+ confidence, explore more',
                ce_preference=0.7,
                exploration_rate=0.15
            ),
            'neural_only': RoutingArm(
                name='neural_only',
                description='Pure neural routing, no exploration',
                ce_preference=0.5,  # Will be overridden by neural
                exploration_rate=0.0
            ),
            'exploratory': RoutingArm(
                name='exploratory',
                description='High exploration for discovery',
                ce_preference=0.5,
                exploration_rate=0.3
            )
        }

        # Thompson sampling state (Beta priors) - local + federated
        self.local_successes: Dict[str, int] = {arm: 1 for arm in self.routing_arms.keys()}  # Beta(1,1) prior
        self.local_failures: Dict[str, int] = {arm: 1 for arm in self.routing_arms.keys()}

        # Performance tracking
        self.routing_history: List[Dict[str, Any]] = []
        self.max_history = 10000

        # Exploration parameters
        self.exploration_decay = 0.99  # Gradually reduce exploration
        self.confidence_threshold_exploration = 0.7  # Only explore below this confidence

        # Federated learning
        self.federation_enabled = os.getenv("FEDERATION_ENABLED", "false").lower() == "true"
        self.federation_sync_interval_hours = int(os.getenv("FEDERATION_SYNC_HOURS", "24"))
        self.last_federation_sync = datetime.now() - timedelta(hours=self.federation_sync_interval_hours + 1)

    def route_with_bandit(self, query: str, intent: Optional[str] = None) -> BanditRoutingDecision:
        """
        Route with bandit-enhanced decision making.

        Combines neural prediction with bandit exploration.
        """
        # Sync with federation if needed
        self._sync_federation_if_needed()

        # Get neural prediction first
        neural_decision = self.neural_router.should_use_ce(query, intent)

        # Select bandit arm using Thompson sampling
        selected_arm = self._select_arm_thompson()

        # Get arm's routing decision
        arm_decision = self.routing_arms[selected_arm].decide_ce(neural_decision)

        # Determine if exploration was used
        exploration_used = False
        bandit_adjustment = None

        if selected_arm == 'neural_only':
            # Pure exploitation - use neural prediction
            final_ce_decision = neural_decision.use_ce
        else:
            # Bandit arm decision
            final_ce_decision = arm_decision
            exploration_used = (final_ce_decision != neural_decision.use_ce)
            bandit_adjustment = selected_arm

        # For low-confidence neural predictions, always allow some exploration
        if (neural_decision.confidence < self.confidence_threshold_exploration and
            not exploration_used and selected_arm != 'exploratory'):
            # Small chance to explore even with conservative arms
            if random.random() < 0.1:
                final_ce_decision = not final_ce_decision
                exploration_used = True
                bandit_adjustment = f"{selected_arm}_low_conf_explore"

        return BanditRoutingDecision(
            use_ce=final_ce_decision,
            confidence=max(neural_decision.confidence, 0.5 if exploration_used else 0.0),
            reasoning=self._build_reasoning(neural_decision, selected_arm, exploration_used),
            expected_improvement=neural_decision.expected_improvement,
            exploration_used=exploration_used,
            bandit_arm=selected_arm,
            neural_prediction=neural_decision,
            bandit_adjustment=bandit_adjustment
        )

    def _select_arm_thompson(self) -> str:
        """Select routing arm using Thompson sampling with federated knowledge."""
        # Sample from Beta posterior for each arm
        samples = {}
        for arm_name in self.routing_arms.keys():
            # Combine local and federated priors
            local_alpha = self.local_successes[arm_name]
            local_beta = self.local_failures[arm_name]

            # Check for federated priors
            federated_priors = get_federated_priors(arm_name) if self.federation_enabled else None

            if federated_priors:
                # Blend local and federated knowledge
                fed_alpha, fed_beta = federated_priors
                # Weight federated knowledge (can be tuned)
                federation_weight = 0.3
                effective_alpha = local_alpha * (1 - federation_weight) + fed_alpha * federation_weight
                effective_beta = local_beta * (1 - federation_weight) + fed_beta * federation_weight
            else:
                effective_alpha = local_alpha
                effective_beta = local_beta

            samples[arm_name] = np.random.beta(effective_alpha, effective_beta)

        # Select arm with highest sample
        return max(samples, key=samples.get)

    def record_routing_outcome(self, decision: BanditRoutingDecision,
                             actual_judge_improvement: float,
                             query: str, intent: Optional[str] = None):
        """
        Record routing outcome and update bandit priors.

        This enables learning which arms work best for different scenarios.
        """
        # Define success criteria (could be made configurable)
        success_threshold = 1.0  # Judge improvement > 1.0 considered success
        was_success = actual_judge_improvement > success_threshold

        # Update local Thompson sampling priors
        arm = decision.bandit_arm
        if arm:
            if was_success:
                self.local_successes[arm] += 1
            else:
                self.local_failures[arm] += 1

        # Record for analysis
        outcome_record = {
            'timestamp': datetime.now().isoformat(),
            'query_preview': query[:50] + '...' if len(query) > 50 else query,
            'intent': intent,
            'arm_used': decision.bandit_arm,
            'neural_confidence': decision.neural_prediction.confidence if decision.neural_prediction else None,
            'final_ce_decision': decision.use_ce,
            'exploration_used': decision.exploration_used,
            'judge_improvement': actual_judge_improvement,
            'was_success': was_success,
            'neural_features': decision.neural_prediction.features if decision.neural_prediction else {}
        }

        self.routing_history.append(outcome_record)

        # Maintain history size
        if len(self.routing_history) > self.max_history:
            self.routing_history.pop(0)

        # Update neural router learning
        from ce_neural_router import record_ce_performance
        reranker_used = "crossencoder" if decision.use_ce else "cosine"
        record_ce_performance(query, reranker_used, actual_judge_improvement)

        # Periodic federation sync (after recording outcomes)
        self._sync_federation_if_needed()

    def _sync_federation_if_needed(self):
        """Sync with federation if enough time has passed and federation is enabled."""
        if not self.federation_enabled:
            return

        hours_since_sync = (datetime.now() - self.last_federation_sync).total_seconds() / 3600

        if hours_since_sync >= self.federation_sync_interval_hours:
            # Prepare local priors for federation
            local_priors = {
                arm: (self.local_successes[arm], self.local_failures[arm])
                for arm in self.routing_arms.keys()
            }

            # Get strategy stats for constitutional validation
            strategy_stats = self.get_bandit_stats()

            # Sync with federation (includes constitutional validation)
            success = sync_federated_knowledge(local_priors, strategy_stats)
            if success:
                self.last_federation_sync = datetime.now()

    def _build_reasoning(self, neural: CERoutingDecision, arm: str, exploration: bool) -> str:
        """Build human-readable reasoning for the decision."""
        reasons = []

        if exploration:
            reasons.append(f"Bandit exploration ({arm})")
        else:
            reasons.append(f"Bandit exploitation ({arm})")

        if neural.reasoning:
            reasons.append(f"Neural: {neural.reasoning}")

        return " + ".join(reasons)

    def get_bandit_stats(self) -> Dict[str, Any]:
        """Get comprehensive bandit performance statistics."""
        total_decisions = sum(self.local_successes[arm] + self.local_failures[arm] - 2  # Subtract priors
                             for arm in self.routing_arms.keys())

        arm_stats = {}
        for arm_name in self.routing_arms.keys():
            local_successes = self.local_successes[arm_name] - 1  # Subtract prior
            local_failures = self.local_failures[arm_name] - 1   # Subtract prior
            total = local_successes + local_failures

            win_rate = local_successes / total if total > 0 else 0.0
            exploration_rate = self.routing_arms[arm_name].exploration_rate

            # Include federated priors if available
            federated_priors = get_federated_priors(arm_name) if self.federation_enabled else None
            federated_win_rate = None
            if federated_priors:
                fed_alpha, fed_beta = federated_priors
                federated_win_rate = fed_alpha / (fed_alpha + fed_beta)

            arm_stats[arm_name] = {
                'local_successes': local_successes,
                'local_failures': local_failures,
                'local_win_rate': win_rate,
                'federated_win_rate': federated_win_rate,
                'exploration_rate': exploration_rate,
                'samples': total,
                'has_federated': federated_priors is not None
            }

        # Historical analysis
        if self.routing_history:
            recent_history = self.routing_history[-100:]  # Last 100 decisions
            exploration_rate_recent = sum(1 for r in recent_history if r['exploration_used']) / len(recent_history)
            avg_improvement = np.mean([r['judge_improvement'] for r in recent_history])
            exploration_improvement = np.mean([r['judge_improvement'] for r in recent_history if r['exploration_used']])
            exploitation_improvement = np.mean([r['judge_improvement'] for r in recent_history if not r['exploration_used']])
        else:
            exploration_rate_recent = 0.0
            avg_improvement = 0.0
            exploration_improvement = 0.0
            exploitation_improvement = 0.0

        # Federation statistics
        from federated_bandit_coordinator import federation_coordinator
        federation_stats = federation_coordinator.get_federation_stats()

        return {
            'total_decisions': total_decisions,
            'arm_performance': arm_stats,
            'exploration_rate_recent': exploration_rate_recent,
            'avg_improvement': avg_improvement,
            'exploration_improvement': exploration_improvement,
            'exploitation_improvement': exploitation_improvement,
            'history_size': len(self.routing_history),
            'best_arm': max(arm_stats.keys(), key=lambda k: arm_stats[k]['local_win_rate']),
            'federation_enabled': self.federation_enabled,
            'federation_stats': federation_stats,
            'last_federation_sync_hours': (datetime.now() - self.last_federation_sync).total_seconds() / 3600
        }

    def reset_exploration_rates(self):
        """Gradually reduce exploration rates as system learns."""
        for arm in self.routing_arms.values():
            arm.exploration_rate *= self.exploration_decay
            arm.exploration_rate = max(arm.exploration_rate, 0.01)  # Minimum exploration

# Global bandit router instance
ce_bandit_router = CEBanditRouter()

def route_with_bandit_enhancement(query: str, intent: Optional[str] = None) -> BanditRoutingDecision:
    """High-level interface for bandit-enhanced CE routing."""
    return ce_bandit_router.route_with_bandit(query, intent)

def record_bandit_outcome(decision: BanditRoutingDecision,
                         judge_improvement: float,
                         query: str, intent: Optional[str] = None):
    """Record bandit routing outcome for learning."""
    ce_bandit_router.record_routing_outcome(decision, judge_improvement, query, intent)

if __name__ == "__main__":
    # Demo the bandit-enhanced router
    print("🎯 CE Bandit Router Demo")
    print("=" * 50)

    test_queries = [
        ("What is the weather today?", None, "Simple query"),
        ("How do ITAR regulations apply to international shipping?", "legal", "Complex legal"),
        ("Can you explain machine learning?", None, "Technical but straightforward"),
        ("What are the compliance requirements for data center operations in regulated industries?", "policy", "Complex policy")
    ]

    print("\n🎲 Bandit Routing Decisions (with exploration):")
    for query, intent, desc in test_queries:
        decision = route_with_bandit_enhancement(query, intent)
        explore_indicator = "🎲" if decision.exploration_used else "🎯"
        ce_indicator = "CE" if decision.use_ce else "Cosine"

        print(f"\n{explore_indicator} {desc}:")
        print(f"  Decision: {ce_indicator} (confidence: {decision.confidence:.2f})")
        print(f"  Arm: {decision.bandit_arm}")
        print(f"  Reasoning: {decision.reasoning}")
        if decision.exploration_used:
            print("  🚀 Exploration triggered!")

    # Show bandit stats
    stats = ce_bandit_router.get_bandit_stats()
    print("\n📊 Bandit Stats:")
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  Best arm: {stats['best_arm']}")
    print(f"  Recent exploration rate: {stats['exploration_rate_recent']:.1%}")

    print("\n🎉 Bandit-enhanced routing ready!")
    print("   Balances known patterns with discovery of new opportunities.")
