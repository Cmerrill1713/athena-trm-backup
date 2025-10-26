"""
TRM Adaptive Policy Metrics - Prometheus Integration
Exports policy performance metrics for monitoring and alerting.
"""
from prometheus_client import Counter, Gauge, Histogram

# Policy predictions
trm_policy_predictions_total = Counter(
    "trm_policy_predictions_total",
    "TRM policy predictions by type",
    ["kind"]  # trigger|cycles|budget
)

# Policy accuracy (rolling window)
trm_policy_accuracy = Gauge(
    "trm_policy_accuracy",
    "Rolling policy trigger accuracy (TP+TN)/(TP+TN+FP+FN)"
)

# Context efficiency
trm_context_waste_ratio = Gauge(
    "trm_context_waste_ratio",
    "Recent context waste ratio by mode",
    ["mode"]
)

# Value metrics
trm_value_score = Gauge(
    "trm_value_score",
    "TRM value score: improvement/overhead ratio"
)

trm_improvement_ratio = Gauge(
    "trm_improvement_ratio",
    "Success rate improvement: with_trm / without_trm"
)

trm_latency_overhead_ms = Histogram(
    "trm_latency_overhead_ms",
    "Latency overhead when TRM is invoked",
    buckets=[10, 25, 50, 100, 200, 500, 1000, 2000]
)

# Cycle allocation metrics
trm_adaptive_cycles = Histogram(
    "trm_adaptive_cycles",
    "Cycles allocated by adaptive policy",
    ["mode"],
    buckets=[3, 6, 8, 12, 16, 18, 24]
)

# Trigger outcomes
trm_trigger_outcome_total = Counter(
    "trm_trigger_outcome_total",
    "TRM trigger outcomes for accuracy tracking",
    ["outcome"]  # tp, fp, tn, fn
)

def update_policy_metrics(policy):
    """
    Periodically update Prometheus metrics from policy state.
    Call this from a background thread or metrics tick loop.
    """
    stats = policy.get_stats()
    
    if stats.get("status") == "no_data":
        return
    
    # Update accuracy gauge
    with_trm = stats.get("success_rate_with_trm", 0.0)
    without_trm = stats.get("success_rate_without_trm", 0.0)
    
    if with_trm > 0 or without_trm > 0:
        # Simplified accuracy: how often does TRM improve outcomes
        improvement = max(0, with_trm - without_trm)
        trm_policy_accuracy.set(with_trm)
        trm_improvement_ratio.set(with_trm / without_trm if without_trm > 0 else 1.0)
    
    # Value score: improvement per unit latency
    # (this would need latency data from stats)
    avg_overhead_ms = 150.0  # placeholder
    if avg_overhead_ms > 0:
        value = (with_trm - without_trm) / (avg_overhead_ms / 1000.0)
        trm_value_score.set(value)

