"""
Models for index recommendation engine endpoint.
Analyzes schemas and workloads to recommend optimal indexes.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class IndexType(str, Enum):
    """Type of database index"""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"
    BITMAP = "bitmap"
    CLUSTERED = "clustered"
    NONCLUSTERED = "nonclustered"


class WorkloadPattern(str, Enum):
    """Type of workload pattern"""
    READ_HEAVY = "read_heavy"
    WRITE_HEAVY = "write_heavy"
    MIXED = "mixed"
    ANALYTICAL = "analytical"
    TRANSACTIONAL = "transactional"


class IndexImpact(str, Enum):
    """Impact level of creating an index"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ColumnUsage(BaseModel):
    """Usage pattern for a column"""
    column_name: str = Field(..., description="Name of the column")
    in_where_clause_count: int = Field(default=0, ge=0, description="Times used in WHERE clause")
    in_join_count: int = Field(default=0, ge=0, description="Times used in JOIN")
    in_order_by_count: int = Field(default=0, ge=0, description="Times used in ORDER BY")
    in_group_by_count: int = Field(default=0, ge=0, description="Times used in GROUP BY")
    selectivity: float = Field(..., ge=0.0, le=100.0, description="Column selectivity percentage")


class TableWorkload(BaseModel):
    """Workload information for a table"""
    table_name: str = Field(..., description="Name of the table")
    row_count: int = Field(..., ge=0, description="Number of rows")
    queries_per_second: float = Field(..., ge=0.0, description="Average queries per second")
    column_usage: List[ColumnUsage] = Field(..., description="Column usage statistics")
    existing_indexes: List[str] = Field(default_factory=list, description="Existing indexes")
    avg_query_time_ms: Optional[float] = Field(None, ge=0.0, description="Average query time in ms")


class IndexRecommendationRequest(BaseModel):
    """Request to get index recommendations"""
    database_type: str = Field(..., description="Database type (postgresql, mysql, etc)")
    workload: List[TableWorkload] = Field(..., min_length=1, description="Workload information")
    workload_pattern: WorkloadPattern = Field(..., description="Overall workload pattern")
    optimization_goal: str = Field(
        default="balanced",
        description="Optimization goal: speed, storage, or balanced"
    )
    max_indexes_per_table: int = Field(default=5, ge=1, le=20, description="Maximum indexes per table")
    include_composite_indexes: bool = Field(default=True, description="Include composite indexes")


class IndexRecommendation(BaseModel):
    """Recommendation for creating an index"""
    table_name: str = Field(..., description="Table for the index")
    index_name: str = Field(..., description="Suggested index name")
    index_type: IndexType = Field(..., description="Type of index")
    columns: List[str] = Field(..., min_length=1, description="Columns in the index")
    is_composite: bool = Field(..., description="Whether it's a composite index")
    estimated_size_mb: float = Field(..., ge=0.0, description="Estimated index size in MB")
    estimated_read_improvement_percent: float = Field(
        ..., ge=0.0, le=100.0,
        description="Expected read performance improvement"
    )
    estimated_write_overhead_percent: float = Field(
        ..., ge=0.0, le=100.0,
        description="Expected write performance overhead"
    )
    priority: str = Field(..., description="Priority level (critical, high, medium, low)")
    rationale: str = Field(..., description="Explanation for recommendation")
    creation_sql: str = Field(..., description="SQL to create the index")
    impact: IndexImpact = Field(..., description="Overall impact level")


class CoveringIndexRecommendation(BaseModel):
    """Recommendation for a covering index"""
    table_name: str = Field(..., description="Table for the covering index")
    index_name: str = Field(..., description="Suggested index name")
    key_columns: List[str] = Field(..., description="Key columns")
    included_columns: List[str] = Field(..., description="Included (covering) columns")
    queries_covered: int = Field(..., ge=1, description="Number of queries this index would cover")
    estimated_improvement_percent: float = Field(..., ge=0.0, le=100.0, description="Expected improvement")
    creation_sql: str = Field(..., description="SQL to create the covering index")


class RedundantIndex(BaseModel):
    """Information about a redundant index"""
    table_name: str = Field(..., description="Table with redundant index")
    redundant_index: str = Field(..., description="Name of redundant index")
    overlaps_with: str = Field(..., description="Index it overlaps with")
    columns: List[str] = Field(..., description="Columns in redundant index")
    reason: str = Field(..., description="Why it's considered redundant")
    space_saved_mb: float = Field(..., ge=0.0, description="Space that would be saved by removing")
    recommendation: str = Field(..., description="Recommendation (remove, keep, modify)")


class MissingIndexPattern(BaseModel):
    """Pattern indicating missing indexes"""
    pattern_type: str = Field(..., description="Type of pattern detected")
    affected_queries: int = Field(..., ge=1, description="Number of affected queries")
    description: str = Field(..., description="Description of the pattern")
    suggested_indexes: List[str] = Field(..., description="Suggested index names to create")


class IndexMaintenanceRecommendation(BaseModel):
    """Recommendation for index maintenance"""
    table_name: str = Field(..., description="Table needing maintenance")
    index_name: str = Field(..., description="Index needing maintenance")
    issue: str = Field(..., description="Maintenance issue detected")
    fragmentation_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Index fragmentation")
    recommendation: str = Field(..., description="Maintenance action recommended")
    maintenance_sql: str = Field(..., description="SQL to perform maintenance")


class WorkloadAnalysis(BaseModel):
    """Analysis of the workload"""
    total_queries_analyzed: int = Field(..., ge=0, description="Total queries in workload")
    read_write_ratio: str = Field(..., description="Read vs write ratio")
    most_frequent_patterns: List[str] = Field(..., description="Most frequent query patterns")
    bottleneck_tables: List[str] = Field(default_factory=list, description="Tables with performance issues")
    optimization_opportunities: int = Field(..., ge=0, description="Number of optimization opportunities")


class IndexStatistics(BaseModel):
    """Statistics about current and recommended indexes"""
    current_indexes_count: int = Field(..., ge=0, description="Current number of indexes")
    recommended_new_indexes: int = Field(..., ge=0, description="Number of new indexes recommended")
    redundant_indexes: int = Field(..., ge=0, description="Number of redundant indexes found")
    total_current_size_mb: float = Field(..., ge=0.0, description="Total size of current indexes")
    estimated_new_size_mb: float = Field(..., ge=0.0, description="Estimated size of new indexes")
    estimated_space_saved_mb: float = Field(..., ge=0.0, description="Space saved by removing redundant")


class IndexRecommendationSummary(BaseModel):
    """Summary of index recommendations"""
    total_recommendations: int = Field(..., ge=0, description="Total recommendations provided")
    critical_recommendations: int = Field(..., ge=0, description="Critical priority recommendations")
    estimated_total_improvement_percent: float = Field(
        ..., ge=0.0,
        description="Estimated overall improvement"
    )
    implementation_complexity: str = Field(..., description="Overall complexity of implementation")
    estimated_implementation_hours: float = Field(..., ge=0.0, description="Estimated implementation time")


class IndexRecommendationResponse(BaseModel):
    """Response from index recommendation engine"""
    workload_analysis: WorkloadAnalysis = Field(..., description="Analysis of the workload")
    recommendations: List[IndexRecommendation] = Field(
        default_factory=list,
        description="Index recommendations"
    )
    covering_indexes: List[CoveringIndexRecommendation] = Field(
        default_factory=list,
        description="Covering index recommendations"
    )
    redundant_indexes: List[RedundantIndex] = Field(
        default_factory=list,
        description="Redundant indexes to remove"
    )
    missing_patterns: List[MissingIndexPattern] = Field(
        default_factory=list,
        description="Missing index patterns"
    )
    maintenance_recommendations: List[IndexMaintenanceRecommendation] = Field(
        default_factory=list,
        description="Index maintenance recommendations"
    )
    statistics: IndexStatistics = Field(..., description="Index statistics")
    summary: IndexRecommendationSummary = Field(..., description="Summary of recommendations")
    warnings: List[str] = Field(default_factory=list, description="Warnings and considerations")
