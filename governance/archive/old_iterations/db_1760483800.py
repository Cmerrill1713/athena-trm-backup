import os
import psycopg2
from typing import Dict, Any

def get_db_conn():
    dsn = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/universal_ai_tools")
    return psycopg2.connect(dsn)

def save_eval(interaction_id: str, evaluator: str, metrics: Dict[str, Any]):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO eval_results (interaction_id, evaluator, metric, score, details)
        VALUES (%s, %s, %s, %s, %s)
    """, (interaction_id, evaluator, list(metrics.keys())[0], list(metrics.values())[0], str(metrics)))
    conn.commit()
    cur.close()
    conn.close()
