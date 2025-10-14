"""
NeuroForge Adapter
==================
Bridges NeuroForge (SwiftUI) ⇆ Universal-AI-Tools (UAT) ⇆ Athena
Single FastAPI adapter on :8014 that forwards to UAT/Athena backends
"""

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
import httpx
import os
import sys
import time
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .schemas import ApiChatInput
import logging

# Prometheus metrics
from prometheus_client import Counter, Histogram

# Feedback metrics
feedback_received = Counter("feedback_events_total", "User feedback events", ["signal_type"])
feedback_processing_time = Histogram("feedback_processing_seconds", "Time to process feedback", buckets=[0.001, 0.005, 0.01, 0.05, 0.1])

# Import logs endpoint
try:
    from logs_endpoint import router as logs_router
    LOGS_ENDPOINT_AVAILABLE = True
except ImportError:
    LOGS_ENDPOINT_AVAILABLE = False

# Bandit feedback support
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../AI-Projects/universal-ai-tools"))
    from bandit.policy import record_feedback
    BANDIT_AVAILABLE = True
except ImportError:
    BANDIT_AVAILABLE = False
    def record_feedback(variant: str, reward: float):
        pass  # No-op if bandit not available
    logs_router = None

# Database connection for evaluation data
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")

def get_evaluation_scores(interaction_id: str) -> dict:
    """Fetch evaluation scores for an interaction."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get average scores for this interaction
            cur.execute("""
                SELECT
                    AVG(CASE WHEN metric = 'helpfulness' THEN score END) as helpfulness,
                    AVG(CASE WHEN metric = 'factuality' THEN score END) as factuality,
                    AVG(CASE WHEN metric = 'clarity' THEN score END) as clarity
                FROM eval_results
                WHERE interaction_id = %s
            """, (interaction_id,))
            row = cur.fetchone()
            if row and row['helpfulness']:
                return {
                    'helpfulness': float(row['helpfulness']),
                    'factuality': float(row['factuality']),
                    'clarity': float(row['clarity'])
                }
    except Exception as e:
        print(f"Evaluation fetch error: {e}")
    return None

# Add parent directory to path for common imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ops import (
    wire_tracing,
    attach_guardrails,
    install_graceful_shutdown,
    add_health_endpoints,
)
from common.secrets import load_secret

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

# Load tokens (keychain-first, env fallback)
UAT_TOKEN = load_secret("uat_token", "UAT_TOKEN", "")
ATH_TOKEN = load_secret("ath_token", "ATH_TOKEN", "")
BRIDGE_TOKEN = load_secret("bridge_token", "BRIDGE_TOKEN", "")

# Security: Refuse to start with mock in production
if ENV == "prod" and USE_MOCK:
    raise RuntimeError("❌ Refusing to start: USE_MOCK=1 in prod environment")

ADAPTER_VERSION = "1.0.0"

app = FastAPI(
    title="NeuroForge Adapter",
    description="Bridges NeuroForge SwiftUI to UAT orchestration and Athena agents",
    version=ADAPTER_VERSION
)

# 2a) Log raw body for any 422 to find old routes/models instantly
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    # log the bad request shape (redact if needed)
    print(f"[422] {request.url.path} body={body.decode('utf-8', 'ignore')}")
    return await request_validation_exception_handler(request, exc)

# Tier 4: Production hardening
add_health_endpoints(app)  # /live, /ready for K8s-style probes
wire_tracing(app, service_name="neuroforge-bridge")  # OTLP tracing
attach_guardrails(
    app,
    per_ip_rate=os.getenv("RATE_LIMIT", "100/minute"),
    max_body_mb=int(os.getenv("MAX_BODY_MB", "5")),
    request_timeout_s=int(os.getenv("REQ_TIMEOUT_S", "30"))
)
install_graceful_shutdown(app, drain_seconds=int(os.getenv("DRAIN_S", "5")))

# Include logs endpoint if available
if LOGS_ENDPOINT_AVAILABLE and logs_router:
    app.include_router(logs_router)
    logger.info("✅ Logs endpoint enabled at /ops/logs")

# Enable CORS for SwiftUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your.app"],
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["Authorization","Content-Type"],
)

# Self-identification (make it impossible to lie about who answered)
import socket
import sys
import subprocess

BOOT_TS = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
PID = os.getpid()
CWD = os.getcwd()
PY = sys.executable
HOST = socket.gethostname()
try:
    GIT = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                   stderr=subprocess.DEVNULL, text=True).strip()
except:
    GIT = "nogit"

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

    # Add headers (with self-identification)
    response.headers["x-correlation-id"] = corr_id
    response.headers["x-adapter-version"] = ADAPTER_VERSION
    response.headers["x-service"] = "neuroforge-bridge"
    response.headers["x-pid"] = str(PID)
    response.headers["x-cwd"] = CWD
    response.headers["x-py"] = PY
    response.headers["x-build"] = GIT
    response.headers["x-boot"] = BOOT_TS
    response.headers["x-mode"] = "mock" if USE_MOCK else "real"

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

def require_auth(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth.split(" ")[1]
    if token != BRIDGE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

# Request/Response Models - imported from schemas.py

# Removed old ChatRequest model

class ChatOut(BaseModel):
    """Output model with ok flag"""
    ok: bool = True
    reply: str
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    request_id: Optional[str] = None
    status: Optional[str] = "success"

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

class FeedbackRequest(BaseModel):
    interaction_id: str
    thumbs_up: Optional[bool] = None
    thumbs_down: Optional[bool] = None
    regenerate: Optional[bool] = None
    edit_resend: Optional[bool] = None

class FeedbackResponse(BaseModel):
    ok: bool
    message: str
    reward: Optional[float] = None

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

@app.get("/api/probe/e2e")
async def probe_e2e():
    """
    QA frontend probe endpoint - simplified health check
    Returns minimal status for QA mode compatibility
    """
    import datetime
    import time as time_mod
    
    start = time_mod.time()
    results = []
    
    async with httpx.AsyncClient(timeout=3) as client:
        # Check Bridge itself
        results.append({
            "service": "bridge",
            "url": "http://127.0.0.1:8014",
            "status": "pass",
            "http": 200,
            "latency_ms": 0.1,
            "note": "Bridge adapter healthy",
            "critical": True
        })
        
        # Check UAT
        try:
            uat_resp = await client.get(f"{UAT_BASE}/health", headers=auth_headers(UAT_TOKEN))
            results.append({
                "service": "uat",
                "url": UAT_BASE,
                "status": "pass" if uat_resp.status_code == 200 else "fail",
                "http": uat_resp.status_code,
                "latency_ms": uat_resp.elapsed.total_seconds() * 1000,
                "note": "UAT service" if uat_resp.status_code == 200 else f"HTTP {uat_resp.status_code}",
                "critical": True
            })
        except Exception as e:
            results.append({
                "service": "uat",
                "url": UAT_BASE,
                "status": "fail",
                "http": 0,
                "latency_ms": 0,
                "note": str(e)[:50],
                "critical": True
            })
        
        # Check Athena
        try:
            ath_resp = await client.get(f"{ATHENA_BASE}/health", headers=auth_headers(ATH_TOKEN))
            results.append({
                "service": "athena",
                "url": ATHENA_BASE,
                "status": "pass" if ath_resp.status_code == 200 else "fail",
                "http": ath_resp.status_code,
                "latency_ms": ath_resp.elapsed.total_seconds() * 1000,
                "note": "Athena service" if ath_resp.status_code == 200 else f"HTTP {ath_resp.status_code}",
                "critical": True
            })
        except Exception as e:
            results.append({
                "service": "athena",
                "url": ATHENA_BASE,
                "status": "fail",
                "http": 0,
                "latency_ms": 0,
                "note": str(e)[:50],
                "critical": True
            })
    
    duration_ms = (time_mod.time() - start) * 1000
    
    # Count statuses
    counts = {
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "warn": sum(1 for r in results if r["status"] == "warn"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "unused": sum(1 for r in results if r["status"] == "unused"),
    }
    
    return {
        "started_at": datetime.datetime.utcnow().isoformat(),
        "duration_ms": duration_ms,
        "total_services": len(results),
        "counts": counts,
        "services": results
    }

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

# SwiftUI compatibility model
class ChatTask(BaseModel):
    kind: Optional[str] = None
    text: str
    imageBase64: Optional[str] = None

@app.middleware("http")
async def auth_guard(request: Request, call_next):
    """Authentication middleware - dev off, prod on"""
    REQUIRE_AUTH = os.getenv("BRIDGE_AUTH", "false").lower() == "true"
    TOKEN = os.getenv("BRIDGE_TOKEN", "")
    
    if REQUIRE_AUTH and request.url.path.startswith("/api/"):
        hdr = request.headers.get("Authorization", "")
        tok = hdr.replace("Bearer ", "", 1)
        if not TOKEN or tok != TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")
    
    return await call_next(request)

@app.post("/api/chat")
async def api_chat(req: Request, body: ApiChatInput):
    print(f"DEBUG: api_chat called with body={body}")
    require_auth(req)
    content = body.content()
    print(f"DEBUG: content='{content}'")
    if not content:
        raise HTTPException(422, detail="Either 'text' or 'message' is required")
    payload = {"message": content}  # canonical field to Athena
    headers = {"Authorization": f"Bearer {ATH_TOKEN}"}
    async with httpx.AsyncClient(timeout=30) as cx:
        r = await cx.post(ATH_URL, json=payload, headers=headers)
        # Log helpful context when debugging 422s upstream
        if r.status_code >= 400:
            log.warning("Upstream error %s: %s", r.status_code, r.text[:512])
        r.raise_for_status()
        data = r.json()
    return {"ok": True, "reply": data.get("reply",""), "variant": data.get("variant")}

# Removed old /chat endpoint to avoid conflicts

    # Rate limiting
    if rate_limiter:
        token = x_bridge_token or "anonymous"
        if not rate_limiter.is_allowed(token):
            raise HTTPException(status_code=429, detail="Rate limit exceeded (60 req/min)")

    # Try to use the sophisticated unified orchestrator
    try:
        # Import the advanced orchestration system
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AI-Projects', 'universal-ai-tools'))
        
        from src.core.unified_orchestration.unified_chat_orchestrator import get_unified_orchestrator
        
        logger.info("🧠 Using unified orchestrator for intelligent routing")
        
        orchestrator = get_unified_orchestrator()
        
        result = await orchestrator.chat(
            message=request.text,
            context=request.context or {}
        )
        
        response_text = result.get("response", "I couldn't process that request.")
        task_type = result.get("task_type", "general")
        backend_used = result.get("backend_used", "unknown")
        
        logger.info(f"✅ Orchestrator: {task_type} → {backend_used}")
        
        return ChatResponse(
            reply=response_text,
            route=f"orchestrated-{task_type}",
            metadata={
                "orchestrator_used": True,
                "task_type": task_type,
                "backend_used": backend_used,
                "rag_used": task_type == "rag",
                "sources": result.get("metadata", {}).get("sources", [])
            }
        )
        
    except ImportError as e:
        logger.warning(f"⚠️  Unified orchestrator not available: {e}")
        # Fallback to TRM router
        try:
            from src.api.trm_router import trm_route
            
            route_policy = trm_route(request.text, request.context or {})
            
            # Determine route based on policy
            if route_policy.rag.enabled:
                route = "rag-agent"
                # Get RAG context
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        rag_response = await client.post(
                            "http://127.0.0.1:8015/api/rag/query",
                            json={"query": request.text, "k": route_policy.rag.k}
                        )
                        if rag_response.status_code == 200:
                            rag_data = rag_response.json()
                            if rag_data.get("hits"):
                                contexts = [hit.get("text", "") for hit in rag_data["hits"][:3]]
                                rag_context = "\n\n".join(contexts)
                                response_text = f"Found context: {rag_context[:200]}...\n\nBased on the available context, here's what I can tell you about your query."
                            else:
                                response_text = f"Searching for relevant information about: {request.text}"
                        else:
                            response_text = f"Processing your query about: {request.text}"
                except Exception as rag_err:
                    logger.warning(f"RAG query failed: {rag_err}")
                    response_text = f"Processing your query about: {request.text}"
            elif route_policy.mode == "code":
                route = "code-agent"
                response_text = f"Analyzing code-related query: {request.text}"
            else:
                route = "chat-agent"
                response_text = f"Processing your message: {request.text}"
            
            logger.info(f"🧠 TRM routed to: {route} (RAG: {route_policy.rag.enabled})")
            
            return ChatResponse(
                reply=response_text,
                route=route,
                metadata={
                    "trm_used": True,
                    "rag_enabled": route_policy.rag.enabled,
                    "route_policy": route_policy.mode
                }
            )
            
        except ImportError as e2:
            logger.warning(f"⚠️  TRM router not available: {e2}")
            
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
    
    # Final fallback to Athena
    logger.info("🔄 Falling back to Athena")
    route = x_route or request.route or "auto"
    
    athena_payload = {
        "message": request.text,
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
            reply=athena_response.get("response", ""),
            route=athena_response.get("route", route),
            metadata=athena_response.get("metadata", {"fallback": True})
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

@app.post("/api/feedback", response_model=FeedbackResponse)
async def feedback_endpoint(request: FeedbackRequest):
    """Collect user feedback for bandit learning"""
    processing_start = time.perf_counter()

    try:
        # Calculate reward from feedback signals
        reward = 0.0

        if request.thumbs_up:
            reward += 0.9
            feedback_received.labels(signal_type="thumbs_up").inc()
        if request.thumbs_down:
            reward -= 0.9
            feedback_received.labels(signal_type="thumbs_down").inc()
        if request.regenerate:
            reward -= 0.2
            feedback_received.labels(signal_type="regenerate").inc()
        if request.edit_resend:
            reward -= 0.2
            feedback_received.labels(signal_type="edit_resend").inc()

        # Blend in evaluation scores if available (provides objective quality signal)
        eval_scores = get_evaluation_scores(request.interaction_id)
        if eval_scores:
            # Normalize eval scores (1-10) to reward component (-0.5 to +0.5)
            eval_score = (eval_scores["helpfulness"] + eval_scores["factuality"] + eval_scores["clarity"]) / 3.0
            eval_reward = (eval_score - 5.5) / 9.0  # Center at 5.5, scale to -0.5..+0.5
            reward += 0.25 * eval_reward  # Small weight for evaluation (human feedback dominates)

            # Log blended reward
            import logging
            logger = logging.getLogger(__name__)
            logger.info("feedback_with_eval", {
                "interaction_id": request.interaction_id,
                "human_reward": reward - (0.25 * eval_reward),
                "eval_reward": 0.25 * eval_reward,
                "total_reward": reward,
                "eval_scores": eval_scores
            })

        # For now, we'll log the feedback. In production, you'd:
        # 1. Fetch the interaction from database using interaction_id
        # 2. Get the prompt_variant from the stored interaction
        # 3. Update bandit stats: record_feedback(variant, reward)

        # Placeholder logging (replace with actual DB operations)
        import logging
        logger = logging.getLogger(__name__)
        logger.info("feedback_received", {
            "interaction_id": request.interaction_id,
            "thumbs_up": request.thumbs_up,
            "thumbs_down": request.thumbs_down,
            "regenerate": request.regenerate,
            "edit_resend": request.edit_resend,
            "calculated_reward": reward
        })

        # TODO: In production, implement:
        # - Fetch interaction from DB by interaction_id
        # - Extract prompt_variant
        # - Call record_feedback(variant, reward)
        # - Update interaction.reward in DB

        processing_time = time.perf_counter() - processing_start
        feedback_processing_time.observe(processing_time)

        return FeedbackResponse(
            ok=True,
            message="Feedback recorded successfully",
            reward=reward
        )

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("feedback_processing_failed", {
            "interaction_id": request.interaction_id,
            "error": str(e)
        })

        return FeedbackResponse(
            ok=False,
            message=f"Feedback processing failed: {str(e)}"
        )

@app.get("/version")
async def version():
    """Version endpoint for deployment tracking"""
    import datetime
    return {
        "service": "bridge",
        "version": ADAPTER_VERSION,
        "git_sha": os.environ.get("GIT_SHA", "unknown"),
        "build_time": os.environ.get("BUILD_TIME", datetime.datetime.utcnow().isoformat()),
        "environment": ENV
    }

@app.get("/ready")
async def ready():
    """Readiness check endpoint - same as health for now"""
    return await health()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8014)
