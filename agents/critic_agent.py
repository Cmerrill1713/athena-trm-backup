"""
NeuroForge Critic Agent
=======================
The "Evaluator" - Reviews outputs, flags errors, scores quality

Role: Quality assessment and feedback generation
Input: Plan + Execution results
Output: Scored feedback with improvement suggestions
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class QualityScore(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"      # 90-100%
    GOOD = "good"                # 70-89%
    ACCEPTABLE = "acceptable"    # 50-69%
    POOR = "poor"                # 30-49%
    FAILED = "failed"            # 0-29%


@dataclass
class StepFeedback:
    """Feedback for a single execution step"""
    step_id: int
    score: float  # 0.0-1.0
    quality: QualityScore
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    meets_criteria: bool


@dataclass
class CriticReview:
    """Complete review of plan execution"""
    review_id: str
    plan_id: str
    overall_score: float  # 0.0-1.0
    overall_quality: QualityScore
    step_feedback: List[StepFeedback]
    key_learnings: List[str]
    improvement_suggestions: List[str]
    should_retry: bool
    reviewed_at: str


class CriticAgent:
    """
    Critic Agent - Evaluates output quality and provides feedback

    Responsibilities:
    - Score execution results
    - Identify strengths and weaknesses
    - Generate improvement suggestions
    - Determine if criteria were met
    - Provide structured feedback for learning
    """

    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLM interface for sophisticated analysis
        """
        self.llm = llm_client
        self.review_counter = 0

    def review(self, plan, execution) -> CriticReview:
        """
        Review execution results against plan

        Args:
            plan: Original Plan from Planner
            execution: PlanExecution from Executor

        Returns:
            CriticReview with scores and feedback
        """
        self.review_counter += 1
        review_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.review_counter}"

        print(f"\n🕵️  Critic Review: {review_id}")
        print(f"Plan: {plan.plan_id}")
        print("=" * 50)

        # Review each step
        step_feedback = []
        for step, result in zip(plan.steps, execution.results):
            feedback = self._review_step(step, result)
            step_feedback.append(feedback)

            quality_emoji = self._quality_emoji(feedback.quality)
            print(f"{quality_emoji} Step {step.step_id}: {feedback.score:.2f} ({feedback.quality.value})")

        # Calculate overall score
        if step_feedback:
            overall_score = sum(f.score for f in step_feedback) / len(step_feedback)
        else:
            overall_score = 0.0

        overall_quality = self._score_to_quality(overall_score)

        # Generate learnings and suggestions
        key_learnings = self._extract_learnings(plan, execution, step_feedback)
        suggestions = self._generate_improvements(plan, execution, step_feedback)

        # Determine if retry is needed
        should_retry = overall_score < 0.5 or any(
            not f.meets_criteria for f in step_feedback
        )

        review = CriticReview(
            review_id=review_id,
            plan_id=plan.plan_id,
            overall_score=overall_score,
            overall_quality=overall_quality,
            step_feedback=step_feedback,
            key_learnings=key_learnings,
            improvement_suggestions=suggestions,
            should_retry=should_retry,
            reviewed_at=datetime.now().isoformat()
        )

        print(f"\n📊 Overall: {overall_score:.2f} ({overall_quality.value})")
        print(f"Retry needed: {should_retry}")
        print()

        return review

    def _review_step(self, step, result) -> StepFeedback:
        """Review a single step execution"""
        # Base score on execution status
        if result.status.value == "success":
            base_score = 0.8
        elif result.status.value == "failed":
            base_score = 0.2
        elif result.status.value == "skipped":
            base_score = 0.0
        else:
            base_score = 0.5

        # Adjust for complexity and execution time
        expected_time = step.estimated_complexity * 1000  # ms
        if result.execution_time_ms > 0:
            time_ratio = expected_time / result.execution_time_ms
            time_bonus = min(0.2, time_ratio * 0.1) if time_ratio > 1 else 0
            base_score += time_bonus

        # Cap at 1.0
        score = min(1.0, base_score)

        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        suggestions = []

        if result.status.value == "success":
            strengths.append("Completed successfully")
            if result.execution_time_ms < expected_time:
                strengths.append("Faster than expected")

        if result.error:
            weaknesses.append(f"Error: {result.error}")
            suggestions.append("Add error handling and retry logic")

        if result.execution_time_ms > expected_time * 2:
            weaknesses.append("Slower than expected")
            suggestions.append("Consider optimization or caching")

        # Check if success criteria met (simple check)
        meets_criteria = result.status.value == "success" and not result.error

        if not meets_criteria:
            suggestions.append(f"Ensure: {step.success_criteria}")

        return StepFeedback(
            step_id=step.step_id,
            score=score,
            quality=self._score_to_quality(score),
            strengths=strengths or ["N/A"],
            weaknesses=weaknesses or ["None identified"],
            suggestions=suggestions or ["Continue as planned"],
            meets_criteria=meets_criteria
        )

    def _extract_learnings(self, plan, execution, feedback: List[StepFeedback]) -> List[str]:
        """Extract key learnings from execution"""
        learnings = []

        # High-scoring steps
        excellent_steps = [f for f in feedback if f.score >= 0.9]
        if excellent_steps:
            learnings.append(f"Excellent execution on {len(excellent_steps)} step(s) - pattern to replicate")

        # Failed steps
        failed_steps = [f for f in feedback if not f.meets_criteria]
        if failed_steps:
            learnings.append(f"Failed {len(failed_steps)} step(s) - need alternative approach")

        # Time insights
        avg_time = sum(r.execution_time_ms for r in execution.results) / len(execution.results) if execution.results else 0
        if avg_time < 500:
            learnings.append("Fast execution - good tool selection")
        elif avg_time > 2000:
            learnings.append("Slow execution - consider caching or optimization")

        return learnings or ["No specific patterns identified"]

    def _generate_improvements(self, plan, execution, feedback: List[StepFeedback]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        # Collect all step suggestions
        for fb in feedback:
            suggestions.extend(fb.suggestions)

        # Deduplicate and prioritize
        unique_suggestions = list(dict.fromkeys(suggestions))

        # Add high-level suggestions
        if execution.overall_status.value == "failed":
            unique_suggestions.insert(0, "Revise plan to handle failures more gracefully")

        if plan.total_complexity > 0.8:
            unique_suggestions.append("Consider breaking complex steps into smaller substeps")

        return unique_suggestions[:5]  # Top 5 suggestions

    def _score_to_quality(self, score: float) -> QualityScore:
        """Convert numeric score to quality level"""
        if score >= 0.9:
            return QualityScore.EXCELLENT
        elif score >= 0.7:
            return QualityScore.GOOD
        elif score >= 0.5:
            return QualityScore.ACCEPTABLE
        elif score >= 0.3:
            return QualityScore.POOR
        else:
            return QualityScore.FAILED

    def _quality_emoji(self, quality: QualityScore) -> str:
        """Get emoji for quality level"""
        return {
            QualityScore.EXCELLENT: "🟢",
            QualityScore.GOOD: "🟢",
            QualityScore.ACCEPTABLE: "🟡",
            QualityScore.POOR: "🟠",
            QualityScore.FAILED: "🔴"
        }.get(quality, "⚪")

    def export_review(self, review: CriticReview) -> str:
        """Export review as JSON"""
        data = asdict(review)
        data["overall_quality"] = review.overall_quality.value
        for fb in data["step_feedback"]:
            fb["quality"] = QualityScore(fb["quality"]).value
        return json.dumps(data, indent=2)


# ============================================
# Example Usage
# ============================================
if __name__ == "__main__":
    from planner_agent import PlannerAgent
    from executor_agent import ExecutorAgent

    # Create agents
    planner = PlannerAgent()
    executor = ExecutorAgent()
    critic = CriticAgent()

    # Full loop
    goal = "Test the critic agent"

    print("🧠 PLANNER: Creating plan...")
    plan = planner.create_plan(goal)

    print("\n🚀 EXECUTOR: Executing plan...")
    execution = executor.execute(plan)

    print("\n🕵️  CRITIC: Reviewing execution...")
    review = critic.review(plan, execution)

    print("\n📋 Final Review:")
    print("=" * 50)
    print(f"Score: {review.overall_score:.2f}")
    print(f"Quality: {review.overall_quality.value}")
    print(f"\nKey Learnings:")
    for learning in review.key_learnings:
        print(f"  • {learning}")
    print(f"\nSuggestions:")
    for suggestion in review.improvement_suggestions:
        print(f"  • {suggestion}")
    print(f"\nRetry needed: {review.should_retry}")
