#!/usr/bin/env python3
"""
NeuroForge Bridge Service
Provides the /traces endpoints that NeuroForge expects
"""
import asyncio
import json
import os
import random
import time
from datetime import datetime

import httpx
from fastapi import FastAPI

# Configuration
UAT_BASE = os.environ.get("UAT_BASE", "http://127.0.0.1:8080")
UAT_TOKEN = os.environ.get("UAT_TOKEN")
ATHENA_BASE = os.environ.get("ATHENA_BASE", "http://127.0.0.1:8090")
ATH_TOKEN = os.environ.get("ATH_TOKEN")
USE_MOCK = os.getenv("USE_MOCK", "1") == "1"

app = FastAPI(title="NeuroForge Bridge", version="1.0.0")

# Circuit breaker state
_circuit_breaker = {
    "failures": 0,
    "last_failure": 0,
    "is_open": False
}

def headers():
    """Get auth headers if token is available"""
    if UAT_TOKEN:
        return {"Authorization": f"Bearer {UAT_TOKEN}"}
    return {}

def athena_headers():
    """Get Athena auth headers if token is available"""
    if ATH_TOKEN:
        return {"Authorization": f"Bearer {ATH_TOKEN}"}
    return {}

async def get_json_with_retry(client: httpx.AsyncClient, url: str, headers: dict, max_retries: int = 3):
    """Get JSON with retry logic and jitter"""
    for i in range(max_retries):
        try:
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code < 500:
                response.raise_for_status()
                return response.json()
            # 5xx error - retry with jitter
            if i < max_retries - 1:
                delay = 0.2 + random.random() * 0.3
                await asyncio.sleep(delay)
        except Exception as e:
            if i < max_retries - 1:
                delay = 0.2 + random.random() * 0.3
                await asyncio.sleep(delay)
            else:
                raise e
    response.raise_for_status()

def check_circuit_breaker():
    """Check if circuit breaker should allow requests"""
    now = time.time()

    # Reset circuit breaker after 30 seconds
    if now - _circuit_breaker["last_failure"] > 30:
        _circuit_breaker["failures"] = 0
        _circuit_breaker["is_open"] = False

    # Open circuit breaker after 5 failures
    if _circuit_breaker["failures"] >= 5:
        _circuit_breaker["is_open"] = True
        return False

    return True

def record_failure():
    """Record a failure for circuit breaker"""
    _circuit_breaker["failures"] += 1
    _circuit_breaker["last_failure"] = time.time()

def record_success():
    """Record a success for circuit breaker"""
    _circuit_breaker["failures"] = 0
    _circuit_breaker["is_open"] = False

@app.get("/health")
async def health():
    """Health check endpoint"""
    from fastapi import Response

    response_data = {
        "status": "ok",
        "service": "neuroforge-bridge",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Add observability headers
    headers = {
        "X-Mode": "mock" if USE_MOCK else "real",
        "X-Breaker": "open" if _circuit_breaker["is_open"] else "closed"
    }

    return Response(
        content=json.dumps(response_data),
        media_type="application/json",
        headers=headers
    )

@app.get("/traces")
async def traces(limit: int = 100):
    """Get traces - bridge to Universal AI Tools or return mock data"""

    # If using mock mode, return mock data immediately
    if USE_MOCK:
        mock_traces = [
            {
                "trace_id": "seed-1",
                "title": "First run: RAG health",
                "timestamp": "2025-10-12T17:00:00Z",
                "capability": "health",
                "status": "success",
                "duration_ms": 45,
                "provider": "demo"
            },
            {
                "trace_id": "demo-002",
                "title": "Demo Trace - Chat Request",
                "timestamp": datetime.utcnow().isoformat(),
                "capability": "chat",
                "status": "success",
                "duration_ms": 1200,
                "provider": "llama3.2:3b"
            }
        ]

        return {
            "traces": mock_traces,
            "count": len(mock_traces),
            "source": "mock-mode"
        }

    # Check circuit breaker
    if not check_circuit_breaker():
        print("Circuit breaker open - returning cached mock data")
        return {
            "traces": [{
                "trace_id": "circuit-breaker-001",
                "title": "Circuit Breaker Active",
                "timestamp": datetime.utcnow().isoformat(),
                "capability": "system",
                "status": "degraded",
                "duration_ms": 0,
                "provider": "bridge"
            }],
            "count": 1,
            "source": "circuit-breaker"
        }

    try:
        # Try to get real traces from Universal AI Tools
        async with httpx.AsyncClient(timeout=10) as client:
            data = await get_json_with_retry(client, f"{UAT_BASE}/traces", headers())
            record_success()
            return {
                "traces": data,
                "count": len(data) if isinstance(data, list) else 1,
                "source": "uat-real"
            }
    except Exception as e:
        print(f"Failed to get traces from {UAT_BASE}: {e}")
        record_failure()

        # Return mock traces as fallback
        mock_traces = [
            {
                "trace_id": "fallback-001",
                "title": "Fallback Trace - UAT Unavailable",
                "timestamp": datetime.utcnow().isoformat(),
                "capability": "fallback",
                "status": "degraded",
                "duration_ms": 0,
                "provider": "bridge"
            }
        ]

        return {
            "traces": mock_traces,
            "count": len(mock_traces),
            "source": "fallback"
        }

@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Get specific trace by ID"""

    # If using mock mode, return mock data immediately
    if USE_MOCK:
        mock_trace = {
            "trace_id": trace_id,
            "title": f"Mock Trace - {trace_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "capability": "demo",
            "status": "success",
            "duration_ms": 500,
            "provider": "mock",
            "input": {"message": "Hello world"},
            "output": {"response": "Mock response for development"},
            "events": [
                {
                    "label": "start",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"step": "initialization"}
                },
                {
                    "label": "complete",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"result": "success"}
                }
            ],
            "source": "mock-mode"
        }
        return mock_trace

    # Check circuit breaker
    if not check_circuit_breaker():
        return {
            "trace_id": trace_id,
            "title": f"Circuit Breaker - {trace_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "capability": "system",
            "status": "degraded",
            "duration_ms": 0,
            "provider": "bridge",
            "source": "circuit-breaker"
        }

    try:
        # Try to get real trace from Universal AI Tools
        async with httpx.AsyncClient(timeout=10) as client:
            data = await get_json_with_retry(client, f"{UAT_BASE}/trace/{trace_id}", headers())
            record_success()
            data["source"] = "uat-real"
            return data
    except Exception as e:
        print(f"Failed to get trace {trace_id} from {UAT_BASE}: {e}")
        record_failure()

        # Fallback: Return mock trace detail
        mock_trace = {
            "trace_id": trace_id,
            "title": f"Fallback Trace - {trace_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "capability": "fallback",
            "status": "degraded",
            "duration_ms": 0,
            "provider": "bridge",
            "source": "fallback"
        }
        return mock_trace

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "NeuroForge Bridge",
        "version": "1.0.0",
        "status": "running",
        "target": UAT_BASE,
        "mock_mode": USE_MOCK,
        "circuit_breaker": {
            "is_open": _circuit_breaker["is_open"],
            "failures": _circuit_breaker["failures"]
        },
        "endpoints": {
            "health": "/health",
            "traces": "/traces",
            "trace": "/trace/{trace_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8014, log_level="info")
