#!/usr/bin/env python3
"""
Athena Local-First Router

Enforces local-first model usage with MLX primary, Ollama fallback.
Provides governance-controlled access to ensure zero accidental cloud calls.

Policy: MLX → Ollama → Browser → Cloud (governed)
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from http import HTTPStatus

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import governance and routing components
from governance.policies.model_access import check_access_policy
from governance.routing.mlx_integration import inference_manager
from governance.observability.routing_metrics import routing_metrics

# Configuration
NO_CLOUD = os.getenv("ATHENA_NO_CLOUD", "0") == "1"
FAIL_CLOSED = os.getenv("ATHENA_FAIL_CLOSED", "1") == "1"
ALLOW_BROWSER = os.getenv("ATHENA_ALLOW_BROWSER", "1") == "1"
ALLOW_CLOUD = os.getenv("ATHENA_ALLOW_CLOUD", "0") == "1"

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://127.0.0.1:11434")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Athena Local-First Router",
    description="Local-first model routing with zero cloud leakage",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RouteRequest(BaseModel):
    """Request for model routing decision."""
    model_hint: Optional[str] = None
    prompt: str
    max_tokens: int = 512
    domain: str = "general"

class RouteResponse(BaseModel):
    """Router decision response."""
    route: str
    policy: str
    endpoint: Optional[str] = None
    backend: Optional[str] = None
    confidence: float = 0.0
    blocked_targets: list = []

class InferenceRequest(BaseModel):
    """Request for complete inference (route + execute)."""
    model_hint: Optional[str] = None
    prompt: str
    max_tokens: int = 512
    domain: str = "general"

class InferenceResponse(BaseModel):
    """Complete inference response."""
    routing: RouteResponse
    inference: Dict[str, Any]
    total_time: float
    backend_used: str
    local_only: bool

def check_local_backends() -> Dict[str, bool]:
    """Check availability of local inference backends."""
    backends = {}

    # Check MLX
    try:
        import mlx.core as mx
        backends["mlx"] = True
        logger.info("MLX backend available")
    except ImportError:
        backends["mlx"] = False
        logger.warning("MLX backend not available")

    # Check Ollama
    try:
        import requests
        response = requests.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=2.0)
        backends["ollama"] = response.status_code == 200
        if backends["ollama"]:
            logger.info("Ollama backend available")
        else:
            logger.warning("Ollama backend not responding")
    except Exception:
        backends["ollama"] = False
        logger.warning("Ollama backend check failed")

    # Check browser tools (placeholder)
    backends["browser"] = ALLOW_BROWSER

    return backends

@app.get("/health")
def health():
    """Health check with backend status."""
    backends = check_local_backends()

    return {
        "status": "healthy" if any(backends.values()) else "degraded",
        "policy": "local_first",
        "no_cloud": NO_CLOUD,
        "fail_closed": FAIL_CLOSED,
        "backends": backends,
        "cloud_blocked": NO_CLOUD,
        "governance_active": True
    }

@app.post("/route", response_model=RouteResponse)
def route(request: RouteRequest):
    """
    Route to appropriate local model backend.

    Priority: MLX → Ollama → Browser → Cloud (if governed)
    """
    backends = check_local_backends()
    blocked_targets = []

    # 1. Try MLX first (Apple Silicon optimized)
    if backends.get("mlx", False):
        # Check governance policy
        if check_access_policy("local_mlx", request.model_hint):
            logger.info(f"Routing to MLX: {request.domain}")
            return RouteResponse(
                route="mlx",
                policy="local_first",
                backend="mlx",
                confidence=0.9,
                blocked_targets=blocked_targets
            )
        else:
            blocked_targets.append("mlx")

    # 2. Try Ollama fallback
    if backends.get("ollama", False):
        if check_access_policy("local_ollama", request.model_hint):
            logger.info(f"Routing to Ollama: {request.domain}")
            return RouteResponse(
                route="ollama",
                policy="local_first",
                endpoint=OLLAMA_ENDPOINT,
                backend="ollama",
                confidence=0.8,
                blocked_targets=blocked_targets
            )
        else:
            blocked_targets.append("ollama")

    # 3. Browser tools (if allowed)
    if backends.get("browser", False):
        if check_access_policy("browser_tools", request.model_hint):
            logger.info(f"Routing to browser tools: {request.domain}")
            return RouteResponse(
                route="browser_tools",
                policy="local_first",
                backend="browser",
                confidence=0.5,
                blocked_targets=blocked_targets
            )
        else:
            blocked_targets.append("browser_tools")

    # 4. Cloud frontier (only if explicitly allowed AND governed)
    if ALLOW_CLOUD and not NO_CLOUD:
        if check_access_policy("cloud_frontier", request.model_hint):
            logger.warning(f"Routing to cloud (governed): {request.domain}")
            routing_metrics.record_cloud_attempt()
            return RouteResponse(
                route="cloud_frontier",
                policy="governed_fallback",
                backend="cloud",
                confidence=0.3,
                blocked_targets=blocked_targets
            )
        else:
            blocked_targets.append("cloud_frontier")
            routing_metrics.record_cloud_blocked()

    # Fail closed - no valid backend available
    if FAIL_CLOSED:
        logger.error(f"Fail-closed: No local backend available for {request.domain}")
        routing_metrics.record_routing_error("no_local_backend")
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="No local model backend available and cloud forbidden (fail-closed mode)."
        )

    # Best effort fallback
    logger.warning(f"Best-effort: No backend available for {request.domain}")
    return RouteResponse(
        route="none",
        policy="best_effort",
        confidence=0.0,
        blocked_targets=blocked_targets
    )

@app.post("/infer", response_model=InferenceResponse)
def infer(request: InferenceRequest):
    """
    Complete inference: route + execute.

    Uses local-first policy with governance enforcement.
    """
    start_time = time.time()

    # Get routing decision
    route_request = RouteRequest(
        model_hint=request.model_hint,
        prompt=request.prompt,
        max_tokens=request.max_tokens,
        domain=request.domain
    )

    routing_decision = route(route_request)

    # Execute inference based on routing decision
    if routing_decision.route == "mlx":
        # MLX inference
        try:
            inference_result = inference_manager.infer(
                athena_model_id=request.model_hint or "gpt-3.5-turbo",
                prompt=request.prompt,
                max_tokens=request.max_tokens
            )
            backend_used = "mlx"
        except Exception as e:
            logger.error(f"MLX inference failed: {e}")
            raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"MLX inference failed: {e}")

    elif routing_decision.route == "ollama":
        # Ollama inference
        try:
            inference_result = inference_manager.infer(
                athena_model_id=request.model_hint or "gpt-3.5-turbo",
                prompt=request.prompt,
                max_tokens=request.max_tokens
            )
            backend_used = "ollama"
        except Exception as e:
            logger.error(f"Ollama inference failed: {e}")
            raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Ollama inference failed: {e}")

    elif routing_decision.route == "browser_tools":
        # Browser tools (placeholder)
        inference_result = {
            "response": "Browser tools not yet implemented",
            "done": False,
            "inference_time": 0.1
        }
        backend_used = "browser"

    elif routing_decision.route == "cloud_frontier":
        # Cloud (should be blocked by governance, but just in case)
        raise HTTPException(
            HTTPStatus.FORBIDDEN,
            "Cloud inference blocked by local-first policy"
        )

    else:
        raise HTTPException(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "No inference backend available"
        )

    total_time = time.time() - start_time

    return InferenceResponse(
        routing=routing_decision,
        inference=inference_result,
        total_time=total_time,
        backend_used=backend_used,
        local_only=routing_decision.route in ["mlx", "ollama", "browser_tools"]
    )

@app.get("/backends")
def list_backends():
    """List available backends and their status."""
    backends = check_local_backends()

    return {
        "backends": backends,
        "policy": {
            "local_first": True,
            "no_cloud": NO_CLOUD,
            "fail_closed": FAIL_CLOSED,
            "allow_browser": ALLOW_BROWSER,
            "allow_cloud": ALLOW_CLOUD
        },
        "governance": {
            "active": True,
            "cloud_blocked": NO_CLOUD or not ALLOW_CLOUD
        }
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    port = int(os.getenv("ATHENA_ROUTER_PORT", "8099"))
    host = os.getenv("ATHENA_ROUTER_HOST", "127.0.0.1")

    logger.info("=" * 60)
    logger.info("🚀 Athena Local-First Router")
    logger.info("=" * 60)
    logger.info(f"📍 Server: {host}:{port}")
    logger.info(f"🔒 Local-first: {NO_CLOUD}")
    logger.info(f"🚪 Fail-closed: {FAIL_CLOSED}")
    logger.info(f"🌐 Allow browser: {ALLOW_BROWSER}")
    logger.info(f"☁️  Allow cloud: {ALLOW_CLOUD}")
    logger.info("=" * 60)

    uvicorn.run(app, host=host, port=port)
