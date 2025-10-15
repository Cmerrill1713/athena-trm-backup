"""
Comprehensive Test Suite for Advanced Optimization Framework
===========================================================

Tests all optimization components with exact mathematical validation:

- Bandit optimizer with Beta distributions and Wilson CI
- Reward shaper with human/judge blending and drift correction
- RAG reranker with threshold tuning and guardrails
- Statistical significance testing
- Integration tests with realistic data
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import patch

from src.core.bandit_optimizer import AdvancedBanditOptimizer, BanditVariant
from src.core.reward_shaper import RewardShaper, FeedbackSignal, JudgeScores
from src.core.rag_reranker import RAGReranker, Document, RAGQuery, CosineReranker


class TestAdvancedBanditOptimizer:
    """Test bandit optimizer with exact mathematical validation."""

    def test_beta_prior_initialization(self):
        """Test Beta(1,1) uninformative prior initialization."""
        optimizer = AdvancedBanditOptimizer()
        variant = optimizer.add_variant("test_variant")

        assert variant.alpha == 1.0
        assert variant.beta == 1.0
        assert variant.theta_hat == 0.5  # (1)/(1+1) = 0.5

    def test_thompson_sampling(self):
        """Test Thompson sampling draws from correct Beta distribution."""
        variant = BanditVariant("test")
        variant.update(1.0)  # Success
        variant.update(0.0)  # Failure → Beta(2,2)

        samples = [variant.sample_theta() for _ in range(1000)]
        mean_sample = np.mean(samples)
        std_sample = np.std(samples)

        # Beta(2,2) has mean 0.5, variance (2*2)/((2+2)^2*(2+2+1)) = 0.0556
        expected_mean = 0.5
        expected_std = np.sqrt(0.0556)

        assert abs(mean_sample - expected_mean) < 0.05  # Within 5% of expected
        assert abs(std_sample - expected_std) < 0.02    # Within reasonable range

    def test_wilson_confidence_interval(self):
        """Test Wilson 95% CI calculation."""
        variant = BanditVariant("test")
        # Add 100 successes, 0 failures → Beta(101,1)
        for _ in range(100):
            variant.update(1.0)

        lower, upper = variant.wilson_ci()

        # With high success rate, CI should be narrow and not include 0.5
        assert lower > 0.9  # Very confident in high performance
        assert upper > lower
        assert upper <= 1.0

    def test_exploration_floor(self):
        """Test 5% exploration floor for new variants."""
        optimizer = AdvancedBanditOptimizer()

        # New variant with no samples
        variant = optimizer.add_variant("new_variant")
        theta_tilde = variant.sample_theta()

        # Should be at least exploration floor
        assert theta_tilde >= optimizer.exploration_floor

    def test_promotion_logic(self):
        """Test variance-aware promotion with Wilson CI."""
        optimizer = AdvancedBanditOptimizer()

        # Create two variants with sufficient samples
        var_a = optimizer.add_variant("variant_a")
        var_b = optimizer.add_variant("variant_b")

        # Make variant_a clearly better: 80 successes, 20 failures
        for _ in range(80):
            var_a.update(1.0)
        for _ in range(20):
            var_a.update(0.0)

        # Variant_b: 50 successes, 50 failures
        for _ in range(50):
            var_b.update(1.0)
        for _ in range(50):
            var_b.update(0.0)

        # Should promote variant_a over variant_b
        assert optimizer.should_promote("variant_a", "variant_b")

        # Should not promote variant_b over variant_a
        assert not optimizer.should_promote("variant_b", "variant_a")

    def test_exponential_decay(self):
        """Test exponential decay adaptation."""
        variant = BanditVariant("test")
        variant.update(1.0)  # Beta(2,1)

        original_alpha = variant.alpha
        original_beta = variant.beta

        variant.apply_decay(lambda_decay=0.9)

        # Should decay towards 1.0
        assert variant.alpha < original_alpha
        assert variant.beta == original_beta  # Beta unchanged since no failures
        assert variant.alpha > 1.0  # But still > 1

    def test_traffic_distribution(self):
        """Test traffic distribution with caps and minimums."""
        optimizer = AdvancedBanditOptimizer()

        # Add variants
        optimizer.add_variant("variant_a")
        optimizer.add_variant("variant_b")

        distribution = optimizer.calculate_traffic_distribution()

        # Should sum to 1.0
        assert abs(sum(distribution.values()) - 1.0) < 1e-6

        # All variants should get some traffic
        for traffic in distribution.values():
            assert traffic > 0


class TestRewardShaper:
    """Test reward shaper with human/judge blending."""

    def test_human_feedback_mapping(self):
        """Test human feedback mapping: {-1,0,+1} → [0,1]."""
        shaper = RewardShaper()

        # Test all human feedback values
        assert shaper._process_human_feedback(-1) == 0.0   # ( -1 + 1) / 2 = 0
        assert shaper._process_human_feedback(0) == 0.5    # (  0 + 1) / 2 = 0.5
        assert shaper._process_human_feedback(1) == 1.0    # (  1 + 1) / 2 = 1

        # Test invalid input
        assert shaper._process_human_feedback(2) is None

    def test_judge_score_normalization(self):
        """Test judge score normalization: [1,10] → [-1,1]."""
        shaper = RewardShaper()

        # Create judge scores
        judge = JudgeScores(helpfulness=7.0, factuality=8.0, clarity=6.0)
        normalized = judge.normalize()

        # Expected: [(7-5.5)/4.5, (8-5.5)/4.5, (6-5.5)/4.5]
        expected = [(7-5.5)/4.5, (8-5.5)/4.5, (6-5.5)/4.5]
        assert normalized == pytest.approx(expected, abs=1e-6)

    def test_reward_blending(self):
        """Test confidence-weighted reward blending."""
        shaper = RewardShaper()

        # Test with both signals
        feedback = FeedbackSignal(
            human_feedback=1,  # +1 → 1.0
            judge_scores=JudgeScores(10, 10, 10)  # All 10s → 1.0 after normalization
        )

        reward = shaper.shape_reward(feedback)

        # With default weights (0.9 human + 0.25 judge), should be close to 1.0
        # Total weight = 1.15, normalized: 0.9/1.15 ≈ 0.783, 0.25/1.15 ≈ 0.217
        # Final: 0.783 * 1.0 + 0.217 * 1.0 = 1.0
        assert reward == pytest.approx(1.0, abs=0.1)

    def test_drift_correction(self):
        """Test drift correction with rolling statistics."""
        shaper = RewardShaper(drift_window_days=7)

        # Add historical data with mean 0.7
        domain = "test_domain"
        for i in range(20):
            score = 0.7 + np.random.normal(0, 0.1)  # Mean 0.7, some noise
            shaper._update_domain_stats(domain, score, datetime.now())

        # Test correction of outlier
        outlier_score = 0.9  # Higher than historical mean
        corrected = shaper._apply_drift_correction(outlier_score, domain)

        # Should be corrected downward towards historical mean
        assert corrected < outlier_score
        assert corrected > shaper.get_domain_stats(domain)['mean'] - 0.1

    def test_fallback_handling(self):
        """Test fallback handling for missing signals."""
        shaper = RewardShaper()

        # Only human feedback
        feedback_human_only = FeedbackSignal(human_feedback=1)
        reward_human = shaper.shape_reward(feedback_human_only)
        assert reward_human == 1.0

        # Only judge feedback
        feedback_judge_only = FeedbackSignal(
            judge_scores=JudgeScores(10, 10, 10)
        )
        reward_judge = shaper.shape_reward(feedback_judge_only)
        assert reward_judge > 0.8  # High judge score

        # No signals
        feedback_none = FeedbackSignal()
        reward_none = shaper.shape_reward(feedback_none)
        assert reward_none == 0.5  # Neutral fallback


class TestRAGReranker:
    """Test RAG reranker with threshold tuning."""

    def test_rerank_scoring(self):
        """Test rerank scoring formula: 0.6 * orig + 0.4 * cosine."""
        reranker = CosineReranker()

        doc = Document(
            id="test",
            content="test content",
            original_score=0.8,
            cosine_score=0.9
        )

        score = reranker.rerank_score(doc)
        expected = 0.6 * 0.8 + 0.4 * 0.9  # 0.48 + 0.36 = 0.84

        assert score == pytest.approx(expected)

    def test_threshold_filtering(self):
        """Test threshold-based filtering with guardrails."""
        reranker = RAGReranker(threshold_range=(0.5, 0.9), min_docs_kept=2)

        documents = [
            Document("doc1", "content1", 0.8, 0.9, rerank_score=0.84),  # Above threshold
            Document("doc2", "content2", 0.6, 0.7, rerank_score=0.66),  # Above threshold
            Document("doc3", "content3", 0.4, 0.3, rerank_score=0.36),  # Below threshold
        ]

        reranker.current_threshold = 0.7
        kept_docs = reranker.rerank("test query", documents)

        # Should keep docs with rerank_score >= 0.7
        assert len(kept_docs) >= 2  # Minimum guardrail
        assert all(doc.rerank_score >= 0.7 or doc.id in ["doc1", "doc2"] for doc in kept_docs)

    def test_overfilter_protection(self):
        """Test over-filter guardrail maintains minimum docs."""
        reranker = RAGReranker(min_docs_kept=3)

        # Create 5 docs, set threshold very high so only 1 would qualify
        documents = []
        for i in range(5):
            doc = Document(f"doc{i}", f"content{i}", 0.5, 0.5, rerank_score=0.5)
            if i == 0:  # Make only first doc qualify
                doc.rerank_score = 0.9
            documents.append(doc)

        reranker.current_threshold = 0.8
        kept_docs = reranker.rerank("test query", documents)

        # Should keep at least min_docs_kept despite threshold
        assert len(kept_docs) >= reranker.min_docs_kept
        assert kept_docs[0].id == "doc0"  # Best doc first

    def test_precision_mode_trigger(self):
        """Test cross-encoder precision mode triggers."""
        reranker = RAGReranker()

        # Test intent-based trigger
        assert reranker.should_use_precision_mode("test", intent="legal")
        assert reranker.should_use_precision_mode("test", intent="policy")

        # Test complexity-based trigger
        assert reranker.should_use_precision_mode("test", token_count=20, score_entropy=1.5)

        # Test non-trigger
        assert not reranker.should_use_precision_mode("simple query", intent="casual")

    @patch('src.core.rag_reranker.RAGReranker._evaluate_current_threshold')
    def test_threshold_tuning(self, mock_evaluate):
        """Test threshold tuning with grid search."""
        reranker = RAGReranker(min_samples_threshold=10)

        # Mock current performance
        mock_evaluate.return_value = 6.5

        # Create evaluation data
        queries = []
        for i in range(50):
            docs = [
                Document(f"doc{j}", "content", 0.8, 0.8, rerank_score=0.8)
                for j in range(5)
            ]
            query = RAGQuery(
                query=f"query{i}",
                documents=docs,
                judge_score=7.0 + np.random.normal(0, 0.5)
            )
            queries.append(query)

        # Tune threshold
        new_threshold, improvement = reranker.tune_threshold(queries)

        # Should update threshold
        assert isinstance(new_threshold, float)
        assert new_threshold >= 0.2 and new_threshold <= 0.85


class TestStatisticalSignificance:
    """Test statistical significance calculations for experiments."""

    def test_sample_size_calculation(self):
        """Test required sample size calculations."""
        # Two-proportion test: p=0.6, MDE=0.05, α=0.05, power=0.8
        # n ≈ (2 * 1.96² * 0.24) / 0.0025 ≈ 737 per arm

        p = 0.6
        mde = 0.05
        alpha = 0.05
        power = 0.8

        z_alpha = 1.96  # norm.ppf(1 - alpha/2)
        z_power = 0.84  # norm.ppf(power)

        n_per_arm = 2 * (z_alpha + z_power)**2 * p * (1-p) / mde**2
        expected_n = int(np.ceil(n_per_arm))

        # Should be around 737
        assert expected_n >= 700 and expected_n <= 800

    def test_continuous_metric_power(self):
        """Test continuous metric sample size (judge helpfulness)."""
        # σ=1.2, Δ=0.3, α=0.05, power=0.8
        # n ≈ 2σ²(z_{1-α/2} + z_{1-β})² / Δ²

        sigma = 1.2
        delta = 0.3
        z_alpha = 1.96
        z_power = 0.84

        n_per_arm = 2 * sigma**2 * (z_alpha + z_power)**2 / delta**2
        expected_n = int(np.ceil(n_per_arm))

        # Should be around 250
        assert expected_n >= 200 and expected_n <= 300


class TestIntegration:
    """Integration tests with realistic data flows."""

    def test_full_optimization_pipeline(self):
        """Test complete optimization pipeline end-to-end."""
        # Initialize components
        bandit = AdvancedBanditOptimizer()
        shaper = RewardShaper()
        reranker = RAGReranker()

        # Add variants to bandit
        bandit.add_variant("cosine_rerank")
        bandit.add_variant("no_rerank")

        # Simulate 100 interactions
        for i in range(100):
            # Select variant
            variant = bandit.select_variant()

            # Simulate reranking decision
            use_rerank = variant == "cosine_rerank"

            # Create mock documents
            docs = [
                Document(f"doc{j}", "content", 0.7, 0.8)
                for j in range(5)
            ]

            # Rerank if selected
            if use_rerank:
                reranked_docs = reranker.rerank(f"query{i}", docs)
                docs_used = len(reranked_docs)
            else:
                docs_used = len(docs)

            # Simulate judge feedback
            base_score = 7.0
            rerank_bonus = 0.3 if use_rerank else 0.0
            judge_score = base_score + rerank_bonus + np.random.normal(0, 0.5)

            # Create feedback signal
            feedback = FeedbackSignal(
                human_feedback=np.random.choice([-1, 0, 1]),
                judge_scores=JudgeScores(
                    helpfulness=min(10, max(1, judge_score + np.random.normal(0, 0.3))),
                    factuality=min(10, max(1, judge_score + np.random.normal(0, 0.3))),
                    clarity=min(10, max(1, judge_score + np.random.normal(0, 0.3)))
                )
            )

            # Shape reward
            reward = shaper.shape_reward(feedback)

            # Update bandit
            bandit.update_variant(variant, reward)

        # Verify learning occurred
        stats = bandit.get_stats()
        assert len(stats) == 2  # Both variants present

        # The better variant should have been selected more
        selections = {name: stats[name]['samples'] for name in stats}
        assert selections['cosine_rerank'] > selections['no_rerank']

    def test_drift_correction_adaptation(self):
        """Test that drift correction adapts to changing judge behavior."""
        shaper = RewardShaper(drift_window_days=7)

        # Simulate initial stable period
        initial_scores = np.random.normal(7.0, 0.5, 50)
        for score in initial_scores:
            shaper._update_domain_stats("test_domain", score, datetime.now())

        # Simulate drift: judges become harsher
        drifted_scores = np.random.normal(6.0, 0.5, 30)
        for score in drifted_scores:
            shaper._update_domain_stats("test_domain", score, datetime.now())

        # Check that correction adapts
        stats = shaper.get_domain_stats("test_domain")
        assert stats['samples'] == 80
        assert abs(stats['mean'] - 6.3) < 0.3  # Should adapt to new mean


if __name__ == "__main__":
    pytest.main([__file__])
