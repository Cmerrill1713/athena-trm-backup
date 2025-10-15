#!/usr/bin/env python3
"""
UAT (Universal AI Tools) Service
Provides traces, stats, and capabilities endpoints
"""
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException

# Add path for common imports (4 levels up: uat -> universal-ai-tools -> AI-Projects -> GitHub)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from common.ops import (
    add_health_endpoints,
    attach_guardrails,
    install_graceful_shutdown,
    wire_tracing,
)
from common.secrets import load_secret

app = FastAPI(title="UAT Service", version="1.0.0")

# Tier 4: Production hardening
add_health_endpoints(app)  # /live, /ready
wire_tracing(app, service_name="uat")  # OTLP tracing
attach_guardrails(
    app,
    per_ip_rate=os.getenv("RATE_LIMIT", "100/minute"),
    max_body_mb=int(os.getenv("MAX_BODY_MB", "5")),
    request_timeout_s=int(os.getenv("REQ_TIMEOUT_S", "30"))
)
install_graceful_shutdown(app, drain_seconds=int(os.getenv("DRAIN_S", "5")))

# Auth configuration (keychain-first, env fallback)
UAT_TOKEN = load_secret("uat_token", "UAT_TOKEN", "supersecret")

# In-memory trace storage (seeded from transcripts)
_traces = []
_stats = {
    "total_traces": 0,
    "total_requests": 0,
    "avg_latency_ms": 0
}

def verify_token(authorization: Optional[str] = Header(None)):
    """Verify Bearer token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization.replace("Bearer ", "")
    if token != UAT_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    return token

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "uat",
        "timestamp": datetime.utcnow().isoformat(),
        "traces_loaded": len(_traces)
    }

@app.get("/traces")
async def get_traces(
    limit: int = 100,
    token: str = Depends(verify_token)
):
    """Get all traces"""
    start = time.time()

    # Update stats
    _stats["total_requests"] += 1

    result = {
        "traces": _traces[:limit],
        "count": len(_traces[:limit]),
        "total": len(_traces),
        "source": "uat-service"
    }

    latency_ms = (time.time() - start) * 1000
    _stats["avg_latency_ms"] = latency_ms

    return result

@app.get("/trace/{trace_id}")
async def get_trace(
    trace_id: str,
    token: str = Depends(verify_token)
):
    """Get specific trace by ID"""
    start = time.time()

    # Find trace by ID
    trace = next((t for t in _traces if t["trace_id"] == trace_id), None)

    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    _stats["total_requests"] += 1
    latency_ms = (time.time() - start) * 1000
    _stats["avg_latency_ms"] = latency_ms

    return trace

@app.get("/stats")
async def get_stats(token: str = Depends(verify_token)):
    """Get service statistics"""
    return {
        **_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/capabilities")
async def get_capabilities(token: str = Depends(verify_token)):
    """Get service capabilities"""
    return {
        "service": "uat",
        "version": "1.0.0",
        "capabilities": [
            "traces",
            "trace_detail",
            "stats",
            "health"
        ],
        "endpoints": {
            "traces": "GET /traces",
            "trace": "GET /trace/{id}",
            "stats": "GET /stats",
            "health": "GET /health",
            "capabilities": "GET /capabilities"
        }
    }

@app.post("/seed")
async def seed_traces(token: str = Depends(verify_token)):
    """Seed traces from transcripts directory"""
    global _traces

    # Look for transcripts
    transcripts_dir = os.path.join(os.path.dirname(__file__), "..", "indydevdan_transcripts")

    if not os.path.exists(transcripts_dir):
        # Create demo traces
        _traces = [
            {
                "trace_id": f"uat-trace-{i:03d}",
                "title": f"UAT Trace {i} - System Operation",
                "timestamp": datetime.utcnow().isoformat(),
                "capability": "system",
                "status": "success",
                "duration_ms": 50 + (i * 10),
                "provider": "uat-service",
                "metadata": {
                    "source": "demo",
                    "index": i
                }
            }
            for i in range(1, 171)  # Create 170 demo traces
        ]
    else:
        # Load real transcripts
        transcript_files = [f for f in os.listdir(transcripts_dir) if f.endswith('.json')]
        _traces = []

        for i, filename in enumerate(transcript_files[:170], 1):
            filepath = os.path.join(transcripts_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)

                trace = {
                    "trace_id": f"transcript-{i:03d}",
                    "title": data.get("title", f"Transcript {i}"),
                    "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
                    "capability": "transcript",
                    "status": "success",
                    "duration_ms": len(data.get("text", "")) // 10,  # Rough estimate
                    "provider": "indydevdan",
                    "metadata": {
                        "source": "transcript",
                        "filename": filename,
                        "author": data.get("author", "unknown")
                    }
                }
                _traces.append(trace)
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

    _stats["total_traces"] = len(_traces)

    return {
        "status": "seeded",
        "traces_loaded": len(_traces),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Auto-seed on startup if UAT_AUTO_SEED=1"""
    if os.getenv("UAT_AUTO_SEED", "1") == "1":
        print("🌱 Auto-seeding traces...")
        # Create initial demo traces without auth
        global _traces
        _traces = [
            {
                "trace_id": f"uat-trace-{i:03d}",
                "title": f"UAT Trace {i} - System Operation",
                "timestamp": datetime.utcnow().isoformat(),
                "capability": "system",
                "status": "success",
                "duration_ms": 50 + (i * 10),
                "provider": "uat-service",
                "metadata": {
                    "source": "demo",
                    "index": i
                }
            }
            for i in range(1, 171)
        ]
        _stats["total_traces"] = len(_traces)
        print(f"✅ Seeded {len(_traces)} traces")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")


