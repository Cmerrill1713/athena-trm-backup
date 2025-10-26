#!/usr/bin/env python3
"""
Dynamic RAG Gateway - Intelligent Multi-Tier Retrieval
Adapts resolution, model choice, and chunking per query complexity
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import httpx
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
MET_QUERIES = Counter("rag_dynamic_queries_total", "Dynamic RAG queries", ["lane", "outcome"])
MET_HITS = Counter("rag_dynamic_hits_total", "Dynamic RAG hits", ["class"])
MET_LATENCY = Histogram("rag_dynamic_latency_ms", "Dynamic RAG latency", ["lane"])
MET_FUSION = Counter("rag_fusion_operations_total", "Fusion operations", ["method"])
MET_RERANK = Counter("rag_rerank_operations_total", "Re-ranking operations", ["depth"])

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
RAG_GATEWAY_URL = os.getenv("RAG_GATEWAY_URL", "http://localhost:8087")

class QueryComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

class RetrievalLane(Enum):
    MINI = "mini"
    BASE = "base"
    LONG = "long"

@dataclass
class RetrievalPlan:
    """Plan for multi-tier retrieval"""
    lanes: List[Tuple[RetrievalLane, int]]  # (lane, top_k)
    fusion_method: str = "rrf"
    rerank_depth: int = 50
    context_budget: int = 2000

class DynamicQueryRequest(BaseModel):
    query: str
    top_k: int = 6
    importance: Optional[str] = None  # "low", "medium", "high" - overrides classifier
    context_budget: Optional[int] = None  # Override default budget

class EmbedRequest(BaseModel):
    texts: List[str]

class DynamicRAGGateway:
    def __init__(self):
        self.app = FastAPI(title="Dynamic RAG Gateway", version="1.0.0")
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.get("/health")
        async def health():
            return {"status": "ok", "service": "dynamic-rag-gateway"}
            
        @self.app.post("/query")
        async def dynamic_query(request: DynamicQueryRequest):
            return await self.handle_dynamic_query(request)
            
        @self.app.post("/embed")
        async def embed(request: EmbedRequest):
            return await self.generate_embeddings(request.texts)
    
    def classify_query_complexity(self, query: str) -> QueryComplexity:
        """Classify query complexity based on heuristics"""
        score = 0
        query_lower = query.lower()
        
        # Length-based scoring
        if len(query) > 120:
            score += 1
        if len(query) > 200:
            score += 1
            
        # Complexity indicators
        complexity_keywords = [
            "why", "how", "compare", "design", "architecture", "schema", 
            "incident", "optimize", "performance", "debug", "troubleshoot",
            "analysis", "explain", "difference", "relationship", "dependency"
        ]
        if any(kw in query_lower for kw in complexity_keywords):
            score += 1
            
        # Code-specific indicators
        code_indicators = ["```", "def ", "class ", "function", "method", "api", "endpoint"]
        if any(indicator in query_lower for indicator in code_indicators):
            score += 1
            
        # Technical depth indicators
        tech_keywords = ["implementation", "algorithm", "data structure", "pattern", "framework"]
        if any(kw in query_lower for kw in tech_keywords):
            score += 1
            
        # Multi-part questions
        if query.count("?") > 1 or " and " in query_lower:
            score += 1
            
        # Map score to complexity
        if score <= 1:
            return QueryComplexity.LOW
        elif score <= 3:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.HIGH
    
    def create_retrieval_plan(self, complexity: QueryComplexity, importance: Optional[str] = None) -> RetrievalPlan:
        """Create retrieval plan based on query complexity"""
        # Override complexity if importance is specified
        if importance:
            complexity = QueryComplexity(importance.lower())
            
        plans = {
            QueryComplexity.LOW: RetrievalPlan(
                lanes=[(RetrievalLane.MINI, 8)],
                fusion_method="none",
                rerank_depth=0,
                context_budget=1000
            ),
            QueryComplexity.MEDIUM: RetrievalPlan(
                lanes=[(RetrievalLane.MINI, 8), (RetrievalLane.BASE, 12)],
                fusion_method="rrf",
                rerank_depth=30,
                context_budget=3000
            ),
            QueryComplexity.HIGH: RetrievalPlan(
                lanes=[(RetrievalLane.MINI, 8), (RetrievalLane.BASE, 16), (RetrievalLane.LONG, 20)],
                fusion_method="rrf",
                rerank_depth=50,
                context_budget=5000
            )
        }
        
        return plans[complexity]
    
    async def hybrid_search(self, lane: RetrievalLane, query: str, top_k: int) -> List[Dict]:
        """Perform hybrid search (vector + BM25) on specified lane"""
        try:
            # Map lane to embedding tier
            tier_mapping = {
                RetrievalLane.MINI: "mini",
                RetrievalLane.BASE: "base",
                RetrievalLane.LONG: "long"
            }
            tier = tier_mapping[lane]
            
            # Generate query embedding from embedding service
            embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8086")
            
            async with httpx.AsyncClient(timeout=15.0) as embed_client:
                embed_resp = await embed_client.post(
                    f"{embedding_url}/embed",
                    json={"texts": [query], "tier": tier}
                )
                embed_resp.raise_for_status()
                query_vector = embed_resp.json()["vectors"][0]
            
            # Map lane to Weaviate class
            class_mapping = {
                RetrievalLane.MINI: "ChunkMini",
                RetrievalLane.BASE: "Docs",  # Keep existing class
                RetrievalLane.LONG: "ChunkLong"
            }
            
            class_name = class_mapping[lane]
            
            # GraphQL query for hybrid search
            graphql_query = {
                "query": f"""
                {{
                    Get {{
                        {class_name}(
                            nearVector: {{
                                vector: {query_vector}
                            }},
                            limit: {top_k}
                        ) {{
                            _additional {{
                                distance
                                id
                            }}
                            canonical_id
                            repo_path
                            file
                            symbol
                            lang
                            section
                            text
                            granularity
                            source_mtime
                            commit
                        }}
                    }}
                }}
                """
            }
            
            # Execute GraphQL query with new client
            async with httpx.AsyncClient(timeout=15.0) as weaviate_client:
                response = await weaviate_client.post(
                    f"{WEAVIATE_URL}/v1/graphql",
                    json=graphql_query
                )
                response.raise_for_status()
                data = response.json()
            
            if "data" in data and "Get" in data["data"]:
                raw_hits = data["data"]["Get"][class_name]
            else:
                raw_hits = []
                
            # Convert to standard format
            hits = []
            for hit in raw_hits:
                hits.append({
                    "canonical_id": hit.get("canonical_id", ""),
                    "text": hit.get("text", ""),
                    "path": hit.get("repo_path", ""),
                    "file": hit.get("file", ""),
                    "symbol": hit.get("symbol", ""),
                    "lang": hit.get("lang", ""),
                    "section": hit.get("section", ""),
                    "granularity": hit.get("granularity", "fine"),
                    "source_mtime": hit.get("source_mtime", 0),
                    "commit": hit.get("commit", ""),
                    "distance": hit.get("_additional", {}).get("distance", 0.5),
                    "certainty": 1.0 - hit.get("_additional", {}).get("distance", 0.5),
                    "lane": lane.value
                })
            
            MET_HITS.labels(class_name).inc(len(hits))
            return hits
                
        except Exception as e:
            logger.error(f"Hybrid search failed for {lane}: {e}")
            return []
    
    def reciprocal_rank_fusion(self, hit_pools: List[List[Dict]], k: int = 50) -> List[Dict]:
        """Fuse results using Reciprocal Rank Fusion"""
        canonical_scores = {}
        
        for pool in hit_pools:
            for rank, hit in enumerate(pool):
                canonical_id = hit.get("canonical_id", "")
                if not canonical_id:
                    continue
                    
                # RRF score: 1 / (60 + rank)
                rrf_score = 1.0 / (60 + rank)
                
                if canonical_id in canonical_scores:
                    canonical_scores[canonical_id]["score"] += rrf_score
                    canonical_scores[canonical_id]["lanes"].add(hit.get("lane", "unknown"))
                else:
                    canonical_scores[canonical_id] = {
                        "score": rrf_score,
                        "hit": hit,
                        "lanes": {hit.get("lane", "unknown")}
                    }
        
        # Sort by RRF score and return top-k
        fused = sorted(canonical_scores.values(), key=lambda x: x["score"], reverse=True)[:k]
        
        # Add fusion metadata
        for item in fused:
            item["hit"]["fusion_score"] = item["score"]
            item["hit"]["lanes_contributing"] = list(item["lanes"])
            
        MET_FUSION.labels(method="rrf").inc()
        return [item["hit"] for item in fused]
    
    def deduplicate_by_canonical_id(self, hits: List[Dict]) -> List[Dict]:
        """Remove duplicates based on canonical_id"""
        seen = set()
        deduped = []
        
        for hit in hits:
            canonical_id = hit.get("canonical_id", "")
            if canonical_id and canonical_id not in seen:
                seen.add(canonical_id)
                deduped.append(hit)
                
        return deduped
    
    def cross_encoder_rerank(self, query: str, hits: List[Dict], top_n: int) -> List[Dict]:
        """Simple re-ranking based on text similarity (placeholder for real cross-encoder)"""
        if not hits or top_n <= 0:
            return hits
            
        # Simple TF-IDF-like scoring as placeholder
        query_words = set(query.lower().split())
        
        for hit in hits:
            text_words = set(hit.get("text", "").lower().split())
            overlap = len(query_words.intersection(text_words))
            hit["rerank_score"] = overlap / max(len(query_words), 1)
        
        # Sort by rerank score and return top-n
        reranked = sorted(hits, key=lambda x: x.get("rerank_score", 0), reverse=True)[:top_n]
        
        MET_RERANK.labels(depth=len(hits)).inc()
        return reranked
    
    async def handle_dynamic_query(self, request: DynamicQueryRequest) -> Dict[str, Any]:
        """Handle dynamic RAG query with adaptive retrieval"""
        t0 = time.perf_counter()
        
        try:
            # Classify query complexity
            complexity = self.classify_query_complexity(request.query)
            
            # Create retrieval plan
            plan = self.create_retrieval_plan(complexity, request.importance)
            
            # Override context budget if specified
            if request.context_budget:
                plan.context_budget = request.context_budget
            
            logger.info(f"Dynamic retrieval: complexity={complexity.value}, lanes={len(plan.lanes)}")
            
            # Execute multi-lane retrieval
            hit_pools = []
            for lane, top_k in plan.lanes:
                hits = await self.hybrid_search(lane, request.query, top_k)
                hit_pools.append(hits)
                logger.info(f"Lane {lane.value}: {len(hits)} hits (canonical_ids: {[(h.get('canonical_id') or 'MISSING')[:8] for h in hits[:3]]})")
            
            # Fuse results if multiple lanes
            if len(hit_pools) > 1 and plan.fusion_method == "rrf":
                fused = self.reciprocal_rank_fusion(hit_pools, k=plan.rerank_depth or 50)
                logger.info(f"RRF fusion: {len(fused)} hits after fusion")
            else:
                fused = hit_pools[0] if hit_pools else []
                logger.info(f"No fusion: {len(fused)} hits from single lane")
            
            # Deduplicate by canonical ID
            deduped = self.deduplicate_by_canonical_id(fused)
            logger.info(f"After dedup: {len(deduped)} unique hits")
            
            # Re-rank if specified
            if plan.rerank_depth > 0 and deduped:
                reranked = self.cross_encoder_rerank(request.query, deduped, request.top_k)
                logger.info(f"After rerank: {len(reranked)} hits")
            else:
                reranked = deduped[:request.top_k]
            
            # Apply context budget
            budgeted_hits = []
            current_chars = 0
            for hit in reranked:
                text_len = len(hit.get("text", ""))
                if current_chars + text_len <= plan.context_budget:
                    budgeted_hits.append(hit)
                    current_chars += text_len
                else:
                    break
            
            logger.info(f"After budgeting: {len(budgeted_hits)} hits, {current_chars} chars")
            
            # Calculate metrics
            ms = (time.perf_counter() - t0) * 1000
            total_hits = sum(len(pool) for pool in hit_pools)
            
            MET_QUERIES.labels(lane=complexity.value, outcome="ok").inc()
            MET_LATENCY.labels(lane=complexity.value).observe(ms)
            
            return {
                "query": request.query,
                "complexity": complexity.value,
                "plan": {
                    "lanes": [f"{lane.value}:{top_k}" for lane, top_k in plan.lanes],
                    "fusion_method": plan.fusion_method,
                    "rerank_depth": plan.rerank_depth,
                    "context_budget": plan.context_budget
                },
                "total_hits": total_hits,
                "fused_hits": len(fused),
                "final_hits": len(budgeted_hits),
                "context_chars": current_chars,
                "hits": budgeted_hits,
                "took_ms": round(ms, 1)
            }
            
        except Exception as e:
            logger.error(f"Dynamic query failed: {e}")
            MET_QUERIES.labels(lane="unknown", outcome="error").inc()
            raise HTTPException(status_code=500, detail=str(e))
    
    async def generate_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """Generate deterministic hash-based embeddings (placeholder)"""
        vectors = []
        for text in texts:
            # Generate deterministic hash-based vector
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to 768-dimensional vector
            vector = []
            for i in range(0, min(len(hash_bytes), 96), 4):  # 96 bytes = 24 floats
                chunk = hash_bytes[i:i+4]
                while len(chunk) < 4:
                    chunk += b'\x00'
                val = int.from_bytes(chunk, 'big') / (2**32)
                vector.append(val)
            
            # Pad to 768 dimensions
            while len(vector) < 768:
                vector.append(0.0)
            
            vectors.append(vector[:768])
        
        return {"vectors": vectors}

# Create FastAPI app
gateway = DynamicRAGGateway()
app = gateway.app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8087"))
    logger.info(f"Starting Dynamic RAG Gateway on port {port}")
    logger.info(f"Weaviate URL: {WEAVIATE_URL}")
    
    # Start Prometheus metrics server
    start_http_server(9090)
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
