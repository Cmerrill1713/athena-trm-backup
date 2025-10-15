#!/usr/bin/env python3
"""
Quick validation test for evaluation metrics system

This script tests that all components are working correctly.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    try:
        from agi_core.evaluation_metrics import (
            MetricsCollector,
            PerformanceMetrics,
            OptimizationResult,
            UtilityFunction,
            get_metrics_collector,
            measure_execution
        )
        print("   ✅ evaluation_metrics imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False


def test_metrics_collector():
    """Test metrics collector functionality"""
    print("\n🧪 Testing MetricsCollector...")
    try:
        from agi_core import get_metrics_collector
        
        collector = get_metrics_collector()
        print(f"   ✅ Collector initialized: {collector.metrics_dir}")
        
        # Test recording metrics
        collector.record_context_metrics(
            agent_id="test_agent",
            operation="test_operation",
            metrics={
                "tokens_used": 1000,
                "efficiency_score": 0.85
            }
        )
        print("   ✅ Context metrics recorded")
        
        collector.record_agent_metrics(
            agent_id="test_agent",
            task_type="test_task",
            metrics={
                "execution_time_ms": 45.0,
                "success": True
            }
        )
        print("   ✅ Agent metrics recorded")
        
        return True
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_metrics():
    """Test PerformanceMetrics utility score calculation"""
    print("\n🧪 Testing PerformanceMetrics...")
    try:
        from agi_core import PerformanceMetrics
        
        metrics = PerformanceMetrics(
            execution_time_ms=45.0,
            latency_p95_ms=48.0,
            tokens_used=5000,
            context_efficiency_score=0.85,
            success_rate=0.95,
            code_quality_score=0.88,
            test_coverage=0.87
        )
        
        utility = metrics.utility_score()
        print(f"   ✅ Utility score calculated: {utility:.3f}")
        
        if 0 <= utility <= 1:
            print("   ✅ Utility score in valid range [0, 1]")
        else:
            print(f"   ❌ Utility score out of range: {utility}")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utility_functions():
    """Test utility function calculations"""
    print("\n🧪 Testing UtilityFunction...")
    try:
        from agi_core import UtilityFunction
        
        # Test context reduction utility
        context_utility = UtilityFunction.context_reduction_utility(
            original_tokens=100000,
            reduced_tokens=60000,
            information_loss=0.05
        )
        print(f"   ✅ Context reduction utility: {context_utility:.3f}")
        
        # Test agent performance utility
        agent_utility = UtilityFunction.agent_performance_utility(
            latency_ms=35.0,
            success_rate=0.95,
            context_efficiency=0.90,
            target_latency_ms=50.0
        )
        print(f"   ✅ Agent performance utility: {agent_utility:.3f}")
        
        # Test governance utility
        gov_utility = UtilityFunction.governance_utility(
            false_positive_rate=0.02,
            false_negative_rate=0.01,
            response_time_ms=30.0
        )
        print(f"   ✅ Governance utility: {gov_utility:.3f}")
        
        return True
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_baseline_establishment():
    """Test baseline establishment"""
    print("\n🧪 Testing baseline establishment...")
    try:
        from agi_core import get_metrics_collector, PerformanceMetrics
        
        collector = get_metrics_collector()
        
        baseline = PerformanceMetrics(
            execution_time_ms=50.0,
            latency_p95_ms=55.0,
            context_efficiency_score=0.80,
            success_rate=0.90
        )
        
        collector.establish_baseline("test_function", baseline)
        print("   ✅ Baseline established")
        
        loaded = collector.load_baseline("test_function")
        if loaded:
            print(f"   ✅ Baseline loaded: utility={loaded.utility_score():.3f}")
        else:
            print("   ❌ Failed to load baseline")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_optimization_recording():
    """Test optimization result recording"""
    print("\n🧪 Testing optimization recording...")
    try:
        from agi_core import get_metrics_collector, PerformanceMetrics
        
        collector = get_metrics_collector()
        
        baseline = PerformanceMetrics(
            latency_p95_ms=60.0,
            context_efficiency_score=0.75,
            success_rate=0.90
        )
        
        improved = PerformanceMetrics(
            latency_p95_ms=45.0,
            context_efficiency_score=0.88,
            success_rate=0.95
        )
        
        result = collector.record_optimization(
            optimization_id="test_opt_001",
            target_function="test_function",
            strategy="test_strategy",
            baseline_metrics=baseline,
            improved_metrics=improved,
            iterations=10,
            duration_seconds=30.0,
            confidence_score=0.92
        )
        
        print(f"   ✅ Optimization recorded")
        print(f"   ✅ Utility improvement: {result.utility_improvement:.2f}%")
        print(f"   ✅ Significant: {result.is_significant_improvement()}")
        
        return True
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_decorator():
    """Test measure_execution decorator"""
    print("\n🧪 Testing @measure_execution decorator...")
    try:
        from agi_core import measure_execution
        import time
        
        @measure_execution
        def test_function():
            time.sleep(0.01)
            return "success"
        
        result = test_function()
        print(f"   ✅ Decorated function executed: {result}")
        
        return True
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("🔬 EVALUATION METRICS VALIDATION TEST")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("MetricsCollector", test_metrics_collector),
        ("PerformanceMetrics", test_performance_metrics),
        ("UtilityFunction", test_utility_functions),
        ("Baseline Establishment", test_baseline_establishment),
        ("Optimization Recording", test_optimization_recording),
        ("Decorator", test_decorator)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed_test in results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - System ready for STOP integration!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

