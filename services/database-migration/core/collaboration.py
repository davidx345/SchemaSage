"""
Collaboration Service - Simplified Team Features (Redis-free)
"""
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import uuid

# Use absolute imports
from models.collaboration import (
    User, Workspace, WorkspaceMember, ChangeRequest, Comment, 
    Annotation, AuditLog, TeamInvitation, UserRole, PermissionType, ChangeStatus
)

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

class SimpleApprovalWorkflow:
    """Simplified change approval workflows (without Redis)."""
    
    def __init__(self):
        self.workflow_rules = {}
    
    async def create_change_request(self, workspace_id: str, migration_plan_id: str, author_id: str, title: str, description: str) -> dict:
        """Create a simple change request."""
        change_request = {
            "request_id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "migration_plan_id": migration_plan_id,
            "title": title,
            "description": description,
            "author_id": author_id,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "required_approvals": 1,
            "approvals": [],
            "rejections": []
        }
        
        return change_request
    
    async def submit_for_review(self, change_request: dict) -> dict:
        """Submit change request for review."""
        change_request["status"] = "pending_review"
        change_request["submitted_at"] = datetime.utcnow().isoformat()
        change_request["updated_at"] = datetime.utcnow().isoformat()
        
        return change_request
    
    async def approve_change(self, change_request: dict, approver_id: str) -> dict:
        """Approve a change request."""
        if approver_id not in change_request["approvals"]:
            change_request["approvals"].append(approver_id)
        
        change_request["updated_at"] = datetime.utcnow().isoformat()
        
        # Check if enough approvals
        if len(change_request["approvals"]) >= change_request["required_approvals"]:
            change_request["status"] = "approved"
            change_request["approved_at"] = datetime.utcnow().isoformat()
        
        return change_request

class SimpleAuditLogger:
    """Simplified audit logging system."""
    
    def __init__(self):
        self.compliance_categories = {
            "access": ["login", "logout", "permission_change"],
            "change": ["create", "update", "delete", "merge"],
            "security": ["auth_failure", "permission_denied", "sensitive_access"],
            "data": ["export", "import", "backup", "restore"]
        }
    
    async def log_action(self, workspace_id: str, user_id: str, action: str, object_type: str, object_id: str, details: Dict[str, Any] = None) -> dict:
        """Log a simple audit event."""
        compliance_category = self._get_compliance_category(action)
        risk_level = self._assess_risk_level(action, object_type, details)
        
        audit_log = {
            "log_id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "user_id": user_id,
            "action": action,
            "object_type": object_type,
            "object_id": object_id,
            "details": details or {},
            "compliance_category": compliance_category,
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
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
