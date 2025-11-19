"""
Query Cost Analysis Models

Pydantic models for query cost analyzer endpoint (POST /api/query/analyze-cost).
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


class QueryType(str, Enum):
    """Query operation types"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    JOIN = "join"
    AGGREGATE = "aggregate"
    SUBQUERY = "subquery"
    UNION = "union"


class OptimizationCategory(str, Enum):
    """Categories of optimization suggestions"""
    INDEX = "index"
    QUERY_REWRITE = "query_rewrite"
    SCHEMA_DESIGN = "schema_design"
    PARTITIONING = "partitioning"
    CACHING = "caching"
    DENORMALIZATION = "denormalization"


class CostSeverity(str, Enum):
    """Severity levels for cost issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QueryCostRequest(BaseModel):
    """Request model for query cost analysis"""
    
    query: str = Field(
        ...,
        description="SQL query to analyze",
        min_length=1,
        max_length=10000
    )
    
    database_type: DatabaseType = Field(
        default=DatabaseType.POSTGRESQL,
        description="Type of database"
    )
    
    schema_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional schema metadata (tables, indexes, row counts)"
    )
    
    explain_plan: Optional[str] = Field(
        default=None,
        description="Optional EXPLAIN plan output from database"
    )
    
    include_optimizations: bool = Field(
        default=True,
        description="Whether to include optimization suggestions"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query is not empty or only whitespace"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class CostBreakdown(BaseModel):
    """Detailed cost breakdown for query execution"""
    
    cpu_cost: float = Field(
        ...,
        description="CPU processing cost",
        ge=0
    )
    
    io_cost: float = Field(
        ...,
        description="Disk I/O cost",
        ge=0
    )
    
    memory_cost: float = Field(
        ...,
        description="Memory usage cost",
        ge=0
    )
    
    network_cost: float = Field(
        default=0.0,
        description="Network transfer cost",
        ge=0
    )
    
    total_cost: float = Field(
        ...,
        description="Total estimated cost",
        ge=0
    )
    
    cost_unit: str = Field(
        default="abstract_units",
        description="Unit of cost measurement"
    )


class ExecutionStats(BaseModel):
    """Estimated execution statistics"""
    
    estimated_rows: int = Field(
        ...,
        description="Estimated number of rows processed",
        ge=0
    )
    
    estimated_time_ms: float = Field(
        ...,
        description="Estimated execution time in milliseconds",
        ge=0
    )
    
    tables_accessed: List[str] = Field(
        default_factory=list,
        description="List of tables accessed by query"
    )
    
    indexes_used: List[str] = Field(
        default_factory=list,
        description="List of indexes used"
    )
    
    full_table_scans: int = Field(
        default=0,
        description="Number of full table scans",
        ge=0
    )


class OptimizationSuggestion(BaseModel):
    """Single optimization suggestion"""
    
    category: OptimizationCategory = Field(
        ...,
        description="Category of optimization"
    )
    
    severity: CostSeverity = Field(
        ...,
        description="Severity of the cost issue"
    )
    
    title: str = Field(
        ...,
        description="Brief title of the suggestion"
    )
    
    description: str = Field(
        ...,
        description="Detailed description of the issue"
    )
    
    suggestion: str = Field(
        ...,
        description="Specific optimization recommendation"
    )
    
    potential_savings: Optional[float] = Field(
        default=None,
        description="Estimated cost reduction percentage",
        ge=0,
        le=100
    )
    
    sql_example: Optional[str] = Field(
        default=None,
        description="Example SQL showing the optimization"
    )


class QueryAnalysis(BaseModel):
    """Detailed query analysis results"""
    
    query_type: QueryType = Field(
        ...,
        description="Type of query operation"
    )
    
    complexity_score: float = Field(
        ...,
        description="Query complexity score (0-100)",
        ge=0,
        le=100
    )
    
    issues_found: int = Field(
        default=0,
        description="Number of performance issues detected",
        ge=0
    )
    
    critical_issues: int = Field(
        default=0,
        description="Number of critical issues",
        ge=0
    )


class QueryCostResponse(BaseModel):
    """Response model for query cost analysis"""
    
    success: bool = Field(
        default=True,
        description="Whether analysis succeeded"
    )
    
    query_analysis: QueryAnalysis = Field(
        ...,
        description="High-level query analysis"
    )
    
    cost_breakdown: CostBreakdown = Field(
        ...,
        description="Detailed cost breakdown"
    )
    
    execution_stats: ExecutionStats = Field(
        ...,
        description="Execution statistics"
    )
    
    optimizations: List[OptimizationSuggestion] = Field(
        default_factory=list,
        description="List of optimization suggestions"
    )
    
    optimized_query: Optional[str] = Field(
        default=None,
        description="Auto-optimized version of the query"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
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
