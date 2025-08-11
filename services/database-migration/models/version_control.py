"""
Version Control Integration Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class VCSProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"

class BranchStatus(str, Enum):
    ACTIVE = "active"
    MERGED = "merged"
    DELETED = "deleted"
    STALE = "stale"

class ConflictType(str, Enum):
    SCHEMA_CONFLICT = "schema_conflict"
    DATA_TYPE_CONFLICT = "data_type_conflict"
    CONSTRAINT_CONFLICT = "constraint_conflict"
    INDEX_CONFLICT = "index_conflict"
    MIGRATION_ORDER_CONFLICT = "migration_order_conflict"

class MergeStrategy(str, Enum):
    AUTO_MERGE = "auto_merge"
    MANUAL_REVIEW = "manual_review"
    THREE_WAY_MERGE = "three_way_merge"
    OURS = "ours"
    THEIRS = "theirs"

class GitRepository(BaseModel):
    """Git repository configuration for schema versioning."""
    repo_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    provider: VCSProvider
    repository_url: str
    repository_name: str
    owner: str  # organization or user
    
    # Authentication
    access_token: Optional[str] = None
    ssh_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Configuration
    default_branch: str = "main"
    schema_path: str = "database/migrations"
    auto_sync: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync: Optional[datetime] = None
    
    # Permissions
    can_push: bool = True
    can_create_pr: bool = True
    can_merge: bool = False

class SchemaBranch(BaseModel):
    """Schema branch for version control."""
    branch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    repo_id: str
    branch_name: str
    base_branch: str = "main"
    status: BranchStatus = BranchStatus.ACTIVE
    
    # Branch metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_commit_sha: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    # Schema state
    migration_plans: List[str] = Field(default_factory=list)  # migration plan IDs
    schema_snapshot: Optional[Dict[str, Any]] = None
    
    # Protection settings
    is_protected: bool = False
    require_review: bool = True
    auto_delete_on_merge: bool = True

class SchemaCommit(BaseModel):
    """Schema change commit tracking."""
    commit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    branch_id: str
    commit_sha: str
    parent_commit_sha: Optional[str] = None
    
    # Commit metadata
    author_id: str
    committer_id: Optional[str] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Schema changes
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    migration_plan_id: Optional[str] = None
    files_changed: List[str] = Field(default_factory=list)
    
    # Impact analysis
    affected_tables: List[str] = Field(default_factory=list)
    risk_assessment: Optional[Dict[str, Any]] = None
    breaking_changes: List[str] = Field(default_factory=list)

class MergeConflict(BaseModel):
    """Schema merge conflict resolution."""
    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    source_branch_id: str
    target_branch_id: str
    conflict_type: ConflictType
    
    # Conflict details
    object_name: str  # table, column, etc.
    object_type: str
    source_state: Dict[str, Any]
    target_state: Dict[str, Any]
    base_state: Optional[Dict[str, Any]] = None
    
    # Resolution
    status: str = "unresolved"  # unresolved, resolved, auto_resolved
    resolution: Optional[Dict[str, Any]] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    merge_strategy: Optional[MergeStrategy] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    auto_resolvable: bool = False
    resolution_suggestions: List[Dict[str, Any]] = Field(default_factory=list)

class PullRequest(BaseModel):
    """Pull request for schema changes."""
    pr_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    repo_id: str
    external_pr_id: Optional[str] = None  # GitHub/GitLab PR ID
    
    # PR details
    title: str
    description: str
    source_branch_id: str
    target_branch_id: str
    author_id: str
    
    # Status
    status: str = "open"  # open, closed, merged, draft
    is_draft: bool = False
    mergeable: bool = True
    
    # Review process
    reviewers: List[str] = Field(default_factory=list)
    approvals: List[str] = Field(default_factory=list)
    required_approvals: int = 1
    
    # Schema impact
    migration_plans: List[str] = Field(default_factory=list)
    schema_changes_summary: Dict[str, Any] = Field(default_factory=dict)
    conflicts: List[str] = Field(default_factory=list)  # conflict IDs
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

class ChangeHistory(BaseModel):
    """Comprehensive change history tracking."""
    history_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    object_type: str  # table, column, index, migration_plan
    object_id: str
    
    # Change details
    change_type: str  # create, update, delete, rename
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    diff: Optional[Dict[str, Any]] = None
    
    # Context
    branch_id: Optional[str] = None
    commit_id: Optional[str] = None
    migration_plan_id: Optional[str] = None
    change_request_id: Optional[str] = None
    
    # Metadata
    changed_by: str
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class GitWebhookEvent(BaseModel):
    """Git webhook event processing."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    repo_id: str
    event_type: str  # push, pull_request, merge, etc.
    
    # Event data
    payload: Dict[str, Any]
    headers: Dict[str, str] = Field(default_factory=dict)
    signature: Optional[str] = None
    
    # Processing
    processed: bool = False
    processed_at: Optional[datetime] = None
    processing_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Metadata
    received_at: datetime = Field(default_factory=datetime.utcnow)
    source_ip: Optional[str] = None

class SyncStatus(BaseModel):
    """Repository synchronization status."""
    sync_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    repo_id: str
    sync_type: str  # full, incremental, webhook
    
    # Status
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0
    
    # Results
    commits_synced: int = 0
    branches_synced: int = 0
    conflicts_detected: int = 0
    errors: List[str] = Field(default_factory=list)
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
