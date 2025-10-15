"""
Prometheus /metrics endpoint for TRM router and evolution
"""
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Import metrics from core

router = APIRouter()

@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint
    Exposes all TRM routing and evolution metrics
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/health")
async def metrics_health():
    """Health check for metrics endpoint"""
    return {
        "status": "healthy",
        "metrics_available": [
            "routing_decisions_total",
            "routing_success_total",
            "routing_errors_total",
            "routing_latency_ms",
            "trm_promotions_total",
            "trm_accuracy_delta",
            "model_inference_ms",
            "rag_retrievals_total",
            "rag_documents_returned"
        ]
    }

