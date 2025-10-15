#!/usr/bin/env python3
"""
Athena Knowledge Sync Service
Synchronizes knowledge across services and keeps data consistent
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
import psycopg2
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

import redis

app = FastAPI(title="Athena Knowledge Sync Service", version="1.0.0")

# Redis connection
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Service URLs
SERVICE_URLS = {
    "weaviate": os.getenv("WEAVIATE_URL", "http://athena-weaviate:8080"),
    "knowledge_context": "http://athena-knowledge-context:8031",
    "knowledge_gateway": "http://athena-knowledge-gateway:8032"
}

class SyncRequest(BaseModel):
    sync_type: str  # "full", "incremental", "context", "knowledge"
    force: bool = False
    target_services: Optional[List[str]] = None

class SyncResponse(BaseModel):
    sync_id: str
    status: str
    services_synced: List[str]
    items_processed: int
    sync_time_ms: float
    errors: List[str]

class SyncStatus(BaseModel):
    sync_id: str
    status: str  # "running", "completed", "failed"
    progress_percentage: float
    services_completed: List[str]
    items_processed: int
    started_at: str
    estimated_completion: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        conn.close()

        # Check Weaviate
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_URLS['weaviate']}/v1/meta", timeout=5)
            weaviate_healthy = response.status_code == 200

        return {
            "status": "healthy" if weaviate_healthy else "degraded",
            "services": {
                "redis": "healthy",
                "postgres": "healthy",
                "weaviate": "healthy" if weaviate_healthy else "unhealthy"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/sync", response_model=SyncResponse)
async def start_sync(request: SyncRequest, background_tasks: BackgroundTasks):
    """Start knowledge synchronization"""
    sync_id = f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    start_time = datetime.utcnow()

    try:
        # Store sync status
        sync_status = {
            "sync_id": sync_id,
            "status": "running",
            "progress_percentage": 0.0,
            "services_completed": [],
            "items_processed": 0,
            "started_at": start_time.isoformat(),
            "sync_type": request.sync_type
        }

        redis_client.setex(
            f"sync_status:{sync_id}",
            3600,  # 1 hour
            json.dumps(sync_status)
        )

        # Start background sync
        background_tasks.add_task(
            perform_sync,
            sync_id,
            request.sync_type,
            request.force,
            request.target_services
        )

        return SyncResponse(
            sync_id=sync_id,
            status="started",
            services_synced=[],
            items_processed=0,
            sync_time_ms=0.0,
            errors=[]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")

async def perform_sync(sync_id: str, sync_type: str, force: bool, target_services: Optional[List[str]]):
    """Perform the actual synchronization"""
    try:
        items_processed = 0
        services_synced = []
        errors = []

        if sync_type == "full":
            items_processed, services_synced, errors = await full_sync(sync_id)
        elif sync_type == "incremental":
            items_processed, services_synced, errors = await incremental_sync(sync_id)
        elif sync_type == "context":
            items_processed, services_synced, errors = await context_sync(sync_id)
        elif sync_type == "knowledge":
            items_processed, services_synced, errors = await knowledge_sync(sync_id)

        # Update final status
        final_status = {
            "sync_id": sync_id,
            "status": "completed" if not errors else "completed_with_errors",
            "progress_percentage": 100.0,
            "services_completed": services_synced,
            "items_processed": items_processed,
            "completed_at": datetime.utcnow().isoformat()
        }

        redis_client.setex(
            f"sync_status:{sync_id}",
            86400,  # 24 hours
            json.dumps(final_status)
        )

    except Exception as e:
        # Mark sync as failed
        error_status = {
            "sync_id": sync_id,
            "status": "failed",
            "progress_percentage": 0.0,
            "services_completed": [],
            "items_processed": 0,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }

        redis_client.setex(
            f"sync_status:{sync_id}",
            86400,
            json.dumps(error_status)
        )

async def full_sync(sync_id: str) -> tuple[int, List[str], List[str]]:
    """Perform full synchronization of all data"""
    items_processed = 0
    services_synced = []
    errors = []

    try:
        # Sync from PostgreSQL to Weaviate
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        cur = conn.cursor()

        # Get all knowledge documents
        cur.execute("SELECT id, title, content, url, source, tags FROM knowledge_documents")
        documents = cur.fetchall()

        async with httpx.AsyncClient() as client:
            for doc_id, title, content, url, source, tags in documents:
                try:
                    # Sync to Weaviate
                    doc_data = {
                        "title": title,
                        "content": content,
                        "url": url,
                        "source": source,
                        "tags": json.loads(tags) if tags else [],
                        "synced_at": datetime.utcnow().isoformat()
                    }

                    response = await client.post(
                        f"{SERVICE_URLS['weaviate']}/v1/objects",
                        json={"class": "KnowledgeDocument", "properties": doc_data},
                        timeout=10
                    )

                    if response.status_code == 200:
                        items_processed += 1
                    else:
                        errors.append(f"Failed to sync document {doc_id}: {response.status_code}")

                except Exception as e:
                    errors.append(f"Error syncing document {doc_id}: {str(e)}")

        cur.close()
        conn.close()
        services_synced.append("weaviate")

        # Update sync progress
        await update_sync_progress(sync_id, 100.0, services_synced, items_processed)

    except Exception as e:
        errors.append(f"Full sync error: {str(e)}")

    return items_processed, services_synced, errors

async def incremental_sync(sync_id: str) -> tuple[int, List[str], List[str]]:
    """Perform incremental synchronization of recent changes"""
    items_processed = 0
    services_synced = []
    errors = []

    try:
        # Get recent changes (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        cur = conn.cursor()

        cur.execute("""
            SELECT id, title, content, url, source, tags 
            FROM knowledge_documents 
            WHERE updated_at > %s
        """, (cutoff_time,))

        recent_documents = cur.fetchall()

        async with httpx.AsyncClient() as client:
            for doc_id, title, content, url, source, tags in recent_documents:
                try:
                    doc_data = {
                        "title": title,
                        "content": content,
                        "url": url,
                        "source": source,
                        "tags": json.loads(tags) if tags else [],
                        "synced_at": datetime.utcnow().isoformat()
                    }

                    response = await client.post(
                        f"{SERVICE_URLS['weaviate']}/v1/objects",
                        json={"class": "KnowledgeDocument", "properties": doc_data},
                        timeout=10
                    )

                    if response.status_code == 200:
                        items_processed += 1
                    else:
                        errors.append(f"Failed to sync document {doc_id}")

                except Exception as e:
                    errors.append(f"Error syncing document {doc_id}: {str(e)}")

        cur.close()
        conn.close()
        services_synced.append("weaviate")

        # Update sync progress
        await update_sync_progress(sync_id, 100.0, services_synced, items_processed)

    except Exception as e:
        errors.append(f"Incremental sync error: {str(e)}")

    return items_processed, services_synced, errors

async def context_sync(sync_id: str) -> tuple[int, List[str], List[str]]:
    """Synchronize conversation contexts"""
    items_processed = 0
    services_synced = []
    errors = []

    try:
        # Sync contexts from Redis to PostgreSQL
        context_keys = redis_client.keys("context:*")

        for key in context_keys:
            try:
                context_data = redis_client.get(key)
                if context_data:
                    data = json.loads(context_data)

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
                        data["session_id"],
                        data["user_id"],
                        json.dumps(data["context"]),
                        datetime.fromisoformat(data["created_at"]),
                        datetime.fromisoformat(data["expires_at"])
                    ))

                    conn.commit()
                    cur.close()
                    conn.close()

                    items_processed += 1

            except Exception as e:
                errors.append(f"Error syncing context {key}: {str(e)}")

        services_synced.append("postgres")
        await update_sync_progress(sync_id, 100.0, services_synced, items_processed)

    except Exception as e:
        errors.append(f"Context sync error: {str(e)}")

    return items_processed, services_synced, errors

async def knowledge_sync(sync_id: str) -> tuple[int, List[str], List[str]]:
    """Synchronize knowledge base data"""
    items_processed = 0
    services_synced = []
    errors = []

    try:
        # Sync from Weaviate to PostgreSQL for backup
        async with httpx.AsyncClient() as client:
            gql_query = {
                "query": """
                {
                    Get {
                        KnowledgeDocument(limit: 1000) {
                            title
                            content
                            url
                            source
                            tags
                            _additional {
                                id
                            }
                        }
                    }
                }
                """
            }

            response = await client.post(
                f"{SERVICE_URLS['weaviate']}/v1/graphql",
                json=gql_query,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                documents = data.get("data", {}).get("Get", {}).get("KnowledgeDocument", [])

                conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
                cur = conn.cursor()

                for doc in documents:
                    try:
                        cur.execute("""
                            INSERT INTO knowledge_documents (weaviate_id, title, content, url, source, tags)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (weaviate_id) DO UPDATE SET
                                title = EXCLUDED.title,
                                content = EXCLUDED.content,
                                url = EXCLUDED.url,
                                source = EXCLUDED.source,
                                tags = EXCLUDED.tags,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            doc["_additional"]["id"],
                            doc["title"],
                            doc["content"],
                            doc["url"],
                            doc["source"],
                            json.dumps(doc["tags"])
                        ))

                        items_processed += 1

                    except Exception as e:
                        errors.append(f"Error syncing document: {str(e)}")

                conn.commit()
                cur.close()
                conn.close()
                services_synced.append("postgres")

            else:
                errors.append(f"Weaviate query failed: {response.status_code}")

        await update_sync_progress(sync_id, 100.0, services_synced, items_processed)

    except Exception as e:
        errors.append(f"Knowledge sync error: {str(e)}")

    return items_processed, services_synced, errors

async def update_sync_progress(sync_id: str, progress: float, services_completed: List[str], items_processed: int):
    """Update sync progress in Redis"""
    try:
        status_data = redis_client.get(f"sync_status:{sync_id}")
        if status_data:
            status = json.loads(status_data)
            status["progress_percentage"] = progress
            status["services_completed"] = services_completed
            status["items_processed"] = items_processed

            redis_client.setex(
                f"sync_status:{sync_id}",
                3600,
                json.dumps(status)
            )
    except Exception as e:
        print(f"Error updating sync progress: {e}")

@app.get("/sync/status/{sync_id}", response_model=SyncStatus)
async def get_sync_status(sync_id: str):
    """Get synchronization status"""
    try:
        status_data = redis_client.get(f"sync_status:{sync_id}")
        if status_data:
            status = json.loads(status_data)
            return SyncStatus(**status)
        else:
            raise HTTPException(status_code=404, detail="Sync not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Count active syncs
        active_syncs = len(redis_client.keys("sync_status:*"))

        # Count sync types
        sync_types = {}
        for key in redis_client.keys("sync_status:*"):
            try:
                status_data = redis_client.get(key)
                if status_data:
                    status = json.loads(status_data)
                    sync_type = status.get("sync_type", "unknown")
                    sync_types[sync_type] = sync_types.get(sync_type, 0) + 1
            except:
                continue

        metrics_data = f"""# HELP athena_sync_active_total Active synchronization jobs
# TYPE athena_sync_active_total gauge
athena_sync_active_total {active_syncs}

# HELP athena_sync_types_total Total syncs by type
# TYPE athena_sync_types_total counter
"""

        for sync_type, count in sync_types.items():
            metrics_data += f'athena_sync_types_total{{type="{sync_type}"}} {count}\n'

        return {"content": metrics_data, "content_type": "text/plain"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8033)
