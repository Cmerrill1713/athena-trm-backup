"""
Governance Middleware for Athena Dev Daemon
Integrates devd with the governance control plane
"""
import httpx
import logging
from fastapi import HTTPException, Request
from typing import Dict, Any

logger = logging.getLogger(__name__)

GOVERNANCE_URL = "http://governance-orchestrator:9110"

async def governance_gate(kind: str, decision: Dict[str, Any], ctx: Dict[str, Any]):
    """
    Call governance /authorize before any expensive operation
    
    Args:
        kind: Type of operation (e.g., "dev.assist", "dev.search")
        decision: Estimated plan (route, topK, model_hint, cost_estimate)
        ctx: Context (user, files, intent, selection)
    
    Raises:
        HTTPException: If governance denies the request
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {
                "type": kind,
                "decision": decision,
                "context": ctx,
                "source": "athena-devd"
            }
            
            response = await client.post(
                f"{GOVERNANCE_URL}/authorize",
                json=payload
            )
            
            if response.status_code != 200:
                reason = response.text or "Governance denied request"
                logger.warning(f"Governance denied {kind}: {reason}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Governance denied: {reason}"
                )
            
            result = response.json()
            logger.info(f"Governance approved {kind}: {result.get('decision_id')}")
            return result
            
    except httpx.ConnectError:
        logger.error("Governance service unreachable - failing open (unsafe!)")
        # TODO: Make this configurable - fail closed in production
        return {"approved": True, "reason": "governance_unavailable"}
    
    except httpx.TimeoutException:
        logger.error("Governance timeout - failing open")
        return {"approved": True, "reason": "governance_timeout"}


def capture_editor_context(req: Any, request: Request) -> Dict[str, Any]:
    """
    Extract editor context from request for governance
    """
    return {
        "user": "christian",  # TODO: Extract from auth token
        "repo": req.repoRoot if hasattr(req, 'repoRoot') else "unknown",
        "file": req.file if hasattr(req, 'file') else None,
        "intent": req.intent if hasattr(req, 'intent') else "unknown",
        "selection_lines": (
            req.selection.get("end", 0) - req.selection.get("start", 0)
            if hasattr(req, 'selection') and req.selection
            else 0
        ),
        "diagnostics_count": len(req.diagnostics) if hasattr(req, 'diagnostics') else 0,
        "visible_files": len(req.visibleFiles) if hasattr(req, 'visibleFiles') else 0,
        "source_ip": request.client.host if request.client else "unknown"
    }


def estimate_plan(req: Any) -> Dict[str, Any]:
    """
    Estimate the cost/complexity of fulfilling this request
    """
    # Simple heuristic - can be improved with ML
    query_length = len(req.query) if hasattr(req, 'query') and req.query else 0
    has_diagnostics = len(req.diagnostics) > 0 if hasattr(req, 'diagnostics') else False
    
    # Estimate tokens (rough)
    estimated_prompt_tokens = query_length * 1.3  # chars to tokens
    estimated_context_tokens = 8 * 300  # max_snippets * max_lines_per_snippet / 4
    estimated_completion_tokens = 500  # typical answer
    
    total_tokens = estimated_prompt_tokens + estimated_context_tokens + estimated_completion_tokens
    
    return {
        "route": "router",  # Will go through intelligent router
        "topK": 8,  # Max snippets
        "model_hint": "auto",  # Let router decide
        "cost_estimate": {
            "tokens": int(total_tokens),
            "latency_ms_estimate": 2000,  # 2 seconds
            "complexity": "high" if has_diagnostics else "medium"
        },
        "requires_rag": True,
        "requires_llm": True
    }


async def emit_audit_event(event_type: str, data: Dict[str, Any]):
    """
    Emit audit event after operation completes
    
    Args:
        event_type: Event type (e.g., "athena.dev.assist.completed")
        data: Event payload
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{GOVERNANCE_URL}/audit",
                json={
                    "event_type": event_type,
                    "data": data,
                    "source": "athena-devd"
                }
            )
            logger.info(f"Audit event emitted: {event_type}")
    except Exception as e:
        logger.error(f"Failed to emit audit event: {e}")
        # Don't fail the request if audit fails

