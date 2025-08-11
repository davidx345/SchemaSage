"""
Collaboration and Enterprise Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime
import uuid

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"

class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    ADMIN = "admin"

class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"

class ChangeStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"

class User(BaseModel):
    """User model for enterprise collaboration."""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    avatar_url: Optional[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sso_provider: Optional[str] = None  # google, azure, okta, etc.
    sso_id: Optional[str] = None

class Workspace(BaseModel):
    """Multi-user workspace for database migration projects."""
    workspace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    owner_id: str
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Enterprise features
    require_approval: bool = False
    retention_days: Optional[int] = 90
    compliance_level: str = "standard"  # standard, high, critical

class WorkspaceMember(BaseModel):
    """Workspace membership with roles and permissions."""
    member_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    role: UserRole
    permissions: Set[PermissionType] = Field(default_factory=set)
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    invited_by: Optional[str] = None
    is_active: bool = True

class ChangeRequest(BaseModel):
    """Change request for approval workflows."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    migration_plan_id: str
    title: str
    description: str
    author_id: str
    status: ChangeStatus = ChangeStatus.DRAFT
    
    # Approval workflow
    reviewers: List[str] = Field(default_factory=list)
    approvals: List[str] = Field(default_factory=list)
    rejections: List[str] = Field(default_factory=list)
    required_approvals: int = 1
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    
    # Change details
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    impact_assessment: Optional[Dict[str, Any]] = None

class Comment(BaseModel):
    """Comment and annotation system."""
    comment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    object_type: str  # migration_plan, change_request, schema_object
    object_id: str
    author_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Threading support
    parent_comment_id: Optional[str] = None
    thread_id: Optional[str] = None
    
    # Annotations for specific locations
    annotation_data: Optional[Dict[str, Any]] = None  # line numbers, column names, etc.

class Annotation(BaseModel):
    """Detailed annotations for schema objects."""
    annotation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    object_type: str  # table, column, index, constraint
    object_name: str
    migration_plan_id: Optional[str] = None
    author_id: str
    
    # Annotation content
    title: str
    description: str
    annotation_type: str  # note, warning, issue, suggestion
    priority: str = "medium"  # low, medium, high, critical
    
    # Location data
    location_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class AuditLog(BaseModel):
    """Enterprise audit logging."""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    action: str
    object_type: str
    object_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Compliance fields
    session_id: Optional[str] = None
    compliance_category: str = "general"  # access, change, security, data
    risk_level: str = "low"  # low, medium, high, critical

class TeamInvitation(BaseModel):
    """Team invitation management."""
    invitation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    invited_email: str
    invited_by: str
    role: UserRole
    permissions: Set[PermissionType] = Field(default_factory=set)
    message: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, accepted, rejected, expired
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))

class SSOProvider(BaseModel):
    """SSO provider configuration."""
    provider_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    provider_name: str  # google, azure, okta, etc.
    provider_type: str  # oauth2, saml, ldap
    configuration: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Security settings
    require_mfa: bool = False
    allowed_domains: List[str] = Field(default_factory=list)
    auto_provision: bool = False

class ComplianceReport(BaseModel):
    """Compliance reporting for enterprise."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    report_type: str  # access, changes, security, gdpr
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Report parameters
    start_date: datetime
    end_date: datetime
    scope: Dict[str, Any] = Field(default_factory=dict)
    
    # Report data
    summary: Dict[str, Any] = Field(default_factory=dict)
    details: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Export info
    file_path: Optional[str] = None
    file_format: str = "json"  # json, csv, pdf
    expiry_date: Optional[datetime] = None
