"""
SQL Dialect Translation Models

Pydantic models for SQL dialect translator endpoint (POST /api/code/translate-sql).
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class SQLDialect(str, Enum):
    """Supported SQL dialects"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    SQLITE = "sqlite"
    MARIADB = "mariadb"
    DB2 = "db2"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"


class CompatibilityLevel(str, Enum):
    """Translation compatibility levels"""
    FULLY_COMPATIBLE = "fully_compatible"
    MOSTLY_COMPATIBLE = "mostly_compatible"
    MANUAL_REVIEW_NEEDED = "manual_review_needed"
    NOT_COMPATIBLE = "not_compatible"


class WarningSeverity(str, Enum):
    """Severity levels for translation warnings"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ChangeCategory(str, Enum):
    """Categories of syntax changes"""
    FUNCTION = "function"
    DATA_TYPE = "data_type"
    OPERATOR = "operator"
    KEYWORD = "keyword"
    JOIN_SYNTAX = "join_syntax"
    LIMIT_SYNTAX = "limit_syntax"
    DATE_FORMAT = "date_format"
    STRING_CONCAT = "string_concat"
    CASE_SENSITIVITY = "case_sensitivity"
    COMMENT_SYNTAX = "comment_syntax"


class TranslationRequest(BaseModel):
    """Request model for SQL dialect translation"""
    
    sql_query: str = Field(
        ...,
        description="SQL query to translate",
        min_length=1,
        max_length=50000
    )
    
    source_dialect: SQLDialect = Field(
        ...,
        description="Source SQL dialect"
    )
    
    target_dialect: SQLDialect = Field(
        ...,
        description="Target SQL dialect"
    )
    
    preserve_comments: bool = Field(
        default=True,
        description="Whether to preserve SQL comments"
    )
    
    format_output: bool = Field(
        default=True,
        description="Whether to format the translated SQL"
    )
    
    include_warnings: bool = Field(
        default=True,
        description="Whether to include compatibility warnings"
    )
    
    @validator('sql_query')
    def validate_query(cls, v):
        """Validate query is not empty or only whitespace"""
        if not v or not v.strip():
            raise ValueError("SQL query cannot be empty")
        return v.strip()
    
    @validator('target_dialect')
    def validate_different_dialects(cls, v, values):
        """Ensure source and target are different"""
        if 'source_dialect' in values and v == values['source_dialect']:
            raise ValueError("Source and target dialects must be different")
        return v


class SyntaxChange(BaseModel):
    """Individual syntax change made during translation"""
    
    category: ChangeCategory = Field(
        ...,
        description="Category of syntax change"
    )
    
    line_number: Optional[int] = Field(
        default=None,
        description="Line number in original query",
        ge=1
    )
    
    original_syntax: str = Field(
        ...,
        description="Original SQL syntax"
    )
    
    translated_syntax: str = Field(
        ...,
        description="Translated SQL syntax"
    )
    
    reason: str = Field(
        ...,
        description="Reason for the change"
    )
    
    is_automatic: bool = Field(
        default=True,
        description="Whether change was automatically applied"
    )


class CompatibilityWarning(BaseModel):
    """Compatibility warning for translated SQL"""
    
    severity: WarningSeverity = Field(
        ...,
        description="Warning severity level"
    )
    
    category: ChangeCategory = Field(
        ...,
        description="Category of warning"
    )
    
    message: str = Field(
        ...,
        description="Warning message"
    )
    
    line_number: Optional[int] = Field(
        default=None,
        description="Line number in query",
        ge=1
    )
    
    affected_fragment: Optional[str] = Field(
        default=None,
        description="SQL fragment affected by warning"
    )
    
    suggestion: Optional[str] = Field(
        default=None,
        description="Suggestion to resolve the warning"
    )
    
    requires_manual_review: bool = Field(
        default=False,
        description="Whether manual review is required"
    )


class TranslationStatistics(BaseModel):
    """Statistics about the translation"""
    
    original_lines: int = Field(
        ...,
        description="Number of lines in original query",
        ge=1
    )
    
    translated_lines: int = Field(
        ...,
        description="Number of lines in translated query",
        ge=1
    )
    
    syntax_changes: int = Field(
        default=0,
        description="Number of syntax changes made",
        ge=0
    )
    
    warnings_count: int = Field(
        default=0,
        description="Number of warnings generated",
        ge=0
    )
    
    critical_warnings: int = Field(
        default=0,
        description="Number of critical warnings",
        ge=0
    )
    
    manual_review_required: bool = Field(
        default=False,
        description="Whether manual review is required"
    )
    
    confidence_score: float = Field(
        ...,
        description="Translation confidence score (0-100)",
        ge=0.0,
        le=100.0
    )


class TranslationResponse(BaseModel):
    """Response model for SQL dialect translation"""
    
    success: bool = Field(
        default=True,
        description="Whether translation succeeded"
    )
    
    original_query: str = Field(
        ...,
        description="Original SQL query"
    )
    
    translated_query: str = Field(
        ...,
        description="Translated SQL query"
    )
    
    compatibility_level: CompatibilityLevel = Field(
        ...,
        description="Overall compatibility level"
    )
    
    statistics: TranslationStatistics = Field(
        ...,
        description="Translation statistics"
    )
    
    syntax_changes: List[SyntaxChange] = Field(
        default_factory=list,
        description="List of syntax changes made"
    )
    
    warnings: List[CompatibilityWarning] = Field(
        default_factory=list,
        description="Compatibility warnings"
    )
    
    notes: List[str] = Field(
        default_factory=list,
        description="Additional notes about translation"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Translation timestamp"
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
