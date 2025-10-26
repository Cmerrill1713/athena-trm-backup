#!/usr/bin/env python3
"""
Model Pool Manager - Hot-Swap Service for Ollama/MLX
Manages GPU exclusivity, model warming, and intelligent swapping
"""

import asyncio
import logging
import os
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict, deque

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics (hardened set)
MET_INFER = Counter("model_pool_infer_total", "Inference requests", ["model", "outcome"])
MET_SWAPS = Counter("model_pool_hotswaps_total", "Model swaps", ["from_model", "to_model"])
MET_ACTIVE_SECONDS = Counter("model_pool_active_seconds_total", "Total seconds model was active", ["model"])
MET_WARM_LAT = Histogram("model_pool_warmup_latency_ms", "Model warm-up latency", ["model"], 
                         buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000])
MET_FIRST_TOKEN = Histogram("model_pool_first_token_latency_ms", "First token latency", ["model", "warm_state"],
                            buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000])
MET_QUEUE_DEPTH = Gauge("model_pool_queue_depth", "Current queue depth")
MET_EVICTS = Counter("model_pool_evicts_total", "Model evictions", ["model", "reason"])
MET_VRAM_MB = Gauge("model_pool_vram_used_mb", "Current VRAM usage estimate")
MET_REQUESTS_QUEUED = Counter("model_pool_requests_queued_total", "Requests queued", ["model"])

class WarmState(Enum):
    COLD = "cold"      # Not loaded at all
    WARM = "warm"      # Loaded but needs warmup
    HOT = "hot"        # Active and ready

@dataclass
class ModelSpec:
    """Model specification and state"""
    model_id: str
    endpoint: str  # e.g., "ollama", "mlx", "custom"
    model_name: str  # e.g., "qwen2.5:7b", "mistral:7b"
    vram_mb: int = 4096  # Estimated VRAM usage
    n_gpu_layers: int = -1  # -1 = all, or specific count
    keep_alive: int = 60  # Seconds to keep loaded
    warm_state: WarmState = WarmState.COLD
    last_used: float = field(default_factory=time.time)
    warm_count: int = 0
    infer_count: int = 0

class InferRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False

class WarmRequest(BaseModel):
    model: str

class ModelPoolManager:
    def __init__(self):
        self.app = FastAPI(title="Model Pool Manager", version="1.0.0")
        self.ollama_url = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        
        # Load routing policy
        self.config = self._load_config()
        
        # Model registry (LRU-ordered)
        self.models: OrderedDict[str, ModelSpec] = OrderedDict()
        
        # GPU lock (only one model active at a time)
        self.gpu_lock = asyncio.Lock()
        self.active_model_id: Optional[str] = None
        self.active_since: Optional[float] = None
        
        # Request queue
        self.queue: deque = deque()
        self.max_queue_depth = self.config.get("guardrails", {}).get("max_queue_depth", 20)
        
        # Swap tracking (for storm detection)
        self.recent_swaps: deque = deque(maxlen=100)  # Last 100 swaps with timestamps
        
        # Register models from config
        self._register_models_from_config()
        self.setup_routes()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load routing policy from YAML"""
        config_path = Path("/Users/christianmerrill/Documents/GitHub/config/routing_policy.yaml")
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"✅ Loaded routing policy from {config_path}")
                return config
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        # Return minimal defaults if config not found
        return {
            "routing": {
                "complexity": {
                    "low": {"model": "fast", "rag_lanes": ["mini:8"], "max_context_chars": 1000},
                    "medium": {"model": "balanced", "rag_lanes": ["mini:8", "base:12"], "max_context_chars": 3000},
                    "high": {"model": "precise", "rag_lanes": ["mini:8", "base:16", "long:20"], "max_context_chars": 5000}
                }
            }
        }
    
    def _register_models_from_config(self):
        """Register models from config"""
        models_config = self.config.get("routing", {}).get("models", {})
        
        if not models_config:
            # Fallback to defaults
            self._register_default_models()
            return
        
        for model_id, model_cfg in models_config.items():
            spec = ModelSpec(
                model_id=model_id,
                endpoint="ollama",
                model_name=model_cfg.get("ollama_model", model_id),
                vram_mb=model_cfg.get("vram_mb", 4096),
                n_gpu_layers=model_cfg.get("n_gpu_layers", -1),
                keep_alive=self.config.get("routing", {}).get("complexity", {}).get("low", {}).get("keep_alive_seconds", 60)
            )
            self.models[model_id] = spec
            logger.info(f"Registered from config: {model_id} ({spec.model_name}, ~{spec.vram_mb}MB)")
    
    def _register_default_models(self):
        """Register default Ollama models + TRM"""
        default_models = [
            ModelSpec("fast", "ollama", "qwen2.5:0.5b", vram_mb=512, keep_alive=300),
            ModelSpec("balanced", "ollama", "qwen2.5:7b", vram_mb=4096, keep_alive=180),
            ModelSpec("precise", "ollama", "qwen2.5:14b", vram_mb=8192, keep_alive=60),
            ModelSpec("code", "ollama", "qwen3-coder:30b", vram_mb=16384, keep_alive=60),
            ModelSpec("trm-reasoning", "trm-service", "trm-7m-mlx", vram_mb=256, keep_alive=300),
        ]
        
        for model in default_models:
            self.models[model.model_id] = model
            logger.info(f"Registered model: {model.model_id} ({model.model_name}, ~{model.vram_mb}MB)")
    
    def setup_routes(self):
        @self.app.get("/health")
        async def health():
            return {
                "status": "ok",
                "service": "model-pool",
                "active_model": self.active_model_id,
                "models_registered": len(self.models)
            }
        
        @self.app.get("/status")
        async def status():
            # Calculate swap rate (last 5 minutes)
            now = time.time()
            recent_swaps_5m = [s for s in self.recent_swaps if now - s < 300]
            
            # Calculate active VRAM
            active_vram_mb = 0
            if self.active_model_id and self.active_model_id in self.models:
                active_vram_mb = self.models[self.active_model_id].vram_mb
            
            # Update VRAM gauge
            MET_VRAM_MB.set(active_vram_mb)
            
            # Calculate queue depth
            queue_depth = len(self.queue)
            MET_QUEUE_DEPTH.set(queue_depth)
            
            return {
                "active_model": self.active_model_id,
                "warm_state": self.models[self.active_model_id].warm_state.value if self.active_model_id else None,
                "loaded": [mid for mid, spec in self.models.items() if spec.warm_state != WarmState.COLD],
                "queue_depth": queue_depth,
                "vram_mb": active_vram_mb,
                "hotswaps_5m": len(recent_swaps_5m),
                "models": {
                    model_id: {
                        "warm_state": spec.warm_state.value,
                        "last_used": spec.last_used,
                        "idle_seconds": round(now - spec.last_used, 1),
                        "infer_count": spec.infer_count,
                        "warm_count": spec.warm_count,
                        "vram_mb": spec.vram_mb,
                        "keep_alive": spec.keep_alive
                    }
                    for model_id, spec in self.models.items()
                },
                "gpu_locked": self.gpu_lock.locked(),
                "config_loaded": bool(self.config)
            }
        
        @self.app.post("/infer")
        async def infer(request: InferRequest):
            return await self.handle_inference(request)
        
        @self.app.post("/warm")
        async def warm(request: WarmRequest):
            return await self.warm_model(request.model)
        
        @self.app.post("/evict")
        async def evict(request: WarmRequest):
            return await self.evict_model(request.model)
    
    async def warm_model(self, model_id: str, force: bool = False) -> Dict[str, Any]:
        """Warm up a model (load + compile + 1-token pass)"""
        if model_id not in self.models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        spec = self.models[model_id]
        
        # Skip if already hot and not forcing
        if spec.warm_state == WarmState.HOT and not force:
            logger.info(f"Model {model_id} already hot, skipping warm-up")
            return {
                "model": model_id,
                "warm_state": "hot",
                "skipped": True,
                "took_ms": 0
            }
        
        t0 = time.perf_counter()
        
        try:
            # Send a ping/warmup request to Ollama
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Small warmup prompt
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": spec.model_name,
                        "prompt": "ping",
                        "stream": False,
                        "options": {
                            "num_predict": 1
                        }
                    }
                )
                response.raise_for_status()
            
            spec.warm_state = WarmState.HOT
            spec.warm_count += 1
            spec.last_used = time.time()
            
            ms = (time.perf_counter() - t0) * 1000
            
            MET_WARM_LAT.labels(model=model_id, warm_state="cold" if spec.warm_count == 1 else "warm").observe(ms)
            
            logger.info(f"✅ Warmed {model_id} in {ms:.1f}ms")
            
            return {
                "model": model_id,
                "warm_state": "hot",
                "took_ms": round(ms, 1),
                "warm_count": spec.warm_count
            }
            
        except Exception as e:
            logger.error(f"Failed to warm {model_id}: {e}")
            spec.warm_state = WarmState.COLD
            raise HTTPException(status_code=500, detail=str(e))
    
    async def evict_model(self, model_id: str, reason: str = "manual") -> Dict[str, Any]:
        """Evict a model from GPU (free VRAM)"""
        if model_id not in self.models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        spec = self.models[model_id]
        
        if spec.warm_state == WarmState.COLD:
            return {
                "model": model_id,
                "warm_state": "cold",
                "already_evicted": True
            }
        
        try:
            # Tell Ollama to unload the model
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use keep_alive=0 to immediately unload
                await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": spec.model_name,
                        "prompt": "",
                        "keep_alive": 0
                    }
                )
            
            spec.warm_state = WarmState.COLD
            MET_EVICTS.labels(model=model_id, reason=reason).inc()
            
            logger.info(f"✅ Evicted {model_id} (reason: {reason})")
            
            return {
                "model": model_id,
                "warm_state": "cold",
                "evicted": True,
                "reason": reason
            }
            
        except Exception as e:
            logger.warning(f"Failed to evict {model_id}: {e}")
            return {
                "model": model_id,
                "error": str(e)
            }
    
    async def swap_models(self, from_model_id: Optional[str], to_model_id: str) -> Dict[str, Any]:
        """Swap from one model to another with GPU exclusivity"""
        t0 = time.perf_counter()
        
        # Track active time for old model
        if from_model_id and self.active_since:
            active_duration = time.time() - self.active_since
            MET_ACTIVE_SECONDS.labels(model=from_model_id).inc(active_duration)
        
        # Evict old model if different
        if from_model_id and from_model_id != to_model_id:
            logger.info(f"Swapping: {from_model_id} → {to_model_id}")
            MET_SWAPS.labels(from_model=from_model_id, to_model=to_model_id).inc()
            
            # Track swap for storm detection
            self.recent_swaps.append(time.time())
            
            # Check for swap storm
            now = time.time()
            swaps_5m = len([s for s in self.recent_swaps if now - s < 300])
            if swaps_5m > 30:
                logger.warning(f"⚠️  Swap storm detected: {swaps_5m} swaps in 5 minutes")
            
            await self.evict_model(from_model_id, reason="swap")
        
        # Warm new model
        warm_result = await self.warm_model(to_model_id)
        
        # Update active model
        self.active_model_id = to_model_id
        self.active_since = time.time()
        
        ms = (time.perf_counter() - t0) * 1000
        
        return {
            "from_model": from_model_id,
            "to_model": to_model_id,
            "swapped": from_model_id != to_model_id,
            "warm_result": warm_result,
            "swap_ms": round(ms, 1)
        }
    
    async def handle_inference(self, request: InferRequest) -> Dict[str, Any]:
        """Handle inference with automatic model swapping"""
        t0 = time.perf_counter()
        
        if request.model not in self.models:
            raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
        
        spec = self.models[request.model]
        
        # Acquire GPU lock (exclusive access)
        async with self.gpu_lock:
            # Swap if needed
            swap_result = None
            if self.active_model_id != request.model:
                swap_result = await self.swap_models(self.active_model_id, request.model)
            elif spec.warm_state != WarmState.HOT:
                # Model is "active" but not warm - warm it up
                await self.warm_model(request.model)
            
            # Run inference
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    t_infer = time.perf_counter()
                    
                    response = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": spec.model_name,
                            "prompt": request.prompt,
                            "stream": request.stream,
                            "options": {
                                "num_predict": request.max_tokens,
                                "temperature": request.temperature
                            }
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    infer_ms = (time.perf_counter() - t_infer) * 1000
                    
                    # Update metrics
                    spec.last_used = time.time()
                    spec.infer_count += 1
                    
                    MET_INFER.labels(model=request.model, outcome="ok").inc()
                    
                    # Record first token latency
                    warm_state_label = "hot" if swap_result is None else "warm"
                    MET_FIRST_TOKEN.labels(model=request.model, warm_state=warm_state_label).observe(infer_ms)
                    
                    total_ms = (time.perf_counter() - t0) * 1000
                    
                    return {
                        "model": request.model,
                        "response": result.get("response", ""),
                        "swap_performed": swap_result is not None,
                        "swap_ms": swap_result.get("swap_ms", 0) if swap_result else 0,
                        "infer_ms": round(infer_ms, 1),
                        "total_ms": round(total_ms, 1),
                        "warm_state": warm_state_label,
                        "tokens": {
                            "prompt": result.get("prompt_eval_count", 0),
                            "response": result.get("eval_count", 0)
                        }
                    }
                    
            except Exception as e:
                logger.error(f"Inference failed for {request.model}: {e}")
                MET_INFER.labels(model=request.model, outcome="error").inc()
                raise HTTPException(status_code=500, detail=str(e))
    
    async def background_eviction(self):
        """Background task to evict idle models"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            try:
                now = time.time()
                
                for model_id, spec in list(self.models.items()):
                    # Skip active model
                    if model_id == self.active_model_id:
                        continue
                    
                    # Skip if not hot
                    if spec.warm_state != WarmState.HOT:
                        continue
                    
                    # Check if idle for longer than keep_alive
                    idle_seconds = now - spec.last_used
                    if idle_seconds > spec.keep_alive:
                        logger.info(f"Auto-evicting {model_id} (idle for {idle_seconds:.0f}s)")
                        await self.evict_model(model_id, reason="idle_timeout")
                        
            except Exception as e:
                logger.error(f"Background eviction failed: {e}")

# Create service
pool_manager = ModelPoolManager()
app = pool_manager.app

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(pool_manager.background_eviction())
    logger.info("✅ Model pool manager started")
    logger.info(f"Registered models: {list(pool_manager.models.keys())}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8085"))
    logger.info(f"Starting Model Pool Manager on port {port}")
    logger.info(f"Ollama URL: {pool_manager.ollama_url}")
    
    # Start Prometheus metrics server
    start_http_server(9092)
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

