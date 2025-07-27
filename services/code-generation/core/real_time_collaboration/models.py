"""
Base types and models for real-time collaboration
"""
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class CollaborationEventType(Enum):
    """Types of collaboration events"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    SCHEMA_UPDATED = "schema_updated"
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed" 
    TABLE_MODIFIED = "table_modified"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_MODIFIED = "column_modified"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_REMOVED = "relationship_removed"
    CURSOR_MOVED = "cursor_moved"
    SELECTION_CHANGED = "selection_changed"
    COMMENT_ADDED = "comment_added"
    LOCK_ACQUIRED = "lock_acquired"
    LOCK_RELEASED = "lock_released"
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"

class UserRole(Enum):
    """User roles in collaboration"""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
    REVIEWER = "reviewer"
    ADMIN = "admin"

class LockType(Enum):
    """Types of locks for collaborative editing"""
    TABLE_LOCK = "table_lock"
    COLUMN_LOCK = "column_lock"
    SCHEMA_LOCK = "schema_lock"
    RELATIONSHIP_LOCK = "relationship_lock"

class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicts"""
    LAST_WRITER_WINS = "last_writer_wins"
    FIRST_WRITER_WINS = "first_writer_wins"
    MANUAL_RESOLUTION = "manual_resolution"
    MERGE_CHANGES = "merge_changes"

@dataclass
class CollaborationUser:
    """Represents a user in collaboration session"""
    user_id: str
    username: str
    email: str
    role: UserRole
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    cursor_position: Optional[Dict[str, Any]] = None
    selection: Optional[Dict[str, Any]] = None
    color: str = "#007bff"  # User's color for cursors/selections
    avatar_url: Optional[str] = None

@dataclass
class CollaborationEvent:
    """Represents a collaboration event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: CollaborationEventType = CollaborationEventType.SCHEMA_UPDATED
    user_id: str = ""
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    affected_elements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ElementLock:
    """Represents a lock on a schema element"""
    lock_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_id: str = ""
    element_type: str = ""  # table, column, relationship
    lock_type: LockType = LockType.TABLE_LOCK
    user_id: str = ""
    acquired_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_exclusive: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConflictInfo:
    """Information about a collaboration conflict"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_id: str = ""
    element_type: str = ""
    conflicting_users: List[str] = field(default_factory=list)
    conflict_data: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)
    resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MANUAL_RESOLUTION
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

@dataclass
class Comment:
    """Comment on schema element"""
    comment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_id: str = ""
    element_type: str = ""  # table, column, relationship
    user_id: str = ""
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    replies: List["Comment"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CursorPosition:
    """User cursor position"""
    user_id: str = ""
    element_id: str = ""
    element_type: str = ""
    position: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Selection:
    """User selection"""
    user_id: str = ""
    selected_elements: List[str] = field(default_factory=list)
    selection_type: str = ""  # table, column, relationship, multiple
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PresenceInfo:
    """User presence information"""
    user_id: str = ""
    is_online: bool = False
    last_seen: datetime = field(default_factory=datetime.now)
    current_view: Optional[str] = None  # Which part of schema they're viewing
    cursor_position: Optional[CursorPosition] = None
    selection: Optional[Selection] = None
    is_typing: bool = False
    typing_element: Optional[str] = None

@dataclass
class SessionPermissions:
    """Permissions for a collaboration session"""
    can_edit_schema: bool = True
    can_add_tables: bool = True
    can_remove_tables: bool = True
    can_edit_tables: bool = True
    can_add_columns: bool = True
    can_remove_columns: bool = True
    can_edit_columns: bool = True
    can_add_relationships: bool = True
    can_remove_relationships: bool = True
    can_edit_relationships: bool = True
    can_comment: bool = True
    can_lock_elements: bool = True
    can_resolve_conflicts: bool = True
    can_manage_users: bool = False
    can_export_schema: bool = True

@dataclass
class CollaborationSession:
    """Represents a collaboration session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_id: str = ""
    name: str = ""
    description: str = ""
    owner_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    max_users: int = 10
    users: Dict[str, CollaborationUser] = field(default_factory=dict)
    locks: Dict[str, ElementLock] = field(default_factory=dict)
    conflicts: Dict[str, ConflictInfo] = field(default_factory=dict)
    comments: Dict[str, Comment] = field(default_factory=dict)
    event_history: List[CollaborationEvent] = field(default_factory=list)
    presence: Dict[str, PresenceInfo] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, SessionPermissions] = field(default_factory=dict)

class CollaborationError(Exception):
    """Base exception for collaboration errors"""
    pass

class UserNotFoundError(CollaborationError):
    """Raised when user is not found in session"""
    pass

class PermissionDeniedError(CollaborationError):
    """Raised when user lacks permission for action"""
    pass

class ElementLockedError(CollaborationError):
    """Raised when trying to modify locked element"""
    pass

class ConflictError(CollaborationError):
    """Raised when collaboration conflict occurs"""
    pass

class SessionFullError(CollaborationError):
    """Raised when session has reached maximum users"""
    pass

def get_user_permissions(user_role: UserRole) -> SessionPermissions:
    """Get default permissions for user role"""
    
    if user_role == UserRole.OWNER:
        return SessionPermissions(
            can_manage_users=True,
            can_resolve_conflicts=True
        )
    
    elif user_role == UserRole.ADMIN:
        return SessionPermissions(
            can_manage_users=True,
            can_resolve_conflicts=True
        )
    
    elif user_role == UserRole.EDITOR:
        return SessionPermissions(
            can_manage_users=False,
            can_resolve_conflicts=False
        )
    
    elif user_role == UserRole.REVIEWER:
        return SessionPermissions(
            can_edit_schema=False,
            can_add_tables=False,
            can_remove_tables=False,
            can_edit_tables=False,
            can_add_columns=False,
            can_remove_columns=False,
            can_edit_columns=False,
            can_add_relationships=False,
            can_remove_relationships=False,
            can_edit_relationships=False,
            can_lock_elements=False,
            can_manage_users=False,
            can_resolve_conflicts=False
        )
    
    elif user_role == UserRole.VIEWER:
        return SessionPermissions(
            can_edit_schema=False,
            can_add_tables=False,
            can_remove_tables=False,
            can_edit_tables=False,
            can_add_columns=False,
            can_remove_columns=False,
            can_edit_columns=False,
            can_add_relationships=False,
            can_remove_relationships=False,
            can_edit_relationships=False,
            can_comment=False,
            can_lock_elements=False,
            can_manage_users=False,
            can_resolve_conflicts=False
        )
    
    else:
        return SessionPermissions(
            can_edit_schema=False,
            can_add_tables=False,
            can_remove_tables=False,
            can_edit_tables=False,
            can_add_columns=False,
            can_remove_columns=False,
            can_edit_columns=False,
            can_add_relationships=False,
            can_remove_relationships=False,
            can_edit_relationships=False,
            can_comment=False,
            can_lock_elements=False,
            can_manage_users=False,
            can_resolve_conflicts=False
        )

def generate_user_color(user_id: str) -> str:
    """Generate a unique color for user based on their ID"""
    import hashlib
    
    # Create a hash of the user ID
    hash_object = hashlib.md5(user_id.encode())
    hash_hex = hash_object.hexdigest()
    
    # Extract RGB values from hash
    r = int(hash_hex[0:2], 16)
    g = int(hash_hex[2:4], 16) 
    b = int(hash_hex[4:6], 16)
    
    # Ensure colors are not too dark or too light
    r = max(50, min(200, r))
    g = max(50, min(200, g))
    b = max(50, min(200, b))
    
    return f"#{r:02x}{g:02x}{b:02x}"

def is_valid_event_type(event_type: str) -> bool:
    """Check if event type is valid"""
    try:
        CollaborationEventType(event_type)
        return True
    except ValueError:
        return False

def create_event(
    event_type: CollaborationEventType,
    user_id: str,
    session_id: str,
    data: Dict[str, Any] = None,
    affected_elements: List[str] = None
) -> CollaborationEvent:
    """Create a collaboration event"""
    
    return CollaborationEvent(
        event_type=event_type,
        user_id=user_id,
        session_id=session_id,
        data=data or {},
        affected_elements=affected_elements or [],
        metadata={
            "created_by": "system",
            "version": "1.0"
        }
    )
