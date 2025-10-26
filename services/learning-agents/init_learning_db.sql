-- Athena Learning System Database Schema

-- User feedback table (already exists from previous implementation)
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) NOT NULL,
    sentiment VARCHAR(10) NOT NULL,
    response_preview TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_feedback_sentiment ON user_feedback(sentiment);
CREATE INDEX IF NOT EXISTS idx_user_feedback_timestamp ON user_feedback(submitted_at);

-- Routing decisions table (for Router Learning Agent)
CREATE TABLE IF NOT EXISTS routing_decisions (
    id SERIAL PRIMARY KEY,
    route VARCHAR(50) NOT NULL,
    latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    tokens_generated INTEGER,
    ece_estimate FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_routing_decisions_route ON routing_decisions(route);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_timestamp ON routing_decisions(timestamp);

-- Learning cycles table (tracks all learning runs)
CREATE TABLE IF NOT EXISTS learning_cycles (
    id SERIAL PRIMARY KEY,
    cycle_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration_seconds FLOAT,
    insights_count INTEGER,
    recommendations_count INTEGER,
    judicial_verdict VARCHAR(50),
    approved BOOLEAN,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learning_cycles_status ON learning_cycles(status);
CREATE INDEX IF NOT EXISTS idx_learning_cycles_started ON learning_cycles(started_at);

-- Agent insights table (stores insights from each agent)
CREATE TABLE IF NOT EXISTS agent_insights (
    id SERIAL PRIMARY KEY,
    cycle_id VARCHAR(255),
    agent_name VARCHAR(100) NOT NULL,
    insight_type VARCHAR(50),
    insight_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_insights_cycle ON agent_insights(cycle_id);
CREATE INDEX IF NOT EXISTS idx_agent_insights_agent ON agent_insights(agent_name);

-- Recommendations table (actionable improvements)
CREATE TABLE IF NOT EXISTS learning_recommendations (
    id SERIAL PRIMARY KEY,
    cycle_id VARCHAR(255),
    priority VARCHAR(20) NOT NULL,
    area VARCHAR(100),
    action TEXT,
    reasoning TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learning_recommendations_cycle ON learning_recommendations(cycle_id);
CREATE INDEX IF NOT EXISTS idx_learning_recommendations_priority ON learning_recommendations(priority);
CREATE INDEX IF NOT EXISTS idx_learning_recommendations_status ON learning_recommendations(status);

-- Model performance tracking (for meta-learning)
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_performance_model ON model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_model_performance_metric ON model_performance(metric_name);
CREATE INDEX IF NOT EXISTS idx_model_performance_timestamp ON model_performance(measured_at);
