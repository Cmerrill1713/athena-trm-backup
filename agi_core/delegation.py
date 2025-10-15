"""
Multi-Agent Delegation System

Implements IndyDevDan's delegation patterns:
- Background agents for out-of-loop work
- Primary agent delegation
- Context isolation between agents
- Result aggregation
"""

import json
import time
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future

import logging
logger = logging.getLogger(__name__)


class DelegationStrategy(Enum):
    """Strategy for delegating work"""
    BACKGROUND = "background"  # Fire and forget, out-of-loop
    PARALLEL = "parallel"  # Execute multiple agents concurrently
    SEQUENTIAL = "sequential"  # Execute in order with dependencies
    SPECIALIST = "specialist"  # Route to domain expert


@dataclass
class AgentTask:
    """Task to be delegated to an agent"""
    task_id: str
    agent_type: str
    description: str
    context: Dict[str, Any]
    strategy: DelegationStrategy
    priority: int = 5
    timeout_seconds: int = 300
    dependencies: List[str] = None
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["strategy"] = self.strategy.value
        return data


@dataclass
class DelegationResult:
    """Result from a delegated agent"""
    task_id: str
    agent_id: str
    success: bool
    output: Dict[str, Any]
    duration_seconds: float
    tokens_used: int
    context_size: int
    timestamp: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BackgroundAgent:
    """
    Background agent that runs out-of-loop
    
    Key characteristics:
    - Executes independently
    - Writes results to report file
    - Minimal supervision needed
    - Focused on single task
    """
    
    def __init__(
        self,
        agent_id: str,
        task: AgentTask,
        report_dir: Path = Path("./state/agents/background")
    ):
        self.agent_id = agent_id
        self.task = task
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.report_file = self.report_dir / f"{agent_id}_{task.task_id}.json"
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.status = "pending"
        
        logger.info(f"Background agent created: {agent_id} for task {task.task_id}")
    
    def execute(self) -> DelegationResult:
        """Execute the task in background"""
        self.started_at = time.time()
        self.status = "running"
        
        logger.info(f"Background agent {self.agent_id} starting task {self.task.task_id}")
        
        try:
            # Simulate agent execution
            # In production, this would invoke actual agent
            output = self._execute_task()
            
            self.completed_at = time.time()
            self.status = "completed"
            
            result = DelegationResult(
                task_id=self.task.task_id,
                agent_id=self.agent_id,
                success=True,
                output=output,
                duration_seconds=self.completed_at - self.started_at,
                tokens_used=5000,
                context_size=8000,
                timestamp=self.completed_at
            )
            
            # Write report
            with self.report_file.open("w") as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Background agent {self.agent_id} completed: {self.report_file}")
            
            return result
            
        except Exception as e:
            self.completed_at = time.time()
            self.status = "failed"
            
            logger.error(f"Background agent {self.agent_id} failed: {e}")
            
            result = DelegationResult(
                task_id=self.task.task_id,
                agent_id=self.agent_id,
                success=False,
                output={},
                duration_seconds=self.completed_at - self.started_at,
                tokens_used=1000,
                context_size=2000,
                timestamp=self.completed_at,
                error=str(e)
            )
            
            # Write error report
            with self.report_file.open("w") as f:
                json.dump(result.to_dict(), f, indent=2)
            
            return result
    
    def _execute_task(self) -> Dict[str, Any]:
        """Execute the actual task"""
        # Simulate work
        time.sleep(0.5)
        
        return {
            "task_id": self.task.task_id,
            "agent_type": self.task.agent_type,
            "description": self.task.description,
            "result": f"Task '{self.task.description}' completed successfully",
            "context_processed": len(str(self.task.context)),
            "operations_performed": 5
        }


class AgentDelegator:
    """
    Agent Delegator - Routes and manages delegated work
    
    Implements multiple delegation strategies:
    - Background: Out-of-loop execution
    - Parallel: Concurrent execution
    - Sequential: Ordered execution with dependencies
    - Specialist: Route to domain experts
    """
    
    def __init__(
        self,
        state_dir: Path = Path("./state/delegation"),
        max_parallel_agents: int = 5
    ):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.max_parallel_agents = max_parallel_agents
        
        self.active_agents: Dict[str, BackgroundAgent] = {}
        self.completed_tasks: Dict[str, DelegationResult] = {}
        self.task_queue: List[AgentTask] = []
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_parallel_agents)
        self.futures: Dict[str, Future] = {}
        
        logger.info(f"AgentDelegator initialized: max_parallel={max_parallel_agents}")
    
    def delegate_task(
        self,
        agent_type: str,
        description: str,
        context: Dict[str, Any],
        strategy: DelegationStrategy = DelegationStrategy.BACKGROUND,
        priority: int = 5
    ) -> str:
        """Delegate a task to an agent"""
        task_id = f"task_{int(time.time() * 1000)}"
        
        task = AgentTask(
            task_id=task_id,
            agent_type=agent_type,
            description=description,
            context=context,
            strategy=strategy,
            priority=priority
        )
        
        self.task_queue.append(task)
        
        logger.info(f"Delegated task: {task_id}, type={agent_type}, strategy={strategy.value}")
        
        # Execute based on strategy
        if strategy == DelegationStrategy.BACKGROUND:
            return self._execute_background(task)
        elif strategy == DelegationStrategy.PARALLEL:
            return self._execute_parallel(task)
        elif strategy == DelegationStrategy.SEQUENTIAL:
            return self._execute_sequential(task)
        else:
            return self._execute_specialist(task)
    
    def _execute_background(self, task: AgentTask) -> str:
        """Execute task in background"""
        task_time = f"{task.task_id}_{time.time()}"
        agent_id = f"bg_{hashlib.md5(task_time.encode()).hexdigest()[:8]}"
        
        agent = BackgroundAgent(
            agent_id=agent_id,
            task=task,
            report_dir=self.state_dir / "background"
        )
        
        self.active_agents[agent_id] = agent
        
        # Submit to thread pool
        future = self.executor.submit(agent.execute)
        self.futures[agent_id] = future
        
        logger.info(f"Background agent {agent_id} submitted for task {task.task_id}")
        
        return agent_id
    
    def _execute_parallel(self, task: AgentTask) -> str:
        """Execute task in parallel with others"""
        return self._execute_background(task)  # Same as background for now
    
    def _execute_sequential(self, task: AgentTask) -> str:
        """Execute task sequentially (blocking)"""
        task_time = f"{task.task_id}_{time.time()}"
        agent_id = f"seq_{hashlib.md5(task_time.encode()).hexdigest()[:8]}"
        
        agent = BackgroundAgent(
            agent_id=agent_id,
            task=task,
            report_dir=self.state_dir / "sequential"
        )
        
        # Execute synchronously
        result = agent.execute()
        self.completed_tasks[task.task_id] = result
        
        return agent_id
    
    def _execute_specialist(self, task: AgentTask) -> str:
        """Route to specialist agent"""
        # This would integrate with ExpertRegistry
        return self._execute_background(task)
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of a delegated agent"""
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            return {
                "agent_id": agent_id,
                "task_id": agent.task.task_id,
                "status": agent.status,
                "started_at": agent.started_at,
                "completed_at": agent.completed_at,
                "report_file": str(agent.report_file) if agent.report_file.exists() else None
            }
        
        return {"error": f"Agent {agent_id} not found"}
    
    def get_task_result(self, task_id: str, wait: bool = False) -> Optional[DelegationResult]:
        """Get result of a delegated task"""
        # Check completed tasks
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        # Check active agents
        for agent_id, agent in self.active_agents.items():
            if agent.task.task_id == task_id:
                if wait and agent_id in self.futures:
                    # Wait for completion
                    future = self.futures[agent_id]
                    result = future.result(timeout=agent.task.timeout_seconds)
                    self.completed_tasks[task_id] = result
                    return result
                elif agent.status == "completed":
                    # Load from report file
                    if agent.report_file.exists():
                        with agent.report_file.open("r") as f:
                            data = json.load(f)
                        result = DelegationResult(**data)
                        self.completed_tasks[task_id] = result
                        return result
        
        return None
    
    def wait_for_agents(self, agent_ids: List[str], timeout: float = 300) -> List[DelegationResult]:
        """Wait for multiple agents to complete"""
        results = []
        
        for agent_id in agent_ids:
            if agent_id in self.futures:
                try:
                    result = self.futures[agent_id].result(timeout=timeout)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Agent {agent_id} failed: {e}")
        
        return results
    
    def list_active_agents(self) -> List[Dict[str, Any]]:
        """List all active agents"""
        return [
            {
                "agent_id": agent_id,
                "task_id": agent.task.task_id,
                "status": agent.status,
                "agent_type": agent.task.agent_type
            }
            for agent_id, agent in self.active_agents.items()
        ]
    
    def cleanup_completed(self):
        """Clean up completed agents from active list"""
        completed = [
            agent_id for agent_id, agent in self.active_agents.items()
            if agent.status in ["completed", "failed"]
        ]
        
        for agent_id in completed:
            del self.active_agents[agent_id]
            if agent_id in self.futures:
                del self.futures[agent_id]
        
        logger.info(f"Cleaned up {len(completed)} completed agents")


class MultiAgentCoordinator:
    """
    Coordinates multiple agents working on related tasks
    
    Manages:
    - Task dependencies
    - Resource allocation
    - Result aggregation
    - Conflict resolution
    """
    
    def __init__(self, delegator: AgentDelegator):
        self.delegator = delegator
        self.coordinated_workflows: Dict[str, Dict[str, Any]] = {}
        
        logger.info("MultiAgentCoordinator initialized")
    
    def coordinate_workflow(
        self,
        workflow_id: str,
        tasks: List[Dict[str, Any]],
        strategy: DelegationStrategy = DelegationStrategy.PARALLEL
    ) -> Dict[str, Any]:
        """
        Coordinate a multi-agent workflow
        
        Args:
            workflow_id: Unique workflow identifier
            tasks: List of task specifications
            strategy: How to execute tasks (parallel, sequential, etc.)
        
        Returns:
            Workflow coordination result
        """
        logger.info(f"Coordinating workflow {workflow_id} with {len(tasks)} tasks")
        
        self.coordinated_workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "tasks": tasks,
            "strategy": strategy.value,
            "started_at": time.time(),
            "agent_ids": [],
            "status": "running"
        }
        
        agent_ids = []
        
        # Delegate all tasks
        for task_spec in tasks:
            agent_id = self.delegator.delegate_task(
                agent_type=task_spec.get("agent_type", "general"),
                description=task_spec["description"],
                context=task_spec.get("context", {}),
                strategy=strategy,
                priority=task_spec.get("priority", 5)
            )
            agent_ids.append(agent_id)
        
        self.coordinated_workflows[workflow_id]["agent_ids"] = agent_ids
        
        # If sequential, wait for completion
        if strategy == DelegationStrategy.SEQUENTIAL:
            results = self.delegator.wait_for_agents(agent_ids)
            self.coordinated_workflows[workflow_id]["status"] = "completed"
            self.coordinated_workflows[workflow_id]["completed_at"] = time.time()
            self.coordinated_workflows[workflow_id]["results"] = [r.to_dict() for r in results]
        
        logger.info(f"Workflow {workflow_id} coordinated with agents: {agent_ids}")
        
        return self.coordinated_workflows[workflow_id]
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a coordinated workflow"""
        if workflow_id not in self.coordinated_workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        workflow = self.coordinated_workflows[workflow_id]
        
        # Check agent statuses
        agent_statuses = [
            self.delegator.get_agent_status(agent_id)
            for agent_id in workflow["agent_ids"]
        ]
        
        return {
            "workflow_id": workflow_id,
            "strategy": workflow["strategy"],
            "total_tasks": len(workflow["tasks"]),
            "started_at": workflow["started_at"],
            "status": workflow["status"],
            "agents": agent_statuses
        }
    
    def aggregate_results(self, workflow_id: str) -> Dict[str, Any]:
        """Aggregate results from all agents in a workflow"""
        if workflow_id not in self.coordinated_workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        workflow = self.coordinated_workflows[workflow_id]
        results = []
        
        for agent_id in workflow["agent_ids"]:
            agent = self.delegator.active_agents.get(agent_id)
            if agent and agent.report_file.exists():
                with agent.report_file.open("r") as f:
                    result = json.load(f)
                results.append(result)
        
        successes = sum(1 for r in results if r.get("success", False))
        
        return {
            "workflow_id": workflow_id,
            "total_agents": len(workflow["agent_ids"]),
            "completed": len(results),
            "successful": successes,
            "failed": len(results) - successes,
            "results": results
        }

