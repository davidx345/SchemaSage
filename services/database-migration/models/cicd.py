"""
CI/CD Integration Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class CIPlatform(str, Enum):
    GITHUB_ACTIONS = "github_actions"
    JENKINS = "jenkins"
    GITLAB_CI = "gitlab_ci"
    AZURE_PIPELINES = "azure_pipelines"
    CIRCLECI = "circleci"
    TRAVIS_CI = "travis_ci"

class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

class TestType(str, Enum):
    MIGRATION_VALIDATION = "migration_validation"
    SCHEMA_COMPATIBILITY = "schema_compatibility"
    DATA_INTEGRITY = "data_integrity"
    PERFORMANCE = "performance"
    ROLLBACK = "rollback"
    INTEGRATION = "integration"

class DeploymentEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

class CIPipeline(BaseModel):
    """CI/CD pipeline configuration."""
    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    name: str
    platform: CIPlatform
    repository_id: str
    
    # Configuration
    config_file_path: str = ".github/workflows/migration.yml"
    trigger_events: List[str] = Field(default_factory=lambda: ["push", "pull_request"])
    target_branches: List[str] = Field(default_factory=lambda: ["main", "develop"])
    
    # Pipeline stages
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    secrets: List[str] = Field(default_factory=list)
    
    # Settings
    is_active: bool = True
    auto_deploy: bool = False
    require_approval: bool = True
    parallel_execution: bool = False
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: Optional[datetime] = None

class PipelineExecution(BaseModel):
    """CI/CD pipeline execution tracking."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    workspace_id: str
    
    # Trigger info
    trigger_type: str  # push, pull_request, manual, scheduled
    trigger_user: Optional[str] = None
    commit_sha: str
    branch_name: str
    
    # Execution details
    status: PipelineStatus = PipelineStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Pipeline data
    job_executions: List[str] = Field(default_factory=list)  # job execution IDs
    logs_url: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Results
    tests_passed: int = 0
    tests_failed: int = 0
    migrations_validated: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class JobExecution(BaseModel):
    """Individual job execution within a pipeline."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    job_name: str
    job_type: str  # test, build, deploy, validate
    
    # Status
    status: PipelineStatus = PipelineStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Configuration
    environment: DeploymentEnvironment
    configuration: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    
    # Results
    output_logs: List[str] = Field(default_factory=list)
    error_logs: List[str] = Field(default_factory=list)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None

class MigrationTest(BaseModel):
    """Automated migration testing configuration."""
    test_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    migration_plan_id: str
    test_name: str
    test_type: TestType
    
    # Test configuration
    test_database_config: Dict[str, Any]
    test_data_set: Optional[str] = None
    expected_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation rules
    validation_queries: List[str] = Field(default_factory=list)
    performance_thresholds: Dict[str, float] = Field(default_factory=dict)
    data_integrity_checks: List[str] = Field(default_factory=list)
    
    # Settings
    is_active: bool = True
    run_on_pr: bool = True
    run_on_merge: bool = True
    timeout_minutes: int = 30
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TestExecution(BaseModel):
    """Migration test execution results."""
    test_execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    job_execution_id: str
    
    # Execution details
    status: PipelineStatus = PipelineStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Test environment
    test_database_url: str
    test_data_size: Optional[int] = None
    environment_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Results
    passed: bool = False
    error_message: Optional[str] = None
    validation_results: List[Dict[str, Any]] = Field(default_factory=list)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # Detailed results
    migration_log: List[str] = Field(default_factory=list)
    rollback_tested: bool = False
    rollback_successful: bool = False
    data_integrity_verified: bool = False

class GitHubAction(BaseModel):
    """GitHub Actions specific configuration."""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    workflow_file: str = ".github/workflows/schemasage-migration.yml"
    
    # Action configuration
    runner_os: str = "ubuntu-latest"
    python_version: str = "3.11"
    node_version: Optional[str] = "18"
    
    # Steps configuration
    setup_steps: List[Dict[str, Any]] = Field(default_factory=list)
    test_steps: List[Dict[str, Any]] = Field(default_factory=list)
    deployment_steps: List[Dict[str, Any]] = Field(default_factory=list)
    
    # GitHub specific
    secrets_required: List[str] = Field(default_factory=list)
    permissions: Dict[str, str] = Field(default_factory=dict)
    concurrency_group: Optional[str] = None

class JenkinsJob(BaseModel):
    """Jenkins job configuration."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    job_name: str
    jenkins_url: str
    
    # Job configuration
    job_type: str = "pipeline"  # freestyle, pipeline, multibranch
    jenkinsfile_path: str = "Jenkinsfile"
    build_triggers: List[str] = Field(default_factory=list)
    
    # Parameters
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    
    # Build configuration
    node_label: Optional[str] = None
    timeout_minutes: int = 60
    concurrent_builds: bool = False
    
    # Notifications
    email_notifications: List[str] = Field(default_factory=list)
    slack_webhook: Optional[str] = None

class DeploymentTarget(BaseModel):
    """Deployment target configuration."""
    target_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    name: str
    environment: DeploymentEnvironment
    
    # Target configuration
    database_connection_id: str
    deployment_strategy: str = "blue_green"  # blue_green, rolling, recreate
    
    # Safety settings
    require_approval: bool = True
    auto_rollback: bool = True
    health_check_url: Optional[str] = None
    health_check_timeout: int = 300
    
    # Deployment configuration
    pre_deployment_scripts: List[str] = Field(default_factory=list)
    post_deployment_scripts: List[str] = Field(default_factory=list)
    rollback_scripts: List[str] = Field(default_factory=list)
    
    # Monitoring
    monitoring_enabled: bool = True
    alert_on_failure: bool = True
    notification_channels: List[str] = Field(default_factory=list)

class PipelineTemplate(BaseModel):
    """Reusable pipeline templates."""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    platform: CIPlatform
    
    # Template content
    template_config: Dict[str, Any]
    variables: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    category: str = "migration"  # migration, testing, deployment
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    
    # Usage
    usage_count: int = 0
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: Optional[datetime] = None

class IntegrationAPI(BaseModel):
    """Pipeline integration API configuration."""
    api_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    api_name: str
    endpoint_url: str
    
    # Authentication
    auth_type: str = "bearer"  # bearer, basic, api_key
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Configuration
    webhook_events: List[str] = Field(default_factory=list)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    
    # Status
    is_active: bool = True
    last_used: Optional[datetime] = None
    success_rate: float = 0.0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
