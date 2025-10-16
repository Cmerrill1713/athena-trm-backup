#!/usr/bin/env python3
"""
STOP Optimizer Examples - WITH LOCAL MODELS

Demonstrates how to use the Self-Taught Optimizer with local LLMs.

Requirements:
  1. Install Ollama: curl https://ollama.ai/install.sh | sh
  2. Pull a model: ollama pull codellama:7b
  3. Run examples: python3 agi_core/examples_stop.py

The examples will use local models if available, otherwise simulate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agi_core import (
    STOPOptimizer,
    OptimizationStrategy,
    get_metrics_collector,
    UtilityFunction,
    optimize_function
)
from agi_core.stop_optimizer import LLMInterface


def example_1_simple_optimization():
    """Example 1: Simple function optimization using convenience function"""
    print("=" * 70)
    print("Example 1: Simple Function Optimization")
    print("=" * 70 + "\n")
    
    # Original code to optimize
    original_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
"""
    
    # Define utility function (simple: favor fewer lines)
    def utility_func(metrics):
        # Simple utility: favor code with fewer lines but maintain correctness
        code_lines = metrics.get("code_lines", 100)
        success = metrics.get("success_rate", 0)
        
        # Penalize long code, reward success
        utility = success * (1.0 - (code_lines / 100.0))
        return max(0.0, min(1.0, utility))
    
    # Run optimization
    result = optimize_function(
        code=original_code,
        utility_function=utility_func,
        description="Optimize for conciseness while maintaining correctness",
        strategy=OptimizationStrategy.BEAM_SEARCH,
        iterations=5
    )
    
    print(f"✓ Optimization complete!")
    print(f"  Baseline utility: {result.baseline_utility:.3f}")
    print(f"  Improved utility: {result.improved_utility:.3f}")
    print(f"  Improvement: {result.improvement_percent:.1f}%")
    print(f"  Confidence: {result.confidence_score:.3f}")
    print(f"  Candidates generated: {result.candidates_generated}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    
    print(f"\nBest candidate code:")
    print("```python")
    print(result.best_candidate.code)
    print("```\n")


def example_2_context_reduction_optimization():
    """Example 2: Optimize context reduction strategy"""
    print("=" * 70)
    print("Example 2: Context Reduction Optimization")
    print("=" * 70 + "\n")
    
    # Original context reduction code
    original_code = """
def reduce_context(tokens):
    # Simple reduction: keep 50%
    return int(tokens * 0.5)
"""
    
    # Utility function focused on context efficiency
    def utility_func(metrics):
        efficiency = metrics.get("context_efficiency", 0.0)
        success = metrics.get("success_rate", 0.0)
        
        # Heavily weight efficiency
        return 0.7 * efficiency + 0.3 * success
    
    # Create optimizer with custom settings
    optimizer = STOPOptimizer()
    
    result = optimizer.optimize(
        target_code=original_code,
        utility_function=utility_func,
        utility_description="Maximize context reduction efficiency",
        strategy=OptimizationStrategy.BEAM_SEARCH,
        iterations=10,
        beam_width=5
    )
    
    print(f"✓ Optimization complete!")
    print(f"  Strategy: {result.strategy.value}")
    print(f"  Improvement: {result.improvement_percent:.1f}%")
    print(f"  Best generation: {result.best_candidate.generation}")
    print(f"  Confidence: {result.confidence_score:.3f}")
    
    # Save result
    print(f"\n  Result saved: state/stop_optimizer/{result.optimization_id}.json\n")


def example_3_multi_strategy_comparison():
    """Example 3: Compare different optimization strategies"""
    print("=" * 70)
    print("Example 3: Multi-Strategy Comparison")
    print("=" * 70 + "\n")
    
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    # Performance-focused utility
    util_func = UtilityFunction()
    
    def perf_utility(metrics):
        speed = util_func.normalize_speed(
            metrics.get("execution_time_ms", 100),
            target_time_ms=10.0
        )
        success = metrics.get("success_rate", 0.0)
        efficiency = metrics.get("context_efficiency", 0.0)
        
        return util_func.calculate(
            speed_score=speed,
            quality_score=success,
            efficiency_score=efficiency,
            cost_score=0.8  # Assume reasonable cost
        )
    
    strategies = [
        OptimizationStrategy.BEAM_SEARCH,
        OptimizationStrategy.HILL_CLIMBING,
        OptimizationStrategy.RANDOM_SEARCH
    ]
    
    results = []
    
    for strategy in strategies:
        print(f"Testing {strategy.value}...")
        
        result = optimize_function(
            code=code,
            utility_function=perf_utility,
            description="Optimize fibonacci for performance",
            strategy=strategy,
            iterations=5
        )
        
        results.append((strategy, result))
        print(f"  Improvement: {result.improvement_percent:.1f}%")
        print(f"  Confidence: {result.confidence_score:.3f}\n")
    
    # Find best strategy
    best_strategy, best_result = max(results, key=lambda x: x[1].improved_utility)
    
    print(f"🏆 Best strategy: {best_strategy.value}")
    print(f"   Improvement: {best_result.improvement_percent:.1f}%")
    print(f"   Utility: {best_result.improved_utility:.3f}\n")


def example_4_with_metrics_integration():
    """Example 4: STOP with metrics collector integration"""
    print("=" * 70)
    print("Example 4: STOP with Metrics Integration")
    print("=" * 70 + "\n")
    
    collector = get_metrics_collector()
    
    # Set baseline
    collector.set_baseline("optimization_utility", 0.75)
    
    code = """
def process_data(items):
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
    return results
"""
    
    def utility_func(metrics):
        # Use AGI Core utility calculation
        util = UtilityFunction()
        
        return util.calculate(
            speed_score=0.8,
            quality_score=metrics.get("success_rate", 0.0),
            efficiency_score=metrics.get("context_efficiency", 0.0),
            cost_score=0.9
        )
    
    result = optimize_function(
        code=code,
        utility_function=utility_func,
        description="Optimize data processing function",
        strategy=OptimizationStrategy.BEAM_SEARCH,
        iterations=8
    )
    
    # Compare to baseline
    comparison = collector.compare_to_baseline(
        "optimization_utility",
        result.improved_utility
    )
    
    if comparison:
        print(f"✓ Optimization complete!")
        print(f"  Baseline: {comparison.baseline_value:.3f}")
        print(f"  Current: {comparison.current_value:.3f}")
        print(f"  Improvement: {comparison.improvement_percent:.1f}%")
        print(f"\n  Recommendation: {comparison.recommendation}\n")


def example_5_expert_agent_optimization():
    """Example 5: Optimize an expert agent's decision logic"""
    print("=" * 70)
    print("Example 5: Expert Agent Optimization")
    print("=" * 70 + "\n")
    
    # Simulate expert agent decision code
    expert_code = """
def should_delegate_task(task_complexity, context_size, agent_capacity):
    # Simple decision logic
    if task_complexity > 7:
        return True
    if context_size > 100000:
        return True
    if agent_capacity < 0.3:
        return True
    return False
"""
    
    def expert_utility(metrics):
        # Want high success rate and good efficiency
        success = metrics.get("success_rate", 0.0)
        efficiency = metrics.get("context_efficiency", 0.0)
        
        # Expert decisions should be accurate and efficient
        return 0.6 * success + 0.4 * efficiency
    
    optimizer = STOPOptimizer()
    
    result = optimizer.optimize(
        target_code=expert_code,
        utility_function=expert_utility,
        utility_description="Optimize expert agent delegation decision logic",
        strategy=OptimizationStrategy.GENETIC_ALGORITHM,
        iterations=10,
        beam_width=4,
        context={
            "agent_type": "expert",
            "domain": "task_delegation"
        }
    )
    
    print(f"✓ Expert agent optimization complete!")
    print(f"  Original utility: {result.baseline_utility:.3f}")
    print(f"  Optimized utility: {result.improved_utility:.3f}")
    print(f"  Improvement: {result.improvement_percent:.1f}%")
    print(f"  Strategy: {result.strategy.value}")
    print(f"  Generations explored: {result.best_candidate.generation}")
    
    if result.improvement_percent > 10 and result.confidence_score > 0.7:
        print(f"\n  ✅ Significant improvement detected!")
        print(f"     Confidence: {result.confidence_score:.3f}")
        print(f"     Recommend deploying optimized version\n")
    else:
        print(f"\n  ⚠️  Improvement not significant enough for deployment")
        print(f"     Try more iterations or different strategy\n")


def check_local_model():
    """Check if local model is available"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                print(f"✅ Found {len(models)} local model(s) in Ollama")
                for model in models[:3]:
                    print(f"   - {model['name']}")
                return True
    except:
        pass
    
    print("⚠️  No local models detected")
    print("   To use real LLM optimization:")
    print("   1. Install Ollama: curl https://ollama.ai/install.sh | sh")
    print("   2. Pull model: ollama pull codellama:7b")
    print("   3. Re-run examples")
    print("\n   For now, using simulated improvements...\n")
    return False


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("STOP Optimizer Examples - Local Models Edition")
    print("=" * 70 + "\n")
    
    # Check for local models
    has_local = check_local_model()
    print()
    
    examples = [
        ("Simple Optimization", example_1_simple_optimization),
        ("Context Reduction", example_2_context_reduction_optimization),
        ("Multi-Strategy Comparison", example_3_multi_strategy_comparison),
        ("Metrics Integration", example_4_with_metrics_integration),
        ("Expert Agent Optimization", example_5_expert_agent_optimization),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ Example '{name}' failed: {e}\n")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 70)
    print("Examples Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review generated optimizations in: state/stop_optimizer/")
    print("  2. Integrate with real LLM for actual code generation")
    print("  3. Apply to production code optimization")
    print()


if __name__ == "__main__":
    main()

