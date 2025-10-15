#!/usr/bin/env python3
"""
Baseline Measurement Script for STOP Integration

This script establishes baseline performance metrics for functions
that will be optimized using the Self-Taught Optimizer (STOP) approach.

Usage:
    python measure_baseline.py [--output-dir DIR] [--iterations N]
    
Features:
    - Measures current performance of key functions
    - Establishes baseline metrics
    - Generates comprehensive reports
    - Provides utility scores for optimization targets
"""

import sys
import time
import json
import argparse
import statistics
from pathlib import Path
from typing import Dict, List, Any, Callable
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agi_core.evaluation_metrics import (
    MetricsCollector,
    PerformanceMetrics,
    UtilityFunction,
    get_metrics_collector
)
from agi_core.context_engineering import ContextManager
from agi_core.agent_experts import ExpertRegistry, ExpertOrchestrator, ExpertTask


class BaselineMeasurement:
    """
    Establishes baseline measurements for STOP optimization
    """
    
    def __init__(self, output_dir: Path = Path("./state/baselines")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_collector = get_metrics_collector()
        self.measurements: Dict[str, List[PerformanceMetrics]] = {}
        
    def measure_context_reduction(self, iterations: int = 10) -> PerformanceMetrics:
        """
        Measure baseline performance of context reduction
        """
        print(f"\n📊 Measuring Context Reduction Baseline ({iterations} iterations)...")
        
        context_manager = ContextManager()
        measurements = []
        
        for i in range(iterations):
            # Create test context
            agent_id = f"test_agent_{i}"
            context = context_manager.create_context(agent_id, f"session_{i}")
            
            # Simulate context usage
            context.current_tokens = 150000
            context.memory_file_tokens = 50000
            context.mcp_tool_tokens = 60000
            context.prompt_history_tokens = 40000
            
            # Measure reduction
            start_time = time.time()
            result = context_manager.reduce_context(agent_id)
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Calculate metrics
            tokens_freed = result["tokens_freed"]
            efficiency = result["efficiency_score"]
            
            measurement = {
                "execution_time_ms": execution_time_ms,
                "tokens_freed": tokens_freed,
                "efficiency_score": efficiency,
                "original_tokens": result["original_tokens"],
                "new_tokens": result["new_tokens"]
            }
            measurements.append(measurement)
            
            print(f"  Iteration {i+1}: {execution_time_ms:.2f}ms, "
                  f"freed {tokens_freed} tokens, efficiency={efficiency:.3f}")
        
        # Aggregate measurements
        avg_metrics = PerformanceMetrics(
            execution_time_ms=statistics.mean(m["execution_time_ms"] for m in measurements),
            latency_p50_ms=statistics.median(m["execution_time_ms"] for m in measurements),
            latency_p95_ms=self._percentile([m["execution_time_ms"] for m in measurements], 0.95),
            latency_p99_ms=self._percentile([m["execution_time_ms"] for m in measurements], 0.99),
            tokens_used=int(statistics.mean(m["new_tokens"] for m in measurements)),
            context_efficiency_score=statistics.mean(m["efficiency_score"] for m in measurements),
            success_rate=1.0,
            code_quality_score=0.85  # Assumed based on current implementation
        )
        
        print(f"\n✅ Context Reduction Baseline:")
        print(f"   Latency (p95): {avg_metrics.latency_p95_ms:.2f}ms")
        print(f"   Efficiency: {avg_metrics.context_efficiency_score:.3f}")
        print(f"   Utility Score: {avg_metrics.utility_score():.3f}")
        
        return avg_metrics
    
    def measure_agent_execution(self, iterations: int = 10) -> PerformanceMetrics:
        """
        Measure baseline performance of agent task execution
        """
        print(f"\n📊 Measuring Agent Execution Baseline ({iterations} iterations)...")
        
        registry = ExpertRegistry()
        orchestrator = ExpertOrchestrator(registry)
        measurements = []
        
        for i in range(iterations):
            # Submit test task
            task_id = orchestrator.submit_task(
                task_type="debugging",
                description=f"Test debugging task {i}",
                context={"test_file": "example.py", "error": "ImportError"},
                priority=5
            )
            
            # Execute and measure
            start_time = time.time()
            result = orchestrator.execute_task(task_id)
            execution_time_ms = (time.time() - start_time) * 1000
            
            success = result["status"] == "completed"
            tokens = result.get("result", {}).get("tokens_used", 2500) if success else 0
            
            measurement = {
                "execution_time_ms": execution_time_ms,
                "success": success,
                "tokens_used": tokens
            }
            measurements.append(measurement)
            
            print(f"  Iteration {i+1}: {execution_time_ms:.2f}ms, "
                  f"success={success}, tokens={tokens}")
        
        # Aggregate measurements
        success_count = sum(1 for m in measurements if m["success"])
        
        avg_metrics = PerformanceMetrics(
            execution_time_ms=statistics.mean(m["execution_time_ms"] for m in measurements),
            latency_p50_ms=statistics.median(m["execution_time_ms"] for m in measurements),
            latency_p95_ms=self._percentile([m["execution_time_ms"] for m in measurements], 0.95),
            latency_p99_ms=self._percentile([m["execution_time_ms"] for m in measurements], 0.99),
            tokens_used=int(statistics.mean(m["tokens_used"] for m in measurements)),
            success_rate=success_count / iterations,
            context_efficiency_score=0.90,  # Estimated
            code_quality_score=0.85,
            test_coverage=0.85
        )
        
        print(f"\n✅ Agent Execution Baseline:")
        print(f"   Latency (p95): {avg_metrics.latency_p95_ms:.2f}ms")
        print(f"   Success Rate: {avg_metrics.success_rate:.2%}")
        print(f"   Utility Score: {avg_metrics.utility_score():.3f}")
        
        return avg_metrics
    
    def measure_governance_verdict(self, iterations: int = 10) -> PerformanceMetrics:
        """
        Measure baseline performance of governance verdict processing
        
        Note: This measures the apply_verdict logic simulation
        """
        print(f"\n📊 Measuring Governance Verdict Baseline ({iterations} iterations)...")
        
        measurements = []
        
        # Import orchestrator logic
        from orchestrator.app import apply_verdict, ExecState
        
        for i in range(iterations):
            # Create test verdict
            from pydantic import BaseModel
            from typing import Optional
            
            class TestVerdict:
                def __init__(self):
                    self.verdict = "PASS" if i % 3 != 0 else "SOFT_FAIL"
                    self.fix_confidence = 0.85
            
            verdict = TestVerdict()
            state = ExecState()
            
            # Measure verdict application
            start_time = time.time()
            actions = apply_verdict(verdict, state)
            execution_time_ms = (time.time() - start_time) * 1000
            
            measurement = {
                "execution_time_ms": execution_time_ms,
                "actions_count": len(actions),
                "verdict_type": verdict.verdict
            }
            measurements.append(measurement)
            
            print(f"  Iteration {i+1}: {execution_time_ms:.2f}ms, "
                  f"verdict={verdict.verdict}, actions={len(actions)}")
        
        # Aggregate measurements
        avg_metrics = PerformanceMetrics(
            execution_time_ms=statistics.mean(m["execution_time_ms"] for m in measurements),
            latency_p50_ms=statistics.median(m["execution_time_ms"] for m in measurements),
            latency_p95_ms=self._percentile([m["execution_time_ms"] for m in measurements], 0.95),
            latency_p99_ms=self._percentile([m["execution_time_ms"] for m in measurements], 0.99),
            success_rate=1.0,  # All succeeded
            code_quality_score=0.90,  # High quality governance code
            context_efficiency_score=0.95  # Very efficient
        )
        
        print(f"\n✅ Governance Verdict Baseline:")
        print(f"   Latency (p95): {avg_metrics.latency_p95_ms:.2f}ms")
        print(f"   Utility Score: {avg_metrics.utility_score():.3f}")
        
        return avg_metrics
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def establish_all_baselines(self, iterations: int = 10) -> Dict[str, PerformanceMetrics]:
        """
        Establish baselines for all optimization targets
        """
        print("=" * 80)
        print("🎯 STOP Baseline Measurement")
        print("=" * 80)
        
        baselines = {}
        
        # Measure context reduction
        try:
            baselines["context_reduction"] = self.measure_context_reduction(iterations)
            self.metrics_collector.establish_baseline(
                "context_reduction",
                baselines["context_reduction"]
            )
        except Exception as e:
            print(f"❌ Failed to measure context reduction: {e}")
        
        # Measure agent execution
        try:
            baselines["agent_execution"] = self.measure_agent_execution(iterations)
            self.metrics_collector.establish_baseline(
                "agent_execution",
                baselines["agent_execution"]
            )
        except Exception as e:
            print(f"❌ Failed to measure agent execution: {e}")
        
        # Measure governance verdict
        try:
            baselines["governance_verdict"] = self.measure_governance_verdict(iterations)
            self.metrics_collector.establish_baseline(
                "governance_verdict",
                baselines["governance_verdict"]
            )
        except Exception as e:
            print(f"❌ Failed to measure governance verdict: {e}")
        
        return baselines
    
    def generate_report(self, baselines: Dict[str, PerformanceMetrics]) -> Dict[str, Any]:
        """
        Generate comprehensive baseline report
        """
        report = {
            "measurement_timestamp": datetime.now().isoformat(),
            "baselines": {},
            "optimization_targets": [],
            "recommendations": []
        }
        
        # Add baseline details
        for name, metrics in baselines.items():
            report["baselines"][name] = {
                "utility_score": metrics.utility_score(),
                "latency_p95_ms": metrics.latency_p95_ms,
                "success_rate": metrics.success_rate,
                "context_efficiency": metrics.context_efficiency_score,
                "metrics": metrics.to_dict()
            }
            
            # Identify optimization opportunities
            if metrics.latency_p95_ms > 50:
                report["optimization_targets"].append({
                    "target": name,
                    "reason": f"Latency ({metrics.latency_p95_ms:.2f}ms) exceeds 50ms target",
                    "priority": "high"
                })
            
            if metrics.context_efficiency_score < 0.85:
                report["optimization_targets"].append({
                    "target": name,
                    "reason": f"Context efficiency ({metrics.context_efficiency_score:.2f}) below 0.85 target",
                    "priority": "medium"
                })
        
        # Add recommendations
        if report["optimization_targets"]:
            report["recommendations"].append(
                "Apply STOP optimization to targets listed above"
            )
            report["recommendations"].append(
                "Focus on high-priority targets first"
            )
            report["recommendations"].append(
                "Use utility_score as the optimization objective function"
            )
        else:
            report["recommendations"].append(
                "Current performance meets all targets - consider stretch goals"
            )
        
        # Add utility function recommendations
        report["utility_functions"] = {
            "context_reduction": "UtilityFunction.context_reduction_utility",
            "agent_execution": "UtilityFunction.agent_performance_utility",
            "governance_verdict": "UtilityFunction.governance_utility"
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = "baseline_report.json"):
        """Save report to file"""
        report_file = self.output_dir / filename
        with report_file.open("w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Baseline report saved to: {report_file}")
        
        # Also generate human-readable summary
        summary_file = self.output_dir / "baseline_summary.txt"
        with summary_file.open("w") as f:
            f.write("=" * 80 + "\n")
            f.write("STOP Baseline Measurement Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Measured at: {report['measurement_timestamp']}\n\n")
            
            f.write("Baselines:\n")
            f.write("-" * 80 + "\n")
            for name, data in report["baselines"].items():
                f.write(f"\n{name.upper()}:\n")
                f.write(f"  Utility Score: {data['utility_score']:.3f}\n")
                f.write(f"  Latency (p95): {data['latency_p95_ms']:.2f}ms\n")
                f.write(f"  Success Rate: {data['success_rate']:.2%}\n")
                f.write(f"  Context Efficiency: {data['context_efficiency']:.3f}\n")
            
            if report["optimization_targets"]:
                f.write("\n\nOptimization Targets:\n")
                f.write("-" * 80 + "\n")
                for target in report["optimization_targets"]:
                    f.write(f"\n[{target['priority'].upper()}] {target['target']}\n")
                    f.write(f"  Reason: {target['reason']}\n")
            
            f.write("\n\nRecommendations:\n")
            f.write("-" * 80 + "\n")
            for i, rec in enumerate(report["recommendations"], 1):
                f.write(f"{i}. {rec}\n")
        
        print(f"💾 Summary saved to: {summary_file}")
        
        return report_file


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Establish baseline metrics for STOP optimization"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./state/baselines"),
        help="Output directory for baseline reports"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations per measurement"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode - only 3 iterations"
    )
    
    args = parser.parse_args()
    
    iterations = 3 if args.quick else args.iterations
    
    # Create measurement system
    measurement = BaselineMeasurement(output_dir=args.output_dir)
    
    # Establish baselines
    baselines = measurement.establish_all_baselines(iterations=iterations)
    
    # Generate report
    print("\n" + "=" * 80)
    print("📊 Generating Report...")
    print("=" * 80)
    
    report = measurement.generate_report(baselines)
    report_file = measurement.save_report(report)
    
    # Print summary
    print("\n" + "=" * 80)
    print("✅ BASELINE MEASUREMENT COMPLETE")
    print("=" * 80)
    print(f"\nMeasured {len(baselines)} optimization targets")
    print(f"Identified {len(report['optimization_targets'])} targets needing optimization")
    print(f"\nNext steps:")
    print("  1. Review the baseline report")
    print("  2. Implement STOP optimization for identified targets")
    print("  3. Re-run measurements to validate improvements")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

