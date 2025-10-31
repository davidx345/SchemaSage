"""Fix user_id data type to integer

Revision ID: 002_fix_user_id_type
Revises: 001_initial_schema
Create Date: 2025-10-31 10:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_fix_user_id_type'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert user_id from VARCHAR to INTEGER in all tables"""
    
    # Fix user_connection_quotas.user_id (primary key)
    # Need to handle this carefully since it's a primary key
    op.execute("""
        ALTER TABLE user_connection_quotas 
        ALTER COLUMN user_id TYPE INTEGER USING user_id::integer
    """)
    
    # Fix connection_audit_logs.user_id
    op.execute("""
        ALTER TABLE connection_audit_logs 
        ALTER COLUMN user_id TYPE INTEGER USING user_id::integer
    """)
    
    # Fix database_connections.user_id
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'database_connections' 
                AND column_name = 'user_id'
                AND data_type = 'character varying'
            ) THEN
                ALTER TABLE database_connections 
                ALTER COLUMN user_id TYPE INTEGER USING user_id::integer;
            END IF;
        END $$;
    """)
    
    # Fix schema_snapshots.user_id
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'schema_snapshots' 
                AND column_name = 'user_id'
                AND data_type = 'character varying'
            ) THEN
                ALTER TABLE schema_snapshots 
                ALTER COLUMN user_id TYPE INTEGER USING user_id::integer;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Revert user_id back to VARCHAR"""
    
    # Revert user_connection_quotas.user_id
    op.execute("""
        ALTER TABLE user_connection_quotas 
        ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::varchar
    """)
    
    # Revert connection_audit_logs.user_id
    op.execute("""
        ALTER TABLE connection_audit_logs 
        ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::varchar
    """)
    
    # Revert database_connections.user_id
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'database_connections' 
                AND column_name = 'user_id'
                AND data_type = 'integer'
            ) THEN
                ALTER TABLE database_connections 
                ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::varchar;
            END IF;
        END $$;
    """)
    
    # Revert schema_snapshots.user_id
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'schema_snapshots' 
                AND column_name = 'user_id'
                AND data_type = 'integer'
            ) THEN
                ALTER TABLE schema_snapshots 
                ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::varchar;
            END IF;
        END $$;
    """)
