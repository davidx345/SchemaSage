"""
Data Type Mapping Models

Pydantic models for data type mapper endpoint (POST /api/migration/map-types).
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
    SQLITE = "sqlite"


class MappingConfidence(str, Enum):
    """Confidence levels for type mapping"""
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class DataLossRisk(str, Enum):
    """Risk levels for potential data loss"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WarningLevel(str, Enum):
    """Warning severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SourceDataType(BaseModel):
    """Source database data type definition"""
    
    type_name: str = Field(
        ...,
        description="Source data type name"
    )
    
    max_length: Optional[int] = Field(
        default=None,
        description="Maximum length for string types",
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
    
    is_unsigned: bool = Field(
        default=False,
        description="Whether numeric type is unsigned"
    )
    
    collation: Optional[str] = Field(
        default=None,
        description="Character collation if applicable"
    )
    
    additional_properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional type-specific properties"
    )


class TypeMappingRequest(BaseModel):
    """Request model for data type mapping"""
    
    source_db_type: DatabaseType = Field(
        ...,
        description="Source database type"
    )
    
    target_db_type: DatabaseType = Field(
        ...,
        description="Target database type"
    )
    
    source_types: List[SourceDataType] = Field(
        ...,
        description="List of source data types to map",
        min_items=1
    )
    
    preserve_precision: bool = Field(
        default=True,
        description="Whether to preserve numeric precision"
    )
    
    allow_lossy_conversion: bool = Field(
        default=False,
        description="Whether to allow lossy type conversions"
    )
    
    @validator('target_db_type')
    def validate_different_databases(cls, v, values):
        """Ensure source and target are different"""
        if 'source_db_type' in values and v == values['source_db_type']:
            raise ValueError("Source and target databases must be different")
        return v


class TargetTypeMapping(BaseModel):
    """Target database type mapping"""
    
    type_name: str = Field(
        ...,
        description="Target data type name"
    )
    
    max_length: Optional[int] = Field(
        default=None,
        description="Maximum length in target type",
        ge=1
    )
    
    precision: Optional[int] = Field(
        default=None,
        description="Precision in target type",
        ge=1
    )
    
    scale: Optional[int] = Field(
        default=None,
        description="Scale in target type",
        ge=0
    )
    
    additional_properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional target type properties"
    )
    
    sql_definition: str = Field(
        ...,
        description="Complete SQL type definition for target"
    )


class TypeMappingWarning(BaseModel):
    """Warning about type mapping"""
    
    level: WarningLevel = Field(
        ...,
        description="Warning severity level"
    )
    
    category: str = Field(
        ...,
        description="Warning category (e.g., 'precision_loss', 'range_mismatch')"
    )
    
    message: str = Field(
        ...,
        description="Warning message"
    )
    
    recommendation: Optional[str] = Field(
        default=None,
        description="Recommendation to address warning"
    )
    
    example: Optional[str] = Field(
        default=None,
        description="Example demonstrating the issue"
    )


class DataTypeMapping(BaseModel):
    """Complete mapping for a single data type"""
    
    source_type: SourceDataType = Field(
        ...,
        description="Source data type"
    )
    
    target_type: TargetTypeMapping = Field(
        ...,
        description="Mapped target data type"
    )
    
    mapping_confidence: MappingConfidence = Field(
        ...,
        description="Confidence level of the mapping"
    )
    
    data_loss_risk: DataLossRisk = Field(
        ...,
        description="Risk of data loss during conversion"
    )
    
    is_direct_mapping: bool = Field(
        default=True,
        description="Whether mapping is direct (1:1)"
    )
    
    requires_conversion: bool = Field(
        default=False,
        description="Whether data conversion is required"
    )
    
    conversion_function: Optional[str] = Field(
        default=None,
        description="SQL function for data conversion if needed"
    )
    
    warnings: List[TypeMappingWarning] = Field(
        default_factory=list,
        description="Warnings about this mapping"
    )
    
    notes: List[str] = Field(
        default_factory=list,
        description="Additional notes about the mapping"
    )


class MappingSummary(BaseModel):
    """Summary of type mapping results"""
    
    total_types: int = Field(
        ...,
        description="Total number of types mapped",
        ge=1
    )
    
    exact_mappings: int = Field(
        default=0,
        description="Number of exact mappings",
        ge=0
    )
    
    approximate_mappings: int = Field(
        default=0,
        description="Number of approximate mappings",
        ge=0
    )
    
    lossy_mappings: int = Field(
        default=0,
        description="Number of lossy mappings",
        ge=0
    )
    
    critical_warnings: int = Field(
        default=0,
        description="Number of critical warnings",
        ge=0
    )
    
    error_warnings: int = Field(
        default=0,
        description="Number of error-level warnings",
        ge=0
    )
    
    overall_confidence: MappingConfidence = Field(
        ...,
        description="Overall mapping confidence"
    )
    
    overall_data_loss_risk: DataLossRisk = Field(
        ...,
        description="Overall data loss risk assessment"
    )


class TypeMappingResponse(BaseModel):
    """Response model for data type mapping"""
    
    success: bool = Field(
        default=True,
        description="Whether mapping succeeded"
    )
    
    summary: MappingSummary = Field(
        ...,
        description="High-level mapping summary"
    )
    
    mappings: List[DataTypeMapping] = Field(
        ...,
        description="Detailed type mappings"
    )
    
    general_recommendations: List[str] = Field(
        default_factory=list,
        description="General recommendations for migration"
    )
    
    unsupported_types: List[str] = Field(
        default_factory=list,
        description="Types that couldn't be mapped"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Mapping timestamp"
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
