# STOP Optimizer - Self-Taught Code Optimization

**Status**: ✅ Operational  
**Version**: 1.0.0  
**Paper**: [arXiv:2310.02304](https://arxiv.org/abs/2310.02304)

## Overview

The STOP (Self-Taught Optimizer) system enables recursive self-improvement of code by generating and evaluating candidate improvements using LLM-guided optimization strategies.

**Key Features:**
- 🔄 Recursive self-improvement
- 🎯 Utility function-driven optimization
- 🧬 Multiple optimization strategies (beam search, genetic algorithms, simulated annealing)
- 🔒 Sandboxed execution for safety
- 📊 Full metrics integration
- 🤖 LLM-powered code generation

## Quick Start

### Basic Usage

```python
from agi_core import optimize_function, OptimizationStrategy

# Define code to optimize
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

# Define utility function
def utility_func(metrics):
    speed = metrics.get("execution_time_ms", 100)
    success = metrics.get("success_rate", 0)
    return success * (1.0 - (speed / 100.0))

# Optimize!
result = optimize_function(
    code=code,
    utility_function=utility_func,
    description="Optimize for speed",
    strategy=OptimizationStrategy.BEAM_SEARCH,
    iterations=10
)

print(f"Improvement: {result.improvement_percent:.1f}%")
print(f"Best code:\n{result.best_candidate.code}")
```

### Advanced Usage

```python
from agi_core import STOPOptimizer, get_metrics_collector

# Create optimizer with custom settings
optimizer = STOPOptimizer(
    metrics_collector=get_metrics_collector(),
    llm_interface=None,  # Will use default (or provide custom)
    sandbox=None         # Will use default sandboxed executor
)

# Run optimization with context
result = optimizer.optimize(
    target_code=code,
    utility_function=utility_func,
    utility_description="Maximize performance while maintaining correctness",
    strategy=OptimizationStrategy.GENETIC_ALGORITHM,
    iterations=20,
    beam_width=5,
    context={"domain": "algorithms", "language": "python"}
)

# Check if improvement is significant
if result.improvement_percent > 10 and result.confidence_score > 0.8:
    print("✅ Significant improvement - deploy!")
    # Deploy optimized code
else:
    print("⚠️  Try more iterations or different strategy")
```

## Optimization Strategies

### 1. Beam Search
```python
OptimizationStrategy.BEAM_SEARCH
```
- Maintains top-K candidates at each generation
- Good for exploring multiple improvement paths
- **Best for**: Most use cases, balanced exploration

### 2. Genetic Algorithm
```python
OptimizationStrategy.GENETIC_ALGORITHM
```
- Combines best features from parent candidates
- Evolves solutions over generations
- **Best for**: Complex optimization landscapes

### 3. Simulated Annealing
```python
OptimizationStrategy.SIMULATED_ANNEALING
```
- Probabilistic approach with cooling schedule
- Can escape local optima
- **Best for**: Avoiding premature convergence

### 4. Hill Climbing
```python
OptimizationStrategy.HILL_CLIMBING
```
- Greedy local optimization
- Fast but may get stuck
- **Best for**: Quick improvements, simple problems

### 5. Random Search
```python
OptimizationStrategy.RANDOM_SEARCH
```
- Explores random variations
- Baseline for comparison
- **Best for**: Establishing baselines

## Utility Functions

### Performance-Focused
```python
from agi_core import UtilityFunction

util = UtilityFunction(weights={
    "speed": 0.5,        # 50% weight on speed
    "quality": 0.3,      # 30% on correctness
    "efficiency": 0.15,  # 15% on efficiency
    "cost": 0.05         # 5% on resource cost
})

def utility_func(metrics):
    return util.calculate(
        speed_score=util.normalize_speed(metrics["execution_time_ms"], 50),
        quality_score=metrics["success_rate"],
        efficiency_score=metrics["context_efficiency"],
        cost_score=util.normalize_cost(metrics["tokens_used"], 5000)
    )
```

### Correctness-Focused
```python
def quality_utility(metrics):
    # Heavily prioritize correctness
    success = metrics.get("success_rate", 0.0)
    efficiency = metrics.get("context_efficiency", 0.0)
    
    # 90% weight on correctness, 10% on efficiency
    return 0.9 * success + 0.1 * efficiency
```

### Efficiency-Focused
```python
def efficiency_utility(metrics):
    # Optimize for token usage
    tokens = metrics.get("tokens_used", 10000)
    success = metrics.get("success_rate", 0.0)
    
    # Lower tokens is better
    token_score = max(0, 1.0 - (tokens / 10000))
    return 0.7 * token_score + 0.3 * success
```

## LLM Integration

### Setup with OpenAI GPT-4
```python
import os
from agi_core import STOPOptimizer
from agi_core.stop_optimizer import LLMInterface

# Set API key
os.environ["OPENAI_API_KEY"] = "your-api-key"

# Create LLM interface
llm = LLMInterface(model="gpt-4")

# Create optimizer with LLM
optimizer = STOPOptimizer(llm_interface=llm)

# Run optimization (will use GPT-4 for code generation)
result = optimizer.optimize(...)
```

### Custom LLM Interface
```python
class CustomLLM(LLMInterface):
    def generate_improvement(self, original_code, utility_description, context, strategy):
        # Your custom LLM integration
        prompt = self._build_prompt(original_code, utility_description, context, strategy)
        response = your_llm_api.generate(prompt)
        return response.code
```

## Sandboxed Execution

STOP includes safe sandboxed execution:

```python
from agi_core.stop_optimizer import SandboxExecutor

sandbox = SandboxExecutor(timeout_seconds=5)

# Execute code safely
success, time_ms, error = sandbox.execute(
    code=candidate_code,
    test_inputs=[1, 2, 3],
    expected_behavior=lambda output: "6" in output
)

if success:
    print(f"Executed in {time_ms:.2f}ms")
else:
    print(f"Failed: {error}")
```

## Examples

### Example 1: Optimize Context Reduction
```python
from agi_core import optimize_function

code = """
def reduce_context(tokens, max_tokens):
    # Keep 60% of tokens
    return int(tokens * 0.6)
"""

def context_utility(metrics):
    efficiency = metrics.get("context_efficiency", 0.0)
    return efficiency

result = optimize_function(
    code=code,
    utility_function=context_utility,
    description="Maximize token reduction efficiency",
    iterations=15
)
```

### Example 2: Optimize Agent Decision Logic
```python
agent_code = """
def should_delegate(complexity, context_size):
    if complexity > 8:
        return True
    return context_size > 150000
"""

def decision_utility(metrics):
    success = metrics.get("success_rate", 0.0)
    speed = 1.0 - (metrics.get("execution_time_ms", 10) / 100.0)
    return 0.7 * success + 0.3 * speed

result = optimize_function(
    code=agent_code,
    utility_function=decision_utility,
    description="Optimize delegation decision accuracy",
    strategy=OptimizationStrategy.GENETIC_ALGORITHM,
    iterations=20
)
```

### Example 3: Multi-Strategy Comparison
```python
strategies = [
    OptimizationStrategy.BEAM_SEARCH,
    OptimizationStrategy.GENETIC_ALGORITHM,
    OptimizationStrategy.SIMULATED_ANNEALING
]

results = []
for strategy in strategies:
    result = optimize_function(
        code=target_code,
        utility_function=util_func,
        strategy=strategy,
        iterations=10
    )
    results.append((strategy, result))

# Find best
best = max(results, key=lambda x: x[1].improved_utility)
print(f"Best strategy: {best[0].value}")
```

## Integration with AGI Core

### With Metrics Collector
```python
from agi_core import get_metrics_collector, STOPOptimizer

collector = get_metrics_collector()

# Set baseline
collector.set_baseline("optimization_utility", 0.75)

# Run optimization
optimizer = STOPOptimizer(metrics_collector=collector)
result = optimizer.optimize(...)

# Compare to baseline
comparison = collector.compare_to_baseline(
    "optimization_utility",
    result.improved_utility
)

print(f"Improvement over baseline: {comparison.improvement_percent:.1f}%")
```

### With Expert Agents
```python
from agi_core import ExpertRegistry, STOPOptimizer

registry = ExpertRegistry()

# Get expert's decision code
expert = registry.get_expert("performance_expert")

# Optimize expert's logic
result = optimize_function(
    code=expert.system_prompt,  # Could optimize prompts too!
    utility_function=expert_utility,
    description="Optimize expert decision making"
)
```

## Running Examples

```bash
# Run all examples
python3 agi_core/examples_stop.py

# View generated optimizations
ls -la state/stop_optimizer/

# Check specific optimization
cat state/stop_optimizer/stop_*.json | python3 -m json.tool
```

## Result Format

```python
@dataclass
class OptimizationResult:
    optimization_id: str              # Unique ID
    target_function: str               # What was optimized
    strategy: OptimizationStrategy     # Strategy used
    iterations: int                    # Iterations run
    candidates_generated: int          # Total candidates
    best_candidate: OptimizationCandidate  # Best solution
    baseline_utility: float            # Starting utility
    improved_utility: float            # Final utility
    improvement_percent: float         # % improvement
    duration_seconds: float            # Time taken
    confidence_score: float            # Confidence (0-1)
    timestamp: float                   # When completed
```

## Confidence Scoring

STOP calculates confidence based on:
1. **Improvement magnitude** (50%) - How much better
2. **Exploration depth** (30%) - How many candidates evaluated
3. **Generation depth** (20%) - How many iterations

```python
if result.confidence_score > 0.8:
    print("High confidence - safe to deploy")
elif result.confidence_score > 0.6:
    print("Medium confidence - review recommended")
else:
    print("Low confidence - more optimization needed")
```

## Best Practices

### 1. Start with Baselines
```python
# Always measure baseline first
collector = get_metrics_collector()
baseline_result = measure_current_performance()
collector.set_baseline("function_utility", baseline_result)
```

### 2. Use Appropriate Strategies
- **Quick improvements**: Hill climbing or random search
- **General optimization**: Beam search (default)
- **Complex problems**: Genetic algorithm or simulated annealing

### 3. Set Reasonable Iterations
```python
# Start small
result = optimize_function(..., iterations=5)

# If promising, increase
if result.improvement_percent > 5:
    result = optimize_function(..., iterations=20)
```

### 4. Validate Results
```python
if result.confidence_score > 0.8 and result.improvement_percent > 10:
    # Run additional validation
    validation_result = validate_candidate(result.best_candidate.code)
    
    if validation_result.success:
        deploy_optimization(result.best_candidate.code)
```

### 5. Human Review Gate
```python
# Require human review for low confidence
if result.confidence_score < 0.7:
    print("⚠️  Low confidence - human review required")
    # Send to review queue
elif result.improvement_percent < 5:
    print("⚠️  Small improvement - verify worthwhile")
else:
    print("✅ Ready for deployment")
```

## Troubleshooting

### No Improvements Generated
```python
# Try different strategy
result = optimize_function(..., strategy=OptimizationStrategy.RANDOM_SEARCH)

# Increase iterations
result = optimize_function(..., iterations=50)

# Adjust utility function
# Make sure it's providing meaningful signal
```

### LLM Not Generating Good Code
```python
# Provide better context
result = optimizer.optimize(
    ...,
    context={
        "language": "python",
        "style": "functional",
        "complexity": "moderate",
        "examples": ["good code examples"]
    }
)

# Refine utility description
utility_description = """
Optimize for:
1. Performance (execution speed < 10ms)
2. Correctness (must handle all edge cases)
3. Readability (clear variable names)
"""
```

### Sandbox Timeouts
```python
# Increase timeout
sandbox = SandboxExecutor(timeout_seconds=10)
optimizer = STOPOptimizer(sandbox=sandbox)
```

## Limitations

1. **LLM Required**: Real improvements need LLM integration (currently simulated)
2. **Syntax Only**: Sandbox validates syntax, not full correctness
3. **No Execution**: Current version doesn't run code to measure actual performance
4. **Cost**: LLM calls for many candidates can be expensive

## Future Enhancements

- [ ] Full code execution in sandbox
- [ ] Performance profiling integration
- [ ] Multi-file optimization
- [ ] Test case generation
- [ ] Automated A/B testing
- [ ] Cloud LLM integration
- [ ] Optimization templates
- [ ] Distributed optimization

## References

- **STOP Paper**: https://arxiv.org/abs/2310.02304
- **AGI Core**: See `README.md`
- **Metrics System**: See `METRICS_SUMMARY.md`

---

**STOP Optimizer - Making code improve itself!** 🚀

