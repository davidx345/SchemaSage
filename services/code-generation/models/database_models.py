"""
SQLAlchemy models for Code Generation service
Stores generated code, templates, generation history, and usage analytics
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, ForeignKey, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class CodeGenerationJob(Base):
    """
    Code generation jobs table
    Tracks code generation requests and their processing status
    """
    __tablename__ = "code_generation_jobs"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Job metadata
    job_name = Column(String(500), nullable=True)
    job_description = Column(Text, nullable=True)
    
    # Input schema information
    source_schema_id = Column(String(255), nullable=True, index=True)  # Reference to schema-detection service
    project_id = Column(String(255), nullable=True, index=True)  # Reference to project-management service
    schema_data = Column(JSONB, nullable=False)  # Complete schema data for generation
    
    # Generation configuration
    output_format = Column(String(50), nullable=False, index=True)  # sqlalchemy, django, sql, etc.
    target_language = Column(String(50), nullable=False, index=True)  # python, sql, typescript, etc.
    framework = Column(String(50), nullable=True, index=True)  # fastapi, django, express, etc.
    template_name = Column(String(100), nullable=True, index=True)  # Template used for generation
    
    # Generation settings
    generation_settings = Column(JSONB, nullable=True)  # Detailed generation configuration
    include_relationships = Column(Boolean, default=True)
    include_constraints = Column(Boolean, default=True)
    include_indexes = Column(Boolean, default=True)
    include_documentation = Column(Boolean, default=True)
    use_type_hints = Column(Boolean, default=True)
    
    # Processing status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    progress_percentage = Column(Integer, default=0)
    
    # Generation results
    generated_files_count = Column(Integer, default=0)
    total_lines_generated = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    
    # Quality metrics
    code_quality_score = Column(Float, nullable=True)  # 0.0-1.0
    complexity_score = Column(Float, nullable=True)
    maintainability_score = Column(Float, nullable=True)
    
    # Performance metrics
    generation_time_ms = Column(Integer, nullable=True)
    template_processing_time_ms = Column(Integer, nullable=True)
    validation_time_ms = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    warnings = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    generated_files = relationship("GeneratedCodeFile", back_populates="generation_job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CodeGenerationJob(id='{self.id}', status='{self.status}', format='{self.output_format}')>"


class GeneratedCodeFile(Base):
    """
    Generated code files table
    Stores individual files generated from schemas
    """
    __tablename__ = "generated_code_files"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    generation_job_id = Column(UUID(as_uuid=True), ForeignKey('code_generation_jobs.id'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # File metadata
    filename = Column(String(500), nullable=False, index=True)
    file_path = Column(String(1000), nullable=True)  # Relative path within project
    file_type = Column(String(50), nullable=False, index=True)  # model, migration, api, test, etc.
    
    # Code content
    generated_code = Column(Text, nullable=False)  # The actual generated code
    code_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for change detection
    file_size_bytes = Column(Integer, nullable=False)
    line_count = Column(Integer, nullable=False)
    
    # Generation metadata
    template_used = Column(String(100), nullable=True)
    template_version = Column(String(50), nullable=True)
    generation_model = Column(String(100), nullable=True)  # AI model used if applicable
    generation_parameters = Column(JSONB, nullable=True)
    
    # Code analysis
    language = Column(String(50), nullable=False, index=True)  # python, sql, typescript, etc.
    syntax_valid = Column(Boolean, nullable=True)
    complexity_metrics = Column(JSONB, nullable=True)  # Cyclomatic complexity, etc.
    code_quality_metrics = Column(JSONB, nullable=True)
    
    # Dependencies and imports
    dependencies = Column(JSONB, nullable=True)  # Required dependencies/imports
    external_dependencies = Column(JSONB, nullable=True)  # Third-party packages needed
    
    # Usage and access
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Version control
    version = Column(Integer, default=1)
    is_latest_version = Column(Boolean, default=True, index=True)
    parent_file_id = Column(UUID(as_uuid=True), nullable=True)  # For versioning
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    generation_job = relationship("CodeGenerationJob", back_populates="generated_files")
    
    def __repr__(self):
        return f"<GeneratedCodeFile(id='{self.id}', filename='{self.filename}')>"


class CodeTemplate(Base):
    """
    Code generation templates
    Stores templates used for generating code in different formats
    """
    __tablename__ = "code_templates"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_by_user_id = Column(String(255), nullable=False, index=True)
    
    # Template metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)  # model, api, migration, etc.
    
    # Template configuration
    output_format = Column(String(50), nullable=False, index=True)  # sqlalchemy, django, sql, etc.
    target_language = Column(String(50), nullable=False, index=True)  # python, sql, typescript, etc.
    framework = Column(String(50), nullable=True, index=True)  # fastapi, django, express, etc.
    
    # Template content
    template_content = Column(Text, nullable=False)  # Jinja2 template content
    template_engine = Column(String(50), default="jinja2")
    template_version = Column(String(50), default="1.0")
    
    # Template configuration
    template_variables = Column(JSONB, nullable=True)  # Available template variables
    required_parameters = Column(JSONB, nullable=True)  # Required parameters
    optional_parameters = Column(JSONB, nullable=True)  # Optional parameters
    
    # Template properties
    is_public = Column(Boolean, default=False, index=True)
    is_official = Column(Boolean, default=False, index=True)  # Official SchemaSage template
    is_active = Column(Boolean, default=True, index=True)
    
    # Quality and validation
    validation_schema = Column(JSONB, nullable=True)  # Schema for validating generated code
    example_output = Column(Text, nullable=True)  # Example of generated code
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Percentage of successful generations
    average_generation_time_ms = Column(Integer, nullable=True)
    
    # Ratings and feedback
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Dependencies
    required_dependencies = Column(JSONB, nullable=True)  # Dependencies for generated code
    template_dependencies = Column(JSONB, nullable=True)  # Dependencies for the template itself
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<CodeTemplate(id='{self.id}', name='{self.name}', format='{self.output_format}')>"


class CodeGenerationUsageStatistics(Base):
    """
    Track usage statistics for code generation service
    """
    __tablename__ = "code_generation_usage_statistics"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    
    # Usage counters
    generation_jobs_created = Column(Integer, default=0)
    generation_jobs_completed = Column(Integer, default=0)
    generation_jobs_failed = Column(Integer, default=0)
    files_generated = Column(Integer, default=0)
    total_lines_generated = Column(Integer, default=0)
    
    # Format breakdown
    sqlalchemy_generations = Column(Integer, default=0)
    django_generations = Column(Integer, default=0)
    sql_generations = Column(Integer, default=0)
    typescript_generations = Column(Integer, default=0)
    other_format_generations = Column(Integer, default=0)
    
    # Performance metrics
    total_generation_time_ms = Column(Integer, default=0)
    average_generation_time_ms = Column(Integer, default=0)
    fastest_generation_time_ms = Column(Integer, nullable=True)
    slowest_generation_time_ms = Column(Integer, nullable=True)
    
    # Quality metrics
    average_code_quality_score = Column(Float, default=0.0)
    average_complexity_score = Column(Float, default=0.0)
    successful_compilations = Column(Integer, default=0)
    
    # Template usage
    templates_used = Column(JSONB, nullable=True)  # Template usage breakdown
    custom_templates_created = Column(Integer, default=0)
    
    # Downloads and exports
    files_downloaded = Column(Integer, default=0)
    zip_exports = Column(Integer, default=0)
    
    # Usage details as JSONB
    usage_details = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<CodeGenerationUsageStatistics(user_id='{self.user_id}', date='{self.date}')>"


class CodeQualityMetrics(Base):
    """
    Code quality metrics and analysis results
    """
    __tablename__ = "code_quality_metrics"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    generated_file_id = Column(UUID(as_uuid=True), ForeignKey('generated_code_files.id'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Analysis metadata
    analysis_tool = Column(String(100), nullable=False)  # pylint, eslint, sonarqube, etc.
    analysis_version = Column(String(50), nullable=True)
    analysis_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Quality scores (0.0 - 1.0)
    overall_quality_score = Column(Float, nullable=False)
    maintainability_score = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    
    # Complexity metrics
    cyclomatic_complexity = Column(Integer, nullable=True)
    cognitive_complexity = Column(Integer, nullable=True)
    lines_of_code = Column(Integer, nullable=False)
    
    # Issues and violations
    critical_issues = Column(Integer, default=0)
    major_issues = Column(Integer, default=0)
    minor_issues = Column(Integer, default=0)
    info_issues = Column(Integer, default=0)
    
    # Detailed analysis results
    issues_breakdown = Column(JSONB, nullable=True)  # Detailed issue list
    metrics_details = Column(JSONB, nullable=True)  # Detailed metrics
    recommendations = Column(JSONB, nullable=True)  # Improvement recommendations
    
    # Code coverage (for test files)
    test_coverage_percentage = Column(Float, nullable=True)
    lines_covered = Column(Integer, nullable=True)
    lines_not_covered = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<CodeQualityMetrics(id='{self.id}', score={self.overall_quality_score})>"


class UserCodePreferences(Base):
    """
    User preferences for code generation
    """
    __tablename__ = "user_code_preferences"
    
    # Primary key
    user_id = Column(String(255), primary_key=True)
    
    # Default generation preferences
    preferred_output_format = Column(String(50), default="sqlalchemy")
    preferred_language = Column(String(50), default="python")
    preferred_framework = Column(String(50), nullable=True)
    
    # Code style preferences
    code_style = Column(String(50), default="pep8")  # pep8, google, airbnb, etc.
    naming_convention = Column(String(50), default="snake_case")  # snake_case, camelCase, PascalCase
    indentation_type = Column(String(10), default="spaces")  # spaces, tabs
    indentation_size = Column(Integer, default=4)
    
    # Generation preferences
    include_type_hints = Column(Boolean, default=True)
    include_docstrings = Column(Boolean, default=True)
    include_comments = Column(Boolean, default=True)
    include_examples = Column(Boolean, default=False)
    include_tests = Column(Boolean, default=False)
    
    # Advanced preferences
    generate_migrations = Column(Boolean, default=True)
    generate_validators = Column(Boolean, default=True)
    generate_serializers = Column(Boolean, default=True)
    use_dataclasses = Column(Boolean, default=False)
    use_async_code = Column(Boolean, default=True)
    
    # Template preferences
    preferred_templates = Column(JSONB, nullable=True)  # List of preferred template IDs
    custom_variables = Column(JSONB, nullable=True)  # User-defined template variables
    
    # Output preferences
    file_organization = Column(String(50), default="single_file")  # single_file, multiple_files, modular
    export_format = Column(String(50), default="zip")  # zip, tar, individual_files
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserCodePreferences(user_id='{self.user_id}', format='{self.preferred_output_format}')>"