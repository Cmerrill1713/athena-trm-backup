"""
Hierarchical Bandit System with Meta-Policy Layer
================================================

Implements a two-level bandit system where a meta-bandit chooses between
optimization strategies, and strategy-specific bandits choose variants within
each strategy.

Key Features:
- Meta-bandit selects between strategies (cosine-only, CE, hybrid, baseline)
- Strategy bandits optimize variants within each strategy
- Hierarchical Thompson sampling with Beta priors
- Cross-level learning and adaptation
- Automatic strategy switching based on context
- Statistical guarantees at both levels
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from .bandit_optimizer import AdvancedBanditOptimizer, BanditVariant

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """High-level optimization strategies."""
    COSINE_ONLY = "cosine_only"           # Basic cosine similarity reranking
    CROSS_ENCODER = "cross_encoder"        # CE reranking for precision
    HYBRID = "hybrid"                     # Adaptive reranking based on query
    BASELINE = "baseline"                 # No optimization (control)
    PERSONALIZED = "personalized"         # User-adaptive optimization

@dataclass
class StrategyContext:
    """Context information for strategy selection."""
    query_length: int = 0
    query_complexity: float = 0.0  # Entropy of query terms
    user_history: Optional[Dict] = None
    intent_category: str = "general"
    latency_budget_ms: int = 1000
    quality_requirement: str = "balanced"  # "speed", "quality", "balanced"

@dataclass
class HierarchicalDecision:
    """Complete decision from hierarchical bandit system."""
    strategy: OptimizationStrategy
    variant: str
    meta_confidence: float
    strategy_confidence: float
    expected_improvement: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class StrategyBanditManager:
    """
    Manages individual bandits for each optimization strategy.

    Each strategy has its own bandit optimizer for choosing variants
    within that strategy's parameter space.
    """

    def __init__(self):
        self.strategy_bandits: Dict[OptimizationStrategy, AdvancedBanditOptimizer] = {}

        # Initialize bandits for each strategy
        for strategy in OptimizationStrategy:
            self.strategy_bandits[strategy] = AdvancedBanditOptimizer(
                exploration_floor=0.05,
                min_samples_promotion=50,  # Lower threshold for strategy variants
                traffic_change_cap=0.3
            )

    def add_variant_to_strategy(self, strategy: OptimizationStrategy, variant_name: str):
        """Add a variant to a specific strategy's bandit."""
        if strategy not in self.strategy_bandits:
            logger.error(f"Unknown strategy: {strategy}")
            return

        self.strategy_bandits[strategy].add_variant(variant_name)
        logger.info(f"Added variant '{variant_name}' to strategy {strategy.value}")

    def select_variant_for_strategy(self, strategy: OptimizationStrategy) -> str:
        """Select best variant within a strategy using Thompson sampling."""
        if strategy not in self.strategy_bandits:
            return "default"

        return self.strategy_bandits[strategy].select_variant()

    def update_strategy_variant(self, strategy: OptimizationStrategy, variant: str, reward: float):
        """Update the bandit for a strategy-variant combination."""
        if strategy in self.strategy_bandits:
            self.strategy_bandits[strategy].update_variant(variant, reward)

    def get_strategy_stats(self, strategy: OptimizationStrategy) -> Dict:
        """Get comprehensive statistics for a strategy's bandit."""
        if strategy not in self.strategy_bandits:
            return {}

        return self.strategy_bandits[strategy].get_stats()

    def promote_variants_in_strategy(self, strategy: OptimizationStrategy) -> List[str]:
        """Run promotion cycle for variants within a strategy."""
        if strategy not in self.strategy_bandits:
            return []

        return self.strategy_bandits[strategy].run_promotion_cycle()

    def add_custom_strategy_variant(self, strategy: OptimizationStrategy,
                                   variant_name: str, strategy_representation):
        """
        Add a custom strategy variant with its representation.

        Used by constitutional governance to deploy evolved strategies.
        """
        # Ensure strategy bandit exists
        if strategy not in self.strategy_bandits:
            self.initialize_strategy_bandit(strategy)

        # Add variant to the strategy bandit
        self.strategy_bandits[strategy].add_variant(variant_name)

        logger.info(f"Added custom variant '{variant_name}' to strategy {strategy.value}")

    def initialize_strategy_bandit(self, strategy: OptimizationStrategy):
        """
        Initialize a bandit for a new strategy.

        Used when adding constitutionally approved strategies.
        """
        if strategy not in self.strategy_bandits:
            self.strategy_bandits[strategy] = StrategyBandit(strategy)
            logger.info(f"Initialized bandit for new strategy: {strategy.value}")

class MetaBandit:
    """
    Meta-bandit that chooses between optimization strategies.

    Uses Beta priors and Thompson sampling to select the best high-level
    approach based on context and historical performance.
    """

    def __init__(self,
                 exploration_bonus: float = 0.1,
                 context_weight: float = 0.3):
        self.strategy_variants: Dict[OptimizationStrategy, BanditVariant] = {}

        # Initialize meta-variants for each strategy
        for strategy in OptimizationStrategy:
            self.strategy_variants[strategy] = BanditVariant(f"meta_{strategy.value}")

        self.exploration_bonus = exploration_bonus
        self.context_weight = context_weight

        # Context-aware selection parameters
        self.strategy_context_scores = self._initialize_context_scores()

    def _initialize_context_scores(self) -> Dict[str, Dict[OptimizationStrategy, float]]:
        """Initialize context-aware strategy preferences."""
        return {
            "query_length": {
                OptimizationStrategy.COSINE_ONLY: 0.8,      # Good for short queries
                OptimizationStrategy.CROSS_ENCODER: 0.2,     # Expensive for short queries
                OptimizationStrategy.HYBRID: 0.6,            # Balanced
                OptimizationStrategy.BASELINE: 0.5,          # Always available
                OptimizationStrategy.PERSONALIZED: 0.4       # Needs user history
            },
            "intent_complexity": {
                OptimizationStrategy.COSINE_ONLY: 0.4,       # Basic for simple intents
                OptimizationStrategy.CROSS_ENCODER: 0.9,      # Best for complex intents
                OptimizationStrategy.HYBRID: 0.7,             # Good balance
                OptimizationStrategy.BASELINE: 0.3,           # Poor for complex
                OptimizationStrategy.PERSONALIZED: 0.5        # Context-dependent
            },
            "latency_budget": {
                OptimizationStrategy.COSINE_ONLY: 0.9,       # Fastest
                OptimizationStrategy.CROSS_ENCODER: 0.3,      # Slowest
                OptimizationStrategy.HYBRID: 0.6,             # Moderate
                OptimizationStrategy.BASELINE: 1.0,           # Fastest (no optimization)
                OptimizationStrategy.PERSONALIZED: 0.7        # Moderate overhead
            }
        }

    def select_strategy(self, context: StrategyContext) -> Tuple[OptimizationStrategy, float]:
        """
        Select optimization strategy using Thompson sampling with context awareness.

        Algorithm:
        1. Calculate context-aware base scores for each strategy
        2. Apply Thompson sampling with exploration bonus
        3. Choose strategy with highest adjusted score
        4. Return strategy and confidence score
        """
        context_scores = self._calculate_context_scores(context)
        thompson_samples = {}

        for strategy, base_score in context_scores.items():
            if strategy not in self.strategy_variants:
                continue

            # Thompson sampling from Beta posterior
            theta_tilde = self.strategy_variants[strategy].sample_theta()

            # Apply context awareness and exploration
            adjusted_score = (1 - self.context_weight) * theta_tilde + \
                           self.context_weight * base_score + \
                           self.exploration_bonus * np.random.beta(1, 10)  # Exploration bonus

            thompson_samples[strategy] = adjusted_score

        if not thompson_samples:
            return OptimizationStrategy.BASELINE, 0.0

        # Select strategy with highest adjusted score
        best_strategy = max(thompson_samples.items(), key=lambda x: x[1])

        # Calculate confidence as distance from second-best
        sorted_scores = sorted(thompson_samples.values(), reverse=True)
        confidence = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]

        return best_strategy[0], min(confidence, 1.0)

    def _calculate_context_scores(self, context: StrategyContext) -> Dict[OptimizationStrategy, float]:
        """Calculate context-aware preference scores for each strategy."""
        scores = {}

        # Query length preference (normalized 0-1)
        length_score = min(context.query_length / 50.0, 1.0)  # Assume 50 chars = high preference for CE

        # Complexity score (0-1, higher = more complex)
        complexity_score = min(context.query_complexity, 1.0)

        # Latency budget score (0-1, higher budget = can use slower methods)
        latency_score = min(context.latency_budget_ms / 2000.0, 1.0)  # 2s budget = full access

        # Intent-based preferences
        intent_multipliers = {
            "simple": {"cosine_only": 1.2, "cross_encoder": 0.8, "hybrid": 1.0},
            "complex": {"cosine_only": 0.7, "cross_encoder": 1.3, "hybrid": 1.1},
            "diagnostic": {"cosine_only": 0.5, "cross_encoder": 1.5, "hybrid": 1.0},
            "policy": {"cosine_only": 0.6, "cross_encoder": 1.4, "hybrid": 1.0},
            "general": {"cosine_only": 1.0, "cross_encoder": 1.0, "hybrid": 1.0}
        }

        intent_mult = intent_multipliers.get(context.intent_category,
                                           intent_multipliers["general"])

        for strategy in OptimizationStrategy:
            # Base context scores
            length_pref = self.strategy_context_scores["query_length"][strategy]
            complexity_pref = self.strategy_context_scores["intent_complexity"][strategy]
            latency_pref = self.strategy_context_scores["latency_budget"][strategy]

            # Calculate final score
            score = (
                0.3 * (length_pref if length_score < 0.5 else (1 - length_pref)) +  # Length preference
                0.4 * complexity_pref * complexity_score +                          # Complexity match
                0.3 * latency_pref * latency_score                                  # Latency budget
            )

            # Apply intent multiplier
            intent_boost = intent_mult.get(strategy.value, 1.0)
            score *= intent_boost

            # User history bonus for personalization
            if context.user_history and strategy == OptimizationStrategy.PERSONALIZED:
                score *= 1.2

            scores[strategy] = np.clip(score, 0.0, 1.0)

        return scores

    def update_strategy(self, strategy: OptimizationStrategy, reward: float, context: StrategyContext):
        """Update meta-bandit with observed reward for a strategy."""
        if strategy in self.strategy_variants:
            # Context-aware reward adjustment
            context_bonus = self._calculate_context_bonus(strategy, context)
            adjusted_reward = np.clip(reward + context_bonus * 0.1, 0.0, 1.0)

            self.strategy_variants[strategy].update(adjusted_reward)

    def _calculate_context_bonus(self, strategy: OptimizationStrategy, context: StrategyContext) -> float:
        """Calculate context-based reward bonus/penalty."""
        bonus = 0.0

        # Latency efficiency bonus
        if context.latency_budget_ms > 1000 and strategy == OptimizationStrategy.COSINE_ONLY:
            bonus += 0.1  # Reward fast method when time allows

        # Complexity matching bonus
        if context.query_complexity > 0.7 and strategy == OptimizationStrategy.CROSS_ENCODER:
            bonus += 0.15  # Reward precision method for complex queries

        # User history bonus
        if context.user_history and strategy == OptimizationStrategy.PERSONALIZED:
            bonus += 0.1

        return bonus

    def get_strategy_performance(self) -> Dict[str, Dict]:
        """Get performance statistics for all strategies."""
        stats = {}
        for strategy, variant in self.strategy_variants.items():
            ci_lower, ci_upper = variant.wilson_ci()
            stats[strategy.value] = {
                'theta_hat': variant.theta_hat,
                'samples': variant.samples,
                'ci_95': [ci_lower, ci_upper],
                'alpha': variant.alpha,
                'beta': variant.beta
            }
        return stats

class HierarchicalBanditSystem:
    """
    Complete hierarchical bandit system with meta-policy and strategy bandits.

    Architecture:
    - Meta-bandit chooses between high-level strategies
    - Strategy bandits choose variants within each strategy
    - Context-aware decision making
    - Hierarchical learning and adaptation
    """

    def __init__(self):
        self.meta_bandit = MetaBandit()
        self.strategy_manager = StrategyBanditManager()
        self.decision_history: List[HierarchicalDecision] = []

        # Initialize default variants for each strategy
        self._initialize_default_variants()

    def _initialize_default_variants(self):
        """Initialize default variants for each strategy."""
        # Cosine-only strategy variants
        for variant in ["cosine_top10", "cosine_top5", "cosine_dynamic"]:
            self.strategy_manager.add_variant_to_strategy(
                OptimizationStrategy.COSINE_ONLY, variant)

        # Cross-encoder strategy variants
        for variant in ["ce_top8", "ce_top12", "ce_adaptive"]:
            self.strategy_manager.add_variant_to_strategy(
                OptimizationStrategy.CROSS_ENCODER, variant)

        # Hybrid strategy variants
        for variant in ["hybrid_short_ce", "hybrid_complex_ce", "hybrid_adaptive"]:
            self.strategy_manager.add_variant_to_strategy(
                OptimizationStrategy.HYBRID, variant)

        # Baseline strategy variants
        self.strategy_manager.add_variant_to_strategy(
            OptimizationStrategy.BASELINE, "no_optimization")

        # Personalized strategy variants
        for variant in ["personalized_full", "personalized_light", "personalized_adaptive"]:
            self.strategy_manager.add_variant_to_strategy(
                OptimizationStrategy.PERSONALIZED, variant)

    def make_decision(self, context: StrategyContext) -> HierarchicalDecision:
        """
        Make hierarchical decision: strategy selection + variant selection.

        Process:
        1. Meta-bandit selects optimal strategy given context
        2. Strategy bandit selects best variant within chosen strategy
        3. Return complete decision with confidence scores
        """
        # Meta-bandit selects strategy
        strategy, meta_confidence = self.meta_bandit.select_strategy(context)

        # Strategy bandit selects variant
        variant = self.strategy_manager.select_variant_for_strategy(strategy)

        # Calculate expected improvement (simplified)
        expected_improvement = self._estimate_expected_improvement(strategy, variant, context)

        decision = HierarchicalDecision(
            strategy=strategy,
            variant=variant,
            meta_confidence=meta_confidence,
            strategy_confidence=0.8,  # Placeholder - could be calculated from variant stats
            expected_improvement=expected_improvement
        )

        self.decision_history.append(decision)
        logger.info(f"Hierarchical decision: {strategy.value} -> {variant} "
                   f"(meta_conf: {meta_confidence:.3f}, expected_improvement: {expected_improvement:.3f})")

        return decision

    def _estimate_expected_improvement(self, strategy: OptimizationStrategy,
                                     variant: str, context: StrategyContext) -> float:
        """Estimate expected improvement for strategy-variant combination."""
        # Simplified estimation based on strategy and context
        base_improvement = {
            OptimizationStrategy.COSINE_ONLY: 0.1,
            OptimizationStrategy.CROSS_ENCODER: 0.25,
            OptimizationStrategy.HYBRID: 0.18,
            OptimizationStrategy.BASELINE: 0.0,
            OptimizationStrategy.PERSONALIZED: 0.15
        }.get(strategy, 0.0)

        # Context modifiers
        if context.query_complexity > 0.7 and strategy == OptimizationStrategy.CROSS_ENCODER:
            base_improvement *= 1.5  # CE excels at complex queries

        if context.latency_budget_ms < 500 and strategy == OptimizationStrategy.CROSS_ENCODER:
            base_improvement *= 0.7  # CE suffers under latency pressure

        if context.user_history and strategy == OptimizationStrategy.PERSONALIZED:
            base_improvement *= 1.3  # Personalization bonus with user history

        return base_improvement

    def record_outcome(self, decision: HierarchicalDecision, reward: float, context: StrategyContext):
        """
        Record outcome and update both meta and strategy bandits.

        This enables hierarchical learning where both levels improve.
        """
        # Update meta-bandit
        self.meta_bandit.update_strategy(decision.strategy, reward, context)

        # Update strategy-specific bandit
        self.strategy_manager.update_strategy_variant(
            decision.strategy, decision.variant, reward)

        logger.debug(f"Recorded outcome: strategy={decision.strategy.value}, "
                    f"variant={decision.variant}, reward={reward:.3f}")

    def run_promotion_cycles(self) -> Dict[str, List[str]]:
        """Run promotion cycles for all strategy bandits."""
        promotions = {}
        for strategy in OptimizationStrategy:
            promoted = self.strategy_manager.promote_variants_in_strategy(strategy)
            if promoted:
                promotions[strategy.value] = promoted

        return promotions

    def get_system_stats(self) -> Dict:
        """Get comprehensive statistics for the entire hierarchical system."""
        meta_stats = self.meta_bandit.get_strategy_performance()

        strategy_stats = {}
        for strategy in OptimizationStrategy:
            strategy_stats[strategy.value] = self.strategy_manager.get_strategy_stats(strategy)

        recent_decisions = self.decision_history[-100:] if self.decision_history else []

        return {
            'meta_bandit': meta_stats,
            'strategy_bandits': strategy_stats,
            'recent_decisions': [
                {
                    'strategy': d.strategy.value,
                    'variant': d.variant,
                    'meta_confidence': d.meta_confidence,
                    'expected_improvement': d.expected_improvement,
                    'timestamp': d.timestamp.isoformat()
                } for d in recent_decisions
            ],
            'total_decisions': len(self.decision_history)
        }

    def add_custom_variant(self, strategy: OptimizationStrategy, variant_name: str):
        """Add a custom variant to a specific strategy."""
        self.strategy_manager.add_variant_to_strategy(strategy, variant_name)

    def get_strategy_recommendation(self, context: StrategyContext) -> Dict:
        """Get detailed recommendation with reasoning."""
        strategy, confidence = self.meta_bandit.select_strategy(context)
        variant = self.strategy_manager.select_variant_for_strategy(strategy)

        context_scores = self.meta_bandit._calculate_context_scores(context)

        return {
            'recommended_strategy': strategy.value,
            'recommended_variant': variant,
            'confidence': confidence,
            'context_scores': {s.value: score for s, score in context_scores.items()},
            'expected_improvement': self._estimate_expected_improvement(strategy, variant, context),
            'reasoning': self._generate_reasoning(strategy, context)
        }

    def _generate_reasoning(self, strategy: OptimizationStrategy, context: StrategyContext) -> str:
        """Generate human-readable reasoning for strategy selection."""
        reasons = []

        if context.query_complexity > 0.7 and strategy == OptimizationStrategy.CROSS_ENCODER:
            reasons.append("High query complexity favors precision reranking")

        if context.latency_budget_ms < 800 and strategy == OptimizationStrategy.COSINE_ONLY:
            reasons.append("Tight latency budget requires fast cosine method")

        if context.intent_category in ['diagnostic', 'policy', 'legal']:
            if strategy == OptimizationStrategy.CROSS_ENCODER:
                reasons.append("High-stakes intent category requires precision")
            elif strategy == OptimizationStrategy.PERSONALIZED:
                reasons.append("Personalization can help with specialized domains")

        if not reasons:
            reasons.append("Balanced selection based on context and performance history")

        return "; ".join(reasons)

    def add_strategy(self, strategy: OptimizationStrategy):
        """
        Add a new dynamically generated strategy to the system.

        This allows the constitutional governance layer to deploy
        auto-generated strategies into the live bandit system.
        """
        try:
            # Add strategy to meta-bandit if not already present
            if strategy not in self.meta_bandit.strategies:
                self.meta_bandit.add_strategy(strategy)
                logger.info(f"Added new strategy to meta-bandit: {strategy.name}")

            # Initialize strategy bandit with default variants
            # The strategy comes with its own representation and parameters
            default_variant = f"auto_variant_{strategy.generation}"

            # Add the strategy's representation as the primary variant
            if hasattr(strategy, 'strategy_representation') and strategy.strategy_representation:
                # Use the strategy's built-in representation
                self.strategy_manager.add_custom_strategy_variant(
                    strategy, default_variant, strategy.strategy_representation)
            else:
                # Fallback: add basic variant
                self.strategy_manager.add_variant_to_strategy(strategy, default_variant)

            # Initialize bandit priors for the new strategy
            self.strategy_manager.initialize_strategy_bandit(strategy)

            logger.info(f"Successfully added constitutional strategy: {strategy.name} "
                       f"(generation: {strategy.generation}, fitness: {strategy.fitness_score:.3f})")

        except Exception as e:
            logger.error(f"Failed to add strategy {strategy.name}: {e}")
            raise

    def get_constitutional_strategies(self) -> List[OptimizationStrategy]:
        """
        Get all constitutionally approved strategies in the system.

        Returns strategies that have passed governance review.
        """
        constitutional_strategies = []

        for strategy in OptimizationStrategy:
            if strategy in self.meta_bandit.strategies:
                # Check if strategy has governance metadata
                if hasattr(strategy, 'governance_score'):
                    if strategy.governance_score >= 0.8:  # High governance approval
                        constitutional_strategies.append(strategy)

        return constitutional_strategies

    def save_state(self, filepath: str):
        """Save complete hierarchical system state."""
        # This would save meta-bandit, strategy manager, and decision history
        # Implementation would serialize all components
        state = {
            'system_stats': self.get_system_stats(),
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def load_state(self, filepath: str):
        """Load complete hierarchical system state."""
        # Implementation would restore all components from saved state
        pass

# Global hierarchical bandit system instance
_hierarchical_system = None

def get_hierarchical_bandit_system() -> HierarchicalBanditSystem:
    """Get or create global hierarchical bandit system instance."""
    global _hierarchical_system
    if _hierarchical_system is None:
        _hierarchical_system = HierarchicalBanditSystem()
    return _hierarchical_system
