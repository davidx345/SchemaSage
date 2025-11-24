"""
Universal Migration Center Models.
Pydantic models for cross-database migration planning, execution, and rollback.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    MSSQL = "mssql"
    ORACLE = "oracle"
    REDIS = "redis"

class MigrationType(str, Enum):
    """Migration types."""
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"
    SCHEMA_AND_DATA = "schema_and_data"

class MigrationStatus(str, Enum):
    """Migration execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CloudProvider(str, Enum):
    """Cloud service providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

# ===== MIGRATION PLANNING MODELS =====

class MigrationPlanRequest(BaseModel):
    """Request for migration planning."""
    source_url: str = Field(description="Source database connection string")
    target_url: str = Field(description="Target database connection string")
    migration_type: MigrationType = Field(description="Type of migration")
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Migration options (preserve_relationships, batch_size, etc.)"
    )

class SourceAnalysis(BaseModel):
    """Source database analysis."""
    database_type: str = Field(description="Database type and version")
    total_tables: int = Field(description="Number of tables")
    total_records: int = Field(description="Total record count")
    total_size_gb: float = Field(description="Database size in GB")
    schemas: List[str] = Field(description="List of schemas")
    relationships: List[Dict[str, Any]] = Field(description="Foreign key relationships")

class TargetAnalysis(BaseModel):
    """Target database analysis."""
    database_type: str = Field(description="Database type and version")
    available_space_gb: float = Field(description="Available storage space")
    compatibility_score: int = Field(ge=0, le=100, description="Compatibility score")
    required_transformations: List[str] = Field(description="Required data transformations")

class MigrationStep(BaseModel):
    """Individual migration step."""
    step_number: int = Field(description="Step sequence number")
    description: str = Field(description="Step description")
    estimated_duration: str = Field(description="Estimated time to complete")
    dependencies: List[int] = Field(description="Dependent step numbers")
    risk_level: RiskLevel = Field(description="Risk level for this step")

class MigrationPlan(BaseModel):
    """Comprehensive migration plan."""
    estimated_duration: str = Field(description="Total estimated duration")
    total_steps: int = Field(description="Number of migration steps")
    steps: List[MigrationStep] = Field(description="Ordered migration steps")
    compatibility_issues: List[str] = Field(description="Potential compatibility issues")
    data_transformations: List[Dict[str, str]] = Field(description="Required data transformations")
    rollback_available: bool = Field(description="Whether rollback is available")

class MigrationPlanData(BaseModel):
    """Migration plan response data."""
    migration_id: str = Field(description="Unique migration identifier")
    source_analysis: SourceAnalysis
    target_analysis: TargetAnalysis
    migration_plan: MigrationPlan
    cross_database_migration: bool = Field(description="Whether cross-database migration")
    migration_type: str = Field(description="Descriptive migration type (e.g., PostgreSQL → MongoDB)")

class MigrationPlanResponse(BaseModel):
    """Response from migration planning."""
    success: bool
    data: Optional[MigrationPlanData] = None
    error: Optional[str] = None

# ===== MIGRATION EXECUTION MODELS =====

class ExecutionOptions(BaseModel):
    """Migration execution options."""
    dry_run: bool = Field(default=False, description="Run in dry-run mode")
    stop_on_error: bool = Field(default=False, description="Stop on first error")
    verify_after_migration: bool = Field(default=True, description="Verify data after migration")
    create_rollback_point: bool = Field(default=True, description="Create rollback checkpoint")

class MigrationExecuteRequest(BaseModel):
    """Request for migration execution."""
    migration_id: str = Field(description="Migration plan ID")
    execution_options: ExecutionOptions = Field(default_factory=ExecutionOptions)

class ProgressInfo(BaseModel):
    """Migration progress information."""
    percentage: float = Field(ge=0, le=100, description="Progress percentage")
    current_step: str = Field(description="Current step description")
    records_processed: int = Field(description="Records processed so far")
    total_records: int = Field(description="Total records to process")
    estimated_remaining: str = Field(description="Estimated time remaining")

class PerformanceMetrics(BaseModel):
    """Migration performance metrics."""
    records_per_second: int = Field(description="Processing throughput")
    error_count: int = Field(description="Number of errors encountered")
    warning_count: int = Field(description="Number of warnings")

class MigrationExecutionData(BaseModel):
    """Migration execution response data."""
    execution_id: str = Field(description="Execution identifier")
    status: MigrationStatus = Field(description="Current execution status")
    progress: ProgressInfo
    performance_metrics: PerformanceMetrics
    logs: List[str] = Field(description="Recent log entries")

class MigrationExecuteResponse(BaseModel):
    """Response from migration execution."""
    success: bool
    data: Optional[MigrationExecutionData] = None
    error: Optional[str] = None

# ===== MULTI-CLOUD COMPARISON MODELS =====

class MultiCloudCompareRequest(BaseModel):
    """Request for multi-cloud comparison."""
    database_engine: str = Field(description="Database engine (postgresql, mysql, etc.)")
    database_version: str = Field(description="Database version")
    vcpu_count: int = Field(description="Number of vCPUs")
    memory_gb: int = Field(description="Memory in GB")
    storage_gb: int = Field(description="Storage in GB")
    multi_az: bool = Field(default=False, description="Multi-AZ deployment")
    region_preference: str = Field(description="Preferred region (us-east, eu-west, etc.)")

class CloudRecommendation(BaseModel):
    """Cloud provider recommendation."""
    provider: CloudProvider = Field(description="Cloud provider")
    service_name: str = Field(description="Service name (RDS, Azure SQL, Cloud SQL)")
    instance_type: str = Field(description="Instance type/SKU")
    monthly_cost: float = Field(description="Estimated monthly cost")
    vcpu_count: int = Field(description="vCPU count")
    memory_gb: int = Field(description="Memory in GB")
    storage_gb: int = Field(description="Storage in GB")
    features: List[str] = Field(description="Key features")
    pros: List[str] = Field(description="Advantages")
    cons: List[str] = Field(description="Disadvantages")
    performance_score: int = Field(ge=0, le=100, description="Performance score")
    reliability_score: int = Field(ge=0, le=100, description="Reliability score")

class BestValue(BaseModel):
    """Best value recommendation."""
    provider: CloudProvider
    reason: str = Field(description="Why this is best value")
    annual_savings_vs_aws: Optional[float] = None
    annual_savings_vs_azure: Optional[float] = None
    annual_savings_vs_gcp: Optional[float] = None

class MultiCloudCompareData(BaseModel):
    """Multi-cloud comparison response data."""
    recommendations: List[CloudRecommendation] = Field(description="Provider recommendations")
    best_value: BestValue = Field(description="Best value recommendation")

class MultiCloudCompareResponse(BaseModel):
    """Response from multi-cloud comparison."""
    success: bool
    data: Optional[MultiCloudCompareData] = None
    error: Optional[str] = None

# ===== PRE-MIGRATION ANALYSIS MODELS =====

class PreAnalysisRequest(BaseModel):
    """Request for pre-migration analysis."""
    source_database: str = Field(description="Source database type")
    source_version: str = Field(description="Source database version")
    target_database: str = Field(description="Target database type")
    target_version: str = Field(description="Target database version")
    connection_string: str = Field(description="Database connection string")

class BreakingChange(BaseModel):
    """Breaking change information."""
    severity: RiskLevel = Field(description="Severity level")
    category: str = Field(description="Change category")
    description: str = Field(description="Change description")
    affected_objects: List[str] = Field(description="Affected database objects")
    migration_strategy: str = Field(description="Recommended migration strategy")
    estimated_effort_hours: int = Field(description="Estimated effort in hours")

class PerformanceImpact(BaseModel):
    """Performance impact analysis."""
    area: str = Field(description="Performance area affected")
    impact_type: str = Field(description="Type of impact (positive/negative/neutral)")
    magnitude: str = Field(description="Impact magnitude")
    details: str = Field(description="Detailed explanation")
    optimization_recommendations: List[str] = Field(description="Optimization suggestions")

class Dependency(BaseModel):
    """Migration dependency."""
    name: str = Field(description="Dependency name")
    type: str = Field(description="Dependency type")
    current_version: str = Field(description="Current version")
    required_version: str = Field(description="Required version for migration")
    upgrade_required: bool = Field(description="Whether upgrade is needed")
    upgrade_complexity: RiskLevel = Field(description="Upgrade complexity")

class PreAnalysisData(BaseModel):
    """Pre-migration analysis response data."""
    overall_risk: RiskLevel = Field(description="Overall migration risk")
    confidence_score: int = Field(ge=0, le=100, description="Analysis confidence")
    breaking_changes: List[BreakingChange] = Field(description="Breaking changes")
    performance_impact: List[PerformanceImpact] = Field(description="Performance impacts")
    dependencies: List[Dependency] = Field(description="Dependencies to check")
    estimated_effort_hours: int = Field(description="Total estimated effort")
    rollback_difficulty: str = Field(description="Rollback difficulty level")
    recommended_approach: str = Field(description="Recommended migration approach")

class PreAnalysisResponse(BaseModel):
    """Response from pre-migration analysis."""
    success: bool
    data: Optional[PreAnalysisData] = None
    error: Optional[str] = None

# ===== SMART ROLLBACK MODELS =====

class RollbackRequest(BaseModel):
    """Request for migration rollback."""
    migration_id: str = Field(description="Migration ID")
    execution_id: str = Field(description="Execution ID")
    rollback_strategy: str = Field(
        default="intelligent_reconstruction",
        description="Rollback strategy"
    )
    preserve_new_data: bool = Field(
        default=True,
        description="Preserve data created during migration"
    )

class RollbackStep(BaseModel):
    """Individual rollback step."""
    step_number: int = Field(description="Step sequence number")
    action: str = Field(description="Rollback action")
    target: str = Field(description="Target object")
    estimated_duration: str = Field(description="Estimated duration")
    risk_level: RiskLevel = Field(description="Risk level")

class RollbackPlan(BaseModel):
    """Rollback execution plan."""
    estimated_duration: str = Field(description="Total estimated duration")
    total_steps: int = Field(description="Number of rollback steps")
    steps: List[RollbackStep] = Field(description="Ordered rollback steps")
    data_preservation_strategy: str = Field(description="How new data is preserved")

class Checkpoint(BaseModel):
    """Rollback checkpoint."""
    checkpoint_id: str = Field(description="Checkpoint identifier")
    timestamp: datetime = Field(description="Checkpoint creation time")
    description: str = Field(description="Checkpoint description")
    size_gb: float = Field(description="Checkpoint size in GB")

class RollbackData(BaseModel):
    """Rollback response data."""
    rollback_id: str = Field(description="Rollback identifier")
    status: str = Field(description="Rollback status")
    rollback_plan: RollbackPlan
    checkpoints: List[Checkpoint] = Field(description="Available checkpoints")

class RollbackResponse(BaseModel):
    """Response from rollback planning."""
    success: bool
    data: Optional[RollbackData] = None
    error: Optional[str] = None

class RollbackExecuteData(BaseModel):
    """Rollback execution response data."""
    execution_id: str = Field(description="Rollback execution ID")
    status: MigrationStatus = Field(description="Current status")
    progress: ProgressInfo
    performance_metrics: PerformanceMetrics
    logs: List[str] = Field(description="Recent log entries")

class RollbackExecuteResponse(BaseModel):
    """Response from rollback execution."""
    success: bool
    data: Optional[RollbackExecuteData] = None
    error: Optional[str] = None
