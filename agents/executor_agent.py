"""
NeuroForge Executor Agent
=========================
The "Worker" - Performs actual tasks based on Planner's instructions

Role: Task execution with tool usage
Input: Structured plan steps
Output: Results with execution metadata
"""

import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    """Execution status for task steps"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionResult:
    """Result of executing a single step"""
    step_id: int
    status: ExecutionStatus
    output: Any
    error: Optional[str]
    execution_time_ms: int
    tool_used: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class PlanExecution:
    """Complete execution of a plan"""
    plan_id: str
    results: List[ExecutionResult]
    overall_status: ExecutionStatus
    total_time_ms: int
    started_at: str
    completed_at: Optional[str]


class ExecutorAgent:
    """
    Executor Agent - Performs work based on structured plans

    Responsibilities:
    - Execute task steps from Planner
    - Use appropriate tools for each step
    - Track execution metadata
    - Handle errors gracefully
    - Return structured results for Critic review
    """

    def __init__(self, llm_client=None, tools: Optional[Dict[str, Callable]] = None):
        """
        Args:
            llm_client: LLM interface for reasoning/generation
            tools: Dictionary of callable tools {name: function}
        """
        self.llm = llm_client
        self.tools = tools or {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register built-in tools"""
        if "code_gen" not in self.tools:
            self.tools["code_gen"] = self._tool_code_generation
        if "file_ops" not in self.tools:
            self.tools["file_ops"] = self._tool_file_operations
        if "api_call" not in self.tools:
            self.tools["api_call"] = self._tool_api_call
        if "reasoning" not in self.tools:
            self.tools["reasoning"] = self._tool_reasoning

    def execute(self, plan) -> PlanExecution:
        """
        Execute a complete plan

        Args:
            plan: Plan object from PlannerAgent

        Returns:
            PlanExecution with all results
        """
        start_time = datetime.now()
        results = []

        print(f"\n🚀 Executing Plan: {plan.plan_id}")
        print(f"Goal: {plan.goal}")
        print(f"Steps: {len(plan.steps)}\n")

        # Execute steps respecting dependencies
        completed_steps = set()

        for step in sorted(plan.steps, key=lambda s: s.step_id):
            # Check dependencies
            if not all(dep in completed_steps for dep in step.dependencies):
                result = ExecutionResult(
                    step_id=step.step_id,
                    status=ExecutionStatus.SKIPPED,
                    output=None,
                    error="Dependencies not met",
                    execution_time_ms=0,
                    tool_used=None,
                    metadata={"dependencies_missing": [d for d in step.dependencies if d not in completed_steps]}
                )
                results.append(result)
                continue

            # Execute step
            result = self._execute_step(step)
            results.append(result)

            if result.status == ExecutionStatus.SUCCESS:
                completed_steps.add(step.step_id)
            elif result.status == ExecutionStatus.FAILED:
                print(f"❌ Step {step.step_id} failed: {result.error}")
                # Decide: continue or abort
                # For now, continue with other steps

        # Calculate overall status
        statuses = [r.status for r in results]
        if all(s == ExecutionStatus.SUCCESS for s in statuses):
            overall = ExecutionStatus.SUCCESS
        elif any(s == ExecutionStatus.FAILED for s in statuses):
            overall = ExecutionStatus.FAILED
        else:
            overall = ExecutionStatus.PENDING

        end_time = datetime.now()
        total_ms = int((end_time - start_time).total_seconds() * 1000)

        execution = PlanExecution(
            plan_id=plan.plan_id,
            results=results,
            overall_status=overall,
            total_time_ms=total_ms,
            started_at=start_time.isoformat(),
            completed_at=end_time.isoformat()
        )

        return execution

    def _execute_step(self, step) -> ExecutionResult:
        """Execute a single task step"""
        start = datetime.now()

        print(f"⚙️  Step {step.step_id}: {step.action}")

        # Determine tool to use
        tool_name = step.context.get("tool", "reasoning")
        tool = self.tools.get(tool_name, self._tool_reasoning)

        try:
            # Execute with tool
            output = tool(step)

            end = datetime.now()
            exec_time = int((end - start).total_seconds() * 1000)

            # Verify success criteria (simple check for now)
            success = self._check_success_criteria(output, step.success_criteria)

            result = ExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                output=output,
                error=None if success else "Success criteria not met",
                execution_time_ms=exec_time,
                tool_used=tool_name,
                metadata={
                    "action": step.action,
                    "complexity": step.estimated_complexity
                }
            )

            if success:
                print(f"  ✅ Completed in {exec_time}ms")
            else:
                print(f"  ⚠️  Completed but criteria not met")

            return result

        except Exception as e:
            end = datetime.now()
            exec_time = int((end - start).total_seconds() * 1000)

            print(f"  ❌ Error: {str(e)}")

            return ExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                output=None,
                error=str(e),
                execution_time_ms=exec_time,
                tool_used=tool_name,
                metadata={"exception_type": type(e).__name__}
            )

    def _check_success_criteria(self, output: Any, criteria: str) -> bool:
        """Simple success criteria check"""
        # TODO: Implement sophisticated criteria validation
        # For now: output exists = success
        return output is not None

    # ========================================
    # Built-in Tools
    # ========================================

    def _tool_code_generation(self, step) -> str:
        """Generate code using LLM"""
        if not self.llm:
            return f"# TODO: {step.action}"

        prompt = f"""Generate code for: {step.action}

Context: {json.dumps(step.context, indent=2)}

Requirements:
- {step.success_criteria}

Return clean, production-ready code."""

        return self.llm.generate(prompt, temperature=0.2)

    def _tool_file_operations(self, step) -> Dict[str, Any]:
        """Perform file operations"""
        action = step.context.get("operation", "read")
        path = step.context.get("path", "")

        if action == "read":
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return {"success": True, "content": content, "path": path}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif action == "write":
            content = step.context.get("content", "")
            try:
                with open(path, 'w') as f:
                    f.write(content)
                return {"success": True, "path": path, "bytes_written": len(content)}
            except Exception as e:
                return {"success": False, "error": str(e)}

        else:
            return {"success": False, "error": f"Unknown operation: {action}"}

    def _tool_api_call(self, step) -> Dict[str, Any]:
        """Make API calls"""
        import requests

        url = step.context.get("url", "")
        method = step.context.get("method", "GET").upper()

        try:
            if method == "GET":
                resp = requests.get(url, timeout=5)
            elif method == "POST":
                data = step.context.get("data", {})
                resp = requests.post(url, json=data, timeout=5)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}

            return {
                "success": True,
                "status_code": resp.status_code,
                "data": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_reasoning(self, step) -> str:
        """Use LLM for reasoning/analysis"""
        if not self.llm:
            return f"Analysis: {step.action} (LLM not available)"

        prompt = f"""Analyze and execute: {step.action}

Context: {json.dumps(step.context, indent=2)}

Provide clear, actionable analysis."""

        return self.llm.generate(prompt, temperature=0.4)

    def register_tool(self, name: str, func: Callable):
        """Register custom tool"""
        self.tools[name] = func

    def export_execution(self, execution: PlanExecution) -> str:
        """Export execution results as JSON"""
        # Convert Enums to strings for JSON serialization
        data = asdict(execution)
        data["overall_status"] = execution.overall_status.value
        for result in data["results"]:
            result["status"] = ExecutionStatus(result["status"]).value
        return json.dumps(data, indent=2, default=str)


# ============================================
# Example Usage
# ============================================
if __name__ == "__main__":
    from planner_agent import PlannerAgent, TaskStep

    # Create executor
    executor = ExecutorAgent()

    # Create a simple plan
    planner = PlannerAgent()
    plan = planner.create_plan("Test the executor agent")

    # Execute plan
    execution = executor.execute(plan)

    print("\n📊 Execution Results:")
    print("=" * 50)
    print(f"Status: {execution.overall_status.value}")
    print(f"Total time: {execution.total_time_ms}ms")
    print(f"Steps completed: {sum(1 for r in execution.results if r.status == ExecutionStatus.SUCCESS)}/{len(execution.results)}")
    print()

    for result in execution.results:
        print(f"Step {result.step_id}: {result.status.value}")
        if result.error:
            print(f"  Error: {result.error}")
        print(f"  Time: {result.execution_time_ms}ms")
        print()
