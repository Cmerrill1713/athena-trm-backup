#!/usr/bin/env python3
"""
Baseline Measurement Tool

Measures baseline performance of AGI system for comparison and optimization.

Usage:
    python -m agi_core.measure_baseline
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agi_core.evaluation_metrics import (
    MetricsCollector,
    UtilityFunction,
    measure_execution
)
from agi_core.context_engineering import ContextManager
from agi_core.agent_experts import ExpertRegistry, ExpertOrchestrator
from agi_core.workflows import ScoutPlanBuild
from agi_core.delegation import AgentDelegator, DelegationStrategy


def measure_context_operations():
    """Measure baseline context engineering performance"""
    print("=" * 70)
    print("Measuring Context Operations Baseline")
    print("=" * 70)
    
    cm = ContextManager()
    
    # Test 1: Context creation
    start = time.time()
    context = cm.create_context("baseline_agent", "baseline_session")
    creation_time = (time.time() - start) * 1000
    print(f"✓ Context creation: {creation_time:.2f}ms")
    
    # Test 2: Context reduction
    context.current_tokens = 150000
    context.memory_file_tokens = 25000
    context.mcp_tool_tokens = 30000
    context.prompt_history_tokens = 95000
    
    start = time.time()
    result = cm.reduce_context("baseline_agent")
    reduction_time = (time.time() - start) * 1000
    print(f"✓ Context reduction: {reduction_time:.2f}ms")
    print(f"  - Tokens freed: {result['tokens_freed']:,}")
    print(f"  - Efficiency: {result.get('efficiency_score', 0):.2%}")
    
    # Test 3: Delegation
    start = time.time()
    delegation = cm.delegate_to_agent(
        "baseline_agent",
        {"type": "test", "description": "Baseline test"},
        "test_expert"
    )
    delegation_time = (time.time() - start) * 1000
    print(f"✓ Delegation: {delegation_time:.2f}ms")
    
    # Test 4: Context priming
    start = time.time()
    primed = cm.prime_context(
        "baseline_agent",
        "testing",
        {"test_data": "baseline measurement"}
    )
    priming_time = (time.time() - start) * 1000
    print(f"✓ Context priming: {priming_time:.2f}ms\n")
    
    return {
        "creation_time_ms": creation_time,
        "reduction_time_ms": reduction_time,
        "delegation_time_ms": delegation_time,
        "priming_time_ms": priming_time
    }


def measure_expert_operations():
    """Measure baseline expert agent performance"""
    print("=" * 70)
    print("Measuring Expert Operations Baseline")
    print("=" * 70)
    
    registry = ExpertRegistry()
    orchestrator = ExpertOrchestrator(registry)
    
    # Test task submission and execution
    test_cases = [
        ("debugging", "Debug test issue"),
        ("refactoring", "Refactor test code"),
        ("testing", "Write unit tests"),
    ]
    
    results = []
    
    for task_type, description in test_cases:
        # Submit task
        start = time.time()
        task_id = orchestrator.submit_task(
            task_type=task_type,
            description=description,
            context={"test": True},
            priority=5
        )
        submission_time = (time.time() - start) * 1000
        
        # Execute task
        start = time.time()
        result = orchestrator.execute_task(task_id)
        execution_time = (time.time() - start) * 1000
        
        print(f"✓ {task_type}: {execution_time:.2f}ms")
        
        results.append({
            "task_type": task_type,
            "submission_time_ms": submission_time,
            "execution_time_ms": execution_time,
            "success": result.get("status") != "failed"
        })
    
    avg_time = sum(r["execution_time_ms"] for r in results) / len(results)
    print(f"\n  Average execution time: {avg_time:.2f}ms\n")
    
    return results


def measure_workflow_operations():
    """Measure baseline workflow performance"""
    print("=" * 70)
    print("Measuring Workflow Operations Baseline")
    print("=" * 70)
    
    # Scout-Plan-Build workflow
    workflow = ScoutPlanBuild(
        workflow_id="baseline_spb",
        task_description="Baseline measurement task",
        codebase_path=Path("./"),
        constraints={}
    )
    
    start = time.time()
    result = workflow.execute()
    total_time = (time.time() - start) * 1000
    
    print(f"✓ Scout-Plan-Build workflow: {total_time:.2f}ms")
    print(f"  - Phases: {result.get('phases_completed', 0)}")
    
    phases = result.get('results', [])
    for phase_result in phases:
        phase = phase_result.get('phase', 'unknown')
        duration = phase_result.get('duration_seconds', 0) * 1000
        tokens = phase_result.get('tokens_used', 0)
        print(f"    • {phase}: {duration:.2f}ms, {tokens:,} tokens")
    
    print()
    
    return {
        "total_time_ms": total_time,
        "phases": len(phases),
        "total_tokens": sum(p.get('tokens_used', 0) for p in phases)
    }


def measure_delegation_operations():
    """Measure baseline delegation performance"""
    print("=" * 70)
    print("Measuring Delegation Operations Baseline")
    print("=" * 70)
    
    delegator = AgentDelegator(max_parallel_agents=3)
    
    # Test background delegation
    tasks = [
        ("refactor", "Refactor module A"),
        ("test", "Test module B"),
        ("document", "Document module C"),
    ]
    
    start = time.time()
    agent_ids = []
    for agent_type, description in tasks:
        agent_id = delegator.delegate_task(
            agent_type=agent_type,
            description=description,
            context={},
            strategy=DelegationStrategy.BACKGROUND,
            priority=5
        )
        agent_ids.append(agent_id)
    delegation_time = (time.time() - start) * 1000
    
    print(f"✓ Delegated {len(tasks)} tasks: {delegation_time:.2f}ms")
    print(f"  - Average per task: {delegation_time/len(tasks):.2f}ms")
    
    # Wait a bit for tasks to "complete"
    time.sleep(0.5)
    
    # Check status
    active = delegator.list_active_agents()
    print(f"  - Active agents: {len(active)}\n")
    
    return {
        "delegation_time_ms": delegation_time,
        "tasks_delegated": len(tasks),
        "avg_per_task_ms": delegation_time / len(tasks)
    }


def generate_baseline_report(metrics_collector: MetricsCollector):
    """Generate baseline performance report"""
    print("=" * 70)
    print("Baseline Performance Summary")
    print("=" * 70)
    
    # Get all agent summaries
    all_agents = list(metrics_collector.agent_stats.keys())
    
    if all_agents:
        print("\nAgent Performance:")
        for agent_id in all_agents[:5]:  # Top 5
            summary = metrics_collector.get_agent_summary(agent_id)
            if "error" not in summary:
                utility = metrics_collector.calculate_utility_score(agent_id)
                print(f"  {agent_id}:")
                print(f"    Tasks: {summary['total_tasks']}")
                print(f"    Success rate: {summary['success_rate']:.1%}")
                print(f"    Avg time: {summary['avg_execution_time_ms']:.2f}ms")
                print(f"    Utility score: {utility:.3f}" if utility else "    Utility score: N/A")
    
    # Context summaries
    context_agents = list(metrics_collector.context_stats.keys())
    if context_agents:
        print("\nContext Engineering:")
        for agent_id in context_agents[:3]:  # Top 3
            summary = metrics_collector.get_context_summary(agent_id)
            if "error" not in summary:
                print(f"  {agent_id}:")
                print(f"    Reduce ops: {summary['reduce_operations']}")
                print(f"    Delegate ops: {summary['delegate_operations']}")
                print(f"    Tokens freed: {summary['total_tokens_freed']:,}")
                print(f"    Avg efficiency: {summary['avg_efficiency_score']:.1%}")
    
    # Top performers
    print("\nTop Performers (by utility score):")
    top = metrics_collector.get_top_performers(limit=3)
    for i, agent in enumerate(top, 1):
        print(f"  {i}. {agent['agent_id']}")
        print(f"     Utility: {agent['utility_score']:.3f}")
        print(f"     Success: {agent['success_rate']:.1%}")
        print(f"     Avg time: {agent['avg_time_ms']:.2f}ms")
    
    # Generate full report
    report_file = Path("./state/metrics/baseline_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report = metrics_collector.generate_report(output_file=report_file)
    
    print(f"\n✓ Full report saved to: {report_file}")
    
    return report


def main():
    """Run baseline measurements"""
    print("\n" + "=" * 70)
    print("AGI Core - Baseline Performance Measurement")
    print("=" * 70 + "\n")
    
    # Initialize metrics collector
    metrics_collector = MetricsCollector()
    
    # Run measurements
    context_results = measure_context_operations()
    expert_results = measure_expert_operations()
    workflow_results = measure_workflow_operations()
    delegation_results = measure_delegation_operations()
    
    # Set baselines
    print("=" * 70)
    print("Setting Baselines")
    print("=" * 70)
    
    metrics_collector.set_baseline("context_reduction_ms", context_results["reduction_time_ms"])
    print(f"✓ Context reduction: {context_results['reduction_time_ms']:.2f}ms")
    
    avg_expert_time = sum(r["execution_time_ms"] for r in expert_results) / len(expert_results)
    metrics_collector.set_baseline("expert_execution_ms", avg_expert_time)
    print(f"✓ Expert execution: {avg_expert_time:.2f}ms")
    
    metrics_collector.set_baseline("workflow_total_ms", workflow_results["total_time_ms"])
    print(f"✓ Workflow execution: {workflow_results['total_time_ms']:.2f}ms")
    
    metrics_collector.set_baseline("delegation_per_task_ms", delegation_results["avg_per_task_ms"])
    print(f"✓ Delegation per task: {delegation_results['avg_per_task_ms']:.2f}ms")
    
    print()
    
    # Generate report
    generate_baseline_report(metrics_collector)
    
    print("\n" + "=" * 70)
    print("Baseline measurement complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Use these baselines to track performance improvements")
    print("  2. Monitor metrics over time with metrics_collector")
    print("  3. Compare future runs with: metrics_collector.compare_to_baseline()")
    print("  4. Optimize based on utility scores")
    print()


if __name__ == "__main__":
    main()
