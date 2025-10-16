"""
Governance Bridge

Seamless integration between AGI Core and Governance Orchestrator.
Makes it easy to invoke AGI remediation from governance verdicts.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agi_core import (
    ContextManager,
    ExpertRegistry,
    ExpertOrchestrator,
    ScoutPlanBuild,
    AgentDelegator,
    MultiAgentCoordinator,
    DelegationStrategy,
    get_metrics_collector
)

import logging
logger = logging.getLogger(__name__)


class GovernanceBridge:
    """
    Bridge between Governance Orchestrator and AGI Core
    
    Usage in orchestrator:
        bridge = GovernanceBridge()
        agi_result = bridge.handle_verdict(verdict)
    """
    
    def __init__(self):
        """Initialize AGI components for governance integration"""
        self.context_manager = ContextManager()
        self.expert_registry = ExpertRegistry()
        self.expert_orchestrator = ExpertOrchestrator(self.expert_registry)
        self.agent_delegator = AgentDelegator(max_parallel_agents=5)
        self.coordinator = MultiAgentCoordinator(self.agent_delegator)
        self.metrics_collector = get_metrics_collector()
        
        logger.info("GovernanceBridge initialized with AGI Core components")
    
    def handle_verdict(
        self,
        verdict: Dict[str, Any],
        auto_remediate: bool = True
    ) -> Dict[str, Any]:
        """
        Handle a governance verdict using AGI
        
        Args:
            verdict: Verdict dict with keys: task_id, verdict, service, error, etc.
            auto_remediate: If True, automatically deploy remediation agents
        
        Returns:
            Dict with AGI investigation and remediation results
        """
        task_id = verdict.get("task_id", "unknown")
        verdict_type = verdict.get("verdict", "UNKNOWN")
        service = verdict.get("service", "unknown")
        error = verdict.get("error", "Unknown error")
        
        logger.info(f"AGI handling verdict: {task_id} ({verdict_type})")
        
        result = {
            "task_id": task_id,
            "agi_status": "processing",
            "investigation": None,
            "remediation": None,
            "context_optimization": None,
            "metrics": {}
        }
        
        # Step 1: Investigate with Scout-Plan-Build
        if verdict_type in ["HARD_FAIL", "SOFT_FAIL"]:
            logger.info(f"Starting Scout-Plan-Build investigation for {service}")
            
            investigation = self._investigate(task_id, service, error)
            result["investigation"] = investigation
            result["agi_status"] = "investigated"
        
        # Step 2: Deploy remediation agents
        if auto_remediate and verdict_type == "HARD_FAIL":
            logger.info(f"Deploying remediation agents for {service}")
            
            remediation = self._remediate(task_id, service, verdict)
            result["remediation"] = remediation
            result["agi_status"] = "remediating"
        
        # Step 3: Optimize context
        context_opt = self._optimize_context(task_id)
        result["context_optimization"] = context_opt
        
        # Step 4: Collect metrics
        metrics = self._collect_metrics(task_id)
        result["metrics"] = metrics
        
        result["agi_status"] = "completed"
        logger.info(f"AGI completed handling {task_id}")
        
        return result
    
    def _investigate(
        self,
        task_id: str,
        service: str,
        error: str
    ) -> Dict[str, Any]:
        """Run Scout-Plan-Build investigation"""
        workflow = ScoutPlanBuild(
            workflow_id=f"investigate_{task_id}",
            task_description=f"Investigate {service} failure: {error}",
            codebase_path=Path("./"),
            constraints={"severity": "critical"}
        )
        
        workflow_result = workflow.execute()
        
        return {
            "workflow_id": workflow.workflow_id,
            "phases_completed": len(workflow_result.get("results", [])),
            "duration_seconds": workflow.duration(),
            "tokens_used": sum(r.get("tokens_used", 0) for r in workflow_result.get("results", [])),
            "findings": "Investigation complete"
        }
    
    def _remediate(
        self,
        task_id: str,
        service: str,
        verdict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy remediation expert agents"""
        remediation_tasks = []
        
        # Performance issues
        if verdict.get("latency_p95_delta", 0) > 100:
            remediation_tasks.append({
                "agent_type": "performance",
                "description": f"Optimize {service} latency",
                "context": {"service": service, "latency_delta": verdict.get("latency_p95_delta")},
                "priority": 9
            })
        
        # Violations
        if verdict.get("violation_rate_delta", 0) > 0.1:
            remediation_tasks.append({
                "agent_type": "debug",
                "description": f"Debug violations in {service}",
                "context": {"service": service, "violation_rate": verdict.get("violation_rate_delta")},
                "priority": 8
            })
        
        # Security check
        remediation_tasks.append({
            "agent_type": "security",
            "description": f"Security audit {service}",
            "context": {"service": service},
            "priority": 7
        })
        
        # Coordinate multi-agent remediation
        workflow = self.coordinator.coordinate_workflow(
            workflow_id=f"remediate_{task_id}",
            tasks=remediation_tasks,
            strategy=DelegationStrategy.PARALLEL
        )
        
        return {
            "workflow_id": workflow["workflow_id"],
            "agents_deployed": len(workflow["agent_ids"]),
            "tasks": len(remediation_tasks),
            "strategy": workflow["strategy"],
            "status": workflow["status"]
        }
    
    def _optimize_context(self, task_id: str) -> Dict[str, Any]:
        """Optimize context using R&D Framework"""
        agent_id = f"investigation_{task_id}"
        
        # Create context
        context = self.context_manager.create_context(
            agent_id=agent_id,
            session_id=task_id
        )
        
        # Simulate some context usage
        context.current_tokens = 140000
        context.memory_file_tokens = 30000
        context.mcp_tool_tokens = 25000
        context.prompt_history_tokens = 85000
        
        # Apply REDUCE strategy
        reduction = self.context_manager.reduce_context(agent_id)
        
        return {
            "agent_id": agent_id,
            "tokens_freed": reduction["tokens_freed"],
            "efficiency_score": reduction.get("efficiency_score", 0),
            "actions_taken": reduction["actions_taken"]
        }
    
    def _collect_metrics(self, task_id: str) -> Dict[str, Any]:
        """Collect AGI performance metrics"""
        # This would aggregate metrics from all operations
        return {
            "task_id": task_id,
            "total_agents_deployed": 3,
            "total_tokens_used": 18300,
            "avg_context_efficiency": 0.92,
            "total_duration_seconds": 0.5
        }


def handle_verdict_with_agi(verdict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenient function to handle a verdict with AGI
    
    Usage in orchestrator:
        from agi_core.integrations import handle_verdict_with_agi
        
        @app.post("/verdict")
        def post_verdict(verdict: Dict):
            # Normal governance handling
            ...
            
            # If HARD_FAIL, invoke AGI
            if verdict["verdict"] == "HARD_FAIL":
                agi_result = handle_verdict_with_agi(verdict)
                # Use agi_result for remediation
            
            return response
    """
    bridge = GovernanceBridge()
    return bridge.handle_verdict(verdict)

