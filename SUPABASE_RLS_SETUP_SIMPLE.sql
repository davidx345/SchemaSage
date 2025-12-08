-- ═══════════════════════════════════════════════════════════════════════════
-- SCHEMASAGE SUPABASE ROW LEVEL SECURITY - SIMPLE VERSION
-- ═══════════════════════════════════════════════════════════════════════════
-- Run this step-by-step in Supabase SQL Editor
-- ═══════════════════════════════════════════════════════════════════════════

-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ STEP 1: CHECK WHAT TABLES EXIST (RUN THIS FIRST!)                      │
-- └─────────────────────────────────────────────────────────────────────────┘

SELECT 
    tablename,
    CASE WHEN rowsecurity THEN '✅ RLS Enabled' ELSE '❌ RLS Disabled' END as status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT IN ('schema_migrations', '_prisma_migrations')
ORDER BY tablename;

-- Copy the table names from the results above, then continue with Step 2


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ STEP 2: ENABLE RLS (Only run for tables that exist!)                   │
-- └─────────────────────────────────────────────────────────────────────────┘

-- IMPORTANT: Only uncomment the lines for tables that appeared in Step 1!

-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE project_activities ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE detected_schemas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE generated_files ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE api_endpoints ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE integration_connections ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ STEP 3: CREATE POLICIES (Copy-paste for each table from Step 1)        │
-- └─────────────────────────────────────────────────────────────────────────┘

-- TEMPLATE: Replace "TABLE_NAME" with actual table name from Step 1
-- Run this block separately for EACH table

/*
DROP POLICY IF EXISTS "Users can view own data" ON TABLE_NAME;
CREATE POLICY "Users can view own data"
ON TABLE_NAME FOR SELECT
USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can insert own data" ON TABLE_NAME;
CREATE POLICY "Users can insert own data"
ON TABLE_NAME FOR INSERT
WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update own data" ON TABLE_NAME;
CREATE POLICY "Users can update own data"
ON TABLE_NAME FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can delete own data" ON TABLE_NAME;
CREATE POLICY "Users can delete own data"
ON TABLE_NAME FOR DELETE
USING (user_id = auth.uid());
*/


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ EXAMPLE: PROJECTS TABLE POLICIES                                        │
-- └─────────────────────────────────────────────────────────────────────────┘

-- Uncomment if 'projects' table exists:
/*
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view own projects"
ON projects FOR SELECT
USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can insert own projects" ON projects;
CREATE POLICY "Users can insert own projects"
ON projects FOR INSERT
WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update own projects" ON projects;
CREATE POLICY "Users can update own projects"
ON projects FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
CREATE POLICY "Users can delete own projects"
ON projects FOR DELETE
USING (user_id = auth.uid());
*/


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ STEP 4: VERIFY SETUP                                                    │
-- └─────────────────────────────────────────────────────────────────────────┘

-- Check RLS is enabled
SELECT 
    tablename,
    CASE WHEN rowsecurity THEN '✅ Enabled' ELSE '❌ Disabled' END as rls_status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT IN ('schema_migrations', '_prisma_migrations')
ORDER BY tablename;

-- Check policies were created
SELECT 
    tablename,
    policyname,
    cmd AS operation
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, operation;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ NOTES                                                                    │
-- └─────────────────────────────────────────────────────────────────────────┘

-- 1. auth.uid() automatically gets the user_id from Supabase Auth JWT
-- 2. If you're using custom JWT (not Supabase Auth), replace auth.uid() with:
--    current_setting('request.jwt.claims')::json->>'user_id'::uuid
-- 3. For tables without user_id column, skip RLS setup
