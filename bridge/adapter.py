"""
NeuroForge Adapter
==================
Bridges NeuroForge (SwiftUI) ⇆ Universal-AI-Tools (UAT) ⇆ Athena
Single FastAPI adapter on :8014 that forwards to UAT/Athena backends
"""

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging

# Import rate limiter
try:
    from rate_limiter import RateLimiter
    rate_limiter = RateLimiter(requests_per_minute=60)
except ImportError:
    rate_limiter = None  # Graceful degradation

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment configuration
ENV = os.environ.get("ENV", "dev")
USE_MOCK = os.environ.get("USE_MOCK", "1") == "1"
UAT_BASE = os.environ.get("UAT_BASE", "http://127.0.0.1:8080")
ATHENA_BASE = os.environ.get("ATHENA_BASE", "http://127.0.0.1:8090")
UAT_TOKEN = os.environ.get("UAT_TOKEN", "")
ATH_TOKEN = os.environ.get("ATH_TOKEN", "")
BRIDGE_TOKEN = os.environ.get("BRIDGE_TOKEN", "")

# Security: Refuse to start with mock in production
if ENV == "prod" and USE_MOCK:
    raise RuntimeError("❌ Refusing to start: USE_MOCK=1 in prod environment")

ADAPTER_VERSION = "1.0.0"

app = FastAPI(
    title="NeuroForge Adapter",
    description="Bridges NeuroForge SwiftUI to UAT orchestration and Athena agents",
    version=ADAPTER_VERSION
)

# Enable CORS for SwiftUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for correlation ID and logging
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID and log requests"""
    # Get or generate correlation ID
    corr_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))

    # Log request
    start_time = time.perf_counter()

    # Process request
    response = await call_next(request)

    # Calculate latency
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    # Add headers
    response.headers["x-correlation-id"] = corr_id
    response.headers["x-adapter-version"] = ADAPTER_VERSION

    # Log response
    source = "mock" if USE_MOCK else "real"
    logger.info(
        f"{int(time.time())} {request.method} {request.url.path} "
        f"{response.status_code} {latency_ms}ms {source} {corr_id}"
    )

    return response

def auth_headers(token: str) -> Dict[str, str]:
    """Generate auth headers if token provided"""
    return {"Authorization": f"Bearer {token}"} if token else {}

def require_bridge_auth(req_token: Optional[str]):
    """Require bridge token only if BRIDGE_TOKEN is set and ENV is not dev"""
    if BRIDGE_TOKEN and ENV != "dev":
        if not req_token or req_token != BRIDGE_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid bridge token")

# Request/Response Models
class ChatRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None
    route: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    route: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    adapter: str
    uat: Dict[str, Any]
    athena: Dict[str, Any]
    timestamp: str

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check across all systems"""
    import datetime

    uat_status = {"status": "unknown", "error": None}
    athena_status = {"status": "unknown", "error": None}

    async with httpx.AsyncClient(timeout=5) as client:
        # Check UAT
        try:
            uat_resp = await client.get(f"{UAT_BASE}/health", headers=auth_headers(UAT_TOKEN))
            if uat_resp.status_code == 200:
                uat_status = uat_resp.json()
            else:
                uat_status = {"status": "error", "error": f"HTTP {uat_resp.status_code}"}
        except Exception as e:
            uat_status = {"status": "error", "error": str(e)}

        # Check Athena
        try:
            athena_resp = await client.get(f"{ATHENA_BASE}/health", headers=auth_headers(ATH_TOKEN))
            if athena_resp.status_code == 200:
                athena_status = athena_resp.json()
            else:
                athena_status = {"status": "error", "error": f"HTTP {athena_resp.status_code}"}
        except Exception as e:
            athena_status = {"status": "error", "error": str(e)}

    overall_status = "healthy" if (
        uat_status.get("status") in ["healthy", "ok"] and
        athena_status.get("status") in ["healthy", "ok"]
    ) else "degraded"

    return HealthResponse(
        status=overall_status,
        adapter="neuroforge-adapter-v1.0.0",
        uat=uat_status,
        athena=athena_status,
        timestamp=datetime.datetime.utcnow().isoformat()
    )

# === Traces (UAT owns telemetry) ===
@app.get("/traces")
async def traces(
    capability: Optional[str] = None,
    limit: int = 100,
    x_bridge_token: Optional[str] = Header(default=None)
):
    """Get execution traces from UAT orchestration"""
    require_bridge_auth(x_bridge_token)

    async with httpx.AsyncClient(timeout=10) as client:
        params = {"limit": limit}
        if capability:
            params["capability"] = capability

        resp = await client.get(f"{UAT_BASE}/traces", params=params, headers=auth_headers(UAT_TOKEN))
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Get detailed trace by ID from UAT"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{UAT_BASE}/trace/{trace_id}", headers=auth_headers(UAT_TOKEN))
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

# === Chat / Task to Athena ===
@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_route: Optional[str] = Header(default=None),
    x_bridge_token: Optional[str] = Header(default=None)
):
    """Forward chat requests to Athena agent system"""
    require_bridge_auth(x_bridge_token)

    # Rate limiting
    if rate_limiter:
        token = x_bridge_token or "anonymous"
        if not rate_limiter.is_allowed(token):
            raise HTTPException(status_code=429, detail="Rate limit exceeded (60 req/min)")

    # Use header override if provided, otherwise use request route
    route = x_route or request.route or "auto"

    # Prepare payload for Athena
    athena_payload = {
        "text": request.text,
        "context": request.context or {},
        "route": route
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{ATHENA_BASE}/chat",
            json=athena_payload,
            headers=auth_headers(ATH_TOKEN)
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        athena_response = resp.json()

        return ChatResponse(
            reply=athena_response.get("reply", ""),
            route=athena_response.get("route", route),
            metadata=athena_response.get("metadata", {})
        )

# === Agents (list/register) ===
@app.get("/agents")
async def agents():
    """Get available agents from Athena"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{ATHENA_BASE}/agents", headers=auth_headers(ATH_TOKEN))
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

# === Capabilities (UAT orchestration) ===
@app.get("/capabilities")
async def capabilities():
    """Get available capabilities from UAT"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{UAT_BASE}/capabilities", headers=auth_headers(UAT_TOKEN))
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

# === Stats (UAT orchestration) ===
@app.get("/stats")
async def stats():
    """Get orchestrator statistics from UAT"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{UAT_BASE}/stats", headers=auth_headers(UAT_TOKEN))
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.get("/stats/{capability}")
async def capability_stats(capability: str):
    """Get stats for specific capability from UAT"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{UAT_BASE}/stats/{capability}", headers=auth_headers(UAT_TOKEN))
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

# === Contract endpoint ===
@app.get("/contract")
async def contract():
    """Interop contract version and schema"""
    return {
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/traces",
            "/trace/{id}",
            "/chat",
            "/agents",
            "/capabilities",
            "/stats",
            "/contract"
        ],
        "fields": {
            "trace": {
                "id": "string",
                "capability": "string",
                "duration_ms": "int",
                "started_at": "float (unix timestamp)",
                "provider": "string | null",
                "score": "float | null"
            },
            "health": {
                "status": "string (healthy|degraded|unhealthy)",
                "adapter": "string",
                "uat": "object",
                "athena": "object",
                "timestamp": "string (iso8601)"
            }
        }
    }

# === Root endpoint ===
@app.get("/")
async def root():
    """Adapter information"""
    return {
        "service": "NeuroForge Adapter",
        "version": ADAPTER_VERSION,
        "description": "Bridges NeuroForge ⇆ UAT ⇆ Athena",
        "environment": ENV,
        "use_mock": USE_MOCK,
        "endpoints": {
            "health": "GET /health",
            "traces": "GET /traces",
            "trace": "GET /trace/{id}",
            "chat": "POST /chat",
            "agents": "GET /agents",
            "capabilities": "GET /capabilities",
            "stats": "GET /stats",
            "contract": "GET /contract"
        },
        "backends": {
            "uat": UAT_BASE,
            "athena": ATHENA_BASE
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8014)
