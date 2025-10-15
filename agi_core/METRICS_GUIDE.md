# AGI Core - Metrics & Evaluation Guide

## 📊 Overview

The AGI Core metrics system provides comprehensive performance tracking and optimization capabilities for your agent systems. It automatically collects, analyzes, and reports on:

- **Context Efficiency** - How well agents manage context windows
- **Agent Performance** - Execution time, success rates, token usage
- **Workflow Outcomes** - Scout-Plan-Build phase metrics
- **Resource Utilization** - Token consumption, parallelization efficiency
- **Multi-Objective Optimization** - Utility scores balancing speed, quality, efficiency, and cost

## 🎯 Key Metrics

### Context Engineering Metrics

1. **Tokens Freed** - Context tokens recovered through REDUCE operations
2. **Efficiency Score** - Ratio of useful to total context (0-1)
3. **Operation Counts** - Reduce, delegate, and prime operations
4. **Utilization** - Context window usage percentage

### Agent Performance Metrics

1. **Execution Time** - Time to complete tasks (milliseconds)
2. **Success Rate** - Percentage of successful task completions
3. **Token Usage** - Average tokens consumed per task
4. **Context Efficiency** - How efficiently agents use context
5. **Utility Score** - Multi-objective optimization score (0-1)

### Workflow Metrics

1. **Phase Duration** - Time for each Scout/Plan/Build phase
2. **Total Time** - End-to-end workflow execution
3. **Token Consumption** - Tokens used across all phases
4. **Success/Failure Rates** - Workflow outcome tracking

## 🚀 Quick Start

### 1. Run Baseline Measurement

```bash
cd /Users/christianmerrill/Documents/GitHub
python3 -m agi_core.measure_baseline
```

**Output:**
```
✓ Context creation: 0.21ms
✓ Context reduction: 0.32ms (freed 142,500 tokens, 95% efficiency)
✓ Expert execution: 0.12ms average
✓ Workflow execution: 0.14ms (3 phases, 18,300 tokens)
✓ Delegation: 0.15ms per task

✓ Full report saved to: state/metrics/baseline_report.json
```

### 2. Access Metrics in Code

```python
from agi_core.evaluation_metrics import get_metrics_collector

# Get metrics collector
collector = get_metrics_collector()

# Get agent summary
summary = collector.get_agent_summary("debug_expert")
print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Avg time: {summary['avg_execution_time_ms']:.2f}ms")
print(f"Tokens/task: {summary['avg_tokens_per_task']:.0f}")

# Get context summary
context = collector.get_context_summary("agent_001")
print(f"Tokens freed: {context['total_tokens_freed']:,}")
print(f"Efficiency: {context['avg_efficiency_score']:.1%}")

# Calculate utility score
utility = collector.calculate_utility_score("debug_expert")
print(f"Utility score: {utility:.3f}")  # 0-1, higher is better
```

### 3. Compare to Baseline

```python
# Set baseline (typically from initial measurement)
collector.set_baseline("execution_time_ms", 1.5)

# Later, compare current performance
current_time = 1.2
result = collector.compare_to_baseline("execution_time_ms", current_time)

print(f"Baseline: {result.baseline_value:.2f}ms")
print(f"Current: {result.current_value:.2f}ms")
print(f"Improvement: {result.improvement_percent:.1f}%")
print(f"Recommendation: {result.recommendation}")
```

## 📈 Utility Function

The utility function balances multiple objectives:

### Components (weights sum to 1.0)

- **Speed (0.3)** - Fast execution time
- **Quality (0.4)** - High success rate (most important)
- **Efficiency (0.2)** - Good context usage
- **Cost (0.1)** - Low token consumption

### Custom Weights

```python
from agi_core.evaluation_metrics import UtilityFunction

# Custom weights for your priorities
utility = UtilityFunction(weights={
    "speed": 0.4,      # Prioritize speed
    "quality": 0.3,
    "efficiency": 0.2,
    "cost": 0.1
})

# Calculate utility score
score = utility.calculate(
    speed_score=0.9,      # Fast
    quality_score=0.95,   # High success
    efficiency_score=0.85,
    cost_score=0.8
)
# → 0.875 (excellent performance)
```

## 🔍 Metrics Collection

### Automatic Collection

Metrics are automatically collected when you use AGI Core:

```python
from agi_core import ContextManager, ExpertOrchestrator

# Context operations auto-tracked
cm = ContextManager()
result = cm.reduce_context("agent_001")
# → Metrics recorded automatically

# Expert operations auto-tracked
orchestrator = ExpertOrchestrator(registry)
task_id = orchestrator.submit_task("debugging", "Fix bug", {})
result = orchestrator.execute_task(task_id)
# → Execution time, success, tokens tracked
```

### Manual Collection

```python
from agi_core.evaluation_metrics import get_metrics_collector

collector = get_metrics_collector()

# Record custom metrics
collector.record_agent_metrics(
    agent_id="custom_agent",
    task_type="optimization",
    metrics={
        "execution_time_ms": 245.0,
        "success": True,
        "tokens_used": 8500,
        "context_efficiency": 0.89,
        "custom_metric": 42
    }
)

# Record context metrics
collector.record_context_metrics(
    agent_id="agent_001",
    operation="custom_reduce",
    metrics={
        "tokens_freed": 15000,
        "efficiency_score": 0.92,
        "strategy": "aggressive"
    }
)
```

### Decorator for Functions

```python
from agi_core.evaluation_metrics import measure_execution

@measure_execution("data_processing")
def process_data(data):
    # Your code here
    result = expensive_operation(data)
    return result

# Execution time and success automatically tracked
result = process_data(my_data)
```

## 📊 Reports

### Generate Comprehensive Report

```python
from pathlib import Path

report = collector.generate_report(
    output_file=Path("./metrics_report.json")
)

# Report includes:
# - All agent summaries
# - Context summaries
# - Top performers
# - Recommendations
print(f"Total agents: {report['total_agents']}")
print(f"Top performer: {report['top_performers'][0]}")
```

### Export Metrics for Analysis

```python
from datetime import datetime, timedelta

# Export last 24 hours
start_time = (datetime.now() - timedelta(days=1)).timestamp()
metrics = collector.export_metrics(
    start_time=start_time,
    output_file=Path("./metrics_export.json")
)

# Use with pandas, jupyter, etc.
import pandas as pd
df = pd.DataFrame(metrics)
```

## 🎯 Optimization Workflow

### 1. Establish Baselines

```bash
# Run baseline measurement
python3 -m agi_core.measure_baseline
```

### 2. Monitor Performance

```python
# Continuously track metrics
collector = get_metrics_collector()

# After each significant operation
summary = collector.get_agent_summary("my_agent")
if summary["success_rate"] < 0.8:
    print("⚠️  Low success rate, investigate!")
```

### 3. Compare & Optimize

```python
# Compare to baseline
result = collector.compare_to_baseline(
    "context_efficiency",
    current_efficiency
)

if result.improvement_percent < 0:
    # Performance degraded
    print(f"⚠️  {result.recommendation}")
    # Apply REDUCE strategy more aggressively
    cm.reduce_context(agent_id)
```

### 4. Track Top Performers

```python
# Identify what works best
top = collector.get_top_performers(limit=5)

for agent in top:
    print(f"{agent['agent_id']}: {agent['utility_score']:.3f}")
    # Study and replicate successful patterns
```

## 📐 Key Performance Indicators (KPIs)

### Target Values

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Success Rate | > 80% | > 90% | > 95% |
| Context Efficiency | > 70% | > 85% | > 90% |
| Execution Time | < 1000ms | < 500ms | < 100ms |
| Utility Score | > 0.7 | > 0.8 | > 0.9 |
| Tokens/Task | < 15k | < 10k | < 5k |

### Monitoring Recommendations

1. **Success Rate < 80%**
   - Review task types and agent matching
   - Check expert capabilities
   - Improve error handling

2. **Context Efficiency < 70%**
   - Apply REDUCE strategy more frequently
   - Trim memory files
   - Remove unused MCP tools
   - Use context priming

3. **Execution Time > 1s**
   - Use parallel workflows
   - Delegate to background agents
   - Optimize critical paths

4. **High Token Usage**
   - Delegate to specialists (smaller context)
   - Use context bundles for replay
   - Implement aggressive reduction

## 🔬 Advanced Analysis

### Trend Analysis

```python
# Get historical data
metrics = collector.performance_metrics[-1000:]  # Last 1000

# Calculate trends
import statistics

recent = metrics[-100:]
older = metrics[-200:-100]

recent_avg = statistics.mean(m.execution_time_ms for m in recent)
older_avg = statistics.mean(m.execution_time_ms for m in older)

trend = (recent_avg - older_avg) / older_avg * 100
print(f"Performance trend: {trend:+.1f}%")
```

### A/B Testing

```python
# Compare two configurations
config_a_metrics = [m for m in collector.performance_metrics 
                    if m.metadata.get("config") == "A"]
config_b_metrics = [m for m in collector.performance_metrics 
                    if m.metadata.get("config") == "B"]

# Compare utilities
utility_a = calculate_avg_utility(config_a_metrics)
utility_b = calculate_avg_utility(config_b_metrics)

print(f"Config A utility: {utility_a:.3f}")
print(f"Config B utility: {utility_b:.3f}")
print(f"Winner: {'B' if utility_b > utility_a else 'A'}")
```

## 📊 Grafana Integration

Metrics are exported in Prometheus format via `/metrics` endpoint:

```prometheus
# AGI-specific metrics
agi_context_efficiency{agent_id="agent_001"} 0.89
agi_execution_time_ms{agent_id="debug_expert"} 245.0
agi_success_rate{agent_id="scout_expert"} 0.95
agi_tokens_used{agent_id="build_expert"} 8500
```

Create Grafana dashboards to visualize:
- Real-time efficiency trends
- Agent performance comparison
- Token usage patterns
- Success rates over time

## 🎓 Best Practices

### 1. Establish Baselines Early

Run `measure_baseline.py` before production deployment to establish reference points.

### 2. Monitor Continuously

Check key metrics after every significant operation:
```python
summary = collector.get_agent_summary(agent_id)
if summary["success_rate"] < 0.9:
    alert_team(summary)
```

### 3. Use Utility Scores for Decisions

Don't optimize single metrics in isolation:
```python
# Bad: Only optimize for speed
if time < 100: deploy()

# Good: Optimize for overall utility
if utility_score > 0.85: deploy()
```

### 4. Set Alerts on Degradation

```python
result = collector.compare_to_baseline(metric, current)
if result.improvement_percent < -20:
    send_alert("Performance degraded 20%+")
```

### 5. Regular Reports

Generate weekly reports to track long-term trends:
```bash
# Cron: Every Monday at 9am
0 9 * * 1 python3 -m agi_core.measure_baseline
```

## 🚨 Troubleshooting

### High Token Usage

```python
# Check context stats
context = collector.get_context_summary(agent_id)
print(f"Reduce ops: {context['reduce_operations']}")

# If reduce_operations is low:
# → Apply REDUCE more frequently
cm.reduce_context(agent_id, strategy="aggressive")
```

### Low Success Rates

```python
# Check task type distribution
summary = collector.get_agent_summary(agent_id)
failed_tasks = summary["failed_tasks"]

# Review failed task metadata
failed = [m for m in collector.performance_metrics 
          if not m.success and m.agent_id == agent_id]
          
# Identify patterns in failures
```

### Performance Degradation

```python
# Compare to baseline
result = collector.compare_to_baseline("utility_score", current)

if result.improvement_percent < -10:
    # Roll back recent changes
    # Review delegation strategy
    # Check context window sizes
    pass
```

## 📚 API Reference

See `evaluation_metrics.py` for complete API documentation.

Key classes:
- `MetricsCollector` - Main metrics collection and analysis
- `PerformanceMetrics` - Individual metric data point
- `UtilityFunction` - Multi-objective optimization
- `OptimizationResult` - Baseline comparison result

---

**With comprehensive metrics, you can optimize your AGI systems based on data, not guesswork!** 📊

