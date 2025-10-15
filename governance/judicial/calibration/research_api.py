#!/usr/bin/env python3
"""
Research API - FastAPI endpoints for autonomous research system
==============================================================
Exposes research discovery, analysis, and implementation capabilities
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from research_hunter import get_research_hunter
from paper_analyzer import get_paper_analyzer
from research_orchestrator import get_research_orchestrator

logger = logging.getLogger(__name__)

app = FastAPI(title="Research Automation API", version="1.0.0")


# === Request/Response Models ===

class ResearchHuntRequest(BaseModel):
    """Request to hunt for new papers"""
    lookback_days: int = 1
    categories: Optional[List[str]] = None


class PaperAnalysisRequest(BaseModel):
    """Request to analyze a specific paper"""
    paper_id: str


class ImplementationRequest(BaseModel):
    """Request to implement a paper"""
    paper_id: str
    auto_test: bool = True
    auto_deploy: bool = False


class ResearchCycleRequest(BaseModel):
    """Request to run full research cycle"""
    lookback_days: int = 1
    max_implementations: int = 3
    auto_test: bool = True


# === Endpoints ===

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "research-automation",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/hunt")
async def hunt_papers(request: ResearchHuntRequest):
    """
    Hunt for new research papers

    Returns:
        List of discovered papers with relevance scores
    """
    hunter = get_research_hunter()

    try:
        papers = await hunter.hunt_daily(lookback_days=request.lookback_days)

        return {
            "success": True,
            "papers_discovered": len(papers),
            "papers": [
                {
                    "paper_id": p.paper_id,
                    "title": p.title,
                    "authors": p.authors,
                    "abstract": p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract,
                    "published": p.published,
                    "url": p.url,
                    "relevance_score": p.relevance_score,
                    "has_code": p.has_code,
                    "categories": p.categories
                }
                for p in papers
            ],
            "stats": hunter.get_stats()
        }
    except Exception as e:
        logger.error(f"Hunt failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_paper(request: PaperAnalysisRequest):
    """
    Analyze a specific paper and generate implementation plan

    Returns:
        Implementation plan with algorithms and structure
    """
    hunter = get_research_hunter()
    analyzer = get_paper_analyzer()

    # Find paper
    paper = next((p for p in hunter.discovered_papers if p.paper_id == request.paper_id), None)

    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {request.paper_id} not found")

    try:
        plan = await analyzer.analyze_paper(asdict(paper))

        return {
            "success": True,
            "paper_id": plan.paper_id,
            "paper_title": plan.paper_title,
            "algorithms": [
                {
                    "name": algo.name,
                    "description": algo.description,
                    "complexity": algo.complexity,
                    "dependencies": algo.dependencies,
                    "test_criteria": algo.test_criteria
                }
                for algo in plan.algorithms
            ],
            "programming_language": plan.programming_language,
            "estimated_complexity": plan.estimated_complexity,
            "test_strategy": plan.test_strategy,
            "project_structure": plan.project_structure,
            "dependencies": plan.dependencies
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/implement")
async def implement_paper(request: ImplementationRequest):
    """
    Trigger implementation of a specific paper

    Returns:
        Implementation task status and results
    """
    orchestrator = get_research_orchestrator()

    try:
        result = await orchestrator.trigger_manual_implementation(request.paper_id)

        return {
            "success": result.get("status") == "completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Implementation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cycle")
async def run_research_cycle(request: ResearchCycleRequest):
    """
    Run complete research cycle: Hunt → Analyze → Implement → Test

    Returns:
        Complete cycle results
    """
    orchestrator = get_research_orchestrator()

    try:
        results = await orchestrator.run_daily_cycle()

        return {
            "success": True,
            "cycle_results": results
        }
    except Exception as e:
        logger.error(f"Research cycle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get research orchestrator status"""
    orchestrator = get_research_orchestrator()

    try:
        status = await orchestrator.get_status()
        return status
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue")
async def get_implementation_queue():
    """Get current implementation queue"""
    hunter = get_research_hunter()

    queue = await hunter.get_implementation_queue()

    return {
        "queue_size": len(queue),
        "tasks": [
            {
                "task_id": task.task_id,
                "paper_title": task.paper.title,
                "priority": task.priority,
                "status": task.status,
                "created_at": task.created_at
            }
            for task in queue
        ]
    }


@app.get("/papers/top")
async def get_top_papers(limit: int = 10):
    """Get top papers by relevance score"""
    hunter = get_research_hunter()

    papers = await hunter.get_top_papers(limit=limit)

    return {
        "count": len(papers),
        "papers": [
            {
                "paper_id": p.paper_id,
                "title": p.title,
                "authors": p.authors[:3],  # First 3 authors
                "abstract": p.abstract[:300] + "...",
                "published": p.published,
                "url": p.url,
                "relevance_score": p.relevance_score,
                "algorithms": p.algorithms
            }
            for p in papers
        ]
    }


# Helper to convert dataclass to dict
def asdict(obj):
    """Convert dataclass to dict"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if isinstance(value, list):
                result[key] = [asdict(item) if hasattr(item, '__dict__') else item for item in value]
            elif hasattr(value, '__dict__'):
                result[key] = asdict(value)
            else:
                result[key] = value
        return result
    return obj


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)
