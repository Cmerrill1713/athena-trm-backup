#!/usr/bin/env python3
"""
Athena Knowledge Gateway Service
Search and routing for knowledge base
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import redis

app = FastAPI(title="Athena Knowledge Gateway Service", version="1.0.0")

# Redis connection
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Service URLs
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

class SearchRequest(BaseModel):
    query: str
    query_type: str = "hybrid"  # "semantic", "keyword", "hybrid"
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query_time_ms: float
    search_type: str

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

@app.post("/search", response_model=SearchResponse)
async def search_knowledge(request: SearchRequest):
    """Search knowledge base"""
    start_time = datetime.utcnow()

    try:
        results = []

        if request.query_type == "semantic" or request.query_type == "hybrid":
            # Semantic search using Weaviate
            semantic_results = await semantic_search(request.query, request.limit)
            results.extend(semantic_results)

        if request.query_type == "keyword" or request.query_type == "hybrid":
            # Keyword search using PostgreSQL
            keyword_results = await keyword_search(request.query, request.limit)
            results.extend(keyword_results)

        # Remove duplicates and sort by relevance
        seen_ids = set()
        unique_results = []
        for result in results:
            doc_id = result.get("id") or result.get("_additional", {}).get("id")
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(result)

        # Sort by relevance score (if available)
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Cache results
        cache_key = f"search:{hash(request.query)}:{request.query_type}:{request.limit}"
        redis_client.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps(unique_results[:request.limit])
        )

        return SearchResponse(
            results=unique_results[:request.limit],
            total_found=len(unique_results),
            query_time_ms=round(query_time, 2),
            search_type=request.query_type
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

async def semantic_search(query: str, limit: int) -> List[Dict[str, Any]]:
    """Perform semantic search using Weaviate"""
    try:
        async with httpx.AsyncClient() as client:
            gql_query = {
                "query": f"""
                {{
                    Get {{
                        KnowledgeDocument(
                            nearText: {{ concepts: ["{query}"] }}
                            limit: {limit}
                        ) {{
                            title
                            content
                            url
                            source
                            tags
                            _additional {{
                                id
                                distance
                            }}
                        }}
                    }}
                }}
                """
            }

            response = await client.post(
                f"{WEAVIATE_URL}/v1/graphql",
                json=gql_query,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                documents = data.get("data", {}).get("Get", {}).get("KnowledgeDocument", [])

                results = []
                for doc in documents:
                    # Convert distance to similarity score
                    distance = doc["_additional"]["distance"]
                    similarity = 1.0 - distance

                    results.append({
                        "id": doc["_additional"]["id"],
                        "title": doc["title"],
                        "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                        "url": doc["url"],
                        "source": doc["source"],
                        "tags": doc["tags"],
                        "score": similarity,
                        "search_type": "semantic"
                    })

                return results
            else:
                return []

    except Exception as e:
        print(f"Semantic search error: {e}")
        return []

async def keyword_search(query: str, limit: int) -> List[Dict[str, Any]]:
    """Perform keyword search using PostgreSQL"""
    try:
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        cur = conn.cursor()

        # Full-text search
        cur.execute("""
            SELECT id, title, content, url, source, tags,
                   ts_rank(to_tsvector('english', title || ' ' || content), 
                          plainto_tsquery('english', %s)) as rank
            FROM knowledge_documents
            WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
        """, (query, query, limit))

        results = []
        for row in cur.fetchall():
            doc_id, title, content, url, source, tags, rank = row

            results.append({
                "id": str(doc_id),
                "title": title,
                "content": content[:500] + "..." if len(content) > 500 else content,
                "url": url,
                "source": source,
                "tags": json.loads(tags) if tags else [],
                "score": float(rank),
                "search_type": "keyword"
            })

        cur.close()
        conn.close()

        return results

    except Exception as e:
        print(f"Keyword search error: {e}")
        return []

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Count cached searches
        cached_searches = len(redis_client.keys("search:*"))

        metrics_data = f"""# HELP athena_knowledge_searches_cached_total Cached search results
# TYPE athena_knowledge_searches_cached_total gauge
athena_knowledge_searches_cached_total {cached_searches}
"""
        return {"content": metrics_data, "content_type": "text/plain"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8032)
