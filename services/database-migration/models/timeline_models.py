"""
Migration Timeline Models

Pydantic models for migration timeline generator endpoint (POST /api/migration/timeline).
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    MONGODB = "mongodb"
    MARIADB = "mariadb"
    AURORA = "aurora"
    DYNAMODB = "dynamodb"


class MigrationComplexity(str, Enum):
    """Migration complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class RiskLevel(str, Enum):
    """Risk levels for migration phases"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PhaseStatus(str, Enum):
    """Status of migration phases"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TimelineRequest(BaseModel):
    """Request model for migration timeline generation"""
    
    source_db_type: DatabaseType = Field(
        ...,
        description="Source database type"
    )
    
    target_db_type: DatabaseType = Field(
        ...,
        description="Target database type"
    )
    
    data_volume_gb: float = Field(
        ...,
        description="Total data volume in GB",
        ge=0.001,
        le=1000000
    )
    
    num_tables: int = Field(
        ...,
        description="Number of tables to migrate",
        ge=1,
        le=100000
    )
    
    num_stored_procedures: int = Field(
        default=0,
        description="Number of stored procedures",
        ge=0
    )
    
    num_views: int = Field(
        default=0,
        description="Number of views",
        ge=0
    )
    
    num_triggers: int = Field(
        default=0,
        description="Number of triggers",
        ge=0
    )
    
    has_replication: bool = Field(
        default=False,
        description="Whether source has replication setup"
    )
    
    has_encryption: bool = Field(
        default=False,
        description="Whether data is encrypted"
    )
    
    complexity: Optional[MigrationComplexity] = Field(
        default=None,
        description="Override auto-calculated complexity"
    )
    
    team_size: int = Field(
        default=3,
        description="Size of migration team",
        ge=1,
        le=50
    )
    
    @validator('target_db_type')
    def validate_different_databases(cls, v, values):
        """Ensure source and target are different"""
        if 'source_db_type' in values and v == values['source_db_type']:
            raise ValueError("Source and target databases must be different")
        return v


class ResourceRequirement(BaseModel):
    """Resource requirements for migration"""
    
    category: str = Field(
        ...,
        description="Resource category (e.g., 'compute', 'storage')"
    )
    
    requirement: str = Field(
        ...,
        description="Detailed requirement description"
    )
    
    estimated_cost: Optional[float] = Field(
        default=None,
        description="Estimated cost in USD",
        ge=0
    )
    
    is_critical: bool = Field(
        default=False,
        description="Whether this resource is critical"
    )


class RiskItem(BaseModel):
    """Individual risk item"""
    
    risk_type: str = Field(
        ...,
        description="Type of risk (e.g., 'data_loss', 'downtime')"
    )
    
    level: RiskLevel = Field(
        ...,
        description="Risk severity level"
    )
    
    description: str = Field(
        ...,
        description="Detailed risk description"
    )
    
    mitigation: str = Field(
        ...,
        description="Recommended mitigation strategy"
    )
    
    probability: float = Field(
        ...,
        description="Probability of occurrence (0-1)",
        ge=0.0,
        le=1.0
    )


class MigrationPhase(BaseModel):
    """Single phase in migration timeline"""
    
    phase_number: int = Field(
        ...,
        description="Phase sequence number",
        ge=1
    )
    
    name: str = Field(
        ...,
        description="Phase name"
    )
    
    description: str = Field(
        ...,
        description="Detailed phase description"
    )
    
    duration_days: float = Field(
        ...,
        description="Estimated duration in days",
        ge=0.1
    )
    
    tasks: List[str] = Field(
        default_factory=list,
        description="List of tasks in this phase"
    )
    
    dependencies: List[int] = Field(
        default_factory=list,
        description="Phase numbers that must complete before this phase"
    )
    
    resource_requirements: List[ResourceRequirement] = Field(
        default_factory=list,
        description="Resources needed for this phase"
    )
    
    risks: List[RiskItem] = Field(
        default_factory=list,
        description="Risks associated with this phase"
    )
    
    status: PhaseStatus = Field(
        default=PhaseStatus.NOT_STARTED,
        description="Current status of the phase"
    )


class TimelineSummary(BaseModel):
    """Summary of migration timeline"""
    
    total_phases: int = Field(
        ...,
        description="Total number of phases",
        ge=1
    )
    
    total_duration_days: float = Field(
        ...,
        description="Total estimated duration in days",
        ge=0.1
    )
    
    total_duration_weeks: float = Field(
        ...,
        description="Total duration in weeks",
        ge=0.01
    )
    
    complexity_level: MigrationComplexity = Field(
        ...,
        description="Overall migration complexity"
    )
    
    overall_risk_level: RiskLevel = Field(
        ...,
        description="Overall risk assessment"
    )
    
    critical_risks_count: int = Field(
        default=0,
        description="Number of critical risks",
        ge=0
    )
    
    high_risks_count: int = Field(
        default=0,
        description="Number of high risks",
        ge=0
    )
    
    recommended_team_size: int = Field(
        ...,
        description="Recommended team size",
        ge=1
    )


class TimelineResponse(BaseModel):
    """Response model for migration timeline"""
    
    success: bool = Field(
        default=True,
        description="Whether timeline generation succeeded"
    )
    
    summary: TimelineSummary = Field(
        ...,
        description="High-level timeline summary"
    )
    
    phases: List[MigrationPhase] = Field(
        ...,
        description="Detailed migration phases"
    )
    
    resource_requirements: List[ResourceRequirement] = Field(
        default_factory=list,
        description="Overall resource requirements"
    )
    
    risks: List[RiskItem] = Field(
        default_factory=list,
        description="All identified risks"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="General recommendations for migration"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timeline generation timestamp"
    )


class ErrorResponse(BaseModel):
    """Error response model"""
    
    success: bool = Field(
        default=False,
        description="Always false for errors"
    )
    
    error: str = Field(
        ...,
        description="Error message"
    )
    
    details: Optional[str] = Field(
        default=None,
        description="Additional error details"
    )
