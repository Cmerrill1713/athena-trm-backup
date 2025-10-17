"""
Tests for contrastive routing with domain embeddings.
"""

import json
import pytest
import numpy as np
from pathlib import Path
import tempfile

from governance.routing.contrastive_router import (
    ContrastiveRouter,
    EmbeddingCache
)
from governance.routing.basic_router import RoutingRequest
from governance.routing.shadow_mode import ShadowModeRouter


@pytest.fixture
def sample_profiles_with_embeddings():
    """Sample profiles with real embeddings."""
    return {
        "version": "1.0.0",
        "models": [
            {
                "model_id": "test-general",
                "domain": "general",
                "domain_embedding": (np.random.rand(384) * 0.5 + 0.5).tolist(),  # Positive values
                "quality_score": 0.8,
                "cost": 0.001,
                "latency_p50_ms": 1000,
                "latency_p95_ms": 2000,
                "is_approximate": False,
                "confidence": 1.0,
                "metadata": {"description": "General model"}
            },
            {
                "model_id": "test-code",
                "domain": "code",
                "domain_embedding": (np.random.rand(384) * 0.5 + 0.5).tolist(),
                "quality_score": 0.9,
                "cost": 0.002,
                "latency_p50_ms": 1200,
                "latency_p95_ms": 2500,
                "is_approximate": False,
                "confidence": 1.0,
                "metadata": {"description": "Code model"}
            },
            {
                "model_id": "test-fast",
                "domain": "general",
                "domain_embedding": (np.random.rand(384) * 0.5 + 0.5).tolist(),
                "quality_score": 0.6,
                "cost": 0.0005,
                "latency_p50_ms": 500,
                "latency_p95_ms": 1000,
                "is_approximate": False,
                "confidence": 1.0,
                "metadata": {"description": "Fast model"}
            }
        ]
    }


@pytest.fixture
def contrastive_router(sample_profiles_with_embeddings):
    """Create contrastive router with sample profiles."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_profiles_with_embeddings, f)
        profile_path = Path(f.name)
    
    router = ContrastiveRouter(
        profiles_path=profile_path,
        fallback_threshold=0.7,
        fallback_margin=0.1
    )
    
    yield router
    
    # Cleanup
    profile_path.unlink()


def test_embedding_cache():
    """Test embedding cache functionality."""
    cache = EmbeddingCache(maxsize=3)
    
    # Add embeddings
    emb1 = np.array([0.1, 0.2, 0.3])
    emb2 = np.array([0.4, 0.5, 0.6])
    emb3 = np.array([0.7, 0.8, 0.9])
    emb4 = np.array([1.0, 1.1, 1.2])
    
    cache.put("domain1", emb1)
    cache.put("domain2", emb2)
    cache.put("domain3", emb3)
    
    # Test retrieval
    assert np.array_equal(cache.get("domain1"), emb1)
    assert np.array_equal(cache.get("domain2"), emb2)
    
    # Test LRU eviction
    cache.put("domain4", emb4)
    
    # domain3 should be evicted (least recently used)
    assert cache.get("domain3") is None
    assert cache.get("domain4") is not None


def test_contrastive_router_initialization(contrastive_router):
    """Test contrastive router initialization."""
    assert len(contrastive_router.models) == 3
    assert contrastive_router.fallback_threshold == 0.7
    assert contrastive_router.fallback_margin == 0.1
    
    # Check embeddings are normalized
    for model in contrastive_router.models:
        if model.domain_embedding_np is not None:
            norm = np.linalg.norm(model.domain_embedding_np)
            assert abs(norm - 1.0) < 1e-6  # Should be normalized


def test_contrastive_routing_code_domain(contrastive_router):
    """Test contrastive routing for code domain."""
    request = RoutingRequest(
        query="Write a Python function",
        domain="code"
    )
    
    choice = contrastive_router.route(request)
    
    # Should route successfully (exact model depends on random embeddings)
    assert choice.model in ["test-code", "test-general", "test-fast"]
    assert choice.confidence > 0
    assert 'strategy' in choice.metadata
    
    # If using contrastive strategy, should have similarity score
    if choice.metadata['strategy'] == 'contrastive':
        assert 'similarity' in choice.metadata
        assert choice.metadata['similarity'] >= 0


def test_contrastive_routing_general_domain(contrastive_router):
    """Test contrastive routing for general domain."""
    request = RoutingRequest(
        query="What is the meaning of life?",
        domain="general"
    )
    
    choice = contrastive_router.route(request)
    
    # Should pick a general model
    assert choice.model in ["test-general", "test-fast"]
    assert choice.domain == "general"


def test_margin_based_fallback(contrastive_router):
    """Test margin-based fallback when scores are close."""
    # Set very high margin threshold to force fallback
    contrastive_router.fallback_margin = 10.0
    
    request = RoutingRequest(
        query="Test query",
        domain="general"
    )
    
    choice = contrastive_router.route(request)
    
    # Should use kNN fallback due to high margin requirement
    # (or weighted fallback if kNN not triggered)
    assert 'strategy' in choice.metadata
    # Confidence should be moderate (not high)
    assert choice.confidence < 0.9


def test_cosine_similarity(contrastive_router):
    """Test cosine similarity computation."""
    # Identical vectors
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([1.0, 0.0, 0.0])
    sim = contrastive_router._cosine_similarity(a, b)
    assert abs(sim - 1.0) < 1e-6
    
    # Orthogonal vectors
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    sim = contrastive_router._cosine_similarity(a, b)
    assert abs(sim) < 1e-6


def test_knn_fallback(contrastive_router):
    """Test kNN fallback router."""
    request = RoutingRequest(
        query="Test query",
        domain="general"
    )
    
    # Get scores
    query_emb = contrastive_router._get_query_embedding("general")
    assert query_emb is not None
    
    scores = contrastive_router._compute_scores(query_emb, request)
    assert len(scores) > 0
    
    # Test kNN fallback
    choice = contrastive_router._knn_fallback(scores, request, k=2)
    
    assert choice.model in [m.model_id for m in contrastive_router.models]
    assert choice.confidence == 0.6  # kNN fallback confidence
    assert 'strategy' in choice.metadata
    assert choice.metadata['strategy'] == 'knn_fallback'


def test_shadow_mode_router(sample_profiles_with_embeddings):
    """Test shadow mode router."""
    # Create two routers
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_profiles_with_embeddings, f)
        profile_path = Path(f.name)
    
    from governance.routing.basic_router import BasicRouter
    
    primary = BasicRouter(profile_path)
    shadow = ContrastiveRouter(profile_path)
    
    # Create shadow mode router
    shadow_router = ShadowModeRouter(
        primary_router=primary,
        shadow_router=shadow,
        sample_rate=1.0  # Shadow all requests for testing
    )
    
    # Route some requests
    requests = [
        RoutingRequest("Write Python", "code"),
        RoutingRequest("Explain AI", "general"),
        RoutingRequest("Debug error", "code")
    ]
    
    for req in requests:
        choice = shadow_router.route(req)
        assert choice is not None
    
    # Check statistics
    stats = shadow_router.get_statistics()
    
    assert stats['total_requests'] == 3
    assert stats['shadow_requests'] == 3  # sample_rate = 1.0
    assert 0 <= stats['agreement_rate'] <= 1.0
    
    # Cleanup
    profile_path.unlink()


def test_shadow_mode_report(sample_profiles_with_embeddings, capsys):
    """Test shadow mode report generation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_profiles_with_embeddings, f)
        profile_path = Path(f.name)
    
    from governance.routing.basic_router import BasicRouter
    
    primary = BasicRouter(profile_path)
    shadow = ContrastiveRouter(profile_path)
    
    shadow_router = ShadowModeRouter(
        primary_router=primary,
        shadow_router=shadow,
        sample_rate=1.0
    )
    
    # Route requests
    for _ in range(5):
        req = RoutingRequest("Test", "general")
        shadow_router.route(req)
    
    # Print report
    shadow_router.print_report()
    
    captured = capsys.readouterr()
    
    assert "SHADOW MODE ROUTING REPORT" in captured.out
    assert "Agreement Rate" in captured.out
    assert "Confidence Delta" in captured.out
    
    # Cleanup
    profile_path.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

