from athena.db import get_db_conn

def blend_judge_into_reward(interaction_id: str, reward: float) -> float:
    judge_scores = fetch_latest_eval(interaction_id)
    if judge_scores:
        j = (judge_scores["helpfulness"] + judge_scores["factuality"] + judge_scores["clarity"]) / 3.0
        reward += 0.25 * ((j - 5.5) / 9.0)  # Blend small weight
    return reward

def fetch_latest_eval(interaction_id: str) -> Dict[str, float]:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT metrics FROM eval_results WHERE interaction_id = %s ORDER BY created_at DESC LIMIT 1", (interaction_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else {}
