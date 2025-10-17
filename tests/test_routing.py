"""
Tests for Athena routing module.
"""

import json
import pytest
from pathlib import Path
import tempfile

from governance.routing.basic_router import (
    BasicRouter,
    RoutingRequest,
    RoutingChoice,
    ModelProfile
)


@pytest.fixture
def sample_profiles():
    """Sample model profiles for testing."""
    return {
        "version": "1.0.0",
        "models": [
            {
                "model_id": "test-general",
                "domain": "general",
                "domain_embedding": [0.1] * 384,
                "quality_score": 0.8,
                "cost": 0.001,
                "latency_p50_ms": 1000,
                "latency_p95_ms": 2000,
                "is_approximate": False,
                "confidence": 1.0,
                "metadata": {"description": "Test general model"}
            },
            {
                "model_id": "test-code",
                "domain": "code",
                "domain_embedding": [0.2] * 384,
                "quality_score": 0.9,
                "cost": 0.002,
                "latency_p50_ms": 1200,
                "latency_p95_ms": 2500,
                "is_approximate": False,
                "confidence": 1.0,
                "metadata": {"description": "Test code model"}
            },
            {
                "model_id": "test-fast",
                "domain": "general",
                "domain_embedding": [0.3] * 384,
                "quality_score": 0.6,
                "cost": 0.0005,
                "latency_p50_ms": 500,
                "latency_p95_ms": 1000,
                "is_approximate": False,
                "confidence": 1.0,
                "metadata": {"description": "Test fast model"}
            }
        ]
    }


@pytest.fixture
def router(sample_profiles):
    """Create router with sample profiles."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_profiles, f)
        profile_path = Path(f.name)
    
    router = BasicRouter(profiles_path=profile_path, fallback_threshold=0.7)
    
    yield router
    
    # Cleanup
    profile_path.unlink()


def test_router_loads_profiles(router):
    """Test that router loads profiles correctly."""
    assert len(router.models) == 3
    assert router.models[0].model_id == "test-general"
    assert router.models[1].model_id == "test-code"
    assert router.models[2].model_id == "test-fast"


def test_router_domain_match(router):
    """Test domain-based routing."""
    request = RoutingRequest(
        query="Write a Python function",
        domain="code"
    )
    
    choice = router.route(request)
    
    assert choice.model == "test-code"
    assert choice.domain == "code"
    assert choice.confidence > 0.7  # Should meet threshold


def test_router_general_domain(router):
    """Test general domain routing."""
    request = RoutingRequest(
        query="What is the meaning of life?",
        domain="general"
    )
    
    choice = router.route(request)
    
    # Should pick higher quality general model
    assert choice.model in ["test-general", "test-fast"]
    assert choice.domain == "general"


def test_router_fallback_unknown_domain(router):
    """Test fallback for unknown domain."""
    request = RoutingRequest(
        query="Solve this math problem",
        domain="math"  # No math model in profiles
    )
    
    choice = router.route(request)
    
    # Should fall back to best quality/cost ratio
    assert choice.model in ["test-general", "test-code", "test-fast"]
    assert choice.confidence <= 0.7  # Fallback has lower confidence


def test_router_records_latency(router):
    """Test that router records latency."""
    request = RoutingRequest(
        query="Test query",
        domain="general"
    )
    
    choice = router.route(request)
    
    assert choice.latency_ms >= 0


def test_router_metadata(router):
    """Test that router includes metadata in choice."""
    request = RoutingRequest(
        query="Test query",
        domain="code",
        metadata={"user_id": "test-123"}
    )
    
    choice = router.route(request)
    
    assert 'strategy' in choice.metadata
    assert 'quality_score' in choice.metadata
    assert 'cost' in choice.metadata


def test_model_profile_from_dict():
    """Test ModelProfile.from_dict."""
    data = {
        "model_id": "test-model",
        "domain": "general",
        "domain_embedding": [0.1] * 384,
        "quality_score": 0.85,
        "cost": 0.001,
        "is_approximate": False,
        "confidence": 1.0,
        "metadata": {"description": "Test"}
    }
    
    profile = ModelProfile.from_dict(data)
    
    assert profile.model_id == "test-model"
    assert profile.domain == "general"
    assert profile.quality_score == 0.85


def test_router_weighted_fallback(router):
    """Test weighted fallback selection."""
    # Set very high threshold to force fallback
    router.fallback_threshold = 0.99
    
    request = RoutingRequest(
        query="Test query",
        domain="general"
    )
    
    choice = router.route(request)
    
    # Should use fallback strategy
    assert 'fallback' in choice.metadata['strategy']


def test_router_round_robin_emergency(router):
    """Test emergency round-robin fallback."""
    # Empty models to force emergency fallback
    original_models = router.models
    router.models = []
    
    request = RoutingRequest(
        query="Test query",
        domain="general"
    )
    
    with pytest.raises(RuntimeError, match="No models available"):
        router.route(request)
    
    # Restore
    router.models = original_models


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

