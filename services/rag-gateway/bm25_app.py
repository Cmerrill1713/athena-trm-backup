#!/usr/bin/env python3
"""
RAG Gateway with BM25 keyword search only (no embeddings needed)
Works with existing Docs class that has no vectors
"""
import os
import logging
from typing import Optional, List
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Gateway (BM25)")

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
PORT = int(os.getenv("PORT", "8087"))

class RAGQuery(BaseModel):
    query: str
    top_k: int = 10
    classes: Optional[List[str]] = None

class RAGHit(BaseModel):
    path: str
    text: str
    score: float

class RAGResponse(BaseModel):
    hits: List[RAGHit]
    took_ms: float
    total: int

@app.get("/health")
async def health():
    return {"status": "ok", "search_mode": "bm25_keyword"}

@app.post("/query")
async def query(q: RAGQuery) -> RAGResponse:
    """BM25 keyword search - no embeddings needed"""
    import time
    start = time.time()
    
    logger.info(f"BM25 query: {q.query} (top_k={q.top_k})")
    
    # BM25 keyword search via Weaviate
    graphql_query = """
    {
      Get {
        Docs(
          bm25: {
            query: "%s"
          }
          limit: %d
        ) {
          path
          text
          _additional {
            score
          }
        }
      }
    }
    """ % (q.query.replace('"', '\\"'), q.top_k)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{WEAVIATE_URL}/v1/graphql",
                json={"query": graphql_query}
            )
            resp.raise_for_status()
            data = resp.json()
            
            raw_hits = data.get("data", {}).get("Get", {}).get("Docs", [])
            
            hits = [
                RAGHit(
                    path=h.get("path", ""),
                    text=h.get("text", ""),
                    score=h.get("_additional", {}).get("score", 0.0)
                )
                for h in raw_hits
            ]
            
            took_ms = (time.time() - start) * 1000
            logger.info(f"BM25 returned {len(hits)} hits in {took_ms:.1f}ms")
            
            return RAGResponse(
                hits=hits,
                took_ms=took_ms,
                total=len(hits)
            )
            
        except Exception as e:
            logger.error(f"BM25 query failed: {e}")
            return RAGResponse(hits=[], took_ms=0, total=0)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting BM25 RAG Gateway on port {PORT}")
    logger.info(f"Weaviate URL: {WEAVIATE_URL}")
    logger.info("Search mode: BM25 keyword only (no embeddings)")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

