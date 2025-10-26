#!/usr/bin/env python3
"""
Minimal RAG Gateway - Direct Weaviate GraphQL queries
Simple, works with existing Docs class
"""
import os
import logging
import time
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Minimal RAG Gateway")

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
PORT = int(os.getenv("PORT", "8087"))

class RAGQuery(BaseModel):
    query: str
    top_k: int = 10

class RAGHit(BaseModel):
    path: str
    text: str
    score: float = 0.0

class RAGResponse(BaseModel):
    hits: List[RAGHit]
    took_ms: float
    total: int

@app.get("/health")
async def health():
    return {"status": "ok", "service": "minimal-rag-gateway"}

@app.post("/query")
async def query(q: RAGQuery) -> RAGResponse:
    """Direct GraphQL query to Weaviate"""
    start = time.time()
    
    logger.info(f"Minimal RAG query: {q.query} (top_k={q.top_k})")
    
    # Use BM25 keyword search (always works, no embeddings needed)
    query_text = q.query.replace('"', '\\"').replace('\n', ' ')
    
    graphql = {
        "query": f'''
        {{
          Get {{
            Docs(
              bm25: {{
                query: "{query_text}"
              }}
              limit: {q.top_k}
            ) {{
              path
              text
              _additional {{
                score
              }}
            }}
          }}
        }}
        '''
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{WEAVIATE_URL}/v1/graphql",
                json=graphql
            )
            resp.raise_for_status()
            data = resp.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return RAGResponse(hits=[], took_ms=0, total=0)
            
            raw_hits = data.get("data", {}).get("Get", {}).get("Docs", [])
            
            hits = [
                RAGHit(
                    path=h.get("path", "unknown"),
                    text=h.get("text", "")[:500],  # Truncate to 500 chars
                    score=h.get("_additional", {}).get("score", 0.0)
                )
                for h in raw_hits
            ]
            
            took_ms = (time.time() - start) * 1000
            logger.info(f"Returned {len(hits)} hits in {took_ms:.1f}ms")
            
            return RAGResponse(
                hits=hits,
                took_ms=took_ms,
                total=len(hits)
            )
            
    except Exception as e:
        logger.error(f"Query failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return RAGResponse(hits=[], took_ms=0, total=0)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Minimal RAG Gateway on port {PORT}")
    logger.info(f"Weaviate URL: {WEAVIATE_URL}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

