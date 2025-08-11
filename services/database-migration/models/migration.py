"""
Migration Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class MigrationStepType(str, Enum):
    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    ALTER_TABLE = "alter_table"
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    MODIFY_COLUMN = "modify_column"
    CREATE_INDEX = "create_index"
    DROP_INDEX = "drop_index"
    ADD_CONSTRAINT = "add_constraint"
    DROP_CONSTRAINT = "drop_constraint"
    MIGRATE_DATA = "migrate_data"
    CUSTOM_SCRIPT = "custom_script"

class MigrationStep(BaseModel):
    """Individual migration step."""
    step_id: str
    step_type: MigrationStepType
    object_name: str
    sql_script: str
    rollback_script: Optional[str] = None
    dependencies: List[str] = []
    estimated_duration: Optional[int] = None  # seconds
    risk_level: str = "low"  # low, medium, high, critical
    validation_query: Optional[str] = None
    description: str = ""

class MigrationPlan(BaseModel):
    """Complete migration plan."""
    plan_id: str
    source_connection_id: str
    target_connection_id: str
    name: str
    description: Optional[str] = None
    steps: List[MigrationStep] = []
    total_estimated_duration: Optional[int] = None
    overall_risk_level: str = "low"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    status: str = "draft"  # draft, ready, running, completed, failed

class RiskAssessment(BaseModel):
    """Risk assessment for migration."""
    migration_id: str
    complexity_score: float = Field(ge=0.0, le=1.0)
    data_loss_risk: float = Field(ge=0.0, le=1.0)
    downtime_risk: float = Field(ge=0.0, le=1.0)
    performance_impact: float = Field(ge=0.0, le=1.0)
    breaking_changes: List[str] = []
    critical_warnings: List[str] = []
    recommendations: List[str] = []
    mitigation_strategies: List[str] = []
    overall_risk: str = "low"  # low, medium, high, critical

class MigrationExecution(BaseModel):
    """Migration execution tracking."""
    execution_id: str
    plan_id: str
    status: str = "pending"  # pending, running, completed, failed, rolled_back
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    completed_steps: List[str] = []
    failed_steps: List[str] = []
    execution_log: List[Dict[str, Any]] = []
    rollback_executed: bool = False
