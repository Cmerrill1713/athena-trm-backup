-- Fast time-window & model pivots
CREATE INDEX IF NOT EXISTS idx_routing_outcomes_created_model
ON routing_outcomes (created_at DESC, selected_model);

-- Speed up recent success scans
CREATE INDEX IF NOT EXISTS idx_routing_outcomes_success_time
ON routing_outcomes (success, created_at DESC);

-- Optional: archive policy marker table
CREATE TABLE IF NOT EXISTS routing_outcomes_archive LIKE routing_outcomes;

-- Example archival (run nightly if desired)
-- INSERT INTO routing_outcomes_archive SELECT * FROM routing_outcomes WHERE created_at < NOW() - INTERVAL '90 days';
-- DELETE FROM routing_outcomes WHERE created_at < NOW() - INTERVAL '90 days';

