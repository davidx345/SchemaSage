"""
Phase 4: Advanced Features - Data Migration Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import uuid

class ETLStepType(str, Enum):
    EXTRACT = "extract"
    TRANSFORM = "transform"
    LOAD = "load"
    VALIDATE = "validate"
    CLEANSE = "cleanse"
    AGGREGATE = "aggregate"
    PARTITION = "partition"

class DataTransformationType(str, Enum):
    DATA_TYPE_CONVERSION = "data_type_conversion"
    VALUE_MAPPING = "value_mapping"
    DATA_CLEANSING = "data_cleansing"
    AGGREGATION = "aggregation"
    DENORMALIZATION = "denormalization"
    NORMALIZATION = "normalization"
    CALCULATED_FIELD = "calculated_field"
    DATA_VALIDATION = "data_validation"

class SyncStrategy(str, Enum):
    FULL_REFRESH = "full_refresh"
    INCREMENTAL = "incremental"
    DELTA = "delta"
    CDC = "change_data_capture"
    TIMESTAMP_BASED = "timestamp_based"
    LOG_BASED = "log_based"

class ETLPipeline(BaseModel):
    """ETL pipeline for data migration."""
    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    name: str
    description: Optional[str] = None
    
    # Source and target
    source_connection_id: str
    target_connection_id: str
    
    # Pipeline configuration
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression
    is_active: bool = True
    
    # Performance settings
    batch_size: int = 10000
    parallel_workers: int = 4
    memory_limit_mb: int = 1024
    timeout_minutes: int = 60
    
    # Data validation
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    error_threshold_percent: float = 1.0
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_executed: Optional[datetime] = None
    execution_count: int = 0

class DataTransformation(BaseModel):
    """Data transformation configuration."""
    transformation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    step_order: int
    name: str
    transformation_type: DataTransformationType
    
    # Source configuration
    source_table: str
    source_columns: List[str] = Field(default_factory=list)
    
    # Target configuration
    target_table: str
    target_columns: List[str] = Field(default_factory=list)
    
    # Transformation logic
    transformation_logic: Dict[str, Any] = Field(default_factory=dict)
    sql_expression: Optional[str] = None
    python_code: Optional[str] = None
    
    # Validation
    pre_conditions: List[str] = Field(default_factory=list)
    post_conditions: List[str] = Field(default_factory=list)
    
    # Error handling
    on_error: str = "skip"  # skip, fail, log
    error_table: Optional[str] = None

class DataMapping(BaseModel):
    """Data type and value mapping configuration."""
    mapping_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transformation_id: str
    
    # Column mapping
    source_column: str
    target_column: str
    
    # Data type mapping
    source_data_type: str
    target_data_type: str
    
    # Value mapping
    value_mappings: Dict[str, str] = Field(default_factory=dict)
    default_value: Optional[str] = None
    null_handling: str = "preserve"  # preserve, default, skip
    
    # Validation rules
    validation_pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: List[str] = Field(default_factory=list)

class LargeDatasetStrategy(BaseModel):
    """Strategy for migrating large datasets."""
    strategy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    table_name: str
    estimated_rows: int
    estimated_size_gb: float
    
    # Partitioning strategy
    partition_column: Optional[str] = None
    partition_size: int = 1000000  # rows per partition
    parallel_partitions: int = 4
    
    # Chunking strategy
    chunk_size: int = 50000
    chunk_overlap: int = 0
    
    # Performance optimization
    use_bulk_insert: bool = True
    disable_constraints: bool = True
    disable_indexes: bool = True
    use_compression: bool = True
    
    # Monitoring
    progress_tracking: bool = True
    checkpoint_frequency: int = 100000  # rows
    
    # Recovery
    resume_on_failure: bool = True
    max_retries: int = 3

class IncrementalSync(BaseModel):
    """Incremental synchronization configuration."""
    sync_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    table_name: str
    strategy: SyncStrategy
    
    # Tracking configuration
    tracking_column: str  # timestamp, sequence, hash
    tracking_column_type: str = "timestamp"
    last_sync_value: Optional[str] = None
    
    # Change detection
    change_detection_method: str = "timestamp"  # timestamp, hash, log
    deleted_records_handling: str = "soft_delete"  # soft_delete, hard_delete, ignore
    
    # Conflict resolution
    conflict_resolution: str = "source_wins"  # source_wins, target_wins, manual
    
    # Performance
    sync_window_hours: int = 24
    batch_size: int = 10000
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = None
    total_synced_records: int = 0

class DataQualityRule(BaseModel):
    """Data quality validation rule."""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    table_name: str
    column_name: Optional[str] = None
    
    # Rule definition
    rule_name: str
    rule_type: str  # not_null, unique, range, pattern, custom
    rule_expression: str
    severity: str = "error"  # error, warning, info
    
    # Thresholds
    failure_threshold_percent: float = 0.0
    warning_threshold_percent: float = 5.0
    
    # Actions
    on_failure: str = "log"  # log, stop, quarantine
    quarantine_table: Optional[str] = None
    
    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ETLExecution(BaseModel):
    """ETL pipeline execution tracking."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    
    # Execution metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled
    
    # Progress tracking
    total_steps: int = 0
    completed_steps: int = 0
    current_step: Optional[str] = None
    
    # Data metrics
    total_source_records: int = 0
    total_target_records: int = 0
    records_processed: int = 0
    records_failed: int = 0
    records_skipped: int = 0
    
    # Performance metrics
    processing_rate_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Data quality results
    quality_check_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Logs
    execution_log: List[str] = Field(default_factory=list)
