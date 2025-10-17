"""
AGI Service - FastAPI Integration

Integrates all AGI components into a production-ready service:
- Context Engineering (R&D Framework)
- Agent Experts
- Scout-Plan-Build Workflows
- Multi-Agent Delegation
- Governance Integration
- Sentry Monitoring
"""

import os
import sys
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge

# Import common ops utilities
sys.path.append(str(Path(__file__).parent.parent))
from common.ops import wire_tracing, attach_guardrails, add_health_endpoints

# Import AGI core components
from agi_core.context_engineering import ContextManager, ContextBundle, ContextMetrics, ContextStrategy
from agi_core.agent_experts import ExpertRegistry, ExpertOrchestrator, ExpertTask
from agi_core.workflows import ScoutPlanBuild, WorkflowOrchestrator, BackgroundWorkflow
from agi_core.delegation import AgentDelegator, MultiAgentCoordinator, DelegationStrategy

import logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AGI Core Service",
    version="1.0.0",
    description="Advanced Agent Intelligence Framework based on IndyDevDan's R&D patterns"
)

# Prometheus metrics
CONTEXT_OPERATIONS = Counter(
    "agi_context_operations_total",
    "Total context operations",
    ["operation", "strategy"]
)
CONTEXT_TOKENS = Histogram(
    "agi_context_tokens",
    "Context window token usage",
    buckets=[1000, 5000, 10000, 25000, 50000, 100000, 200000]
)
CONTEXT_EFFICIENCY = Gauge(
    "agi_context_efficiency",
    "Context efficiency score (0-1)"
)
WORKFLOW_EXECUTIONS = Counter(
    "agi_workflow_executions_total",
    "Total workflow executions",
    ["workflow_type", "status"]
)
WORKFLOW_DURATION = Histogram(
    "agi_workflow_duration_seconds",
    "Workflow execution duration",
    buckets=[1, 5, 10, 30, 60, 120, 300]
)
DELEGATION_TASKS = Counter(
    "agi_delegation_tasks_total",
    "Total delegated tasks",
    ["strategy", "status"]
)

# Initialize AGI components
STATE_DIR = Path(os.getenv("AGI_STATE_DIR", "./state/agi"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

context_manager = ContextManager(state_dir=STATE_DIR / "context")
context_bundle = ContextBundle(bundle_dir=STATE_DIR / "bundles")
expert_registry = ExpertRegistry(experts_dir=STATE_DIR / "experts")
expert_orchestrator = ExpertOrchestrator(registry=expert_registry)
workflow_orchestrator = WorkflowOrchestrator(state_dir=STATE_DIR / "workflows")
agent_delegator = AgentDelegator(state_dir=STATE_DIR / "delegation")
multi_agent_coordinator = MultiAgentCoordinator(delegator=agent_delegator)

# Wire operational concerns
wire_tracing(app, "agi-core")
attach_guardrails(app)
add_health_endpoints(app)

logger.info("AGI Core Service initialized")


# ============================================================================
# Request/Response Models
# ============================================================================

class ContextCreateRequest(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier")
    session_id: str = Field(..., description="Session identifier")
    max_tokens: int = Field(200000, description="Maximum context tokens")


class ContextReduceRequest(BaseModel):
    agent_id: str = Field(..., description="Agent to reduce context for")
    strategy: str = Field("auto", description="Reduction strategy")


class ContextPrimeRequest(BaseModel):
    agent_id: str = Field(..., description="Agent to prime")
    prime_type: str = Field(..., description="Type of priming (bug, feature, refactor, etc.)")
    context_data: Dict[str, Any] = Field({}, description="Context-specific data")


class DelegateTaskRequest(BaseModel):
    source_agent_id: str = Field(..., description="Source agent delegating work")
    task: Dict[str, Any] = Field(..., description="Task specification")
    specialist_type: Optional[str] = Field(None, description="Specialist type if needed")


class WorkflowExecuteRequest(BaseModel):
    workflow_type: str = Field(..., description="Type of workflow (scout_plan_build, background, etc.)")
    task_description: str = Field(..., description="What to accomplish")
    codebase_path: Optional[str] = Field(None, description="Path to codebase")
    context: Dict[str, Any] = Field({}, description="Additional context")


class ExpertTaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task")
    description: str = Field(..., description="Task description")
    context: Dict[str, Any] = Field({}, description="Task context")
    priority: int = Field(5, ge=1, le=10, description="Priority (1-10)")


class MultiAgentWorkflowRequest(BaseModel):
    workflow_id: str = Field(..., description="Unique workflow ID")
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks to coordinate")
    strategy: str = Field("parallel", description="Execution strategy (parallel, sequential)")


# ============================================================================
# Context Management Endpoints
# ============================================================================

@app.post("/context/create")
def create_context(request: ContextCreateRequest):
    """Create a new context window for an agent"""
    try:
        context = context_manager.create_context(
            agent_id=request.agent_id,
            session_id=request.session_id,
            max_tokens=request.max_tokens
        )
        
        CONTEXT_OPERATIONS.labels(operation="create", strategy="n/a").inc()
        
        return context.to_dict()
    except Exception as e:
        logger.error(f"Failed to create context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/context/reduce")
def reduce_context(request: ContextReduceRequest):
    """Reduce context for an agent using R&D Framework"""
    try:
        result = context_manager.reduce_context(
            agent_id=request.agent_id,
            strategy=request.strategy
        )
        
        CONTEXT_OPERATIONS.labels(operation="reduce", strategy="reduce").inc()
        CONTEXT_TOKENS.observe(result["new_tokens"])
        
        return result
    except Exception as e:
        logger.error(f"Failed to reduce context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/context/delegate")
def delegate_context(request: DelegateTaskRequest):
    """Delegate work to a new agent (D in R&D Framework)"""
    try:
        result = context_manager.delegate_to_agent(
            source_agent_id=request.source_agent_id,
            task=request.task,
            specialist_type=request.specialist_type
        )
        
        CONTEXT_OPERATIONS.labels(operation="delegate", strategy="delegate").inc()
        
        return result
    except Exception as e:
        logger.error(f"Failed to delegate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/context/prime")
def prime_context(request: ContextPrimeRequest):
    """Prime agent context with focused data"""
    try:
        context = context_manager.prime_context(
            agent_id=request.agent_id,
            prime_type=request.prime_type,
            context_data=request.context_data
        )
        
        CONTEXT_OPERATIONS.labels(operation="prime", strategy="prime").inc()
        
        return context.to_dict()
    except Exception as e:
        logger.error(f"Failed to prime context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/context/{agent_id}/status")
def get_context_status(agent_id: str):
    """Get context status for an agent"""
    return context_manager.get_context_status(agent_id)


# ============================================================================
# Context Bundle Endpoints
# ============================================================================

@app.post("/bundle/start")
def start_bundle(agent_id: str, session_id: str, initial_prompt: str):
    """Start tracking a context bundle"""
    try:
        bundle_id = context_bundle.start_bundle(
            agent_id=agent_id,
            session_id=session_id,
            initial_prompt=initial_prompt
        )
        return {"bundle_id": bundle_id}
    except Exception as e:
        logger.error(f"Failed to start bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bundle/{bundle_id}/record")
def record_operation(bundle_id: str, operation_type: str, details: Dict[str, Any] = Body(...)):
    """Record an operation in a bundle"""
    try:
        context_bundle.record_operation(bundle_id, operation_type, details)
        return {"status": "recorded"}
    except Exception as e:
        logger.error(f"Failed to record operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bundle/{bundle_id}/finalize")
def finalize_bundle(bundle_id: str):
    """Finalize and save a bundle"""
    try:
        bundle_file = context_bundle.finalize_bundle(bundle_id)
        return {"bundle_file": str(bundle_file)}
    except Exception as e:
        logger.error(f"Failed to finalize bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bundle/{bundle_id}/replay")
def replay_bundle(bundle_id: str, target_agent_id: str):
    """Replay a bundle to prime a new agent"""
    try:
        summary = context_bundle.replay_bundle(bundle_id, target_agent_id)
        return summary
    except Exception as e:
        logger.error(f"Failed to replay bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Expert Agent Endpoints
# ============================================================================

@app.get("/experts/list")
def list_experts():
    """List all registered expert agents"""
    return expert_registry.list_experts()


@app.get("/experts/{expert_id}")
def get_expert(expert_id: str):
    """Get details of a specific expert"""
    expert = expert_registry.get_expert(expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")
    return expert.to_dict()


@app.post("/experts/task/submit")
def submit_expert_task(request: ExpertTaskRequest):
    """Submit a task to be executed by an expert agent"""
    try:
        task_id = expert_orchestrator.submit_task(
            task_type=request.task_type,
            description=request.description,
            context=request.context,
            priority=request.priority
        )
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/experts/task/{task_id}/execute")
def execute_expert_task(task_id: str):
    """Execute a specific expert task"""
    try:
        result = expert_orchestrator.execute_task(task_id)
        return result
    except Exception as e:
        logger.error(f"Failed to execute task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/experts/task/{task_id}/status")
def get_expert_task_status(task_id: str):
    """Get status of an expert task"""
    return expert_orchestrator.get_task_status(task_id)


# ============================================================================
# Workflow Endpoints
# ============================================================================

@app.post("/workflow/execute")
def execute_workflow(request: WorkflowExecuteRequest):
    """Execute a workflow"""
    try:
        workflow_id = f"wf_{int(time.time() * 1000)}"
        
        # Create appropriate workflow
        if request.workflow_type == "scout_plan_build":
            if not request.codebase_path:
                raise HTTPException(status_code=400, detail="codebase_path required for scout_plan_build")
            
            workflow = ScoutPlanBuild(
                workflow_id=workflow_id,
                task_description=request.task_description,
                codebase_path=Path(request.codebase_path),
                constraints=request.context
            )
        elif request.workflow_type == "background":
            report_file = STATE_DIR / "workflows" / f"{workflow_id}_report.json"
            workflow = BackgroundWorkflow(
                workflow_id=workflow_id,
                task={"description": request.task_description, **request.context},
                report_file=report_file
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow type: {request.workflow_type}")
        
        # Register and execute
        workflow_orchestrator.register_workflow(workflow)
        
        start_time = time.time()
        result = workflow_orchestrator.execute_workflow(workflow_id)
        duration = time.time() - start_time
        
        # Update metrics
        WORKFLOW_EXECUTIONS.labels(
            workflow_type=request.workflow_type,
            status="success"
        ).inc()
        WORKFLOW_DURATION.observe(duration)
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        WORKFLOW_EXECUTIONS.labels(
            workflow_type=request.workflow_type,
            status="failed"
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/status")
def get_workflow_status(workflow_id: str):
    """Get status of a workflow"""
    return workflow_orchestrator.get_workflow_status(workflow_id)


# ============================================================================
# Multi-Agent Delegation Endpoints
# ============================================================================

@app.post("/delegation/task")
def delegate_task(
    agent_type: str,
    description: str,
    context: Dict[str, Any] = Body({}),
    strategy: str = "background",
    priority: int = 5
):
    """Delegate a task to an agent"""
    try:
        strategy_enum = DelegationStrategy(strategy)
        
        agent_id = agent_delegator.delegate_task(
            agent_type=agent_type,
            description=description,
            context=context,
            strategy=strategy_enum,
            priority=priority
        )
        
        DELEGATION_TASKS.labels(strategy=strategy, status="submitted").inc()
        
        return {"agent_id": agent_id}
        
    except Exception as e:
        logger.error(f"Task delegation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/delegation/agent/{agent_id}/status")
def get_agent_status(agent_id: str):
    """Get status of a delegated agent"""
    return agent_delegator.get_agent_status(agent_id)


@app.get("/delegation/task/{task_id}/result")
def get_task_result(task_id: str, wait: bool = False):
    """Get result of a delegated task"""
    result = agent_delegator.get_task_result(task_id, wait=wait)
    
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or not completed")
    
    return result.to_dict()


@app.get("/delegation/agents/active")
def list_active_agents():
    """List all active delegated agents"""
    return agent_delegator.list_active_agents()


# ============================================================================
# Multi-Agent Coordination Endpoints
# ============================================================================

@app.post("/coordination/workflow")
def coordinate_workflow(request: MultiAgentWorkflowRequest):
    """Coordinate a multi-agent workflow"""
    try:
        strategy_enum = DelegationStrategy(request.strategy)
        
        result = multi_agent_coordinator.coordinate_workflow(
            workflow_id=request.workflow_id,
            tasks=request.tasks,
            strategy=strategy_enum
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow coordination failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/coordination/workflow/{workflow_id}/status")
def get_coordination_status(workflow_id: str):
    """Get status of a coordinated workflow"""
    return multi_agent_coordinator.get_workflow_status(workflow_id)


@app.get("/coordination/workflow/{workflow_id}/results")
def aggregate_workflow_results(workflow_id: str):
    """Aggregate results from a coordinated workflow"""
    return multi_agent_coordinator.aggregate_results(workflow_id)


# ============================================================================
# Governance Integration
# ============================================================================

@app.post("/governance/report")
def report_to_governance(
    agent_id: str,
    metrics: Dict[str, Any],
    verdict: Optional[str] = None
):
    """Report agent metrics to governance system"""
    try:
        # This would integrate with your existing governance/orchestrator
        # For now, just log and return
        logger.info(f"Governance report from {agent_id}: {metrics}")
        
        # Update Prometheus metrics
        if "context_efficiency" in metrics:
            CONTEXT_EFFICIENCY.set(metrics["context_efficiency"])
        
        return {
            "status": "reported",
            "agent_id": agent_id,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Governance reporting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics and Monitoring
# ============================================================================

@app.get("/stats")
def get_stats():
    """Get AGI service statistics"""
    return {
        "active_contexts": len(context_manager.active_contexts),
        "registered_experts": len(expert_registry.experts),
        "active_workflows": len(workflow_orchestrator.workflows),
        "active_agents": len(agent_delegator.active_agents),
        "completed_tasks": len(agent_delegator.completed_tasks),
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGI_SERVICE_PORT", "8100"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

