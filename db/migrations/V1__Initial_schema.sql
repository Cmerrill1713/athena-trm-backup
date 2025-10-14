-- Initial Database Schema
-- Flyway migration for universal_ai_tools database

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge documents (for RAG)
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    url VARCHAR(1000),
    source VARCHAR(255),
    tags TEXT[],
    embedding_vector VECTOR(768), -- Adjust dimension as needed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- MCP results table
CREATE TABLE IF NOT EXISTS mcp_results (
    id SERIAL PRIMARY KEY,
    agent VARCHAR(255) NOT NULL,
    service VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- PASS, FAIL, WARN
    summary TEXT,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_tags ON knowledge_documents USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_mcp_results_agent ON mcp_results(agent);
CREATE INDEX IF NOT EXISTS idx_mcp_results_timestamp ON mcp_results(timestamp);

-- Feature flags table (for Unleash integration)
CREATE TABLE IF NOT EXISTS feature_flags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bandit Prompt Optimization Schema

-- Prompt variants catalog
CREATE TABLE IF NOT EXISTS prompt_variants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,           -- e.g., 'v1_baseline', 'v2_toolaware'
    template TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bandit stats (aggregated performance)
CREATE TABLE IF NOT EXISTS bandit_stats (
    variant_name VARCHAR(255) PRIMARY KEY REFERENCES prompt_variants(name),
    trials BIGINT NOT NULL DEFAULT 0,
    wins   BIGINT NOT NULL DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User interactions (enhanced with bandit data)
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_text TEXT NOT NULL,
    reply_text TEXT NOT NULL,
    prompt_variant VARCHAR(255) REFERENCES prompt_variants(name),
    model_version VARCHAR(100),
    latency_ms INTEGER,
    reward NUMERIC,                              -- [-1..+1], computed from feedback
    trace_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_interactions_prompt_variant ON interactions(prompt_variant);
CREATE INDEX IF NOT EXISTS idx_interactions_trace_id ON interactions(trace_id);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at);

-- Seed initial prompt variants
INSERT INTO prompt_variants (name, template) VALUES
    ('v1_baseline', 'You are Athena, an advanced AI assistant. Be helpful, truthful, and direct. Context: {{context}} User: {{user}}'),
    ('v2_toolaware', 'You are Athena, an advanced AI assistant. When confidence is low, prefer to use available tools. Be helpful and accurate. Context: {{context}} User: {{user}}')
ON CONFLICT (name) DO NOTHING;

-- Initialize bandit stats
INSERT INTO bandit_stats (variant_name) VALUES ('v1_baseline'), ('v2_toolaware')
ON CONFLICT (variant_name) DO NOTHING;

-- LLM Self-Evaluation Schema

-- Evaluation results table
CREATE TABLE IF NOT EXISTS eval_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts TIMESTAMPTZ DEFAULT now(),
    interaction_id UUID NOT NULL,
    evaluator TEXT NOT NULL,           -- "llm-judge:v1"
    metric TEXT NOT NULL,              -- "helpfulness" | "factuality" | "clarity"
    score DOUBLE PRECISION NOT NULL,   -- 1..10
    details JSONB
);

-- Optional rollup view for quick reads
CREATE MATERIALIZED VIEW IF NOT EXISTS eval_daily AS
SELECT date_trunc('day', ts) AS day,
       evaluator,
       avg(score) FILTER (WHERE metric='helpfulness') AS helpfulness,
       avg(score) FILTER (WHERE metric='factuality')  AS factuality,
       avg(score) FILTER (WHERE metric='clarity')     AS clarity,
       count(*) AS n
FROM eval_results
GROUP BY 1,2;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_eval_results_interaction_id ON eval_results(interaction_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_metric ON eval_results(metric);
CREATE INDEX IF NOT EXISTS idx_eval_results_ts ON eval_results(ts);

-- Auto-Promotion System Schema

-- Promotion actions audit log
CREATE TABLE IF NOT EXISTS promotion_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts TIMESTAMPTZ DEFAULT now(),
    variant_name TEXT NOT NULL,
    action_type TEXT NOT NULL,           -- "promote" | "demote" | "rollback_promote" | "rollback_demote"
    reason TEXT NOT NULL,
    old_traffic_pct DOUBLE PRECISION,
    new_traffic_pct DOUBLE PRECISION,
    judge_score DOUBLE PRECISION,        -- Overall judge score at time of action
    eval_count INTEGER,                  -- Number of evaluations considered
    applied_at TIMESTAMPTZ DEFAULT now(),
    applied_by TEXT DEFAULT 'auto_promotion_system'
);

-- Promotion rules configuration
CREATE TABLE IF NOT EXISTS promotion_rules (
    rule_name TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT true,
    min_samples INTEGER DEFAULT 50,
    promotion_threshold DOUBLE PRECISION DEFAULT 7.5,
    demotion_threshold DOUBLE PRECISION DEFAULT 5.5,
    max_traffic_change_pct DOUBLE PRECISION DEFAULT 25.0,
    min_variant_traffic_pct DOUBLE PRECISION DEFAULT 5.0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Insert default promotion rules
INSERT INTO promotion_rules (
    rule_name, enabled, min_samples, promotion_threshold,
    demotion_threshold, max_traffic_change_pct, min_variant_traffic_pct
) VALUES (
    'default',
    true,
    50,
    7.5,
    5.5,
    25.0,
    5.0
) ON CONFLICT (rule_name) DO NOTHING;

-- Indexes for promotion system
CREATE INDEX IF NOT EXISTS idx_promotion_actions_variant_ts ON promotion_actions(variant_name, ts DESC);
CREATE INDEX IF NOT EXISTS idx_promotion_actions_applied_at ON promotion_actions(applied_at DESC);

-- RAG Reranker Optimization Schema

-- RAG retrieval logging for optimization
CREATE TABLE IF NOT EXISTS rag_retrieval (
    interaction_id UUID PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT now(),
    query TEXT NOT NULL,
    candidates JSONB NOT NULL
);

-- Key-value configuration for dynamic tuning
CREATE TABLE IF NOT EXISTS kv_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    ts TIMESTAMPTZ DEFAULT now()
);

-- Indexes for RAG optimization
CREATE INDEX IF NOT EXISTS idx_rag_retrieval_ts ON rag_retrieval(ts DESC);
CREATE INDEX IF NOT EXISTS idx_rag_retrieval_query ON rag_retrieval USING gin(to_tsvector('english', query));

-- Personalization v1 Schema

-- User preference profiles (lightweight, learned from behavior)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    preferred_length TEXT DEFAULT 'medium',  -- short, medium, long
    preferred_tone TEXT DEFAULT 'balanced',  -- direct, empathetic, formal, casual
    evidence_appetite TEXT DEFAULT 'moderate', -- minimal, moderate, comprehensive
    interaction_count INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Preference learning signals (from user feedback)
CREATE TABLE IF NOT EXISTS preference_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    interaction_id UUID NOT NULL,
    signal_type TEXT NOT NULL,  -- length_feedback, tone_feedback, evidence_feedback
    signal_value TEXT NOT NULL, -- preferred value (short/medium/long, direct/empathetic/formal/casual, etc.)
    confidence DOUBLE PRECISION DEFAULT 1.0,
    ts TIMESTAMPTZ DEFAULT now()
);

-- Indexes for personalization
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_preference_signals_user_id ON preference_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_preference_signals_ts ON preference_signals(ts DESC);
