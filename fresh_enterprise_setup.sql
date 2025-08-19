-- SchemaSage Fresh Enterprise Database Setup
-- Use this script for a CLEAN/EMPTY database setup
-- This creates the full enterprise schema without migration complexity
-- 
-- Execute this SQL in your Supabase SQL Editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Drop any existing tables if they exist (since database is empty anyway)
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS integrations CASCADE;
DROP TABLE IF EXISTS generated_code CASCADE;
DROP TABLE IF EXISTS schema_history CASCADE;
DROP TABLE IF EXISTS schemas CASCADE;
DROP TABLE IF EXISTS files CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE; -- Remove any existing custom users table

-- Projects table for project management (Enterprise-grade)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL CHECK (length(trim(name)) > 0),
    description TEXT,
    
    -- Supabase Auth integration (references auth.users)
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Metadata and lifecycle
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    archived_at TIMESTAMPTZ NULL, -- Soft delete for compliance
    
    -- Project configuration
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'archived')),
    settings JSONB DEFAULT '{}' NOT NULL,
    
    -- Search and indexing
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))
    ) STORED,
    
    -- Constraints
    CONSTRAINT projects_name_user_unique UNIQUE (name, user_id, archived_at),
    CONSTRAINT projects_settings_valid CHECK (jsonb_typeof(settings) = 'object')
);

-- Files table for file management (Enterprise-grade)
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- File metadata
    filename VARCHAR(500) NOT NULL CHECK (length(trim(filename)) > 0),
    file_path VARCHAR(1000), -- Increased for cloud storage paths
    file_type VARCHAR(100),
    file_size BIGINT CHECK (file_size >= 0),
    file_hash VARCHAR(64), -- SHA256 hash for deduplication and integrity
    
    -- Processing status
    upload_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processing_started_at TIMESTAMPTZ NULL,
    processing_completed_at TIMESTAMPTZ NULL,
    processing_error TEXT NULL,
    
    -- Metadata and compliance
    metadata JSONB DEFAULT '{}' NOT NULL,
    archived_at TIMESTAMPTZ NULL,
    retention_until TIMESTAMPTZ NULL, -- Data retention compliance
    
    -- Search capabilities
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(filename, ''))
    ) STORED,
    
    CONSTRAINT files_metadata_valid CHECK (jsonb_typeof(metadata) = 'object')
);

-- Schemas table for detected schemas (Enhanced)
CREATE TABLE schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    
    -- Schema identification
    schema_name VARCHAR(255) NOT NULL,
    schema_type VARCHAR(100) NOT NULL,
    schema_version INTEGER DEFAULT 1 CHECK (schema_version > 0),
    
    -- Schema data with compression for large schemas
    schema_data JSONB NOT NULL,
    compressed_schema_data BYTEA NULL, -- For very large schemas
    
    -- AI/ML metadata
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    detection_model VARCHAR(100),
    detection_metadata JSONB DEFAULT '{}',
    
    -- Lifecycle management
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    archived_at TIMESTAMPTZ NULL,
    
    -- Search and indexing
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(schema_name, ''))
    ) STORED,
    
    CONSTRAINT schemas_data_valid CHECK (jsonb_typeof(schema_data) = 'object'),
    CONSTRAINT schemas_detection_metadata_valid CHECK (jsonb_typeof(detection_metadata) = 'object')
);

-- Schema history for comprehensive version tracking
CREATE TABLE schema_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_id UUID NOT NULL REFERENCES schemas(id) ON DELETE CASCADE,
    
    -- Version information
    version INTEGER NOT NULL CHECK (version > 0),
    parent_version INTEGER NULL CHECK (parent_version > 0 AND parent_version < version),
    
    -- Change tracking
    changes JSONB NOT NULL,
    change_type VARCHAR(50) NOT NULL CHECK (change_type IN ('create', 'update', 'delete', 'merge', 'rollback')),
    change_summary TEXT,
    
    -- Attribution and timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES auth.users(id),
    
    -- Approval workflow
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ NULL,
    
    CONSTRAINT schema_history_changes_valid CHECK (jsonb_typeof(changes) = 'object'),
    CONSTRAINT schema_history_version_unique UNIQUE (schema_id, version)
);

-- Generated code tracking (Enhanced)
CREATE TABLE generated_code (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    schema_id UUID REFERENCES schemas(id) ON DELETE CASCADE,
    
    -- Code metadata
    code_type VARCHAR(100) NOT NULL, -- 'python', 'sql', 'json_schema', 'typescript', etc.
    framework VARCHAR(100), -- 'fastapi', 'express', 'django', etc.
    template_used VARCHAR(200),
    template_version VARCHAR(50),
    
    -- Code content (with compression for large files)
    generated_code TEXT NOT NULL,
    compressed_code BYTEA NULL,
    code_hash VARCHAR(64), -- SHA256 for deduplication
    
    -- Generation metadata
    generation_model VARCHAR(100),
    generation_parameters JSONB DEFAULT '{}',
    generation_duration_ms INTEGER,
    
    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    archived_at TIMESTAMPTZ NULL,
    
    CONSTRAINT generated_code_parameters_valid CHECK (jsonb_typeof(generation_parameters) = 'object')
);

-- Chat sessions for AI interactions (Enhanced)
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Session metadata
    session_name VARCHAR(255),
    session_context JSONB DEFAULT '{}', -- Store conversation context
    
    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_message_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    archived_at TIMESTAMPTZ NULL,
    
    -- Session configuration
    ai_provider VARCHAR(50) DEFAULT 'openai' CHECK (ai_provider IN ('openai', 'anthropic', 'google')),
    model_version VARCHAR(100),
    
    CONSTRAINT chat_sessions_context_valid CHECK (jsonb_typeof(session_context) = 'object')
);

-- Chat messages (Enhanced)
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    
    -- Message content
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    
    -- Enhanced metadata
    metadata JSONB DEFAULT '{}',
    token_count INTEGER,
    processing_time_ms INTEGER,
    
    -- Timestamps
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Search capabilities
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', content)
    ) STORED,
    
    CONSTRAINT chat_messages_metadata_valid CHECK (jsonb_typeof(metadata) = 'object')
);

-- Integrations configuration (Enhanced)
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Integration details
    integration_type VARCHAR(100) NOT NULL,
    integration_name VARCHAR(255),
    
    -- Configuration
    config JSONB NOT NULL,
    encrypted_credentials BYTEA, -- For sensitive data
    
    -- Status and health
    is_active BOOLEAN DEFAULT TRUE,
    last_health_check TIMESTAMPTZ,
    health_status VARCHAR(50) DEFAULT 'unknown',
    
    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    archived_at TIMESTAMPTZ NULL,
    
    CONSTRAINT integrations_config_valid CHECK (jsonb_typeof(config) = 'object')
);

-- Create comprehensive indexes for performance
-- Basic lookups
CREATE INDEX idx_projects_user_id ON projects(user_id) WHERE archived_at IS NULL;
CREATE INDEX idx_projects_status ON projects(status) WHERE archived_at IS NULL;
CREATE INDEX idx_projects_created_at ON projects(created_at);

CREATE INDEX idx_files_project_id ON files(project_id) WHERE archived_at IS NULL;
CREATE INDEX idx_files_processed ON files(processed) WHERE archived_at IS NULL;
CREATE INDEX idx_files_upload_date ON files(upload_date);
CREATE INDEX idx_files_hash ON files(file_hash) WHERE file_hash IS NOT NULL;

CREATE INDEX idx_schemas_project_id ON schemas(project_id) WHERE archived_at IS NULL;
CREATE INDEX idx_schemas_file_id ON schemas(file_id) WHERE archived_at IS NULL;
CREATE INDEX idx_schemas_type ON schemas(schema_type) WHERE archived_at IS NULL;
CREATE INDEX idx_schemas_confidence ON schemas(confidence_score DESC) WHERE archived_at IS NULL;

CREATE INDEX idx_schema_history_schema_id ON schema_history(schema_id);
CREATE INDEX idx_schema_history_version ON schema_history(schema_id, version);
CREATE INDEX idx_schema_history_created_by ON schema_history(created_by);

CREATE INDEX idx_generated_code_project_id ON generated_code(project_id) WHERE archived_at IS NULL;
CREATE INDEX idx_generated_code_schema_id ON generated_code(schema_id) WHERE archived_at IS NULL;
CREATE INDEX idx_generated_code_type ON generated_code(code_type) WHERE archived_at IS NULL;
CREATE INDEX idx_generated_code_hash ON generated_code(code_hash) WHERE code_hash IS NOT NULL;

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id) WHERE archived_at IS NULL;
CREATE INDEX idx_chat_sessions_project_id ON chat_sessions(project_id) WHERE archived_at IS NULL;
CREATE INDEX idx_chat_sessions_last_message ON chat_sessions(last_message_at DESC) WHERE archived_at IS NULL;

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp DESC);
CREATE INDEX idx_chat_messages_type ON chat_messages(message_type);

CREATE INDEX idx_integrations_project_id ON integrations(project_id) WHERE archived_at IS NULL;
CREATE INDEX idx_integrations_type ON integrations(integration_type) WHERE archived_at IS NULL;
CREATE INDEX idx_integrations_active ON integrations(is_active) WHERE archived_at IS NULL;

-- JSONB GIN indexes for fast JSON queries
CREATE INDEX idx_projects_settings_gin ON projects USING gin(settings);
CREATE INDEX idx_files_metadata_gin ON files USING gin(metadata);
CREATE INDEX idx_schemas_data_gin ON schemas USING gin(schema_data);
CREATE INDEX idx_schemas_detection_metadata_gin ON schemas USING gin(detection_metadata);
CREATE INDEX idx_schema_history_changes_gin ON schema_history USING gin(changes);
CREATE INDEX idx_generated_code_parameters_gin ON generated_code USING gin(generation_parameters);
CREATE INDEX idx_chat_sessions_context_gin ON chat_sessions USING gin(session_context);
CREATE INDEX idx_chat_messages_metadata_gin ON chat_messages USING gin(metadata);
CREATE INDEX idx_integrations_config_gin ON integrations USING gin(config);

-- Full-text search indexes
CREATE INDEX idx_projects_search ON projects USING gin(search_vector);
CREATE INDEX idx_files_search ON files USING gin(search_vector);
CREATE INDEX idx_schemas_search ON schemas USING gin(search_vector);
CREATE INDEX idx_chat_messages_search ON chat_messages USING gin(search_vector);

-- Composite indexes for common query patterns
CREATE INDEX idx_files_project_processed ON files(project_id, processed) WHERE archived_at IS NULL;
CREATE INDEX idx_schemas_project_type ON schemas(project_id, schema_type) WHERE archived_at IS NULL;
CREATE INDEX idx_chat_sessions_user_project ON chat_sessions(user_id, project_id) WHERE archived_at IS NULL;

-- Enable Row Level Security (RLS) for multi-tenant isolation
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE schemas ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_code ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;

-- RLS Policies - Users can only access their own data
CREATE POLICY "Users can manage their own projects" ON projects
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage files in their projects" ON files
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = files.project_id 
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage schemas in their projects" ON schemas
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = schemas.project_id 
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage schema history in their projects" ON schema_history
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM schemas s
            JOIN projects p ON p.id = s.project_id
            WHERE s.id = schema_history.schema_id 
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage generated code in their projects" ON generated_code
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = generated_code.project_id 
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage their own chat sessions" ON chat_sessions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage messages in their chat sessions" ON chat_messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM chat_sessions 
            WHERE chat_sessions.id = chat_messages.session_id 
            AND chat_sessions.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage integrations in their projects" ON integrations
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = integrations.project_id 
            AND projects.user_id = auth.uid()
        )
    );

-- Create functions for automated tasks
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_integrations_updated_at
    BEFORE UPDATE ON integrations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update last_message_at in chat sessions
CREATE OR REPLACE FUNCTION update_chat_session_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions 
    SET last_message_at = NEW.timestamp 
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_chat_session_last_message_trigger
    AFTER INSERT ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_session_last_message();

-- Create views for common queries
CREATE VIEW active_projects AS
SELECT * FROM projects 
WHERE archived_at IS NULL;

CREATE VIEW active_files AS
SELECT * FROM files 
WHERE archived_at IS NULL;

CREATE VIEW active_schemas AS
SELECT * FROM schemas 
WHERE archived_at IS NULL;

CREATE VIEW active_integrations AS
SELECT * FROM integrations 
WHERE archived_at IS NULL;

-- Project statistics view
CREATE VIEW project_stats AS
SELECT 
    p.id,
    p.name,
    p.user_id,
    COUNT(DISTINCT f.id) as file_count,
    COUNT(DISTINCT s.id) as schema_count,
    COUNT(DISTINCT gc.id) as generated_code_count,
    COUNT(DISTINCT cs.id) as chat_session_count,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN files f ON p.id = f.project_id AND f.archived_at IS NULL
LEFT JOIN schemas s ON p.id = s.project_id AND s.archived_at IS NULL
LEFT JOIN generated_code gc ON p.id = gc.project_id AND gc.archived_at IS NULL
LEFT JOIN chat_sessions cs ON p.id = cs.project_id AND cs.archived_at IS NULL
WHERE p.archived_at IS NULL
GROUP BY p.id, p.name, p.user_id, p.created_at, p.updated_at;

-- Grant permissions for Supabase service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Success notification
DO $$
BEGIN
    RAISE NOTICE '=============================================================';
    RAISE NOTICE 'SchemaSage Enterprise Database Setup COMPLETE!';
    RAISE NOTICE '';
    RAISE NOTICE 'Enterprise features enabled:';
    RAISE NOTICE '  ✓ UUID primary keys for better scalability';
    RAISE NOTICE '  ✓ Supabase Auth integration (no custom users table)';
    RAISE NOTICE '  ✓ Row Level Security (RLS) for multi-tenant isolation';
    RAISE NOTICE '  ✓ Full-text search with tsvector columns';
    RAISE NOTICE '  ✓ JSONB GIN indexes for fast JSON queries';
    RAISE NOTICE '  ✓ Audit trails and soft deletes';
    RAISE NOTICE '  ✓ Automatic triggers for timestamps';
    RAISE NOTICE '  ✓ Performance-optimized indexes';
    RAISE NOTICE '  ✓ Enterprise-grade constraints and validation';
    RAISE NOTICE '  ✓ Statistical views for analytics';
    RAISE NOTICE '';
    RAISE NOTICE 'Your SchemaSage database is ready for production!';
    RAISE NOTICE '=============================================================';
END $$;
