"""
Collaboration Router
Real-time collaboration, comments, change requests, and approval workflows
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime

from ..models.collaboration import (
    ChangeRequest, Comment, Annotation, Workspace, ChangeStatus
)
from ..core.collaboration import (
    CollaborationManager, ApprovalWorkflow, CommentSystem
)

router = APIRouter(tags=["collaboration"])
logger = logging.getLogger(__name__)

# External dependencies (these would be injected in production)
workspaces_store: Dict[str, Workspace] = {}
change_requests_store: Dict[str, ChangeRequest] = {}
comments_store: Dict[str, List[Comment]] = {}
annotations_store: Dict[str, List[Annotation]] = {}

# Initialize collaboration services (would be injected in production)
import redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
collaboration_manager = CollaborationManager(redis_client)
approval_workflow = ApprovalWorkflow()
comment_system = CommentSystem(collaboration_manager)

# Real-time Collaboration WebSocket
@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str, user_id: str):
    """WebSocket endpoint for real-time collaboration."""
    try:
        await collaboration_manager.connect_user(websocket, user_id, workspace_id)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Broadcast message to other users in workspace
            await collaboration_manager.broadcast_to_workspace(
                workspace_id, 
                {
                    "type": "user_message",
                    "user_id": user_id,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_websocket=websocket
            )
    
    except WebSocketDisconnect:
        await collaboration_manager.disconnect_user(websocket, user_id, workspace_id)

# Change Request Management
@router.post("/workspaces/{workspace_id}/change-requests", response_model=ChangeRequest)
async def create_change_request(workspace_id: str, request_data: Dict[str, Any]):
    """Create a change request for approval workflow."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        workspace = workspaces_store[workspace_id]
        change_request = await approval_workflow.create_change_request(
            workspace,
            request_data["migration_plan_id"],
            request_data["author_id"],
            request_data["title"],
            request_data["description"]
        )
        
        change_requests_store[change_request.request_id] = change_request
        
        return change_request
    
    except Exception as e:
        logger.error(f"Error creating change request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-requests/{request_id}/submit", response_model=ChangeRequest)
async def submit_change_request(request_id: str):
    """Submit change request for review."""
    if request_id not in change_requests_store:
        raise HTTPException(status_code=404, detail="Change request not found")
    
    try:
        change_request = change_requests_store[request_id]
        updated_request = await approval_workflow.submit_for_review(change_request)
        change_requests_store[request_id] = updated_request
        
        return updated_request
    
    except Exception as e:
        logger.error(f"Error submitting change request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-requests/{request_id}/approve", response_model=ChangeRequest)
async def approve_change_request(request_id: str, approval_data: Dict[str, Any]):
    """Approve a change request."""
    if request_id not in change_requests_store:
        raise HTTPException(status_code=404, detail="Change request not found")
    
    try:
        change_request = change_requests_store[request_id]
        updated_request = await approval_workflow.approve_change(
            change_request, 
            approval_data["approver_id"]
        )
        change_requests_store[request_id] = updated_request
        
        return updated_request
    
    except Exception as e:
        logger.error(f"Error approving change request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Comments and Annotations
@router.post("/workspaces/{workspace_id}/comments", response_model=Comment)
async def add_comment(workspace_id: str, comment_data: Dict[str, Any]):
    """Add a comment."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        comment = Comment(
            workspace_id=workspace_id,
            object_type=comment_data["object_type"],
            object_id=comment_data["object_id"],
            author_id=comment_data["author_id"],
            content=comment_data["content"],
            parent_comment_id=comment_data.get("parent_comment_id")
        )
        
        updated_comment = await comment_system.add_comment(comment)
        
        if workspace_id not in comments_store:
            comments_store[workspace_id] = []
        comments_store[workspace_id].append(updated_comment)
        
        return updated_comment
    
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces/{workspace_id}/comments", response_model=List[Comment])
async def list_comments(workspace_id: str, object_type: Optional[str] = None, object_id: Optional[str] = None):
    """List comments for workspace or specific object."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    comments = comments_store.get(workspace_id, [])
    
    if object_type and object_id:
        comments = [c for c in comments if c.object_type == object_type and c.object_id == object_id]
    
    return comments
