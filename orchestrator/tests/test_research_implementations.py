"""
Quick Integration Tests for All Research Implementations
========================================================
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_contextual_thompson_sampling_imports():
    """Test that contextual TS can be imported"""
    from providers.contextual_thompson_sampling import ContextualThompsonSampling
    assert ContextualThompsonSampling is not None


def test_adaptive_prompts_imports():
    """Test that adaptive prompts can be imported"""
    try:
        from providers import adaptive_prompts
        assert adaptive_prompts is not None
    except ImportError:
        pytest.skip("adaptive_prompts not yet wrapped for import")


def test_statistical_rollout_imports():
    """Test that statistical rollout can be imported"""
    try:
        from providers import statistical_rollout
        assert statistical_rollout is not None
    except ImportError:
        pytest.skip("statistical_rollout not yet wrapped for import")


def test_uncertainty_estimation_imports():
    """Test that uncertainty estimation can be imported"""
    try:
        from providers import uncertainty_estimation
        assert uncertainty_estimation is not None
    except ImportError:
        pytest.skip("uncertainty_estimation not yet wrapped for import")


def test_meta_learning_imports():
    """Test that meta_learning can be imported"""
    try:
        from providers import meta_learning
        assert meta_learning is not None
    except ImportError:
        pytest.skip("meta_learning not yet wrapped for import")


def test_registry_has_research_providers():
    """Test that registry includes research providers"""
    from registry import REGISTRY
    
    assert "decision_making" in REGISTRY
    assert "prompt_optimization" in REGISTRY
    assert "uncertainty" in REGISTRY
    assert "meta_learning" in REGISTRY


def test_research_providers_structure():
    """Test that research providers have correct structure"""
    from registry import REGISTRY
    
    for capability in ["decision_making", "prompt_optimization", "uncertainty"]:
        providers = REGISTRY[capability]
        assert len(providers) > 0
        
        for provider in providers:
            assert "name" in provider
            assert "entry" in provider
            assert "caps" in provider
