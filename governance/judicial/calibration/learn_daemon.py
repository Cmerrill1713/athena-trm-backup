#!/usr/bin/env python3
"""
Learn Daemon - Continuous data preparation for TRM

Maintains a rolling window of recent routing outcomes.
Prepares training data in the background.

Usage:
    python3 scripts/learn/learn_daemon.py [window_size]
"""

import os
import sys
import time
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/athena_db"
)

WINDOW_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

def fetch_recent_outcomes(limit=1000):
    """Fetch recent routing outcomes"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, prompt, policy, selected_model, latency_ms, success, created_at
            FROM routing_outcomes
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return rows
    except Exception as e:
        print(f"❌ Fetch failed: {e}", file=sys.stderr)
        return []

def prepare_training_batch():
    """Prepare data for next training run"""
    outcomes = fetch_recent_outcomes(WINDOW_SIZE)
    
    if not outcomes:
        return 0
    
    # Basic stats
    total = len(outcomes)
    successes = sum(1 for row in outcomes if row[5])  # success column
    avg_latency = sum(row[4] for row in outcomes) / total if total > 0 else 0
    
    print(f"📊 Rolling window: {total} outcomes")
    print(f"   Success rate: {successes/total*100:.1f}%")
    print(f"   Avg latency: {avg_latency:.0f}ms")
    
    return total

def run_daemon():
    """Run continuous data preparation"""
    print("🧠 Learn Daemon Started")
    print("=" * 60)
    print(f"📊 Window size: {WINDOW_SIZE}")
    print(f"🗄️  Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    print("=" * 60)
    print("")
    
    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iteration {iteration}")
            
            count = prepare_training_batch()
            
            if count > 0:
                print(f"✅ Ingesting outcomes... rolling_window={count}")
            else:
                print("⏳ Waiting for data...")
            
            # Sleep for 60 seconds between checks
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n🛑 Daemon stopped")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}", file=sys.stderr)
            time.sleep(10)

if __name__ == "__main__":
    run_daemon()

