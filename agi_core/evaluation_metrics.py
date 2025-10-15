"""
Evaluation Metrics - Measure AGI System Performance

Tracks and analyzes:
- Context efficiency
- Agent performance
- Workflow success rates
- Token usage optimization
- Time-to-completion
- Resource utilization

Enables data-driven optimization of AGI systems.
"""

import time
import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime, timedelta
import statistics

import logging
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for AGI operations"""
    timestamp: float
    operation: str
    agent_id: str
    execution_time_ms: float
    success: bool
    tokens_used: int = 0
    context_efficiency: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationResult:
    """Result of optimization analysis"""
    metric_name: str
    baseline_value: float
    current_value: float
    improvement_percent: float
    recommendation: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    

class UtilityFunction:
    """
    Multi-objective utility function for AGI optimization
    
    Balances:
    - Speed (execution time)
    - Quality (success rate)
    - Efficiency (context usage)
    - Cost (token consumption)
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None
    ):
        # Default weights (must sum to 1.0)
        self.weights = weights or {
            "speed": 0.3,        # Fast execution
            "quality": 0.4,      # High success rate
            "efficiency": 0.2,   # Good context efficiency
            "cost": 0.1          # Low token usage
        }
        
        # Validate weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")
    
    def calculate(
        self,
        speed_score: float,      # 0-1, higher is better
        quality_score: float,    # 0-1, higher is better
        efficiency_score: float, # 0-1, higher is better
        cost_score: float        # 0-1, higher is better (inverse of cost)
    ) -> float:
        """Calculate overall utility score (0-1)"""
        utility = (
            self.weights["speed"] * speed_score +
            self.weights["quality"] * quality_score +
            self.weights["efficiency"] * efficiency_score +
            self.weights["cost"] * cost_score
        )
        return utility
    
    def normalize_speed(self, execution_time_ms: float, target_time_ms: float = 1000) -> float:
        """Normalize speed (lower time is better)"""
        return max(0.0, min(1.0, target_time_ms / max(execution_time_ms, 1)))
    
    def normalize_cost(self, tokens_used: int, target_tokens: int = 10000) -> float:
        """Normalize cost (lower tokens is better)"""
        return max(0.0, min(1.0, target_tokens / max(tokens_used, 1)))


class MetricsCollector:
    """
    Centralized metrics collection and analysis for AGI systems
    """
    
    def __init__(self, metrics_dir: Path = Path("./state/metrics")):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory metrics (last 10k)
        self.performance_metrics: List[PerformanceMetrics] = []
        self.max_memory_metrics = 10000
        
        # Aggregated statistics
        self.agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time_ms": 0.0,
            "total_tokens": 0,
            "context_efficiency_sum": 0.0
        })
        
        self.context_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "reduce_count": 0,
            "delegate_count": 0,
            "prime_count": 0,
            "total_tokens_freed": 0,
            "efficiency_scores": []
        })
        
        # Baseline metrics for comparison
        self.baselines: Dict[str, float] = {}
        
        # Utility function
        self.utility = UtilityFunction()
        
        logger.info(f"MetricsCollector initialized: {self.metrics_dir}")
    
    def record_agent_metrics(
        self,
        agent_id: str,
        task_type: str,
        metrics: Dict[str, Any]
    ):
        """Record agent performance metrics"""
        perf = PerformanceMetrics(
            timestamp=time.time(),
            operation=f"agent.{task_type}",
            agent_id=agent_id,
            execution_time_ms=metrics.get("execution_time_ms", 0.0),
            success=metrics.get("success", False),
            tokens_used=metrics.get("tokens_used", 0),
            context_efficiency=metrics.get("context_efficiency", 0.0),
            metadata=metrics
        )
        
        self._store_metric(perf)
        
        # Update agent stats
        stats = self.agent_stats[agent_id]
        stats["total_tasks"] += 1
        if perf.success:
            stats["successful_tasks"] += 1
        else:
            stats["failed_tasks"] += 1
        stats["total_execution_time_ms"] += perf.execution_time_ms
        stats["total_tokens"] += perf.tokens_used
        if perf.context_efficiency > 0:
            stats["context_efficiency_sum"] += perf.context_efficiency
        
        logger.debug(f"Recorded agent metrics: {agent_id}, task={task_type}, success={perf.success}")
    
    def record_context_metrics(
        self,
        agent_id: str,
        operation: str,
        metrics: Dict[str, Any]
    ):
        """Record context engineering metrics"""
        perf = PerformanceMetrics(
            timestamp=time.time(),
            operation=f"context.{operation}",
            agent_id=agent_id,
            execution_time_ms=0.0,  # Context ops are fast
            success=True,
            tokens_used=metrics.get("tokens_freed", 0),
            context_efficiency=metrics.get("efficiency_score", 0.0),
            metadata=metrics
        )
        
        self._store_metric(perf)
        
        # Update context stats
        stats = self.context_stats[agent_id]
        if operation == "reduce_context":
            stats["reduce_count"] += 1
            stats["total_tokens_freed"] += metrics.get("tokens_freed", 0)
            if "efficiency_score" in metrics:
                stats["efficiency_scores"].append(metrics["efficiency_score"])
        elif operation == "delegate_to_agent":
            stats["delegate_count"] += 1
        elif operation == "prime_context":
            stats["prime_count"] += 1
        
        logger.debug(f"Recorded context metrics: {agent_id}, op={operation}")
    
    def _store_metric(self, metric: PerformanceMetrics):
        """Store metric in memory and disk"""
        # Add to memory
        self.performance_metrics.append(metric)
        
        # Trim if too many
        if len(self.performance_metrics) > self.max_memory_metrics:
            self.performance_metrics = self.performance_metrics[-self.max_memory_metrics:]
        
        # Append to disk
        date_str = datetime.fromtimestamp(metric.timestamp).strftime("%Y-%m-%d")
        metrics_file = self.metrics_dir / f"metrics_{date_str}.jsonl"
        
        with metrics_file.open("a") as f:
            f.write(json.dumps(metric.to_dict()) + "\n")
    
    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get summary statistics for an agent"""
        stats = self.agent_stats.get(agent_id)
        if not stats or stats["total_tasks"] == 0:
            return {"error": f"No metrics for agent {agent_id}"}
        
        success_rate = stats["successful_tasks"] / stats["total_tasks"]
        avg_time = stats["total_execution_time_ms"] / stats["total_tasks"]
        avg_tokens = stats["total_tokens"] / stats["total_tasks"]
        
        tasks_with_efficiency = stats["successful_tasks"]
        avg_efficiency = (
            stats["context_efficiency_sum"] / tasks_with_efficiency
            if tasks_with_efficiency > 0 else 0.0
        )
        
        return {
            "agent_id": agent_id,
            "total_tasks": stats["total_tasks"],
            "success_rate": success_rate,
            "failed_tasks": stats["failed_tasks"],
            "avg_execution_time_ms": avg_time,
            "avg_tokens_per_task": avg_tokens,
            "avg_context_efficiency": avg_efficiency,
            "total_tokens": stats["total_tokens"]
        }
    
    def get_context_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get context engineering summary for an agent"""
        stats = self.context_stats.get(agent_id)
        if not stats:
            return {"error": f"No context metrics for agent {agent_id}"}
        
        avg_efficiency = (
            statistics.mean(stats["efficiency_scores"])
            if stats["efficiency_scores"] else 0.0
        )
        
        return {
            "agent_id": agent_id,
            "reduce_operations": stats["reduce_count"],
            "delegate_operations": stats["delegate_count"],
            "prime_operations": stats["prime_count"],
            "total_tokens_freed": stats["total_tokens_freed"],
            "avg_efficiency_score": avg_efficiency,
            "total_context_operations": (
                stats["reduce_count"] + 
                stats["delegate_count"] + 
                stats["prime_count"]
            )
        }
    
    def calculate_utility_score(
        self,
        agent_id: str,
        target_time_ms: float = 1000,
        target_tokens: int = 10000
    ) -> Optional[float]:
        """Calculate multi-objective utility score for an agent"""
        summary = self.get_agent_summary(agent_id)
        if "error" in summary:
            return None
        
        # Calculate component scores
        speed_score = self.utility.normalize_speed(
            summary["avg_execution_time_ms"],
            target_time_ms
        )
        
        quality_score = summary["success_rate"]
        
        efficiency_score = summary["avg_context_efficiency"]
        
        cost_score = self.utility.normalize_cost(
            int(summary["avg_tokens_per_task"]),
            target_tokens
        )
        
        # Calculate overall utility
        utility = self.utility.calculate(
            speed_score=speed_score,
            quality_score=quality_score,
            efficiency_score=efficiency_score,
            cost_score=cost_score
        )
        
        return utility
    
    def set_baseline(self, metric_name: str, value: float):
        """Set a baseline value for comparison"""
        self.baselines[metric_name] = value
        logger.info(f"Set baseline: {metric_name} = {value}")
    
    def compare_to_baseline(
        self,
        metric_name: str,
        current_value: float
    ) -> Optional[OptimizationResult]:
        """Compare current value to baseline"""
        if metric_name not in self.baselines:
            logger.warning(f"No baseline for {metric_name}")
            return None
        
        baseline = self.baselines[metric_name]
        improvement = ((current_value - baseline) / baseline) * 100
        
        # Generate recommendation
        if improvement > 10:
            recommendation = "Excellent improvement! Current approach is working well."
        elif improvement > 0:
            recommendation = "Slight improvement. Continue monitoring."
        elif improvement > -10:
            recommendation = "Performance is similar to baseline."
        else:
            recommendation = "Performance degradation detected. Investigate and optimize."
        
        return OptimizationResult(
            metric_name=metric_name,
            baseline_value=baseline,
            current_value=current_value,
            improvement_percent=improvement,
            recommendation=recommendation,
            timestamp=time.time()
        )
    
    def get_top_performers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing agents by utility score"""
        agent_scores = []
        
        for agent_id in self.agent_stats.keys():
            utility = self.calculate_utility_score(agent_id)
            if utility is not None:
                summary = self.get_agent_summary(agent_id)
                agent_scores.append({
                    "agent_id": agent_id,
                    "utility_score": utility,
                    "success_rate": summary["success_rate"],
                    "avg_time_ms": summary["avg_execution_time_ms"],
                    "total_tasks": summary["total_tasks"]
                })
        
        # Sort by utility score
        agent_scores.sort(key=lambda x: x["utility_score"], reverse=True)
        
        return agent_scores[:limit]
    
    def generate_report(self, output_file: Optional[Path] = None) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        report = {
            "generated_at": time.time(),
            "total_metrics": len(self.performance_metrics),
            "total_agents": len(self.agent_stats),
            "agent_summaries": {},
            "context_summaries": {},
            "top_performers": self.get_top_performers(),
            "recommendations": []
        }
        
        # Agent summaries
        for agent_id in self.agent_stats.keys():
            report["agent_summaries"][agent_id] = self.get_agent_summary(agent_id)
        
        # Context summaries
        for agent_id in self.context_stats.keys():
            report["context_summaries"][agent_id] = self.get_context_summary(agent_id)
        
        # Recommendations
        for agent_id in self.agent_stats.keys():
            summary = self.get_agent_summary(agent_id)
            if "error" not in summary:
                if summary["success_rate"] < 0.8:
                    report["recommendations"].append({
                        "agent_id": agent_id,
                        "issue": "Low success rate",
                        "recommendation": "Review agent configuration and task types"
                    })
                
                if summary["avg_context_efficiency"] < 0.7:
                    report["recommendations"].append({
                        "agent_id": agent_id,
                        "issue": "Low context efficiency",
                        "recommendation": "Apply REDUCE strategy more aggressively"
                    })
        
        # Save to file if specified
        if output_file:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")
        
        return report
    
    def export_metrics(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        output_file: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """Export metrics for analysis"""
        filtered_metrics = [
            m for m in self.performance_metrics
            if (start_time is None or m.timestamp >= start_time) and
               (end_time is None or m.timestamp <= end_time)
        ]
        
        exported = [m.to_dict() for m in filtered_metrics]
        
        if output_file:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w") as f:
                json.dump(exported, f, indent=2)
            logger.info(f"Exported {len(exported)} metrics to {output_file}")
        
        return exported


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def measure_execution(operation_name: str):
    """
    Decorator to measure execution time and record metrics
    
    Usage:
        @measure_execution("my_operation")
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            result = None
            error = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                collector = get_metrics_collector()
                collector.record_agent_metrics(
                    agent_id=f"function.{func.__name__}",
                    task_type=operation_name,
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "success": success,
                        "error": error,
                        "function_name": func.__name__
                    }
                )
        
        return wrapper
    
    return decorator
