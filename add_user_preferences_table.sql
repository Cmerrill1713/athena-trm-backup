-- User Preferences Table for Persistent Learning
-- Athena remembers user corrections FOREVER

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(255) NOT NULL,
    preference_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

CREATE INDEX IF NOT EXISTS idx_user_prefs_user ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_prefs_updated ON user_preferences(updated_at DESC);

-- Insert default preferences
INSERT INTO user_preferences (user_id, preference_key, preference_value)
VALUES ('default', 'communication_style', 'default')
ON CONFLICT (user_id, preference_key) DO NOTHING;

COMMENT ON TABLE user_preferences IS 'Stores learned user preferences permanently - Athena never forgets!';
COMMENT ON COLUMN user_preferences.preference_value IS 'Learned correction from user (e.g., "be brief", "be casual")';
