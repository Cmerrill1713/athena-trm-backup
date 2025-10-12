-- Add task_type and token tracking to routing_outcomes
-- Enables per-task grading and prevents cross-contamination

-- Add columns if missing
ALTER TABLE routing_outcomes
  ADD COLUMN IF NOT EXISTS task_type TEXT,
  ADD COLUMN IF NOT EXISTS tokens_in INT,
  ADD COLUMN IF NOT EXISTS tokens_out INT;

-- Index for fast per-task queries
CREATE INDEX IF NOT EXISTS idx_outcomes_task_time 
  ON routing_outcomes(task_type, created_at DESC);

-- Index for task + model queries
CREATE INDEX IF NOT EXISTS idx_outcomes_task_model 
  ON routing_outcomes(task_type, selected_model, created_at DESC);

COMMENT ON COLUMN routing_outcomes.task_type IS 
  'Task type: vision, ocr, chart, ui, diagram, text, code, etc.';

COMMENT ON COLUMN routing_outcomes.tokens_in IS 
  'Input tokens (prompt length)';

COMMENT ON COLUMN routing_outcomes.tokens_out IS 
  'Output tokens (response length)';

