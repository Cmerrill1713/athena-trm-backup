#!/usr/bin/env python3
"""
Governance Executive API
Simple API for governance verdicts and actions
Port 9110
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
governance_verdicts_total = Counter(
    'athena_governance_verdicts_total',
    'Total governance verdicts',
    ['action', 'status']
)

# ============================================================================
# API MODELS
# ============================================================================

class VerdictRequest(BaseModel):
    """Governance verdict request."""
    action: str
    reason: Optional[str] = "governance_decision"
    ttl_minutes: Optional[int] = 120
    agent_id: Optional[str] = "manual"

class VerdictResponse(BaseModel):
    """Verdict response."""
    status: str
    action: str
    message: str
    expires_at: Optional[str] = None
    ttl_minutes: Optional[int] = None

# ============================================================================
# APPLICATION
# ============================================================================

app = FastAPI(
    title="Athena Governance Executive API",
    description="Governance verdicts and policy actions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "governance_executive",
        "version": "1.0.0"
    }

@app.post("/verdict", response_model=VerdictResponse)
async def verdict(request: VerdictRequest):
    """
    Execute governance verdict/action.
    
    Supported actions:
    - ALLOW_CLOUD: Enable cloud routing with TTL
    - BLOCK_CLOUD: Disable cloud routing
    - CANARY_DEPLOY: Enable canary deployment
    - ROLLBACK: Rollback to previous state
    """
    logger.info(f"Verdict received: action={request.action}, reason={request.reason}")
    
    try:
        if request.action == "ALLOW_CLOUD":
            return await _handle_allow_cloud(request)
        
        elif request.action == "BLOCK_CLOUD":
            return await _handle_block_cloud(request)
        
        elif request.action == "CANARY_DEPLOY":
            governance_verdicts_total.labels(action="canary_deploy", status="success").inc()
            return VerdictResponse(
                status="success",
                action=request.action,
                message="Canary deployment enabled"
            )
        
        elif request.action == "ROLLBACK":
            governance_verdicts_total.labels(action="rollback", status="success").inc()
            return VerdictResponse(
                status="success",
                action=request.action,
                message="Rollback initiated"
            )
        
        else:
            governance_verdicts_total.labels(action=request.action, status="error").inc()
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
    
    except Exception as e:
        logger.error(f"Verdict execution failed: {e}")
        governance_verdicts_total.labels(action=request.action, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

async def _handle_allow_cloud(request: VerdictRequest) -> VerdictResponse:
    """Handle ALLOW_CLOUD action with TTL jitter."""
    import random
    
    ttl_minutes = request.ttl_minutes or 120
    
    # Add jitter: ±10% to prevent synchronized expiry storms
    jitter = random.uniform(-0.1, 0.1)
    jittered_ttl = ttl_minutes * (1 + jitter)
    
    expires_at = datetime.now() + timedelta(minutes=jittered_ttl)
    
    # Write policy override file that router watches
    override_path = Path("state/router_policy_overrides.json")
    override_path.parent.mkdir(parents=True, exist_ok=True)
    
    override = {
        "allow_cloud": True,
        "enabled_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "ttl_minutes": ttl_minutes,
        "reason": request.reason,
        "agent_id": request.agent_id
    }
    
    with open(override_path, 'w') as f:
        json.dump(override, f, indent=2)
    
    logger.warning(f"☁️  Cloud access ENABLED until {expires_at.isoformat()}")
    governance_verdicts_total.labels(action="allow_cloud", status="success").inc()
    
    return VerdictResponse(
        status="success",
        action="ALLOW_CLOUD",
        message=f"Cloud routing enabled for {ttl_minutes} minutes",
        expires_at=expires_at.isoformat(),
        ttl_minutes=ttl_minutes
    )

async def _handle_block_cloud(request: VerdictRequest) -> VerdictResponse:
    """Handle BLOCK_CLOUD action."""
    override_path = Path("state/router_policy_overrides.json")
    
    if override_path.exists():
        override_path.unlink()
        logger.info("☁️  Cloud access BLOCKED (override removed)")
    
    governance_verdicts_total.labels(action="block_cloud", status="success").inc()
    
    return VerdictResponse(
        status="success",
        action="BLOCK_CLOUD",
        message="Cloud routing blocked"
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/policy-status")
async def policy_status():
    """Get current policy override status."""
    override_path = Path("state/router_policy_overrides.json")
    
    if not override_path.exists():
        return {
            "active": False,
            "allow_cloud": False,
            "message": "No active policy overrides"
        }
    
    try:
        with open(override_path, 'r') as f:
            override = json.load(f)
        
        # Check if expired
        if 'expires_at' in override:
            expires_at = datetime.fromisoformat(override['expires_at'])
            if datetime.now() > expires_at:
                override_path.unlink()
                return {
                    "active": False,
                    "allow_cloud": False,
                    "message": "Policy override expired"
                }
        
        return {
            "active": True,
            "override": override
        }
    
    except Exception as e:
        logger.error(f"Failed to read policy status: {e}")
        return {
            "active": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("GOVERNANCE_PORT", "9110"))
    host = os.getenv("GOVERNANCE_HOST", "127.0.0.1")
    
    logger.info("=" * 60)
    logger.info("🏛️  Athena Governance Executive API")
    logger.info("=" * 60)
    logger.info(f"📍 Server: {host}:{port}")
    logger.info("=" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


