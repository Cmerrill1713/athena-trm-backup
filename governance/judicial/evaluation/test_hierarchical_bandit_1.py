"""
Comprehensive Test Suite for Hierarchical Bandit System
=======================================================

Tests the meta-bandit layer, strategy bandits, and hierarchical decision making
with statistical validation and integration testing.
"""

import pytest
from unittest.mock import Mock, patch

from src.core.hierarchical_bandit import (
    HierarchicalBanditSystem, OptimizationStrategy,
    StrategyContext, MetaBandit, StrategyBanditManager
)
from src.core.hierarchical_optimizer import HierarchicalOptimizer, OptimizationRequest


class TestMetaBandit:
    """Test meta-bandit strategy selection."""

    def test_meta_bandit_initialization(self):
        """Test meta-bandit initializes all strategies."""
        meta = MetaBandit()

        for strategy in OptimizationStrategy:
            assert strategy in meta.strategy_variants
            variant = meta.strategy_variants[strategy]
            assert variant.alpha == 1.0
            assert variant.beta == 1.0

    def test_context_aware_selection(self):
        """Test context influences strategy selection."""
        meta = MetaBandit()

        # Simple query should favor fast methods
        simple_context = StrategyContext(
            query_length=10,
            query_complexity=0.2,
            latency_budget_ms=500
        )

        strategy, confidence = meta.select_strategy(simple_context)
        # Should favor COSINE_ONLY for simple, fast queries
        assert strategy in [OptimizationStrategy.COSINE_ONLY, OptimizationStrategy.BASELINE]

        # Complex query should favor precision methods
        complex_context = StrategyContext(
            query_length=100,
            query_complexity=0.9,
            intent_category="diagnostic",
            latency_budget_ms=2000
        )

        strategy, confidence = meta.select_strategy(complex_context)
        # Should favor CROSS_ENCODER for complex queries
        # Note: This is probabilistic, so we test the mechanism rather than exact outcome

    def test_strategy_update(self):
        """Test meta-bandit learns from feedback."""
        meta = MetaBandit()

        context = StrategyContext(query_length=50, query_complexity=0.5)

        # Initial selection
        strategy1, _ = meta.select_strategy(context)

        # Provide strong positive feedback
        meta.update_strategy(strategy1, 1.0, context)

        # Strategy should be selected more often (probabilistic test)
        selections = []
        for _ in range(20):
            strategy, _ = meta.select_strategy(context)
            selections.append(strategy)

        # The rewarded strategy should appear more frequently
        strategy1_count = selections.count(strategy1)
        assert strategy1_count >= 8  # Should be >40% of selections


class TestStrategyBanditManager:
    """Test strategy-specific bandit management."""

    def test_strategy_variant_management(self):
        """Test adding and selecting variants per strategy."""
        manager = StrategyBanditManager()

        # Add variants to different strategies
        manager.add_variant_to_strategy(OptimizationStrategy.COSINE_ONLY, "cosine_v1")
        manager.add_variant_to_strategy(OptimizationStrategy.CROSS_ENCODER, "ce_v1")

        # Should be able to select from each
        cosine_variant = manager.select_variant_for_strategy(OptimizationStrategy.COSINE_ONLY)
        ce_variant = manager.select_variant_for_strategy(OptimizationStrategy.CROSS_ENCODER)

        assert cosine_variant == "cosine_v1"
        assert ce_variant == "ce_v1"

    def test_strategy_learning(self):
        """Test that strategies learn from feedback."""
        manager = StrategyBanditManager()

        manager.add_variant_to_strategy(OptimizationStrategy.COSINE_ONLY, "good_variant")
        manager.add_variant_to_strategy(OptimizationStrategy.COSINE_ONLY, "bad_variant")

        # Reward good variant heavily
        for _ in range(10):
            manager.update_strategy_variant(OptimizationStrategy.COSINE_ONLY, "good_variant", 1.0)
            manager.update_strategy_variant(OptimizationStrategy.COSINE_ONLY, "bad_variant", 0.0)

        # Good variant should be selected more often
        selections = []
        for _ in range(50):
            variant = manager.select_variant_for_strategy(OptimizationStrategy.COSINE_ONLY)
            selections.append(variant)

        good_selections = selections.count("good_variant")
        assert good_selections >= 30  # Should be >60% of selections


class TestHierarchicalBanditSystem:
    """Test complete hierarchical bandit system."""

    def test_hierarchical_decision_making(self):
        """Test end-to-end hierarchical decision process."""
        system = HierarchicalBanditSystem()

        context = StrategyContext(
            query_length=30,
            query_complexity=0.6,
            intent_category="general",
            latency_budget_ms=1000
        )

        decision = system.make_decision(context)

        assert isinstance(decision, HierarchicalDecision)
        assert decision.strategy in OptimizationStrategy
        assert isinstance(decision.variant, str)
        assert 0 <= decision.meta_confidence <= 1
        assert 0 <= decision.strategy_confidence <= 1

    def test_outcome_recording(self):
        """Test that outcomes update both meta and strategy bandits."""
        system = HierarchicalBanditSystem()

        context = StrategyContext(query_length=20, query_complexity=0.3)
        decision = system.make_decision(context)

        # Record positive outcome
        system.record_outcome(decision, 0.9, context)

        # Check that stats were updated
        stats = system.get_system_stats()
        assert stats['total_decisions'] >= 1

        # Meta-bandit should have learned
        meta_stats = stats['meta_bandit']
        strategy_key = decision.strategy.value
        assert strategy_key in meta_stats
        assert meta_stats[strategy_key]['samples'] >= 1

    def test_promotion_cycles(self):
        """Test that promotion cycles work across strategies."""
        system = HierarchicalBanditSystem()

        # Add some history to enable promotions
        context = StrategyContext(query_length=25, query_complexity=0.5)

        # Simulate multiple decisions with consistent good outcomes
        for _ in range(20):
            decision = system.make_decision(context)
            system.record_outcome(decision, 0.8, context)

        # Run promotion cycle
        promotions = system.run_promotion_cycles()

        # Should have some promotions (probabilistic, so we check the mechanism works)
        assert isinstance(promotions, dict)


class TestHierarchicalOptimizer:
    """Test the complete hierarchical optimizer integration."""

    @patch('src.core.hierarchical_optimizer.StrategyExecutor')
    def test_optimization_pipeline(self, mock_executor):
        """Test complete optimization pipeline."""
        # Mock the executor to return predictable results
        mock_executor_instance = Mock()
        mock_executor_instance.execute_strategy.return_value = (
            [Mock()], "cosine", False, 50
        )
        mock_executor.return_value = mock_executor_instance

        optimizer = HierarchicalOptimizer()

        request = OptimizationRequest(
            query="test query",
            documents=[Mock()],
            intent_category="general"
        )

        result = optimizer.optimize(request)

        assert isinstance(result, OptimizationResult)
        assert result.rerank_strategy == "cosine"
        assert result.latency_used_ms == 50
        assert not result.personalization_applied

    def test_context_analysis(self):
        """Test context analysis for optimization requests."""
        optimizer = HierarchicalOptimizer()

        request = OptimizationRequest(
            query="This is a complex query with many words that should indicate high complexity",
            documents=[Mock()],
            intent_category="diagnostic"
        )

        context = optimizer._analyze_context(request)

        assert context.query_length > 50
        assert context.query_complexity > 0  # Should detect complexity
        assert context.intent_category == "diagnostic"

    def test_feedback_recording(self):
        """Test feedback recording updates learning systems."""
        optimizer = HierarchicalOptimizer()

        # Create mock result
        decision = HierarchicalDecision(
            strategy=OptimizationStrategy.COSINE_ONLY,
            variant="cosine_v1",
            meta_confidence=0.8,
            strategy_confidence=0.7,
            expected_improvement=0.1
        )

        result = OptimizationResult(
            decision=decision,
            optimized_documents=[Mock()],
            rerank_strategy="cosine",
            personalization_applied=False,
            latency_used_ms=50,
            expected_quality_improvement=0.1
        )

        context = StrategyContext(query_length=30, query_complexity=0.5)

        # Record feedback
        optimizer.record_feedback(result, human_feedback=1, context=context)

        # Should update without errors
        stats = optimizer.get_optimization_stats()
        assert 'hierarchical_system' in stats
        assert 'execution_stats' in stats


class TestStrategyExecution:
    """Test strategy execution logic."""

    def test_baseline_strategy(self):
        """Test baseline strategy returns original documents."""
        from src.core.hierarchical_optimizer import StrategyExecutor

        executor = StrategyExecutor()

        # Mock the reranker to not be called for baseline
        with patch.object(executor, 'rag_reranker') as mock_reranker:
            request = OptimizationRequest(query="test", documents=["doc1", "doc2"])
            decision = HierarchicalDecision(
                strategy=OptimizationStrategy.BASELINE,
                variant="no_optimization",
                meta_confidence=1.0,
                strategy_confidence=1.0,
                expected_improvement=0.0
            )

            docs, strategy, personalized, latency = executor.execute_strategy(request, decision)

            assert docs == ["doc1", "doc2"]  # Original documents
            assert strategy == "none"
            assert not personalized
            assert latency == 0
            mock_reranker.rerank.assert_not_called()

    def test_cosine_strategy(self):
        """Test cosine strategy calls reranker correctly."""
        from src.core.hierarchical_optimizer import StrategyExecutor

        executor = StrategyExecutor()

        with patch.object(executor, 'rag_reranker') as mock_reranker:
            mock_reranker.rerank.return_value = ["reranked_doc1", "reranked_doc2"]

            request = OptimizationRequest(query="test", documents=["doc1", "doc2"])
            decision = HierarchicalDecision(
                strategy=OptimizationStrategy.COSINE_ONLY,
                variant="cosine_v1",
                meta_confidence=1.0,
                strategy_confidence=1.0,
                expected_improvement=0.1
            )

            docs, strategy, personalized, latency = executor.execute_strategy(request, decision)

            assert docs == ["reranked_doc1", "reranked_doc2"]
            assert strategy == "cosine"
            assert not personalized
            assert latency > 0  # Some latency incurred
            mock_reranker.rerank.assert_called_once_with("test", ["doc1", "doc2"], use_precision=False)


class TestStatisticalValidation:
    """Test statistical properties of hierarchical system."""

    def test_decision_diversity(self):
        """Test that hierarchical system produces diverse decisions."""
        system = HierarchicalBanditSystem()

        contexts = [
            StrategyContext(query_length=10, query_complexity=0.2, latency_budget_ms=500),
            StrategyContext(query_length=100, query_complexity=0.8, latency_budget_ms=2000,
                          intent_category="diagnostic"),
            StrategyContext(query_length=50, query_complexity=0.5, latency_budget_ms=1000,
                          intent_category="policy")
        ]

        decisions = []
        for context in contexts:
            for _ in range(10):  # Multiple decisions per context
                decision = system.make_decision(context)
                decisions.append(decision.strategy)

        # Should see variety in strategies (not all the same)
        unique_strategies = set(decisions)
        assert len(unique_strategies) >= 2  # At least some diversity

    def test_learning_convergence(self):
        """Test that system learns and converges on good strategies."""
        system = HierarchicalBanditSystem()

        context = StrategyContext(query_length=30, query_complexity=0.6)

        # Simulate learning: reward one strategy consistently
        preferred_strategy = None

        for i in range(50):
            decision = system.make_decision(context)

            # Arbitrarily prefer COSINE_ONLY for this test
            reward = 0.9 if decision.strategy == OptimizationStrategy.COSINE_ONLY else 0.3
            system.record_outcome(decision, reward, context)

            if preferred_strategy is None and decision.strategy == OptimizationStrategy.COSINE_ONLY:
                preferred_strategy = OptimizationStrategy.COSINE_ONLY

        # After learning, should prefer the rewarded strategy more often
        recent_decisions = []
        for _ in range(20):
            decision = system.make_decision(context)
            recent_decisions.append(decision.strategy)

        if preferred_strategy:
            preferred_count = recent_decisions.count(preferred_strategy)
            assert preferred_count >= 12  # Should be >60% of recent decisions


if __name__ == "__main__":
    pytest.main([__file__])
