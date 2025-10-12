#!/usr/bin/env python3
"""
Routing Outcome Logger - Track every decision for TRM training

Logs routing decisions to PostgreSQL for continuous learning.
Powers the self-improvement loop.

Usage:
    from scripts.learn.outcome_logger import log_routing_decision
    
    log_routing_decision(
        prompt="User request...",
        policy={"engine": "fastvlm", "mode": "fast"},
        selected_model="fastvlm-1.5b",
        latency_ms=145.2,
        success=True,
        user_feedback=None,
        meta={"channel": "prod", "task": "vision"}
    )
"""

import os
import sys
import json
import psycopg2
from datetime import datetime
from typing import Optional, Dict, Any

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/athena_db"
)

def log_routing_decision(
    prompt: str,
    policy: Dict[str, Any],
    selected_model: str,
    latency_ms: float,
    success: bool,
    user_feedback: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None
):
    """
    Log a routing decision for TRM training
    
    Args:
        prompt: User request text
        policy: Routing policy dict (engine, mode, etc.)
        selected_model: Model that was selected
        latency_ms: Response latency in milliseconds
        success: Whether the request succeeded
        user_feedback: Optional 1-5 rating
        meta: Additional metadata (channel, task_type, etc.)
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Prepare data
        policy_json = json.dumps(policy)
        meta_json = json.dumps(meta or {})
        
        # Insert outcome
        cur.execute("""
            INSERT INTO routing_outcomes (
                prompt,
                policy,
                selected_model,
                latency_ms,
                success,
                user_feedback,
                meta
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            prompt,
            policy_json,
            selected_model,
            int(latency_ms),
            success,
            user_feedback,
            meta_json
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        # Don't let logging failures break routing
        print(f"⚠️  Outcome logging failed: {e}", file=sys.stderr)

def get_stats(days: int = 30):
    """Get routing stats for the last N days"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_decisions,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                AVG(latency_ms) as avg_latency_ms,
                COUNT(DISTINCT selected_model) as unique_models,
                MIN(created_at) as earliest,
                MAX(created_at) as latest
            FROM routing_outcomes
            WHERE created_at > NOW() - INTERVAL '%s days'
        """, (days,))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            total, successes, avg_lat, models, earliest, latest = row
            success_rate = (successes / total * 100) if total > 0 else 0
            
            print(f"📊 Routing Stats (Last {days} days)")
            print("=" * 50)
            print(f"Total Decisions:  {total or 0}")
            print(f"Success Rate:     {success_rate:.1f}%")
            print(f"Avg Latency:      {avg_lat or 0:.0f}ms")
            print(f"Unique Models:    {models or 0}")
            print(f"Earliest:         {earliest}")
            print(f"Latest:           {latest}")
            
            return {
                "total": total or 0,
                "success_rate": success_rate,
                "avg_latency_ms": avg_lat or 0,
                "unique_models": models or 0
            }
        else:
            print("No data available")
            return None
            
    except Exception as e:
        print(f"❌ Stats query failed: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    # Run stats when called directly
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    get_stats(days)
