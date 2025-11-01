"""
SQLAlchemy models for database-migration service
Enterprise-grade database schema with encryption and audit trails
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, LargeBinary, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class DatabaseConnection(Base):
    """
    Database connections table with enterprise security features
    - Encrypted password storage
    - User isolation
    - Audit trail
    - Connection metadata
    """
    __tablename__ = "database_connections"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # From JWT token
    
    # Connection metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Connection details
    db_type = Column(String(50), nullable=False, index=True)  # postgresql, mysql, etc.
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=True)
    database_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=False)
    
    # Encrypted sensitive data
    encrypted_password = Column(LargeBinary, nullable=False)  # AES encrypted
    encrypted_connection_params = Column(LargeBinary, nullable=True)  # Additional params
    
    # SSL/Security configuration
    ssl_enabled = Column(Boolean, default=False)
    ssl_cert_path = Column(String(500), nullable=True)
    ssl_key_path = Column(String(500), nullable=True)
    ssl_ca_path = Column(String(500), nullable=True)
    ssl_mode = Column(String(50), default="prefer")
    
    # Connection status and health
    status = Column(String(50), default="created", index=True)  # created, connected, error, disabled
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_connection_attempt = Column(DateTime(timezone=True), nullable=True)
    connection_test_count = Column(Integer, default=0)
    successful_connections = Column(Integer, default=0)
    failed_connections = Column(Integer, default=0)
    
    # Performance metrics
    average_response_time_ms = Column(Integer, nullable=True)
    last_response_time_ms = Column(Integer, nullable=True)
    
    # Schema and usage metadata
    detected_schemas = Column(JSONB, nullable=True)  # Store detected schema info
    connection_metadata = Column(JSONB, nullable=True)  # Additional metadata
    usage_statistics = Column(JSONB, nullable=True)  # Usage tracking
    
    # Audit and lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=False)  # User ID who created
    last_modified_by = Column(String(255), nullable=True)  # User ID who last modified
    
    # Soft delete and archival
    is_active = Column(Boolean, default=True, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by = Column(String(255), nullable=True)
    
    # Enterprise features
    tags = Column(JSONB, nullable=True)  # User-defined tags for organization
    environment = Column(String(50), nullable=True, index=True)  # dev, staging, prod
    team_id = Column(String(255), nullable=True, index=True)  # For team sharing
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_connections', 'user_id', 'is_active'),
        Index('idx_connection_status', 'status', 'is_active'),
        Index('idx_connection_type', 'db_type', 'environment'),
        Index('idx_connection_health', 'last_tested_at', 'status'),
    )


class ConnectionAuditLog(Base):
    """
    Audit log for all connection-related activities
    Tracks who did what when for security and compliance
    """
    __tablename__ = "connection_audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    connection_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Nullable for failed operations
    user_id = Column(Integer, nullable=False, index=True)
    
    # Audit details
    action = Column(String(100), nullable=False, index=True)  # created, tested, updated, deleted, etc.
    action_description = Column(Text, nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Action results
    success = Column(Boolean, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Metadata (renamed to avoid SQLAlchemy reserved word)
    action_metadata = Column(JSONB, nullable=True)  # Additional context
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Indexes for audit queries
    __table_args__ = (
        Index('idx_audit_connection_action', 'connection_id', 'action', 'created_at'),
        Index('idx_audit_user_timeline', 'user_id', 'created_at'),
        Index('idx_audit_security', 'action', 'success', 'created_at'),
    )


class ConnectionSecret(Base):
    """
    Separate table for highly sensitive connection secrets
    Additional layer of security with encryption keys
    """
    __tablename__ = "connection_secrets"
    
    # Primary key and reference
    connection_id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Encrypted secrets with key rotation support
    encrypted_data = Column(LargeBinary, nullable=False)  # JSON with all secrets
    encryption_key_version = Column(Integer, default=1, nullable=False)
    encryption_algorithm = Column(String(50), default="AES-256-GCM", nullable=False)
    
    # Key derivation info (for security)
    salt = Column(LargeBinary, nullable=False)  # For key derivation
    iterations = Column(Integer, default=100000, nullable=False)  # PBKDF2 iterations
    
    # Access control
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    
    # Security features
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Secret expiration
    rotation_required = Column(Boolean, default=False)  # Force password rotation


class UserConnectionQuota(Base):
    """
    Track user connection quotas and usage limits
    Enterprise feature for resource management
    """
    __tablename__ = "user_connection_quotas"
    
    # Primary key
    user_id = Column(Integer, primary_key=True)
    
    # Quota limits
    max_connections = Column(Integer, default=10, nullable=False)
    max_test_requests_per_hour = Column(Integer, default=100, nullable=False)
    max_schema_imports_per_day = Column(Integer, default=50, nullable=False)
    
    # Current usage
    current_connections = Column(Integer, default=0, nullable=False)
    test_requests_this_hour = Column(Integer, default=0, nullable=False)
    schema_imports_today = Column(Integer, default=0, nullable=False)
    
    # Reset timestamps
    last_hour_reset = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_day_reset = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Subscription info
    plan_type = Column(String(50), default="free", nullable=False)  # free, pro, enterprise
    plan_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SchemaSnapshot(Base):
    """
    Store schema snapshots for version control and drift detection
    """
    __tablename__ = "schema_snapshots"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Snapshot metadata
    snapshot_name = Column(String(255), nullable=True)
    schema_version = Column(String(50), nullable=True)
    
    # Schema data (compressed for large schemas)
    schema_data = Column(JSONB, nullable=False)  # Full schema structure
    compressed_schema = Column(LargeBinary, nullable=True)  # Gzipped for large schemas
    schema_hash = Column(String(64), nullable=False, index=True)  # SHA-256 for change detection
    
    # Statistics
    table_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    index_count = Column(Integer, default=0)
    
    # Capture details
    capture_duration_ms = Column(Integer, nullable=True)
    capture_method = Column(String(50), nullable=True)  # auto, manual, scheduled
    
    # Lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    is_baseline = Column(Boolean, default=False, index=True)  # Mark as baseline version
    
    # Indexes for version control queries
    __table_args__ = (
        Index('idx_schema_connection_time', 'connection_id', 'created_at'),
        Index('idx_schema_hash_detection', 'connection_id', 'schema_hash'),
        Index('idx_schema_baselines', 'connection_id', 'is_baseline'),
    )