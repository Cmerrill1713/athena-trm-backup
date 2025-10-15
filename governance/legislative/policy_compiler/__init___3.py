"""
NeuroForge Agent System
=======================
Self-improving collaborative AI architecture

Agents:
- Planner: Strategic task decomposition
- Executor: Task execution with tools
- Critic: Quality assessment and feedback
- Memory: Pattern storage and learning

Orchestrator: Coordinates the complete learning loop
"""

from .planner_agent import PlannerAgent, Plan, TaskStep
from .executor_agent import ExecutorAgent, ExecutionResult, PlanExecution, ExecutionStatus
from .critic_agent import CriticAgent, CriticReview, StepFeedback, QualityScore
from .memory_layer import MemoryLayer, StoredPlan, Learning
from .orchestrator import Orchestrator, OrchestratorResult

__all__ = [
    # Agents
    "PlannerAgent",
    "ExecutorAgent",
    "CriticAgent",
    "MemoryLayer",
    "Orchestrator",

    # Data structures
    "Plan",
    "TaskStep",
    "ExecutionResult",
    "PlanExecution",
    "ExecutionStatus",
    "CriticReview",
    "StepFeedback",
    "QualityScore",
    "StoredPlan",
    "Learning",
    "OrchestratorResult",
]

__version__ = "0.1.0"
