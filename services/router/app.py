#!/usr/bin/env python3
"""
Athena Router - Local-first model routing with governance
Port 9113 | MLX → Ollama → MCP-Browser → Cloud (governed)
"""
import os
import sys
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, 
    CONTENT_TYPE_LATEST
)
import yaml

# Import providers and health
from health import HealthMonitor
from providers.mlx_provider import MLXProvider
from providers.ollama_provider import OllamaProvider
from providers.mcp_browser_provider import MCPBrowserProvider
from providers.cloud_provider import CloudProvider
from providers.vision_fastvlm import FastVLMProvider
from providers.tts_kokoro import KokoroTTSProvider
from providers.uai_provider import UAIProvider

# Build version tracking
BUILD = os.getenv("BUILD_SHA", "dev")
FEATURE_MCP = os.getenv("FEATURE_MCP", "1") == "1"
FEATURE_SEARCH = os.getenv("FEATURE_SEARCH", "1") == "1"

# Import intent respond function
from intent import respond

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

router_requests_total = Counter(
    'athena_router_requests_total',
    'Total routing requests',
    ['route', 'status']
)

router_decisions_count = Counter(
    'athena_router_decisions_count',
    'Routing decisions made',
    ['route']
)

router_failovers_count = Counter(
    'athena_router_failovers_count',
    'Provider failovers',
    ['from_provider', 'to_provider', 'reason']
)

router_latency_seconds = Histogram(
    'athena_router_latency_seconds',
    'End-to-end routing latency',
    ['route'],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 5.0]
)

router_cloud_attempts_total = Counter(
    'athena_router_cloud_attempts_total',
    'Cloud routing attempts (should be 0)',
    ['blocked']
)

router_allow_cloud_gauge = Gauge(
    'athena_router_allow_cloud',
    'Cloud routing enabled (0=disabled, 1=enabled)'
)

router_cache_hits = Counter(
    'athena_router_cache_hits_total',
    'Prompt cache hits'
)

router_cache_misses = Counter(
    'athena_router_cache_misses_total',
    'Prompt cache misses'
)

# A3: Canary metrics
router_ece_estimate = Gauge(
    'athena_router_ece_estimate',
    'Expected cost error estimate for route decisions',
    ['route']
)

governance_canary_active = Gauge(
    'athena_governance_canary_active',
    'Canary deployment active (0=disabled, 1=active)'
)

canary_rollback_total = Counter(
    'athena_canary_rollback_total',
    'Total canary rollbacks triggered',
    ['reason']
)

# Modal-specific metrics
router_vision_latency_seconds = Histogram(
    'athena_vision_latency_seconds',
    'Vision analysis latency',
    ['route'],
    buckets=[0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
)

router_voice_latency_seconds = Histogram(
    'athena_voice_latency_seconds',
    'Voice synthesis latency',
    ['route'],
    buckets=[0.05, 0.1, 0.2, 0.35, 0.5, 1.0]
)

router_modality_requests_total = Counter(
    'athena_route_selection_total',
    'Route selections by modality',
    ['route', 'modality']
)

router_modality_ece = Gauge(
    'athena_modality_ece_estimate',
    'ECE estimate per modality',
    ['modality']
)

# ============================================================================
# CONFIGURATION & STATE
# ============================================================================

class RouterConfig:
    """Router configuration loaded from policy file."""
    
    def __init__(self, policy_path: str):
        self.policy_path = policy_path
        self.reload()
    
    def reload(self):
        """Reload policy from disk."""
        try:
            with open(self.policy_path, 'r') as f:
                policy = yaml.safe_load(f)
            
            self.order = policy.get('order', ['mlx', 'ollama', 'mcp_browser', 'cloud'])
            self.timeouts_ms = policy.get('timeouts_ms', {
                'mlx': 1500,
                'ollama': 2000,
                'mcp_browser': 4000,
                'cloud': 5000
            })
            self.max_tokens = policy.get('max_tokens', 1024)
            self.allow_cloud = policy.get('allow_cloud', False)
            self.failure_backoff_s = policy.get('failure_backoff_s', [1, 2, 5, 15, 60])
            
            logger.info(f"✅ Policy loaded: {self.order}, cloud={self.allow_cloud}")
        except Exception as e:
            logger.error(f"❌ Failed to load policy: {e}")
            # Use safe defaults
            self.order = ['mlx', 'ollama']
            self.timeouts_ms = {'mlx': 1500, 'ollama': 2000}
            self.max_tokens = 1024
            self.allow_cloud = False
            self.failure_backoff_s = [1, 2, 5, 15, 60]

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RouteRequest(BaseModel):
    """Routing request."""
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    model_hint: Optional[str] = None

class RouteResponse(BaseModel):
    """Routing response with inference result."""
    route: str
    text: str
    latency_ms: float
    tokens_generated: Optional[int] = None
    cached: bool = False
    provider_health: Dict[str, Any]
    decision_reasoning: str

class VisionAnalyzeRequest(BaseModel):
    """Vision analysis request."""
    image_b64: str
    prompt: Optional[str] = "Describe the image in detail"

class VisionAnalyzeResponse(BaseModel):
    """Vision analysis response."""
    result: Dict[str, Any]
    route: str
    latency_ms: float
    modality: str = "vision"

class TTSSynthesizeRequest(BaseModel):
    """TTS synthesis request."""
    text: str
    voice: Optional[str] = None

class TTSSynthesizeResponse(BaseModel):
    """TTS synthesis response."""
    audio_b64: str
    duration_ms: int
    sample_rate: int
    route: str
    latency_ms: float
    modality: str = "voice"

# ============================================================================
# DECISION LOGGER
# ============================================================================

class DecisionLogger:
    """Logs routing decisions to JSONL for explainability."""
    
    def __init__(self, log_path: str = "/tmp/router_decisions.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_decision(
        self,
        prompt: str,
        route: str,
        latency_ms: float,
        provider_health: Dict[str, Any],
        cached: bool = False,
        error: Optional[str] = None,
        tokens_generated: Optional[int] = None,
        ece_estimate: Optional[float] = None
    ):
        """Log a routing decision with ECE."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
            "route": route,
            "latency_ms": latency_ms,
            "provider_health": provider_health,
            "cached": cached,
            "tokens_generated": tokens_generated,
            "ece_estimate": ece_estimate,
            "error": error
        }
        
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.warning(f"Failed to log decision: {e}")

# ============================================================================
# PROMPT CACHE (Quick win #2)
# ============================================================================

class PromptCache:
    """Simple TTL cache for identical prompts."""
    
    def __init__(self, ttl_seconds: int = 60):
        self.cache: Dict[str, tuple] = {}
        self.ttl_seconds = ttl_seconds
    
    def get(self, prompt: str) -> Optional[str]:
        """Get cached response if still valid."""
        key = hashlib.sha256(prompt.encode()).hexdigest()
        if key in self.cache:
            response, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                router_cache_hits.inc()
                return response
            else:
                del self.cache[key]
        router_cache_misses.inc()
        return None
    
    def put(self, prompt: str, response: str):
        """Cache a response."""
        key = hashlib.sha256(prompt.encode()).hexdigest()
        self.cache[key] = (response, time.time())
    
    def clear_expired(self):
        """Clear expired entries."""
        now = time.time()
        expired = [
            k for k, (_, ts) in self.cache.items()
            if now - ts >= self.ttl_seconds
        ]
        for k in expired:
            del self.cache[k]

# ============================================================================
# ROUTER APPLICATION
# ============================================================================

app = FastAPI(
    title="Athena Router",
    description="Local-first model routing with governance",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
config: RouterConfig
health_monitor: HealthMonitor
decision_logger: DecisionLogger
prompt_cache: PromptCache
providers: Dict[str, Any] = {}

@app.on_event("startup")
async def startup():
    """Initialize router on startup."""
    global config, health_monitor, decision_logger, prompt_cache, providers
    
    logger.info("=" * 60)
    logger.info("🚀 Athena Router Starting")
    logger.info("=" * 60)
    
    # Load configuration
    policy_path = os.getenv(
        "ROUTER_POLICY_PATH",
        "services/router/policies/local_first.yaml"
    )
    config = RouterConfig(policy_path)
    router_allow_cloud_gauge.set(1 if config.allow_cloud else 0)
    
    # Initialize providers
    providers['mlx'] = MLXProvider(
        endpoint=os.getenv("MLX_ENDPOINT", "http://127.0.0.1:8080"),
        model=os.getenv("MLX_MODEL", "qwen2.5-coder-7b"),
        timeout_ms=config.timeouts_ms.get('mlx', 1500)
    )
    
    providers['ollama'] = OllamaProvider(
        endpoint=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
        timeout_ms=config.timeouts_ms.get('ollama', 2000)
    )
    
    providers['mcp_browser'] = MCPBrowserProvider(
        endpoint=os.getenv("MCP_BROWSER_ENDPOINT", "http://127.0.0.1:8095"),
        enabled=os.getenv("MCP_BROWSER_ENABLE", "true").lower() == "true",
        timeout_ms=config.timeouts_ms.get('mcp_browser', 4000)
    )
    
    providers['cloud'] = CloudProvider(
        enabled=config.allow_cloud,
        timeout_ms=config.timeouts_ms.get('cloud', 5000)
    )
    
    # Modal providers
    providers['fastvlm'] = FastVLMProvider(
        endpoint=os.getenv("FASTVLM_ENDPOINT", "http://127.0.0.1:8088"),
        timeout_ms=1500
    )
    
    providers['kokoro'] = KokoroTTSProvider(
        endpoint=os.getenv("KOKORO_ENDPOINT", "http://127.0.0.1:8091"),
        voice=os.getenv("KOKORO_VOICE", "en_US-female"),
        timeout_ms=350
    )
    
    # UAI provider (Universal AI Tools)
    providers['uai'] = UAIProvider(
        endpoint=os.getenv("UAI_ENDPOINT", "http://uai:8080"),
        model=os.getenv("UAI_MODEL", "qwen2.5:7b"),
        timeout_ms=30000
    )
    
    # Initialize health monitor
    health_monitor = HealthMonitor(
        providers=providers,
        backoff_schedule=config.failure_backoff_s
    )
    
    # Initialize decision logger
    decision_logger = DecisionLogger()
    
    # Initialize prompt cache
    prompt_cache = PromptCache(ttl_seconds=60)
    
    # Pre-warm MLX model (Quick win #1)
    logger.info("🔥 Pre-warming MLX model...")
    try:
        await providers['mlx'].generate("test", max_tokens=5)
        logger.info("✅ MLX model pre-warmed")
    except Exception as e:
        logger.warning(f"⚠️  MLX pre-warm failed: {e}")
    
    # Start health monitoring
    await health_monitor.start()
    
    logger.info(f"📊 Policy order: {config.order}")
    logger.info(f"☁️  Cloud allowed: {config.allow_cloud}")
    logger.info("✅ Router ready")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if health_monitor:
        await health_monitor.stop()
    logger.info("👋 Router shutdown complete")

def calculate_ece(route: str, latency_ms: float, tokens: int) -> float:
    """
    Calculate Expected Cost Error (ECE) for route decision.
    
    ECE = (latency_seconds × cost_per_token × tokens)
    
    Higher ECE means more expensive routing decision.
    """
    # Cost per token estimates (USD)
    COST_PER_TOKEN = {
        'mlx': 0.0,        # Free (local)
        'ollama': 0.0,     # Free (local)
        'mcp_browser': 0.0001,  # Minimal (bandwidth)
        'cloud': 0.001     # OpenAI/Anthropic rates
    }
    
    cost = COST_PER_TOKEN.get(route, 0.0)
    latency_s = latency_ms / 1000.0
    
    # ECE = latency × cost × tokens
    ece = latency_s * cost * tokens
    
    return ece

@app.get("/health")
async def health():
    """Health check with provider status."""
    provider_status = health_monitor.get_all_status()
    
    # Check if any provider is healthy
    any_healthy = any(
        status.get('available', False) 
        for status in provider_status.values()
    )
    
    # Check governance policy overrides
    override_path = Path("/tmp/router_policy_overrides.json")
    policy_override = None
    if override_path.exists():
        try:
            with open(override_path, 'r') as f:
                policy_override = json.load(f)
        except:
            pass
    
    return {
        "status": "healthy" if any_healthy else "degraded",
        "providers": provider_status,
        "policy": {
            "order": config.order,
            "allow_cloud": config.allow_cloud,
            "override": policy_override
        },
        "uptime_seconds": health_monitor.uptime_seconds if health_monitor else 0
    }

@app.get("/canary")
async def canary_metrics():
    """
    Canary metrics endpoint for governance controller.
    
    Returns rolling p95 latency and token cost for each provider.
    Used by governance canary controller for breach detection.
    """
    provider_status = health_monitor.get_all_status()
    
    canary_data = {}
    for provider_name, status in provider_status.items():
        canary_data[provider_name] = {
            "available": status.get("available", False),
            "p95_latency_ms": status.get("p95_latency_ms", 0.0),
            "error_rate": status.get("error_rate", 0.0),
            "total_requests": status.get("total_requests", 0),
            "consecutive_failures": status.get("consecutive_failures", 0),
            "in_backoff": status.get("in_backoff", False)
        }
    
    # Check if canary is active (cloud enabled)
    canary_active = config.allow_cloud
    
    # Calculate aggregate metrics
    available_providers = [p for p, s in canary_data.items() if s["available"]]
    avg_p95 = sum(s["p95_latency_ms"] for s in canary_data.values()) / len(canary_data) if canary_data else 0
    
    return {
        "canary_active": canary_active,
        "providers": canary_data,
        "aggregate": {
            "available_count": len(available_providers),
            "avg_p95_latency_ms": avg_p95
        },
        "breach_thresholds": {
            "max_p95_ms": 1200,
            "max_cost_per_request": 0.05
        }
    }

@app.get("/ready")
async def ready():
    """Readiness probe - checks if dependencies are available."""
    provider_status = health_monitor.get_all_status()
    available_providers = [name for name, status in provider_status.items() 
                          if status.get("available", False)]
    
    if not available_providers:
        raise HTTPException(status_code=503, detail="No providers available")
    
    return {
        "ready": True,
        "available_providers": available_providers
    }

@app.get("/version")
async def version():
    """Return build version and timestamp."""
    return {
        "build": BUILD,
        "ts": int(time.time()),
        "features": {
            "mcp": FEATURE_MCP,
            "search": FEATURE_SEARCH
        }
    }

@app.post("/route", response_model=RouteResponse)
async def route_request(request: RouteRequest):
    """
    Route request to best available provider.
    
    Order: MLX → Ollama → MCP-Browser → Cloud (if governed)
    """
    start_time = time.time()
    
    # Check cache first
    cached_response = prompt_cache.get(request.prompt)
    if cached_response:
        latency_ms = (time.time() - start_time) * 1000
        return RouteResponse(
            route="cache",
            text=cached_response,
            latency_ms=latency_ms,
            cached=True,
            provider_health=health_monitor.get_all_status(),
            decision_reasoning="Served from cache"
        )
    
    # Check policy overrides (governance hook)
    _check_policy_overrides()
    
    # Get provider health
    provider_health = health_monitor.get_all_status()
    
    # Try providers in order
    last_error = None
    failover_from = None
    
    for provider_name in config.order:
        provider = providers.get(provider_name)
        if not provider:
            continue
        
        # Skip if not available
        status = provider_health.get(provider_name, {})
        if not status.get('available', False):
            logger.debug(f"Skipping {provider_name}: not available")
            continue
        
        # Skip cloud if not allowed
        if provider_name == 'cloud' and not config.allow_cloud:
            router_cloud_attempts_total.labels(blocked='true').inc()
            logger.info("☁️  Cloud routing blocked by policy")
            continue
        
        try:
            logger.info(f"🎯 Routing to {provider_name}")
            
            # Track cloud attempts
            if provider_name == 'cloud':
                router_cloud_attempts_total.labels(blocked='false').inc()
            
            # Generate response
            response_text = await provider.generate(
                prompt=request.prompt,
                max_tokens=request.max_tokens or config.max_tokens,
                temperature=request.temperature or 0.7
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Cache successful response
            prompt_cache.put(request.prompt, response_text)
            
            # Calculate tokens and ECE
            tokens_generated = len(response_text.split())  # Rough estimate
            ece = calculate_ece(provider_name, latency_ms, tokens_generated)
            
            # Record metrics
            router_requests_total.labels(route=provider_name, status='success').inc()
            router_decisions_count.labels(route=provider_name).inc()
            router_latency_seconds.labels(route=provider_name).observe(latency_ms / 1000)
            router_ece_estimate.labels(route=provider_name).set(ece)
            
            if failover_from:
                router_failovers_count.labels(
                    from_provider=failover_from,
                    to_provider=provider_name,
                    reason='provider_failure'
                ).inc()
            
            # Log decision with ECE
            decision_logger.log_decision(
                prompt=request.prompt,
                route=provider_name,
                latency_ms=latency_ms,
                provider_health=provider_health,
                cached=False,
                tokens_generated=tokens_generated,
                ece_estimate=ece
            )
            
            return RouteResponse(
                route=provider_name,
                text=response_text,
                latency_ms=latency_ms,
                tokens_generated=len(response_text.split()),  # Rough estimate
                cached=False,
                provider_health=provider_health,
                decision_reasoning=f"Routed to {provider_name} (primary available)"
            )
            
        except Exception as e:
            logger.warning(f"❌ {provider_name} failed: {e}")
            last_error = str(e)
            failover_from = provider_name
            
            # Record provider failure
            health_monitor.record_failure(provider_name)
            router_requests_total.labels(route=provider_name, status='error').inc()
            continue
    
    # All providers failed
    latency_ms = (time.time() - start_time) * 1000
    
    decision_logger.log_decision(
        prompt=request.prompt,
        route="none",
        latency_ms=latency_ms,
        provider_health=provider_health,
        error=last_error or "No providers available"
    )
    
    raise HTTPException(
        status_code=503,
        detail=f"No providers available. Last error: {last_error}"
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.post("/reload-policy")
async def reload_policy():
    """Reload routing policy from disk."""
    config.reload()
    router_allow_cloud_gauge.set(1 if config.allow_cloud else 0)
    return {"status": "reloaded", "allow_cloud": config.allow_cloud}

@app.post("/vision/analyze", response_model=VisionAnalyzeResponse)
async def vision_analyze(request: VisionAnalyzeRequest):
    """
    Analyze image using FastVLM (local vision model).
    
    Returns caption, bounding boxes, and routing metadata.
    """
    start_time = time.time()
    
    try:
        # Use FastVLM provider
        fastvlm = providers.get('fastvlm')
        if not fastvlm:
            raise HTTPException(status_code=503, detail="FastVLM provider not available")
        
        # Check health
        if not health_monitor.is_available('fastvlm'):
            raise HTTPException(status_code=503, detail="FastVLM is not healthy")
        
        # Analyze
        result = await fastvlm.analyze(
            image_b64=request.image_b64,
            prompt=request.prompt or "Describe the image in detail"
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        router_vision_latency_seconds.labels(route='fastvlm').observe(latency_ms / 1000)
        router_modality_requests_total.labels(route='fastvlm', modality='vision').inc()
        
        # Calculate modal ECE (vision is more expensive due to tokens)
        tokens_estimate = len(result.get('caption', '').split()) + 100  # Image tokens
        ece = calculate_ece('fastvlm', latency_ms, tokens_estimate)
        router_modality_ece.labels(modality='vision').set(ece)
        
        health_monitor.record_success('fastvlm', latency_ms)
        
        return VisionAnalyzeResponse(
            result=result,
            route='fastvlm',
            latency_ms=latency_ms,
            modality='vision'
        )
    
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        health_monitor.record_failure('fastvlm')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/synthesize", response_model=TTSSynthesizeResponse)
async def tts_synthesize(request: TTSSynthesizeRequest):
    """
    Synthesize speech from text using Kokoro-82M (local TTS model).
    
    Returns base64-encoded WAV audio.
    """
    start_time = time.time()
    
    try:
        # Use Kokoro provider
        kokoro = providers.get('kokoro')
        if not kokoro:
            raise HTTPException(status_code=503, detail="Kokoro TTS provider not available")
        
        # Check health
        if not health_monitor.is_available('kokoro'):
            raise HTTPException(status_code=503, detail="Kokoro TTS is not healthy")
        
        # Synthesize
        result = await kokoro.synthesize(
            text=request.text,
            voice=request.voice
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        router_voice_latency_seconds.labels(route='kokoro-82m').observe(latency_ms / 1000)
        router_modality_requests_total.labels(route='kokoro-82m', modality='voice').inc()
        
        # Calculate modal ECE (TTS is cheaper, mostly latency)
        tokens_estimate = len(request.text.split())
        ece = calculate_ece('kokoro', latency_ms, tokens_estimate)
        router_modality_ece.labels(modality='voice').set(ece)
        
        health_monitor.record_success('kokoro', latency_ms)
        
        return TTSSynthesizeResponse(
            audio_b64=result['audio_b64'],
            duration_ms=result.get('duration_ms', 0),
            sample_rate=result.get('sample_rate', 24000),
            route='kokoro-82m',
            latency_ms=latency_ms,
            modality='voice'
        )
    
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        health_monitor.record_failure('kokoro')
        raise HTTPException(status_code=500, detail=str(e))

def _check_policy_overrides():
    """Check for governance policy overrides."""
    override_path = Path("/tmp/router_policy_overrides.json")
    if not override_path.exists():
        return
    
    try:
        with open(override_path, 'r') as f:
            override = json.load(f)
        
        # Check TTL
        if 'expires_at' in override:
            expires_at = datetime.fromisoformat(override['expires_at'])
            if datetime.utcnow() > expires_at:
                logger.info("🕐 Policy override expired")
                override_path.unlink()
                config.allow_cloud = False
                router_allow_cloud_gauge.set(0)
                return
        
        # Apply override
        if 'allow_cloud' in override:
            old_value = config.allow_cloud
            config.allow_cloud = override['allow_cloud']
            
            if old_value != config.allow_cloud:
                logger.info(f"🔄 Cloud policy override: {config.allow_cloud}")
                router_allow_cloud_gauge.set(1 if config.allow_cloud else 0)
    
    except Exception as e:
        logger.warning(f"Failed to read policy override: {e}")

@app.post("/respond")
async def respond_endpoint(request: dict):
    """Deterministic intent-based responses."""
    message = request.get("message", "")
    if not message:
        return {"error": "Message required"}
    
    response = respond(message)
    return {
        "response": response,
        "intent": "deterministic",
        "latency_ms": 0
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("ROUTER_PORT", "9113"))
    host = os.getenv("ROUTER_HOST", "127.0.0.1")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


