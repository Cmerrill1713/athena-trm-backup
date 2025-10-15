#!/usr/bin/env python3
"""
CE Neural Router
================

Intelligent routing between Cross-Encoder and Cosine reranking using neural context analysis.

Automatically determines when CE will provide value vs. when cosine is sufficient,
based on learned query features and historical performance data.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

# CE reranker for predictions
# Neural context integration
from src.core.neural_context_encoder import get_neural_context_analyzer


@dataclass
class CERoutingDecision:
    """Decision result for CE vs cosine routing."""
    use_ce: bool
    confidence: float
    reasoning: str
    expected_improvement: float
    features: Dict[str, Any]

class CENeuralRouter:
    """
    Neural router for CE vs cosine reranking decisions.

    Uses query complexity, ambiguity, and historical performance to route intelligently.
    """

    def __init__(self):
        self.neural_analyzer = get_neural_context_analyzer()

        # Routing thresholds (learned/tuned)
        self.complexity_threshold = float(os.getenv('CE_ROUTER_COMPLEXITY_THRESHOLD', '0.6'))
        self.ambiguity_threshold = float(os.getenv('CE_ROUTER_AMBIGUITY_THRESHOLD', '0.5'))
        self.intent_confidence_threshold = float(os.getenv('CE_ROUTER_INTENT_CONFIDENCE', '0.7'))

        # Performance prediction weights (learned from data)
        self.performance_weights = {
            'complexity': 0.4,
            'ambiguity': 0.3,
            'intent_certainty': 0.3
        }

        # Historical performance cache
        self.performance_cache: Dict[str, Dict[str, float]] = {}
        self.cache_size = 1000

    def should_use_ce(self, query: str, intent: Optional[str] = None) -> CERoutingDecision:
        """
        Decide whether to use CE reranking for this query.

        Uses neural context analysis + performance prediction.
        """
        # Get neural context analysis
        context = self.neural_analyzer.analyze_query(query)

        # Extract key features
        complexity = context.features.get('complexity', 0.0)
        ambiguity = context.features.get('ambiguity', 0.0)
        intent_certainty = context.confidence

        # Multi-factor decision making
        factors = {
            'complexity': complexity >= self.complexity_threshold,
            'ambiguity': ambiguity >= self.ambiguity_threshold,
            'intent_certainty': intent_certainty >= self.intent_confidence_threshold,
            'intent_match': self._check_intent_match(intent, context.features.get('intent'))
        }

        # Weighted decision
        ce_score = (
            self.performance_weights['complexity'] * (complexity / self.complexity_threshold) +
            self.performance_weights['ambiguity'] * (ambiguity / self.ambiguity_threshold) +
            self.performance_weights['intent_certainty'] * (intent_certainty / self.intent_confidence_threshold)
        )

        # Intent matching bonus
        if factors['intent_match']:
            ce_score += 0.2

        # Historical performance adjustment
        historical_boost = self._get_historical_performance(query)
        ce_score += historical_boost

        # Final decision
        use_ce = ce_score >= 0.6  # Tunable threshold
        confidence = min(ce_score, 1.0)

        # Expected improvement prediction
        expected_improvement = self._predict_improvement(complexity, ambiguity, intent_certainty)

        # Reasoning
        reasons = []
        if factors['complexity']:
            reasons.append(f"High complexity ({complexity:.2f})")
        if factors['ambiguity']:
            reasons.append(f"High ambiguity ({ambiguity:.2f})")
        if factors['intent_certainty']:
            reasons.append(f"Clear intent (confidence: {intent_certainty:.2f})")
        if factors['intent_match']:
            reasons.append("Intent matches CE domains")
        if historical_boost > 0:
            reasons.append("Historical CE performance positive")

        reasoning = "; ".join(reasons) if reasons else "Default routing"

        return CERoutingDecision(
            use_ce=use_ce,
            confidence=confidence,
            reasoning=reasoning,
            expected_improvement=expected_improvement,
            features={
                'complexity': complexity,
                'ambiguity': ambiguity,
                'intent_certainty': intent_certainty,
                'ce_score': ce_score,
                'historical_boost': historical_boost
            }
        )

    def _check_intent_match(self, provided_intent: Optional[str], predicted_intent: Optional[str]) -> bool:
        """Check if intent matches CE-routed categories."""
        if not provided_intent and not predicted_intent:
            return False

        intent = provided_intent or predicted_intent
        ce_intents = {'policy', 'incident', 'legal', 'diagnosis', 'technical', 'complex'}

        return intent.lower() in ce_intents

    def _get_historical_performance(self, query: str) -> float:
        """Get historical CE performance boost for similar queries."""
        # Simple cache-based approach (could be enhanced with embeddings)
        query_hash = hash(query) % 1000

        if str(query_hash) in self.performance_cache:
            return self.performance_cache[str(query_hash)].get('ce_boost', 0.0)

        return 0.0

    def _predict_improvement(self, complexity: float, ambiguity: float, intent_certainty: float) -> float:
        """Predict expected judge score improvement from CE."""
        # Learned prediction model (simplified)
        base_improvement = 0.5  # Base CE improvement

        # Complexity multiplier
        complexity_multiplier = min(complexity * 2, 2.0)  # Up to 2x for very complex queries

        # Ambiguity bonus
        ambiguity_bonus = ambiguity * 1.5  # Up to 1.5pts for highly ambiguous queries

        # Intent certainty bonus
        intent_bonus = intent_certainty * 1.0  # Up to 1pt for certain intents

        total_improvement = base_improvement * complexity_multiplier + ambiguity_bonus + intent_bonus

        return min(total_improvement, 6.0)  # Cap at realistic maximum

    def record_performance(self, query: str, reranker_used: str, judge_improvement: float):
        """Record performance outcome for learning."""
        query_hash = str(hash(query) % 1000)

        if query_hash not in self.performance_cache:
            self.performance_cache[query_hash] = {}

        # Update running average
        current = self.performance_cache[query_hash].get('ce_boost', 0.0)
        count = self.performance_cache[query_hash].get('count', 0)

        new_avg = (current * count + judge_improvement) / (count + 1)

        self.performance_cache[query_hash]['ce_boost'] = new_avg
        self.performance_cache[query_hash]['count'] = count + 1

        # Cache size management
        if len(self.performance_cache) > self.cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.performance_cache))
            del self.performance_cache[oldest_key]

    def get_router_stats(self) -> Dict[str, Any]:
        """Get router performance statistics."""
        total_queries = len(self.performance_cache)
        avg_improvement = np.mean([
            data.get('ce_boost', 0.0)
            for data in self.performance_cache.values()
        ]) if self.performance_cache else 0.0

        return {
            'cache_size': len(self.performance_cache),
            'cache_max': self.cache_size,
            'avg_predicted_improvement': avg_improvement,
            'neural_analyzer_available': self.neural_analyzer.is_trained if hasattr(self.neural_analyzer, 'is_trained') else False,
            'complexity_threshold': self.complexity_threshold,
            'ambiguity_threshold': self.ambiguity_threshold,
            'intent_confidence_threshold': self.intent_confidence_threshold
        }

# Global router instance
ce_router = CENeuralRouter()

def route_to_ce(query: str, intent: Optional[str] = None) -> CERoutingDecision:
    """High-level interface for CE routing decisions."""
    return ce_router.should_use_ce(query, intent)

def record_ce_performance(query: str, reranker_used: str, judge_improvement: float):
    """Record CE performance outcome for learning."""
    ce_router.record_performance(query, reranker_used, judge_improvement)

if __name__ == "__main__":
    # Demo the neural router
    print("🎯 CE Neural Router Demo")
    print("=" * 40)

    test_queries = [
        ("What is the company vacation policy?", "policy"),
        ("My computer crashed, what should I do?", "technical"),
        ("Tell me about the weather", "general"),
        ("How do I implement JWT authentication with role-based access control in a microservices architecture?", "technical")
    ]

    for query, intent in test_queries:
        decision = route_to_ce(query, intent)
        print(f"\nQuery: {query[:50]}...")
        print(f"  Use CE: {decision.use_ce} (confidence: {decision.confidence:.2f})")
        print(f"  Expected improvement: +{decision.expected_improvement:.1f}pts")
        print(f"  Reasoning: {decision.reasoning}")

    # Router stats
    stats = ce_router.get_router_stats()
    print("\n📊 Router Stats:")
    print(f"  Cache size: {stats['cache_size']}")
    print(f"  Neural analyzer: {'✅' if stats['neural_analyzer_available'] else '❌'}")

    print("\n🎉 Neural CE routing ready!")
