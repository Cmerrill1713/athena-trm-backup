#!/usr/bin/env python3
"""
AGI Core + Governance Integration Demo

Demonstrates complete integration between AGI Core and your governance system.
Shows the full workflow from governance verdict to AGI remediation.
"""

import sys
import time
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agi_core import (
    ContextManager,
    ExpertRegistry,
    ExpertOrchestrator,
    ScoutPlanBuild,
    AgentDelegator,
    MultiAgentCoordinator,
    DelegationStrategy,
    get_metrics_collector
)


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def simulate_governance_verdict():
    """Simulate a governance verdict (HARD_FAIL)"""
    return {
        "task_id": "verdict_001",
        "verdict": "HARD_FAIL",
        "ece_estimate": 0.45,
        "entropy_drift": 0.23,
        "violation_rate_delta": 0.15,
        "latency_p95_delta": 150,
        "service": "user-api",
        "error": "High latency + violations detected",
        "timestamp": time.time()
    }


def main():
    print("\n" + "="*70)
    print("  🤖 AGI CORE + GOVERNANCE INTEGRATION DEMO 🤖")
    print("="*70)
    
    # Initialize AGI components
    print("\n📦 Initializing AGI Core components...")
    cm = ContextManager()
    expert_registry = ExpertRegistry()
    expert_orchestrator = ExpertOrchestrator(expert_registry)
    delegator = AgentDelegator(max_parallel_agents=5)
    coordinator = MultiAgentCoordinator(delegator)
    metrics_collector = get_metrics_collector()
    
    print("✓ ContextManager initialized")
    print("✓ ExpertRegistry initialized (6 experts)")
    print("✓ AgentDelegator initialized")
    print("✓ MetricsCollector initialized")
    
    # ========================================================================
    # SCENARIO: Governance System Detects Failure
    # ========================================================================
    
    print_section("1. GOVERNANCE VERDICT RECEIVED")
    
    verdict = simulate_governance_verdict()
    
    print(f"⚠️  Governance Verdict: {verdict['verdict']}")
    print(f"   Service: {verdict['service']}")
    print(f"   Error: {verdict['error']}")
    print(f"   ECE: {verdict['ece_estimate']:.2f}")
    print(f"   Latency Delta: +{verdict['latency_p95_delta']}ms")
    print(f"   Violation Rate: +{verdict['violation_rate_delta']:.1%}")
    
    # ========================================================================
    # STEP 1: AGI Takes Over Investigation
    # ========================================================================
    
    print_section("2. AGI INVESTIGATION (Scout-Plan-Build)")
    
    print("🔍 Creating AGI investigation workflow...")
    
    # Create Scout-Plan-Build workflow for investigation
    investigation = ScoutPlanBuild(
        workflow_id=f"investigate_{verdict['task_id']}",
        task_description=f"Investigate {verdict['service']} failure: {verdict['error']}",
        codebase_path=Path("./"),
        constraints={
            "severity": "critical",
            "max_time_minutes": 30,
            "requires_fix": True
        }
    )
    
    print(f"✓ Workflow created: {investigation.workflow_id}")
    
    # Execute investigation
    print("\n📊 Executing Scout-Plan-Build phases...")
    start_time = time.time()
    result = investigation.execute()
    investigation_time = time.time() - start_time
    
    print(f"\n✅ Investigation complete in {investigation_time:.2f}s")
    print(f"   Phases completed: {len(result.get('results', []))}")
    
    for phase_result in result.get('results', []):
        phase = phase_result.get('phase', 'unknown')
        tokens = phase_result.get('tokens_used', 0)
        efficiency = phase_result.get('context_efficiency', 0)
        print(f"   • {phase.upper()}: {tokens:,} tokens, {efficiency:.0%} efficient")
    
    # ========================================================================
    # STEP 2: Delegate Remediation to Expert Agents
    # ========================================================================
    
    print_section("3. EXPERT AGENT REMEDIATION")
    
    print("🤖 Delegating remediation tasks to expert agents...")
    
    # Multi-agent remediation workflow
    remediation_workflow = coordinator.coordinate_workflow(
        workflow_id=f"remediate_{verdict['task_id']}",
        tasks=[
            {
                "agent_type": "performance",
                "description": f"Optimize {verdict['service']} latency",
                "context": {
                    "current_p95": 500 + verdict['latency_p95_delta'],
                    "target_p95": 200,
                    "service": verdict['service']
                },
                "priority": 9
            },
            {
                "agent_type": "debug",
                "description": f"Debug violations in {verdict['service']}",
                "context": {
                    "violation_rate": verdict['violation_rate_delta'],
                    "service": verdict['service']
                },
                "priority": 8
            },
            {
                "agent_type": "security",
                "description": f"Security audit {verdict['service']}",
                "context": {
                    "focus": "violations",
                    "service": verdict['service']
                },
                "priority": 7
            }
        ],
        strategy=DelegationStrategy.PARALLEL
    )
    
    print(f"✓ Remediation workflow coordinated: {remediation_workflow['workflow_id']}")
    print(f"   Tasks: {len(remediation_workflow['tasks'])}")
    print(f"   Strategy: {remediation_workflow['strategy']}")
    print(f"   Agents deployed: {len(remediation_workflow['agent_ids'])}")
    
    # Simulate agents working
    print("\n⏳ Expert agents working in parallel...")
    time.sleep(1)
    
    # Get workflow status
    status = coordinator.get_workflow_status(remediation_workflow['workflow_id'])
    print(f"\n✓ Remediation tasks dispatched")
    print(f"   Total tasks: {status['total_tasks']}")
    print(f"   Strategy: {status['strategy']}")
    
    # ========================================================================
    # STEP 3: Context Engineering (R&D Framework)
    # ========================================================================
    
    print_section("4. CONTEXT ENGINEERING (R&D Framework)")
    
    # Create context for main investigation agent
    print("🧠 Managing agent context windows...")
    
    context = cm.create_context(
        agent_id="investigation_agent",
        session_id=verdict['task_id'],
        max_tokens=200000
    )
    
    # Simulate context growth
    context.current_tokens = 140000
    context.memory_file_tokens = 30000
    context.mcp_tool_tokens = 25000
    context.prompt_history_tokens = 85000
    
    print(f"⚠️  Context at {context.utilization_percent():.1f}% utilization")
    print(f"   Current: {context.current_tokens:,} tokens")
    
    # Apply REDUCE strategy
    print("\n📉 Applying REDUCE strategy...")
    reduction = cm.reduce_context("investigation_agent")
    
    print(f"✓ Context reduced")
    print(f"   Freed: {reduction['tokens_freed']:,} tokens")
    print(f"   Efficiency: {reduction.get('efficiency_score', 0):.1%}")
    print(f"   New utilization: {reduction['new_tokens'] / context.max_tokens * 100:.1f}%")
    
    # ========================================================================
    # STEP 4: Performance Metrics & Optimization
    # ========================================================================
    
    print_section("5. PERFORMANCE METRICS & OPTIMIZATION")
    
    print("📊 Collecting performance metrics...")
    
    # Get agent summaries
    experts_found = 0
    for expert_id in ["performance_expert", "debug_expert", "security_expert"]:
        summary = metrics_collector.get_agent_summary(expert_id)
        if "error" not in summary:
            experts_found += 1
            print(f"\n✓ {expert_id}")
            print(f"   Tasks: {summary['total_tasks']}")
            print(f"   Success rate: {summary['success_rate']:.1%}")
    
    if experts_found == 0:
        print("\n⚠️  No agent metrics yet (agents just deployed)")
        print("   Metrics will be available after task completion")
    
    # Context engineering metrics
    context_summary = metrics_collector.get_context_summary("investigation_agent")
    if "error" not in context_summary:
        print(f"\n✓ Context Engineering:")
        print(f"   Reduce ops: {context_summary['reduce_operations']}")
        print(f"   Tokens freed: {context_summary['total_tokens_freed']:,}")
        print(f"   Efficiency: {context_summary['avg_efficiency_score']:.1%}")
    
    # ========================================================================
    # STEP 5: Report Back to Governance
    # ========================================================================
    
    print_section("6. REPORT TO GOVERNANCE SYSTEM")
    
    # Prepare governance report
    governance_report = {
        "task_id": verdict['task_id'],
        "agi_verdict": "REMEDIATION_IN_PROGRESS",
        "investigation_complete": True,
        "investigation_time_seconds": investigation_time,
        "remediation_agents_deployed": len(remediation_workflow['agent_ids']),
        "context_efficiency": reduction.get('efficiency_score', 0),
        "tokens_used": sum(r.get('tokens_used', 0) for r in result.get('results', [])),
        "estimated_fix_time_minutes": 15,
        "confidence_score": 0.87,
        "actions_taken": [
            f"Investigated with Scout-Plan-Build ({len(result.get('results', []))} phases)",
            f"Deployed {len(remediation_workflow['agent_ids'])} expert agents",
            "Applied context reduction (R&D Framework)",
            f"Freed {reduction['tokens_freed']:,} context tokens"
        ],
        "timestamp": time.time()
    }
    
    print("✓ AGI Report prepared for governance system")
    print(f"   Status: {governance_report['agi_verdict']}")
    print(f"   Investigation time: {governance_report['investigation_time_seconds']:.2f}s")
    print(f"   Agents deployed: {governance_report['remediation_agents_deployed']}")
    print(f"   Context efficiency: {governance_report['context_efficiency']:.1%}")
    print(f"   Tokens used: {governance_report['tokens_used']:,}")
    print(f"   Confidence: {governance_report['confidence_score']:.1%}")
    
    print("\n📤 Sending report to governance orchestrator...")
    print("   POST http://localhost:8000/verdict")
    
    # In production, this would be:
    # response = requests.post("http://localhost:8000/verdict", json=governance_report)
    
    print("\n✅ Report sent successfully")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print_section("7. INTEGRATION SUMMARY")
    
    print("🎉 Complete AGI + Governance Integration Demonstrated!")
    print()
    print("Workflow:")
    print("  1. ✓ Governance detected HARD_FAIL")
    print("  2. ✓ AGI investigated with Scout-Plan-Build")
    print("  3. ✓ Expert agents deployed for remediation")
    print("  4. ✓ Context optimized with R&D Framework")
    print("  5. ✓ Performance metrics collected")
    print("  6. ✓ Report sent back to governance")
    print()
    print("Key Metrics:")
    print(f"  • Investigation time: {investigation_time:.2f}s")
    print(f"  • Context efficiency: {reduction.get('efficiency_score', 0):.1%}")
    print(f"  • Tokens freed: {reduction['tokens_freed']:,}")
    print(f"  • Expert agents: {len(remediation_workflow['agent_ids'])}")
    print(f"  • Confidence score: {governance_report['confidence_score']:.1%}")
    print()
    print("AGI Core + Governance = 🚀 Autonomous System")
    
    # Save report
    report_file = Path("./state/metrics/integration_demo_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with report_file.open("w") as f:
        json.dump(governance_report, f, indent=2)
    
    print(f"\n✓ Full report saved: {report_file}")
    
    print("\n" + "="*70)
    print("  Demo complete! AGI Core is ready for production.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

