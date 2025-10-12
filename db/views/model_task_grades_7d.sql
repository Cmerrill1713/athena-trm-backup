-- Per-task, per-model grades with Bayesian smoothing
-- Prevents wild swings for new/rare models using Beta(5,5) prior

CREATE OR REPLACE VIEW model_task_grades_7d AS
SELECT
  task_type,
  selected_model,
  COUNT(*)              AS trials,
  SUM(CASE WHEN success THEN 1 ELSE 0 END) AS wins,
  
  -- Raw success rate
  ROUND(
    100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
    1
  ) AS success_rate_raw,
  
  -- Smoothed success rate (Beta prior: 5 successes, 5 failures)
  ROUND(
    100.0 * (SUM(CASE WHEN success THEN 1 ELSE 0 END) + 5.0) / (COUNT(*) + 10.0),
    1
  ) AS success_rate_smoothed,
  
  -- Average latency
  ROUND(AVG(latency_ms)) AS avg_latency_ms,
  
  -- p95 latency
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms,
  
  -- Most recent request
  MAX(created_at) AS last_used,
  
  -- Average user feedback (if any)
  ROUND(AVG(user_feedback), 1) AS avg_user_rating

FROM routing_outcomes
WHERE created_at > NOW() - INTERVAL '7 days'
  AND task_type IS NOT NULL  -- Only graded tasks
GROUP BY task_type, selected_model
ORDER BY task_type, success_rate_smoothed DESC;

COMMENT ON VIEW model_task_grades_7d IS 
  'Per-task model grades with Bayesian smoothing. Use success_rate_smoothed for stable grading.';


-- Quick lookup view: best model per task
CREATE OR REPLACE VIEW best_model_per_task AS
SELECT DISTINCT ON (task_type)
  task_type,
  selected_model AS best_model,
  success_rate_smoothed AS grade,
  trials,
  avg_latency_ms
FROM model_task_grades_7d
WHERE trials >= 10  -- Only models with enough data
ORDER BY task_type, success_rate_smoothed DESC, avg_latency_ms ASC;

COMMENT ON VIEW best_model_per_task IS
  'Best model for each task type (min 10 trials, sorted by smoothed success then latency)';

