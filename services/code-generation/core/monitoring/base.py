"""
Base classes and types for monitoring system
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringStatus(Enum):
    """Monitoring component status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class Metric:
    """Represents a single metric measurement"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    description: str = ""

@dataclass
class Alert:
    """Represents a monitoring alert"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    metric_name: str
    condition: str
    threshold: float
    current_value: float
    status: str = "active"
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    notification_channels: List[str] = field(default_factory=list)

@dataclass
class HealthCheck:
    """Represents a health check result"""
    component: str
    status: MonitoringStatus
    message: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceProfile:
    """Performance profiling data"""
    function_name: str
    file_name: str
    line_number: int
    call_count: int
    total_time: float
    cumulative_time: float
    average_time: float
    max_time: float
    min_time: float

@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: List[float]
    uptime_seconds: float
    process_count: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ApplicationMetrics:
    """Application-level metrics"""
    active_connections: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    error_rate_percent: float
    schemas_processed: int
    code_generations: int
    active_workflows: int
    cache_hit_rate: float
    database_connections: int
    queue_size: int
    timestamp: datetime = field(default_factory=datetime.now)
