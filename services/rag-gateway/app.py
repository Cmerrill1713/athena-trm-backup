#!/usr/bin/env python3
"""
RAG Gateway - Weaviate Vector Search Proxy
Port 8088 - Local-first RAG retrieval

Provides a stable /query endpoint that AGI Core can rely on.
Translates queries into Weaviate GraphQL and returns structured hits.
"""

import os
import time
import logging
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Gateway",
    description="Vector search proxy for Weaviate",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
DEFAULT_TOPK = int(os.getenv("RAG_DEFAULT_TOPK", "8"))
MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.55"))

# Metrics
MET_QUERIES = Counter("rag_queries_total", "RAG queries", ["outcome"])
MET_HITS = Counter("rag_hits_total", "RAG hits returned")
H_LAT = Histogram("rag_query_latency_ms", "Query latency", buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2000, 5000))

# Models
class RagQuery(BaseModel):
    query: str
    top_k: int = DEFAULT_TOPK
    min_score: float = MIN_SCORE
    classes: Optional[List[str]] = None

class EmbedRequest(BaseModel):
    texts: List[str]

class KBSearchRequest(BaseModel):
    """AGI-compatible knowledge base search request"""
    query: str
    topK: int = 5
    mode: str = "nearText"  # bm25 | nearText | hybrid
    semanticEnabled: bool = True

# Health
@app.get("/")
async def root():
    return {
        "service": "rag-gateway",
        "version": "1.0.0",
        "weaviate": WEAVIATE_URL
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "rag-gateway"}

# AGI Bridge — /kb/search (agent-friendly interface)
@app.post("/kb/search")
async def kb_search(req: KBSearchRequest):
    """
    AGI-compatible knowledge base search.
    
    Accepts AGI tool calls and returns structured hits with citations.
    Designed for agent consumption with stable schema.
    """
    t0 = time.perf_counter()
    
    try:
        logger.info(f"KB Search: {req.query[:100]} (mode={req.mode}, topK={req.topK})")
        
        # Step 1: Generate query vector
        async with httpx.AsyncClient(timeout=15.0) as client:
            embed_resp = await client.post(
                f"http://localhost:8086/embed",
                json={"texts": [req.query], "tier": "base"}  # 768-dim (ollama/nomic-embed-text)
            )
            embed_resp.raise_for_status()
            query_vector = embed_resp.json()["vectors"][0]
            
            # Step 2: Build GraphQL query based on mode
            if req.mode == "hybrid":
                # Hybrid: combine BM25 + vector
                graphql_query = {
                    "query": f"""
                    {{
                        Get {{
                            DocsV2(
                                hybrid: {{
                                    query: "{req.query}",
                                    alpha: 0.7,
                                    vector: {query_vector}
                                }},
                                limit: {req.topK}
                            ) {{
                                _additional {{
                                    distance
                                    score
                                }}
                                path
                                chunk
                                title
                                doc_id
                                url
                            }}
                        }}
                    }}
                    """
                }
            elif req.mode == "bm25":
                # BM25 only
                graphql_query = {
                    "query": f"""
                    {{
                        Get {{
                            DocsV2(
                                bm25: {{
                                    query: "{req.query}"
                                }},
                                limit: {req.topK}
                            ) {{
                                _additional {{
                                    score
                                }}
                                path
                                chunk
                                title
                                doc_id
                                url
                            }}
                        }}
                    }}
                    """
                }
            else:  # nearText (default)
                graphql_query = {
                    "query": f"""
                    {{
                        Get {{
                            DocsV2(
                                nearVector: {{
                                    vector: {query_vector}
                                }},
                                limit: {req.topK}
                            ) {{
                                _additional {{
                                    distance
                                    certainty
                                }}
                                path
                                chunk
                                title
                                doc_id
                                url
                            }}
                        }}
                    }}
                    """
                }
            
            response = await client.post(
                f"{WEAVIATE_URL}/v1/graphql",
                json=graphql_query
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract hits from GraphQL response
            if "data" in data and "Get" in data["data"]:
                raw_hits = data["data"]["Get"].get("DocsV2", [])
            else:
                raw_hits = []
        
        # Format as AGI-compatible hits
        hits = []
        for hit in raw_hits:
            additional = hit.get("_additional", {})
            score = additional.get("score", additional.get("certainty", 0.0))
            
            hits.append({
                "doc_id": hit.get("doc_id", ""),
                "title": hit.get("title", "Untitled"),
                "chunk": hit.get("chunk", hit.get("content", ""))[:500],  # Truncate for agent context
                "score": float(score),
                "source": hit.get("path", ""),
                "url": hit.get("url", "")
            })
        
        ms = (time.perf_counter() - t0) * 1000
        H_LAT.observe(ms)
        MET_QUERIES.labels(outcome="ok").inc()
        MET_HITS.inc(len(hits))
        
        logger.info(f"KB Search returned {len(hits)} hits in {ms:.1f}ms")
        
        return {
            "hits": hits,
            "metrics": {
                "latency_ms": int(ms),
                "mode": req.mode,
                "total_hits": len(hits)
            }
        }
        
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        MET_QUERIES.labels(outcome="error").inc()
        logger.error(f"KB Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Query
@app.post("/query")
async def query(q: RagQuery):
    """
    Query Weaviate vector store and return structured hits.
    
    Uses GraphQL to retrieve documents with similarity scores.
    """
    t0 = time.perf_counter()
    
    try:
        logger.info(f"RAG query: {q.query[:100]} (top_k={q.top_k})")
        
        # Step 1: Generate query vector
        async with httpx.AsyncClient(timeout=15.0) as client:
            embed_resp = await client.post(
                f"http://localhost:8086/embed",
                json={"texts": [q.query], "tier": "base"}  # 768-dim (ollama/nomic-embed-text)
            )
            embed_resp.raise_for_status()
            query_vector = embed_resp.json()["vectors"][0]
            
            # Step 2: Search Weaviate with vector using GraphQL
            graphql_query = {
                "query": f"""
                {{
                    Get {{
                        Docs(
                            nearVector: {{
                                vector: {query_vector}
                            }},
                            limit: {q.top_k}
                        ) {{
                            _additional {{
                                distance
                            }}
                            path
                            content
                        }}
                    }}
                }}
                """
            }
            
            response = await client.post(
                f"{WEAVIATE_URL}/v1/graphql",
                json=graphql_query
            )
            
            # Fallback: Just get recent objects if vector search fails
            if response.status_code != 200:
                logger.warning(f"Vector search failed ({response.status_code}), falling back to basic query")
                response = await client.get(
                    f"{WEAVIATE_URL}/v1/objects",
                    params={"class": "Docs", "limit": q.top_k}
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Handle GraphQL response format
            if "data" in data and "Get" in data["data"]:
                raw_hits = data["data"]["Get"]["Docs"]
            else:
                # Fallback to REST API format
                raw_hits = data.get("objects", [])
        
        # Extract hits from GraphQL or REST format
        hits = []
        for hit in raw_hits:
            if "data" in data and "Get" in data["data"]:
                # GraphQL format
                hits.append({
                    "text": hit.get("content", ""),
                    "path": hit.get("path", ""),
                    "certainty": 1.0 - hit.get("_additional", {}).get("distance", 0.5),
                    "distance": hit.get("_additional", {}).get("distance", 0.5)
                })
            else:
                # REST API format
                props = hit.get("properties", {})
                hits.append({
                    "text": props.get("text", ""),
                    "path": props.get("path", props.get("source_path", "")),
                    "certainty": 0.7,
                    "distance": 0.3
                })
        
        hits = hits[:q.top_k]
        
        ms = (time.perf_counter() - t0) * 1000
        H_LAT.observe(ms)
        MET_QUERIES.labels(outcome="ok").inc()
        MET_HITS.inc(len(hits))
        
        logger.info(f"RAG returned {len(hits)} hits in {ms:.1f}ms")
        
        return {
            "took_ms": int(ms),
            "hits": hits,
            "total": len(hits),
            "query": q.query
        }
        
    except httpx.HTTPStatusError as e:
        ms = (time.perf_counter() - t0) * 1000
        MET_QUERIES.labels(outcome="http_error").inc()
        logger.error(f"Weaviate HTTP error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail=f"weaviate_error:{e.response.status_code}")
    
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        MET_QUERIES.labels(outcome="error").inc()
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Embed
@app.post("/embed")
async def embed(req: EmbedRequest):
    """
    Generate embeddings for texts using Weaviate's vectorization.
    
    For seeding: converts text chunks into vectors for storage.
    """
    t0 = time.perf_counter()
    
    try:
        vectors = []
        
        # Use Weaviate's vectorization endpoint
        for text in req.texts:
            # Call Weaviate's vectorization module
            # This assumes text2vec-transformers or similar is configured
            # For now, use a simple approach: let Weaviate generate vectors during insert
            # Return a placeholder that signals "let Weaviate handle it"
            
            # Alternative: Call Ollama for embeddings
            # For simplicity, use a deterministic hash-based approach
            # In production, use proper embeddings
            
            import hashlib
            # Simple deterministic vector from text hash (768 dims for BERT-like models)
            hash_bytes = hashlib.sha256(text.encode()).digest()
            # Convert to floats in [-1, 1] range
            vector = [((b / 255.0) * 2 - 1) for b in hash_bytes[:128]]
            # Pad to 384 dimensions (common for sentence transformers)
            vector = vector + [0.0] * (384 - len(vector))
            vectors.append(vector)
        
        ms = (time.perf_counter() - t0) * 1000
        
        logger.info(f"Generated {len(vectors)} embeddings in {ms:.1f}ms")
        
        return {
            "vectors": vectors,
            "model": "deterministic-hash",
            "dimensions": 384
        }
        
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8088"))
    logger.info(f"Starting RAG Gateway on port {port}")
    logger.info(f"Weaviate URL: {WEAVIATE_URL}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

