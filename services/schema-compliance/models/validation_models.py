"""
Models for data validation suite endpoint.
Validates data integrity, quality, and consistency.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ValidationType(str, Enum):
    """Type of validation to perform"""
    SCHEMA_COMPLIANCE = "schema_compliance"
    DATA_INTEGRITY = "data_integrity"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    DATA_QUALITY = "data_quality"
    BUSINESS_RULES = "business_rules"
    DUPLICATE_DETECTION = "duplicate_detection"
    COMPLETENESS = "completeness"


class ValidationSeverity(str, Enum):
    """Severity level of validation issues"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DataType(str, Enum):
    """Data type categories"""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    JSON = "json"
    BINARY = "binary"


class ColumnValidationRule(BaseModel):
    """Validation rule for a column"""
    column_name: str = Field(..., description="Name of the column")
    data_type: DataType = Field(..., description="Expected data type")
    nullable: bool = Field(default=True, description="Whether NULL values are allowed")
    min_value: Optional[float] = Field(None, description="Minimum value for numeric columns")
    max_value: Optional[float] = Field(None, description="Maximum value for numeric columns")
    min_length: Optional[int] = Field(None, ge=0, description="Minimum string length")
    max_length: Optional[int] = Field(None, ge=0, description="Maximum string length")
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    allowed_values: Optional[List[Any]] = Field(None, description="List of allowed values")
    unique: bool = Field(default=False, description="Whether values must be unique")


class TableValidationSpec(BaseModel):
    """Validation specification for a table"""
    table_name: str = Field(..., description="Name of the table")
    column_rules: List[ColumnValidationRule] = Field(..., description="Column validation rules")
    primary_key: List[str] = Field(default_factory=list, description="Primary key columns")
    foreign_keys: Optional[Dict[str, Dict[str, str]]] = Field(
        None,
        description="Foreign key relationships"
    )
    business_rules: Optional[List[str]] = Field(None, description="Business rule descriptions")


class ValidationRequest(BaseModel):
    """Request to validate data"""
    database_connection: Dict[str, Any] = Field(..., description="Database connection details")
    validation_specs: List[TableValidationSpec] = Field(..., min_length=1, description="Validation specifications")
    validation_types: List[ValidationType] = Field(..., min_length=1, description="Types of validation to perform")
    sample_size: Optional[int] = Field(None, ge=1, description="Number of rows to sample (None = all rows)")
    fail_fast: bool = Field(default=False, description="Stop on first critical error")
    parallel_execution: bool = Field(default=True, description="Execute validations in parallel")


class ValidationIssue(BaseModel):
    """A validation issue found"""
    issue_id: str = Field(..., description="Unique issue identifier")
    table_name: str = Field(..., description="Table where issue was found")
    column_name: Optional[str] = Field(None, description="Column where issue was found")
    row_identifier: Optional[str] = Field(None, description="Identifier for the problematic row")
    validation_type: ValidationType = Field(..., description="Type of validation that failed")
    severity: ValidationSeverity = Field(..., description="Severity level")
    description: str = Field(..., description="Description of the issue")
    expected_value: Optional[str] = Field(None, description="Expected value or format")
    actual_value: Optional[str] = Field(None, description="Actual value found")
    rule_violated: str = Field(..., description="Validation rule that was violated")
    suggestion: Optional[str] = Field(None, description="Suggestion for fixing the issue")


class DuplicateRecord(BaseModel):
    """Information about duplicate records"""
    table_name: str = Field(..., description="Table containing duplicates")
    columns: List[str] = Field(..., description="Columns checked for duplicates")
    duplicate_count: int = Field(..., ge=2, description="Number of duplicate records")
    sample_values: List[Dict[str, Any]] = Field(..., description="Sample duplicate values")
    total_occurrences: int = Field(..., ge=2, description="Total occurrences of the duplicate")


class DataQualityMetrics(BaseModel):
    """Data quality metrics for a table"""
    table_name: str = Field(..., description="Table name")
    total_rows: int = Field(..., ge=0, description="Total number of rows")
    valid_rows: int = Field(..., ge=0, description="Number of valid rows")
    invalid_rows: int = Field(..., ge=0, description="Number of invalid rows")
    completeness_percent: float = Field(..., ge=0.0, le=100.0, description="Data completeness percentage")
    accuracy_percent: float = Field(..., ge=0.0, le=100.0, description="Data accuracy percentage")
    consistency_percent: float = Field(..., ge=0.0, le=100.0, description="Data consistency percentage")
    uniqueness_percent: float = Field(..., ge=0.0, le=100.0, description="Data uniqueness percentage")
    overall_quality_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")


class ColumnStatistics(BaseModel):
    """Statistics for a column"""
    column_name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type")
    null_count: int = Field(..., ge=0, description="Number of NULL values")
    null_percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of NULL values")
    distinct_count: int = Field(..., ge=0, description="Number of distinct values")
    min_value: Optional[Any] = Field(None, description="Minimum value")
    max_value: Optional[Any] = Field(None, description="Maximum value")
    avg_length: Optional[float] = Field(None, ge=0.0, description="Average string length")
    pattern_compliance: Optional[float] = Field(None, ge=0.0, le=100.0, description="Pattern compliance percentage")


class IntegrityCheckResult(BaseModel):
    """Result of integrity check"""
    check_type: str = Field(..., description="Type of integrity check")
    table_name: str = Field(..., description="Table checked")
    passed: bool = Field(..., description="Whether check passed")
    issues_found: int = Field(..., ge=0, description="Number of issues found")
    details: str = Field(..., description="Details about the check")
    affected_rows: Optional[int] = Field(None, ge=0, description="Number of affected rows")


class ValidationStatistics(BaseModel):
    """Statistics about validation execution"""
    total_tables_validated: int = Field(..., ge=0, description="Total tables validated")
    total_rows_validated: int = Field(..., ge=0, description="Total rows validated")
    total_columns_validated: int = Field(..., ge=0, description="Total columns validated")
    validation_duration_seconds: float = Field(..., ge=0.0, description="Validation duration")
    issues_found: int = Field(..., ge=0, description="Total issues found")
    critical_issues: int = Field(..., ge=0, description="Critical issues found")
    errors: int = Field(..., ge=0, description="Errors found")
    warnings: int = Field(..., ge=0, description="Warnings found")


class ValidationSummary(BaseModel):
    """Summary of validation results"""
    validation_id: str = Field(..., description="Unique validation identifier")
    timestamp: datetime = Field(..., description="Validation timestamp")
    overall_status: str = Field(..., description="Overall validation status (passed/failed)")
    overall_quality_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")
    needs_attention: bool = Field(..., description="Whether issues need attention")
    recommendation: str = Field(..., description="Overall recommendation")


class ValidationResponse(BaseModel):
    """Response from data validation suite"""
    summary: ValidationSummary = Field(..., description="Validation summary")
    statistics: ValidationStatistics = Field(..., description="Validation statistics")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Issues found")
    duplicates: List[DuplicateRecord] = Field(default_factory=list, description="Duplicate records found")
    quality_metrics: List[DataQualityMetrics] = Field(default_factory=list, description="Quality metrics per table")
    column_statistics: List[ColumnStatistics] = Field(
        default_factory=list,
        description="Column-level statistics"
    )
    integrity_checks: List[IntegrityCheckResult] = Field(
        default_factory=list,
        description="Integrity check results"
    )
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
