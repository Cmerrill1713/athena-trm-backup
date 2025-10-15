"""
AI Team API - REST Interface for Multi-Agent Collaboration
==========================================================
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_team import AITeam, AgentRole, route_to_specialist

app = FastAPI(title="AI Team API", version="1.0.0")


# ============================================================================
# Request/Response Models
# ============================================================================

class TaskRequest(BaseModel):
    """Request to delegate a task"""
    task: str
    task_type: str  # "design", "implement", "test", "review", etc.
    context: Optional[Dict[str, Any]] = None


class CollaborativeProjectRequest(BaseModel):
    """Request for full collaborative workflow"""
    project_description: str
    include_docs: bool = True
    include_review: bool = True


class TaskResponse(BaseModel):
    """Response from task delegation"""
    success: bool
    agent_role: str
    model: str
    host: str
    response: str
    tokens: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "ai-team-api"}


@app.get("/team")
async def get_team():
    """Get information about all team members"""
    team = AITeam()

    return {
        "team_size": len(team.agents),
        "agents": [
            {
                "role": agent.role.value,
                "model": agent.model,
                "host": agent.host,
                "port": agent.port,
                "capabilities": agent.capabilities
            }
            for agent in team.agents.values()
        ]
    }


@app.post("/delegate", response_model=TaskResponse)
async def delegate_task(request: TaskRequest):
    """
    Delegate a task to the appropriate specialist

    Examples:
    - POST /delegate {"task": "Design a rate limiter", "task_type": "design"}
    - POST /delegate {"task": "Implement Thompson Sampling", "task_type": "implement"}
    - POST /delegate {"task": "Generate tests for X", "task_type": "test"}
    """

    result = await route_to_specialist(
        task=request.task,
        task_type=request.task_type
    )

    if result.get("success"):
        return TaskResponse(
            success=True,
            agent_role=request.task_type,
            model=result.get("model", ""),
            host=result.get("host", ""),
            response=result.get("response", ""),
            tokens=result.get("tokens")
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Task failed")
        )


@app.post("/collaborate")
async def collaborative_project(request: CollaborativeProjectRequest):
    """
    Run full collaborative workflow:
    Architect → Code Gen → Tester → Reviewer → Documenter

    Example:
    POST /collaborate {
        "project_description": "Build a rate limiter using token bucket",
        "include_docs": true,
        "include_review": true
    }
    """

    team = AITeam()
    results = await team.collaborative_workflow(request.project_description)

    return {
        "project": request.project_description,
        "workflow_complete": True,
        "phases": {
            "architecture": {
                "success": results["architecture"].get("success"),
                "preview": results["architecture"].get("response", "")[:200]
            },
            "implementation": {
                "success": results["implementation"].get("success"),
                "preview": results["implementation"].get("response", "")[:200]
            },
            "tests": {
                "success": results["tests"].get("success"),
                "preview": results["tests"].get("response", "")[:200]
            },
            "review": {
                "success": results.get("review", {}).get("success"),
                "preview": results.get("review", {}).get("response", "")[:200]
            },
            "documentation": {
                "success": results.get("documentation", {}).get("success"),
                "preview": results.get("documentation", {}).get("response", "")[:200]
            }
        },
        "full_results": results
    }


@app.get("/history")
async def get_task_history():
    """Get history of delegated tasks"""
    team = AITeam()
    return {
        "total_tasks": len(team.task_history),
        "tasks": team.task_history[-20:]  # Last 20 tasks
    }


@app.get("/agents/{role}")
async def get_agent_info(role: str):
    """Get information about a specific agent"""
    team = AITeam()

    try:
        agent_role = AgentRole(role)
        agent = team.agents[agent_role]

        return {
            "role": agent.role.value,
            "model": agent.model,
            "host": agent.host,
            "port": agent.port,
            "capabilities": agent.capabilities,
            "endpoint": agent.endpoint,
            "prompt_preview": agent.prompt[:200] + "..."
        }
    except (ValueError, KeyError):
        raise HTTPException(status_code=404, detail=f"Agent role '{role}' not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
