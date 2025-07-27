"""
Data models for team collaboration and schema governance
"""

from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ApprovalStatus(Enum):
    """Schema change approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"


class ChangeType(Enum):
    """Types of schema changes"""
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    MODIFY_COLUMN = "modify_column"
    ADD_TABLE = "add_table"
    DROP_TABLE = "drop_table"
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    ADD_CONSTRAINT = "add_constraint"
    DROP_CONSTRAINT = "drop_constraint"


class UserRole(Enum):
    """User roles in the system"""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    OWNER = "owner"


class NotificationType(Enum):
    """Types of notifications"""
    SCHEMA_CHANGE_PROPOSED = "schema_change_proposed"
    APPROVAL_REQUESTED = "approval_requested"
    CHANGE_APPROVED = "change_approved"
    CHANGE_REJECTED = "change_rejected"
    COMMENT_ADDED = "comment_added"
    TEAM_INVITATION = "team_invitation"


@dataclass
class TeamMember:
    """Team member information"""
    user_id: str
    username: str
    email: str
    role: UserRole
    joined_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    permissions: Set[str] = field(default_factory=set)
    
    def has_permission(self, permission: str) -> bool:
        """Check if member has specific permission"""
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'joined_at': self.joined_at.isoformat(),
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'permissions': list(self.permissions)
        }


@dataclass
class Team:
    """Team workspace"""
    team_id: str
    name: str
    description: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    members: List[TeamMember] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_member(self, user_id: str) -> Optional[TeamMember]:
        """Get team member by user ID"""
        return next((m for m in self.members if m.user_id == user_id), None)
    
    def has_member(self, user_id: str) -> bool:
        """Check if user is team member"""
        return any(m.user_id == user_id for m in self.members)
    
    def get_members_with_permission(self, permission: str) -> List[TeamMember]:
        """Get all members with specific permission"""
        return [m for m in self.members if m.has_permission(permission)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'members': [m.to_dict() for m in self.members],
            'settings': self.settings,
            'member_count': len(self.members)
        }


@dataclass
class Comment:
    """Comment on schema changes"""
    comment_id: str
    user_id: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    thread_id: Optional[str] = None
    parent_comment_id: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'comment_id': self.comment_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'thread_id': self.thread_id,
            'parent_comment_id': self.parent_comment_id,
            'resolved': self.resolved
        }


@dataclass
class SchemaChange:
    """Represents a proposed schema change"""
    change_id: str
    schema_id: str
    change_type: ChangeType
    description: str
    proposed_by: str
    proposed_at: datetime = field(default_factory=datetime.now)
    current_definition: Dict[str, Any] = field(default_factory=dict)
    proposed_definition: Dict[str, Any] = field(default_factory=dict)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewers: List[str] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    approved_by: List[str] = field(default_factory=list)
    rejected_by: List[str] = field(default_factory=list)
    
    def is_approved(self) -> bool:
        """Check if change is approved"""
        return self.status == ApprovalStatus.APPROVED
    
    def is_rejected(self) -> bool:
        """Check if change is rejected"""
        return self.status == ApprovalStatus.REJECTED
    
    def can_be_applied(self) -> bool:
        """Check if change can be applied"""
        return self.is_approved() and not self.is_rejected()
    
    def add_comment(self, comment: Comment):
        """Add comment to change"""
        self.comments.append(comment)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'change_id': self.change_id,
            'schema_id': self.schema_id,
            'change_type': self.change_type.value,
            'description': self.description,
            'proposed_by': self.proposed_by,
            'proposed_at': self.proposed_at.isoformat(),
            'current_definition': self.current_definition,
            'proposed_definition': self.proposed_definition,
            'impact_analysis': self.impact_analysis,
            'status': self.status.value,
            'reviewers': self.reviewers,
            'comments': [c.to_dict() for c in self.comments],
            'approved_by': self.approved_by,
            'rejected_by': self.rejected_by
        }


@dataclass
class SchemaVersion:
    """Schema version with metadata"""
    version_id: str
    schema_id: str
    version_number: str
    definition: Dict[str, Any]
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    change_summary: str = ""
    is_active: bool = False
    tags: List[str] = field(default_factory=list)
    parent_version_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'version_id': self.version_id,
            'schema_id': self.schema_id,
            'version_number': self.version_number,
            'definition': self.definition,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'change_summary': self.change_summary,
            'is_active': self.is_active,
            'tags': self.tags,
            'parent_version_id': self.parent_version_id
        }


@dataclass
class SchemaRegistry:
    """Schema registry entry"""
    schema_id: str
    name: str
    description: str
    team_id: str
    category: str
    current_version: str
    versions: List[SchemaVersion] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_active_version(self) -> Optional[SchemaVersion]:
        """Get the currently active version"""
        return next((v for v in self.versions if v.is_active), None)
    
    def get_version(self, version_id: str) -> Optional[SchemaVersion]:
        """Get specific version by ID"""
        return next((v for v in self.versions if v.version_id == version_id), None)
    
    def add_version(self, version: SchemaVersion):
        """Add new version and mark as active"""
        # Deactivate current active version
        for v in self.versions:
            v.is_active = False
        
        # Add and activate new version
        version.is_active = True
        self.versions.append(version)
        self.current_version = version.version_number
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'schema_id': self.schema_id,
            'name': self.name,
            'description': self.description,
            'team_id': self.team_id,
            'category': self.category,
            'current_version': self.current_version,
            'versions': [v.to_dict() for v in self.versions],
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'metadata': self.metadata,
            'version_count': len(self.versions)
        }


@dataclass
class Notification:
    """User notification"""
    notification_id: str
    user_id: str
    type: NotificationType
    title: str
    content: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    is_read: bool = False
    priority: str = "normal"  # low, normal, high, urgent
    
    def mark_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'type': self.type.value,
            'title': self.title,
            'content': self.content,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_read': self.is_read,
            'priority': self.priority
        }


@dataclass
class ApprovalWorkflow:
    """Approval workflow configuration"""
    workflow_id: str
    name: str
    description: str
    team_id: str
    schema_categories: List[str] = field(default_factory=list)  # Which schema categories this applies to
    required_approvals: int = 1
    reviewer_roles: List[UserRole] = field(default_factory=list)
    auto_approve_conditions: Dict[str, Any] = field(default_factory=dict)
    escalation_rules: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    is_active: bool = True
    
    def applies_to_schema(self, schema_category: str) -> bool:
        """Check if workflow applies to schema category"""
        return not self.schema_categories or schema_category in self.schema_categories
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'team_id': self.team_id,
            'schema_categories': self.schema_categories,
            'required_approvals': self.required_approvals,
            'reviewer_roles': [role.value for role in self.reviewer_roles],
            'auto_approve_conditions': self.auto_approve_conditions,
            'escalation_rules': self.escalation_rules,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'is_active': self.is_active
        }
