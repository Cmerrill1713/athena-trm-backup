"""
Health check router
"""

from datetime import datetime

from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "universal-ai-tools-api"
    }


@router.options("/health")
async def health_options():
    """CORS preflight handler for /health"""
    return Response(status_code=200)


@router.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "universal-ai-tools-api",
        "path": "/api/health"
    }


@router.options("/api/health")
async def api_health_options():
    """CORS preflight handler for /api/health"""
    return Response(status_code=200)

