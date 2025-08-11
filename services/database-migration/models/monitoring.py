"""
Phase 4: Monitoring & Alerting Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime, timedelta
import uuid

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class MetricType(str, Enum):
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    CAPACITY = "capacity"
    SECURITY = "security"
    DATA_QUALITY = "data_quality"
    BUSINESS = "business"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    SMS = "sms"
    PAGERDUTY = "pagerduty"
    DISCORD = "discord"

class MonitoringRule(BaseModel):
    """Monitoring rule configuration."""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    connection_id: Optional[str] = None
    
    # Rule definition
    name: str
    description: str
    metric_type: MetricType
    is_active: bool = True
    
    # Conditions
    metric_name: str
    operator: str  # >, <, >=, <=, ==, !=, contains, not_contains
    threshold_value: Union[float, str]
    evaluation_window_minutes: int = 5
    
    # Advanced conditions
    consecutive_violations: int = 1
    percentage_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)
    baseline_comparison: bool = False
    seasonal_adjustment: bool = False
    
    # Alert configuration
    alert_severity: AlertSeverity = AlertSeverity.MEDIUM
    cooldown_minutes: int = 60
    auto_resolve: bool = True
    auto_resolve_timeout_minutes: int = 1440  # 24 hours
    
    # Notifications
    notification_channels: List[NotificationChannel] = Field(default_factory=list)
    escalation_enabled: bool = False
    escalation_timeout_minutes: int = 30
    
    # Custom SQL for complex rules
    custom_sql: Optional[str] = None
    expected_result_type: str = "scalar"  # scalar, count, boolean
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    last_evaluated: Optional[datetime] = None

class Alert(BaseModel):
    """System alert instance."""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    workspace_id: str
    connection_id: Optional[str] = None
    
    # Alert details
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    
    # Trigger information
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    trigger_value: Union[float, str]
    threshold_value: Union[float, str]
    evaluation_window: timedelta
    
    # Context
    affected_resources: List[str] = Field(default_factory=list)
    related_metrics: Dict[str, Any] = Field(default_factory=dict)
    environmental_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Resolution
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    auto_resolved: bool = False
    
    # Acknowledgment
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledgment_notes: Optional[str] = None
    
    # Impact assessment
    business_impact: str = "unknown"  # none, low, medium, high, critical
    affected_users: int = 0
    estimated_revenue_impact: float = 0.0
    
    # Incident tracking
    incident_id: Optional[str] = None
    related_alerts: List[str] = Field(default_factory=list)
    parent_alert_id: Optional[str] = None
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    notification_count: int = 0
    escalation_level: int = 0

class MonitoringDashboard(BaseModel):
    """Monitoring dashboard configuration."""
    dashboard_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    
    # Dashboard details
    name: str
    description: str
    category: str = "general"
    is_public: bool = False
    
    # Layout
    layout: Dict[str, Any] = Field(default_factory=dict)
    widgets: List[Dict[str, Any]] = Field(default_factory=list)
    refresh_interval_seconds: int = 300
    
    # Access control
    owner_id: str
    shared_with: List[str] = Field(default_factory=list)
    team_access: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    view_count: int = 0
    last_viewed: Optional[datetime] = None

class MetricDataPoint(BaseModel):
    """Individual metric data point."""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    connection_id: Optional[str] = None
    
    # Metric identification
    metric_name: str
    metric_type: MetricType
    source: str
    
    # Value
    value: Union[float, str, bool]
    unit: Optional[str] = None
    
    # Dimensions/Tags
    tags: Dict[str, str] = Field(default_factory=dict)
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    
    # Context
    query_hash: Optional[str] = None
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Quality
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)
    is_anomaly: bool = False
    anomaly_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class PerformanceBaseline(BaseModel):
    """Performance baseline for comparison."""
    baseline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    connection_id: str
    
    # Baseline definition
    name: str
    description: str
    metric_name: str
    
    # Time period
    baseline_start: datetime
    baseline_end: datetime
    data_points_count: int
    
    # Statistical measures
    mean_value: float
    median_value: float
    percentile_95: float
    percentile_99: float
    standard_deviation: float
    
    # Seasonal patterns
    hourly_patterns: Dict[int, float] = Field(default_factory=dict)  # hour -> avg value
    daily_patterns: Dict[int, float] = Field(default_factory=dict)   # day_of_week -> avg value
    monthly_patterns: Dict[int, float] = Field(default_factory=dict) # month -> avg value
    
    # Thresholds derived from baseline
    warning_threshold: float
    critical_threshold: float
    
    # Validity
    is_active: bool = True
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.95)
    next_recalculation: datetime
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class NotificationTemplate(BaseModel):
    """Notification message template."""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    
    # Template details
    name: str
    description: str
    channel: NotificationChannel
    alert_severity: AlertSeverity
    
    # Message content
    subject_template: str
    body_template: str
    
    # Variables
    available_variables: List[str] = Field(default_factory=list)
    required_variables: List[str] = Field(default_factory=list)
    
    # Formatting
    message_format: str = "text"  # text, html, markdown
    include_charts: bool = False
    include_runbook_links: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0

class HealthCheck(BaseModel):
    """System health check definition."""
    health_check_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    connection_id: Optional[str] = None
    
    # Check definition
    name: str
    description: str
    check_type: str  # connectivity, query_performance, data_freshness, custom
    
    # Check configuration
    check_sql: Optional[str] = None
    expected_result: Optional[Union[int, float, str]] = None
    timeout_seconds: int = 30
    
    # Scheduling
    interval_minutes: int = 5
    is_enabled: bool = True
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # other health check IDs
    
    # Results tracking
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    # Status
    current_status: str = "unknown"  # healthy, warning, critical, unknown
    consecutive_failures: int = 0
    uptime_percentage: float = Field(ge=0.0, le=100.0, default=100.0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class HealthCheckResult(BaseModel):
    """Health check execution result."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    health_check_id: str
    
    # Execution details
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: float
    
    # Results
    status: str  # healthy, warning, critical, error
    success: bool
    error_message: Optional[str] = None
    
    # Metrics
    response_time_ms: float
    result_value: Optional[Union[int, float, str]] = None
    
    # Context
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    system_metrics: Dict[str, Any] = Field(default_factory=dict)

class Incident(BaseModel):
    """Incident tracking."""
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    
    # Incident details
    title: str
    description: str
    severity: AlertSeverity
    status: str = "open"  # open, investigating, resolved, closed
    
    # Timeline
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    team_assigned: Optional[str] = None
    
    # Related data
    related_alerts: List[str] = Field(default_factory=list)
    root_cause_alerts: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    
    # Impact
    business_impact: str = "unknown"
    affected_users_count: int = 0
    estimated_revenue_impact: float = 0.0
    
    # Resolution
    resolution_summary: Optional[str] = None
    root_cause: Optional[str] = None
    action_items: List[str] = Field(default_factory=list)
    
    # Communication
    public_status_page_update: bool = False
    customer_communication_sent: bool = False
    
    # Metadata
    created_by: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
