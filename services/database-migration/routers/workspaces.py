"""
Workspace Management Router
Workspace creation, member management, and workspace operations
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging

from ..models.collaboration import Workspace, WorkspaceMember, UserRole, AuditLog
from ..core.collaboration import AuditLogger

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
logger = logging.getLogger(__name__)

# External dependencies (these would be injected in production)
workspaces_store: Dict[str, Workspace] = {}
workspace_members_store: Dict[str, List[WorkspaceMember]] = {}
audit_logs_store: Dict[str, List[AuditLog]] = {}
audit_logger = AuditLogger()

@router.post("", response_model=Dict[str, Any])
async def create_workspace(workspace_data: Dict[str, Any]):
    """Create a new workspace."""
    try:
        workspace = Workspace(
            name=workspace_data["name"],
            description=workspace_data.get("description"),
            owner_id=workspace_data["owner_id"],
            settings=workspace_data.get("settings", {})
        )
        
        workspaces_store[workspace.workspace_id] = workspace
        workspace_members_store[workspace.workspace_id] = []
        
        # Add owner as workspace member
        owner_member = WorkspaceMember(
            workspace_id=workspace.workspace_id,
            user_id=workspace.owner_id,
            role=UserRole.OWNER
        )
        workspace_members_store[workspace.workspace_id].append(owner_member)
        
        # Log workspace creation
        audit_log = await audit_logger.log_action(
            workspace.workspace_id, workspace.owner_id, "create_workspace",
            "workspace", workspace.workspace_id
        )
        if workspace.workspace_id not in audit_logs_store:
            audit_logs_store[workspace.workspace_id] = []
        audit_logs_store[workspace.workspace_id].append(audit_log)
        
        return {
            "workspace_id": workspace.workspace_id,
            "message": "Workspace created successfully",
            "workspace": workspace.model_dump()
        }
    
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[Dict[str, Any]])
async def list_workspaces(user_id: Optional[str] = None):
    """List workspaces accessible to user."""
    workspaces_list = []
    
    for workspace_id, workspace in workspaces_store.items():
        # Check if user has access to workspace
        if user_id:
            members = workspace_members_store.get(workspace_id, [])
            if not any(member.user_id == user_id for member in members):
                continue
        
        workspace_info = workspace.model_dump()
        workspace_info["member_count"] = len(workspace_members_store.get(workspace_id, []))
        workspaces_list.append(workspace_info)
    
    return workspaces_list

@router.get("/{workspace_id}", response_model=Workspace)
async def get_workspace(workspace_id: str):
    """Get workspace details."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspaces_store[workspace_id]

@router.post("/{workspace_id}/members", response_model=Dict[str, Any])
async def add_workspace_member(workspace_id: str, member_data: Dict[str, Any]):
    """Add member to workspace."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=member_data["user_id"],
            role=UserRole(member_data["role"]),
            invited_by=member_data.get("invited_by")
        )
        
        if workspace_id not in workspace_members_store:
            workspace_members_store[workspace_id] = []
        workspace_members_store[workspace_id].append(member)
        
        return {
            "message": "Member added successfully",
            "member": member.model_dump()
        }
    
    except Exception as e:
        logger.error(f"Error adding workspace member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMember])
async def list_workspace_members(workspace_id: str):
    """List workspace members."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return workspace_members_store.get(workspace_id, [])

@router.get("/{workspace_id}/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(workspace_id: str, limit: int = 100, category: Optional[str] = None):
    """Get audit logs for workspace."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    logs = audit_logs_store.get(workspace_id, [])
    
    if category:
        logs = [log for log in logs if log.compliance_category == category]
    
    return logs[:limit]
