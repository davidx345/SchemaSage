"""
SQLAlchemy models for Project Management service
Stores projects, files, collaboration data, and project settings
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, ForeignKey, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, TSVECTOR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class Project(Base):
    """
    Projects table - central project management
    Stores project metadata, settings, and collaboration info
    """
    __tablename__ = "projects"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Project owner
    
    # Project metadata
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    project_type = Column(String(100), default="database_migration", index=True)  # database_migration, schema_analysis, etc.
    
    # Project status and lifecycle
    status = Column(String(50), default="active", index=True)  # active, paused, completed, archived
    priority = Column(String(20), default="medium", index=True)  # low, medium, high, critical
    
    # Project settings stored as JSONB
    settings = Column(JSONB, nullable=True)  # Project-specific configuration
    preferences = Column(JSONB, nullable=True)  # User preferences for this project
    
    # Tags and categorization
    tags = Column(JSONB, nullable=True)  # User-defined tags
    category = Column(String(100), nullable=True, index=True)  # Business category
    environment = Column(String(50), default="development", index=True)  # development, staging, production
    
    # Collaboration and sharing
    is_public = Column(Boolean, default=False, index=True)
    is_template = Column(Boolean, default=False, index=True)  # Can be used as template
    team_id = Column(String(255), nullable=True, index=True)  # For team projects
    collaborators = Column(JSONB, nullable=True)  # List of collaborator user IDs with permissions
    
    # Project progress and metrics
    progress_percentage = Column(Integer, default=0)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, default=0)
    
    # File and data management
    total_files = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    
    # Quality and health metrics
    health_score = Column(Float, nullable=True)  # Overall project health 0.0-1.0
    quality_score = Column(Float, nullable=True)  # Code/schema quality 0.0-1.0
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    
    # Timeline and deadlines
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Search optimization (GENERATED column - do not insert)
    search_vector = Column(TSVECTOR, nullable=True, server_default=func.text("''"), insert_default=func.text("DEFAULT"))
    
    # Relationships
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("ProjectActivity", back_populates="project", cascade="all, delete-orphan")
    schemas = relationship("ProjectSchema", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id='{self.id}', name='{self.name}', status='{self.status}')>"


class ProjectFile(Base):
    """
    Project files table
    Stores uploaded files, processing status, and file metadata
    """
    __tablename__ = "project_files"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # File metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_extension = Column(String(20), nullable=True, index=True)
    mime_type = Column(String(100), nullable=True)
    
    # File storage
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for deduplication
    storage_path = Column(String(1000), nullable=True)  # Cloud storage path
    local_path = Column(String(1000), nullable=True)  # Local file path if applicable
    
    # File content and processing
    file_content = Column(LargeBinary, nullable=True)  # Small files stored in DB
    is_processed = Column(Boolean, default=False, index=True)
    processing_status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # File analysis results
    content_type = Column(String(100), nullable=True, index=True)  # schema, data, config, etc.
    schema_format = Column(String(50), nullable=True, index=True)  # json, csv, sql, xml, etc.
    detected_encoding = Column(String(50), nullable=True)
    line_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    
    # Processing metadata
    analysis_results = Column(JSONB, nullable=True)  # File analysis results
    extraction_metadata = Column(JSONB, nullable=True)  # Data extraction metadata
    
    # Version control
    version = Column(Integer, default=1)
    parent_file_id = Column(UUID(as_uuid=True), nullable=True)  # For file versioning
    is_latest_version = Column(Boolean, default=True, index=True)
    
    # Access and usage
    download_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="files")
    
    def __repr__(self):
        return f"<ProjectFile(id='{self.id}', filename='{self.filename}')>"


class ProjectSchema(Base):
    """
    Project schemas table
    Links detected schemas to projects and stores project-specific schema data
    """
    __tablename__ = "project_schemas"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Schema identification
    schema_name = Column(String(500), nullable=False, index=True)
    schema_version = Column(String(50), default="1.0")
    source_file_id = Column(UUID(as_uuid=True), ForeignKey('project_files.id'), nullable=True, index=True)
    external_schema_id = Column(String(255), nullable=True, index=True)  # Reference to schema-detection service
    
    # Schema content
    schema_data = Column(JSONB, nullable=False)  # Complete schema definition
    tables_count = Column(Integer, default=0)
    columns_count = Column(Integer, default=0)
    relationships_count = Column(Integer, default=0)
    
    # Schema status in project context
    is_primary = Column(Boolean, default=False, index=True)  # Primary schema for project
    is_active = Column(Boolean, default=True, index=True)
    validation_status = Column(String(50), default="pending", index=True)  # pending, valid, invalid, warning
    
    # Project-specific schema metadata
    role_in_project = Column(String(100), nullable=True)  # source, target, reference, etc.
    migration_status = Column(String(50), nullable=True, index=True)  # for migration projects
    code_generation_status = Column(String(50), nullable=True, index=True)
    
    # Quality and analysis
    quality_score = Column(Float, nullable=True)
    complexity_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    
    # Usage tracking
    code_generated_count = Column(Integer, default=0)
    export_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="schemas")
    
    def __repr__(self):
        return f"<ProjectSchema(id='{self.id}', name='{self.schema_name}')>"


class ProjectActivity(Base):
    """
    Project activity log
    Tracks all actions and changes within projects
    """
    __tablename__ = "project_activities"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=True, index=True)  # Made nullable for global activities
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)  # file_upload, schema_detected, code_generated, etc.
    activity_category = Column(String(50), nullable=False, index=True)  # file, schema, analysis, collaboration, etc.
    action = Column(String(100), nullable=False)  # created, updated, deleted, shared, etc.
    
    # Activity description and metadata
    description = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)  # Additional activity details
    
    # Referenced objects
    target_object_type = Column(String(50), nullable=True)  # file, schema, user, etc.
    target_object_id = Column(String(255), nullable=True)
    
    # Activity context
    ip_address = Column(String(45), nullable=True)  # User IP address
    user_agent = Column(Text, nullable=True)  # User browser/client
    session_id = Column(String(255), nullable=True)
    
    # Impact and importance
    impact_level = Column(String(20), default="low", index=True)  # low, medium, high
    is_automated = Column(Boolean, default=False, index=True)  # Human vs automated activity
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    project = relationship("Project", back_populates="activities")
    
    def __repr__(self):
        return f"<ProjectActivity(id='{self.id}', type='{self.activity_type}')>"


class ProjectCollaboration(Base):
    """
    Project collaboration and sharing
    Manages project access, permissions, and collaboration features
    """
    __tablename__ = "project_collaborations"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    collaborator_user_id = Column(String(255), nullable=False, index=True)
    invited_by_user_id = Column(String(255), nullable=False, index=True)
    
    # Collaboration details
    role = Column(String(50), default="viewer", index=True)  # owner, admin, editor, viewer
    permissions = Column(JSONB, nullable=True)  # Detailed permissions
    
    # Invitation and acceptance
    invitation_status = Column(String(50), default="pending", index=True)  # pending, accepted, declined, revoked
    invitation_token = Column(String(255), nullable=True, unique=True)
    invitation_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Access control
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    can_export = Column(Boolean, default=True)
    
    # Usage tracking
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ProjectCollaboration(id='{self.id}', role='{self.role}')>"


class ProjectTemplate(Base):
    """
    Project templates
    Reusable project configurations and workflows
    """
    __tablename__ = "project_templates"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_by_user_id = Column(String(255), nullable=False, index=True)
    
    # Template metadata
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    
    # Template configuration
    template_data = Column(JSONB, nullable=False)  # Complete template definition
    default_settings = Column(JSONB, nullable=True)  # Default project settings
    required_files = Column(JSONB, nullable=True)  # Required file types/formats
    
    # Template properties
    is_public = Column(Boolean, default=False, index=True)
    is_official = Column(Boolean, default=False, index=True)  # Official SchemaSage template
    difficulty_level = Column(String(20), default="beginner", index=True)  # beginner, intermediate, advanced
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Percentage of successful projects from this template
    average_completion_time_hours = Column(Integer, nullable=True)
    
    # Ratings and feedback
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ProjectTemplate(id='{self.id}', name='{self.name}')>"