"""
NeuroForge Orchestrator
=======================
The "Conductor" - Coordinates all agents in the learning loop

Role: Agent coordination and workflow management
Input: User goal
Output: Complete execution with learning feedback
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from planner_agent import PlannerAgent
from executor_agent import ExecutorAgent, ExecutionStatus
from critic_agent import CriticAgent
from memory_layer import MemoryLayer


@dataclass
class OrchestratorResult:
    """Complete orchestration result"""
    goal: str
    plan_id: str
    execution_id: str
    review_id: str
    overall_score: float
    success: bool
    iterations: int
    total_time_ms: int
    learnings: List[str]
    output: Any


class Orchestrator:
    """
    Orchestrator - Coordinates Planner → Executor → Critic → Memory loop

    This is the brain that makes the agents collaborate and learn from each other.

    Workflow:
    1. User provides goal
    2. Planner creates structured plan (with historical context from Memory)
    3. Executor performs work
    4. Critic reviews results
    5. Memory stores feedback
    6. If needed, iterate with improvements
    7. Return final result
    """

    def __init__(
        self,
        llm_client=None,
        memory_path: str = "memory/neuroforge.db",
        max_iterations: int = 3
    ):
        """
        Args:
            llm_client: Shared LLM interface for all agents
            memory_path: Path to memory database
            max_iterations: Max retry attempts
        """
        self.memory = MemoryLayer(memory_path)
        self.planner = PlannerAgent(llm_client, self.memory)
        self.executor = ExecutorAgent(llm_client)
        self.critic = CriticAgent(llm_client)
        self.max_iterations = max_iterations
        self.execution_counter = 0

    def execute_goal(self, goal: str, context: Optional[Dict] = None) -> OrchestratorResult:
        """
        Execute a goal with full agent collaboration

        This is the main entry point - handles the complete learning loop

        Args:
            goal: User's objective
            context: Additional context

        Returns:
            OrchestratorResult with final output and learnings
        """
        start_time = datetime.now()

        print("\n" + "=" * 60)
        print(f"🧠 NEUROFORGE AGENT SYSTEM")
        print("=" * 60)
        print(f"Goal: {goal}")
        print()

        iteration = 0
        best_score = 0.0
        best_result = None
        all_learnings = []

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n🔁 Iteration {iteration}/{self.max_iterations}")
            print("-" * 60)

            # PHASE 1: PLANNING (with memory)
            print("\n🧠 PLANNER: Creating execution plan...")
            if iteration == 1:
                plan = self.planner.create_plan(goal, context)
            else:
                # Use learnings from previous iteration
                plan = self.planner.refine_with_memory(goal)

            print(f"   Plan ID: {plan.plan_id}")
            print(f"   Steps: {len(plan.steps)}")
            print(f"   Complexity: {plan.total_complexity:.2f}")

            # PHASE 2: EXECUTION
            print("\n🚀 EXECUTOR: Running plan...")
            self.execution_counter += 1
            execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.execution_counter}"

            execution = self.executor.execute(plan)
            self.memory.store_execution(execution, execution_id)

            print(f"   Status: {execution.overall_status.value}")
            print(f"   Time: {execution.total_time_ms}ms")

            # PHASE 3: REVIEW
            print("\n🕵️  CRITIC: Reviewing execution...")
            review = self.critic.review(plan, execution)
            self.memory.store_review(review)

            print(f"   Score: {review.overall_score:.2f}")
            print(f"   Quality: {review.overall_quality.value}")
            print(f"   Retry needed: {review.should_retry}")

            # Collect learnings
            all_learnings.extend(review.key_learnings)

            # Track best result
            if review.overall_score > best_score:
                best_score = review.overall_score
                best_result = {
                    "plan": plan,
                    "execution": execution,
                    "review": review
                }

            # PHASE 4: DECISION
            if not review.should_retry or review.overall_score >= 0.9:
                print(f"\n✅ Goal achieved (score: {review.overall_score:.2f})")
                break

            if iteration < self.max_iterations:
                print(f"\n🔄 Score below threshold, iterating with improvements...")
                # Learnings automatically stored in memory for next iteration

        # PHASE 5: FINAL RESULT
        end_time = datetime.now()
        total_ms = int((end_time - start_time).total_seconds() * 1000)

        if not best_result:
            # Should never happen, but handle gracefully
            return OrchestratorResult(
                goal=goal,
                plan_id="",
                execution_id="",
                review_id="",
                overall_score=0.0,
                success=False,
                iterations=iteration,
                total_time_ms=total_ms,
                learnings=[],
                output=None
            )

        # Extract final output
        successful_results = [
            r for r in best_result["execution"].results
            if r.status == ExecutionStatus.SUCCESS
        ]
        final_output = [r.output for r in successful_results] if successful_results else None

        result = OrchestratorResult(
            goal=goal,
            plan_id=best_result["plan"].plan_id,
            execution_id=execution_id,
            review_id=best_result["review"].review_id,
            overall_score=best_score,
            success=best_score >= 0.7,
            iterations=iteration,
            total_time_ms=total_ms,
            learnings=all_learnings,
            output=final_output
        )

        print("\n" + "=" * 60)
        print("🎯 FINAL RESULT")
        print("=" * 60)
        print(f"Success: {result.success}")
        print(f"Score: {result.overall_score:.2f}")
        print(f"Iterations: {result.iterations}")
        print(f"Total time: {result.total_time_ms}ms")
        print(f"\n📚 Learnings:")
        for learning in result.learnings[:5]:  # Top 5
            print(f"  • {learning}")
        print()

        return result

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory layer statistics"""
        return self.memory.get_stats()

    def close(self):
        """Clean shutdown"""
        if self.memory:
            self.memory.close()


# ============================================
# Example Usage
# ============================================
if __name__ == "__main__":
    print("🧠 NeuroForge Agent System - Demo")
    print("=" * 60)

    # Create orchestrator
    orchestrator = Orchestrator(memory_path="memory/demo.db")

    # Execute a goal
    goal = "Create a validation script for DMG builds"
    result = orchestrator.execute_goal(goal)

    print("\n📋 Result Summary:")
    print(json.dumps(asdict(result), indent=2, default=str))

    # Show memory stats
    stats = orchestrator.get_memory_stats()
    print("\n📊 Memory Stats:")
    print(json.dumps(stats, indent=2))

    # Cleanup
    orchestrator.close()
