"""
Data models for workflow automation system
"""

from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from models.schemas import SchemaResponse, TableInfo, ColumnInfo, Relationship


class WorkflowStatus(Enum):
    """Workflow execution status"""
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Types of workflow tasks"""
    SCHEMA_ANALYSIS = "schema_analysis"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    NOTIFICATION = "notification"
    DATA_TRANSFORMATION = "data_transformation"
    INTEGRATION = "integration"
    APPROVAL = "approval"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    WEBHOOK = "webhook"
    SCRIPT = "script"
    FILE_OPERATION = "file_operation"
    DATABASE_OPERATION = "database_operation"


class TriggerType(Enum):
    """Types of workflow triggers"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    SCHEMA_CHANGE = "schema_change"
    FILE_UPLOAD = "file_upload"
    API_REQUEST = "api_request"
    WEBHOOK = "webhook"
    EMAIL = "email"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ConditionOperator(Enum):
    """Operators for conditional logic"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX_MATCH = "regex_match"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class WorkflowCondition:
    """Represents a condition for conditional tasks"""
    field: str
    operator: ConditionOperator
    value: Any = None
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context"""
        field_value = self._get_field_value(context, self.field)
        
        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == ConditionOperator.GREATER_THAN:
            return field_value > self.value
        elif self.operator == ConditionOperator.LESS_THAN:
            return field_value < self.value
        elif self.operator == ConditionOperator.GREATER_EQUAL:
            return field_value >= self.value
        elif self.operator == ConditionOperator.LESS_EQUAL:
            return field_value <= self.value
        elif self.operator == ConditionOperator.CONTAINS:
            return self.value in field_value
        elif self.operator == ConditionOperator.NOT_CONTAINS:
            return self.value not in field_value
        elif self.operator == ConditionOperator.IN:
            return field_value in self.value
        elif self.operator == ConditionOperator.NOT_IN:
            return field_value not in self.value
        elif self.operator == ConditionOperator.IS_NULL:
            return field_value is None
        elif self.operator == ConditionOperator.IS_NOT_NULL:
            return field_value is not None
        elif self.operator == ConditionOperator.REGEX_MATCH:
            import re
            return bool(re.match(str(self.value), str(field_value)))
        
        return False
    
    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get field value from context using dot notation"""
        parts = field_path.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value


@dataclass
class WorkflowTask:
    """Represents a single task in a workflow"""
    task_id: str
    name: str
    task_type: TaskType
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    retry_count: int = 0
    retry_delay: int = 60  # seconds
    conditions: List[WorkflowCondition] = field(default_factory=list)
    parallel_tasks: List[str] = field(default_factory=list)  # For parallel execution
    on_success: Optional[str] = None  # Next task on success
    on_failure: Optional[str] = None  # Next task on failure
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if task should be executed based on conditions"""
        if not self.conditions:
            return True
        
        return all(condition.evaluate(context) for condition in self.conditions)


@dataclass
class WorkflowTrigger:
    """Defines when a workflow should be triggered"""
    trigger_type: TriggerType
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    # Schedule configuration for SCHEDULED triggers
    schedule_cron: Optional[str] = None
    
    # Event configuration for event-based triggers
    event_filters: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    """Defines a workflow structure"""
    workflow_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def get_task_by_id(self, task_id: str) -> Optional[WorkflowTask]:
        """Get task by ID"""
        return next((task for task in self.tasks if task.task_id == task_id), None)


@dataclass
class TaskExecution:
    """Represents execution state of a single task"""
    task_id: str
    execution_id: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Any = None
    retry_count: int = 0
    logs: List[str] = field(default_factory=list)
    
    def duration(self) -> Optional[float]:
        """Get task execution duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class WorkflowExecution:
    """Represents a workflow execution instance"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    task_executions: Dict[str, TaskExecution] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    triggered_by: Optional[str] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    
    def duration(self) -> Optional[float]:
        """Get workflow execution duration in seconds"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_task_execution(self, task_id: str) -> Optional[TaskExecution]:
        """Get task execution by task ID"""
        return self.task_executions.get(task_id)
    
    def add_task_execution(self, task_execution: TaskExecution):
        """Add task execution"""
        self.task_executions[task_execution.task_id] = task_execution


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration: float = 0.0
    last_execution: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        if self.total_executions == 0:
            return 0.0
        return self.failed_executions / self.total_executions


@dataclass
class WorkflowTemplate:
    """Template for creating workflows"""
    template_id: str
    name: str
    description: str
    category: str
    template_data: Dict[str, Any]
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def instantiate(self, parameters: Dict[str, Any]) -> WorkflowDefinition:
        """Create workflow instance from template"""
        # This would substitute template parameters
        # For now, return basic workflow structure
        workflow_id = str(uuid.uuid4())
        
        return WorkflowDefinition(
            workflow_id=workflow_id,
            name=f"{self.name} Instance",
            description=self.description,
            tasks=[],  # Would be populated from template
            metadata={'template_id': self.template_id, 'parameters': parameters}
        )


@dataclass
class WorkflowEvent:
    """Represents a workflow-related event"""
    event_id: str
    event_type: str
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None


@dataclass
class ApprovalRequest:
    """Represents an approval request in workflow"""
    request_id: str
    workflow_id: str
    execution_id: str
    task_id: str
    title: str
    description: str
    approvers: List[str]
    required_approvals: int = 1
    current_approvals: int = 0
    approved_by: List[str] = field(default_factory=list)
    rejected_by: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, approved, rejected, expired
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    approval_data: Dict[str, Any] = field(default_factory=dict)
    
    def is_approved(self) -> bool:
        """Check if request is approved"""
        return self.current_approvals >= self.required_approvals
    
    def is_expired(self) -> bool:
        """Check if request is expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


@dataclass
class NotificationConfig:
    """Configuration for workflow notifications"""
    channels: List[str] = field(default_factory=list)  # email, slack, webhook, etc.
    recipients: List[str] = field(default_factory=list)
    template: Optional[str] = None
    conditions: List[WorkflowCondition] = field(default_factory=list)
    
    def should_notify(self, context: Dict[str, Any]) -> bool:
        """Check if notification should be sent"""
        if not self.conditions:
            return True
        return all(condition.evaluate(context) for condition in self.conditions)


@dataclass
class IntegrationConfig:
    """Configuration for external integrations"""
    integration_type: str  # api, database, file_system, cloud_storage, etc.
    endpoint: Optional[str] = None
    authentication: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationRule:
    """Validation rule for workflow data"""
    rule_id: str
    name: str
    description: str
    rule_type: str  # schema, data, business, custom
    configuration: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # error, warning, info
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate data against rule"""
        # Implementation would depend on rule type
        return True, []


@dataclass
class DeploymentConfig:
    """Configuration for deployment tasks"""
    target_environment: str
    deployment_type: str  # direct, blue_green, canary, rolling
    rollback_enabled: bool = True
    pre_deployment_checks: List[str] = field(default_factory=list)
    post_deployment_checks: List[str] = field(default_factory=list)
    approval_required: bool = False
    notification_config: Optional[NotificationConfig] = None
