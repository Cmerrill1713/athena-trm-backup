"""
NeuroForge Memory Layer
=======================
The "Knowledge Base" - Stores context, patterns, and learnings

Role: Persistent learning and pattern recognition
Input: Plans, executions, reviews
Output: Historical patterns, learnings, recommendations
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class StoredPlan:
    """Plan stored in memory"""
    plan_id: str
    goal: str
    plan_json: str
    created_at: str
    success_rate: Optional[float] = None
    execution_count: int = 0


@dataclass
class Learning:
    """Extracted learning from execution"""
    learning_id: str
    plan_id: str
    lesson: str
    context: Dict[str, Any]
    confidence: float  # 0.0-1.0
    created_at: str


class MemoryLayer:
    """
    Memory Layer - Persistent storage and pattern recognition

    Responsibilities:
    - Store plans, executions, and reviews
    - Retrieve similar historical patterns
    - Extract learnings from feedback
    - Provide recommendations based on history
    - Track success/failure patterns
    """

    def __init__(self, db_path: str = "memory/neuroforge.db"):
        """
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        """Create database schema"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                plan_id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                success_rate REAL,
                execution_count INTEGER DEFAULT 0
            )
        """)

        # Executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                execution_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                execution_json TEXT NOT NULL,
                status TEXT NOT NULL,
                total_time_ms INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
            )
        """)

        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                execution_id TEXT,
                review_json TEXT NOT NULL,
                overall_score REAL NOT NULL,
                overall_quality TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
            )
        """)

        # Learnings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learnings (
                learning_id TEXT PRIMARY KEY,
                plan_id TEXT,
                lesson TEXT NOT NULL,
                context_json TEXT,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Success patterns table (for quick lookups)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.conn.commit()

    def store_plan(self, plan):
        """Store a plan in memory"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO plans (plan_id, goal, plan_json, created_at, execution_count)
            VALUES (?, ?, ?, ?, COALESCE((SELECT execution_count FROM plans WHERE plan_id = ?), 0))
        """, (plan.plan_id, plan.goal, json.dumps(asdict(plan)), plan.created_at, plan.plan_id))
        self.conn.commit()

    def store_execution(self, execution, execution_id: str):
        """Store execution results"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO executions (execution_id, plan_id, execution_json, status, total_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            execution.plan_id,
            json.dumps(asdict(execution), default=str),
            execution.overall_status.value,
            execution.total_time_ms,
            execution.started_at
        ))

        # Update plan execution count
        cursor.execute("""
            UPDATE plans SET execution_count = execution_count + 1
            WHERE plan_id = ?
        """, (execution.plan_id,))

        self.conn.commit()

    def store_review(self, review):
        """Store critic review"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (review_id, plan_id, review_json, overall_score, overall_quality, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            review.review_id,
            review.plan_id,
            json.dumps(asdict(review), default=str),
            review.overall_score,
            review.overall_quality.value,
            review.reviewed_at
        ))

        # Update plan success rate
        cursor.execute("""
            UPDATE plans SET success_rate = (
                SELECT AVG(overall_score) FROM reviews WHERE plan_id = ?
            )
            WHERE plan_id = ?
        """, (review.plan_id, review.plan_id))

        # Store learnings
        for i, learning in enumerate(review.key_learnings):
            learning_id = f"{review.review_id}_learning_{i}"
            self.store_learning(Learning(
                learning_id=learning_id,
                plan_id=review.plan_id,
                lesson=learning,
                context={"review_score": review.overall_score},
                confidence=review.overall_score,
                created_at=review.reviewed_at
            ))

        self.conn.commit()

    def store_learning(self, learning: Learning):
        """Store a learning"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO learnings (learning_id, plan_id, lesson, context_json, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            learning.learning_id,
            learning.plan_id,
            learning.lesson,
            json.dumps(learning.context),
            learning.confidence,
            learning.created_at
        ))
        self.conn.commit()

    def retrieve_similar_plans(self, goal: str, limit: int = 5) -> List[Dict]:
        """Retrieve plans with similar goals"""
        cursor = self.conn.cursor()
        # Simple similarity: keyword overlap (upgrade to embeddings later)
        cursor.execute("""
            SELECT plan_id, goal, success_rate, execution_count
            FROM plans
            WHERE goal LIKE ?
            ORDER BY success_rate DESC, execution_count DESC
            LIMIT ?
        """, (f"%{goal}%", limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                "plan_id": row["plan_id"],
                "goal": row["goal"],
                "success_rate": row["success_rate"] or 0.0,
                "execution_count": row["execution_count"]
            })

        return results

    def retrieve_learnings(self, goal: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant learnings"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.lesson, l.confidence, l.created_at, p.goal
            FROM learnings l
            LEFT JOIN plans p ON l.plan_id = p.plan_id
            WHERE p.goal LIKE ? OR l.lesson LIKE ?
            ORDER BY l.confidence DESC, l.created_at DESC
            LIMIT ?
        """, (f"%{goal}%", f"%{goal}%", limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                "lesson": row["lesson"],
                "confidence": row["confidence"],
                "goal": row["goal"],
                "created_at": row["created_at"]
            })

        return results

    def get_success_patterns(self, goal: str) -> List[str]:
        """Get patterns that led to success"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT l.lesson
            FROM learnings l
            JOIN plans p ON l.plan_id = p.plan_id
            WHERE p.goal LIKE ?
              AND l.confidence > 0.7
            ORDER BY l.confidence DESC
            LIMIT 5
        """, (f"%{goal}%",))

        return [row["lesson"] for row in cursor.fetchall()]

    def get_failure_patterns(self, goal: str) -> List[str]:
        """Get patterns that led to failure"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT l.lesson
            FROM learnings l
            JOIN plans p ON l.plan_id = p.plan_id
            WHERE p.goal LIKE ?
              AND l.confidence < 0.5
            ORDER BY l.confidence ASC
            LIMIT 5
        """, (f"%{goal}%",))

        return [row["lesson"] for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM plans")
        plan_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM executions")
        execution_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM reviews")
        review_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM learnings")
        learning_count = cursor.fetchone()["count"]

        cursor.execute("SELECT AVG(overall_score) as avg FROM reviews")
        avg_score = cursor.fetchone()["avg"] or 0.0

        return {
            "total_plans": plan_count,
            "total_executions": execution_count,
            "total_reviews": review_count,
            "total_learnings": learning_count,
            "average_score": avg_score
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ============================================
# Example Usage
# ============================================
if __name__ == "__main__":
    # Create memory layer
    memory = MemoryLayer("memory/test.db")

    # Store some test data
    from planner_agent import Plan, TaskStep

    test_plan = Plan(
        plan_id="test_001",
        goal="Test memory layer",
        steps=[
            TaskStep(1, "Test storage", {}, [], "Data stored", 0.3)
        ],
        total_complexity=0.3,
        created_at=datetime.now().isoformat(),
        metadata={}
    )

    memory.store_plan(test_plan)

    # Store learning
    learning = Learning(
        learning_id="learn_001",
        plan_id="test_001",
        lesson="Memory layer works correctly",
        context={"test": True},
        confidence=0.95,
        created_at=datetime.now().isoformat()
    )

    memory.store_learning(learning)

    # Get stats
    stats = memory.get_stats()
    print("\n📊 Memory Stats:")
    print(json.dumps(stats, indent=2))

    # Retrieve similar plans
    similar = memory.retrieve_similar_plans("memory")
    print("\n🔍 Similar Plans:")
    print(json.dumps(similar, indent=2))

    memory.close()
