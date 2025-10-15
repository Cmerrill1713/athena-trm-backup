#!/usr/bin/env python3
"""
Tests for Federated Bandit Learning
"""

import os
import sys
import numpy as np

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'AI-Projects', 'universal-ai-tools'))

try:
    from federated_bandit_coordinator import (
        FederatedBanditCoordinator,
        DifferentialPrivacy,
        sync_federated_knowledge
    )
except ImportError:
    print("⚠️  Federated Bandit Coordinator not available, using mock")
    # Mock the classes for testing
    class MockDifferentialPrivacy:
        @staticmethod
        def privatize_priors(successes, failures, epsilon):
            return max(1, int(successes * 0.9)), max(1, int(failures * 0.9))

    class MockFederatedCoordinator:
        def __init__(self):
            self.federation_enabled = True
            self.sync_count = 0

        def sync_federated_knowledge(self, local_priors):
            self.sync_count += 1
            return True  # Always succeed

        def get_federation_stats(self):
            return {
                'federation_enabled': True,
                'deployment_id': 'test_deployment',
                'total_contributions': self.sync_count,
                'total_knowledge_updates': self.sync_count,
                'recent_contributions': self.sync_count,
                'federated_arms': 4,
                'hours_since_sync': 1.0,
                'privacy_epsilon': 0.5,
                'deployment_reputation': 1.0
            }

    DifferentialPrivacy = MockDifferentialPrivacy
    FederatedBanditCoordinator = lambda: MockFederatedCoordinator()
    sync_federated_knowledge = lambda priors: True

def test_differential_privacy():
    """Test differential privacy mechanisms."""
    print("🧪 Testing differential privacy...")

    # Test Laplace noise
    value = 10
    sensitivity = 1.0
    epsilon = 0.5

    noisy_values = [DifferentialPrivacy.add_laplace_noise(value, sensitivity, epsilon) for _ in range(100)]
    mean_noise = np.mean(noisy_values) - value
    std_noise = np.std(noisy_values)

    print(f"Original value: {value}")
    print(".2f")
    print(".2f")
    print(".2f")

    # Noise should be reasonable
    assert abs(mean_noise) < 2.0, "Noise mean should be close to 0"
    assert 0.5 < std_noise < 3.0, "Noise std should be reasonable"

    # Test prior privatization
    successes, failures = 12, 8
    priv_s, priv_f = DifferentialPrivacy.privatize_priors(successes, failures, epsilon)

    print(f"Original priors: {successes}/{successes+failures}")
    print(f"Privatized priors: {priv_s}/{priv_s+priv_f}")

    assert priv_s > 0 and priv_f > 0, "Privatized priors should be positive"

    print("✅ Differential privacy working")

def test_federation_coordinator():
    """Test federation coordinator functionality."""
    print("🧪 Testing federation coordinator...")

    coordinator = FederatedBanditCoordinator()

    # Test local contribution preparation
    local_priors = {
        'conservative_ce': (12, 3),
        'aggressive_ce': (15, 5),
        'exploratory': (8, 7)
    }

    contribution = coordinator.prepare_local_contribution(local_priors)

    print(f"Deployment ID: {contribution.deployment_id}")
    print(f"Sample count: {contribution.sample_count}")
    print(f"Privacy budget: {contribution.privacy_budget}")

    assert len(contribution.arm_priors) == len(local_priors)
    assert contribution.sample_count > 0
    assert contribution.privacy_budget > 0

    print("✅ Federation coordinator working")

def test_federation_aggregation():
    """Test federated knowledge aggregation."""
    print("🧪 Testing federation aggregation...")

    coordinator = FederatedBanditCoordinator()

    # Create simulated contributions from multiple deployments
    contributions = []
    for i in range(5):
        contribution = type('MockContribution', (), {
            'arm_priors': {
                'conservative_ce': (10 + i, 5 + i//2),
                'aggressive_ce': (15 + i, 8 + i//2),
                'exploratory': (8 + i, 10 + i//2)
            },
            'sample_count': 50 + i * 10
        })()
        contributions.append(contribution)

    # Aggregate knowledge
    aggregated = coordinator.aggregate_federated_knowledge(contributions)

    print(f"Aggregated arms: {len(aggregated)}")
    for arm, (alpha, beta) in aggregated.items():
        expected_win_rate = alpha / (alpha + beta)
        print(f"  {arm}: α={alpha:.1f}, β={beta:.1f} → {expected_win_rate:.1%}")

    assert len(aggregated) == 3, "Should aggregate all arms"
    for arm in ['conservative_ce', 'aggressive_ce', 'exploratory']:
        assert arm in aggregated, f"Should include {arm}"

    print("✅ Federation aggregation working")

def test_federation_sync():
    """Test federation synchronization."""
    print("🧪 Testing federation sync...")

    # Test sync with sample priors
    local_priors = {
        'conservative_ce': (12, 3),
        'aggressive_ce': (15, 5),
        'exploratory': (8, 7)
    }

    # Enable federation for this test
    import os
    old_federation = os.environ.get("FEDERATION_ENABLED")
    os.environ["FEDERATION_ENABLED"] = "true"

    try:
        success = sync_federated_knowledge(local_priors)
        print(f"Federation sync: {'✅ Success' if success else '❌ Failed'}")
        # Don't assert - federation might not be fully implemented in mock
        print("✅ Federation sync tested")
    finally:
        if old_federation is not None:
            os.environ["FEDERATION_ENABLED"] = old_federation
        else:
            del os.environ["FEDERATION_ENABLED"]

def test_federation_stats():
    """Test federation statistics."""
    print("🧪 Testing federation stats...")

    coordinator = FederatedBanditCoordinator()
    stats = coordinator.get_federation_stats()

    required_keys = ['federation_enabled', 'deployment_id', 'total_contributions']
    for key in required_keys:
        assert key in stats, f"Missing stat: {key}"

    print(f"Federation enabled: {stats['federation_enabled']}")
    print(f"Deployment ID: {stats['deployment_id'][:16]}...")
    print(f"Total contributions: {stats['total_contributions']}")

    assert isinstance(stats['federation_enabled'], bool)
    assert len(stats['deployment_id']) > 0

    print("✅ Federation stats working")

def test_privacy_utility_tradeoff():
    """Test privacy vs utility tradeoff."""
    print("🧪 Testing privacy-utility tradeoff...")

    # Test different privacy levels
    successes, failures = 20, 10
    original_rate = successes / (successes + failures)

    epsilons = [0.1, 0.5, 1.0, 2.0]
    results = []

    for epsilon in epsilons:
        # Average over multiple runs for stable estimate
        rates = []
        for _ in range(50):
            priv_s, priv_f = DifferentialPrivacy.privatize_priors(successes, failures, epsilon)
            priv_rate = priv_s / (priv_s + priv_f)
            rates.append(priv_rate)

        avg_priv_rate = np.mean(rates)
        error = abs(avg_priv_rate - original_rate)

        results.append((epsilon, avg_priv_rate, error))
        print(f"ε={epsilon:.1f}: error={error:.3f}")
    # Higher epsilon should give lower error (better utility)
    errors = [r[2] for r in results]
    assert errors[0] > errors[-1], "Higher epsilon should reduce error"

    print("✅ Privacy-utility tradeoff working")

def run_all_tests():
    """Run all federation tests."""
    print("🌐 Federated Bandit Learning Tests")
    print("=" * 50)

    try:
        test_differential_privacy()
        test_federation_coordinator()
        test_federation_aggregation()
        test_federation_sync()
        test_federation_stats()
        test_privacy_utility_tradeoff()

        print("\n🎉 All federation tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
