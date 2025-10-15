"""
Workflows - Scout-Plan-Build and Agentic Patterns

Implements IndyDevDan's key workflow patterns:
1. Scout - Explore and gather information
2. Plan - Break down tasks and strategize
3. Build - Execute the plan

These patterns enable efficient, focused agent work
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import logging
logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """Phases of the Scout-Plan-Build workflow"""
    SCOUT = "scout"
    PLAN = "plan"
    BUILD = "build"
    REVIEW = "review"  # Optional verification phase


@dataclass
class WorkflowResult:
    """Result from a workflow execution"""
    workflow_id: str
    phase: WorkflowPhase
    success: bool
    output: Dict[str, Any]
    duration_seconds: float
    tokens_used: int
    context_efficiency: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["phase"] = self.phase.value
        return data


class AgentWorkflow:
    """
    Base class for agentic workflows
    
    Provides structure for:
    - Purpose: What are we trying to accomplish?
    - Variables: What inputs do we need?
    - Workflow: What steps to execute?
    - Report: How to present results?
    """
    
    def __init__(
        self,
        workflow_id: str,
        purpose: str,
        variables: Dict[str, Any],
        report_format: str = "json"
    ):
        self.workflow_id = workflow_id
        self.purpose = purpose
        self.variables = variables
        self.report_format = report_format
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.results: List[WorkflowResult] = []
        
        logger.info(f"Created workflow: {workflow_id}, purpose: {purpose}")
    
    def execute(self) -> Dict[str, Any]:
        """Execute the workflow"""
        self.started_at = time.time()
        
        try:
            result = self._run()
            self.completed_at = time.time()
            return result
        except Exception as e:
            logger.error(f"Workflow {self.workflow_id} failed: {e}")
            self.completed_at = time.time()
            raise
    
    def _run(self) -> Dict[str, Any]:
        """Override this to implement workflow logic"""
        raise NotImplementedError("Subclasses must implement _run()")
    
    def duration(self) -> float:
        """Get workflow duration"""
        if not self.started_at or not self.completed_at:
            return 0.0
        return self.completed_at - self.started_at
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate workflow report"""
        return {
            "workflow_id": self.workflow_id,
            "purpose": self.purpose,
            "duration_seconds": self.duration(),
            "phases_completed": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "timestamp": self.completed_at or time.time()
        }


class ScoutPlanBuild(AgentWorkflow):
    """
    Scout-Plan-Build Workflow Pattern
    
    The most powerful agentic workflow pattern:
    
    1. SCOUT - Reconnaissance
       - Explore codebase
       - Identify key files
       - Understand architecture
       - Map dependencies
       - Keep context minimal
    
    2. PLAN - Strategy
       - Break down task
       - Identify approach
       - List required changes
       - Estimate complexity
       - Create step-by-step plan
    
    3. BUILD - Execution
       - Follow the plan
       - Make changes
       - Add tests
       - Verify correctness
       - Report completion
    """
    
    def __init__(
        self,
        workflow_id: str,
        task_description: str,
        codebase_path: Path,
        constraints: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            workflow_id=workflow_id,
            purpose=f"Scout-Plan-Build: {task_description}",
            variables={
                "task_description": task_description,
                "codebase_path": str(codebase_path),
                "constraints": constraints or {}
            }
        )
        self.task_description = task_description
        self.codebase_path = Path(codebase_path)
        self.constraints = constraints or {}
        
        self.scout_findings: Dict[str, Any] = {}
        self.plan: Dict[str, Any] = {}
        self.build_results: Dict[str, Any] = {}
    
    def _run(self) -> Dict[str, Any]:
        """Execute Scout-Plan-Build workflow"""
        logger.info(f"Starting Scout-Plan-Build workflow: {self.workflow_id}")
        
        # Phase 1: Scout
        scout_result = self._scout_phase()
        self.results.append(scout_result)
        
        if not scout_result.success:
            return {"error": "Scout phase failed", "details": scout_result.output}
        
        # Phase 2: Plan
        plan_result = self._plan_phase()
        self.results.append(plan_result)
        
        if not plan_result.success:
            return {"error": "Plan phase failed", "details": plan_result.output}
        
        # Phase 3: Build
        build_result = self._build_phase()
        self.results.append(build_result)
        
        if not build_result.success:
            return {"error": "Build phase failed", "details": build_result.output}
        
        return self.generate_report()
    
    def _scout_phase(self) -> WorkflowResult:
        """
        SCOUT Phase: Explore and gather information
        
        Key principle: Keep context minimal, focus on reconnaissance
        """
        logger.info(f"Scout phase starting for: {self.task_description}")
        start_time = time.time()
        
        # Simulate scouting
        # In production, this would invoke the scout_expert
        scout_output = {
            "relevant_files": [
                "agi_core/context_engineering.py",
                "agi_core/agent_experts.py",
                "orchestrator/app.py"
            ],
            "architecture_type": "microservices",
            "key_patterns": ["agent_orchestration", "context_management"],
            "dependencies": ["fastapi", "pydantic", "sentry_sdk"],
            "estimated_complexity": "medium",
            "notes": "Codebase uses agent-based architecture with governance layer"
        }
        
        self.scout_findings = scout_output
        duration = time.time() - start_time
        
        logger.info(f"Scout phase completed in {duration:.2f}s")
        
        return WorkflowResult(
            workflow_id=self.workflow_id,
            phase=WorkflowPhase.SCOUT,
            success=True,
            output=scout_output,
            duration_seconds=duration,
            tokens_used=3500,  # Estimated
            context_efficiency=0.92,
            timestamp=time.time()
        )
    
    def _plan_phase(self) -> WorkflowResult:
        """
        PLAN Phase: Create execution strategy
        
        Key principle: Break down into clear, actionable steps
        """
        logger.info(f"Plan phase starting based on scout findings")
        start_time = time.time()
        
        # Use scout findings to create plan
        plan_output = {
            "objective": self.task_description,
            "approach": "incremental_implementation",
            "steps": [
                {
                    "step": 1,
                    "action": "Create data models and schemas",
                    "files": ["models.py"],
                    "estimated_time": "5min"
                },
                {
                    "step": 2,
                    "action": "Implement core business logic",
                    "files": self.scout_findings.get("relevant_files", [])[:2],
                    "estimated_time": "15min"
                },
                {
                    "step": 3,
                    "action": "Add API endpoints",
                    "files": ["app.py"],
                    "estimated_time": "10min"
                },
                {
                    "step": 4,
                    "action": "Add tests and validation",
                    "files": ["tests/test_feature.py"],
                    "estimated_time": "10min"
                }
            ],
            "total_estimated_time": "40min",
            "risks": ["integration_complexity"],
            "dependencies": self.scout_findings.get("dependencies", []),
            "success_criteria": [
                "All tests pass",
                "Code follows existing patterns",
                "Documentation updated"
            ]
        }
        
        self.plan = plan_output
        duration = time.time() - start_time
        
        logger.info(f"Plan phase completed with {len(plan_output['steps'])} steps")
        
        return WorkflowResult(
            workflow_id=self.workflow_id,
            phase=WorkflowPhase.PLAN,
            success=True,
            output=plan_output,
            duration_seconds=duration,
            tokens_used=2800,
            context_efficiency=0.88,
            timestamp=time.time()
        )
    
    def _build_phase(self) -> WorkflowResult:
        """
        BUILD Phase: Execute the plan
        
        Key principle: Follow the plan precisely, report progress
        """
        logger.info(f"Build phase starting with {len(self.plan['steps'])} steps")
        start_time = time.time()
        
        # Execute plan steps
        # In production, this would invoke the build_expert
        build_output = {
            "steps_completed": len(self.plan["steps"]),
            "steps_failed": 0,
            "files_created": 4,
            "files_modified": 2,
            "tests_added": 8,
            "tests_passed": 8,
            "tests_failed": 0,
            "implementation_notes": [
                "Followed existing code patterns",
                "Added comprehensive error handling",
                "Included inline documentation"
            ],
            "deviations_from_plan": [],
            "status": "completed"
        }
        
        self.build_results = build_output
        duration = time.time() - start_time
        
        logger.info(f"Build phase completed in {duration:.2f}s")
        
        return WorkflowResult(
            workflow_id=self.workflow_id,
            phase=WorkflowPhase.BUILD,
            success=True,
            output=build_output,
            duration_seconds=duration,
            tokens_used=12000,
            context_efficiency=0.85,
            timestamp=time.time()
        )


class BackgroundWorkflow(AgentWorkflow):
    """
    Background workflow that runs out-of-loop
    
    Executes independently and reports when complete
    """
    
    def __init__(
        self,
        workflow_id: str,
        task: Dict[str, Any],
        report_file: Path
    ):
        super().__init__(
            workflow_id=workflow_id,
            purpose=task.get("description", "Background task"),
            variables=task
        )
        self.task = task
        self.report_file = Path(report_file)
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _run(self) -> Dict[str, Any]:
        """Execute background workflow"""
        logger.info(f"Background workflow {self.workflow_id} starting")
        
        # Execute task
        # This is where actual work would happen
        result = {
            "workflow_id": self.workflow_id,
            "task": self.task,
            "status": "completed",
            "output": "Task completed successfully",
            "timestamp": time.time()
        }
        
        # Write report
        with self.report_file.open("w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Background workflow {self.workflow_id} completed, report: {self.report_file}")
        
        return result


class ParallelWorkflow(AgentWorkflow):
    """
    Parallel workflow that executes multiple sub-workflows concurrently
    
    Implements delegation to maximize throughput
    """
    
    def __init__(
        self,
        workflow_id: str,
        purpose: str,
        sub_workflows: List[AgentWorkflow]
    ):
        super().__init__(
            workflow_id=workflow_id,
            purpose=purpose,
            variables={"sub_workflow_count": len(sub_workflows)}
        )
        self.sub_workflows = sub_workflows
    
    def _run(self) -> Dict[str, Any]:
        """Execute sub-workflows in parallel (simulated)"""
        logger.info(f"Parallel workflow {self.workflow_id} starting with {len(self.sub_workflows)} sub-workflows")
        
        results = []
        
        # In production, this would use actual parallelization
        # For now, execute sequentially but track as parallel
        for sub_workflow in self.sub_workflows:
            try:
                result = sub_workflow.execute()
                results.append({
                    "workflow_id": sub_workflow.workflow_id,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Sub-workflow {sub_workflow.workflow_id} failed: {e}")
                results.append({
                    "workflow_id": sub_workflow.workflow_id,
                    "success": False,
                    "error": str(e)
                })
        
        successes = sum(1 for r in results if r["success"])
        
        logger.info(f"Parallel workflow completed: {successes}/{len(results)} succeeded")
        
        return {
            "workflow_id": self.workflow_id,
            "purpose": self.purpose,
            "total_sub_workflows": len(self.sub_workflows),
            "successful": successes,
            "failed": len(results) - successes,
            "results": results,
            "duration_seconds": self.duration()
        }


class WorkflowOrchestrator:
    """
    Orchestrates complex multi-workflow executions
    
    Manages:
    - Workflow lifecycle
    - Dependencies between workflows
    - Resource allocation
    - Result aggregation
    """
    
    def __init__(self, state_dir: Path = Path("./state/workflows")):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.workflows: Dict[str, AgentWorkflow] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"WorkflowOrchestrator initialized: {self.state_dir}")
    
    def register_workflow(self, workflow: AgentWorkflow):
        """Register a workflow"""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.workflow_id}")
    
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a registered workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        logger.info(f"Executing workflow: {workflow_id}")
        
        try:
            result = workflow.execute()
            
            # Record history
            self.execution_history.append({
                "workflow_id": workflow_id,
                "success": True,
                "duration": workflow.duration(),
                "timestamp": time.time()
            })
            
            # Save result
            result_file = self.state_dir / f"{workflow_id}_result.json"
            with result_file.open("w") as f:
                json.dump(result, f, indent=2)
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            
            self.execution_history.append({
                "workflow_id": workflow_id,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
            
            raise
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "purpose": workflow.purpose,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "duration_seconds": workflow.duration(),
            "phases_completed": len(workflow.results)
        }

