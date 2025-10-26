"""
AGI Proxy for Athena Router
Routes complex tasks to AGI Core for Scout-Plan-Build execution
"""
import os
import time
import logging
import httpx
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

AGI_URL = os.getenv("AGI_URL", "http://athena-agi-core:8000")
AGI_TIMEOUT = 60.0

router = APIRouter()


class AGIExecuteRequest(BaseModel):
    """AGI execution request"""
    objective: str
    context: Dict[str, Any] = {}
    tools: List[str] = []
    max_steps: int = 12


@router.post("/agi/execute")
async def agi_execute(payload: AGIExecuteRequest = Body(...)):
    """
    Execute complex task via AGI Core
    
    Routes to AGI Core's Scout-Plan-Build system for autonomous task execution
    """
    t0 = time.time()
    
    try:
        logger.info(f"AGI execute: {payload.objective}")
        
        # Hardened timeout: 15s connect, 45s read
        timeout = httpx.Timeout(15.0, read=45.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{AGI_URL}/api/execute",
                json=payload.dict()
            )
            response.raise_for_status()
            data = response.json()
        
        return {
            "t_s": round(time.time() - t0, 3),
            "task_id": data.get("task_id"),
            "status": data.get("status"),
            "result": data.get("result"),
            "trace": data.get("trace", [])
        }
    
    except httpx.TimeoutException:
        logger.error("AGI execution timed out")
        raise HTTPException(
            status_code=504,
            detail="AGI execution timed out (>45s)"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"AGI returned error: {e.response.status_code}")
        raise HTTPException(
            status_code=502,
            detail=f"AGI Core error: {e.response.text}"
        )
    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to AGI Core: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AGI Core unavailable at {AGI_URL}"
        )
    except Exception as e:
        logger.error(f"AGI proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agi/health")
async def agi_health():
    """Check AGI Core health"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{AGI_URL}/health")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "agi_url": AGI_URL
        }
