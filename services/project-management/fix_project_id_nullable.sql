-- Fix project_activities table to allow nullable project_id
-- This allows tracking global activities (schema generation, etc.) without requiring a project

-- Make project_id nullable for global activities
ALTER TABLE project_activities 
ALTER COLUMN project_id DROP NOT NULL;

-- Add index for queries that filter by NULL project_id
CREATE INDEX IF NOT EXISTS idx_project_activities_project_id_null 
ON project_activities(activity_type) 
WHERE project_id IS NULL;

-- Add comment explaining the nullable project_id
COMMENT ON COLUMN project_activities.project_id IS 
'Project ID - can be NULL for global/unassociated activities like schema generation without a project context';

-- Verify the change
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'project_activities' 
        AND column_name = 'project_id' 
        AND is_nullable = 'YES'
    ) THEN
        RAISE NOTICE '✅ project_id is now nullable';
    ELSE
        RAISE EXCEPTION '❌ project_id is still NOT NULL - migration failed';
    END IF;
END $$;
