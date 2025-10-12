"""
NeuroForge Agent System Tests
==============================
Validates the complete agent collaboration loop
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from planner_agent import PlannerAgent
from executor_agent import ExecutorAgent
from critic_agent import CriticAgent
from memory_layer import MemoryLayer
from orchestrator import Orchestrator


def test_planner():
    """Test Planner Agent"""
    print("\n🧪 Testing Planner Agent...")
    print("-" * 50)

    planner = PlannerAgent()
    plan = planner.create_plan("Write a hello world script")

    assert plan is not None, "Plan should be created"
    assert len(plan.steps) > 0, "Plan should have steps"
    assert plan.goal == "Write a hello world script", "Goal should match"

    print(f"✅ Plan created with {len(plan.steps)} steps")
    print(f"   Complexity: {plan.total_complexity:.2f}")
    return True


def test_executor():
    """Test Executor Agent"""
    print("\n🧪 Testing Executor Agent...")
    print("-" * 50)

    planner = PlannerAgent()
    executor = ExecutorAgent()

    plan = planner.create_plan("Test executor")
    execution = executor.execute(plan)

    assert execution is not None, "Execution should complete"
    assert len(execution.results) == len(plan.steps), "Should have result for each step"

    print(f"✅ Executed {len(execution.results)} steps")
    print(f"   Status: {execution.overall_status.value}")
    print(f"   Time: {execution.total_time_ms}ms")
    return True


def test_critic():
    """Test Critic Agent"""
    print("\n🧪 Testing Critic Agent...")
    print("-" * 50)

    planner = PlannerAgent()
    executor = ExecutorAgent()
    critic = CriticAgent()

    plan = planner.create_plan("Test critic")
    execution = executor.execute(plan)
    review = critic.review(plan, execution)

    assert review is not None, "Review should be generated"
    assert 0.0 <= review.overall_score <= 1.0, "Score should be 0-1"
    assert len(review.step_feedback) == len(plan.steps), "Should review each step"

    print(f"✅ Review generated")
    print(f"   Score: {review.overall_score:.2f}")
    print(f"   Quality: {review.overall_quality.value}")
    print(f"   Learnings: {len(review.key_learnings)}")
    return True


def test_memory():
    """Test Memory Layer"""
    print("\n🧪 Testing Memory Layer...")
    print("-" * 50)

    import tempfile
    import os

    # Use temp database
    temp_db = tempfile.mktemp(suffix=".db")

    try:
        memory = MemoryLayer(temp_db)

        # Create and store plan
        planner = PlannerAgent()
        plan = planner.create_plan("Test memory")
        memory.store_plan(plan)

        # Retrieve similar plans
        similar = memory.retrieve_similar_plans("memory")
        assert len(similar) > 0, "Should find stored plan"

        # Get stats
        stats = memory.get_stats()
        assert stats["total_plans"] >= 1, "Should have at least 1 plan"

        print(f"✅ Memory working")
        print(f"   Plans: {stats['total_plans']}")
        print(f"   Learnings: {stats['total_learnings']}")

        memory.close()
        return True

    finally:
        # Cleanup
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_orchestrator():
    """Test complete orchestration loop"""
    print("\n🧪 Testing Orchestrator...")
    print("-" * 50)

    import tempfile
    temp_db = tempfile.mktemp(suffix=".db")

    try:
        orch = Orchestrator(memory_path=temp_db)

        result = orch.execute_goal("Test orchestration loop")

        assert result is not None, "Result should be returned"
        assert result.iterations > 0, "Should have iterations"
        assert result.total_time_ms > 0, "Should take time"

        print(f"✅ Orchestration complete")
        print(f"   Success: {result.success}")
        print(f"   Score: {result.overall_score:.2f}")
        print(f"   Iterations: {result.iterations}")

        orch.close()
        return True

    finally:
        import os
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_learning_loop():
    """Test that system actually learns and improves"""
    print("\n🧪 Testing Learning Loop...")
    print("-" * 50)

    import tempfile
    temp_db = tempfile.mktemp(suffix=".db")

    try:
        orch = Orchestrator(memory_path=temp_db, max_iterations=2)

        goal = "Create a validation script"

        # First attempt
        result1 = orch.execute_goal(goal)
        score1 = result1.overall_score

        # Second attempt (should use learnings)
        result2 = orch.execute_goal(goal)
        score2 = result2.overall_score

        print(f"✅ Learning loop tested")
        print(f"   Attempt 1 score: {score1:.2f}")
        print(f"   Attempt 2 score: {score2:.2f}")
        print(f"   Improvement: {((score2 - score1) / score1 * 100) if score1 > 0 else 0:.1f}%")

        # Check memory has learnings
        stats = orch.get_memory_stats()
        assert stats["total_learnings"] > 0, "Should have learnings"

        print(f"   Learnings stored: {stats['total_learnings']}")

        orch.close()
        return True

    finally:
        import os
        if os.path.exists(temp_db):
            os.remove(temp_db)


# ============================================
# Run All Tests
# ============================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧠 NEUROFORGE AGENT SYSTEM - TEST SUITE")
    print("=" * 60)

    tests = [
        ("Planner", test_planner),
        ("Executor", test_executor),
        ("Critic", test_critic),
        ("Memory", test_memory),
        ("Orchestrator", test_orchestrator),
        ("Learning Loop", test_learning_loop),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} test failed")
        except Exception as e:
            failed += 1
            print(f"❌ {name} test error: {e}")

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print()

    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Agent system is ready to use!")
        print("\nTry:")
        print("  python agents/orchestrator.py")
        print()
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nFix failures before proceeding.")
        print()
        sys.exit(1)
