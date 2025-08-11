"""
Phase 4: Performance Optimization Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
import uuid

class QueryType(str, Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE_TABLE = "create_table"
    CREATE_INDEX = "create_index"
    ALTER_TABLE = "alter_table"

class IndexType(str, Enum):
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    PARTIAL = "partial"
    UNIQUE = "unique"
    COMPOSITE = "composite"
    COVERING = "covering"

class PartitionType(str, Enum):
    RANGE = "range"
    LIST = "list"
    HASH = "hash"
    DATE = "date"
    INTERVAL = "interval"

class PerformanceMetric(BaseModel):
    """Performance metric measurement."""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    connection_id: str
    
    # Query information
    query_hash: str
    query_text: str
    query_type: QueryType
    
    # Performance metrics
    execution_time_ms: float
    rows_examined: Optional[int] = None
    rows_returned: Optional[int] = None
    cpu_time_ms: Optional[float] = None
    io_reads: Optional[int] = None
    io_writes: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    
    # Database-specific metrics
    index_scans: Optional[int] = None
    sequential_scans: Optional[int] = None
    sort_operations: Optional[int] = None
    temp_tables_created: Optional[int] = None
    
    # Context
    table_names: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database_size_mb: Optional[float] = None
    concurrent_connections: Optional[int] = None

class QueryAnalysis(BaseModel):
    """Query performance analysis."""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    query_hash: str
    
    # Query details
    original_query: str
    normalized_query: str
    query_type: QueryType
    complexity_score: float = Field(ge=0.0, le=1.0)
    
    # Performance analysis
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    execution_count: int
    
    # Issues identified
    performance_issues: List[Dict[str, Any]] = Field(default_factory=list)
    optimization_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recommendations
    index_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    query_rewrite_suggestions: List[str] = Field(default_factory=list)
    
    # Impact assessment
    estimated_improvement_percent: Optional[float] = None
    priority_score: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)

class IndexRecommendation(BaseModel):
    """Index recommendation for performance optimization."""
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    table_name: str
    
    # Index details
    index_name: str
    index_type: IndexType
    columns: List[str]
    include_columns: List[str] = Field(default_factory=list)  # For covering indexes
    
    # Conditions
    where_clause: Optional[str] = None  # For partial indexes
    unique: bool = False
    
    # Impact analysis
    estimated_size_mb: float
    estimated_creation_time_minutes: float
    estimated_maintenance_overhead_percent: float
    
    # Benefits
    queries_improved: List[str] = Field(default_factory=list)
    estimated_performance_gain_percent: float
    selectivity_ratio: float = Field(ge=0.0, le=1.0)
    
    # Cost-benefit analysis
    cost_score: float = Field(ge=0.0, le=1.0)
    benefit_score: float = Field(ge=0.0, le=1.0)
    priority_score: float = Field(ge=0.0, le=1.0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, approved, implemented, rejected

class PartitionRecommendation(BaseModel):
    """Table partitioning recommendation."""
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    table_name: str
    
    # Partitioning strategy
    partition_type: PartitionType
    partition_column: str
    partition_scheme: Dict[str, Any]  # Specific to partition type
    
    # Current table metrics
    current_size_mb: float
    current_row_count: int
    query_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Projected benefits
    estimated_query_improvement_percent: float
    estimated_maintenance_improvement_percent: float
    estimated_storage_efficiency_percent: float
    
    # Implementation details
    migration_complexity_score: float = Field(ge=0.0, le=1.0)
    estimated_migration_time_hours: float
    downtime_required_minutes: float
    
    # Partition specifications
    suggested_partitions: List[Dict[str, Any]] = Field(default_factory=list)
    retention_policy: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(ge=0.0, le=1.0)

class PerformanceBaseline(BaseModel):
    """Performance baseline for comparison."""
    baseline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    connection_id: str
    name: str
    
    # Baseline metrics
    avg_query_time_ms: float
    queries_per_second: float
    cpu_utilization_percent: float
    memory_utilization_percent: float
    io_operations_per_second: float
    
    # Database metrics
    total_tables: int
    total_indexes: int
    database_size_mb: float
    active_connections: int
    
    # Query distribution
    query_type_distribution: Dict[QueryType, int] = Field(default_factory=dict)
    slowest_queries: List[Dict[str, Any]] = Field(default_factory=list)
    most_frequent_queries: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    measurement_period_hours: int = 24
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    is_active_baseline: bool = False

class PerformanceReport(BaseModel):
    """Comprehensive performance analysis report."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    name: str
    
    # Report scope
    connection_ids: List[str]
    analysis_period_start: datetime
    analysis_period_end: datetime
    
    # Executive summary
    overall_performance_score: float = Field(ge=0.0, le=1.0)
    critical_issues_count: int = 0
    recommendations_count: int = 0
    estimated_total_improvement_percent: float = 0.0
    
    # Detailed analysis
    query_analysis_results: List[str] = Field(default_factory=list)  # analysis IDs
    index_recommendations: List[str] = Field(default_factory=list)  # recommendation IDs
    partition_recommendations: List[str] = Field(default_factory=list)
    
    # Performance trends
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)
    bottleneck_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Resource utilization
    resource_utilization: Dict[str, Any] = Field(default_factory=dict)
    capacity_planning: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    report_format: str = "json"  # json, html, pdf

class PerformanceAlert(BaseModel):
    """Performance monitoring alert."""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    connection_id: str
    
    # Alert details
    alert_type: str  # slow_query, high_cpu, high_memory, etc.
    severity: str = "medium"  # low, medium, high, critical
    title: str
    description: str
    
    # Trigger conditions
    metric_name: str
    current_value: float
    threshold_value: float
    threshold_operator: str  # >, <, >=, <=, ==
    
    # Context
    affected_queries: List[str] = Field(default_factory=list)
    affected_tables: List[str] = Field(default_factory=list)
    duration_minutes: Optional[int] = None
    
    # Resolution
    status: str = "open"  # open, acknowledged, resolved, suppressed
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Metadata
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    last_occurrence: datetime = Field(default_factory=datetime.utcnow)
    occurrence_count: int = 1

class PerformanceOptimization(BaseModel):
    """Performance optimization task."""
    optimization_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    
    # Optimization details
    optimization_type: str  # index_creation, query_rewrite, partitioning
    target_table: Optional[str] = None
    target_query: Optional[str] = None
    
    # Implementation
    optimization_script: str
    rollback_script: Optional[str] = None
    estimated_impact: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution
    status: str = "planned"  # planned, testing, implemented, rolled_back
    implemented_at: Optional[datetime] = None
    
    # Results
    before_metrics: Optional[Dict[str, float]] = None
    after_metrics: Optional[Dict[str, float]] = None
    actual_improvement_percent: Optional[float] = None
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = "medium"  # low, medium, high, critical
