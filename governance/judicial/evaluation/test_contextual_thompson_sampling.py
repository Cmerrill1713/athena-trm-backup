"""
Tests for Contextual Thompson Sampling Implementation
====================================================
"""

import pytest
import numpy as np


# Import with path handling
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from providers.contextual_thompson_sampling import ContextualThompsonSampling


@pytest.fixture
def cts_instance():
    """Create a CTS instance for testing"""
    return ContextualThompsonSampling(
        num_arms=3,
        context_dim=5,
        hidden_dim=16,
        learning_rate=0.01
    )


def test_initialization(cts_instance):
    """Test proper initialization"""
    assert cts_instance.num_arms == 3
    assert cts_instance.context_dim == 5
    assert len(cts_instance.alphas) == 3
    assert len(cts_instance.betas) == 3
    assert all(cts_instance.alphas == 1.0)
    assert all(cts_instance.betas == 1.0)


def test_select_arm(cts_instance):
    """Test arm selection"""
    context = np.random.rand(5)
    arm = cts_instance.select_arm(context)
    assert 0 <= arm < 3
    assert isinstance(arm, int)


def test_update_increases_counts(cts_instance):
    """Test that update modifies Beta parameters"""
    initial_alpha = cts_instance.alphas[0].copy()
    initial_beta = cts_instance.betas[0].copy()

    context = np.random.rand(5)
    cts_instance.update(context, arm=0, reward=1.0)

    assert cts_instance.alphas[0] > initial_alpha
    assert cts_instance.betas[0] > initial_beta


def test_history_storage(cts_instance):
    """Test that experiences are stored"""
    context = np.random.rand(5)
    cts_instance.update(context, arm=1, reward=0.5)

    assert len(cts_instance.context_history) == 1
    assert len(cts_instance.arm_history) == 1
    assert len(cts_instance.reward_history) == 1


def test_neural_network_training_trigger(cts_instance):
    """Test that NN training is triggered after 10 samples"""
    context = np.random.rand(5)

    for i in range(11):
        cts_instance.update(context, arm=i % 3, reward=float(i % 2))

    # History should be cleared after training
    assert len(cts_instance.context_history) == 1


def test_multiple_arm_selection(cts_instance):
    """Test selecting arms multiple times"""
    context = np.random.rand(5)
    arms = [cts_instance.select_arm(context) for _ in range(100)]

    # Should explore all arms eventually
    unique_arms = set(arms)
    assert len(unique_arms) >= 2  # At least 2 different arms selected


@pytest.mark.parametrize("reward", [0.0, 0.5, 1.0])
def test_different_rewards(cts_instance, reward):
    """Test with different reward values"""
    context = np.random.rand(5)
    arm = cts_instance.select_arm(context)
    cts_instance.update(context, arm, reward)

    # Should not crash
    assert True


def test_context_dimension_enforcement():
    """Test that wrong context dimension fails gracefully"""
    cts = ContextualThompsonSampling(num_arms=3, context_dim=5)
    context = np.random.rand(10)  # Wrong dimension

    # Should raise error or handle gracefully
    with pytest.raises((RuntimeError, ValueError)):
        cts.select_arm(context)
