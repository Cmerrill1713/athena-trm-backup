#!/usr/bin/env python3
"""
Athena Master Control API
FastAPI server providing unified control over all subsystems.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from athena_master_orchestrator import AthenaMasterOrchestrator, SystemMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Athena Master Control API",
    description="Unified API for Governance, DGM, AGI Core, and Monitoring",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None


# Request Models
class TaskRequest(BaseModel):
    type: str
    payload: Optional[Dict] = None
    priority: Optional[str] = "normal"


class WorkflowRequest(BaseModel):
    workflow_type: str
    parameters: Optional[Dict] = None


class ExperimentRequest(BaseModel):
    experiment_config: str
    max_generations: Optional[int] = 10


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup."""
    global orchestrator
    logger.info("🚀 Starting Athena Master Control API")
    orchestrator = AthenaMasterOrchestrator()
    logger.info("✓ Orchestrator initialized")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "Athena Master Control API",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": orchestrator._list_capabilities() if orchestrator else [],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check of all subsystems."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    health = await orchestrator.health_check()
    
    if health['overall'] != 'healthy':
        return {"status": health['overall'], **health}
    
    return health


@app.get("/status")
async def get_status():
    """Get current system status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return orchestrator.get_system_status()


@app.post("/task")
async def process_task(task: TaskRequest, background_tasks: BackgroundTasks):
    """
    Process a task through the integrated system.
    
    Task Types:
    - self_improvement: Route to DGM
    - multi_agent: Route to AGI Core
    - research: Route to experiment framework
    - code: General code task
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    task_dict = {
        "type": task.type,
        "payload": task.payload or {},
        "priority": task.priority,
        "submitted_at": datetime.now().isoformat()
    }
    
    try:
        result = await orchestrator.process_task(task_dict)
        return result
    except Exception as e:
        logger.error(f"Task processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/{workflow_type}")
async def run_workflow(workflow_type: str, request: WorkflowRequest):
    """
    Run integrated end-to-end workflow.
    
    Workflows:
    - full_evolution: DGM → AGI Core → Governance → Deploy
    - research_experiment: Research → Validation → Report
    - multi_agent_task: AGI delegation → Governance
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        result = await orchestrator.run_integrated_workflow(
            workflow_type,
            **(request.parameters or {})
        )
        return result
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dgm/evolve")
async def trigger_dgm_evolution(max_generations: int = 10):
    """Trigger DGM evolution cycle."""
    if not orchestrator or not orchestrator.state.dgm_active:
        raise HTTPException(status_code=503, detail="DGM not available")
    
    try:
        results = await orchestrator.dgm_orchestrator.run_continuous_evolution(
            max_generations=max_generations
        )
        
        return {
            "status": "completed",
            "generations": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dgm/archive")
async def get_dgm_archive():
    """Get DGM agent archive."""
    if not orchestrator or not orchestrator.governance_adapter:
        raise HTTPException(status_code=503, detail="DGM not available")
    
    agents = orchestrator.governance_adapter.load_archive()
    
    return {
        "total": len(agents),
        "agents": agents[:100],  # Limit to 100 for API response
        "top_performers": orchestrator.governance_adapter.get_top_performers(n=10)
    }


@app.get("/dgm/verdicts")
async def get_dgm_verdicts(limit: int = 50):
    """Get recent DGM verdicts."""
    if not orchestrator or not orchestrator.verdict_validator:
        raise HTTPException(status_code=503, detail="Verdict system not available")
    
    verdicts = orchestrator.verdict_validator.get_verdict_history(limit=limit)
    stats = orchestrator.verdict_validator.get_approval_rate()
    
    return {
        "recent_verdicts": verdicts,
        "statistics": stats
    }


@app.post("/experiment/run")
async def run_experiment(request: ExperimentRequest):
    """Run DGM experiment."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        result = await orchestrator.run_integrated_workflow(
            'research_experiment',
            experiment_config=request.experiment_config
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get current system metrics."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return {
        "system_metrics": orchestrator.state.metrics,
        "dgm_metrics": {
            "generation": orchestrator.state.dgm_generation,
            "archive_size": len(orchestrator.governance_adapter.load_archive()) if orchestrator.governance_adapter else 0
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/governance/policies")
async def list_policies():
    """List active governance policies."""
    policies = [
        {
            "id": "SELF_MOD_001",
            "name": "Self-Modification Policy",
            "path": "governance/legislative/self_modification_policy.yaml",
            "status": "active"
        }
    ]
    
    return {"policies": policies}


@app.get("/capabilities")
async def list_capabilities():
    """List system capabilities."""
    if not orchestrator:
        return {"capabilities": []}
    
    return {
        "capabilities": orchestrator._list_capabilities(),
        "mode": orchestrator.state.mode.value,
        "subsystems_active": {
            "governance": orchestrator.state.governance_active,
            "dgm": orchestrator.state.dgm_active,
            "agi_core": orchestrator.state.agi_core_active,
            "monitoring": orchestrator.state.monitoring_active
        }
    }


# Main entry point
def start_api(host: str = "0.0.0.0", port: int = 8000):
    """Start the Athena API server."""
    logger.info(f"🌐 Starting Athena API on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Athena Master Control API")
    parser.add_argument('--host', default="0.0.0.0", help="API host")
    parser.add_argument('--port', type=int, default=8000, help="API port")
    
    args = parser.parse_args()
    
    start_api(host=args.host, port=args.port)

