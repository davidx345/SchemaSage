"""Initial enterprise database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-10-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial enterprise database schema"""
    
    # Create database_connections table
    op.create_table(
        'database_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('db_type', sa.String(50), nullable=False, index=True),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=True),
        sa.Column('database_name', sa.String(255), nullable=True),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('encrypted_password', sa.LargeBinary, nullable=False),
        sa.Column('encrypted_connection_params', sa.LargeBinary, nullable=True),
        sa.Column('ssl_enabled', sa.Boolean, default=False),
        sa.Column('ssl_cert_path', sa.String(500), nullable=True),
        sa.Column('ssl_key_path', sa.String(500), nullable=True),
        sa.Column('ssl_ca_path', sa.String(500), nullable=True),
        sa.Column('ssl_mode', sa.String(50), default='prefer'),
        sa.Column('status', sa.String(50), default='created', index=True),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_connection_attempt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connection_test_count', sa.Integer, default=0),
        sa.Column('successful_connections', sa.Integer, default=0),
        sa.Column('failed_connections', sa.Integer, default=0),
        sa.Column('average_response_time_ms', sa.Integer, nullable=True),
        sa.Column('last_response_time_ms', sa.Integer, nullable=True),
        sa.Column('detected_schemas', postgresql.JSONB, nullable=True),
        sa.Column('connection_metadata', postgresql.JSONB, nullable=True),
        sa.Column('usage_statistics', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('last_modified_by', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_by', sa.String(255), nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=True),
        sa.Column('environment', sa.String(50), nullable=True, index=True),
        sa.Column('team_id', sa.String(255), nullable=True, index=True),
    )
    
    # Create indexes for database_connections
    op.create_index('idx_user_connections', 'database_connections', ['user_id', 'is_active'])
    op.create_index('idx_connection_status', 'database_connections', ['status', 'is_active'])
    op.create_index('idx_connection_type', 'database_connections', ['db_type', 'environment'])
    op.create_index('idx_connection_health', 'database_connections', ['last_tested_at', 'status'])
    
    # Create connection_audit_logs table
    op.create_table(
        'connection_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('action_description', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True, index=True),
        sa.Column('success', sa.Boolean, nullable=False, index=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    
    # Create indexes for connection_audit_logs
    op.create_index('idx_audit_connection_action', 'connection_audit_logs', ['connection_id', 'action', 'created_at'])
    op.create_index('idx_audit_user_timeline', 'connection_audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_security', 'connection_audit_logs', ['action', 'success', 'created_at'])
    
    # Create connection_secrets table
    op.create_table(
        'connection_secrets',
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('encrypted_data', sa.LargeBinary, nullable=False),
        sa.Column('encryption_key_version', sa.Integer, default=1, nullable=False),
        sa.Column('encryption_algorithm', sa.String(50), default='AES-256-GCM', nullable=False),
        sa.Column('salt', sa.LargeBinary, nullable=False),
        sa.Column('iterations', sa.Integer, default=100000, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer, default=0),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rotation_required', sa.Boolean, default=False),
    )
    
    # Create user_connection_quotas table
    op.create_table(
        'user_connection_quotas',
        sa.Column('user_id', sa.String(255), primary_key=True),
        sa.Column('max_connections', sa.Integer, default=10, nullable=False),
        sa.Column('max_test_requests_per_hour', sa.Integer, default=100, nullable=False),
        sa.Column('max_schema_imports_per_day', sa.Integer, default=50, nullable=False),
        sa.Column('current_connections', sa.Integer, default=0, nullable=False),
        sa.Column('test_requests_this_hour', sa.Integer, default=0, nullable=False),
        sa.Column('schema_imports_today', sa.Integer, default=0, nullable=False),
        sa.Column('last_hour_reset', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_day_reset', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('plan_type', sa.String(50), default='free', nullable=False),
        sa.Column('plan_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create schema_snapshots table
    op.create_table(
        'schema_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('snapshot_name', sa.String(255), nullable=True),
        sa.Column('schema_version', sa.String(50), nullable=True),
        sa.Column('schema_data', postgresql.JSONB, nullable=False),
        sa.Column('compressed_schema', sa.LargeBinary, nullable=True),
        sa.Column('schema_hash', sa.String(64), nullable=False, index=True),
        sa.Column('table_count', sa.Integer, default=0),
        sa.Column('column_count', sa.Integer, default=0),
        sa.Column('relationship_count', sa.Integer, default=0),
        sa.Column('index_count', sa.Integer, default=0),
        sa.Column('capture_duration_ms', sa.Integer, nullable=True),
        sa.Column('capture_method', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('is_baseline', sa.Boolean, default=False, index=True),
    )
    
    # Create indexes for schema_snapshots
    op.create_index('idx_schema_connection_time', 'schema_snapshots', ['connection_id', 'created_at'])
    op.create_index('idx_schema_hash_detection', 'schema_snapshots', ['connection_id', 'schema_hash'])
    op.create_index('idx_schema_baselines', 'schema_snapshots', ['connection_id', 'is_baseline'])


def downgrade() -> None:
    """Drop all enterprise database tables"""
    
    # Drop indexes first
    op.drop_index('idx_schema_baselines', table_name='schema_snapshots')
    op.drop_index('idx_schema_hash_detection', table_name='schema_snapshots')
    op.drop_index('idx_schema_connection_time', table_name='schema_snapshots')
    
    op.drop_index('idx_audit_security', table_name='connection_audit_logs')
    op.drop_index('idx_audit_user_timeline', table_name='connection_audit_logs')
    op.drop_index('idx_audit_connection_action', table_name='connection_audit_logs')
    
    op.drop_index('idx_connection_health', table_name='database_connections')
    op.drop_index('idx_connection_type', table_name='database_connections')
    op.drop_index('idx_connection_status', table_name='database_connections')
    op.drop_index('idx_user_connections', table_name='database_connections')
    
    # Drop tables
    op.drop_table('schema_snapshots')
    op.drop_table('user_connection_quotas')
    op.drop_table('connection_secrets')
    op.drop_table('connection_audit_logs')
    op.drop_table('database_connections')