"""
Data models for schema drift detection system
"""

from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from models.schemas import SchemaResponse, TableInfo, ColumnInfo


class ChangeType(Enum):
    """Types of schema changes"""
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed" 
    TABLE_RENAMED = "table_renamed"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_MODIFIED = "column_modified"
    COLUMN_RENAMED = "column_renamed"
    INDEX_ADDED = "index_added"
    INDEX_REMOVED = "index_removed"
    CONSTRAINT_ADDED = "constraint_added"
    CONSTRAINT_REMOVED = "constraint_removed"
    PRIMARY_KEY_ADDED = "primary_key_added"
    PRIMARY_KEY_REMOVED = "primary_key_removed"
    FOREIGN_KEY_ADDED = "foreign_key_added"
    FOREIGN_KEY_REMOVED = "foreign_key_removed"
    UNIQUE_CONSTRAINT_ADDED = "unique_constraint_added"
    UNIQUE_CONSTRAINT_REMOVED = "unique_constraint_removed"


class ChangeSeverity(Enum):
    """Severity levels for schema changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    DISCORD = "discord"


@dataclass
class SchemaChange:
    """Represents a detected schema change"""
    change_id: str
    change_type: ChangeType
    severity: ChangeSeverity
    object_name: str
    details: Dict[str, Any]
    detected_at: datetime = field(default_factory=datetime.now)
    database_name: str = ""
    table_name: str = ""
    column_name: str = ""
    old_value: Any = None
    new_value: Any = None
    impact_analysis: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'change_id': self.change_id,
            'change_type': self.change_type.value,
            'severity': self.severity.value,
            'object_name': self.object_name,
            'details': self.details,
            'detected_at': self.detected_at.isoformat(),
            'database_name': self.database_name,
            'table_name': self.table_name,
            'column_name': self.column_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'impact_analysis': self.impact_analysis
        }


@dataclass
class SchemaSnapshot:
    """Represents a schema snapshot at a point in time"""
    snapshot_id: str
    schema_hash: str
    schema: SchemaResponse
    captured_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'snapshot_id': self.snapshot_id,
            'schema_hash': self.schema_hash,
            'captured_at': self.captured_at.isoformat(),
            'metadata': self.metadata,
            'table_count': len(self.schema.tables),
            'relationship_count': len(self.schema.relationships or [])
        }


@dataclass
class DriftAlert:
    """Represents an alert triggered by schema drift"""
    alert_id: str
    changes: List[SchemaChange]
    severity: ChangeSeverity
    message: str
    channels: List[AlertChannel]
    triggered_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def acknowledge(self, user: str):
        """Acknowledge the alert"""
        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'alert_id': self.alert_id,
            'changes': [change.to_dict() for change in self.changes],
            'severity': self.severity.value,
            'message': self.message,
            'channels': [channel.value for channel in self.channels],
            'triggered_at': self.triggered_at.isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


@dataclass
class MonitoringConfig:
    """Configuration for schema monitoring"""
    check_interval: int = 300  # seconds
    max_snapshots: int = 100
    severity_thresholds: Dict[str, int] = field(default_factory=lambda: {
        'critical': 1,  # Any critical change triggers alert
        'high': 3,      # 3 high severity changes
        'medium': 5,    # 5 medium severity changes
        'low': 10       # 10 low severity changes
    })
    alert_channels: List[AlertChannel] = field(default_factory=list)
    ignored_changes: Set[ChangeType] = field(default_factory=set)
    table_patterns: Optional[List[str]] = None  # Regex patterns for tables to monitor
    excluded_tables: Set[str] = field(default_factory=set)
    retention_days: int = 30
    enable_impact_analysis: bool = True
    auto_acknowledge_low: bool = False
    
    def should_monitor_table(self, table_name: str) -> bool:
        """Check if table should be monitored"""
        if table_name in self.excluded_tables:
            return False
        
        if self.table_patterns:
            import re
            return any(re.match(pattern, table_name) for pattern in self.table_patterns)
        
        return True
    
    def should_ignore_change(self, change_type: ChangeType) -> bool:
        """Check if change type should be ignored"""
        return change_type in self.ignored_changes


@dataclass
class ImpactAnalysis:
    """Analysis of the impact of schema changes"""
    affected_queries: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    migration_required: bool = False
    estimated_downtime: Optional[str] = None
    rollback_difficulty: str = "low"  # low, medium, high
    dependencies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'affected_queries': self.affected_queries,
            'breaking_changes': self.breaking_changes,
            'migration_required': self.migration_required,
            'estimated_downtime': self.estimated_downtime,
            'rollback_difficulty': self.rollback_difficulty,
            'dependencies': self.dependencies,
            'recommendations': self.recommendations
        }


@dataclass
class DatabaseConnection:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    driver: str = "postgresql"
    ssl_mode: str = "prefer"
    connection_timeout: int = 30
    query_timeout: int = 60
    
    def get_connection_string(self) -> str:
        """Generate connection string"""
        if self.driver == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        elif self.driver == "mysql":
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.driver == "sqlite":
            return f"sqlite:///{self.database}"
        else:
            raise ValueError(f"Unsupported database driver: {self.driver}")


@dataclass
class ComparisonResult:
    """Result of comparing two schemas"""
    changes: List[SchemaChange]
    summary: Dict[str, int]
    total_changes: int = 0
    severity_breakdown: Dict[ChangeSeverity, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate totals after initialization"""
        self.total_changes = len(self.changes)
        
        # Calculate severity breakdown
        severity_counts = {}
        for severity in ChangeSeverity:
            severity_counts[severity] = 0
        
        for change in self.changes:
            severity_counts[change.severity] += 1
        
        self.severity_breakdown = severity_counts
        
        # Update summary
        if not self.summary:
            change_type_counts = {}
            for change_type in ChangeType:
                change_type_counts[change_type.value] = 0
            
            for change in self.changes:
                change_type_counts[change.change_type.value] += 1
            
            self.summary = change_type_counts
    
    def has_critical_changes(self) -> bool:
        """Check if there are any critical changes"""
        return self.severity_breakdown.get(ChangeSeverity.CRITICAL, 0) > 0
    
    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes"""
        breaking_change_types = {
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.PRIMARY_KEY_REMOVED,
            ChangeType.FOREIGN_KEY_REMOVED
        }
        
        return any(change.change_type in breaking_change_types for change in self.changes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'changes': [change.to_dict() for change in self.changes],
            'summary': self.summary,
            'total_changes': self.total_changes,
            'severity_breakdown': {k.value: v for k, v in self.severity_breakdown.items()},
            'has_critical_changes': self.has_critical_changes(),
            'has_breaking_changes': self.has_breaking_changes()
        }
