# STOP Evaluation Metrics System

This document describes the evaluation metrics system designed to support Self-Taught Optimizer (STOP) integration into the AGI Core framework.

## Overview

The evaluation metrics system provides:

1. **Baseline Measurement** - Establish current performance benchmarks
2. **Real-time Instrumentation** - Track metrics during operation
3. **Utility Functions** - Objective functions for STOP optimization
4. **Before/After Comparison** - Measure improvement from optimizations
5. **Comprehensive Reporting** - Generate detailed performance reports

## Architecture

```
agi_core/
├── evaluation_metrics.py      # Core metrics framework
├── measure_baseline.py         # Baseline measurement script
├── context_engineering.py      # Instrumented with metrics
├── agent_experts.py            # Instrumented with metrics
└── EVALUATION_METRICS_README.md  # This file
```

### Key Components

#### 1. `PerformanceMetrics`
Tracks comprehensive performance data:
- **Timing**: execution_time_ms, latency_p50/p95/p99
- **Context**: tokens_used, context_utilization, efficiency_score
- **Quality**: success_rate, error_rate, test_coverage, code_quality_score
- **Resources**: memory_mb, cpu_percent
- **Utility Score**: Weighted combination optimized for PRD requirements

#### 2. `MetricsCollector`
Central collection and storage:
```python
from agi_core import get_metrics_collector

collector = get_metrics_collector()

# Record context metrics
collector.record_context_metrics(
    agent_id="agent_1",
    operation="reduce_context",
    metrics={
        "tokens_freed": 50000,
        "efficiency_score": 0.85
    }
)

# Record agent metrics
collector.record_agent_metrics(
    agent_id="expert_1",
    task_type="debugging",
    metrics={
        "execution_time_ms": 45.2,
        "success": True
    }
)

# Generate report
report = collector.generate_report()
```

#### 3. `UtilityFunction`
Objective functions for STOP optimization:

```python
from agi_core import UtilityFunction

# Context reduction utility
utility = UtilityFunction.context_reduction_utility(
    original_tokens=100000,
    reduced_tokens=60000,
    information_loss=0.05
)

# Agent performance utility
utility = UtilityFunction.agent_performance_utility(
    latency_ms=35.0,
    success_rate=0.95,
    context_efficiency=0.90,
    target_latency_ms=50.0
)

# Governance utility
utility = UtilityFunction.governance_utility(
    false_positive_rate=0.02,
    false_negative_rate=0.01,
    response_time_ms=30.0
)
```

#### 4. `OptimizationResult`
Captures before/after comparison:
```python
result = collector.record_optimization(
    optimization_id="opt_001",
    target_function="reduce_context",
    strategy="beam_search",
    baseline_metrics=baseline,
    improved_metrics=improved,
    iterations=10,
    duration_seconds=45.3,
    confidence_score=0.92
)

print(f"Improvement: {result.utility_improvement:.2f}%")
print(f"Significant: {result.is_significant_improvement()}")
```

## Usage

### Step 1: Establish Baselines

Run the baseline measurement script:

```bash
# Full baseline measurement (10 iterations each)
python agi_core/measure_baseline.py

# Quick baseline (3 iterations)
python agi_core/measure_baseline.py --quick

# Custom output directory and iterations
python agi_core/measure_baseline.py \
    --output-dir ./my_baselines \
    --iterations 20
```

Output:
```
📊 Measuring Context Reduction Baseline (10 iterations)...
  Iteration 1: 0.15ms, freed 90000 tokens, efficiency=0.600
  ...
  
✅ Context Reduction Baseline:
   Latency (p95): 0.18ms
   Efficiency: 0.600
   Utility Score: 0.850

📊 Measuring Agent Execution Baseline (10 iterations)...
  ...

💾 Baseline report saved to: ./state/baselines/baseline_report.json
💾 Summary saved to: ./state/baselines/baseline_summary.txt
```

### Step 2: Review Baselines

Check the generated reports:

```bash
cat state/baselines/baseline_summary.txt
```

Example output:
```
================================================================================
STOP Baseline Measurement Summary
================================================================================

Measured at: 2025-10-15T14:30:00

Baselines:
--------------------------------------------------------------------------------

CONTEXT_REDUCTION:
  Utility Score: 0.850
  Latency (p95): 0.18ms
  Success Rate: 100.00%
  Context Efficiency: 0.600

AGENT_EXECUTION:
  Utility Score: 0.875
  Latency (p95): 1.25ms
  Success Rate: 100.00%
  Context Efficiency: 0.900

GOVERNANCE_VERDICT:
  Utility Score: 0.920
  Latency (p95): 0.05ms
  Success Rate: 100.00%
  Context Efficiency: 0.950

Optimization Targets:
--------------------------------------------------------------------------------

[MEDIUM] context_reduction
  Reason: Context efficiency (0.600) below 0.85 target

Recommendations:
--------------------------------------------------------------------------------
1. Apply STOP optimization to targets listed above
2. Focus on high-priority targets first
3. Use utility_score as the optimization objective function
```

### Step 3: Monitor Real-Time Metrics

The system automatically collects metrics during operation:

```python
from agi_core import ContextManager, get_metrics_collector

# Context operations are automatically instrumented
context_manager = ContextManager()
context = context_manager.create_context("agent_1", "session_1")
result = context_manager.reduce_context("agent_1")

# View collected metrics
collector = get_metrics_collector()
report = collector.generate_report()
print(report)
```

### Step 4: Measure Optimizations

When implementing STOP improvements:

```python
from agi_core import get_metrics_collector, PerformanceMetrics

collector = get_metrics_collector()

# Load baseline
baseline = collector.load_baseline("context_reduction")

# ... run STOP optimization ...

# Create improved metrics
improved = PerformanceMetrics(
    execution_time_ms=0.12,
    latency_p95_ms=0.15,
    context_efficiency_score=0.85,
    success_rate=1.0,
    # ... other metrics
)

# Record the optimization
result = collector.record_optimization(
    optimization_id="stop_001",
    target_function="context_reduction",
    strategy="genetic_algorithm",
    baseline_metrics=baseline,
    improved_metrics=improved,
    iterations=50,
    duration_seconds=120.5,
    confidence_score=0.94
)

if result.is_significant_improvement():
    print(f"✅ Significant improvement: {result.utility_improvement:.2f}%")
else:
    print("❌ No significant improvement detected")
```

## Utility Score Calculation

The utility score is the primary objective function for STOP optimization. It combines multiple metrics with PRD-aligned weights:

```python
def utility_score(self) -> float:
    weights = {
        "latency": 0.25,           # Rule #8: Performance budget < 50ms
        "context_efficiency": 0.25, # Context engineering focus
        "success_rate": 0.20,       # Reliability
        "code_quality": 0.15,       # Rule #7: Test coverage ≥ 85%
        "resource": 0.15            # Efficiency
    }
    
    # Normalize and weight each component
    latency_score = max(0, 1 - (latency_p95_ms / 50.0))
    context_score = context_efficiency_score
    success_score = success_rate
    quality_score = code_quality_score
    resource_score = max(0, 1 - (cpu_percent / 100.0))
    
    return (
        weights["latency"] * latency_score +
        weights["context_efficiency"] * context_score +
        weights["success_rate"] * success_score +
        weights["code_quality"] * quality_score +
        weights["resource"] * resource_score
    )
```

**Interpretation:**
- `1.0` = Perfect performance across all dimensions
- `0.85+` = Excellent, meets all PRD targets
- `0.70-0.85` = Good, meets most targets
- `< 0.70` = Needs optimization

## Instrumentation

The system automatically instruments key components:

### Context Engineering
- `reduce_context()` - Tracks token reduction and efficiency
- `delegate_to_agent()` - Tracks delegation patterns
- `prime_context()` - Tracks context priming effectiveness

### Agent Experts
- `execute_task()` - Tracks execution time, success rate, token usage
- Expert-specific metrics per domain

### Governance Orchestrator
- `apply_verdict()` - Tracks verdict processing (via orchestrator/app.py)
- ECE, latency deltas, violation rates

## Data Storage

Metrics are stored in multiple formats:

```
state/
├── metrics/
│   ├── context_metrics.jsonl        # Time-series context data
│   ├── agent_metrics.jsonl          # Time-series agent data
│   ├── governance_metrics.jsonl     # Time-series governance data
│   ├── baseline_*.json              # Baseline measurements
│   └── optimization_*.json          # Optimization results
└── baselines/
    ├── baseline_report.json         # Comprehensive baseline report
    └── baseline_summary.txt         # Human-readable summary
```

### JSONL Format
Each line is a complete JSON record:
```json
{"agent_id": "agent_1", "operation": "reduce_context", "metrics": {...}, "timestamp": 1234567890.123}
{"agent_id": "agent_2", "operation": "prime_context", "metrics": {...}, "timestamp": 1234567891.456}
```

Benefits:
- Append-only writes (fast)
- Easy to stream and process
- Simple disaster recovery

## PRD Alignment

This metrics system supports the following PRD rules:

### Rule #7: Test Coverage Must Be ≥ 85%
- `code_quality_score` includes test coverage
- Utility function penalizes coverage below 0.85

### Rule #8: Performance Budget Is Non-Negotiable
- Target latency: < 50ms for latency-sensitive operations
- `latency_p95_ms` tracked for all operations
- Utility function heavily penalizes latency above 50ms

### Rule #1: All Work Must Trace Back to PRD
- Metrics system enables measuring compliance
- Optimization targets tied to PRD requirements
- Baselines establish current state vs. PRD targets

## Integration with STOP

When implementing STOP optimization:

1. **Use `utility_score()` as the objective function**
   - STOP maximizes this value
   - Already aligned with PRD priorities

2. **Use specific utility functions for domain optimization**
   - `UtilityFunction.context_reduction_utility()` for context work
   - `UtilityFunction.agent_performance_utility()` for agent work
   - `UtilityFunction.governance_utility()` for governance work

3. **Record all optimization attempts**
   - Use `record_optimization()` to track improvements
   - Compare baseline vs. improved metrics
   - Calculate confidence scores

4. **Validate improvements**
   - Use `is_significant_improvement()` (threshold: 5%)
   - Require human review for < 80% confidence
   - Align with governance `require_human_review` flag

## Decorator Usage

For quick instrumentation:

```python
from agi_core import measure_execution

@measure_execution
def my_optimization_function(args):
    # Your function code
    return result

# Metrics automatically collected on each execution
```

## Example: Complete STOP Integration

```python
from agi_core import (
    get_metrics_collector,
    PerformanceMetrics,
    UtilityFunction
)

def stop_optimize_context_reduction():
    """
    Example: Use STOP to optimize context reduction
    """
    collector = get_metrics_collector()
    
    # 1. Load baseline
    baseline = collector.load_baseline("context_reduction")
    print(f"Baseline utility: {baseline.utility_score():.3f}")
    
    # 2. Run STOP optimization
    # (This would invoke actual STOP framework)
    improved_strategy = run_stop_optimization(
        target_function="reduce_context",
        baseline_metrics=baseline,
        utility_function=UtilityFunction.context_reduction_utility,
        iterations=50
    )
    
    # 3. Measure improved version
    improved = measure_improved_performance(improved_strategy)
    
    # 4. Record optimization
    result = collector.record_optimization(
        optimization_id="stop_context_001",
        target_function="context_reduction",
        strategy=improved_strategy["strategy"],
        baseline_metrics=baseline,
        improved_metrics=improved,
        iterations=50,
        duration_seconds=improved_strategy["duration"],
        confidence_score=improved_strategy["confidence"]
    )
    
    # 5. Decide whether to deploy
    if result.is_significant_improvement() and result.confidence_score > 0.8:
        print(f"✅ Deploying optimization: +{result.utility_improvement:.2f}%")
        deploy_improved_strategy(improved_strategy)
    else:
        print("❌ Optimization not significant enough - keeping baseline")
    
    return result
```

## Troubleshooting

### Metrics not being collected?

Check that the metrics collector is initialized:
```python
from agi_core import get_metrics_collector
collector = get_metrics_collector()
print(f"Metrics dir: {collector.metrics_dir}")
```

### Baseline measurement failing?

Run with verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from agi_core.measure_baseline import BaselineMeasurement
measurement = BaselineMeasurement()
baselines = measurement.establish_all_baselines(iterations=3)
```

### Missing dependencies?

Ensure all AGI Core modules are installed:
```bash
cd /path/to/agi_core
python -c "import agi_core; print('OK')"
```

## Next Steps

After establishing baselines:

1. **Review optimization targets** - Focus on functions below PRD thresholds
2. **Implement STOP framework** - Create `STOPOptimizer` class
3. **Run optimizations** - Apply STOP to identified targets
4. **Validate improvements** - Re-measure and compare to baselines
5. **Deploy optimizations** - Promote successful improvements

## References

- **STOP Paper**: [arXiv:2310.02304](https://arxiv.org/abs/2310.02304)
- **PRD Rules**: See user_rules in project documentation
- **IndyDevDan Framework**: Context Engineering (R&D) patterns

## Support

For questions or issues with the metrics system:
- Review the baseline reports
- Check metric collection in JSONL files
- Verify instrumentation is active
- Consult STOP paper for optimization strategies

