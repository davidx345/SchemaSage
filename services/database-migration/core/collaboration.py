"""
Collaboration Service - Team Features and Workflows
"""
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional, Set
import json
import redis
import asyncio
from datetime import datetime, timedelta
import uuid

from ..models.collaboration import (
    User, Workspace, WorkspaceMember, ChangeRequest, Comment, 
    Annotation, AuditLog, TeamInvitation, UserRole, PermissionType, ChangeStatus
)

class CollaborationManager:
    """Manages real-time collaboration features."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_workspaces: Dict[str, Set[str]] = {}
    
    async def connect_user(self, websocket: WebSocket, user_id: str, workspace_id: str):
        """Connect user to workspace for real-time collaboration."""
        await websocket.accept()
        
        # Add to active connections
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = set()
        self.active_connections[workspace_id].add(websocket)
        
        # Track user workspaces
        if user_id not in self.user_workspaces:
            self.user_workspaces[user_id] = set()
        self.user_workspaces[user_id].add(workspace_id)
        
        # Store connection in Redis for scalability
        await self._store_connection_in_redis(user_id, workspace_id)
        
        # Notify other users
        await self.broadcast_to_workspace(workspace_id, {
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_websocket=websocket)
    
    async def disconnect_user(self, websocket: WebSocket, user_id: str, workspace_id: str):
        """Disconnect user from workspace."""
        # Remove from active connections
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].discard(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]
        
        # Update user workspaces
        if user_id in self.user_workspaces:
            self.user_workspaces[user_id].discard(workspace_id)
            if not self.user_workspaces[user_id]:
                del self.user_workspaces[user_id]
        
        # Remove from Redis
        await self._remove_connection_from_redis(user_id, workspace_id)
        
        # Notify other users
        await self.broadcast_to_workspace(workspace_id, {
            "type": "user_left",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_to_workspace(self, workspace_id: str, message: Dict[str, Any], exclude_websocket: Optional[WebSocket] = None):
        """Broadcast message to all users in workspace."""
        if workspace_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_websockets = set()
        
        for websocket in self.active_connections[workspace_id]:
            if websocket == exclude_websocket:
                continue
                
            try:
                await websocket.send_text(message_str)
            except:
                disconnected_websockets.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.active_connections[workspace_id].discard(websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user across all their workspaces."""
        if user_id not in self.user_workspaces:
            return
        
        message_str = json.dumps(message)
        
        for workspace_id in self.user_workspaces[user_id]:
            if workspace_id in self.active_connections:
                for websocket in self.active_connections[workspace_id]:
                    try:
                        await websocket.send_text(message_str)
                    except:
                        pass  # Handle disconnection
    
    async def _store_connection_in_redis(self, user_id: str, workspace_id: str):
        """Store user connection in Redis for scalability."""
        key = f"collaboration:workspace:{workspace_id}:users"
        await self.redis.sadd(key, user_id)
        await self.redis.expire(key, 3600)  # 1 hour TTL
    
    async def _remove_connection_from_redis(self, user_id: str, workspace_id: str):
        """Remove user connection from Redis."""
        key = f"collaboration:workspace:{workspace_id}:users"
        await self.redis.srem(key, user_id)

class PermissionManager:
    """Manages workspace permissions and access control."""
    
    def __init__(self):
        self.role_permissions = {
            UserRole.OWNER: {
                PermissionType.READ, PermissionType.WRITE, PermissionType.DELETE,
                PermissionType.EXECUTE, PermissionType.APPROVE, PermissionType.ADMIN
            },
            UserRole.ADMIN: {
                PermissionType.READ, PermissionType.WRITE, PermissionType.DELETE,
                PermissionType.EXECUTE, PermissionType.APPROVE
            },
            UserRole.EDITOR: {
                PermissionType.READ, PermissionType.WRITE, PermissionType.EXECUTE
            },
            UserRole.VIEWER: {
                PermissionType.READ
            },
            UserRole.GUEST: {
                PermissionType.READ
            }
        }
    
    def get_user_permissions(self, member: WorkspaceMember) -> Set[PermissionType]:
        """Get effective permissions for a workspace member."""
        # Start with role-based permissions
        permissions = self.role_permissions.get(member.role, set()).copy()
        
        # Add any additional permissions
        permissions.update(member.permissions)
        
        return permissions
    
    def has_permission(self, member: WorkspaceMember, permission: PermissionType) -> bool:
        """Check if user has specific permission."""
        user_permissions = self.get_user_permissions(member)
        return permission in user_permissions
    
    def can_perform_action(self, member: WorkspaceMember, action: str, resource_type: str) -> bool:
        """Check if user can perform specific action on resource type."""
        action_permission_map = {
            "read": PermissionType.READ,
            "create": PermissionType.WRITE,
            "update": PermissionType.WRITE,
            "delete": PermissionType.DELETE,
            "execute": PermissionType.EXECUTE,
            "approve": PermissionType.APPROVE,
            "admin": PermissionType.ADMIN
        }
        
        required_permission = action_permission_map.get(action)
        if not required_permission:
            return False
        
        return self.has_permission(member, required_permission)

class ApprovalWorkflow:
    """Manages change approval workflows."""
    
    def __init__(self):
        self.workflow_rules = {}
    
    async def create_change_request(self, workspace: Workspace, migration_plan_id: str, author_id: str, title: str, description: str) -> ChangeRequest:
        """Create a new change request."""
        change_request = ChangeRequest(
            workspace_id=workspace.workspace_id,
            migration_plan_id=migration_plan_id,
            title=title,
            description=description,
            author_id=author_id,
            required_approvals=self._get_required_approvals(workspace)
        )
        
        # Auto-assign reviewers if configured
        change_request.reviewers = await self._get_default_reviewers(workspace)
        
        return change_request
    
    async def submit_for_review(self, change_request: ChangeRequest) -> ChangeRequest:
        """Submit change request for review."""
        change_request.status = ChangeStatus.PENDING_REVIEW
        change_request.submitted_at = datetime.utcnow()
        change_request.updated_at = datetime.utcnow()
        
        return change_request
    
    async def approve_change(self, change_request: ChangeRequest, approver_id: str) -> ChangeRequest:
        """Approve a change request."""
        if approver_id not in change_request.approvals:
            change_request.approvals.append(approver_id)
        
        change_request.updated_at = datetime.utcnow()
        
        # Check if enough approvals
        if len(change_request.approvals) >= change_request.required_approvals:
            change_request.status = ChangeStatus.APPROVED
            change_request.approved_at = datetime.utcnow()
        
        return change_request
    
    async def reject_change(self, change_request: ChangeRequest, rejector_id: str, reason: str) -> ChangeRequest:
        """Reject a change request."""
        if rejector_id not in change_request.rejections:
            change_request.rejections.append(rejector_id)
        
        change_request.status = ChangeStatus.REJECTED
        change_request.updated_at = datetime.utcnow()
        
        return change_request
    
    def _get_required_approvals(self, workspace: Workspace) -> int:
        """Get required number of approvals for workspace."""
        return workspace.settings.get("required_approvals", 1)
    
    async def _get_default_reviewers(self, workspace: Workspace) -> List[str]:
        """Get default reviewers for workspace."""
        # This would typically query the database for workspace members with approve permissions
        return workspace.settings.get("default_reviewers", [])

class CommentSystem:
    """Manages comments and annotations."""
    
    def __init__(self, collaboration_manager: CollaborationManager):
        self.collaboration_manager = collaboration_manager
    
    async def add_comment(self, comment: Comment) -> Comment:
        """Add a new comment."""
        # Generate thread ID if this is a top-level comment
        if not comment.parent_comment_id:
            comment.thread_id = comment.comment_id
        
        # Broadcast comment to workspace
        await self.collaboration_manager.broadcast_to_workspace(
            comment.workspace_id,
            {
                "type": "comment_added",
                "comment": comment.model_dump(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return comment
    
    async def update_comment(self, comment: Comment) -> Comment:
        """Update an existing comment."""
        comment.updated_at = datetime.utcnow()
        
        # Broadcast update to workspace
        await self.collaboration_manager.broadcast_to_workspace(
            comment.workspace_id,
            {
                "type": "comment_updated",
                "comment": comment.model_dump(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return comment
    
    async def resolve_comment(self, comment: Comment, resolver_id: str) -> Comment:
        """Resolve a comment."""
        comment.is_resolved = True
        comment.resolved_by = resolver_id
        comment.resolved_at = datetime.utcnow()
        
        # Broadcast resolution to workspace
        await self.collaboration_manager.broadcast_to_workspace(
            comment.workspace_id,
            {
                "type": "comment_resolved",
                "comment_id": comment.comment_id,
                "resolved_by": resolver_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return comment
    
    async def add_annotation(self, annotation: Annotation) -> Annotation:
        """Add a new annotation."""
        # Broadcast annotation to workspace
        await self.collaboration_manager.broadcast_to_workspace(
            annotation.workspace_id,
            {
                "type": "annotation_added",
                "annotation": annotation.model_dump(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return annotation

class AuditLogger:
    """Enterprise audit logging system."""
    
    def __init__(self):
        self.compliance_categories = {
            "access": ["login", "logout", "permission_change"],
            "change": ["create", "update", "delete", "merge"],
            "security": ["auth_failure", "permission_denied", "sensitive_access"],
            "data": ["export", "import", "backup", "restore"]
        }
    
    async def log_action(self, workspace_id: str, user_id: str, action: str, object_type: str, object_id: str, details: Dict[str, Any] = None, request_info: Dict[str, Any] = None) -> AuditLog:
        """Log an audit event."""
        compliance_category = self._get_compliance_category(action)
        risk_level = self._assess_risk_level(action, object_type, details)
        
        audit_log = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            details=details or {},
            ip_address=request_info.get("ip_address") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None,
            session_id=request_info.get("session_id") if request_info else None,
            compliance_category=compliance_category,
            risk_level=risk_level
        )
        
        return audit_log
    
    def _get_compliance_category(self, action: str) -> str:
        """Determine compliance category for action."""
        for category, actions in self.compliance_categories.items():
            if any(action.startswith(a) for a in actions):
                return category
        return "general"
    
    def _assess_risk_level(self, action: str, object_type: str, details: Dict[str, Any]) -> str:
        """Assess risk level for the action."""
        high_risk_actions = ["delete", "execute", "export", "permission_change"]
        sensitive_objects = ["user", "workspace", "migration_plan"]
        
        if action in high_risk_actions and object_type in sensitive_objects:
            return "high"
        elif action in high_risk_actions or object_type in sensitive_objects:
            return "medium"
        else:
            return "low"

class TeamInvitationManager:
    """Manages team invitations and onboarding."""
    
    def __init__(self):
        self.invitation_expiry_hours = 72  # 3 days
    
    async def create_invitation(self, workspace_id: str, invited_email: str, invited_by: str, role: UserRole, message: str = None) -> TeamInvitation:
        """Create a team invitation."""
        invitation = TeamInvitation(
            workspace_id=workspace_id,
            invited_email=invited_email,
            invited_by=invited_by,
            role=role,
            message=message,
            expires_at=datetime.utcnow() + timedelta(hours=self.invitation_expiry_hours)
        )
        
        return invitation
    
    async def accept_invitation(self, invitation: TeamInvitation, user_id: str) -> WorkspaceMember:
        """Accept a team invitation."""
        if invitation.status != "pending":
            raise ValueError("Invitation is not pending")
        
        if datetime.utcnow() > invitation.expires_at:
            raise ValueError("Invitation has expired")
        
        # Create workspace member
        member = WorkspaceMember(
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            role=invitation.role,
            permissions=invitation.permissions,
            invited_by=invitation.invited_by
        )
        
        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        
        return member
    
    async def reject_invitation(self, invitation: TeamInvitation) -> TeamInvitation:
        """Reject a team invitation."""
        invitation.status = "rejected"
        return invitation
