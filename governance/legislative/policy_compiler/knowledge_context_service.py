#!/usr/bin/env python3
"""
Athena Knowledge Context Service
Manages conversation context and memory
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import redis

app = FastAPI(title="Athena Knowledge Context Service", version="1.0.0")

# Redis connection
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

class ContextRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    context_data: Dict[str, Any]
    ttl_seconds: int = 3600

class ContextResponse(BaseModel):
    session_id: str
    context_data: Dict[str, Any]
    expires_at: str
    created_at: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        conn.close()
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/context", response_model=ContextResponse)
async def store_context(request: ContextRequest):
    """Store conversation context"""
    try:
        expires_at = datetime.utcnow() + timedelta(seconds=request.ttl_seconds)

        context_data = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "context": request.context_data,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat()
        }

        # Store in Redis
        redis_client.setex(
            f"context:{request.session_id}",
            request.ttl_seconds,
            json.dumps(context_data)
        )

        # Store in PostgreSQL for persistence
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO conversation_contexts (session_id, user_id, context_data, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                context_data = EXCLUDED.context_data,
                expires_at = EXCLUDED.expires_at
        """, (
            request.session_id,
            request.user_id,
            json.dumps(request.context_data),
            datetime.utcnow(),
            expires_at
        ))

        conn.commit()
        cur.close()
        conn.close()

        return ContextResponse(
            session_id=request.session_id,
            context_data=request.context_data,
            expires_at=expires_at.isoformat(),
            created_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store context: {str(e)}")

@app.get("/context/{session_id}", response_model=ContextResponse)
async def get_context(session_id: str):
    """Retrieve conversation context"""
    try:
        # Try Redis first
        context_data = redis_client.get(f"context:{session_id}")

        if context_data:
            data = json.loads(context_data)
            return ContextResponse(
                session_id=session_id,
                context_data=data["context"],
                expires_at=data["expires_at"],
                created_at=data["created_at"]
            )

        # Fallback to PostgreSQL
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        cur = conn.cursor()

        cur.execute("""
            SELECT context_data, created_at, expires_at
            FROM conversation_contexts
            WHERE session_id = %s AND expires_at > %s
        """, (session_id, datetime.utcnow()))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            context_data, created_at, expires_at = result
            return ContextResponse(
                session_id=session_id,
                context_data=json.loads(context_data),
                expires_at=expires_at.isoformat(),
                created_at=created_at.isoformat()
            )
        else:
            raise HTTPException(status_code=404, detail="Context not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve context: {str(e)}")

@app.delete("/context/{session_id}")
async def delete_context(session_id: str):
    """Delete conversation context"""
    try:
        # Delete from Redis
        redis_client.delete(f"context:{session_id}")

        # Delete from PostgreSQL
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        cur = conn.cursor()

        cur.execute("DELETE FROM conversation_contexts WHERE session_id = %s", (session_id,))
        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Context deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete context: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Count active contexts
        active_contexts = len(redis_client.keys("context:*"))

        metrics_data = f"""# HELP athena_context_active_total Active conversation contexts
# TYPE athena_context_active_total gauge
athena_context_active_total {active_contexts}
"""
        return {"content": metrics_data, "content_type": "text/plain"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8031)
