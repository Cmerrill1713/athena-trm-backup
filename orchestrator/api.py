"""
FastAPI Shim for Orchestrator
==============================
REST API for capability routing (SwiftUI integration)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from router import run_capability
from scorer import get_stats, get_all_stats
from registry import list_capabilities, list_providers
from telemetry import query_traces


app = FastAPI(title="NeuroForge Orchestrator API", version="1.0.0")


class CapabilityRequest(BaseModel):
    """Request model for capability execution"""
    record: Dict[str, Any]
    params: Dict[str, Any] = {}


class CapabilityResponse(BaseModel):
    """Response model for capability execution"""
    output: Dict[str, Any]
    trace: Dict[str, Any]


@app.post("/capability/{name}", response_model=CapabilityResponse)
def execute_capability(name: str, req: CapabilityRequest):
    """
    Execute a capability

    Args:
        name: Capability name (summarize, plan, generate, reason)
        req: Request with record and params

    Returns:
        CapabilityResponse with output and trace
    """
    try:
        result = run_capability(name, req.record, req.params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "ok": True,
        "service": "orchestrator",
        "version": "1.0.0"
    }


@app.get("/capabilities")
def capabilities():
    """List all registered capabilities"""
    caps = list_capabilities()
    return {
        "capabilities": caps,
        "count": len(caps)
    }


@app.get("/capabilities/{name}/providers")
def capability_providers(name: str):
    """List providers for a capability"""
    providers = list_providers(name)
    return {
        "capability": name,
        "providers": providers,
        "count": len(providers)
    }


@app.get("/stats/{capability}")
def capability_stats(capability: str):
    """Get bandit statistics for a capability"""
    stats = get_stats(capability)
    return {
        "capability": capability,
        "providers": stats
    }


@app.get("/stats")
def all_stats():
    """Get all bandit statistics"""
    stats = get_all_stats()
    return {"stats": stats}


@app.get("/traces")
def traces(capability: Optional[str] = None, limit: int = 100):
    """Query execution traces"""
    results = query_traces(capability, limit)
    return {
        "traces": results,
        "count": len(results)
    }


# ============================================
# CLI Runner
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
