#!/usr/bin/env python3
"""
Athena Evolutionary API
Port 8014 - Evolutionary algorithms and self-improvement
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Athena Evolutionary API",
    description="Evolutionary algorithms and agent self-improvement",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
evolution_cycles_total = Counter(
    'athena_evolution_cycles_total',
    'Total evolution cycles'
)

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "evolutionary",
        "port": 8014,
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.post("/evolve")
async def evolve():
    """Trigger evolution cycle."""
    evolution_cycles_total.inc()
    return {
        "status": "evolution_triggered",
        "generation": 1
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8014"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

