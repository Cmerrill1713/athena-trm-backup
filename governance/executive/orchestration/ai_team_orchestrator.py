"""
AI Team Orchestrator - Multi-LLM Specialist Team (UAT Integration)
==================================================================
Extends UAT's existing agent system with specialized LLM team members
Routes CODE tasks to dedicated CODE machines with GPU
"""

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import httpx

# Import UAT's existing Thompson Sampling scorer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "orchestrator"))
try:
    from scorer import choose, record_loss, record_win
    THOMPSON_AVAILABLE = True
except ImportError:
    THOMPSON_AVAILABLE = False
    print("⚠️  Thompson Sampling not available, using round-robin")


class SpecialistRole(Enum):
    """Specialized LLM roles for the AI team"""
    ARCHITECT = "architect"          # qwen2.5:14b - System design
    CODE_GEN = "code_generator"      # qwen3-coder:30b on GPU - Code implementation
    TESTER = "test_engineer"         # qwen3-coder:30b on GPU - Test generation
    REVIEWER = "code_reviewer"       # qwen2.5:14b - Quality assurance
    RESEARCHER = "researcher"        # qwen2.5:14b - Research analysis
    OPTIMIZER = "optimizer"          # qwen3-coder:30b on GPU - Performance tuning
    DOCUMENTER = "documenter"        # qwen2.5:14b - Documentation
    DEBUGGER = "debugger"            # qwen3-coder:30b on GPU - Bug fixing


@dataclass
class SpecialistAgent:
    """Configuration for a specialist LLM"""
    role: SpecialistRole
    model: str
    host: str                        # Hostname (localhost or dedicated machine)
    port: int
    capabilities: List[str]
    system_prompt: str
    gpu_required: bool = False       # True for CODE machines


class AITeamOrchestrator:
    """
    Orchestrates a team of specialized LLMs with intelligent routing
    
    Key Features:
    - Thompson Sampling learns which specialist performs best
    - CODE tasks automatically routed to GPU machines
    - Collaborative workflows (Architect → Coder → Tester → Reviewer)
    - Load balancing across multiple CODE machines
    """

    def __init__(self):
        self.specialists = self._initialize_specialists()
        self.use_thompson = THOMPSON_AVAILABLE

    def _initialize_specialists(self) -> Dict[SpecialistRole, List[SpecialistAgent]]:
        """
        Initialize specialist team
        Note: Multiple agents can have same role (for load balancing)
        """

        specialists = {
            SpecialistRole.ARCHITECT: [
                SpecialistAgent(
                    role=SpecialistRole.ARCHITECT,
                    model="qwen2.5:14b",
                    host="localhost",
                    port=11434,
                    capabilities=["system_design", "planning", "architecture"],
                    gpu_required=False,
                    system_prompt="""You are a Senior Software Architect.
Design clean, scalable systems. Provide component diagrams, API specs, and architectural decisions."""
                )
            ],

            SpecialistRole.CODE_GEN: [
                # CODE MACHINE 1 (primary)
                SpecialistAgent(
                    role=SpecialistRole.CODE_GEN,
                    model="qwen3-coder:30b",
                    host=os.environ.get("CODE_MACHINE_1_HOST", "localhost"),
                    port=int(os.environ.get("CODE_MACHINE_1_PORT", "11434")),
                    capabilities=["code_generation", "implementation"],
                    gpu_required=True,
                    system_prompt="""You are an Expert Code Generator.
Generate production-ready Python code with type hints, docstrings, and error handling."""
                ),
                # CODE MACHINE 2 (backup/load balancing)
                SpecialistAgent(
                    role=SpecialistRole.CODE_GEN,
                    model="qwen3-coder:30b",
                    host=os.environ.get("CODE_MACHINE_2_HOST", "localhost"),
                    port=int(os.environ.get("CODE_MACHINE_2_PORT", "11435")),
                    capabilities=["code_generation", "implementation"],
                    gpu_required=True,
                    system_prompt="""You are an Expert Code Generator.
Generate production-ready Python code with type hints, docstrings, and error handling."""
                ),
            ],

            SpecialistRole.TESTER: [
                SpecialistAgent(
                    role=SpecialistRole.TESTER,
                    model="qwen3-coder:30b",
                    host=os.environ.get("TEST_MACHINE_HOST", "localhost"),
                    port=int(os.environ.get("TEST_MACHINE_PORT", "11436")),
                    capabilities=["test_generation", "qa"],
                    gpu_required=True,
                    system_prompt="""You are a Test Engineer.
Generate comprehensive pytest tests with 90%+ coverage."""
                )
            ],

            SpecialistRole.REVIEWER: [
                SpecialistAgent(
                    role=SpecialistRole.REVIEWER,
                    model="qwen2.5:14b",
                    host="localhost",
                    port=11434,
                    capabilities=["code_review", "quality"],
                    gpu_required=False,
                    system_prompt="""You are a Senior Code Reviewer.
Review for bugs, security issues, and best practices."""
                )
            ],

            SpecialistRole.RESEARCHER: [
                SpecialistAgent(
                    role=SpecialistRole.RESEARCHER,
                    model="qwen2.5:14b",
                    host="localhost",
                    port=11434,
                    capabilities=["research", "analysis"],
                    gpu_required=False,
                    system_prompt="""You are a Research Specialist.
Analyze research papers and extract implementation plans."""
                )
            ],
        }

        return specialists

    async def route_task(self, task: str, role: SpecialistRole, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route task to specialist using Thompson Sampling
        
        For CODE tasks, this automatically routes to GPU machines!
        """

        # Get available specialists for this role
        specialists = self.specialists.get(role, [])

        if not specialists:
            return {"success": False, "error": f"No specialists available for role: {role.value}"}

        # Use Thompson Sampling if available, else round-robin
        if self.use_thompson and len(specialists) > 1:
            # Thompson chooses best performing specialist
            specialist_names = [f"{s.host}:{s.port}" for s in specialists]
            chosen_name = choose(role.value)

            # Find matching specialist
            specialist = next(
                (s for s in specialists if f"{s.host}:{s.port}" == chosen_name),
                specialists[0]  # fallback
            )
        else:
            # Use first available
            specialist = specialists[0]

        # Log routing decision
        machine_type = "🖥️ CODE MACHINE (GPU)" if specialist.gpu_required else "💻 Standard"
        print(f"🎯 Routing {role.value} → {specialist.model} @ {specialist.host}:{specialist.port} {machine_type}")

        # Execute on chosen specialist
        result = await self._call_specialist(specialist, task, context)

        # Update Thompson Sampling
        if self.use_thompson:
            if result.get("success"):
                record_win(role.value, f"{specialist.host}:{specialist.port}")
            else:
                record_loss(role.value, f"{specialist.host}:{specialist.port}")

        return result

    async def _call_specialist(self, specialist: SpecialistAgent, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specialist LLM via Ollama API"""

        # Build prompt
        full_prompt = f"{specialist.system_prompt}\n\n---\n\nTask: {task}"
        if context:
            full_prompt += f"\n\nContext: {context}"

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"http://{specialist.host}:{specialist.port}/api/generate",
                    json={
                        "model": specialist.model,
                        "prompt": full_prompt,
                        "stream": False
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data.get("response", ""),
                        "tokens": data.get("eval_count", 0),
                        "model": specialist.model,
                        "host": f"{specialist.host}:{specialist.port}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def collaborative_build(self, spec: str) -> Dict[str, Any]:
        """
        Full software development workflow with specialist team
        
        Workflow:
        1. ARCHITECT designs (qwen2.5:14b)
        2. CODE GEN implements (qwen3-coder:30b on GPU CODE machine!)
        3. TESTER generates tests (qwen3-coder:30b on GPU CODE machine!)
        4. REVIEWER checks quality (qwen2.5:14b)
        
        Thompson Sampling learns optimal routing for each phase!
        """

        print("=" * 80)
        print("🏢 COLLABORATIVE BUILD - AI TEAM")
        print("=" * 80)

        results = {}

        # Phase 1: Architecture
        print("\n📐 Phase 1: System Design")
        arch = await self.route_task(
            task=f"Design system architecture for: {spec}",
            role=SpecialistRole.ARCHITECT
        )
        results["architecture"] = arch

        if not arch.get("success"):
            return {"error": "Architecture failed", "results": results}

        # Phase 2: Implementation (AUTO-ROUTED TO CODE MACHINE!)
        print("\n💻 Phase 2: Implementation (CODE MACHINE)")
        code = await self.route_task(
            task=f"Implement this design:\n{arch['response'][:500]}...",
            role=SpecialistRole.CODE_GEN,
            context={"architecture": arch["response"]}
        )
        results["code"] = code

        # Phase 3: Testing (AUTO-ROUTED TO CODE MACHINE!)
        print("\n🧪 Phase 3: Test Generation (CODE MACHINE)")
        tests = await self.route_task(
            task=f"Generate comprehensive tests for:\n{code['response'][:500]}...",
            role=SpecialistRole.TESTER,
            context={"code": code["response"]}
        )
        results["tests"] = tests

        # Phase 4: Review
        print("\n👀 Phase 4: Code Review")
        review = await self.route_task(
            task=f"Review implementation:\n{code['response'][:500]}...",
            role=SpecialistRole.REVIEWER,
            context={"code": code["response"], "tests": tests["response"]}
        )
        results["review"] = review

        print("\n" + "=" * 80)
        print("✅ COLLABORATIVE BUILD COMPLETE!")
        print("=" * 80)

        return results


# Global instance
_team_orchestrator = None

def get_team_orchestrator() -> AITeamOrchestrator:
    """Get or create the AI team orchestrator"""
    global _team_orchestrator
    if _team_orchestrator is None:
        _team_orchestrator = AITeamOrchestrator()
    return _team_orchestrator


# Import guard for environment variables
import os

