"""
Performance monitoring data models and enums
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional


class MetricType(Enum):
    """Types of performance metrics"""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    API_LATENCY = "api_latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    CONCURRENT_REQUESTS = "concurrent_requests"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Single performance metric measurement"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemSnapshot:
    """System resource snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int


@dataclass
class OperationStats:
    """Statistics for a tracked operation"""
    name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    error_count: int = 0
    
    def update(self, execution_time: float, is_error: bool = False):
        """Update statistics with new execution"""
        self.count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.count
        
        if is_error:
            self.error_count += 1
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.count == 0:
            return 0.0
        return (self.error_count / self.count) * 100
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation"""
        return {
            'count': self.count,
            'total_time': self.total_time,
            'min_time': self.min_time if self.min_time != float('inf') else 0.0,
            'max_time': self.max_time,
            'avg_time': self.avg_time,
            'error_count': self.error_count,
            'error_rate': self.error_rate
        }


@dataclass
class ActiveOperation:
    """Currently active operation being tracked"""
    operation_id: str
    name: str
    start_time: float
    start_memory: float
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get current duration of the operation"""
        import time
        return time.time() - self.start_time


@dataclass
class MetricStatistics:
    """Statistical summary of metrics"""
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    p95_value: float
    p99_value: float
    
    @classmethod
    def from_values(cls, values: List[float]) -> 'MetricStatistics':
        """Create statistics from list of values"""
        if not values:
            return cls(
                count=0,
                min_value=0.0,
                max_value=0.0,
                avg_value=0.0,
                median_value=0.0,
                p95_value=0.0,
                p99_value=0.0
            )
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return cls(
            count=count,
            min_value=min(sorted_values),
            max_value=max(sorted_values),
            avg_value=sum(sorted_values) / count,
            median_value=sorted_values[count // 2],
            p95_value=sorted_values[int(count * 0.95)] if count > 0 else 0.0,
            p99_value=sorted_values[int(count * 0.99)] if count > 0 else 0.0
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation"""
        return {
            'count': self.count,
            'min': self.min_value,
            'max': self.max_value,
            'avg': self.avg_value,
            'median': self.median_value,
            'p95': self.p95_value,
            'p99': self.p99_value
        }


@dataclass
class SystemTrend:
    """System resource trend analysis"""
    metric_name: str
    trend_direction: str  # 'increasing', 'decreasing', 'stable', 'insufficient_data'
    sample_count: int
    time_span_minutes: float
    values: List[float] = field(default_factory=list)
    
    @classmethod
    def calculate_trend(cls, metric_name: str, values: List[float], time_span_minutes: float) -> 'SystemTrend':
        """Calculate trend from values"""
        if len(values) < 2:
            return cls(
                metric_name=metric_name,
                trend_direction='insufficient_data',
                sample_count=len(values),
                time_span_minutes=time_span_minutes,
                values=values
            )
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        # Avoid division by zero
        denominator = n * x2_sum - x_sum * x_sum
        if denominator == 0:
            trend_direction = 'stable'
        else:
            slope = (n * xy_sum - x_sum * y_sum) / denominator
            
            if slope > 0.1:
                trend_direction = 'increasing'
            elif slope < -0.1:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        
        return cls(
            metric_name=metric_name,
            trend_direction=trend_direction,
            sample_count=n,
            time_span_minutes=time_span_minutes,
            values=values
        )


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    timestamp: str
    time_range_hours: float
    metrics_summary: Dict[str, MetricStatistics]
    operation_statistics: Dict[str, OperationStats]
    alerts: List[Dict[str, Any]]
    system_trends: Dict[str, SystemTrend]
    recommendations: List[str]
    system_health: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            'timestamp': self.timestamp,
            'time_range_hours': self.time_range_hours,
            'metrics_summary': {
                metric_type: stats.to_dict() 
                for metric_type, stats in self.metrics_summary.items()
            },
            'operation_statistics': {
                op_name: stats.to_dict() 
                for op_name, stats in self.operation_statistics.items()
            },
            'alerts': self.alerts,
            'system_trends': {
                trend_name: {
                    'direction': trend.trend_direction,
                    'sample_count': trend.sample_count,
                    'time_span_minutes': trend.time_span_minutes
                }
                for trend_name, trend in self.system_trends.items()
            },
            'recommendations': self.recommendations,
            'system_health': self.system_health
        }


@dataclass 
class ProfileResult:
    """Results from performance profiling"""
    profile_name: str
    timestamp: str
    total_time: float
    profile_output: str
    stats_summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'profile_name': self.profile_name,
            'timestamp': self.timestamp,
            'total_time': self.total_time,
            'profile_output': self.profile_output,
            'stats_summary': self.stats_summary
        }


# Default alert thresholds
DEFAULT_ALERT_THRESHOLDS = {
    MetricType.EXECUTION_TIME: 10.0,  # 10 seconds
    MetricType.MEMORY_USAGE: 500.0,   # 500 MB
    MetricType.CPU_USAGE: 85.0,       # 85%
    MetricType.API_LATENCY: 2.0,      # 2 seconds
    MetricType.ERROR_RATE: 5.0,       # 5% error rate
    MetricType.THROUGHPUT: 100.0,     # requests per second
    MetricType.CACHE_HIT_RATE: 0.8,   # 80% hit rate
    MetricType.CONCURRENT_REQUESTS: 1000.0  # concurrent requests
}


# Utility functions
def create_metric(
    metric_type: MetricType,
    value: float,
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
) -> PerformanceMetric:
    """Create a performance metric with current timestamp"""
    return PerformanceMetric(
        metric_type=metric_type,
        value=value,
        timestamp=datetime.now(),
        context=context or {},
        tags=tags or []
    )


def create_alert(
    metric_type: MetricType,
    value: float,
    threshold: float,
    context: Optional[Dict[str, Any]] = None
) -> PerformanceAlert:
    """Create a performance alert"""
    import time
    
    # Determine alert level
    ratio = value / threshold
    if ratio > 2.0:
        level = AlertLevel.CRITICAL
    elif ratio > 1.5:
        level = AlertLevel.ERROR
    elif ratio > 1.2:
        level = AlertLevel.WARNING
    else:
        level = AlertLevel.INFO
    
    return PerformanceAlert(
        alert_id=f"{metric_type.value}_{int(time.time())}",
        level=level,
        metric_type=metric_type,
        message=f"{metric_type.value} exceeded threshold: {value:.2f} > {threshold}",
        value=value,
        threshold=threshold,
        timestamp=datetime.now(),
        context=context or {}
    )


def is_metric_above_threshold(metric: PerformanceMetric, thresholds: Dict[MetricType, float]) -> bool:
    """Check if metric exceeds configured threshold"""
    threshold = thresholds.get(metric.metric_type)
    return threshold is not None and metric.value > threshold
