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
from .agent_experts import AgentExpert, ExpertRegistry
from .workflows import ScoutPlanBuild, AgentWorkflow
from .delegation import AgentDelegator, BackgroundAgent
from .evaluation_metrics import (
    MetricsCollector,
    PerformanceMetrics,
    OptimizationResult,
    UtilityFunction,
    get_metrics_collector,
    measure_execution
)

__all__ = [
    "ContextManager",
    "ContextBundle",
    "AgentExpert",
    "ExpertRegistry",
    "ScoutPlanBuild",
    "AgentWorkflow",
    "AgentDelegator",
    "BackgroundAgent",
    "MetricsCollector",
    "PerformanceMetrics",
    "OptimizationResult",
    "UtilityFunction",
    "get_metrics_collector",
    "measure_execution",
]

__version__ = "1.0.0"

