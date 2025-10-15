# RAG Data Capture for Optimization Learning
# Logs retrieval candidates and outcomes for automated tuning

import json
import os
from typing import Any, Dict, List

import psycopg2
import psycopg2.extras

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")

def get_db_connection():
    """Get database connection with proper error handling."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def log_retrieval(interaction_id: str, query: str, candidates: List[Dict[str, Any]]) -> bool:
    """
    Log retrieval candidates and outcomes for optimization learning.

    Args:
        interaction_id: Unique interaction identifier
        query: Original user query
        candidates: List of candidate documents with scores

    Returns:
        Success status
    """
    if not candidates:
        return True  # Nothing to log

    # Prepare candidate data for JSON storage
    candidate_data = []
    for candidate in candidates:
        candidate_data.append({
            "doc_id": candidate.get("doc_id", ""),
            "orig": float(candidate.get("orig", 0)),
            "rerank": float(candidate.get("rerank", candidate.get("orig", 0))),
            "used": bool(candidate.get("used", False))
        })

    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rag_retrieval (interaction_id, query, candidates)
                VALUES (%s, %s, %s)
                ON CONFLICT (interaction_id) DO UPDATE SET
                    candidates = EXCLUDED.candidates,
                    ts = now()
            """, (interaction_id, query, json.dumps(candidate_data)))

        conn.commit()
        return True

    except Exception as e:
        print(f"Failed to log retrieval data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_recent_retrievals(days: int = 7) -> List[Dict[str, Any]]:
    """Get recent retrieval data for analysis."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM rag_retrieval
                WHERE ts > now() - interval '%s days'
                ORDER BY ts DESC
            """, (days,))

            return [dict(row) for row in cur.fetchall()]

    except Exception as e:
        print(f"Failed to fetch retrieval data: {e}")
        return []
    finally:
        conn.close()

def get_retrieval_stats(days: int = 7) -> Dict[str, Any]:
    """Get statistics about retrieval performance."""
    retrievals = get_recent_retrievals(days)

    if not retrievals:
        return {}

    total_queries = len(retrievals)
    total_candidates = sum(len(r.get('candidates', [])) for r in retrievals)
    total_used = sum(
        sum(1 for c in r.get('candidates', []) if c.get('used', False))
        for r in retrievals
    )

    rerank_scores = []
    for r in retrievals:
        for c in r.get('candidates', []):
            if 'rerank' in c:
                rerank_scores.append(c['rerank'])

    return {
        "total_queries": total_queries,
        "total_candidates": total_candidates,
        "avg_candidates_per_query": total_candidates / total_queries if total_queries > 0 else 0,
        "total_used_candidates": total_used,
        "avg_used_per_query": total_used / total_queries if total_queries > 0 else 0,
        "rerank_scores": {
            "count": len(rerank_scores),
            "mean": sum(rerank_scores) / len(rerank_scores) if rerank_scores else 0,
            "min": min(rerank_scores) if rerank_scores else 0,
            "max": max(rerank_scores) if rerank_scores else 0
        },
        "analysis_period_days": days
    }
