"""
Models for query performance predictor endpoint.
Predicts query performance and provides optimization suggestions.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class QueryType(str, Enum):
    """Type of SQL query"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    JOIN = "join"
    AGGREGATION = "aggregation"
    SUBQUERY = "subquery"
    UNION = "union"


class DatabaseEngine(str, Enum):
    """Database engine type"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    MARIADB = "mariadb"


class PerformancePrediction(str, Enum):
    """Predicted performance level"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    SLOW = "slow"
    VERY_SLOW = "very_slow"


class OptimizationPriority(str, Enum):
    """Priority level for optimization"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TableStatistics(BaseModel):
    """Statistics for a database table"""
    table_name: str = Field(..., description="Name of the table")
    row_count: int = Field(..., ge=0, description="Number of rows in the table")
    avg_row_size_bytes: Optional[int] = Field(None, ge=0, description="Average row size in bytes")
    total_size_mb: Optional[float] = Field(None, ge=0.0, description="Total table size in MB")
    index_count: int = Field(default=0, ge=0, description="Number of indexes")
    has_primary_key: bool = Field(default=True, description="Whether table has primary key")


class PredictorRequest(BaseModel):
    """Request to predict query performance"""
    sql_query: str = Field(..., min_length=1, description="SQL query to analyze")
    database_engine: DatabaseEngine = Field(..., description="Target database engine")
    table_statistics: List[TableStatistics] = Field(..., min_length=1, description="Statistics for involved tables")
    query_type: Optional[QueryType] = Field(None, description="Type of query (auto-detected if not provided)")
    expected_result_rows: Optional[int] = Field(None, ge=0, description="Expected number of result rows")
    concurrent_queries: int = Field(default=1, ge=1, le=1000, description="Expected concurrent queries")


class QueryAnalysis(BaseModel):
    """Analysis of the SQL query structure"""
    query_type: QueryType = Field(..., description="Detected query type")
    tables_involved: List[str] = Field(..., description="Tables referenced in query")
    joins_count: int = Field(..., ge=0, description="Number of joins")
    has_subqueries: bool = Field(..., description="Whether query contains subqueries")
    has_aggregations: bool = Field(..., description="Whether query uses aggregations")
    where_clause_complexity: str = Field(..., description="Complexity of WHERE clause")
    estimated_rows_scanned: int = Field(..., ge=0, description="Estimated rows to scan")
    selectivity: float = Field(..., ge=0.0, le=100.0, description="Query selectivity percentage")


class PerformanceMetrics(BaseModel):
    """Predicted performance metrics"""
    estimated_execution_time_ms: float = Field(..., ge=0.0, description="Estimated execution time in milliseconds")
    estimated_cpu_cost: float = Field(..., ge=0.0, description="Estimated CPU cost")
    estimated_io_cost: float = Field(..., ge=0.0, description="Estimated I/O cost")
    estimated_memory_mb: float = Field(..., ge=0.0, description="Estimated memory usage in MB")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in prediction")
    performance_rating: PerformancePrediction = Field(..., description="Overall performance rating")


class OptimizationSuggestion(BaseModel):
    """Suggestion for query optimization"""
    priority: OptimizationPriority = Field(..., description="Priority level")
    category: str = Field(..., description="Optimization category")
    suggestion: str = Field(..., description="Detailed optimization suggestion")
    expected_improvement: str = Field(..., description="Expected performance improvement")
    implementation_complexity: str = Field(..., description="Complexity of implementing suggestion")
    example: Optional[str] = Field(None, description="Example implementation")


class IndexRecommendation(BaseModel):
    """Recommendation for creating an index"""
    table_name: str = Field(..., description="Table for index")
    columns: List[str] = Field(..., min_length=1, description="Columns to index")
    index_type: str = Field(..., description="Type of index (BTREE, HASH, etc)")
    estimated_improvement_percent: float = Field(..., ge=0.0, le=100.0, description="Expected improvement")
    creation_sql: str = Field(..., description="SQL to create the index")


class BottleneckAnalysis(BaseModel):
    """Analysis of query bottlenecks"""
    bottleneck_type: str = Field(..., description="Type of bottleneck")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Detailed description")
    impact_on_performance: str = Field(..., description="Impact on overall performance")
    resolution: str = Field(..., description="How to resolve the bottleneck")


class ComparisonMetrics(BaseModel):
    """Comparison with similar queries"""
    similar_query_avg_time_ms: float = Field(..., ge=0.0, description="Average time for similar queries")
    percentile_ranking: float = Field(..., ge=0.0, le=100.0, description="Percentile ranking vs similar queries")
    improvement_potential_percent: float = Field(..., ge=0.0, description="Potential improvement percentage")


class PredictorSummary(BaseModel):
    """Summary of performance prediction"""
    overall_assessment: str = Field(..., description="Overall performance assessment")
    needs_optimization: bool = Field(..., description="Whether optimization is needed")
    critical_issues_count: int = Field(..., ge=0, description="Number of critical issues")
    estimated_optimization_time_hours: float = Field(..., ge=0.0, description="Estimated time to optimize")


class PredictorResponse(BaseModel):
    """Response from query performance predictor"""
    query_analysis: QueryAnalysis = Field(..., description="Analysis of the query structure")
    performance_metrics: PerformanceMetrics = Field(..., description="Predicted performance metrics")
    bottlenecks: List[BottleneckAnalysis] = Field(default_factory=list, description="Identified bottlenecks")
    optimization_suggestions: List[OptimizationSuggestion] = Field(
        default_factory=list,
        description="Optimization suggestions"
    )
    index_recommendations: List[IndexRecommendation] = Field(
        default_factory=list,
        description="Index recommendations"
    )
    comparison: Optional[ComparisonMetrics] = Field(None, description="Comparison with similar queries")
    summary: PredictorSummary = Field(..., description="Summary and recommendations")
    warnings: List[str] = Field(default_factory=list, description="Warnings about the query")
