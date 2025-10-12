#!/usr/bin/env python3
"""
Standalone test API to verify TRM metrics integration works
Run: python test_metrics_api.py
Then: curl http://localhost:8080/metrics
"""
import sys
import time
from pathlib import Path
from fastapi import FastAPI
import uvicorn

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# Import our metrics modules
from src.metrics.route_metrics import (
    ROUTING_DECISIONS,
    ROUTING_SUCCESS,
    ROUTING_LATENCY
)
from src.api.metrics_mount import mount_metrics

# Create app
app = FastAPI(title="TRM Metrics Test")

# Mount metrics endpoint
app = mount_metrics(app)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "TRM Metrics Test API",
        "endpoints": {
            "/metrics": "Prometheus metrics",
            "/test/route": "Simulate routing decision"
        }
    }

@app.post("/test/route")
async def test_route(prompt: str = "test prompt"):
    """Simulate a routing decision with metrics"""
    import os
    start = time.time()
    
    # Get environment labels
    env = os.getenv("ENV", "test")
    build = os.getenv("BUILD_SHA", "test")
    
    # Simulate routing
    selected_model = "mlx/chat"
    
    # Emit metrics with labels
    ROUTING_DECISIONS.labels(model=selected_model, env=env, build=build).inc()
    ROUTING_SUCCESS.labels(env=env, build=build).inc()
    
    latency_ms = (time.time() - start) * 1000
    ROUTING_LATENCY.labels(env=env, build=build).observe(latency_ms)
    
    return {
        "status": "routed",
        "model": selected_model,
        "env": env,
        "build": build,
        "latency_ms": round(latency_ms, 2),
        "metrics_emitted": True
    }

if __name__ == "__main__":
    print("🚀 Starting TRM Metrics Test API on http://localhost:8085")
    print("   /metrics - Prometheus endpoint")
    print("   POST /test/route - Simulate routing")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8085)

