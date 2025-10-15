"""
AI Team API Routes - UAT Integration
====================================
REST endpoints for AI team orchestration within UAT
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import core UAT team orchestrator
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.ai_team_orchestrator import SpecialistRole, get_team_orchestrator

router = APIRouter(prefix="/ai-team", tags=["AI Team"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TeamTaskRequest(BaseModel):
    """Request to delegate task to specialist"""
    task: str
    role: str  # "architect", "code_generator", "test_engineer", etc.
    context: Optional[Dict[str, Any]] = None


class CollaborativeRequest(BaseModel):
    """Request for full team collaboration"""
    project_spec: str


class TeamTaskResponse(BaseModel):
    """Response from specialist"""
    success: bool
    role: str
    model: str
    host: str
    response: str
    tokens: Optional[int] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health():
    """Health check for AI team"""
    return {"status": "healthy", "service": "ai-team"}


@router.get("/team")
async def get_team_info():
    """Get information about all specialists"""
    orchestrator = get_team_orchestrator()

    team_info = []
    for role, agents in orchestrator.specialists.items():
        for agent in agents:
            team_info.append({
                "role": role.value,
                "model": agent.model,
                "host": agent.host,
                "port": agent.port,
                "capabilities": agent.capabilities,
                "gpu_enabled": agent.gpu_required
            })

    return {
        "total_specialists": len(team_info),
        "specialists": team_info,
        "thompson_sampling_enabled": orchestrator.use_thompson
    }


@router.post("/delegate")
async def delegate_to_specialist(request: TeamTaskRequest):
    """
    Delegate task to appropriate specialist
    
    Examples:
    - Design: POST /ai-team/delegate {"task": "Design rate limiter", "role": "architect"}
    - Code: POST /ai-team/delegate {"task": "Implement X", "role": "code_generator"}
    - Test: POST /ai-team/delegate {"task": "Test Y", "role": "test_engineer"}
    """

    orchestrator = get_team_orchestrator()

    # Map role string to enum
    try:
        role = SpecialistRole(request.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {request.role}. Valid roles: {[r.value for r in SpecialistRole]}"
        )

    # Route to specialist (Thompson Sampling chooses if multiple available)
    result = await orchestrator.route_task(request.task, role, request.context)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    return TeamTaskResponse(
        success=True,
        role=role.value,
        model=result.get("model", ""),
        host=result.get("host", ""),
        response=result.get("response", ""),
        tokens=result.get("tokens")
    )


@router.post("/build")
async def collaborative_build(request: CollaborativeRequest):
    """
    Run full collaborative software development workflow
    
    Example:
    POST /ai-team/build {
        "project_spec": "Build a rate limiter using token bucket algorithm"
    }
    
    Workflow:
    1. ARCHITECT designs → qwen2.5:14b
    2. CODE GEN implements → qwen3-coder:30b on CODE MACHINE (GPU) ⚡
    3. TESTER generates tests → qwen3-coder:30b on CODE MACHINE (GPU) ⚡
    4. REVIEWER checks → qwen2.5:14b
    
    Thompson Sampling learns best routing for each phase!
    """

    orchestrator = get_team_orchestrator()
    results = await orchestrator.collaborative_build(request.project_spec)

    return {
        "project": request.project_spec,
        "workflow_complete": True,
        "phases": {
            "architecture": {
                "success": results["architecture"].get("success"),
                "tokens": results["architecture"].get("tokens", 0)
            },
            "code": {
                "success": results["code"].get("success"),
                "tokens": results["code"].get("tokens", 0),
                "host": results["code"].get("host")  # Shows which CODE machine
            },
            "tests": {
                "success": results["tests"].get("success"),
                "tokens": results["tests"].get("tokens", 0),
                "host": results["tests"].get("host")
            },
            "review": {
                "success": results["review"].get("success"),
                "tokens": results["review"].get("tokens", 0)
            }
        },
        "full_results": results
    }


@router.get("/stats")
async def get_team_stats():
    """Get Thompson Sampling statistics for team routing"""

    if not THOMPSON_AVAILABLE:
        return {"error": "Thompson Sampling not available"}

    # Import scoring stats
    from scorer import get_stats

    stats = {}
    for role in SpecialistRole:
        try:
            role_stats = get_stats(role.value)
            stats[role.value] = role_stats
        except:
            stats[role.value] = {"error": "No data yet"}

    return {
        "thompson_enabled": True,
        "role_stats": stats
    }

