"""
SQLAlchemy models for Schema Detection service
Stores detected schemas, analysis results, and processing history
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class SchemaDetectionJob(Base):
    """
    Schema detection jobs table
    Tracks schema detection requests and their processing status
    """
    __tablename__ = "schema_detection_jobs"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # From JWT token
    
    # Job metadata
    job_name = Column(String(500), nullable=True)
    job_description = Column(Text, nullable=True)
    
    # Input data information
    input_format = Column(String(50), nullable=False, index=True)  # json, csv, xml, sql, etc.
    input_size_bytes = Column(Integer, nullable=True)
    input_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for deduplication
    
    # Processing configuration
    detection_settings = Column(JSONB, nullable=True)  # Detection parameters
    ai_enhancement_enabled = Column(Boolean, default=True)
    relationship_detection_enabled = Column(Boolean, default=True)
    confidence_threshold = Column(Float, default=0.7)
    
    # Processing status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    progress_percentage = Column(Integer, default=0)
    
    # Processing results
    detected_tables_count = Column(Integer, default=0)
    detected_columns_count = Column(Integer, default=0)
    detected_relationships_count = Column(Integer, default=0)
    overall_confidence_score = Column(Float, nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    cpu_time_ms = Column(Integer, nullable=True)
    memory_usage_mb = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    detected_schemas = relationship("DetectedSchema", back_populates="detection_job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SchemaDetectionJob(id='{self.id}', status='{self.status}')>"


class DetectedSchema(Base):
    """
    Detected schemas table
    Stores the actual schema structures detected from input data
    """
    __tablename__ = "detected_schemas"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    detection_job_id = Column(UUID(as_uuid=True), ForeignKey('schema_detection_jobs.id'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Schema metadata
    schema_name = Column(String(255), nullable=False, index=True)
    schema_version = Column(String(50), default="1.0")
    schema_type = Column(String(50), default="relational", index=True)  # relational, document, key-value
    
    # Schema structure (stored as JSONB for complex queries)
    schema_structure = Column(JSONB, nullable=False)  # Complete schema definition
    tables_data = Column(JSONB, nullable=True)  # Table definitions
    relationships_data = Column(JSONB, nullable=True)  # Relationship definitions
    indexes_data = Column(JSONB, nullable=True)  # Index definitions
    constraints_data = Column(JSONB, nullable=True)  # Constraint definitions
    
    # Detection metadata
    detection_model = Column(String(100), nullable=True)  # AI model used for detection
    detection_confidence = Column(Float, nullable=True)
    detection_method = Column(String(100), nullable=True)  # rule-based, ai-enhanced, hybrid
    
    # Schema statistics
    table_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    index_count = Column(Integer, default=0)
    constraint_count = Column(Integer, default=0)
    
    # Quality metrics
    completeness_score = Column(Float, nullable=True)  # 0.0 - 1.0
    consistency_score = Column(Float, nullable=True)  # 0.0 - 1.0
    complexity_score = Column(Float, nullable=True)  # 0.0 - 1.0
    
    # AI enhancement results
    ai_suggestions = Column(JSONB, nullable=True)  # AI-generated suggestions
    semantic_annotations = Column(JSONB, nullable=True)  # Semantic meaning of fields
    business_rules = Column(JSONB, nullable=True)  # Inferred business rules
    
    # Usage and sharing
    is_public = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Search optimization
    search_vector = Column(Text, nullable=True)  # Full-text search vector
    tags = Column(JSONB, nullable=True)  # User-defined tags
    
    # Relationships
    detection_job = relationship("SchemaDetectionJob", back_populates="detected_schemas")
    analyses = relationship("SchemaAnalysis", back_populates="schema", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DetectedSchema(id='{self.id}', name='{self.schema_name}')>"


class SchemaAnalysis(Base):
    """
    Schema analysis results table
    Stores detailed analysis results for detected schemas
    """
    __tablename__ = "schema_analyses"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    schema_id = Column(UUID(as_uuid=True), ForeignKey('detected_schemas.id'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Analysis metadata
    analysis_type = Column(String(100), nullable=False, index=True)  # quality, performance, security, etc.
    analysis_version = Column(String(50), default="1.0")
    analyzer_model = Column(String(100), nullable=True)  # AI model used for analysis
    
    # Analysis results
    analysis_results = Column(JSONB, nullable=False)  # Detailed analysis results
    recommendations = Column(JSONB, nullable=True)  # Improvement recommendations
    warnings = Column(JSONB, nullable=True)  # Potential issues found
    metrics = Column(JSONB, nullable=True)  # Calculated metrics
    
    # Scoring
    overall_score = Column(Float, nullable=True)  # Overall analysis score
    quality_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    maintainability_score = Column(Float, nullable=True)
    
    # Processing info
    processing_time_ms = Column(Integer, nullable=True)
    analysis_depth = Column(String(50), default="standard")  # basic, standard, comprehensive
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    schema = relationship("DetectedSchema", back_populates="analyses")
    
    def __repr__(self):
        return f"<SchemaAnalysis(id='{self.id}', type='{self.analysis_type}')>"


class SchemaUsageStatistics(Base):
    """
    Track usage statistics for schema detection service
    """
    __tablename__ = "schema_usage_statistics"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    
    # Usage counters
    detection_jobs_created = Column(Integer, default=0)
    detection_jobs_completed = Column(Integer, default=0)
    detection_jobs_failed = Column(Integer, default=0)
    schemas_detected = Column(Integer, default=0)
    analyses_performed = Column(Integer, default=0)
    
    # Data processing statistics
    total_input_size_bytes = Column(Integer, default=0)
    total_processing_time_ms = Column(Integer, default=0)
    average_processing_time_ms = Column(Integer, default=0)
    
    # AI usage
    ai_enhancements_used = Column(Integer, default=0)
    ai_tokens_consumed = Column(Integer, default=0)
    ai_processing_time_ms = Column(Integer, default=0)
    
    # Quality metrics
    average_confidence_score = Column(Float, default=0.0)
    average_completeness_score = Column(Float, default=0.0)
    
    # Usage details as JSONB
    usage_details = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SchemaUsageStatistics(user_id='{self.user_id}', date='{self.date}')>"


class SchemaFeedback(Base):
    """
    User feedback on detected schemas and analysis results
    """
    __tablename__ = "schema_feedback"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    schema_id = Column(UUID(as_uuid=True), ForeignKey('detected_schemas.id'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Feedback details
    feedback_type = Column(String(50), nullable=False, index=True)  # accuracy, usefulness, quality
    rating = Column(Integer, nullable=False)  # 1-5 star rating
    feedback_text = Column(Text, nullable=True)
    
    # Specific feedback areas
    schema_accuracy_rating = Column(Integer, nullable=True)
    relationship_accuracy_rating = Column(Integer, nullable=True)
    ai_suggestions_rating = Column(Integer, nullable=True)
    performance_rating = Column(Integer, nullable=True)
    
    # Improvement suggestions
    suggested_improvements = Column(JSONB, nullable=True)
    reported_issues = Column(JSONB, nullable=True)
    
    # Context
    usage_context = Column(String(100), nullable=True)  # migration, analysis, documentation, etc.
    user_experience_level = Column(String(50), nullable=True)  # beginner, intermediate, expert
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SchemaFeedback(id='{self.id}', rating={self.rating})>"


class CloudDeployment(Base):
    """
    Cloud deployment tracking table
    Stores information about cloud infrastructure deployments
    """
    __tablename__ = "cloud_deployments"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Link to project if exists
    
    # Input description
    description = Column(Text, nullable=False)
    provider = Column(String(20), nullable=False, index=True)  # aws, gcp, azure
    
    # Configuration
    database_type = Column(String(50), nullable=False)  # postgresql, mysql, mongodb
    database_version = Column(String(20), nullable=True)
    instance_type = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    storage_gb = Column(Integer, nullable=False)
    
    # Generated schema (stored as JSONB for querying)
    schema_json = Column(JSONB, nullable=False)
    
    # Cloud resources
    cloud_instance_id = Column(String(200), nullable=True, index=True)
    connection_string = Column(Text, nullable=True)  # Encrypted
    endpoint = Column(String(500), nullable=True)
    port = Column(Integer, nullable=True)
    
    # Status tracking
    status = Column(
        String(20), 
        nullable=False, 
        default='pending', 
        index=True
    )  # pending, analyzing, provisioning, configuring, generating, ready, failed
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(200), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Cost tracking
    estimated_monthly_cost = Column(Float, nullable=True)
    actual_monthly_cost = Column(Float, nullable=True)
    cost_breakdown = Column(JSONB, nullable=True)
    
    # Generated assets metadata
    generated_code = Column(Boolean, default=False)
    generated_migrations = Column(Boolean, default=False)
    generated_api = Column(Boolean, default=False)
    generated_assets = Column(JSONB, nullable=True)  # Store file paths/content
    
    # Deployment options
    auto_scaling = Column(Boolean, default=False)
    backup_enabled = Column(Boolean, default=True)
    multi_az = Column(Boolean, default=False)
    public_access = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    logs = relationship("DeploymentLog", back_populates="deployment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CloudDeployment(id='{self.id}', provider='{self.provider}', status='{self.status}')>"


class DeploymentLog(Base):
    """
    Deployment logs table
    Stores detailed logs for each deployment step
    """
    __tablename__ = "deployment_logs"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey('cloud_deployments.id'), nullable=False, index=True)
    
    # Log details
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)  # info, warning, error, success
    message = Column(Text, nullable=False)
    step = Column(String(200), nullable=True)  # Which deployment step
    metadata = Column(JSONB, nullable=True)  # Additional context
    
    # Relationships
    deployment = relationship("CloudDeployment", back_populates="logs")
    
    def __repr__(self):
        return f"<DeploymentLog(deployment_id='{self.deployment_id}', level='{self.level}')>"


class CloudCredentials(Base):
    """
    Cloud credentials table (encrypted)
    Stores encrypted cloud provider credentials
    """
    __tablename__ = "cloud_credentials"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    provider = Column(String(20), nullable=False, index=True)  # aws, gcp, azure
    
    # Encrypted credentials (use pgcrypto or application-level encryption)
    credentials_encrypted = Column(Text, nullable=False)
    
    # Metadata
    region = Column(String(50), nullable=True)
    account_id = Column(String(100), nullable=True)
    account_name = Column(String(200), nullable=True)
    is_valid = Column(Boolean, default=True)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    validation_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<CloudCredentials(user_id='{self.user_id}', provider='{self.provider}')>"
