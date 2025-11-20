"""
Models for migration rollback planner endpoint.
Creates detailed rollback plans for migration operations.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RollbackComplexity(str, Enum):
    """Complexity level of rollback operation"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"
    IRREVERSIBLE = "irreversible"


class RollbackRisk(str, Enum):
    """Risk level of rollback operation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataRecoveryMethod(str, Enum):
    """Method for recovering data during rollback"""
    BACKUP_RESTORE = "backup_restore"
    REVERSE_MIGRATION = "reverse_migration"
    SNAPSHOT_REVERT = "snapshot_revert"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    MANUAL_RECOVERY = "manual_recovery"
    POINT_IN_TIME_RECOVERY = "point_in_time_recovery"


class RollbackPhase(str, Enum):
    """Phase of rollback operation"""
    PREPARATION = "preparation"
    TRAFFIC_REDIRECT = "traffic_redirect"
    DATA_VALIDATION = "data_validation"
    SCHEMA_ROLLBACK = "schema_rollback"
    DATA_ROLLBACK = "data_rollback"
    VERIFICATION = "verification"
    CLEANUP = "cleanup"
    COMPLETION = "completion"


class MigrationState(BaseModel):
    """Current state of migration for rollback planning"""
    migration_id: str = Field(..., description="Migration identifier")
    current_phase: str = Field(..., description="Current migration phase")
    tables_migrated: List[str] = Field(..., description="List of tables already migrated")
    tables_pending: List[str] = Field(..., description="List of tables not yet migrated")
    data_migrated_gb: float = Field(..., ge=0.0, description="Amount of data migrated in GB")
    schema_changes_applied: List[str] = Field(..., description="Schema changes already applied")
    has_backup: bool = Field(..., description="Whether backup exists")
    backup_timestamp: Optional[datetime] = Field(None, description="When backup was created")


class RollbackRequest(BaseModel):
    """Request to generate rollback plan"""
    migration_id: str = Field(..., description="Unique identifier for the migration")
    migration_state: MigrationState = Field(..., description="Current state of migration")
    source_db_type: str = Field(..., description="Source database type")
    target_db_type: str = Field(..., description="Target database type")
    include_data_recovery: bool = Field(default=True, description="Include data recovery steps")
    max_downtime_minutes: Optional[int] = Field(
        None,
        ge=0,
        le=1440,
        description="Maximum acceptable downtime in minutes"
    )
    preserve_target_changes: bool = Field(
        default=False,
        description="Whether to preserve changes made in target"
    )


class RollbackStep(BaseModel):
    """Individual step in rollback plan"""
    step_number: int = Field(..., ge=1, description="Step sequence number")
    phase: RollbackPhase = Field(..., description="Rollback phase")
    action: str = Field(..., description="Action to perform")
    description: str = Field(..., description="Detailed description of the step")
    sql_commands: Optional[List[str]] = Field(None, description="SQL commands to execute")
    estimated_duration_minutes: int = Field(..., ge=0, description="Estimated duration")
    risk_level: RollbackRisk = Field(..., description="Risk level of this step")
    reversible: bool = Field(..., description="Whether this step can be undone")
    validation_query: Optional[str] = Field(None, description="Query to validate step completion")
    dependencies: List[int] = Field(default_factory=list, description="Step numbers that must complete first")
    warning: Optional[str] = Field(None, description="Warning or caution for this step")


class DataRecoveryPlan(BaseModel):
    """Plan for recovering data during rollback"""
    method: DataRecoveryMethod = Field(..., description="Recovery method to use")
    source: str = Field(..., description="Source of recovery data (backup location, etc)")
    estimated_duration_minutes: int = Field(..., ge=0, description="Estimated recovery time")
    data_to_recover_gb: float = Field(..., ge=0.0, description="Amount of data to recover")
    recovery_steps: List[str] = Field(..., description="Detailed recovery steps")
    validation_checks: List[str] = Field(..., description="Checks to validate recovery")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors for this method")


class RollbackValidation(BaseModel):
    """Validation checks for rollback completion"""
    check_name: str = Field(..., description="Name of validation check")
    query: str = Field(..., description="Query to perform check")
    expected_result: str = Field(..., description="Expected result")
    critical: bool = Field(..., description="Whether this check is critical")
    description: str = Field(..., description="Description of what is being validated")


class RollbackRiskAssessment(BaseModel):
    """Risk assessment for rollback operation"""
    overall_risk: RollbackRisk = Field(..., description="Overall rollback risk level")
    data_loss_risk: RollbackRisk = Field(..., description="Risk of data loss")
    downtime_risk: RollbackRisk = Field(..., description="Risk of extended downtime")
    complexity_risk: RollbackRisk = Field(..., description="Risk due to complexity")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    mitigation_strategies: List[str] = Field(..., description="Strategies to mitigate risks")
    irreversible_changes: List[str] = Field(default_factory=list, description="Changes that cannot be rolled back")


class RollbackPrerequisite(BaseModel):
    """Prerequisites for rollback execution"""
    requirement: str = Field(..., description="Required prerequisite")
    description: str = Field(..., description="Detailed description")
    critical: bool = Field(..., description="Whether this is critical")
    validation_command: Optional[str] = Field(None, description="Command to validate prerequisite")


class RollbackResourceRequirement(BaseModel):
    """Resources required for rollback"""
    storage_required_gb: float = Field(..., ge=0.0, description="Storage space required")
    memory_required_gb: float = Field(..., ge=0.0, description="Memory required")
    cpu_cores: int = Field(..., ge=1, description="CPU cores recommended")
    network_bandwidth_mbps: Optional[float] = Field(None, ge=0.0, description="Network bandwidth needed")
    personnel_required: int = Field(..., ge=1, description="Number of personnel required")
    specialist_skills: List[str] = Field(default_factory=list, description="Required specialist skills")


class RollbackTimeline(BaseModel):
    """Timeline for rollback execution"""
    phase: RollbackPhase = Field(..., description="Rollback phase")
    start_offset_minutes: int = Field(..., ge=0, description="Minutes from rollback start")
    duration_minutes: int = Field(..., ge=0, description="Phase duration")
    critical_path: bool = Field(..., description="Whether on critical path")
    description: str = Field(..., description="Phase description")


class RollbackSummary(BaseModel):
    """Summary of rollback plan"""
    migration_id: str = Field(..., description="Migration identifier")
    plan_created_at: datetime = Field(..., description="When plan was created")
    complexity: RollbackComplexity = Field(..., description="Overall complexity")
    estimated_total_duration_minutes: int = Field(..., ge=0, description="Total estimated duration")
    estimated_downtime_minutes: int = Field(..., ge=0, description="Estimated downtime")
    total_steps: int = Field(..., ge=0, description="Total number of steps")
    critical_steps: int = Field(..., ge=0, description="Number of critical steps")
    can_rollback: bool = Field(..., description="Whether rollback is feasible")
    recommendation: str = Field(..., description="Recommendation about rollback")


class RollbackResponse(BaseModel):
    """Response from rollback planner endpoint"""
    summary: RollbackSummary = Field(..., description="Rollback plan summary")
    risk_assessment: RollbackRiskAssessment = Field(..., description="Risk assessment")
    prerequisites: List[RollbackPrerequisite] = Field(..., description="Prerequisites for rollback")
    steps: List[RollbackStep] = Field(..., description="Ordered rollback steps")
    timeline: List[RollbackTimeline] = Field(..., description="Rollback timeline by phase")
    data_recovery: Optional[DataRecoveryPlan] = Field(None, description="Data recovery plan if applicable")
    validations: List[RollbackValidation] = Field(..., description="Validation checks")
    resource_requirements: RollbackResourceRequirement = Field(..., description="Required resources")
    warnings: List[str] = Field(default_factory=list, description="Important warnings")
    recommendations: List[str] = Field(default_factory=list, description="Best practices and recommendations")
    emergency_contacts: List[str] = Field(
        default_factory=list,
        description="Emergency contacts or escalation procedures"
    )
