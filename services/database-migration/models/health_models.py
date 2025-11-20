"""
Health Benchmark models for Phase 2.2 features.
Includes models for performance scoring, health timeline, and slow query analysis.
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

# --- Enums ---

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    MONGODB = "mongodb"

class HealthStatus(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class TrendDirection(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"

class QueryIssueType(str, Enum):
    MISSING_INDEX = "missing_index"
    FULL_TABLE_SCAN = "full_table_scan"
    INEFFICIENT_JOIN = "inefficient_join"
    N_PLUS_ONE = "n_plus_one"
    SUBOPTIMAL_QUERY = "suboptimal_query"

# --- Performance Score Models ---

class PerformanceScoreRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    include_recommendations: bool = True

class CategoryScore(BaseModel):
    category: str
    score: int = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    issues: List[str]
    recommendations: List[str]

class PerformanceMetrics(BaseModel):
    total_queries: int
    slow_queries: int
    avg_query_time_ms: float
    cache_hit_ratio: float
    connection_pool_usage: float
    table_count: int
    index_count: int
    missing_indexes: int

class PerformanceScoreData(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    health_status: HealthStatus
    category_breakdown: List[CategoryScore]
    metrics: PerformanceMetrics
    top_recommendations: List[str]
    last_analyzed: datetime
    next_check_recommended: datetime

class PerformanceScoreResponse(BaseModel):
    success: bool
    data: PerformanceScoreData

# --- Health Timeline Models ---

class HealthTimelineRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    days: int = Field(default=30, ge=1, le=365)
    include_forecast: bool = True

class DataPoint(BaseModel):
    timestamp: datetime
    score: int = Field(..., ge=0, le=100)
    health_status: HealthStatus
    key_metrics: Dict[str, float]

class Anomaly(BaseModel):
    timestamp: datetime
    severity: str
    description: str
    impact_score: int = Field(..., ge=0, le=100)
    potential_cause: str

class Forecast(BaseModel):
    timestamp: datetime
    predicted_score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    prediction_range: Dict[str, int]  # min/max

class TrendAnalysis(BaseModel):
    direction: TrendDirection
    change_percentage: float
    velocity: float  # Score change per day
    volatility: float  # Standard deviation

class HealthTimelineData(BaseModel):
    timeline: List[DataPoint]
    trend_analysis: TrendAnalysis
    anomalies: List[Anomaly]
    forecast: Optional[List[Forecast]]
    period_summary: Dict[str, Any]

class HealthTimelineResponse(BaseModel):
    success: bool
    data: HealthTimelineData

# --- Slow Query Analyzer Models ---

class SlowQueryRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    threshold_ms: int = Field(default=1000, ge=100)
    limit: int = Field(default=50, ge=1, le=1000)
    include_explain: bool = True

class ExecutionPlan(BaseModel):
    operation: str
    cost: float
    rows: int
    details: Dict[str, Any]

class QueryOptimization(BaseModel):
    issue_type: QueryIssueType
    severity: str
    description: str
    suggested_fix: str
    estimated_improvement: str
    sql_fix: Optional[str]

class SlowQuery(BaseModel):
    query_id: str
    query_text: str
    execution_time_ms: float
    execution_count: int
    avg_time_ms: float
    max_time_ms: float
    last_executed: datetime
    tables_accessed: List[str]
    execution_plan: Optional[ExecutionPlan]
    optimizations: List[QueryOptimization]
    cost_estimate: float

class QueryStatistics(BaseModel):
    total_slow_queries: int
    total_execution_time_ms: float
    avg_execution_time_ms: float
    queries_analyzed: int
    optimization_opportunities: int

class ImpactAnalysis(BaseModel):
    current_cost_per_day: float
    potential_savings_per_day: float
    affected_users: int
    business_impact: str

class SlowQueryData(BaseModel):
    slow_queries: List[SlowQuery]
    statistics: QueryStatistics
    impact_analysis: ImpactAnalysis
    top_optimizations: List[QueryOptimization]
    auto_fix_available: bool
    auto_fix_sql: List[str]

class SlowQueryResponse(BaseModel):
    success: bool
    data: SlowQueryData
