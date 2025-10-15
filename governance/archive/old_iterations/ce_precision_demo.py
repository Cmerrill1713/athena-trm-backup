#!/usr/bin/env python3
"""
Cross-Encoder Precision Mode Demo
Shows how CE reranking works for high-value queries
"""

import os
import sys
import numpy as np

# Set up demo environment
os.environ['RAG_RERANK_ENABLED'] = 'true'
os.environ['RAG_RERANKER_CE_ENABLED'] = 'true'
os.environ['RAG_RERANKER_CE_INTENTS'] = 'policy,incident,legal,diagnosis'
os.environ['RAG_RERANKER_CE_LATENCY_BUDGET_MS'] = '500'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AI-Projects', 'universal-ai-tools'))

from rag.rerank import rerank, should_use_cross_encoder

def demo_ce_routing():
    """Demonstrate CE routing decisions."""
    print("🎯 Cross-Encoder Precision Mode Demo")
    print("=" * 50)

    test_cases = [
        ("What is the company policy on remote work?", "policy", "Policy intent → CE"),
        ("How do I handle a security incident?", "incident", "Incident intent → CE"),
        ("What are the legal requirements for this?", "legal", "Legal intent → CE"),
        ("Regular question about documentation", "general", "General intent → Cosine"),
        ("This is a very long question with many words that exceeds the sixteen word threshold for cross encoder reranking in our precision mode system", None, "Long query (>16 words) → CE"),
        ("Short query here", None, "Short query → Cosine"),
    ]

    print("\n📋 Routing Decisions:")
    for query, intent, explanation in test_cases:
        use_ce = should_use_cross_encoder(query, intent)
        reranker = "Cross-Encoder" if use_ce else "Cosine"
        print(f"  {reranker}: {query[:50]}... ({explanation})")

def demo_ce_reranking():
    """Demonstrate actual reranking with CE."""
    print("\n🔄 Reranking Demo:")

    # Mock candidates with different relevance levels
    candidates = [
        {
            "doc_id": "policy_doc",
            "text": "Company policy on data security and incident response procedures",
            "orig": 0.7,
            "emb": np.random.rand(384)
        },
        {
            "doc_id": "general_doc",
            "text": "General information about company operations",
            "orig": 0.8,
            "emb": np.random.rand(384)
        },
        {
            "doc_id": "irrelevant_doc",
            "text": "Unrelated content about vacation policies",
            "orig": 0.5,
            "emb": np.random.rand(384)
        }
    ]

    # Test queries
    test_queries = [
        ("What is the security incident response policy?", "policy", "Policy query"),
        ("How does the company handle general operations?", "general", "General query"),
    ]

    for query_text, intent, desc in test_queries:
        print(f"\n  {desc}: '{query_text}'")
        query_emb = np.random.rand(384)

        results = rerank(query_emb, candidates, query_text=query_text, intent=intent)

        for i, result in enumerate(results[:2]):  # Show top 2
            reranker_type = result.get("reranker_type", "unknown")
            score = result.get("rerank", 0)
            print(f"    {i+1}. {result['doc_id']} (reranker: {reranker_type}, score: {score:.3f})")

def demo_metrics():
    """Show what metrics are collected."""
    print("\n📊 Metrics Collected:")
    print("  ✅ rag_ce_requests_total{intent='...'} - CE usage counter")
    print("  ✅ rag_ce_request_duration_seconds - CE latency histogram")
    print("  ✅ rag_ce_enabled - CE enabled status gauge")
    print("  ✅ Existing reranker metrics (threshold, docs_used, etc.)")

if __name__ == "__main__":
    demo_ce_routing()
    demo_ce_reranking()
    demo_metrics()

    print("\n🎉 CE Precision Mode Ready!")
    print("\nNext steps:")
    print("  1. Deploy with RAG_RERANKER_CE_ENABLED=true")
    print("  2. Monitor CE latency vs. precision improvement")
    print("  3. Replace placeholder CE with real model (MS MARCO CrossEncoder)")
    print("  4. Tune latency budget based on production performance")
