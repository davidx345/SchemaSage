-- Final database fix for AI Chat service
-- Run this in Supabase SQL editor to completely resolve foreign key and schema issues

-- 1. Drop all existing foreign key constraints
ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_conversation_id_fkey;
ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_session_id_fkey;
ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey;

-- 2. Ensure username column exists in chat_sessions
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'chat_sessions' AND column_name = 'username') THEN
        ALTER TABLE chat_sessions ADD COLUMN username VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_username ON chat_sessions(username);
    END IF;
END $$;

-- 3. Update chat_sessions.user_id to be integer (if it's not already)
DO $$
BEGIN
    -- Check if user_id is already integer type
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'chat_sessions' 
               AND column_name = 'user_id' 
               AND data_type != 'integer') THEN
        -- If it's not integer, convert it
        ALTER TABLE chat_sessions ALTER COLUMN user_id TYPE INTEGER USING user_id::INTEGER;
    END IF;
END $$;

-- 4. Create missing tables if they don't exist (ChatConversation, ChatMessage, etc.)
CREATE TABLE IF NOT EXISTS chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    session_id UUID,
    ai_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    conversation_settings JSONB,
    system_prompt TEXT,
    status VARCHAR(50) DEFAULT 'active',
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_message_at TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd VARCHAR(20) DEFAULT '0.00'
);

-- Indexes for chat_conversations
CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_id ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_session_id ON chat_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_ai_provider ON chat_conversations(ai_provider);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_status ON chat_conversations(status);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_last_message_at ON chat_conversations(last_message_at);

-- Update trigger for chat_conversations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_chat_conversations_updated_at ON chat_conversations;
CREATE TRIGGER update_chat_conversations_updated_at
    BEFORE UPDATE ON chat_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Ensure chat_messages table exists with correct structure (no foreign keys)
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,  -- No FK constraint
    session_id UUID,  -- No FK constraint
    role VARCHAR(20) NOT NULL,
    message_type VARCHAR(50) NOT NULL DEFAULT 'user',
    content TEXT NOT NULL,
    message_order INTEGER NOT NULL,
    parent_message_id UUID,
    ai_provider VARCHAR(50),
    model_name VARCHAR(100),
    finish_reason VARCHAR(50),
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost_usd VARCHAR(20) DEFAULT '0.00',
    response_time_ms INTEGER,
    user_rating INTEGER,
    user_feedback TEXT,
    processing_metadata JSONB,
    error_details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMPTZ
);

-- Indexes for chat_messages
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON chat_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

-- Create user_chat_preferences table
CREATE TABLE IF NOT EXISTS user_chat_preferences (
    user_id VARCHAR(255) PRIMARY KEY,
    preferred_ai_provider VARCHAR(50) DEFAULT 'openai',
    preferred_model VARCHAR(100),
    default_temperature VARCHAR(10) DEFAULT '0.7',
    default_max_tokens INTEGER DEFAULT 1000,
    conversation_style VARCHAR(50) DEFAULT 'helpful',
    enable_message_sounds BOOLEAN DEFAULT TRUE,
    enable_typing_indicator BOOLEAN DEFAULT TRUE,
    theme_preference VARCHAR(50) DEFAULT 'auto',
    save_conversations BOOLEAN DEFAULT TRUE,
    allow_conversation_analysis BOOLEAN DEFAULT TRUE,
    auto_delete_after_days INTEGER,
    daily_message_limit INTEGER DEFAULT 100,
    monthly_token_limit INTEGER DEFAULT 50000,
    custom_settings JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Update trigger for user_chat_preferences
DROP TRIGGER IF EXISTS update_user_chat_preferences_updated_at ON user_chat_preferences;
CREATE TRIGGER update_user_chat_preferences_updated_at
    BEFORE UPDATE ON user_chat_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create chat_usage_statistics table
CREATE TABLE IF NOT EXISTS chat_usage_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    date VARCHAR(10) NOT NULL,  -- YYYY-MM-DD format
    messages_sent INTEGER DEFAULT 0,
    ai_responses_received INTEGER DEFAULT 0,
    total_conversations INTEGER DEFAULT 0,
    openai_tokens_used INTEGER DEFAULT 0,
    gemini_tokens_used INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    openai_cost_usd VARCHAR(20) DEFAULT '0.00',
    gemini_cost_usd VARCHAR(20) DEFAULT '0.00',
    total_cost_usd VARCHAR(20) DEFAULT '0.00',
    average_response_time_ms INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    usage_details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, date)
);

-- Indexes for chat_usage_statistics
CREATE INDEX IF NOT EXISTS idx_chat_usage_statistics_user_id ON chat_usage_statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_usage_statistics_date ON chat_usage_statistics(date);

-- Update trigger for chat_usage_statistics
DROP TRIGGER IF EXISTS update_chat_usage_statistics_updated_at ON chat_usage_statistics;
CREATE TRIGGER update_chat_usage_statistics_updated_at
    BEFORE UPDATE ON chat_usage_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Final verification: Check that no foreign key constraints exist
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE 
    constraint_type = 'FOREIGN KEY' 
    AND tc.table_name IN ('chat_sessions', 'chat_messages', 'chat_conversations', 'user_chat_preferences', 'chat_usage_statistics');

-- Success message
SELECT 'AI Chat database schema fixed successfully! All foreign key constraints removed and tables created.' AS status;