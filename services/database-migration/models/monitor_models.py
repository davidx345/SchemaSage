"""
Models for real-time migration monitoring endpoint.
Tracks migration progress, performance metrics, and issues.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MigrationStatus(str, Enum):
    """Current status of migration operation"""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    SCHEMA_MIGRATION = "schema_migration"
    DATA_MIGRATION = "data_migration"
    VALIDATION = "validation"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class HealthStatus(str, Enum):
    """Health status of migration process"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DEGRADED = "degraded"


class IssueType(str, Enum):
    """Type of issue encountered during migration"""
    CONNECTIVITY = "connectivity"
    PERFORMANCE = "performance"
    DATA_INTEGRITY = "data_integrity"
    SCHEMA_MISMATCH = "schema_mismatch"
    RESOURCE_LIMIT = "resource_limit"
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    OTHER = "other"


class IssueSeverity(str, Enum):
    """Severity level of migration issues"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitorRequest(BaseModel):
    """Request to monitor migration progress"""
    migration_id: str = Field(..., description="Unique identifier for the migration job")
    include_metrics: bool = Field(default=True, description="Include performance metrics")
    include_logs: bool = Field(default=False, description="Include recent log entries")
    refresh_interval: Optional[int] = Field(
        default=5,
        ge=1,
        le=300,
        description="Refresh interval in seconds for real-time monitoring"
    )


class ProgressMetrics(BaseModel):
    """Detailed progress metrics for migration"""
    total_tables: int = Field(..., ge=0, description="Total number of tables to migrate")
    completed_tables: int = Field(..., ge=0, description="Number of tables completed")
    failed_tables: int = Field(default=0, ge=0, description="Number of tables that failed")
    total_rows: int = Field(..., ge=0, description="Total number of rows to migrate")
    migrated_rows: int = Field(..., ge=0, description="Number of rows migrated")
    failed_rows: int = Field(default=0, ge=0, description="Number of rows that failed")
    percentage_complete: float = Field(..., ge=0.0, le=100.0, description="Overall completion percentage")
    current_table: Optional[str] = Field(None, description="Currently processing table")
    estimated_time_remaining: Optional[int] = Field(None, ge=0, description="Estimated seconds remaining")


class PerformanceMetrics(BaseModel):
    """Performance metrics for migration operation"""
    rows_per_second: float = Field(..., ge=0.0, description="Current throughput in rows/second")
    avg_rows_per_second: float = Field(..., ge=0.0, description="Average throughput in rows/second")
    peak_rows_per_second: float = Field(..., ge=0.0, description="Peak throughput in rows/second")
    cpu_usage_percent: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    memory_usage_mb: float = Field(..., ge=0.0, description="Memory usage in MB")
    network_throughput_mbps: float = Field(..., ge=0.0, description="Network throughput in Mbps")
    source_connection_pool: int = Field(..., ge=0, description="Active source connections")
    target_connection_pool: int = Field(..., ge=0, description="Active target connections")
    error_rate: float = Field(..., ge=0.0, le=100.0, description="Error rate percentage")


class MigrationIssue(BaseModel):
    """Issue encountered during migration"""
    issue_id: str = Field(..., description="Unique identifier for the issue")
    timestamp: datetime = Field(..., description="When the issue occurred")
    type: IssueType = Field(..., description="Type of issue")
    severity: IssueSeverity = Field(..., description="Severity level")
    table_name: Optional[str] = Field(None, description="Table where issue occurred")
    description: str = Field(..., description="Detailed description of the issue")
    affected_rows: Optional[int] = Field(None, ge=0, description="Number of rows affected")
    resolution: Optional[str] = Field(None, description="Suggested resolution")
    resolved: bool = Field(default=False, description="Whether issue has been resolved")


class ResourceUtilization(BaseModel):
    """Resource utilization metrics"""
    source_db_connections: int = Field(..., ge=0, description="Active source database connections")
    target_db_connections: int = Field(..., ge=0, description="Active target database connections")
    worker_threads: int = Field(..., ge=0, description="Number of active worker threads")
    queue_depth: int = Field(..., ge=0, description="Number of items in processing queue")
    temp_storage_mb: float = Field(..., ge=0.0, description="Temporary storage used in MB")


class LogEntry(BaseModel):
    """Recent log entry from migration"""
    timestamp: datetime = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level (INFO, WARNING, ERROR, etc)")
    message: str = Field(..., description="Log message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


class MonitorSummary(BaseModel):
    """Summary of current monitoring session"""
    migration_id: str = Field(..., description="Migration job identifier")
    status: MigrationStatus = Field(..., description="Current migration status")
    health: HealthStatus = Field(..., description="Overall health status")
    start_time: datetime = Field(..., description="When migration started")
    current_time: datetime = Field(..., description="Current timestamp")
    elapsed_time_seconds: int = Field(..., ge=0, description="Elapsed time in seconds")
    estimated_total_time_seconds: Optional[int] = Field(None, ge=0, description="Estimated total time")


class MonitorResponse(BaseModel):
    """Response from migration monitoring endpoint"""
    summary: MonitorSummary = Field(..., description="Migration summary information")
    progress: ProgressMetrics = Field(..., description="Detailed progress metrics")
    performance: Optional[PerformanceMetrics] = Field(None, description="Performance metrics if requested")
    issues: List[MigrationIssue] = Field(default_factory=list, description="List of issues encountered")
    resources: ResourceUtilization = Field(..., description="Resource utilization metrics")
    logs: Optional[List[LogEntry]] = Field(None, description="Recent log entries if requested")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for optimization or issue resolution"
    )
    next_refresh: Optional[datetime] = Field(None, description="Suggested next refresh time")
