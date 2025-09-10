"""
Pydantic models for Cloud Migration API endpoints
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class MigrationStrategy(str, Enum):
    """Migration strategy options"""
    LIFT_AND_SHIFT = "lift_and_shift"
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    HYBRID = "hybrid"


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class MigrationComplexity(str, Enum):
    """Migration complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class CloudMigrationRequest(BaseModel):
    """Request model for cloud migration operations"""
    source_connection_id: str = Field(..., description="Source database connection ID")
    target_cloud_provider: CloudProvider = Field(..., description="Target cloud provider")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Migration requirements and constraints")
    migration_strategy: Optional[MigrationStrategy] = Field(None, description="Preferred migration strategy")
    target_region: Optional[str] = Field(None, description="Target cloud region")
    performance_requirements: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Performance requirements")
    compliance_requirements: Optional[List[str]] = Field(default_factory=list, description="Compliance requirements (e.g., HIPAA, PCI-DSS)")
    budget_constraints: Optional[Dict[str, float]] = Field(default_factory=dict, description="Budget constraints")


class CloudAssessmentResponse(BaseModel):
    """Response model for cloud readiness assessment"""
    overall_score: float = Field(..., description="Overall readiness score (0-100)")
    dimension_scores: Dict[str, float] = Field(..., description="Scores for each assessment dimension")
    risk_level: str = Field(..., description="Overall risk level (low, medium, high)")
    blockers: List[str] = Field(default_factory=list, description="Migration blockers")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    estimated_complexity: MigrationComplexity = Field(..., description="Estimated migration complexity")
    cloud_provider_specific: Dict[str, Any] = Field(default_factory=dict, description="Cloud provider specific information")


class MigrationPhase(BaseModel):
    """Individual migration phase details"""
    phase_number: int = Field(..., description="Phase sequence number")
    name: str = Field(..., description="Phase name")
    description: str = Field(..., description="Phase description")
    duration_days: int = Field(..., description="Estimated duration in days")
    tasks: List[str] = Field(default_factory=list, description="Tasks in this phase")


class MigrationRisk(BaseModel):
    """Migration risk details"""
    type: str = Field(..., description="Risk type")
    severity: str = Field(..., description="Risk severity level")
    description: str = Field(..., description="Risk description")
    mitigation: str = Field(..., description="Risk mitigation strategy")


class MigrationPlanResponse(BaseModel):
    """Response model for migration plan"""
    migration_id: str = Field(..., description="Unique migration identifier")
    strategy: MigrationStrategy = Field(..., description="Selected migration strategy")
    complexity: MigrationComplexity = Field(..., description="Migration complexity")
    estimated_duration_days: int = Field(..., description="Total estimated duration in days")
    estimated_cost: float = Field(..., description="Estimated migration cost")
    phases: List[MigrationPhase] = Field(default_factory=list, description="Migration phases")
    risks: List[MigrationRisk] = Field(default_factory=list, description="Identified risks")
    rollback_plan: Dict[str, Any] = Field(default_factory=dict, description="Rollback plan details")
    success_criteria: List[str] = Field(default_factory=list, description="Success criteria")
    target_configuration: Dict[str, Any] = Field(default_factory=dict, description="Target environment configuration")
    readiness_score: float = Field(..., description="Overall readiness score")


class TargetEnvironmentSetup(BaseModel):
    """Target environment setup configuration"""
    cloud_provider: CloudProvider = Field(..., description="Cloud provider")
    region: str = Field(..., description="Target region")
    database_service: str = Field(..., description="Database service type")
    instance_type: str = Field(..., description="Instance type/size")
    storage_type: str = Field(default="ssd", description="Storage type")
    storage_size_gb: int = Field(..., description="Storage size in GB")
    backup_retention_days: int = Field(default=7, description="Backup retention period")
    multi_az: bool = Field(default=True, description="Multi-AZ deployment")
    encryption_enabled: bool = Field(default=True, description="Encryption at rest")
    vpc_configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="VPC/Network configuration")
    security_groups: Optional[List[str]] = Field(default_factory=list, description="Security group IDs")
    tags: Optional[Dict[str, str]] = Field(default_factory=dict, description="Resource tags")


class MigrationProgress(BaseModel):
    """Migration progress tracking"""
    migration_id: str = Field(..., description="Migration identifier")
    status: str = Field(..., description="Current status")
    current_phase: str = Field(..., description="Current migration phase")
    progress_percentage: float = Field(..., description="Overall progress percentage")
    estimated_time_remaining_minutes: int = Field(..., description="Estimated time remaining")
    tables_completed: int = Field(default=0, description="Number of tables completed")
    tables_total: int = Field(default=0, description="Total number of tables")
    rows_migrated: int = Field(default=0, description="Number of rows migrated")
    current_operation: str = Field(default="", description="Current operation description")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    issues: List[str] = Field(default_factory=list, description="Issues encountered")


class CostOptimizationRequest(BaseModel):
    """Cost optimization request"""
    connection_id: str = Field(..., description="Database connection ID")
    optimization_goals: List[str] = Field(default_factory=list, description="Optimization goals")
    risk_tolerance: str = Field(default="medium", description="Risk tolerance level")
    performance_requirements: Dict[str, Any] = Field(default_factory=dict, description="Performance requirements")
    availability_requirements: Dict[str, Any] = Field(default_factory=dict, description="Availability requirements")


class CostOptimizationResponse(BaseModel):
    """Cost optimization response"""
    connection_id: str = Field(..., description="Database connection ID")
    current_monthly_cost: float = Field(..., description="Current monthly cost")
    optimized_monthly_cost: float = Field(..., description="Optimized monthly cost")
    potential_savings: float = Field(..., description="Potential monthly savings")
    savings_percentage: float = Field(..., description="Savings percentage")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Optimization recommendations")
    implementation_effort: str = Field(..., description="Implementation effort level")
    risk_assessment: str = Field(..., description="Risk assessment of changes")


class MigrationReport(BaseModel):
    """Comprehensive migration report"""
    migration_id: str = Field(..., description="Migration identifier")
    migration_summary: Dict[str, Any] = Field(default_factory=dict, description="Migration summary")
    data_migration_stats: Dict[str, Any] = Field(default_factory=dict, description="Data migration statistics")
    performance_comparison: Dict[str, Any] = Field(default_factory=dict, description="Performance comparison")
    cost_analysis: Dict[str, Any] = Field(default_factory=dict, description="Cost analysis")
    recommendations: List[str] = Field(default_factory=list, description="Post-migration recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")


class DatabaseConnection(BaseModel):
    """Database connection configuration"""
    connection_id: str = Field(..., description="Unique connection identifier")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password", min_length=1)
    db_type: str = Field(..., description="Database type")
    cloud_provider: Optional[CloudProvider] = Field(None, description="Cloud provider")
    ssl_enabled: bool = Field(default=False, description="SSL enabled")
    connection_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional connection parameters")


class DatabaseMetadata(BaseModel):
    """Database metadata information"""
    database_type: str = Field(..., description="Database type")
    database_name: str = Field(..., description="Database name")
    cloud_provider: str = Field(..., description="Cloud provider")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Table information")
    views: List[str] = Field(default_factory=list, description="View names")
    indexes: List[Dict[str, Any]] = Field(default_factory=list, description="Index information")
    stored_procedures: List[str] = Field(default_factory=list, description="Stored procedure names")
    functions: List[str] = Field(default_factory=list, description="Function names")
    triggers: List[str] = Field(default_factory=list, description="Trigger names")
    sequences: List[str] = Field(default_factory=list, description="Sequence names")
    extensions: List[str] = Field(default_factory=list, description="Database extensions")
    constraints: List[Dict[str, Any]] = Field(default_factory=list, description="Constraint information")
    estimated_size_gb: float = Field(default=0.0, description="Estimated database size in GB")
    row_counts: Dict[str, int] = Field(default_factory=dict, description="Row counts per table")
    unsupported_features: List[str] = Field(default_factory=list, description="Unsupported features for cloud migration")


class CloudProviderInfo(BaseModel):
    """Cloud provider information"""
    provider_name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    database_services: List[Dict[str, Any]] = Field(default_factory=list, description="Available database services")
    regions: List[str] = Field(default_factory=list, description="Available regions")
    features: List[str] = Field(default_factory=list, description="Key features")
    pricing_model: str = Field(..., description="Pricing model description")
    support_level: str = Field(..., description="Support level")


class MigrationValidation(BaseModel):
    """Migration validation results"""
    validation_id: str = Field(..., description="Validation identifier")
    migration_id: str = Field(..., description="Associated migration ID")
    validation_type: str = Field(..., description="Type of validation")
    status: str = Field(..., description="Validation status")
    checks_performed: List[Dict[str, Any]] = Field(default_factory=list, description="Checks performed")
    issues_found: List[Dict[str, Any]] = Field(default_factory=list, description="Issues found")
    recommendations: List[str] = Field(default_factory=list, description="Validation recommendations")
    validation_score: float = Field(..., description="Overall validation score")
    performed_at: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")


# Response models for common operations
class OperationResponse(BaseModel):
    """Generic operation response"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
