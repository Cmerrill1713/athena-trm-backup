"""
NeuroForge Planner Agent
========================
The "Teacher" - Breaks down user intent into structured, executable tasks

Role: Strategic task decomposition
Input: User prompt/goal
Output: Structured plan with steps, context, and success criteria
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TaskStep:
    """Single executable step in a plan"""
    step_id: int
    action: str
    context: Dict[str, Any]
    dependencies: List[int]  # IDs of steps that must complete first
    success_criteria: str
    estimated_complexity: float  # 0.0-1.0


@dataclass
class Plan:
    """Complete execution plan"""
    plan_id: str
    goal: str
    steps: List[TaskStep]
    total_complexity: float
    created_at: str
    metadata: Dict[str, Any]


class PlannerAgent:
    """
    Planner Agent - Strategic task decomposition

    Responsibilities:
    - Analyze user intent
    - Break into atomic, executable steps
    - Provide context for each step
    - Define success criteria
    - Learn from historical patterns
    """

    def __init__(self, llm_client=None, memory=None):
        """
        Args:
            llm_client: LLM interface (Ollama, LM Studio, etc.)
            memory: Memory layer for historical patterns
        """
        self.llm = llm_client
        self.memory = memory
        self.plan_counter = 0

    def create_plan(self, goal: str, context: Optional[Dict] = None) -> Plan:
        """
        Create a structured plan from user goal

        Args:
            goal: User's objective
            context: Additional context (files, state, etc.)

        Returns:
            Structured Plan object
        """
        self.plan_counter += 1
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.plan_counter}"

        # Get historical patterns if memory available
        historical_context = ""
        if self.memory:
            similar_plans = self.memory.retrieve_similar_plans(goal, limit=3)
            if similar_plans:
                historical_context = self._format_historical_context(similar_plans)

        # Build planning prompt
        planning_prompt = self._build_planning_prompt(goal, context, historical_context)

        # Get plan from LLM
        if self.llm:
            plan_json = self.llm.generate(planning_prompt, temperature=0.3)
            steps = self._parse_plan_response(plan_json)
        else:
            # Fallback: Simple decomposition
            steps = self._simple_decomposition(goal)

        # Calculate complexity
        total_complexity = sum(step.estimated_complexity for step in steps) / len(steps) if steps else 0.0

        plan = Plan(
            plan_id=plan_id,
            goal=goal,
            steps=steps,
            total_complexity=total_complexity,
            created_at=datetime.now().isoformat(),
            metadata={
                "context": context or {},
                "has_historical_context": bool(historical_context),
                "step_count": len(steps)
            }
        )

        # Store plan in memory for future learning
        if self.memory:
            self.memory.store_plan(plan)

        return plan

    def refine_with_memory(self, goal: str) -> Plan:
        """
        Create plan using historical learnings

        This is where the "teaching" happens - the agent learns from past
        successes and failures to create better plans
        """
        if not self.memory:
            return self.create_plan(goal)

        # Retrieve relevant historical feedback
        learnings = self.memory.retrieve_learnings(goal, limit=5)

        # Build context from learnings
        context = {
            "learnings": learnings,
            "patterns": self.memory.get_success_patterns(goal),
            "common_failures": self.memory.get_failure_patterns(goal)
        }

        return self.create_plan(goal, context=context)

    def _build_planning_prompt(self, goal: str, context: Optional[Dict], historical: str) -> str:
        """Build LLM prompt for planning"""
        prompt = f"""You are a strategic planner. Break down this goal into executable steps.

Goal: {goal}

Context: {json.dumps(context or {}, indent=2)}

{historical}

Return a JSON plan with this structure:
{{
  "steps": [
    {{
      "step_id": 1,
      "action": "clear action description",
      "context": {{"key": "value"}},
      "dependencies": [],
      "success_criteria": "specific, measurable outcome",
      "estimated_complexity": 0.5
    }}
  ]
}}

Guidelines:
- Make steps atomic and executable
- Each step should be independently testable
- Include clear success criteria
- Estimate complexity: 0.1 (trivial) to 1.0 (complex)
- Order steps by dependencies
"""
        return prompt

    def _format_historical_context(self, similar_plans: List[Dict]) -> str:
        """Format historical patterns for prompt"""
        if not similar_plans:
            return ""

        context = "Historical Context (learned from past executions):\n"
        for i, plan in enumerate(similar_plans, 1):
            context += f"\n{i}. Similar goal: {plan.get('goal', 'unknown')}\n"
            context += f"   Success rate: {plan.get('success_rate', 0):.1%}\n"
            context += f"   Key learning: {plan.get('learning', 'N/A')}\n"

        return context

    def _parse_plan_response(self, response: str) -> List[TaskStep]:
        """Parse LLM JSON response into TaskStep objects"""
        try:
            data = json.loads(response)
            steps = []
            for step_data in data.get("steps", []):
                step = TaskStep(
                    step_id=step_data["step_id"],
                    action=step_data["action"],
                    context=step_data.get("context", {}),
                    dependencies=step_data.get("dependencies", []),
                    success_criteria=step_data.get("success_criteria", "complete without error"),
                    estimated_complexity=step_data.get("estimated_complexity", 0.5)
                )
                steps.append(step)
            return steps
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  Failed to parse LLM response: {e}")
            return []

    def _simple_decomposition(self, goal: str) -> List[TaskStep]:
        """Fallback: Simple rule-based decomposition"""
        # Basic decomposition when LLM not available
        return [
            TaskStep(
                step_id=1,
                action=f"Analyze: {goal}",
                context={"goal": goal},
                dependencies=[],
                success_criteria="Goal understood and validated",
                estimated_complexity=0.2
            ),
            TaskStep(
                step_id=2,
                action=f"Execute: {goal}",
                context={"goal": goal},
                dependencies=[1],
                success_criteria="Task completed successfully",
                estimated_complexity=0.6
            ),
            TaskStep(
                step_id=3,
                action=f"Verify: {goal}",
                context={"goal": goal},
                dependencies=[2],
                success_criteria="Results validated and correct",
                estimated_complexity=0.2
            )
        ]

    def export_plan(self, plan: Plan) -> str:
        """Export plan as JSON"""
        return json.dumps(asdict(plan), indent=2)

    def import_plan(self, plan_json: str) -> Plan:
        """Import plan from JSON"""
        data = json.loads(plan_json)
        steps = [TaskStep(**step_data) for step_data in data["steps"]]
        return Plan(
            plan_id=data["plan_id"],
            goal=data["goal"],
            steps=steps,
            total_complexity=data["total_complexity"],
            created_at=data["created_at"],
            metadata=data["metadata"]
        )


# ============================================
# Example Usage
# ============================================
if __name__ == "__main__":
    # Example: Create a planner without LLM (rule-based fallback)
    planner = PlannerAgent()

    # Create plan
    goal = "Write a DMG preflight validation script"
    plan = planner.create_plan(goal)

    print("📋 Generated Plan:")
    print("=" * 50)
    print(f"Goal: {plan.goal}")
    print(f"Steps: {len(plan.steps)}")
    print(f"Complexity: {plan.total_complexity:.2f}")
    print()

    for step in plan.steps:
        print(f"Step {step.step_id}: {step.action}")
        print(f"  Dependencies: {step.dependencies}")
        print(f"  Success: {step.success_criteria}")
        print(f"  Complexity: {step.estimated_complexity}")
        print()

    # Export plan
    plan_json = planner.export_plan(plan)
    print("\n📄 Plan JSON:")
    print(plan_json)
