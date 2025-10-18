"""
Prometheus metrics endpoint for UAI
"""
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False


@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    if not HAS_PROMETHEUS:
        return Response(
            "# Prometheus client not installed\n",
            media_type="text/plain"
        )
    
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
