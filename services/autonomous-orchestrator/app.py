"""
Autonomous Orchestrator
Coordinates all self-improvement systems
"""
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import logging
import httpx

from auto_rollback import AutoRollbackEngine
from prompt_evolution import PromptEvolver
from adaptive_trm import AdaptiveTRMDecider
from judicial_client import submit_judicial_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autonomous Orchestrator",
    description="Self-improving AI coordination system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize all autonomous systems
auto_rollback = AutoRollbackEngine()
prompt_evolver = PromptEvolver()
trm_decider = AdaptiveTRMDecider()

# Models
class EvolutionRequest(BaseModel):
    initial_prompt: str
    test_cases: List[Dict[str, Any]]
    generations: int = 5

class FeedbackRequest(BaseModel):
    query_id: str
    query: str
    used_trm: bool
    success: bool
    latency_ms: float
    complexity: float = None

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "autonomous-orchestrator",
        "autonomous_systems": {
            "auto_rollback": auto_rollback.enabled,
            "prompt_evolution": True,
            "adaptive_trm": True,
            "knowledge_sync": "external (file watcher)"
        }
    }

@app.get("/status")
async def autonomous_status():
    """Get status of all autonomous systems"""
    return {
        "auto_rollback": {
            "enabled": auto_rollback.enabled,
            "error_threshold": auto_rollback.error_threshold,
            "latency_threshold_ms": auto_rollback.latency_threshold_ms,
            "sample_size": auto_rollback.sample_size
        },
        "adaptive_trm": trm_decider.get_stats(),
        "prompt_evolution": {
            "population_size": prompt_evolver.population_size,
            "generations": prompt_evolver.generations,
            "mutation_rate": prompt_evolver.mutation_rate
        }
    }

@app.post("/rollback/evaluate")
async def evaluate_canary():
    """Evaluate canary deployment and decide action"""
    # TODO: Fetch real metrics from Prometheus
    canary_metrics = {
        "requests": 100,
        "errors": 2,
        "latency_p95_ms": 150
    }
    prod_metrics = {
        "requests": 1000,
        "errors": 10,
        "latency_p95_ms": 120
    }
    
    decision = await auto_rollback.evaluate_deployment(canary_metrics, prod_metrics)
    
    return {
        "decision": decision,
        "canary_metrics": canary_metrics,
        "production_metrics": prod_metrics
    }

@app.post("/prompt/evolve")
async def evolve_prompt(request: EvolutionRequest):
    """Evolve prompt using genetic algorithm"""
    logger.info(f"🧬 Evolving prompt over {request.generations} generations...")
    
    prompt_evolver.generations = request.generations
    best_prompt, score = await prompt_evolver.evolve(
        request.initial_prompt, 
        request.test_cases
    )
    
    return {
        "original_prompt": request.initial_prompt,
        "evolved_prompt": best_prompt,
        "improvement_score": score,
        "generations": request.generations,
        "population_size": prompt_evolver.population_size
    }

@app.post("/trm/decide")
async def trm_decision(query: str):
    """Decide if query should use TRM reasoning"""
    use_trm, complexity, reasoning = trm_decider.should_use_trm(query)
    
    return {
        "use_trm": use_trm,
        "complexity_score": complexity,
        "reasoning": reasoning,
        "trigger_probability": trm_decider.policy["trigger_probability"]
    }

@app.post("/feedback")
async def record_feedback(request: FeedbackRequest):
    """Record feedback for adaptive learning"""
    # If complexity not provided, calculate it
    if request.complexity is None:
        _, complexity, _ = trm_decider.should_use_trm(request.query)
    else:
        complexity = request.complexity
    
    trm_decider.record_outcome(
        used_trm=request.used_trm,
        success=request.success,
        complexity=complexity,
        latency_ms=request.latency_ms
    )
    
    return {
        "recorded": True,
        "updated_stats": trm_decider.get_stats()
    }

@app.post("/autonomous/enable-all")
async def enable_all_autonomous():
    """Enable all autonomous features"""
    auto_rollback.enabled = True
    
    logger.info("🚀 All autonomous features enabled!")
    
    return {
        "status": "all_autonomous_features_enabled",
        "features": {
            "auto_rollback": auto_rollback.enabled,
            "prompt_evolution": True,
            "adaptive_trm": True,
            "knowledge_sync": "requires external watcher",
            "auto_remediation": "requires AGI remediator integration"
        }
    }

@app.post("/autonomous/disable-all")
async def disable_all_autonomous():
    """Disable all autonomous features (safety)"""
    auto_rollback.enabled = False
    
    logger.warning("⚠️ All autonomous features disabled")
    
    return {
        "status": "autonomous_features_disabled",
        "reason": "manual_control"
    }

# Background task: Continuous improvement
async def continuous_improvement_loop():
    """Run continuous improvement in background"""
    logger.info("🔄 Starting continuous improvement loop...")
    
    while True:
        try:
            await asyncio.sleep(3600)  # 1 hour
            
            logger.info("🔄 Running hourly improvement cycle...")
            
            # Get current stats
            stats = trm_decider.get_stats()
            logger.info(f"   TRM decisions: {stats['total_decisions']}")
            logger.info(f"   TRM trigger prob: {stats['trigger_probability']:.2%}")
            logger.info(f"   TRM success rate: {stats['trm_success_rate']:.2%}")
            
            # TODO: Additional improvement logic
            # - Check if prompts need evolution
            # - Analyze error patterns
            # - Suggest optimizations
            
        except Exception as e:
            logger.error(f"Error in improvement loop: {e}")

@app.on_event("startup")
async def startup():
    """Start background tasks"""
    asyncio.create_task(continuous_improvement_loop())
    logger.info("✅ Autonomous Orchestrator started")

if __name__ == "__main__":
    import uvicorn
    port = 9114
    logger.info(f"🚀 Starting Autonomous Orchestrator on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

