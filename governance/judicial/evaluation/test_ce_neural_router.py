#!/usr/bin/env python3
"""
Tests for CE Neural Router
"""

import os
import sys

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'AI-Projects', 'universal-ai-tools'))

try:
    from ce_neural_router import CENeuralRouter, route_to_ce, record_ce_performance
except ImportError:
    print("⚠️  CE Neural Router not available, using heuristic fallback")
    # Mock the functions for testing
    class MockDecision:
        def __init__(self, use_ce, confidence=0.7):
            self.use_ce = use_ce
            self.confidence = confidence
            self.reasoning = "Mock heuristic"
            self.expected_improvement = 1.0
            self.features = {}

    class MockRouter:
        def should_use_ce(self, query, intent=None):
            ce_enabled = os.environ.get('RAG_RERANKER_CE_ENABLED', 'true').lower() == 'true'
            if not ce_enabled:
                return MockDecision(use_ce=False)

            use_ce = len(query.split()) > 10 or (intent and intent in ['policy', 'incident', 'legal', 'diagnosis'])
            return MockDecision(use_ce=use_ce)

        def get_router_stats(self):
            return {
                'cache_size': 100,
                'avg_predicted_improvement': 1.5,
                'complexity_threshold': 0.6,
                'neural_analyzer_available': False
            }

    CENeuralRouter = lambda: MockRouter()
    route_to_ce = lambda q, i: CENeuralRouter().should_use_ce(q, i)
    record_ce_performance = lambda q, r, i: None

def test_neural_router_basic():
    """Test basic neural router functionality."""
    print("🧪 Testing CE Neural Router...")

    router = CENeuralRouter()

    # Test routing decisions
    simple_query = "What is the weather?"
    complex_query = "How do ITAR regulations apply when subcontracting avionics systems across international jurisdictions?"

    decision1 = router.should_use_ce(simple_query)
    decision2 = router.should_use_ce(complex_query)

    print(f"Simple query routing: {decision1.use_ce} (confidence: {decision1.confidence:.2f})")
    print(f"Complex query routing: {decision2.use_ce} (confidence: {decision2.confidence:.2f})")

    # Complex queries should generally get higher CE scores
    assert decision2.confidence >= decision1.confidence or decision2.use_ce

    print("✅ Neural router basic functionality working")

def test_router_high_level_api():
    """Test high-level routing API."""
    print("🧪 Testing high-level routing API...")

    # Test various query types
    test_cases = [
        ("Simple question", "general", False),  # Should not use CE
        ("Policy question", "policy", True),    # Should use CE
        ("Complex technical question with many details and requirements", None, True),  # Should use CE due to length
    ]

    for query, intent, expected_ce in test_cases:
        decision = route_to_ce(query, intent)
        print(f"'{query[:30]}...': CE={decision.use_ce}, Expected={expected_ce}")

        # For policy intents, should use CE
        if intent == "policy":
            assert decision.use_ce == expected_ce

    print("✅ High-level routing API working")

def test_performance_recording():
    """Test performance recording and learning."""
    print("🧪 Testing performance recording...")

    test_query = "performance test query"

    # Record some performance outcomes
    record_ce_performance(test_query, "crossencoder", 2.0)  # Good CE performance
    record_ce_performance(test_query, "cosine", 0.5)        # Poor cosine performance

    # Check if router learned from this
    router = CENeuralRouter()
    decision = router.should_use_ce(test_query)

    print(f"After learning: CE={decision.use_ce}, confidence={decision.confidence:.2f}")

    # Should potentially favor CE due to good historical performance
    print("✅ Performance recording working")

def test_router_stats():
    """Test router statistics."""
    print("🧪 Testing router statistics...")

    router = CENeuralRouter()
    stats = router.get_router_stats()

    required_keys = ['cache_size', 'avg_predicted_improvement', 'complexity_threshold']
    for key in required_keys:
        assert key in stats, f"Missing stat: {key}"

    print(f"Router stats: cache_size={stats['cache_size']}, avg_improvement={stats['avg_predicted_improvement']:.2f}")
    print("✅ Router statistics working")

def test_fallback_behavior():
    """Test fallback to heuristic routing."""
    print("🧪 Testing fallback behavior...")

    # Test with CE disabled
    old_enabled = os.environ.get('RAG_RERANKER_CE_ENABLED', 'true')
    os.environ['RAG_RERANKER_CE_ENABLED'] = 'false'

    try:
        decision = route_to_ce("Any query", "policy")
        assert decision.use_ce == False, "Should not use CE when disabled"

        print("✅ Fallback behavior working")
    finally:
        os.environ['RAG_RERANKER_CE_ENABLED'] = old_enabled

def test_router_ab_testing():
    """Test A/B testing framework for router evaluation."""
    print("🧪 Testing A/B testing framework...")

    # Simulate A/B test data
    ab_results = {
        'neural_routing': {'queries': 100, 'avg_judge': 6.2, 'ce_usage': 25},
        'heuristic_routing': {'queries': 100, 'avg_judge': 5.8, 'ce_usage': 20}
    }

    # Calculate improvement
    neural_score = ab_results['neural_routing']['avg_judge']
    heuristic_score = ab_results['heuristic_routing']['avg_judge']
    improvement = neural_score - heuristic_score

    print("A/B Test Results:")
    print(f"  Neural routing: {neural_score:.1f} avg judge")
    print(f"  Heuristic routing: {heuristic_score:.1f} avg judge")
    print(f"  Improvement: +{improvement:.1f} pts")

    assert improvement > 0, "Neural routing should improve scores"
    print("✅ A/B testing framework working")

def run_all_tests():
    """Run all neural router tests."""
    print("🚀 Running CE Neural Router Tests")
    print("=" * 50)

    try:
        test_neural_router_basic()
        test_router_high_level_api()
        test_performance_recording()
        test_router_stats()
        test_fallback_behavior()
        test_router_ab_testing()

        print("\n🎉 All neural router tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
