-- Fix connection_audit_logs.connection_id to be nullable
-- This allows logging audit events for failed connection creation attempts
-- Run this on your Supabase database

-- Make connection_id nullable in connection_audit_logs
ALTER TABLE connection_audit_logs 
ALTER COLUMN connection_id DROP NOT NULL;

-- Verify the change
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'connection_audit_logs' 
  AND column_name = 'connection_id';

-- Expected result: is_nullable = 'YES'
