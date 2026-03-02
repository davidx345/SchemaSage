"""
Schema Compatibility Models

Pydantic models for schema compatibility checker endpoint (POST /api/schema/compatibility).
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


class CompatibilityLevel(str, Enum):
    """Compatibility levels"""
    FULLY_COMPATIBLE = "fully_compatible"
    MOSTLY_COMPATIBLE = "mostly_compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"


class IssueSeverity(str, Enum):
    """Severity levels for compatibility issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Categories of compatibility issues"""
    DATA_TYPE = "data_type"
    CONSTRAINT = "constraint"
    INDEX = "index"
    TRIGGER = "trigger"
    STORED_PROCEDURE = "stored_procedure"
    VIEW = "view"
    FUNCTION = "function"
    SYNTAX = "syntax"
    FEATURE = "feature"
    ENCODING = "encoding"


class ColumnSchema(BaseModel):
    """Column schema definition"""
    
    name: str = Field(
        ...,
        description="Column name"
    )
    
    data_type: str = Field(
        ...,
        description="Column data type"
    )
    
    nullable: bool = Field(
        default=True,
        description="Whether column allows NULL"
    )
    
    default_value: Optional[str] = Field(
        default=None,
        description="Default value if any"
    )
    
    max_length: Optional[int] = Field(
        default=None,
        description="Maximum length for varchar/char types",
        ge=1
    )
    
    precision: Optional[int] = Field(
        default=None,
        description="Precision for numeric types",
        ge=1
    )
    
    scale: Optional[int] = Field(
        default=None,
        description="Scale for numeric types",
        ge=0
    )
    
    is_primary_key: bool = Field(
        default=False,
        description="Whether column is part of primary key"
    )
    
    is_foreign_key: bool = Field(
        default=False,
        description="Whether column is a foreign key"
    )


class TableSchema(BaseModel):
    """Table schema definition"""
    
    name: str = Field(
        ...,
        description="Table name"
    )
    
    columns: List[ColumnSchema] = Field(
        ...,
        description="List of columns in table"
    )
    
    indexes: List[str] = Field(
        default_factory=list,
        description="List of index names"
    )
    
    constraints: List[str] = Field(
        default_factory=list,
        description="List of constraint names"
    )


class CompatibilityRequest(BaseModel):
    """Request model for schema compatibility check"""
    
    source_db_type: DatabaseType = Field(
        ...,
        description="Source database type"
    )
    
    target_db_type: DatabaseType = Field(
        ...,
        description="Target database type"
    )
    
    schema: Dict[str, Any] = Field(
        ...,
        description="Source schema definition (tables, columns, types)"
    )
    
    check_stored_procedures: bool = Field(
        default=True,
        description="Whether to check stored procedures compatibility"
    )
    
    check_triggers: bool = Field(
        default=True,
        description="Whether to check triggers compatibility"
    )
    
    check_views: bool = Field(
        default=True,
        description="Whether to check views compatibility"
    )
    
    @validator('target_db_type')
    def validate_different_databases(cls, v, values):
        """Ensure source and target are different"""
        if 'source_db_type' in values and v == values['source_db_type']:
            raise ValueError("Source and target databases must be different")
        return v


class CompatibilityIssue(BaseModel):
    """Individual compatibility issue"""
    
    category: IssueCategory = Field(
        ...,
        description="Issue category"
    )
    
    severity: IssueSeverity = Field(
        ...,
        description="Issue severity"
    )
    
    object_type: str = Field(
        ...,
        description="Type of object affected (table, column, etc.)"
    )
    
    object_name: str = Field(
        ...,
        description="Name of affected object"
    )
    
    description: str = Field(
        ...,
        description="Detailed issue description"
    )
    
    source_definition: Optional[str] = Field(
        default=None,
        description="Source database definition"
    )
    
    target_equivalent: Optional[str] = Field(
        default=None,
        description="Suggested target database equivalent"
    )
    
    workaround: Optional[str] = Field(
        default=None,
        description="Suggested workaround or solution"
    )
    
    is_blocker: bool = Field(
        default=False,
        description="Whether this issue blocks migration"
    )


class MigrationRecommendation(BaseModel):
    """Migration recommendation"""
    
    priority: str = Field(
        ...,
        description="Priority level (high, medium, low)"
    )
    
    title: str = Field(
        ...,
        description="Recommendation title"
    )
    
    description: str = Field(
        ...,
        description="Detailed recommendation"
    )
    
    effort_estimate: str = Field(
        ...,
        description="Estimated effort (e.g., '2 days', '1 week')"
    )


class CompatibilitySummary(BaseModel):
    """Summary of compatibility check"""
    
    overall_compatibility: CompatibilityLevel = Field(
        ...,
        description="Overall compatibility level"
    )
    
    total_issues: int = Field(
        default=0,
        description="Total number of issues found",
        ge=0
    )
    
    critical_issues: int = Field(
        default=0,
        description="Number of critical issues",
        ge=0
    )
    
    error_issues: int = Field(
        default=0,
        description="Number of error-level issues",
        ge=0
    )
    
    warning_issues: int = Field(
        default=0,
        description="Number of warnings",
        ge=0
    )
    
    info_issues: int = Field(
        default=0,
        description="Number of informational issues",
        ge=0
    )
    
    blockers_count: int = Field(
        default=0,
        description="Number of migration blockers",
        ge=0
    )
    
    compatibility_percentage: float = Field(
        ...,
        description="Percentage of compatible features (0-100)",
        ge=0.0,
        le=100.0
    )


class CompatibilityResponse(BaseModel):
    """Response model for schema compatibility check"""
    
    success: bool = Field(
        default=True,
        description="Whether compatibility check succeeded"
    )
    
    summary: CompatibilitySummary = Field(
        ...,
        description="High-level compatibility summary"
    )
    
    issues: List[CompatibilityIssue] = Field(
        default_factory=list,
        description="List of compatibility issues"
    )
    
    recommendations: List[MigrationRecommendation] = Field(
        default_factory=list,
        description="Migration recommendations"
    )
    
    supported_features: List[str] = Field(
        default_factory=list,
        description="List of fully supported features"
    )
    
    unsupported_features: List[str] = Field(
        default_factory=list,
        description="List of unsupported features"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Check timestamp"
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
