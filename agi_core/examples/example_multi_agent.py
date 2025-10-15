#!/usr/bin/env python3
"""
Example: Multi-Agent Delegation

Demonstrates:
- Background agents
- Parallel execution
- Agent coordination
- Result aggregation
"""

import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from agi_core.delegation import (
    AgentDelegator,
    MultiAgentCoordinator,
    DelegationStrategy
)


def main():
    print("🤖 Multi-Agent Delegation Example\n")
    
    # Initialize delegation system
    delegator = AgentDelegator(max_parallel_agents=3)
    coordinator = MultiAgentCoordinator(delegator)
    
    print("=" * 60)
    print("1. Background Agent (Out-of-Loop)")
    print("=" * 60)
    
    # Delegate a background task
    agent_id_1 = delegator.delegate_task(
        agent_type="refactor",
        description="Refactor payment service for better error handling",
        context={"files": ["payment.py", "transactions.py"]},
        strategy=DelegationStrategy.BACKGROUND,
        priority=7
    )
    
    print(f"✓ Delegated background task")
    print(f"  Agent ID: {agent_id_1}")
    print(f"  Type: refactor")
    print(f"  Strategy: background (out-of-loop)\n")
    
    print("=" * 60)
    print("2. Parallel Execution")
    print("=" * 60)
    
    # Delegate multiple parallel tasks
    tasks = [
        {
            "agent_type": "test",
            "description": "Write unit tests for user service",
            "context": {"coverage_target": 0.85}
        },
        {
            "agent_type": "documentation",
            "description": "Update API documentation",
            "context": {"endpoints": ["users", "auth", "payments"]}
        },
        {
            "agent_type": "optimization",
            "description": "Optimize database queries",
            "context": {"tables": ["users", "transactions"]}
        }
    ]
    
    agent_ids = []
    for task in tasks:
        agent_id = delegator.delegate_task(
            agent_type=task["agent_type"],
            description=task["description"],
            context=task["context"],
            strategy=DelegationStrategy.PARALLEL,
            priority=5
        )
        agent_ids.append(agent_id)
        print(f"✓ Delegated parallel task: {task['agent_type']}")
    
    print(f"\n  Total agents: {len(agent_ids)}")
    print(f"  Execution: parallel (concurrent)\n")
    
    print("=" * 60)
    print("3. Check Agent Status")
    print("=" * 60)
    
    # Give agents time to "work"
    print("⏳ Agents working...")
    time.sleep(1)
    
    active = delegator.list_active_agents()
    print(f"\n✓ Active agents: {len(active)}")
    
    for agent_info in active[:3]:  # Show first 3
        status = delegator.get_agent_status(agent_info['agent_id'])
        print(f"  • {agent_info['agent_id']}: {status['status']}")
    
    print()
    
    print("=" * 60)
    print("4. Multi-Agent Coordination")
    print("=" * 60)
    
    # Coordinate a complex workflow
    workflow_result = coordinator.coordinate_workflow(
        workflow_id="api_v2_migration",
        tasks=[
            {
                "agent_type": "scout",
                "description": "Analyze current API structure",
                "context": {"version": "v1"},
                "priority": 9
            },
            {
                "agent_type": "plan",
                "description": "Create v2 migration strategy",
                "context": {"breaking_changes": True},
                "priority": 8
            },
            {
                "agent_type": "build",
                "description": "Implement v2 endpoints",
                "context": {"backwards_compatible": True},
                "priority": 7
            },
            {
                "agent_type": "test",
                "description": "Test v2 endpoints",
                "context": {"test_v1_compatibility": True},
                "priority": 6
            }
        ],
        strategy=DelegationStrategy.SEQUENTIAL
    )
    
    print(f"✓ Coordinated workflow: {workflow_result['workflow_id']}")
    print(f"  Tasks: {len(workflow_result['tasks'])}")
    print(f"  Strategy: {workflow_result['strategy']}")
    print(f"  Status: {workflow_result['status']}")
    print(f"  Agents: {len(workflow_result['agent_ids'])}\n")
    
    print("=" * 60)
    print("5. Wait for Completion & Aggregate Results")
    print("=" * 60)
    
    # Wait for agents to complete
    print("⏳ Waiting for agents to complete...")
    time.sleep(1)
    
    # Get aggregated results
    aggregated = coordinator.aggregate_results("api_v2_migration")
    
    print(f"\n✓ Workflow completed!")
    print(f"  Total agents: {aggregated['total_agents']}")
    print(f"  Completed: {aggregated['completed']}")
    print(f"  Successful: {aggregated['successful']}")
    print(f"  Failed: {aggregated['failed']}\n")
    
    print("Results:")
    for result in aggregated['results'][:3]:  # Show first 3
        print(f"  ✓ {result['task_id']}")
        print(f"    Agent: {result['agent_id']}")
        print(f"    Duration: {result['duration_seconds']:.2f}s")
        print(f"    Tokens: {result['tokens_used']:,}")
    
    print("\n✅ Multi-Agent Delegation complete!")
    print("\nKey Takeaways:")
    print("  • Background agents work out-of-loop")
    print("  • Parallel execution maximizes throughput")
    print("  • Sequential execution handles dependencies")
    print("  • Coordinator aggregates results")
    print("  • Each agent has focused, isolated context")


if __name__ == "__main__":
    main()

