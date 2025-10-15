"""
Hierarchical Optimizer Integration Layer
========================================

Integrates the hierarchical bandit system with existing optimization components:

- Meta-bandit chooses between: cosine-only, CE, hybrid, baseline, personalized
- Each strategy routes to appropriate optimization logic
- Unified interface for the optimization pipeline
- Context-aware decision making with statistical guarantees
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .automated_strategy_generation import get_automated_strategy_generation
from .bandit_optimizer import get_bandit_optimizer
from .hierarchical_bandit import (
    HierarchicalBanditSystem,
    HierarchicalDecision,
    OptimizationStrategy,
    StrategyContext,
)
from .neural_context_encoder import QueryContext, get_neural_context_analyzer
from .personalization_engine import get_personalization_engine
from .rag_reranker import get_rag_reranker
from .reward_shaper import get_reward_shaper

logger = logging.getLogger(__name__)

@dataclass
class OptimizationRequest:
    """Request for optimization with full context."""
    query: str
    documents: List[Any]
    user_id: Optional[str] = None
    intent_category: str = "general"
    latency_budget_ms: int = 1000
    quality_requirement: str = "balanced"

@dataclass
class OptimizationResult:
    """Result of hierarchical optimization."""
    decision: HierarchicalDecision
    optimized_documents: List[Any]
    rerank_strategy: str
    personalization_applied: bool
    latency_used_ms: int
    expected_quality_improvement: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class StrategyExecutor:
    """
    Executes specific optimization strategies based on hierarchical decisions.

    Maps each strategy to its implementation logic:
    - COSINE_ONLY: Basic cosine similarity reranking
    - CROSS_ENCODER: CE reranking for precision
    - HYBRID: Adaptive based on query characteristics
    - BASELINE: No optimization
    - PERSONALIZED: User-adaptive optimization
    """

    def __init__(self):
        self.rag_reranker = get_rag_reranker()
        self.personalization = get_personalization_engine()
        self.bandit_optimizer = get_bandit_optimizer()

    def execute_strategy(self, request: OptimizationRequest,
                        decision: HierarchicalDecision) -> Tuple[List[Any], str, bool, int]:
        """
        Execute the chosen optimization strategy.

        Returns: (optimized_docs, rerank_strategy, personalization_applied, latency_used)
        """
        start_time = datetime.now()

        if decision.strategy == OptimizationStrategy.BASELINE:
            # No optimization - return original order
            return request.documents, "none", False, 0

        elif decision.strategy == OptimizationStrategy.COSINE_ONLY:
            # Basic cosine reranking only
            optimized_docs = self.rag_reranker.rerank(
                request.query, request.documents, use_precision=False)
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return optimized_docs, "cosine", False, int(latency)

        elif decision.strategy == OptimizationStrategy.CROSS_ENCODER:
            # Cross-encoder precision reranking
            optimized_docs = self.rag_reranker.rerank(
                request.query, request.documents, use_precision=True)
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return optimized_docs, "cross_encoder", False, int(latency)

        elif decision.strategy == OptimizationStrategy.HYBRID:
            # Adaptive reranking based on query characteristics
            use_precision = self._should_use_precision_hybrid(request)
            optimized_docs = self.rag_reranker.rerank(
                request.query, request.documents, use_precision=use_precision)
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return optimized_docs, "hybrid", False, int(latency)

        elif decision.strategy == OptimizationStrategy.PERSONALIZED:
            # User-adaptive optimization
            use_precision = self._should_use_precision_personalized(request)

            # Get user signal
            user_signal = None
            if request.user_id:
                user_signal = self.personalization.get_personalization_signal(request.user_id)

            # Apply personalization bias if user signal available
            docs_for_rerank = request.documents
            personalization_applied = False

            if user_signal and user_signal.confidence > 0.3:
                docs_for_rerank = self.personalization.apply_personalization_bias(
                    request.documents, user_signal)
                personalization_applied = True

            # Rerank with personalized documents
            optimized_docs = self.rag_reranker.rerank(
                request.query, docs_for_rerank, use_precision=use_precision)

            latency = (datetime.now() - start_time).total_seconds() * 1000
            return optimized_docs, "personalized", personalization_applied, int(latency)

        else:
            # Fallback to baseline
            return request.documents, "fallback", False, 0

    def _should_use_precision_hybrid(self, request: OptimizationRequest) -> bool:
        """Determine if hybrid strategy should use precision reranking."""
        # Use precision for complex queries or high-stakes intents
        query_complexity = len(request.query.split()) / 50.0  # Normalize by expected length

        precision_triggers = [
            query_complexity > 0.8,  # Very long queries
            request.intent_category in ['diagnostic', 'policy', 'legal'],
            request.latency_budget_ms > 800  # Time to be precise
        ]

        return any(precision_triggers)

    def _should_use_precision_personalized(self, request: OptimizationRequest) -> bool:
        """Determine precision usage for personalized strategy."""
        # More conservative precision usage for personalized (latency matters more)
        return (request.intent_category in ['diagnostic', 'policy'] and
                request.latency_budget_ms > 1200)

class HierarchicalOptimizer:
    """
    Main interface for hierarchical optimization system.

    Orchestrates the complete optimization pipeline:
    1. Context analysis
    2. Hierarchical decision making
    3. Strategy execution
    4. Result aggregation
    5. Learning from outcomes
    """

    def __init__(self):
        self.hierarchical_system = HierarchicalBanditSystem()
        self.strategy_executor = StrategyExecutor()
        self.reward_shaper = get_reward_shaper()
        self.neural_analyzer = get_neural_context_analyzer()
        self.strategy_generator = get_automated_strategy_generation()

        # Optimization history for analysis (used for strategy generation)
        self.optimization_history: List[OptimizationResult] = []
        self.historical_queries: List[Tuple[QueryContext, List[Any], float]] = []

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """
        Execute hierarchical optimization for a request.

        Full pipeline:
        1. Analyze context
        2. Make hierarchical decision
        3. Execute chosen strategy
        4. Return optimization result
        """
        # Analyze context for decision making
        context = self._analyze_context(request)

        # Make hierarchical decision
        decision = self.hierarchical_system.make_decision(context)

        # Check for automated strategy suggestions
        auto_suggestions = self.strategy_generator.get_strategy_suggestions(context)
        if auto_suggestions and auto_suggestions[0][1] > 0.8:  # High confidence suggestion
            suggested_strategy_id, confidence = auto_suggestions[0]
            # In practice, this would map the auto-generated strategy to the decision
            logger.info(f"Using auto-generated strategy suggestion: {suggested_strategy_id} "
                       f"(confidence: {confidence:.3f})")

        # Execute the chosen strategy
        (optimized_docs, rerank_strategy,
         personalization_applied, latency_used) = self.strategy_executor.execute_strategy(request, decision)

        # Create result
        result = OptimizationResult(
            decision=decision,
            optimized_documents=optimized_docs,
            rerank_strategy=rerank_strategy,
            personalization_applied=personalization_applied,
            latency_used_ms=latency_used,
            expected_quality_improvement=decision.expected_improvement
        )

        self.optimization_history.append(result)

        logger.info(f"Optimization completed: {decision.strategy.value} -> {decision.variant} "
                   f"(latency: {latency_used}ms, expected_improvement: {decision.expected_improvement:.3f})")

        return result

    def _analyze_context(self, request: OptimizationRequest) -> StrategyContext:
        """Analyze request to create optimization context using neural encoder."""
        # Use neural context analyzer
        query_context = self.neural_analyzer.analyze_query(request.query)

        # Extract features for strategy selection
        features = query_context.features

        # Map neural features to strategy context
        # Use neural features if available and confident, otherwise use rule-based
        if query_context.confidence >= 0.6 and len(query_context.embedding) > 0:
            # Neural-based context
            query_complexity = features.get('complexity', 0.5)
            intent_category = self._map_neural_intent_to_category(features.get('intent', 4))

            # Enhanced complexity from neural ambiguity
            ambiguity = features.get('ambiguity', 0.5)
            query_complexity = min(query_complexity + 0.3 * ambiguity, 1.0)
        else:
            # Fallback to rule-based features
            raw_features = query_context.raw_features
            query_complexity = raw_features.get('query_complexity', 0.5)
            intent_category = raw_features.get('intent', 'general')

        # Get user history for personalization context
        user_history = None
        if request.user_id:
            user_signal = self.strategy_executor.personalization.get_personalization_signal(request.user_id)
            if user_signal.confidence > 0:
                user_history = {
                    'has_history': True,
                    'confidence': user_signal.confidence,
                    'tone_preference': user_signal.tone_hint,
                    'citation_preference': user_signal.citation_hint
                }

        # Override intent if explicitly provided
        if request.intent_category and request.intent_category != 'general':
            intent_category = request.intent_category

        return StrategyContext(
            query_length=len(request.query),
            query_complexity=min(query_complexity, 1.0),
            user_history=user_history,
            intent_category=intent_category,
            latency_budget_ms=request.latency_budget_ms,
            quality_requirement=request.quality_requirement
        )

    def _map_neural_intent_to_category(self, intent_idx: int) -> str:
        """Map neural intent classification to category strings."""
        intent_map = {
            0: 'simple',      # Simple questions
            1: 'complex',     # Complex multi-part
            2: 'diagnostic',  # Medical/technical diagnosis
            3: 'policy',      # Legal/compliance
            4: 'general'      # Everything else
        }
        return intent_map.get(intent_idx, 'general')

    def record_feedback(self, result: OptimizationResult,
                       human_feedback: Optional[int] = None,
                       judge_scores: Optional[Any] = None,
                       user_accepted: bool = True,
                       context: Optional[StrategyContext] = None):
        """
        Record feedback and update all learning systems.

        Updates hierarchical bandits, reward shaping, and neural context encoder.
        """
        # Shape reward from feedback
        feedback_signal = self.reward_shaper.FeedbackSignal(
            human_feedback=human_feedback,
            judge_scores=judge_scores,
            domain=result.decision.strategy.value
        )

        reward = self.reward_shaper.shape_reward(feedback_signal)

        # Adjust reward based on user acceptance
        if not user_accepted:
            reward *= 0.3  # Heavy penalty for rejection

        # Update hierarchical system
        if context:
            self.hierarchical_system.record_outcome(result.decision, reward, context)

        # Collect historical query data for strategy generation
        if context:
            # Store query context for automated strategy generation
            query_data = (context, result.optimized_documents, reward)
            self.historical_queries.append(query_data)

            # Keep last 1000 queries for generation
            if len(self.historical_queries) > 1000:
                self.historical_queries = self.historical_queries[-1000:]

        # Train neural context encoder with this example
        # Extract context features for training
        context_features = {}
        if context:
            context_features = {
                'query_complexity': context.query_complexity,
                'ambiguity': getattr(context, 'ambiguity', 0.5),  # If available
                'intent': context.intent_category
            }

        # Add to neural analyzer training buffer
        self.neural_analyzer.add_training_example(
            query=result.decision.variant,  # Using variant as proxy for full query context
            strategy=result.decision.strategy.value,
            reward=reward,
            context_features=context_features
        )

        # Trigger neural training if we have enough data and it's time
        if len(self.neural_analyzer.training_buffer) >= 200 and len(self.neural_analyzer.training_buffer) % 100 == 0:
            logger.info("Triggering neural context encoder training...")
            success = self.neural_analyzer.train_on_buffer(epochs=3, batch_size=16)
            if success:
                logger.info("Neural context encoder training completed successfully")
            else:
                logger.warning("Neural context encoder training did not meet quality thresholds")

        # Trigger automated strategy generation periodically
        if len(self.historical_queries) >= 500 and len(self.historical_queries) % 200 == 0:
            logger.info("Triggering automated strategy generation cycle...")
            new_strategies = self.strategy_generator.run_strategy_generation_cycle(self.historical_queries)
            if new_strategies:
                logger.info(f"Generated {len(new_strategies)} new strategy candidates")
                # Auto-deploy validated strategies
                for strategy_id in new_strategies:
                    if self.strategy_generator.deploy_strategy(strategy_id):
                        logger.info(f"Auto-deployed strategy: {strategy_id}")
            else:
                logger.info("No new strategies generated this cycle")

        logger.debug(f"Feedback recorded: reward={reward:.3f}, "
                    f"strategy={result.decision.strategy.value}, "
                    f"variant={result.decision.variant}")

    def get_optimization_stats(self) -> Dict:
        """Get comprehensive optimization statistics."""
        system_stats = self.hierarchical_system.get_system_stats()

        # Add execution statistics
        recent_results = self.optimization_history[-100:] if self.optimization_history else []

        strategy_usage = {}
        latency_stats = []
        quality_improvements = []

        for result in recent_results:
            strategy = result.decision.strategy.value
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1

            latency_stats.append(result.latency_used_ms)
            quality_improvements.append(result.expected_quality_improvement)

        execution_stats = {
            'total_optimizations': len(self.optimization_history),
            'strategy_usage': strategy_usage,
            'avg_latency_ms': np.mean(latency_stats) if latency_stats else 0,
            'p95_latency_ms': np.percentile(latency_stats, 95) if latency_stats else 0,
            'avg_quality_improvement': np.mean(quality_improvements) if quality_improvements else 0,
            'personalization_rate': sum(1 for r in recent_results if r.personalization_applied) / max(len(recent_results), 1)
        }

        return {
            'hierarchical_system': system_stats,
            'execution_stats': execution_stats
        }

    def run_maintenance(self):
        """Run maintenance operations (promotion cycles, cleanup)."""
        # Run promotion cycles for all strategies
        promotions = self.hierarchical_system.run_promotion_cycles()

        if promotions:
            logger.info(f"Strategy promotions completed: {promotions}")

        # Cleanup old history (keep last 1000)
        if len(self.optimization_history) > 1000:
            self.optimization_history = self.optimization_history[-1000:]

        # Apply exponential decay to bandits (weekly operation)
        self.hierarchical_system.meta_bandit.strategy_variants
        # Note: Decay would be applied weekly in production

    def get_strategy_recommendation(self, request: OptimizationRequest) -> Dict:
        """Get detailed strategy recommendation with reasoning."""
        context = self._analyze_context(request)
        return self.hierarchical_system.get_strategy_recommendation(context)

    def force_strategy(self, strategy: OptimizationStrategy, request: OptimizationRequest) -> OptimizationResult:
        """
        Force a specific strategy for testing/analysis purposes.

        Bypasses hierarchical decision making.
        """
        # Create mock decision
        decision = HierarchicalDecision(
            strategy=strategy,
            variant=self.hierarchical_system.strategy_manager.select_variant_for_strategy(strategy),
            meta_confidence=1.0,  # Forced
            strategy_confidence=0.8,
            expected_improvement=0.1
        )

        # Execute strategy
        (optimized_docs, rerank_strategy,
         personalization_applied, latency_used) = self.strategy_executor.execute_strategy(request, decision)

        return OptimizationResult(
            decision=decision,
            optimized_documents=optimized_docs,
            rerank_strategy=rerank_strategy,
            personalization_applied=personalization_applied,
            latency_used_ms=latency_used,
            expected_quality_improvement=decision.expected_improvement
        )

# Global hierarchical optimizer instance
_hierarchical_optimizer = None

def get_hierarchical_optimizer() -> HierarchicalOptimizer:
    """Get or create global hierarchical optimizer instance."""
    global _hierarchical_optimizer
    if _hierarchical_optimizer is None:
        _hierarchical_optimizer = HierarchicalOptimizer()
    return _hierarchical_optimizer
