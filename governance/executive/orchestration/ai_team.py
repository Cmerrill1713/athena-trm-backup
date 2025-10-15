"""
AI Team Orchestration - Multi-Agent Specialist System
=====================================================
Routes work to specialized agents based on task type, with dedicated CODE machines
"""

import asyncio
import httpx
from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass
import json


class AgentRole(Enum):
    """Specialized agent roles"""
    ARCHITECT = "architect"          # System design, planning
    CODE_GEN = "code_gen"           # Code generation (uses CODE machines)
    TESTER = "tester"               # Test generation
    REVIEWER = "reviewer"            # Code review
    RESEARCHER = "researcher"        # Research & analysis
    OPTIMIZER = "optimizer"          # Performance optimization
    DOCUMENTER = "documenter"        # Documentation
    DEBUGGER = "debugger"            # Bug fixing


@dataclass
class Agent:
    """Represents a specialized AI agent"""
    role: AgentRole
    model: str                       # Ollama model or endpoint
    host: str                        # Where this agent runs
    port: int
    capabilities: List[str]
    prompt: str                      # System prompt for this agent

    @property
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"


class AITeam:
    """
    Orchestrates a team of specialized AI agents
    Routes tasks to the right specialist based on task type
    """

    def __init__(self):
        self.agents = self._initialize_team()
        self.task_history = []

    def _initialize_team(self) -> Dict[AgentRole, Agent]:
        """Initialize the AI team with specialized agents"""

        return {
            AgentRole.ARCHITECT: Agent(
                role=AgentRole.ARCHITECT,
                model="qwen2.5:14b",  # Your general reasoning model
                host="localhost",
                port=11434,
                capabilities=["design", "planning", "architecture"],
                prompt="""You are a Senior Software Architect.

Your role:
- Design system architectures
- Create implementation plans
- Define interfaces and contracts
- Plan component interactions
- Make technical decisions

Provide clear, structured designs with:
- Component diagrams
- Data flow diagrams
- API specifications
- Technology choices with rationale
"""
            ),

            AgentRole.CODE_GEN: Agent(
                role=AgentRole.CODE_GEN,
                model="qwen3-coder:30b",  # Your powerful code model
                host="code-machine-1",     # Dedicated CODE machine!
                port=11434,
                capabilities=["code_generation", "implementation"],
                prompt="""You are an Expert Code Generator.

Your role:
- Generate production-ready code
- Implement algorithms and features
- Write clean, typed, documented code
- Follow best practices and patterns

Always include:
- Type hints
- Docstrings
- Error handling
- Modular design
- Clear variable names
"""
            ),

            AgentRole.TESTER: Agent(
                role=AgentRole.TESTER,
                model="qwen3-coder:30b",
                host="code-machine-2",     # Another CODE machine
                port=11434,
                capabilities=["test_generation", "qa"],
                prompt="""You are a Test Engineer.

Your role:
- Generate comprehensive pytest tests
- Create test cases for edge cases
- Write integration tests
- Ensure 90%+ code coverage

Include:
- Unit tests for all functions
- Integration tests
- Fixtures and mocks
- Parameterized tests
"""
            ),

            AgentRole.REVIEWER: Agent(
                role=AgentRole.REVIEWER,
                model="qwen2.5:14b",
                host="localhost",
                port=11434,
                capabilities=["code_review", "quality_assurance"],
                prompt="""You are a Senior Code Reviewer.

Your role:
- Review code for bugs and issues
- Check for security vulnerabilities
- Verify best practices
- Suggest improvements

Focus on:
- Logic errors
- Security issues
- Performance problems
- Maintainability
- Test coverage
"""
            ),

            AgentRole.RESEARCHER: Agent(
                role=AgentRole.RESEARCHER,
                model="qwen2.5:14b",
                host="localhost",
                port=11434,
                capabilities=["research", "analysis", "learning"],
                prompt="""You are a Research Specialist.

Your role:
- Analyze research papers
- Extract key algorithms
- Create implementation plans
- Identify relevant techniques

Provide:
- Algorithm descriptions
- Step-by-step implementation guides
- Complexity analysis
- Integration recommendations
"""
            ),

            AgentRole.OPTIMIZER: Agent(
                role=AgentRole.OPTIMIZER,
                model="qwen3-coder:30b",
                host="code-machine-1",
                port=11434,
                capabilities=["optimization", "performance"],
                prompt="""You are a Performance Optimization Expert.

Your role:
- Optimize code for speed and efficiency
- Reduce memory usage
- Improve algorithms
- Profile and benchmark

Focus on:
- Time complexity
- Space complexity
- Caching strategies
- Parallel processing
"""
            ),

            AgentRole.DOCUMENTER: Agent(
                role=AgentRole.DOCUMENTER,
                model="qwen2.5:14b",
                host="localhost",
                port=11434,
                capabilities=["documentation", "technical_writing"],
                prompt="""You are a Technical Documentation Specialist.

Your role:
- Write clear documentation
- Create usage examples
- Document APIs
- Write architectural guides

Include:
- Getting started guides
- API references
- Architecture diagrams
- Usage examples
"""
            ),

            AgentRole.DEBUGGER: Agent(
                role=AgentRole.DEBUGGER,
                model="qwen3-coder:30b",
                host="code-machine-2",
                port=11434,
                capabilities=["debugging", "troubleshooting"],
                prompt="""You are a Debugging Specialist.

Your role:
- Analyze error traces
- Identify root causes
- Suggest fixes
- Prevent similar bugs

Provide:
- Root cause analysis
- Step-by-step fix
- Prevention strategies
- Test cases to prevent regression
"""
            ),
        }

    async def delegate_task(self, task: str, task_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delegate a task to the appropriate specialist agent

        Args:
            task: The task description
            task_type: Type of task (maps to AgentRole)
            context: Additional context for the task

        Returns:
            Result from the specialist agent
        """

        # Map task type to agent role
        role_mapping = {
            "design": AgentRole.ARCHITECT,
            "implement": AgentRole.CODE_GEN,
            "test": AgentRole.TESTER,
            "review": AgentRole.REVIEWER,
            "research": AgentRole.RESEARCHER,
            "optimize": AgentRole.OPTIMIZER,
            "document": AgentRole.DOCUMENTER,
            "debug": AgentRole.DEBUGGER,
        }

        role = role_mapping.get(task_type, AgentRole.CODE_GEN)
        agent = self.agents[role]

        print(f"🤖 Delegating to {agent.role.value} ({agent.model} on {agent.host})")

        # Prepare prompt with agent's system prompt
        full_prompt = f"{agent.prompt}\n\n---\n\nTask: {task}"

        if context:
            full_prompt += f"\n\nContext: {json.dumps(context, indent=2)}"

        # Call the agent (Ollama API)
        result = await self._call_ollama(
            host=agent.endpoint,
            model=agent.model,
            prompt=full_prompt
        )

        # Record in history
        self.task_history.append({
            "task": task,
            "agent": agent.role.value,
            "model": agent.model,
            "host": agent.host,
            "result_length": len(result.get("response", "")),
            "tokens": result.get("tokens", 0)
        })

        return result

    async def _call_ollama(self, host: str, model: str, prompt: str) -> Dict[str, Any]:
        """Call Ollama API on specified host"""

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data.get("response", ""),
                        "tokens": data.get("eval_count", 0),
                        "model": model,
                        "host": host
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def collaborative_workflow(self, project_spec: str) -> Dict[str, Any]:
        """
        Run a full collaborative workflow:
        Architect → Code Gen → Tester → Reviewer → Documenter

        This mimics a real software team!
        """

        print("=" * 80)
        print("🏢 STARTING COLLABORATIVE AI TEAM WORKFLOW")
        print("=" * 80)

        results = {}

        # Step 1: Architect designs the system
        print("\n📐 Phase 1: Architecture & Design")
        arch_result = await self.delegate_task(
            task=f"Design the architecture for: {project_spec}",
            task_type="design"
        )
        results["architecture"] = arch_result

        if not arch_result.get("success"):
            return {"error": "Architecture phase failed", "results": results}

        # Step 2: Code Generator implements (ON CODE MACHINE!)
        print("\n💻 Phase 2: Code Generation (CODE MACHINE)")
        code_result = await self.delegate_task(
            task=f"Implement this design:\n{arch_result['response'][:500]}...",
            task_type="implement",
            context={"architecture": arch_result["response"]}
        )
        results["implementation"] = code_result

        if not code_result.get("success"):
            return {"error": "Implementation phase failed", "results": results}

        # Step 3: Tester creates tests (ON ANOTHER CODE MACHINE!)
        print("\n🧪 Phase 3: Test Generation (CODE MACHINE)")
        test_result = await self.delegate_task(
            task=f"Generate comprehensive tests for:\n{code_result['response'][:500]}...",
            task_type="test",
            context={"code": code_result["response"]}
        )
        results["tests"] = test_result

        # Step 4: Reviewer checks everything
        print("\n👀 Phase 4: Code Review")
        review_result = await self.delegate_task(
            task=f"Review this implementation:\n{code_result['response'][:500]}...",
            task_type="review",
            context={
                "code": code_result["response"],
                "tests": test_result.get("response", "")
            }
        )
        results["review"] = review_result

        # Step 5: Documenter creates docs
        print("\n📚 Phase 5: Documentation")
        doc_result = await self.delegate_task(
            task=f"Document this implementation:\n{code_result['response'][:500]}...",
            task_type="document",
            context={"code": code_result["response"]}
        )
        results["documentation"] = doc_result

        print("\n" + "=" * 80)
        print("✅ COLLABORATIVE WORKFLOW COMPLETE!")
        print("=" * 80)

        return results


# Global team instance
_team = None

def get_ai_team() -> AITeam:
    """Get or create the AI team"""
    global _team
    if _team is None:
        _team = AITeam()
    return _team


async def route_to_specialist(task: str, task_type: str) -> Dict[str, Any]:
    """
    Route a task to the appropriate specialist
    This is the main entry point for task delegation
    """
    team = get_ai_team()
    return await team.delegate_task(task, task_type)


# Example usage
if __name__ == "__main__":
    async def demo():
        team = AITeam()

        print("=" * 80)
        print("🏢 AI TEAM - SPECIALIZED AGENTS")
        print("=" * 80)
        print("\n👥 Team Members:")
        for role, agent in team.agents.items():
            print(f"  • {role.value:15s} → {agent.model:20s} @ {agent.host}")

        print("\n" + "=" * 80)
        print("💡 Example: Full Project Workflow")
        print("=" * 80)

        project = "Build a rate limiter using token bucket algorithm"

        print(f"\n📋 Project: {project}")
        print("\n🚀 Starting collaborative workflow...")
        print("   (This would orchestrate Architect → Coder → Tester → Reviewer → Documenter)")

        # Note: Actual execution requires code machines to be set up
        print("\n✅ Team ready! To run for real:")
        print("   1. Set up CODE machines with Ollama + qwen3-coder:30b")
        print("   2. Run: python3 orchestrator/ai_team.py")
        print("   3. Watch the team collaborate!")

    asyncio.run(demo())
