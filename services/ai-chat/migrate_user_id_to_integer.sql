-- Migration: Change chat_sessions.user_id from UUID to INTEGER
-- This aligns with the users.id column which is INTEGER

-- Step 1: Drop RLS policies that depend on user_id
DROP POLICY IF EXISTS "Users can manage their own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can manage messages in their chat sessions" ON chat_messages;

-- Step 2: Drop the foreign key constraint if it exists
ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey;

-- Step 3: Drop the old user_id column (CASCADE to drop dependencies)
ALTER TABLE chat_sessions DROP COLUMN IF EXISTS user_id CASCADE;

-- Step 4: Add new user_id column as INTEGER
ALTER TABLE chat_sessions ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1;

-- Step 5: Add foreign key constraint to reference users.id
ALTER TABLE chat_sessions 
ADD CONSTRAINT chat_sessions_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Step 6: Create index on user_id for performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);

-- Step 7: Recreate RLS policies with INTEGER user_id
CREATE POLICY "Users can manage their own chat sessions" ON chat_sessions
    FOR ALL
    USING (user_id = (current_setting('request.jwt.claims'::text, true)::json->>'user_id')::integer);

CREATE POLICY "Users can manage messages in their chat sessions" ON chat_messages
    FOR ALL
    USING (
        session_id IN (
            SELECT id FROM chat_sessions 
            WHERE user_id = (current_setting('request.jwt.claims'::text, true)::json->>'user_id')::integer
        )
    );

-- Step 8: Verify the change
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'chat_sessions' 
AND column_name = 'user_id';
