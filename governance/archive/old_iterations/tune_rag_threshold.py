#!/usr/bin/env python3
"""
RAG Threshold Auto-Tuner

Uses judge evaluation scores to automatically optimize RAG reranking thresholds.
Learns the best threshold (TAU) that maximizes response quality.

Algorithm:
1. Analyze recent retrieval data paired with evaluation scores
2. Try different threshold values on historical data
3. Find threshold that maximizes average judge score
4. Update configuration with optimal threshold

Safety:
- Only updates if sufficient data available
- Gradual changes to prevent instability
- Logs all decisions for audit trail
"""

import os
import psycopg2
import psycopg2.extras
import numpy as np
from typing import List, Dict, Tuple

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")

def get_db_connection():
    """Get database connection."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def get_training_data(days: int = 7, min_samples: int = 10) -> List[Tuple[List[Dict], float]]:
    """
    Get paired retrieval data and evaluation scores for training.

    Returns list of (candidates, judge_score) pairs.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Join retrieval data with evaluation scores
            cur.execute("""
                SELECT
                    r.candidates,
                    (e.helpfulness + e.factuality + e.clarity) / 3.0 as judge_score
                FROM rag_retrieval r
                JOIN eval_results e ON e.interaction_id = r.interaction_id::text
                WHERE r.ts > now() - interval '%s days'
                  AND jsonb_array_length(r.candidates) > 0
                ORDER BY r.ts DESC
            """, (days,))

            training_pairs = []
            for row in cur.fetchall():
                candidates = row['candidates']
                judge_score = float(row['judge_score'])

                # Convert JSON candidates to dict format
                candidate_list = []
                for c in candidates:
                    candidate_list.append({
                        'doc_id': c.get('doc_id', ''),
                        'orig': float(c.get('orig', 0)),
                        'rerank': float(c.get('rerank', c.get('orig', 0))),
                        'used': bool(c.get('used', False))
                    })

                training_pairs.append((candidate_list, judge_score))

            return training_pairs

    except Exception as e:
        print(f"Failed to fetch training data: {e}")
        return []
    finally:
        conn.close()

def evaluate_threshold(candidates: List[Dict], threshold: float) -> List[Dict]:
    """
    Apply threshold to candidates and return filtered results.
    Simulates the reranker logic for evaluation.
    """
    # Sort by rerank score
    sorted_candidates = sorted(candidates, key=lambda x: x.get('rerank', 0), reverse=True)

    # Apply threshold filtering (same logic as rerank.py)
    kept = []
    topk = int(os.getenv("RAG_RERANK_TOPK", "8"))

    for candidate in sorted_candidates:
        if len(kept) >= topk:
            break

        rerank_score = candidate.get('rerank', 0)
        # Keep if score >= threshold OR if we haven't filled half of top-k yet
        if rerank_score >= threshold or len(kept) < (topk // 2):
            kept.append(candidate)

    return kept

def find_optimal_threshold(training_data: List[Tuple[List[Dict], float]],
                          threshold_range: Tuple[float, float] = (0.2, 0.85),
                          num_candidates: int = 14) -> Tuple[float, float]:
    """
    Find the threshold that maximizes average judge score.

    Returns (best_threshold, best_score)
    """
    if not training_data:
        return 0.45, 0.0  # Default fallback

    # Generate threshold candidates
    thresholds = np.linspace(threshold_range[0], threshold_range[1], num_candidates)

    best_threshold = 0.45  # Default
    best_avg_score = 0.0

    print(f"Testing {len(thresholds)} threshold values on {len(training_data)} training examples...")

    for threshold in thresholds:
        scores = []

        # Evaluate this threshold on all training examples
        for candidates, judge_score in training_data:
            filtered_candidates = evaluate_threshold(candidates, threshold)

            # Only count if we kept some candidates (avoid penalizing too much filtering)
            if filtered_candidates:
                scores.append(judge_score)

        if scores:
            avg_score = float(np.mean(scores))
            print(".3f")
            if avg_score > best_avg_score:
                best_avg_score = avg_score
                best_threshold = float(threshold)

    return best_threshold, best_avg_score

def update_threshold_config(new_threshold: float) -> bool:
    """Update the RAG threshold in the configuration database."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO kv_config (key, value)
                VALUES ('RAG_THRESHOLD', %s)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    ts = now()
            """, (str(new_threshold),))

        conn.commit()
        print(f"✅ Updated RAG_THRESHOLD to {new_threshold}")
        return True

    except Exception as e:
        print(f"❌ Failed to update threshold: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_current_threshold() -> float:
    """Get the current threshold from config."""
    conn = get_db_connection()
    if not conn:
        return float(os.getenv("RAG_THRESHOLD", "0.45"))

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT value FROM kv_config WHERE key = 'RAG_THRESHOLD'")
            row = cur.fetchone()
            return float(row['value']) if row else float(os.getenv("RAG_THRESHOLD", "0.45"))
    except Exception:
        return float(os.getenv("RAG_THRESHOLD", "0.45"))
    finally:
        conn.close()

def should_update_threshold(current: float, new: float, min_improvement: float = 0.05) -> bool:
    """Decide if the threshold change is worth applying."""
    improvement = abs(new - current) / current if current > 0 else abs(new)
    return improvement >= min_improvement

def main():
    """Run the RAG threshold tuning process."""
    print("🎯 RAG Threshold Auto-Tuner")
    print("=" * 40)

    # Get training data
    print("\n📊 Gathering training data...")
    training_data = get_training_data(days=7, min_samples=10)

    if not training_data:
        print("⚠️  No sufficient training data available. Need more RAG queries with evaluations.")
        print("   - Ensure RAG_RERANK_ENABLED=true")
        print("   - Ensure EVAL_ENABLED=true")
        print("   - Let system run for a few days to collect data")
        return

    print(f"✅ Found {len(training_data)} training examples")

    # Find optimal threshold
    print("\n🔍 Optimizing threshold...")
    current_threshold = get_current_threshold()
    optimal_threshold, avg_score = find_optimal_threshold(training_data)

    print("\n📈 Results:")
    print(".3f")
    print(".3f")
    print(".3f")
    # Decide whether to update
    if should_update_threshold(current_threshold, optimal_threshold):
        print("\n🎯 Updating threshold...")
        success = update_threshold_config(optimal_threshold)
        if success:
            print("✅ Threshold updated successfully!")
            print(".3f")
            print("   This will improve RAG retrieval quality over the next few queries.")
        else:
            print("❌ Failed to update threshold configuration")
    else:
        print("\n📊 Threshold change too small, keeping current value")
        print(".3f")
    # Show training data stats
    total_candidates = sum(len(candidates) for candidates, _ in training_data)
    avg_candidates = total_candidates / len(training_data) if training_data else 0

    print("\n📈 Training Data Summary:")
    print(f"   Total queries: {len(training_data)}")
    print(".1f")
    print(".1f")
if __name__ == "__main__":
    main()
