#!/usr/bin/env python3
"""
Research Orchestrator - Autonomous Research → Implementation Pipeline
====================================================================
Coordinates the full cycle: Hunt → Analyze → Implement → Test → Deploy
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from research_hunter import ImplementationTask, get_research_hunter
from paper_analyzer import ImplementationPlan, get_paper_analyzer

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrates autonomous research paper implementation"""
    
    def __init__(self):
        self.hunter = get_research_hunter()
        self.analyzer = get_paper_analyzer()
        
        # Service endpoints
        self.athena_base = os.getenv("ATHENA_BASE", "http://127.0.0.1:8090")
        self.bridge_base = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
        self.ath_token = os.getenv("ATH_TOKEN", "supersecret")
        
        # VM Coding Agent (would be integrated)
        self.vm_agent_available = False  # Set to True when VM agent is running
        
        # State tracking
        self.active_implementations: Dict[str, ImplementationTask] = {}
        self.completed_implementations: List[Dict] = []
        self.failed_implementations: List[Dict] = []
    
    async def run_daily_cycle(self) -> Dict[str, Any]:
        """
        Run the complete daily research cycle
        
        Returns:
            Summary of discoveries and implementations
        """
        logger.info("🚀 Starting daily research cycle")
        
        cycle_start = datetime.utcnow()
        
        # 1. Hunt for new papers
        papers = await self.hunter.hunt_daily(lookback_days=1)
        logger.info(f"📚 Discovered {len(papers)} relevant papers")
        
        # 2. Analyze top papers
        top_papers = await self.hunter.get_top_papers(limit=5)
        implementation_plans = []
        
        for paper in top_papers:
            try:
                plan = await self.analyzer.analyze_paper(asdict(paper))
                implementation_plans.append(plan)
            except Exception as e:
                logger.error(f"Failed to analyze paper {paper.paper_id}: {e}")
                continue
        
        logger.info(f"📋 Generated {len(implementation_plans)} implementation plans")
        
        # 3. Queue for implementation
        queued_tasks = []
        for plan in implementation_plans:
            # Find corresponding paper
            paper = next((p for p in top_papers if p.paper_id == plan.paper_id), None)
            if paper:
                task = await self.hunter.queue_for_implementation(paper)
                queued_tasks.append(task)
        
        # 4. Execute implementations (async)
        implementation_results = await self._execute_implementation_queue(queued_tasks[:3])  # Top 3
        
        cycle_end = datetime.utcnow()
        duration = (cycle_end - cycle_start).total_seconds()
        
        return {
            "cycle_start": cycle_start.isoformat(),
            "cycle_end": cycle_end.isoformat(),
            "duration_seconds": duration,
            "papers_discovered": len(papers),
            "papers_analyzed": len(implementation_plans),
            "implementations_queued": len(queued_tasks),
            "implementations_completed": len(implementation_results),
            "hunter_stats": self.hunter.get_stats(),
            "results": implementation_results
        }
    
    async def _execute_implementation_queue(self, tasks: List[ImplementationTask]) -> List[Dict]:
        """Execute implementation tasks"""
        
        results = []
        
        for task in tasks:
            try:
                result = await self._implement_and_test(task)
                results.append(result)
            except Exception as e:
                logger.error(f"Implementation failed for {task.task_id}: {e}")
                results.append({
                    "task_id": task.task_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    async def _implement_and_test(self, task: ImplementationTask) -> Dict[str, Any]:
        """
        Implement a paper and run tests
        
        Returns:
            Implementation result with test outcomes
        """
        logger.info(f"🔨 Implementing: {task.paper.title}")
        
        task.status = "implementing"
        
        # Generate implementation plan
        plan = await self.analyzer.analyze_paper(asdict(task.paper))
        
        # Generate code using Athena + Code Agent
        code_result = await self._generate_code(plan)
        
        if not code_result.get("success"):
            task.status = "failed"
            return {
                "task_id": task.task_id,
                "status": "failed",
                "phase": "code_generation",
                "error": code_result.get("error")
            }
        
        task.status = "testing"
        
        # Run automated tests
        test_result = await self._run_tests(task, code_result)
        
        if test_result.get("success"):
            task.status = "completed"
            task.completed_at = datetime.utcnow().isoformat()
            task.test_results = test_result
            self.completed_implementations.append(asdict(task))
        else:
            task.status = "failed"
            self.failed_implementations.append(asdict(task))
        
        return {
            "task_id": task.task_id,
            "paper_title": task.paper.title,
            "paper_id": task.paper.paper_id,
            "status": task.status,
            "code_generated": code_result.get("success", False),
            "tests_passed": test_result.get("success", False),
            "test_results": test_result,
            "completed_at": task.completed_at
        }
    
    async def _generate_code(self, plan: ImplementationPlan) -> Dict[str, Any]:
        """
        Generate code using Athena Code Agent
        
        Returns:
            Code generation result
        """
        logger.info(f"💻 Generating code for: {plan.paper_title}")
        
        try:
            # Build prompt for code generation
            prompt = self._build_code_generation_prompt(plan)
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.athena_base}/chat",
                    json={
                        "message": prompt,
                        "agent": "code-agent",
                        "context": {
                            "task": "code_generation",
                            "language": plan.programming_language,
                            "plan": asdict(plan)
                        }
                    },
                    headers={"Authorization": f"Bearer {self.ath_token}"}
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Athena returned {response.status_code}"
                    }
                
                data = response.json()
                
                return {
                    "success": True,
                    "code": data.get("response", ""),
                    "agent": data.get("agent"),
                    "route": data.get("route")
                }
                
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_code_generation_prompt(self, plan: ImplementationPlan) -> str:
        """Build prompt for code generation"""
        
        prompt = f"""
Generate a complete {plan.programming_language} implementation for:

**Paper**: {plan.paper_title}

**Algorithms to Implement**:
"""
        
        for i, algo in enumerate(plan.algorithms, 1):
            prompt += f"\n{i}. {algo.name}"
            prompt += f"\n   Description: {algo.description}"
            prompt += f"\n   Key Steps: {', '.join(algo.key_steps[:3])}"
        
        prompt += f"""

**Requirements**:
1. Implement all algorithms with clean, modular code
2. Include type hints and documentation
3. Add error handling and validation
4. Follow best practices for {plan.programming_language}
5. Make code testable and maintainable

**Project Structure**:
{json.dumps(plan.project_structure, indent=2)}

**Dependencies**: {', '.join(plan.dependencies or [])}

Generate the complete implementation with all necessary files.
"""
        
        return prompt
    
    async def _run_tests(self, task: ImplementationTask, code_result: Dict) -> Dict[str, Any]:
        """
        Run automated tests on generated code
        
        Returns:
            Test execution results
        """
        logger.info(f"🧪 Running tests for: {task.paper.title}")
        
        try:
            # Use Athena's /run_tests endpoint
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.athena_base}/run_tests",
                    json={
                        "suite": "integration",
                        "markers": "",
                        "verbose": True,
                        "maxfail": 5
                    },
                    headers={"Authorization": f"Bearer {self.ath_token}"}
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Test execution returned {response.status_code}"
                    }
                
                test_data = response.json()
                
                # Parse pytest results
                passed = test_data.get("passed", 0)
                failed = test_data.get("failed", 0)
                total = passed + failed
                
                return {
                    "success": failed == 0 and passed > 0,
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "duration": test_data.get("duration", 0),
                    "details": test_data.get("output", "")
                }
                
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        
        return {
            "active_implementations": len(self.active_implementations),
            "completed": len(self.completed_implementations),
            "failed": len(self.failed_implementations),
            "queue_size": len(self.hunter.implementation_queue),
            "hunter_stats": self.hunter.get_stats()
        }
    
    async def trigger_manual_implementation(self, paper_id: str) -> Dict[str, Any]:
        """Manually trigger implementation of a specific paper"""
        
        paper = next((p for p in self.hunter.discovered_papers if p.paper_id == paper_id), None)
        
        if not paper:
            return {
                "success": False,
                "error": f"Paper {paper_id} not found in discovered papers"
            }
        
        task = await self.hunter.queue_for_implementation(paper)
        result = await self._implement_and_test(task)
        
        return result


# Global instance
_orchestrator: Optional[ResearchOrchestrator] = None

def get_research_orchestrator() -> ResearchOrchestrator:
    """Get global research orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ResearchOrchestrator()
    return _orchestrator


# Helper to convert dataclass to dict
def asdict(obj):
    """Convert dataclass to dict (simple implementation)"""
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

