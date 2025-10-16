"""
DGM Metrics Collection
Prometheus metrics for Darwin Gödel Machine evolution monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary
import logging

logger = logging.getLogger(__name__)

# Generation Metrics
dgm_generations_total = Counter(
    'dgm_generations_total',
    'Total number of DGM evolution generations'
)

dgm_verdicts_total = Counter(
    'dgm_verdicts_total',
    'Total verdicts by type',
    ['verdict_type']  # APPROVE, REJECT, CANARY_DEPLOY, etc.
)

# Performance Metrics
dgm_agent_performance = Gauge(
    'dgm_agent_performance',
    'Current best agent performance on benchmarks',
    ['benchmark']
)

dgm_performance_improvement = Histogram(
    'dgm_performance_improvement',
    'Performance delta per generation',
    buckets=[-0.1, -0.05, 0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
)

# Safety Metrics
dgm_safety_violations_total = Counter(
    'dgm_safety_violations_total',
    'Safety violations detected',
    ['violation_type']
)

dgm_ece_estimate = Histogram(
    'dgm_ece_estimate',
    'Epistemic Confidence Estimates',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Archive Metrics
dgm_archive_size = Gauge(
    'dgm_archive_size',
    'Total agents in archive'
)

dgm_archive_diversity = Gauge(
    'dgm_archive_diversity',
    'Archive diversity score (0-1)'
)

# Circuit Breaker
dgm_consecutive_failures = Gauge(
    'dgm_consecutive_failures',
    'Consecutive evolution failures'
)

# Timing
dgm_generation_duration = Summary(
    'dgm_generation_duration_seconds',
    'Time to complete one generation'
)

dgm_benchmark_duration = Summary(
    'dgm_benchmark_duration_seconds',
    'Time to run benchmarks',
    ['benchmark']
)

# Auto-Remediation Metrics
governance_remediations_requested_total = Counter(
    'governance_remediations_requested_total',
    'Total remediation requests triggered'
)

governance_remediations_started_total = Counter(
    'governance_remediations_started_total',
    'Total remediations started'
)

governance_remediations_completed_total = Counter(
    'governance_remediations_completed_total',
    'Total remediations completed',
    ['decision']  # PROMOTE, ROLLBACK, HOLD
)

governance_remediations_promoted_total = Counter(
    'governance_remediations_promoted_total',
    'Total remediations successfully promoted'
)

governance_remediations_rolled_back_total = Counter(
    'governance_remediations_rolled_back_total',
    'Total remediations rolled back'
)

governance_remediations_failed_total = Counter(
    'governance_remediations_failed_total',
    'Total remediation failures'
)

governance_remediation_duration = Summary(
    'governance_remediation_duration_seconds',
    'Time to complete remediation cycle'
)


class DGMMetricsCollector:
    """Collects and exports DGM metrics to Prometheus."""
    
    @staticmethod
    def record_generation():
        """Increment generation counter."""
        dgm_generations_total.inc()
    
    @staticmethod
    def record_verdict(verdict_type: str):
        """Record a verdict by type."""
        dgm_verdicts_total.labels(verdict_type=verdict_type).inc()
    
    @staticmethod
    def update_performance(benchmark: str, performance: float):
        """Update current performance gauge."""
        dgm_agent_performance.labels(benchmark=benchmark).set(performance)
    
    @staticmethod
    def record_improvement(delta: float):
        """Record performance improvement/regression."""
        dgm_performance_improvement.observe(delta)
    
    @staticmethod
    def record_safety_violation(violation_type: str):
        """Record safety violation."""
        dgm_safety_violations_total.labels(violation_type=violation_type).inc()
    
    @staticmethod
    def record_ece(ece: float):
        """Record ECE estimate."""
        dgm_ece_estimate.observe(ece)
    
    @staticmethod
    def update_archive_size(size: int):
        """Update archive size."""
        dgm_archive_size.set(size)
    
    @staticmethod
    def update_archive_diversity(diversity: float):
        """Update archive diversity score."""
        dgm_archive_diversity.set(diversity)
    
    @staticmethod
    def update_failures(count: int):
        """Update consecutive failures gauge."""
        dgm_consecutive_failures.set(count)
    
    @staticmethod
    def time_generation(duration: float):
        """Record generation duration."""
        dgm_generation_duration.observe(duration)
    
    @staticmethod
    def time_benchmark(benchmark: str, duration: float):
        """Record benchmark duration."""
        dgm_benchmark_duration.labels(benchmark=benchmark).observe(duration)
    
    @staticmethod
    def record_remediation_requested():
        """Record remediation request."""
        governance_remediations_requested_total.inc()
    
    @staticmethod
    def record_remediation_started():
        """Record remediation start."""
        governance_remediations_started_total.inc()
    
    @staticmethod
    def record_remediation_completed(decision: str):
        """Record remediation completion with decision."""
        governance_remediations_completed_total.labels(decision=decision).inc()
        if decision == "PROMOTE":
            governance_remediations_promoted_total.inc()
        elif decision == "ROLLBACK":
            governance_remediations_rolled_back_total.inc()
    
    @staticmethod
    def record_remediation_failed():
        """Record remediation failure."""
        governance_remediations_failed_total.inc()
    
    @staticmethod
    def time_remediation(duration: float):
        """Record remediation duration."""
        governance_remediation_duration.observe(duration)


# Example Grafana dashboard query snippets
GRAFANA_QUERIES = {
    "approval_rate": """
        rate(dgm_verdicts_total{verdict_type=~"APPROVE|CANARY_DEPLOY"}[5m])
        /
        rate(dgm_verdicts_total[5m])
    """,
    
    "performance_trend": """
        dgm_agent_performance{benchmark="swe-bench-lite"}
    """,
    
    "safety_violations_rate": """
        rate(dgm_safety_violations_total[1h])
    """,
    
    "evolution_efficiency": """
        dgm_verdicts_total{verdict_type="APPROVE"}
        /
        dgm_generations_total
    """,
    
    "archive_health": """
        dgm_archive_diversity
    """,
    
    "remediation_success_rate": """
        rate(governance_remediations_promoted_total[1h])
        /
        rate(governance_remediations_completed_total[1h])
    """,
    
    "remediation_volume": """
        rate(governance_remediations_requested_total[5m])
    """,
    
    "remediation_decision_breakdown": """
        sum(rate(governance_remediations_completed_total[1h])) by (decision)
    """
}


if __name__ == "__main__":
    # Example usage
    collector = DGMMetricsCollector()
    
    collector.record_generation()
    collector.record_verdict("APPROVE")
    collector.update_performance("swe-bench-lite", 0.35)
    collector.record_improvement(0.05)
    collector.record_ece(0.85)
    
    print("✓ DGM metrics recorded")

