#!/usr/bin/env python3
"""
Learning System API - Athena's Design
Expose learning agents via HTTP for external triggers and monitoring
"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import os
import logging
from typing import Dict, Any

from central_learning_coordinator import CentralLearningCoordinator
from feedback_analyzer import FeedbackAnalysisOrchestrator
from router_learning_agent import RouterLearningAgent
from autonomous_improvement import AutonomousImprovementEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Athena Learning System", version="1.0.0")

# CORS for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize coordinator and autonomous engine
coordinator = CentralLearningCoordinator()
autonomous_engine = AutonomousImprovementEngine()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "athena-learning-system"}

@app.post("/v1/learning/trigger")
async def trigger_learning_cycle(background_tasks: BackgroundTasks):
    """Trigger a complete learning cycle"""
    background_tasks.add_task(coordinator.run_learning_cycle)
    return {"status": "triggered", "message": "Learning cycle started in background"}

@app.post("/v1/learning/run")
async def run_learning_cycle():
    """Run learning cycle synchronously (for testing)"""
    result = await coordinator.run_learning_cycle()
    return result

@app.get("/v1/learning/history")
async def get_learning_history():
    """Get learning history"""
    return {
        "cycles": coordinator.learning_history,
        "total_cycles": len(coordinator.learning_history)
    }

@app.post("/v1/feedback/analyze")
async def analyze_feedback(hours: int = 24):
    """Analyze feedback (standalone)"""
    orchestrator = FeedbackAnalysisOrchestrator()
    result = await orchestrator.analyze_recent_feedback(hours)
    return result

@app.post("/v1/router/learn")
async def learn_routing(hours: int = 24):
    """Analyze routing patterns (standalone)"""
    agent = RouterLearningAgent()
    result = await agent.analyze_routing_patterns(hours)
    return result

@app.post("/v1/autonomous/improve")
async def autonomous_improvement():
    """
    Run complete autonomous improvement cycle
    
    This is THE KEY ENDPOINT that Athena uses to modify her own code:
    1. Analyzes feedback/patterns
    2. Generates recommendations
    3. Executes via AGI Core (Scout-Plan-Build)
    4. Modifies files autonomously
    5. Judicial safety review
    6. Reports results
    """
    result = await autonomous_engine.run_improvement_cycle()
    return result

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8098))
    uvicorn.run(app, host="0.0.0.0", port=port)
