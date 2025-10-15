"""
Evaluation Metrics for Self-Taught Optimizer (STOP) Integration

This module provides comprehensive metrics and utility functions for:
1. Measuring code generation quality
2. Tracking context efficiency
3. Monitoring agent performance
4. Evaluating optimization improvements
5. Providing utility functions for STOP

Metrics are designed to be:
- Objective and quantifiable
- Traceable to PRD requirements
- Useful for before/after comparisons
- Compatible with STOP utility functions
"""

import json
import time
import statistics
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
import hashlib

import logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics tracked"""
    CONTEXT_EFFICIENCY = "context_efficiency"
    AGENT_PERFORMANCE = "agent_performance"
    CODE_QUALITY = "code_quality"
    GOVERNANCE_EFFECTIVENESS = "governance_effectiveness"
    OPTIMIZATION_IMPROVEMENT = "optimization_improvement"


@dataclass
class PerformanceMetrics:
    """Core performance metrics for evaluation"""
    # Timing metrics
    execution_time_ms: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    
    # Context metrics
    tokens_used: int = 0
    context_utilization: float = 0.0  # 0-1
    context_efficiency_score: float = 0.0  # 0-1
    wasted_tokens: int = 0
    
    # Quality metrics
    success_rate: float = 0.0  # 0-1
    error_rate: float = 0.0  # 0-1
    test_coverage: float = 0.0  # 0-1
    code_quality_score: float = 0.0  # 0-1
    
    # Resource metrics
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    
    # Timestamp
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def utility_score(self) -> float:
        """
        Calculate overall utility score for STOP optimization
        
        This is the objective function that STOP will try to maximize.
        Weights are tuned based on PRD priorities.
        """
        # Weights based on PRD requirements
        weights = {
            "latency": 0.25,      # Rule #8: Performance budget < 50ms
            "context_efficiency": 0.25,  # Context engineering focus
            "success_rate": 0.20,  # Reliability
            "code_quality": 0.15,  # Rule #7: Test coverage
            "resource": 0.15       # Efficiency
        }
        
        # Normalize latency (target < 50ms, penalize above)
        latency_score = max(0, 1 - (self.latency_p95_ms / 50.0))
        
        # Context efficiency (already 0-1)
        context_score = self.context_efficiency_score
        
        # Success rate (already 0-1)
        success_score = self.success_rate
        
        # Code quality (already 0-1)
        quality_score = self.code_quality_score
        
        # Resource efficiency (normalize to 0-1, lower is better)
        resource_score = max(0, 1 - (self.cpu_percent / 100.0))
        
        # Weighted sum
        utility = (
            weights["latency"] * latency_score +
            weights["context_efficiency"] * context_score +
            weights["success_rate"] * success_score +
            weights["code_quality"] * quality_score +
            weights["resource"] * resource_score
        )
        
        return utility


@dataclass
class OptimizationResult:
    """Result of an optimization attempt"""
    optimization_id: str
    target_function: str
    strategy: str  # e.g., "beam_search", "genetic_algorithm", "simulated_annealing"
    
    # Before/After metrics
    baseline_metrics: PerformanceMetrics
    improved_metrics: PerformanceMetrics
    
    # Improvement deltas
    utility_improvement: float  # Percentage improvement
    latency_improvement_ms: float
    context_efficiency_improvement: float
    success_rate_improvement: float
    
    # Metadata
    iterations: int
    duration_seconds: float
    confidence_score: float  # 0-1, confidence in improvement
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["baseline_metrics"] = self.baseline_metrics.to_dict()
        data["improved_metrics"] = self.improved_metrics.to_dict()
        return data
    
    def is_significant_improvement(self, threshold: float = 0.05) -> bool:
        """Check if improvement is statistically significant"""
        return self.utility_improvement > threshold


class MetricsCollector:
    """
    Collects and aggregates metrics for STOP evaluation
    
    Features:
    - Real-time metric collection
    - Baseline establishment
    - Before/after comparison
    - Utility function calculation
    - Statistical analysis
    """
    
    def __init__(self, metrics_dir: Path = Path("./state/metrics")):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory metric stores
        self.context_metrics: List[Dict[str, Any]] = []
        self.agent_metrics: List[Dict[str, Any]] = []
        self.governance_metrics: List[Dict[str, Any]] = []
        self.optimization_results: List[OptimizationResult] = []
        
        # Baseline storage
        self.baselines: Dict[str, PerformanceMetrics] = {}
        
        # Time-series data
        self.time_series: Dict[str, List[float]] = defaultdict(list)
        
        logger.info(f"MetricsCollector initialized: {self.metrics_dir}")
    
    def record_context_metrics(
        self,
        agent_id: str,
        operation: str,
        metrics: Dict[str, Any]
    ):
        """Record context management metrics"""
        record = {
            "agent_id": agent_id,
            "operation": operation,
            "metrics": metrics,
            "timestamp": time.time()
        }
        
        self.context_metrics.append(record)
        
        # Update time series
        if "tokens_used" in metrics:
            self.time_series[f"{agent_id}_tokens"].append(metrics["tokens_used"])
        if "efficiency_score" in metrics:
            self.time_series[f"{agent_id}_efficiency"].append(metrics["efficiency_score"])
        
        # Persist to disk
        self._append_to_file("context_metrics.jsonl", record)
        
        logger.debug(f"Recorded context metrics: agent={agent_id}, op={operation}")
    
    def record_agent_metrics(
        self,
        agent_id: str,
        task_type: str,
        metrics: Dict[str, Any]
    ):
        """Record agent execution metrics"""
        record = {
            "agent_id": agent_id,
            "task_type": task_type,
            "metrics": metrics,
            "timestamp": time.time()
        }
        
        self.agent_metrics.append(record)
        
        # Update time series
        if "execution_time_ms" in metrics:
            self.time_series[f"{agent_id}_latency"].append(metrics["execution_time_ms"])
        if "success" in metrics:
            self.time_series[f"{agent_id}_success"].append(1 if metrics["success"] else 0)
        
        self._append_to_file("agent_metrics.jsonl", record)
        
        logger.debug(f"Recorded agent metrics: agent={agent_id}, task={task_type}")
    
    def record_governance_metrics(
        self,
        verdict: str,
        metrics: Dict[str, Any]
    ):
        """Record governance system metrics"""
        record = {
            "verdict": verdict,
            "metrics": metrics,
            "timestamp": time.time()
        }
        
        self.governance_metrics.append(record)
        
        # Update time series for governance
        if "ece_estimate" in metrics:
            self.time_series["governance_ece"].append(metrics["ece_estimate"])
        if "latency_p95_delta" in metrics:
            self.time_series["governance_latency_delta"].append(metrics["latency_p95_delta"])
        
        self._append_to_file("governance_metrics.jsonl", record)
        
        logger.debug(f"Recorded governance metrics: verdict={verdict}")
    
    def establish_baseline(
        self,
        target_function: str,
        metrics: PerformanceMetrics
    ):
        """Establish baseline metrics for a function"""
        self.baselines[target_function] = metrics
        
        baseline_record = {
            "target_function": target_function,
            "metrics": metrics.to_dict(),
            "timestamp": time.time()
        }
        
        # Save baseline to disk
        baseline_file = self.metrics_dir / f"baseline_{target_function}.json"
        with baseline_file.open("w") as f:
            json.dump(baseline_record, f, indent=2)
        
        logger.info(f"Established baseline for: {target_function}, utility={metrics.utility_score():.3f}")
    
    def load_baseline(self, target_function: str) -> Optional[PerformanceMetrics]:
        """Load baseline metrics for a function"""
        if target_function in self.baselines:
            return self.baselines[target_function]
        
        baseline_file = self.metrics_dir / f"baseline_{target_function}.json"
        if baseline_file.exists():
            with baseline_file.open("r") as f:
                data = json.load(f)
            metrics = PerformanceMetrics(**data["metrics"])
            self.baselines[target_function] = metrics
            return metrics
        
        return None
    
    def record_optimization(
        self,
        optimization_id: str,
        target_function: str,
        strategy: str,
        baseline_metrics: PerformanceMetrics,
        improved_metrics: PerformanceMetrics,
        iterations: int,
        duration_seconds: float,
        confidence_score: float
    ) -> OptimizationResult:
        """Record an optimization result"""
        
        # Calculate improvements
        baseline_utility = baseline_metrics.utility_score()
        improved_utility = improved_metrics.utility_score()
        
        utility_improvement = ((improved_utility - baseline_utility) / baseline_utility) * 100 if baseline_utility > 0 else 0
        latency_improvement = baseline_metrics.latency_p95_ms - improved_metrics.latency_p95_ms
        context_improvement = improved_metrics.context_efficiency_score - baseline_metrics.context_efficiency_score
        success_improvement = improved_metrics.success_rate - baseline_metrics.success_rate
        
        result = OptimizationResult(
            optimization_id=optimization_id,
            target_function=target_function,
            strategy=strategy,
            baseline_metrics=baseline_metrics,
            improved_metrics=improved_metrics,
            utility_improvement=utility_improvement,
            latency_improvement_ms=latency_improvement,
            context_efficiency_improvement=context_improvement,
            success_rate_improvement=success_improvement,
            iterations=iterations,
            duration_seconds=duration_seconds,
            confidence_score=confidence_score
        )
        
        self.optimization_results.append(result)
        
        # Save to disk
        result_file = self.metrics_dir / f"optimization_{optimization_id}.json"
        with result_file.open("w") as f:
            json.dump(result.to_dict(), f, indent=2)
        
        logger.info(
            f"Optimization recorded: {target_function}, "
            f"utility_improvement={utility_improvement:.2f}%, "
            f"latency_improvement={latency_improvement:.2f}ms, "
            f"confidence={confidence_score:.3f}"
        )
        
        return result
    
    def get_statistics(self, metric_key: str) -> Dict[str, float]:
        """Get statistical summary of a metric"""
        if metric_key not in self.time_series or not self.time_series[metric_key]:
            return {}
        
        values = self.time_series[metric_key]
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "p50": statistics.median(values),
            "p95": self._percentile(values, 0.95),
            "p99": self._percentile(values, 0.99)
        }
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _append_to_file(self, filename: str, record: Dict[str, Any]):
        """Append record to JSONL file"""
        file_path = self.metrics_dir / filename
        try:
            with file_path.open("a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to append to {filename}: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        report = {
            "generated_at": time.time(),
            "collection_period": {
                "start": min((m["timestamp"] for m in self.context_metrics), default=time.time()),
                "end": max((m["timestamp"] for m in self.context_metrics), default=time.time())
            },
            "context_metrics": {
                "total_records": len(self.context_metrics),
                "statistics": {
                    key: self.get_statistics(key)
                    for key in self.time_series.keys()
                    if "tokens" in key or "efficiency" in key
                }
            },
            "agent_metrics": {
                "total_records": len(self.agent_metrics),
                "statistics": {
                    key: self.get_statistics(key)
                    for key in self.time_series.keys()
                    if "latency" in key or "success" in key
                }
            },
            "governance_metrics": {
                "total_records": len(self.governance_metrics),
                "statistics": {
                    key: self.get_statistics(key)
                    for key in self.time_series.keys()
                    if "governance" in key
                }
            },
            "optimizations": {
                "total_optimizations": len(self.optimization_results),
                "successful_improvements": sum(
                    1 for r in self.optimization_results
                    if r.is_significant_improvement()
                ),
                "average_improvement": statistics.mean([
                    r.utility_improvement for r in self.optimization_results
                ]) if self.optimization_results else 0
            },
            "baselines": {
                name: {
                    "utility_score": metrics.utility_score(),
                    "latency_p95_ms": metrics.latency_p95_ms,
                    "context_efficiency": metrics.context_efficiency_score,
                    "success_rate": metrics.success_rate
                }
                for name, metrics in self.baselines.items()
            }
        }
        
        return report


class UtilityFunction:
    """
    Utility functions for STOP optimization
    
    These functions evaluate the "goodness" of code improvements
    and guide the optimization process.
    """
    
    @staticmethod
    def context_reduction_utility(
        original_tokens: int,
        reduced_tokens: int,
        information_loss: float  # 0-1, how much useful info was lost
    ) -> float:
        """
        Utility for context reduction strategies
        
        Maximizes token savings while minimizing information loss
        """
        if original_tokens == 0:
            return 0.0
        
        token_savings = (original_tokens - reduced_tokens) / original_tokens
        
        # Penalize information loss heavily
        utility = token_savings * (1 - information_loss)
        
        return max(0.0, utility)
    
    @staticmethod
    def agent_performance_utility(
        latency_ms: float,
        success_rate: float,
        context_efficiency: float,
        target_latency_ms: float = 50.0
    ) -> float:
        """
        Utility for agent performance optimization
        
        Balances speed, reliability, and efficiency
        """
        # Latency score (target < 50ms per PRD Rule #8)
        latency_score = max(0, 1 - (latency_ms / target_latency_ms))
        
        # Combined utility
        utility = (
            0.4 * latency_score +
            0.3 * success_rate +
            0.3 * context_efficiency
        )
        
        return utility
    
    @staticmethod
    def governance_utility(
        false_positive_rate: float,
        false_negative_rate: float,
        response_time_ms: float
    ) -> float:
        """
        Utility for governance policy optimization
        
        Minimizes both false positives and false negatives
        while maintaining fast response
        """
        # Penalize both types of errors
        accuracy = 1 - (false_positive_rate + false_negative_rate) / 2
        
        # Normalize response time (target < 50ms)
        speed_score = max(0, 1 - (response_time_ms / 50.0))
        
        utility = 0.7 * accuracy + 0.3 * speed_score
        
        return max(0.0, utility)
    
    @staticmethod
    def code_generation_utility(
        test_coverage: float,
        linter_errors: int,
        complexity_score: float,  # 0-1, lower is better
        execution_time_ms: float
    ) -> float:
        """
        Utility for code generation optimization
        
        Balances quality, maintainability, and performance
        """
        # Test coverage (target 85% per PRD Rule #7)
        coverage_score = min(1.0, test_coverage / 0.85)
        
        # Linter score (penalize errors)
        linter_score = max(0, 1 - (linter_errors / 10.0))
        
        # Complexity (lower is better)
        complexity_score_norm = 1 - complexity_score
        
        # Performance
        perf_score = max(0, 1 - (execution_time_ms / 50.0))
        
        utility = (
            0.3 * coverage_score +
            0.25 * linter_score +
            0.25 * complexity_score_norm +
            0.2 * perf_score
        )
        
        return utility


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def measure_execution(func: Callable) -> Callable:
    """
    Decorator to measure function execution and collect metrics
    
    Usage:
        @measure_execution
        def my_function(args):
            # function code
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = False
        result = None
        error = None
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            error = e
            logger.error(f"Function {func.__name__} failed: {e}")
            raise
        finally:
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            
            # Record metrics
            collector = get_metrics_collector()
            collector.record_agent_metrics(
                agent_id=func.__name__,
                task_type="function_execution",
                metrics={
                    "execution_time_ms": execution_time_ms,
                    "success": success,
                    "error": str(error) if error else None,
                    "timestamp": end_time
                }
            )
        
        return result
    
    return wrapper


# Export key components
__all__ = [
    "MetricType",
    "PerformanceMetrics",
    "OptimizationResult",
    "MetricsCollector",
    "UtilityFunction",
    "get_metrics_collector",
    "measure_execution"
]

