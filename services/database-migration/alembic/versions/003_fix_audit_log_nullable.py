"""Fix audit log connection_id to be nullable

Revision ID: 003_fix_audit_log_nullable
Revises: 002_fix_user_id_type
Create Date: 2025-11-01 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_fix_audit_log_nullable'
down_revision = '002_fix_user_id_type'
branch_label = None
depends_on = None


def upgrade():
    """
    Make connection_id nullable in connection_audit_logs table
    This allows logging audit events for failed connection creation attempts
    """
    # Make connection_id nullable
    op.alter_column(
        'connection_audit_logs',
        'connection_id',
        existing_type=postgresql.UUID(),
        nullable=True,
        existing_nullable=False
    )


def downgrade():
    """
    Revert connection_id to non-nullable
    Note: This will fail if there are NULL values in the column
    """
    # Remove NULL values first (if any)
    op.execute(
        "DELETE FROM connection_audit_logs WHERE connection_id IS NULL"
    )
    
    # Make connection_id non-nullable again
    op.alter_column(
        'connection_audit_logs',
        'connection_id',
        existing_type=postgresql.UUID(),
        nullable=False,
        existing_nullable=True
    )
