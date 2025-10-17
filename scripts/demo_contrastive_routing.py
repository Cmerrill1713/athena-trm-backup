#!/usr/bin/env python3
"""
Demo: Contrastive Routing vs Basic Routing

Compares routing decisions between BasicRouter and ContrastiveRouter
using shadow mode to validate the new routing strategy.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.routing.basic_router import BasicRouter, RoutingRequest
from governance.routing.contrastive_router import ContrastiveRouter
from governance.routing.shadow_mode import ShadowModeRouter


def main():
    """Run contrastive routing demo."""
    print("\n" + "="*70)
    print("ATHENA CONTRASTIVE ROUTING DEMO")
    print("="*70 + "\n")
    
    # Load routers
    profiles_path = Path("governance/routing/model_profiles.json")
    
    print(f"Loading model profiles from {profiles_path}...")
    
    basic_router = BasicRouter(profiles_path)
    contrastive_router = ContrastiveRouter(
        profiles_path,
        fallback_threshold=0.7,
        fallback_margin=0.1
    )
    
    print(f"✅ Loaded {len(basic_router.models)} models\n")
    
    # Create shadow mode router
    shadow_router = ShadowModeRouter(
        primary_router=basic_router,
        shadow_router=contrastive_router,
        sample_rate=1.0  # Shadow all requests
    )
    
    # Test queries
    test_queries = [
        ("Write a Python function to sort a list", "code"),
        ("Explain quantum computing", "general"),
        ("Debug this error message", "code"),
        ("What is the capital of France?", "general"),
        ("Implement a binary search algorithm", "code"),
        ("Tell me a story", "general"),
        ("Solve x^2 + 5x + 6 = 0", "math"),  # Unknown domain test
        ("Optimize SQL query", "code"),
        ("Recommend a book", "general"),
        ("Create REST API endpoint", "code"),
    ]
    
    print("Running test queries...\n")
    print("-" * 70)
    
    for i, (query, domain) in enumerate(test_queries, 1):
        request = RoutingRequest(query=query, domain=domain)
        
        # Route with shadow mode (primary = basic, shadow = contrastive)
        choice = shadow_router.route(request)
        
        print(f"\n{i}. Query: {query[:50]}...")
        print(f"   Domain: {domain}")
        print(f"   Primary Router → {choice.model} (confidence: {choice.confidence:.3f})")
        print(f"   Strategy: {choice.metadata.get('strategy', 'N/A')}")
    
    print("\n" + "-" * 70)
    
    # Print shadow mode report
    shadow_router.print_report()
    
    # Compare direct routing
    print("\n" + "="*70)
    print("DIRECT COMPARISON: Basic vs Contrastive")
    print("="*70 + "\n")
    
    sample_request = RoutingRequest(
        query="Implement a web scraper",
        domain="code"
    )
    
    basic_choice = basic_router.route(sample_request)
    contrastive_choice = contrastive_router.route(sample_request)
    
    print("Query: 'Implement a web scraper' (domain: code)\n")
    
    print(f"BasicRouter:")
    print(f"  Model: {basic_choice.model}")
    print(f"  Confidence: {basic_choice.confidence:.3f}")
    print(f"  Strategy: {basic_choice.metadata.get('strategy', 'N/A')}")
    print(f"  Latency: {basic_choice.latency_ms:.2f}ms\n")
    
    print(f"ContrastiveRouter:")
    print(f"  Model: {contrastive_choice.model}")
    print(f"  Confidence: {contrastive_choice.confidence:.3f}")
    print(f"  Strategy: {contrastive_choice.metadata.get('strategy', 'N/A')}")
    if 'similarity' in contrastive_choice.metadata:
        print(f"  Similarity: {contrastive_choice.metadata['similarity']:.3f}")
    if 'margin' in contrastive_choice.metadata:
        print(f"  Margin: {contrastive_choice.metadata['margin']:.3f}")
    print(f"  Latency: {contrastive_choice.latency_ms:.2f}ms")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70 + "\n")
    
    # Check shadow mode log
    log_path = Path("state/shadow_mode_comparisons.jsonl")
    if log_path.exists():
        import json
        comparisons = []
        with open(log_path) as f:
            for line in f:
                comparisons.append(json.loads(line))
        
        print(f"📄 Shadow mode log: {log_path}")
        print(f"   {len(comparisons)} comparisons logged")
        print(f"   View with: cat {log_path} | jq .\n")


if __name__ == '__main__':
    main()

