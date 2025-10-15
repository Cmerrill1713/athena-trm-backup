"""
Agent Experts - Specialized Agent Framework

Implements IndyDevDan's Agent Expert pattern:
"Better agents and then more agents"

Each expert is a specialized agent with:
- Focused system prompt
- Specific tools/capabilities
- Domain expertise
- Minimal context footprint
"""

import json
import time
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import logging
logger = logging.getLogger(__name__)

# Import metrics collector (lazy to avoid circular imports)
def _get_metrics_collector():
    """Lazy import of metrics collector"""
    try:
        from .evaluation_metrics import get_metrics_collector
        return get_metrics_collector()
    except ImportError:
        return None


class ExpertDomain(Enum):
    """Domain specializations for expert agents"""
    # Code domains
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    CODE_REVIEW = "code_review"
    OPTIMIZATION = "optimization"
    
    # Architecture domains
    ARCHITECTURE = "architecture"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"
    
    # Operations domains
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    INCIDENT_RESPONSE = "incident_response"
    
    # Analysis domains
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DATA_ANALYSIS = "data_analysis"
    
    # Documentation
    DOCUMENTATION = "documentation"
    TECHNICAL_WRITING = "technical_writing"
    
    # Planning
    PROJECT_PLANNING = "project_planning"
    TASK_BREAKDOWN = "task_breakdown"


@dataclass
class AgentExpert:
    """
    Specialized agent expert with focused capabilities
    
    Based on the principle: A focused agent is a performant agent
    """
    expert_id: str
    domain: ExpertDomain
    name: str
    description: str
    system_prompt: str
    tools: List[str]
    max_context_tokens: int = 50000  # Smaller context for focus
    capabilities: List[str] = None
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        data = asdict(self)
        data["domain"] = self.domain.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentExpert":
        """Create from dict"""
        data["domain"] = ExpertDomain(data["domain"])
        return cls(**data)
    
    def can_handle(self, task_type: str) -> bool:
        """Check if this expert can handle a task type"""
        task_lower = task_type.lower()
        domain_lower = self.domain.value.lower()
        
        # Direct match
        if task_lower == domain_lower:
            return True
        
        # Check capabilities
        for capability in self.capabilities:
            if capability.lower() in task_lower or task_lower in capability.lower():
                return True
        
        return False


class ExpertRegistry:
    """
    Registry of specialized agent experts
    
    Manages the expert pool and routes tasks to appropriate specialists
    """
    
    def __init__(self, experts_dir: Path = Path("./experts")):
        self.experts_dir = Path(experts_dir)
        self.experts_dir.mkdir(parents=True, exist_ok=True)
        self.experts: Dict[str, AgentExpert] = {}
        self._load_experts()
        self._register_default_experts()
        
        logger.info(f"ExpertRegistry initialized with {len(self.experts)} experts")
    
    def _load_experts(self):
        """Load experts from disk"""
        for expert_file in self.experts_dir.glob("*.json"):
            try:
                with expert_file.open("r") as f:
                    data = json.load(f)
                expert = AgentExpert.from_dict(data)
                self.experts[expert.expert_id] = expert
                logger.debug(f"Loaded expert: {expert.name} ({expert.domain.value})")
            except Exception as e:
                logger.error(f"Failed to load expert from {expert_file}: {e}")
    
    def _register_default_experts(self):
        """Register default built-in experts"""
        
        # Only register if not already loaded
        if "debug_expert" not in self.experts:
            self.register_expert(AgentExpert(
                expert_id="debug_expert",
                domain=ExpertDomain.DEBUGGING,
                name="Debug Expert",
                description="Specialist in debugging and troubleshooting code issues",
                system_prompt="""You are a debugging specialist. Your role:
- Analyze stack traces and error messages
- Identify root causes of bugs
- Suggest targeted fixes
- Use minimal context - focus only on relevant code
- Provide clear, actionable solutions""",
                tools=["read_file", "grep", "run_tests"],
                capabilities=["bug_fixing", "error_analysis", "troubleshooting"]
            ))
        
        if "scout_expert" not in self.experts:
            self.register_expert(AgentExpert(
                expert_id="scout_expert",
                domain=ExpertDomain.CODE_REVIEW,
                name="Scout Expert",
                description="Specialist in code exploration and reconnaissance",
                system_prompt="""You are a code scout. Your role:
- Explore codebases efficiently
- Identify key files and patterns
- Map out architecture
- Find relevant code sections
- Report findings concisely""",
                tools=["list_dir", "grep", "codebase_search", "read_file"],
                capabilities=["exploration", "reconnaissance", "mapping"]
            ))
        
        if "plan_expert" not in self.experts:
            self.register_expert(AgentExpert(
                expert_id="plan_expert",
                domain=ExpertDomain.TASK_BREAKDOWN,
                name="Planning Expert",
                description="Specialist in task breakdown and planning",
                system_prompt="""You are a planning specialist. Your role:
- Break down complex tasks into steps
- Identify dependencies
- Estimate effort and risks
- Create actionable plans
- Prioritize work items""",
                tools=["read_file", "codebase_search"],
                capabilities=["planning", "task_breakdown", "prioritization"]
            ))
        
        if "build_expert" not in self.experts:
            self.register_expert(AgentExpert(
                expert_id="build_expert",
                domain=ExpertDomain.REFACTORING,
                name="Build Expert",
                description="Specialist in implementing code changes",
                system_prompt="""You are a build specialist. Your role:
- Implement code changes precisely
- Follow established patterns
- Write clean, maintainable code
- Add appropriate tests
- Execute the plan accurately""",
                tools=["read_file", "write", "search_replace", "run_terminal_cmd"],
                capabilities=["implementation", "coding", "execution"]
            ))
        
        if "security_expert" not in self.experts:
            self.register_expert(AgentExpert(
                expert_id="security_expert",
                domain=ExpertDomain.SECURITY_AUDIT,
                name="Security Expert",
                description="Specialist in security analysis and auditing",
                system_prompt="""You are a security specialist. Your role:
- Identify security vulnerabilities
- Analyze authentication/authorization
- Check for common vulnerabilities (SQL injection, XSS, etc.)
- Review secrets management
- Suggest security improvements""",
                tools=["grep", "read_file", "codebase_search"],
                capabilities=["security_audit", "vulnerability_assessment", "threat_analysis"]
            ))
        
        if "performance_expert" not in self.experts:
            self.register_expert(AgentExpert(
                expert_id="performance_expert",
                domain=ExpertDomain.PERFORMANCE_ANALYSIS,
                name="Performance Expert",
                description="Specialist in performance optimization",
                system_prompt="""You are a performance specialist. Your role:
- Identify performance bottlenecks
- Analyze algorithmic complexity
- Suggest optimizations
- Profile code execution
- Improve efficiency""",
                tools=["read_file", "grep", "run_terminal_cmd"],
                capabilities=["optimization", "profiling", "performance_analysis"]
            ))
    
    def register_expert(self, expert: AgentExpert) -> None:
        """Register a new expert"""
        self.experts[expert.expert_id] = expert
        
        # Save to disk
        expert_file = self.experts_dir / f"{expert.expert_id}.json"
        with expert_file.open("w") as f:
            json.dump(expert.to_dict(), f, indent=2)
        
        logger.info(f"Registered expert: {expert.name} ({expert.domain.value})")
    
    def get_expert(self, expert_id: str) -> Optional[AgentExpert]:
        """Get expert by ID"""
        return self.experts.get(expert_id)
    
    def find_expert_for_task(self, task_type: str) -> Optional[AgentExpert]:
        """Find the best expert for a given task type"""
        for expert in self.experts.values():
            if expert.can_handle(task_type):
                logger.info(f"Selected expert {expert.name} for task: {task_type}")
                return expert
        
        logger.warning(f"No expert found for task type: {task_type}")
        return None
    
    def list_experts(self) -> List[Dict[str, Any]]:
        """List all registered experts"""
        return [
            {
                "expert_id": expert.expert_id,
                "name": expert.name,
                "domain": expert.domain.value,
                "description": expert.description,
                "capabilities": expert.capabilities
            }
            for expert in self.experts.values()
        ]
    
    def get_experts_by_domain(self, domain: ExpertDomain) -> List[AgentExpert]:
        """Get all experts for a specific domain"""
        return [
            expert for expert in self.experts.values()
            if expert.domain == domain
        ]


class ExpertTask:
    """
    Task to be executed by an expert agent
    """
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        description: str,
        context: Dict[str, Any],
        priority: int = 5,
        timeout_seconds: int = 300
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.context = context
        self.priority = priority
        self.timeout_seconds = timeout_seconds
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.assigned_expert: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.status: str = "pending"  # pending, in_progress, completed, failed
    
    def start(self, expert_id: str):
        """Mark task as started"""
        self.started_at = time.time()
        self.assigned_expert = expert_id
        self.status = "in_progress"
    
    def complete(self, result: Dict[str, Any]):
        """Mark task as completed"""
        self.completed_at = time.time()
        self.result = result
        self.status = "completed"
    
    def fail(self, error: str):
        """Mark task as failed"""
        self.completed_at = time.time()
        self.result = {"error": error}
        self.status = "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "context": self.context,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "assigned_expert": self.assigned_expert,
            "result": self.result,
            "status": self.status
        }


class ExpertOrchestrator:
    """
    Orchestrates expert agents to execute tasks
    
    Implements:
    - Task routing to appropriate experts
    - Context isolation per expert
    - Parallel execution when possible
    - Result aggregation
    """
    
    def __init__(self, registry: ExpertRegistry):
        self.registry = registry
        self.tasks: Dict[str, ExpertTask] = {}
        self.task_queue: List[str] = []
        
        logger.info("ExpertOrchestrator initialized")
    
    def submit_task(
        self,
        task_type: str,
        description: str,
        context: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Submit a task to be executed by an expert"""
        task_id = f"task_{int(time.time() * 1000)}"
        
        task = ExpertTask(
            task_id=task_id,
            task_type=task_type,
            description=description,
            context=context,
            priority=priority
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        self.task_queue.sort(key=lambda tid: self.tasks[tid].priority, reverse=True)
        
        logger.info(f"Submitted task: {task_id}, type={task_type}, priority={priority}")
        
        return task_id
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a specific task"""
        if task_id not in self.tasks:
            raise ValueError(f"Unknown task: {task_id}")
        
        task = self.tasks[task_id]
        
        # Find appropriate expert
        expert = self.registry.find_expert_for_task(task.task_type)
        
        if not expert:
            task.fail(f"No expert available for task type: {task.task_type}")
            logger.error(f"Task {task_id} failed: no expert found")
            return task.to_dict()
        
        # Start task
        task.start(expert.expert_id)
        start_time = time.time()
        logger.info(f"Executing task {task_id} with expert {expert.name}")
        
        try:
            # Here we would actually invoke the expert agent
            # For now, we'll simulate execution
            result = self._simulate_expert_execution(expert, task)
            task.complete(result)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Record agent performance metrics
            metrics_collector = _get_metrics_collector()
            if metrics_collector:
                metrics_collector.record_agent_metrics(
                    agent_id=expert.expert_id,
                    task_type=task.task_type,
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "success": True,
                        "tokens_used": result.get("tokens_used", 0),
                        "context_efficiency": result.get("context_efficiency", 0.0),
                        "expert_domain": expert.domain.value,
                        "task_description": task.description
                    }
                )
            
            logger.info(f"Task {task_id} completed successfully in {execution_time_ms:.2f}ms")
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            task.fail(str(e))
            
            # Record failure metrics
            metrics_collector = _get_metrics_collector()
            if metrics_collector:
                metrics_collector.record_agent_metrics(
                    agent_id=expert.expert_id,
                    task_type=task.task_type,
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "success": False,
                        "error": str(e),
                        "expert_domain": expert.domain.value,
                        "task_description": task.description
                    }
                )
            
            logger.error(f"Task {task_id} failed after {execution_time_ms:.2f}ms: {e}")
        
        return task.to_dict()
    
    def _simulate_expert_execution(
        self,
        expert: AgentExpert,
        task: ExpertTask
    ) -> Dict[str, Any]:
        """
        Simulate expert execution
        In production, this would invoke the actual agent
        """
        return {
            "expert_id": expert.expert_id,
            "expert_name": expert.name,
            "task_id": task.task_id,
            "execution_time": 1.5,
            "tokens_used": 2500,
            "context_efficiency": 0.95,
            "output": f"Task '{task.description}' completed by {expert.name}"
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task"""
        if task_id not in self.tasks:
            return {"error": f"Task {task_id} not found"}
        
        return self.tasks[task_id].to_dict()
    
    def list_pending_tasks(self) -> List[Dict[str, Any]]:
        """List all pending tasks"""
        return [
            self.tasks[tid].to_dict()
            for tid in self.task_queue
            if self.tasks[tid].status == "pending"
        ]

