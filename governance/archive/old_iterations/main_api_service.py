#!/usr/bin/env python3
"""
Athena Main API Service
Central API gateway for the Athena platform
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import redis

app = FastAPI(title="Athena Main API Service", version="1.0.0")

# Service connections
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    use_knowledge: bool = True
    use_evolution: bool = False

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    confidence: float
    processing_time_ms: float
    session_id: str
    knowledge_used: bool
    evolution_applied: bool

class SystemStatus(BaseModel):
    service: str
    status: str
    version: str
    uptime_seconds: float
    last_check: str

# Service URLs
SERVICE_URLS = {
    "knowledge_context": "http://athena-knowledge-context:8031",
    "knowledge_gateway": "http://athena-knowledge-gateway:8032",
    "knowledge_sync": "http://athena-knowledge-sync:8033",
    "evolutionary": "http://athena-evolutionary:8034",
    "weaviate": os.getenv("WEAVIATE_URL", "http://athena-weaviate:8080")
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        conn.close()

        # Check other services
        healthy_services = 0
        total_services = len(SERVICE_URLS)

        async with httpx.AsyncClient() as client:
            for service_name, url in SERVICE_URLS.items():
                try:
                    response = await client.get(f"{url}/health", timeout=5)
                    if response.status_code == 200:
                        healthy_services += 1
                except:
                    pass

        health_status = "healthy" if healthy_services == total_services else "degraded"

        return {
            "status": health_status,
            "services_healthy": f"{healthy_services}/{total_services}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with full platform integration"""
    start_time = datetime.utcnow()

    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Get context from knowledge service
        context_data = {}
        knowledge_used = False

        if request.use_knowledge:
            try:
                async with httpx.AsyncClient() as client:
                    # Get stored context
                    context_response = await client.get(
                        f"{SERVICE_URLS['knowledge_context']}/context/{session_id}",
                        timeout=5
                    )
                    if context_response.status_code == 200:
                        context_data = context_response.json().get("context", {})

                    # Search knowledge base
                    search_response = await client.post(
                        f"{SERVICE_URLS['knowledge_gateway']}/search",
                        json={
                            "query": request.message,
                            "query_type": "hybrid",
                            "limit": 5
                        },
                        timeout=10
                    )

                    if search_response.status_code == 200:
                        search_results = search_response.json()
                        context_data["knowledge_results"] = search_results["results"]
                        knowledge_used = True

            except Exception as e:
                print(f"Knowledge service error: {e}")

        # Apply evolutionary optimization if requested
        evolution_applied = False
        if request.use_evolution:
            try:
                async with httpx.AsyncClient() as client:
                    evolution_response = await client.post(
                        f"{SERVICE_URLS['evolutionary']}/evolve",
                        json={
                            "system_component": "routing",
                            "performance_data": [
                                {
                                    "route": "chat",
                                    "success": True,
                                    "latency_ms": 100,
                                    "quality_score": 0.8
                                }
                            ]
                        },
                        timeout=5
                    )

                    if evolution_response.status_code == 200:
                        evolution_data = evolution_response.json()
                        context_data["evolution_recommendations"] = evolution_data["recommendations"]
                        evolution_applied = True

            except Exception as e:
                print(f"Evolution service error: {e}")

        # Generate response (simplified - in production, this would call LLM)
        response_text = f"Athena Platform Response: {request.message}"
        if knowledge_used:
            response_text += "\n\n[Knowledge-based response with context]"
        if evolution_applied:
            response_text += "\n\n[Evolution-optimized response]"

        # Store context for future conversations
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{SERVICE_URLS['knowledge_context']}/context",
                    json={
                        "session_id": session_id,
                        "user_id": request.user_id,
                        "context_data": {
                            "last_message": request.message,
                            "last_response": response_text,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "ttl_seconds": 3600
                    },
                    timeout=5
                )
        except Exception as e:
            print(f"Context storage error: {e}")

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Track usage
        usage_key = f"api_usage:{datetime.utcnow().strftime('%Y-%m-%d')}"
        redis_client.hincrby(usage_key, "chat_requests", 1)

        return ChatResponse(
            response=response_text,
            sources=["knowledge_base", "evolutionary_optimization"] if knowledge_used else [],
            confidence=0.85,
            processing_time_ms=round(processing_time, 2),
            session_id=session_id,
            knowledge_used=knowledge_used,
            evolution_applied=evolution_applied
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/status")
async def get_system_status():
    """Get comprehensive system status"""
    services_status = []

    # Check each service
    async with httpx.AsyncClient() as client:
        for service_name, url in SERVICE_URLS.items():
            try:
                start_time = datetime.utcnow()
                response = await client.get(f"{url}/health", timeout=5)
                latency = (datetime.utcnow() - start_time).total_seconds()

                if response.status_code == 200:
                    service_data = response.json()
                    services_status.append(SystemStatus(
                        service=service_name,
                        status=service_data.get("status", "unknown"),
                        version="1.0.0",
                        uptime_seconds=0.0,  # Would be calculated from actual uptime
                        last_check=datetime.utcnow().isoformat()
                    ))
                else:
                    services_status.append(SystemStatus(
                        service=service_name,
                        status="unhealthy",
                        version="unknown",
                        uptime_seconds=0.0,
                        last_check=datetime.utcnow().isoformat()
                    ))

            except Exception:
                services_status.append(SystemStatus(
                    service=service_name,
                    status="unreachable",
                    version="unknown",
                    uptime_seconds=0.0,
                    last_check=datetime.utcnow().isoformat()
                ))

    return {
        "system_status": "healthy" if all(s.status == "healthy" for s in services_status) else "degraded",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Get usage statistics
        usage_key = f"api_usage:{datetime.utcnow().strftime('%Y-%m-%d')}"
        usage_data = redis_client.hgetall(usage_key)

        # Count active sessions
        active_sessions = len(redis_client.keys("context:*"))

        metrics_data = f"""# HELP athena_api_requests_total Total API requests
# TYPE athena_api_requests_total counter
athena_api_requests_total{{endpoint="chat"}} {usage_data.get(b'chat_requests', b'0').decode()}

# HELP athena_api_active_sessions_total Active user sessions
# TYPE athena_api_active_sessions_total gauge
athena_api_active_sessions_total {active_sessions}
"""
        return {"content": metrics_data, "content_type": "text/plain"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8035)
