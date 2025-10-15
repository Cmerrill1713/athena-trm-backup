#!/usr/bin/env python3
"""
Tests for RAG Cross-Encoder Precision Mode
"""

import os
import sys
import numpy as np

# Set up test environment
os.environ['RAG_RERANK_ENABLED'] = 'true'
os.environ['RAG_RERANKER_CE_ENABLED'] = 'true'
os.environ['RAG_RERANKER_CE_INTENTS'] = 'policy,incident,legal,diagnosis'
os.environ['RAG_RERANKER_CE_LATENCY_BUDGET_MS'] = '500'

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'AI-Projects', 'universal-ai-tools'))

from rag.rerank import should_use_cross_encoder, rerank, _cross_encoder_similarity

def test_ce_routing():
    """Test cross-encoder routing logic."""
    print("🧪 Testing CE routing logic...")

    # Test intent-based routing
    assert should_use_cross_encoder("What is the policy on this?", intent="policy") == True
    assert should_use_cross_encoder("Legal question here", intent="legal") == True
    assert should_use_cross_encoder("Regular question", intent="general") == False

    # Test query length routing
    long_query = " ".join(["word"] * 20)  # 20 words
    short_query = "short query"

    assert should_use_cross_encoder(long_query) == True
    assert should_use_cross_encoder(short_query) == False

    print("✅ CE routing logic working correctly")

def test_ce_reranking():
    """Test cross-encoder reranking."""
    print("🧪 Testing CE reranking...")

    # Mock candidates
    candidates = [
        {"doc_id": "doc1", "text": "This is about policy and procedures", "orig": 0.8, "emb": np.random.rand(384)},
        {"doc_id": "doc2", "text": "Regular content here", "orig": 0.6, "emb": np.random.rand(384)},
    ]

    query_emb = np.random.rand(384)
    query_text = "What is the company policy on this matter?"

    # Test CE reranking
    results = rerank(query_emb, candidates, query_text=query_text, intent="policy")

    # Should use cross-encoder for policy intent
    assert len(results) > 0
    assert all(r.get("reranker_type") == "crossencoder" for r in results)

    print("✅ CE reranking working correctly")

def test_ce_similarity():
    """Test cross-encoder similarity function."""
    print("🧪 Testing CE similarity...")

    query = "What is the policy?"
    doc = "This document explains the company policy in detail."

    score = _cross_encoder_similarity(query, doc)
    assert 0.0 <= score <= 1.0  # Should be in valid range

    # Test caching - same query should return same score
    score2 = _cross_encoder_similarity(query, doc)
    assert abs(score - score2) < 0.001  # Should be cached

    print("✅ CE similarity function working correctly")

def test_ce_model_health():
    """Test CE model health and fallback."""
    print("🧪 Testing CE model health...")

    from rag.rerank import ce_manager

    health = ce_manager.health_check()
    assert isinstance(health, dict)
    assert "model_loaded" in health
    assert "inference_working" in health

    # Even if model not loaded, fallback should work
    assert health["inference_working"] or health.get("fallback_mode", False)

    print("✅ CE model health check working correctly")

def test_cosine_fallback():
    """Test that cosine reranking still works for non-CE queries."""
    print("🧪 Testing cosine fallback...")

    candidates = [
        {"doc_id": "doc1", "text": "Regular content", "orig": 0.8, "emb": np.random.rand(384)},
        {"doc_id": "doc2", "text": "More regular content", "orig": 0.6, "emb": np.random.rand(384)},
    ]

    query_emb = np.random.rand(384)
    query_text = "Regular short question?"

    results = rerank(query_emb, candidates, query_text=query_text, intent="general")

    # Should use cosine for general queries
    assert len(results) > 0
    assert all(r.get("reranker_type") == "cosine" for r in results)

    print("✅ Cosine fallback working correctly")

def test_ce_disabled():
    """Test behavior when CE is disabled."""
    print("🧪 Testing CE disabled...")

    # Temporarily disable CE
    old_enabled = os.environ.get('RAG_RERANKER_CE_ENABLED')
    os.environ['RAG_RERANKER_CE_ENABLED'] = 'false'

    try:
        # Reload module to pick up new env var
        import importlib
        import rag.rerank
        importlib.reload(rag.rerank)

        assert rag.rerank.should_use_cross_encoder("Policy question", intent="policy") == False
        print("✅ CE disabled behavior working correctly")
    finally:
        # Restore original setting
        if old_enabled:
            os.environ['RAG_RERANKER_CE_ENABLED'] = old_enabled
        else:
            os.environ.pop('RAG_RERANKER_CE_ENABLED', None)

def run_all_tests():
    """Run all CE precision mode tests."""
    print("🚀 Running RAG Cross-Encoder Precision Mode Tests")
    print("=" * 60)

    try:
        test_ce_routing()
        test_ce_reranking()
        test_ce_similarity()
        test_ce_model_health()
        test_cosine_fallback()
        test_ce_disabled()

        print("\n🎉 All CE precision mode tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
