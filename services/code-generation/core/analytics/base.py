"""
Base classes and types for advanced analytics system
"""
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

class AnalyticsMetricType(Enum):
    """Types of analytics metrics"""
    USAGE_FREQUENCY = "usage_frequency"
    PERFORMANCE = "performance"
    COMPLEXITY = "complexity"
    GROWTH_TREND = "growth_trend"
    ERROR_RATE = "error_rate"
    OPTIMIZATION_SCORE = "optimization_score"
    USER_BEHAVIOR = "user_behavior"
    SYSTEM_HEALTH = "system_health"

class TimeGranularity(Enum):
    """Time granularity for analytics"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

@dataclass
class AnalyticsDataPoint:
    """Single analytics data point"""
    id: str
    metric_type: AnalyticsMetricType
    value: float
    timestamp: datetime
    schema_id: Optional[str] = None
    user_id: Optional[str] = None
    operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

@dataclass
class AnalyticsQuery:
    """Query parameters for analytics data"""
    metric_types: List[AnalyticsMetricType]
    start_time: datetime
    end_time: datetime
    schema_ids: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    operations: Optional[List[str]] = None
    granularity: TimeGranularity = TimeGranularity.HOUR
    aggregation: str = "avg"  # avg, sum, count, min, max
    filters: Dict[str, Any] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)
    limit: Optional[int] = None

@dataclass
class AnalyticsInsight:
    """Analytics insight or recommendation"""
    id: str
    title: str
    description: str
    category: str
    confidence: float
    impact: str  # low, medium, high
    recommendations: List[str]
    supporting_data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SchemaUsagePattern:
    """Usage pattern for a schema"""
    schema_id: str
    total_operations: int
    unique_users: int
    peak_usage_time: datetime
    most_accessed_tables: List[Tuple[str, int]]
    operation_distribution: Dict[str, int]
    user_activity_distribution: Dict[str, int]
    temporal_patterns: Dict[str, List[float]]
    anomaly_scores: Dict[str, float]

@dataclass
class PerformanceMetric:
    """Performance metric data"""
    operation: str
    average_duration: float
    p50_duration: float
    p95_duration: float
    p99_duration: float
    error_rate: float
    throughput: float
    sample_count: int
    time_period: Tuple[datetime, datetime]
