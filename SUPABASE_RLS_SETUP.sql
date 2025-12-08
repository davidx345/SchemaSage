-- ═══════════════════════════════════════════════════════════════════════════
-- SCHEMASAGE SUPABASE ROW LEVEL SECURITY (RLS) SETUP
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Enable user-level data isolation across all tables
-- Security Model: Each user_id acts as a tenant boundary
-- Run this in your Supabase SQL Editor to enforce data isolation
-- ═══════════════════════════════════════════════════════════════════════════

-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ STEP 1: ENABLE ROW LEVEL SECURITY ON ALL USER TABLES                   │
-- └─────────────────────────────────────────────────────────────────────────┘
-- NOTE: Skip tables that don't exist in your database (you'll see errors for those)

-- Projects table (core data isolation)
ALTER TABLE IF EXISTS projects ENABLE ROW LEVEL SECURITY;

-- Activity tracking
ALTER TABLE IF EXISTS project_activities ENABLE ROW LEVEL SECURITY;

-- Chat system
ALTER TABLE IF EXISTS chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chat_messages ENABLE ROW LEVEL SECURITY;

-- Schema detection
ALTER TABLE IF EXISTS detected_schemas ENABLE ROW LEVEL SECURITY;

-- Database migrations
ALTER TABLE IF EXISTS migration_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS migration_history ENABLE ROW LEVEL SECURITY;

-- Code generation
ALTER TABLE IF EXISTS generated_files ENABLE ROW LEVEL SECURITY;

-- API documentation
ALTER TABLE IF EXISTS api_endpoints ENABLE ROW LEVEL SECURITY;

-- Integration connections
ALTER TABLE IF EXISTS integration_connections ENABLE ROW LEVEL SECURITY;

-- Audit logs (if exists)
ALTER TABLE IF EXISTS audit_logs ENABLE ROW LEVEL SECURITY;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ STEP 2: CREATE USER-LEVEL ISOLATION POLICIES                           │
-- └─────────────────────────────────────────────────────────────────────────┘

-- ═══════════════════════════════════════════════════════════════════════════
-- PROJECTS TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════
-- NOTE: These will fail silently if the table doesn't exist

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'projects') THEN
        DROP POLICY IF EXISTS "Users can view own projects" ON projects;
        CREATE POLICY "Users can view own projects"
        ON projects FOR SELECT
        USING (user_id = current_setting('app.current_user_id'));

        DROP POLICY IF EXISTS "Users can insert own projects" ON projects;
        CREATE POLICY "Users can insert own projects"
        ON projects FOR INSERT
        WITH CHECK (user_id = current_setting('app.current_user_id'));

        DROP POLICY IF EXISTS "Users can update own projects" ON projects;
        CREATE POLICY "Users can update own projects"
        ON projects FOR UPDATE
        USING (user_id = current_setting('app.current_user_id'))
        WITH CHECK (user_id = current_setting('app.current_user_id'));

        DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
        CREATE POLICY "Users can delete own projects"
        ON projects FOR DELETE
        USING (user_id = current_setting('app.current_user_id'));
    END IF;
END $$;


-- ═══════════════════════════════════════════════════════════════════════════
-- PROJECT ACTIVITIES TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own activities"
ON project_activities FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own activities"
ON project_activities FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own activities"
ON project_activities FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own activities"
ON project_activities FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- CHAT SESSIONS TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own chat sessions"
ON chat_sessions FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own chat sessions"
ON chat_sessions FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own chat sessions"
ON chat_sessions FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own chat sessions"
ON chat_sessions FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- CHAT MESSAGES TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own chat messages"
ON chat_messages FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own chat messages"
ON chat_messages FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own chat messages"
ON chat_messages FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own chat messages"
ON chat_messages FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- DETECTED SCHEMAS TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own detected schemas"
ON detected_schemas FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own detected schemas"
ON detected_schemas FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own detected schemas"
ON detected_schemas FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own detected schemas"
ON detected_schemas FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- MIGRATION JOBS TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own migration jobs"
ON migration_jobs FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own migration jobs"
ON migration_jobs FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own migration jobs"
ON migration_jobs FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own migration jobs"
ON migration_jobs FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- GENERATED FILES TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own generated files"
ON generated_files FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own generated files"
ON generated_files FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own generated files"
ON generated_files FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own generated files"
ON generated_files FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- API ENDPOINTS TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own API endpoints"
ON api_endpoints FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own API endpoints"
ON api_endpoints FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own API endpoints"
ON api_endpoints FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own API endpoints"
ON api_endpoints FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- INTEGRATION CONNECTIONS TABLE POLICIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own integration connections"
ON integration_connections FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own integration connections"
ON integration_connections FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can update own integration connections"
ON integration_connections FOR UPDATE
USING (user_id = current_setting('app.current_user_id'))
WITH CHECK (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can delete own integration connections"
ON integration_connections FOR DELETE
USING (user_id = current_setting('app.current_user_id'));


-- ═══════════════════════════════════════════════════════════════════════════
-- AUDIT LOGS TABLE POLICIES (if exists)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE POLICY "Users can view own audit logs"
ON audit_logs FOR SELECT
USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can insert own audit logs"
ON audit_logs FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id'));


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ STEP 3: VERIFICATION QUERIES                                            │
-- └─────────────────────────────────────────────────────────────────────────┘

-- ═══════════════════════════════════════════════════════════════════════════
-- CHECK 1: Verify RLS is enabled on all tables
-- ═══════════════════════════════════════════════════════════════════════════
SELECT 
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'projects', 'project_activities', 'chat_sessions', 'chat_messages',
    'detected_schemas', 'migration_jobs', 'migration_history',
    'generated_files', 'api_endpoints', 'integration_connections', 'audit_logs'
)
ORDER BY tablename;


-- ═══════════════════════════════════════════════════════════════════════════
-- CHECK 2: List all RLS policies
-- ═══════════════════════════════════════════════════════════════════════════
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    cmd AS command_type
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;


-- ═══════════════════════════════════════════════════════════════════════════
-- CHECK 3: Verify no orphaned data (NULL user_ids)
-- ═══════════════════════════════════════════════════════════════════════════
SELECT 'projects' AS table_name, COUNT(*) AS orphaned_rows
FROM projects WHERE user_id IS NULL
UNION ALL
SELECT 'project_activities', COUNT(*)
FROM project_activities WHERE user_id IS NULL
UNION ALL
SELECT 'chat_sessions', COUNT(*)
FROM chat_sessions WHERE user_id IS NULL
UNION ALL
SELECT 'chat_messages', COUNT(*)
FROM chat_messages WHERE user_id IS NULL
UNION ALL
SELECT 'detected_schemas', COUNT(*)
FROM detected_schemas WHERE user_id IS NULL
UNION ALL
SELECT 'migration_jobs', COUNT(*)
FROM migration_jobs WHERE user_id IS NULL
UNION ALL
SELECT 'generated_files', COUNT(*)
FROM generated_files WHERE user_id IS NULL
UNION ALL
SELECT 'api_endpoints', COUNT(*)
FROM api_endpoints WHERE user_id IS NULL
UNION ALL
SELECT 'integration_connections', COUNT(*)
FROM integration_connections WHERE user_id IS NULL
UNION ALL
SELECT 'audit_logs', COUNT(*)
FROM audit_logs WHERE user_id IS NULL;


-- ═══════════════════════════════════════════════════════════════════════════
-- CHECK 4: User data distribution (sanity check)
-- ═══════════════════════════════════════════════════════════════════════════
SELECT 
    user_id,
    COUNT(*) AS total_projects
FROM projects
GROUP BY user_id
ORDER BY total_projects DESC;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ NOTES FOR DEVELOPERS                                                    │
-- └─────────────────────────────────────────────────────────────────────────┘

-- 1. APPLICATION MUST SET USER CONTEXT:
--    Before querying, your application MUST execute:
--    SET app.current_user_id = '<user_uuid_from_jwt>';
--
-- 2. SERVICE ACCOUNT BYPASS:
--    For internal service-to-service calls that need full access:
--    - Use a dedicated service role with BYPASSRLS permission
--    - Never expose this role's credentials to frontend
--
-- 3. ADMIN ACCESS:
--    If you need admin users to see all data:
--    CREATE POLICY "Admins can view all data"
--    ON <table> FOR SELECT
--    USING (
--        user_id = current_setting('app.current_user_id')::uuid
--        OR current_setting('app.user_is_admin')::boolean = true
--    );
--
-- 4. PERFORMANCE:
--    Ensure user_id columns have indexes:
--    CREATE INDEX IF NOT EXISTS idx_<table>_user_id ON <table>(user_id);
--
-- 5. TESTING RLS:
--    SET app.current_user_id = '<test_user_uuid>';
--    SELECT * FROM projects;  -- Should only show test user's data
