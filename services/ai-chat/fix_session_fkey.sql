-- Fix foreign key constraint issue
-- Remove the foreign key constraint on session_id since we don't use a chat_sessions table

-- Drop the foreign key constraint
ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_session_id_fkey;

-- Verify the constraint is removed
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'chat_messages'::regclass
AND contype = 'f';  -- foreign key constraints only