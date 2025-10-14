"""
NeuroForge Meta-Agent
=====================
The "Teacher of Teachers" - Adjusts strategies dynamically

Role: Meta-learning and strategy optimization
Input: Historical execution patterns
Output: Strategy adjustments and recommendations
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class StrategyAdjustment:
    """Recommended strategy change"""
    adjustment_id: str
    target_agent: str  # planner, executor, or critic
    adjustment_type: str
    description: str
    expected_improvement: float
    confidence: float
    created_at: str


@dataclass
class MetaAnalysis:
    """Meta-level analysis of system performance"""
    analysis_id: str
    time_period: str
    total_executions: int
    average_score: float
    score_trend: str  # "improving", "declining", "stable"
    bottleneck_agent: Optional[str]
    strategy_adjustments: List[StrategyAdjustment]
    created_at: str


class MetaAgent:
    """
    Meta-Agent - Watches the watchers, teaches the teachers

    Responsibilities:
    - Analyze system-wide patterns
    - Identify bottlenecks
    - Suggest strategy adjustments
    - Optimize agent collaboration
    - Meta-level learning

    This is the highest level of intelligence - it doesn't execute tasks,
    it optimizes how OTHER agents execute tasks.
    """

    def __init__(self, memory: 'MemoryLayer', llm_client=None):
        """
        Args:
            memory: MemoryLayer for accessing historical data
            llm_client: LLM for sophisticated analysis
        """
        self.memory = memory
        self.llm = llm_client
        self.analysis_counter = 0

    def analyze_system_performance(self, lookback_hours: int = 24) -> MetaAnalysis:
        """
        Analyze overall system performance and suggest improvements

        Args:
            lookback_hours: How far back to analyze

        Returns:
            MetaAnalysis with strategy adjustments
        """
        self.analysis_counter += 1
        analysis_id = f"meta_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.analysis_counter}"

        print(f"\n🧠 Meta-Agent Analysis: {analysis_id}")
        print("=" * 60)

        # Get historical data
        stats = self.memory.get_stats()

        # Analyze trends
        score_trend = self._analyze_score_trend()
        bottleneck = self._identify_bottleneck()
        adjustments = self._generate_adjustments(score_trend, bottleneck)

        analysis = MetaAnalysis(
            analysis_id=analysis_id,
            time_period=f"last_{lookback_hours}h",
            total_executions=stats.get("total_executions", 0),
            average_score=stats.get("average_score", 0.0),
            score_trend=score_trend,
            bottleneck_agent=bottleneck,
            strategy_adjustments=adjustments,
            created_at=datetime.now().isoformat()
        )

        print("📊 Analysis Complete:")
        print(f"   Executions: {analysis.total_executions}")
        print(f"   Avg Score: {analysis.average_score:.2f}")
        print(f"   Trend: {analysis.score_trend}")
        if analysis.bottleneck_agent:
            print(f"   Bottleneck: {analysis.bottleneck_agent}")
        print(f"   Adjustments: {len(analysis.strategy_adjustments)}")

        return analysis

    def _analyze_score_trend(self) -> str:
        """Determine if scores are improving, declining, or stable"""
        # Query recent reviews
        cursor = self.memory.conn.cursor()
        cursor.execute("""
            SELECT overall_score, created_at
            FROM reviews
            ORDER BY created_at DESC
            LIMIT 10
        """)

        scores = [row["overall_score"] for row in cursor.fetchall()]

        if len(scores) < 3:
            return "insufficient_data"

        # Simple trend analysis: compare first half to second half
        mid = len(scores) // 2
        recent_avg = sum(scores[:mid]) / mid if mid > 0 else 0
        older_avg = sum(scores[mid:]) / (len(scores) - mid) if (len(scores) - mid) > 0 else 0

        if recent_avg > older_avg * 1.1:
            return "improving"
        elif recent_avg < older_avg * 0.9:
            return "declining"
        else:
            return "stable"

    def _identify_bottleneck(self) -> Optional[str]:
        """Identify which agent is the bottleneck"""
        cursor = self.memory.conn.cursor()

        # Get recent executions
        cursor.execute("""
            SELECT execution_json
            FROM executions
            ORDER BY created_at DESC
            LIMIT 20
        """)

        # Analyze time spent in each phase
        phase_times = defaultdict(list)

        for row in cursor.fetchall():
            try:
                execution_data = json.loads(row["execution_json"])
                for result in execution_data.get("results", []):
                    phase_times["executor"].append(result.get("execution_time_ms", 0))
            except:
                continue

        # Simple heuristic: if executor is consistently slow, it's the bottleneck
        if phase_times["executor"]:
            avg_executor_time = sum(phase_times["executor"]) / len(phase_times["executor"])
            if avg_executor_time > 1000:  # >1s per step
                return "executor"

        # More sophisticated analysis would compare planning, execution, and review times
        return None

    def _generate_adjustments(self, trend: str, bottleneck: Optional[str]) -> List[StrategyAdjustment]:
        """Generate strategy adjustment recommendations"""
        adjustments = []
        now = datetime.now().isoformat()

        # Declining performance adjustments
        if trend == "declining":
            adjustments.append(StrategyAdjustment(
                adjustment_id=f"adj_{datetime.now().strftime('%Y%m%d%H%M%S')}_1",
                target_agent="planner",
                adjustment_type="complexity_reduction",
                description="Reduce plan complexity - recent executions showing declining scores",
                expected_improvement=0.15,
                confidence=0.7,
                created_at=now
            ))

        # Bottleneck adjustments
        if bottleneck == "executor":
            adjustments.append(StrategyAdjustment(
                adjustment_id=f"adj_{datetime.now().strftime('%Y%m%d%H%M%S')}_2",
                target_agent="executor",
                adjustment_type="tool_optimization",
                description="Executor is slow - enable caching or optimize tool selection",
                expected_improvement=0.20,
                confidence=0.8,
                created_at=now
            ))

        # Stable/improving - optimization adjustments
        if trend in ("stable", "improving"):
            adjustments.append(StrategyAdjustment(
                adjustment_id=f"adj_{datetime.now().strftime('%Y%m%d%H%M%S')}_3",
                target_agent="planner",
                adjustment_type="complexity_increase",
                description="System is stable - can handle more complex tasks",
                expected_improvement=0.10,
                confidence=0.6,
                created_at=now
            ))

        return adjustments

    def recommend_next_goal(self, user_context: Dict[str, Any]) -> str:
        """Recommend what goal to tackle next based on system learning"""
        # Analyze what the system is good at
        cursor = self.memory.conn.cursor()
        cursor.execute("""
            SELECT p.goal, r.overall_score
            FROM plans p
            JOIN reviews r ON p.plan_id = r.plan_id
            WHERE r.overall_score > 0.8
            ORDER BY r.created_at DESC
            LIMIT 5
        """)

        successful_goals = [row["goal"] for row in cursor.fetchall()]

        if successful_goals:
            # Pattern recognition: what types of goals succeed?
            if any("script" in g.lower() for g in successful_goals):
                return "Consider script-related tasks - system excels at these"
            elif any("validation" in g.lower() for g in successful_goals):
                return "Consider validation tasks - system has strong patterns here"

        return "Explore new task types to expand system capabilities"

    def export_analysis(self, analysis: MetaAnalysis) -> str:
        """Export analysis as JSON"""
        return json.dumps(asdict(analysis), indent=2, default=str)


# ============================================
# Example Usage
# ============================================
if __name__ == "__main__":
    from memory_layer import MemoryLayer
    import tempfile

    # Create temp memory
    temp_db = tempfile.mktemp(suffix=".db")
    memory = MemoryLayer(temp_db)

    # Create meta-agent
    meta = MetaAgent(memory)

    # Analyze system
    analysis = meta.analyze_system_performance()

    print("\n📊 Meta-Analysis:")
    print("=" * 60)
    print(f"Trend: {analysis.score_trend}")
    print(f"Bottleneck: {analysis.bottleneck_agent or 'None'}")
    print("\n💡 Strategy Adjustments:")
    for adj in analysis.strategy_adjustments:
        print(f"\n  {adj.target_agent.upper()}:")
        print(f"  • {adj.description}")
        print(f"  • Expected improvement: +{adj.expected_improvement:.1%}")
        print(f"  • Confidence: {adj.confidence:.1%}")

    # Get recommendation
    recommendation = meta.recommend_next_goal({})
    print("\n🎯 Recommendation:")
    print(f"  {recommendation}")

    # Cleanup
    memory.close()
    import os
    os.remove(temp_db)
