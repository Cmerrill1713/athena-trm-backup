#!/usr/bin/env python3
"""
Unified Embedding Service - Multi-Tier Local Embeddings
Routes to MLX (fast), Ollama (balanced), or HuggingFace (precision) per tier
"""

import asyncio
import logging
import os
import time
from typing import List, Dict, Any, Optional
from enum import Enum

import httpx
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, start_http_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
MET_EMBEDS = Counter("embeddings_generated_total", "Embeddings generated", ["tier", "outcome"])
MET_LATENCY = Histogram("embedding_latency_ms", "Embedding generation latency", ["tier"])

class EmbeddingTier(Enum):
    MINI = "mini"    # MLX - fast, 384d
    BASE = "base"    # Ollama - balanced, 768d
    LONG = "long"    # HuggingFace/Ollama - precision, 1024d+

class EmbedRequest(BaseModel):
    texts: List[str]
    tier: Optional[str] = "base"  # "mini", "base", or "long"

class EmbeddingService:
    def __init__(self):
        self.app = FastAPI(title="Embedding Service", version="1.0.0")
        self.ollama_url = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        
        # Initialize sentence-transformers for MLX fallback
        try:
            from sentence_transformers import SentenceTransformer
            self.mini_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384d, fast
            logger.info("✅ Loaded sentence-transformers MiniLM model")
        except Exception as e:
            logger.warning(f"⚠️  sentence-transformers not available: {e}")
            self.mini_model = None
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/health")
        async def health():
            return {
                "status": "ok",
                "service": "embedding-service",
                "tiers": {
                    "mini": "sentence-transformers/MiniLM",
                    "base": "ollama/nomic-embed-text",
                    "long": "ollama/mxbai-embed-large"
                }
            }
        
        @self.app.post("/embed")
        async def embed(request: EmbedRequest):
            return await self.generate_embeddings(request.texts, request.tier)
    
    async def mlx_embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using MLX (Apple Silicon optimized)"""
        try:
            if self.mini_model:
                # Use sentence-transformers as MLX-compatible fallback
                vectors = self.mini_model.encode(texts, convert_to_numpy=True)
                return vectors.tolist()
            else:
                raise Exception("MLX/sentence-transformers not available")
        except Exception as e:
            logger.error(f"MLX embedding failed: {e}")
            raise
    
    async def ollama_embed(self, texts: List[str], model: str = "nomic-embed-text") -> List[List[float]]:
        """Generate embeddings using Ollama"""
        try:
            vectors = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for text in texts:
                    response = await client.post(
                        f"{self.ollama_url}/api/embeddings",
                        json={"model": model, "prompt": text}
                    )
                    response.raise_for_status()
                    data = response.json()
                    vectors.append(data["embedding"])
            
            return vectors
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str], tier: str = "base") -> Dict[str, Any]:
        """Route to appropriate embedder based on tier"""
        t0 = time.perf_counter()
        
        try:
            tier_enum = EmbeddingTier(tier.lower())
            
            if tier_enum == EmbeddingTier.MINI:
                # Use sentence-transformers MiniLM for fast lane (384-dim)
                vectors = await self.mlx_embed(texts)
                model_used = "sentence-transformers/MiniLM-L6-v2"
                
            elif tier_enum == EmbeddingTier.BASE:
                # Ollama nomic-embed-text for balanced
                vectors = await self.ollama_embed(texts, "nomic-embed-text")
                model_used = "ollama/nomic-embed-text"
                
            elif tier_enum == EmbeddingTier.LONG:
                # Use qwen3-embedding for precision (fallback until mxbai loads)
                vectors = await self.ollama_embed(texts, "qwen3-embedding:4b")
                model_used = "ollama/qwen3-embedding"
            
            else:
                raise ValueError(f"Unknown tier: {tier}")
            
            ms = (time.perf_counter() - t0) * 1000
            
            MET_EMBEDS.labels(tier=tier, outcome="ok").inc(len(texts))
            MET_LATENCY.labels(tier=tier).observe(ms)
            
            logger.info(f"Generated {len(vectors)} embeddings ({tier}) in {ms:.1f}ms using {model_used}")
            
            return {
                "vectors": vectors,
                "count": len(vectors),
                "dimension": len(vectors[0]) if vectors else 0,
                "tier": tier,
                "model": model_used,
                "took_ms": round(ms, 1)
            }
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            MET_EMBEDS.labels(tier=tier, outcome="error").inc()
            raise HTTPException(status_code=500, detail=str(e))

# Create FastAPI app
service = EmbeddingService()
app = service.app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8086"))
    logger.info(f"Starting Embedding Service on port {port}")
    logger.info(f"Ollama URL: {service.ollama_url}")
    
    # Start Prometheus metrics server
    start_http_server(9091)
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

