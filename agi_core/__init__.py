"""
AGI Core - Advanced Agent Intelligence Framework
Based on IndyDevDan's R&D Framework and Context Engineering Patterns

This module provides:
- R&D (Reduce & Delegate) context management
- Context bundles for agent audit trails
- Agent experts framework
- Scout-Plan-Build workflow patterns
- Multi-agent delegation systems
"""

from .context_engineering import ContextManager, ContextBundle
from .agent_experts import AgentExpert, ExpertRegistry, ExpertDomain, ExpertOrchestrator
from .workflows import ScoutPlanBuild, AgentWorkflow
from .delegation import AgentDelegator, BackgroundAgent, MultiAgentCoordinator, DelegationStrategy
from .evaluation_metrics import (
    MetricsCollector,
    PerformanceMetrics,
    OptimizationResult,
    UtilityFunction,
    get_metrics_collector,
    measure_execution
)
from .stop_optimizer import (
    STOPOptimizer,
    OptimizationStrategy,
    OptimizationCandidate,
    optimize_function,
    LLMInterface
)

__all__ = [
    # Context Engineering
    "ContextManager",
    "ContextBundle",
    # Agent Experts
    "AgentExpert",
    "ExpertRegistry",
    "ExpertDomain",
    "ExpertOrchestrator",
    # Workflows
    "ScoutPlanBuild",
    "AgentWorkflow",
    # Delegation
    "AgentDelegator",
    "BackgroundAgent",
    "MultiAgentCoordinator",
    "DelegationStrategy",
    # Metrics
    "MetricsCollector",
    "PerformanceMetrics",
    "OptimizationResult",
    "UtilityFunction",
    "get_metrics_collector",
    "measure_execution",
    # STOP Optimizer
    "STOPOptimizer",
    "OptimizationStrategy",
    "OptimizationCandidate",
    "optimize_function",
    "LLMInterface",
]

__version__ = "1.0.0"

