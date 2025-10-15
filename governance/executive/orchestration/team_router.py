"""
Team Router - Intelligent Task Routing with Thompson Sampling
=============================================================
Uses Thompson Sampling to route tasks to the best specialist agent
"""

from typing import Dict, Any
from ai_team import get_ai_team
from scorer import choose, record_win, record_loss


class TeamRouter:
    """
    Intelligently routes tasks to specialist agents using Thompson Sampling
    Learns which agent/model combination works best for each task type
    """

    def __init__(self):
        self.team = get_ai_team()
        self.task_type_mapping = {
            "design": "architect",
            "implement": "code_gen",
            "test": "tester",
            "review": "reviewer",
            "research": "researcher",
            "optimize": "optimizer",
            "document": "documenter",
            "debug": "debugger"
        }

    async def route_task(self, task: str, task_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route a task to the best agent using Thompson Sampling

        Workflow:
        1. Thompson Sampling selects which specialist to use
        2. Task is sent to that specialist (potentially on CODE machine)
        3. Result is evaluated
        4. Thompson Sampling is updated with success/failure
        5. System learns which agents work best
        """

        capability = self.task_type_mapping.get(task_type, "code_gen")

        # Step 1: Thompson Sampling chooses the provider
        # For task_type="implement", this might choose between:
        # - code-machine-1 (qwen3-coder:30b)
        # - code-machine-2 (qwen3-coder:30b)
        # - local-ollama (qwen3-coder:30b)
        # Based on which has performed best historically

        provider_name = choose(capability)

        print(f"🎯 Thompson Sampling selected: {provider_name} for {capability}")

        # Step 2: Delegate to the chosen specialist
        result = await self.team.delegate_task(task, task_type, context)

        # Step 3: Evaluate result quality
        success = result.get("success", False)

        # Step 4: Update Thompson Sampling
        if success:
            record_win(capability, provider_name)
            print(f"✅ Success! Updated {provider_name} stats (WIN)")
        else:
            record_loss(capability, provider_name)
            print(f"❌ Failed! Updated {provider_name} stats (LOSS)")

        return result

    async def collaborative_build(self, spec: str) -> Dict[str, Any]:
        """
        Full collaborative build using Thompson Sampling for each phase

        This mimics a real software team where:
        - Architect designs (chosen by Thompson Sampling)
        - CODE machine implements (chosen by Thompson Sampling)
        - Another CODE machine tests (chosen by Thompson Sampling)
        - Reviewer checks (chosen by Thompson Sampling)
        - Documenter writes docs (chosen by Thompson Sampling)

        Each choice is independent and learned over time!
        """

        print("=" * 80)
        print("🏢 COLLABORATIVE BUILD WITH THOMPSON SAMPLING")
        print("=" * 80)

        results = {}

        # Phase 1: Architecture (Thompson chooses best architect)
        print("\n📐 Phase 1: Architecture")
        arch_result = await self.route_task(
            task=f"Design architecture for: {spec}",
            task_type="design"
        )
        results["architecture"] = arch_result

        # Phase 2: Implementation (Thompson chooses best CODE machine!)
        print("\n💻 Phase 2: Implementation (CODE MACHINE)")
        code_result = await self.route_task(
            task=f"Implement: {arch_result.get('response', '')[:300]}",
            task_type="implement",
            context={"architecture": arch_result.get("response")}
        )
        results["code"] = code_result

        # Phase 3: Testing (Thompson chooses another CODE machine!)
        print("\n🧪 Phase 3: Testing (CODE MACHINE)")
        test_result = await self.route_task(
            task=f"Generate tests for: {code_result.get('response', '')[:300]}",
            task_type="test",
            context={"code": code_result.get("response")}
        )
        results["tests"] = test_result

        # Phase 4: Review
        print("\n👀 Phase 4: Code Review")
        review_result = await self.route_task(
            task=f"Review: {code_result.get('response', '')[:300]}",
            task_type="review",
            context={
                "code": code_result.get("response"),
                "tests": test_result.get("response")
            }
        )
        results["review"] = review_result

        # Phase 5: Documentation
        print("\n📚 Phase 5: Documentation")
        doc_result = await self.route_task(
            task=f"Document: {code_result.get('response', '')[:300]}",
            task_type="document",
            context={"code": code_result.get("response")}
        )
        results["documentation"] = doc_result

        print("\n" + "=" * 80)
        print("✅ COLLABORATIVE BUILD COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Thompson Sampling learned from {len(results)} phases")
        print("   Next time it will route to better-performing agents!")

        return results


# Global router instance
_router = None

def get_router() -> TeamRouter:
    """Get or create the team router"""
    global _router
    if _router is None:
        _router = TeamRouter()
    return _router
