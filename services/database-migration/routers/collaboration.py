"""
Collaboration Router (Simplified - Redis removed)
Basic collaboration features without real-time functionality
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Use absolute imports
from models.collaboration import (
    ChangeRequest, Comment, Annotation, Workspace, ChangeStatus
)

router = APIRouter(tags=["collaboration"])
logger = logging.getLogger(__name__)

# In-memory storage (would be replaced with database in production)
workspaces_store: Dict[str, Workspace] = {}
change_requests_store: Dict[str, ChangeRequest] = {}
comments_store: Dict[str, List[Comment]] = {}
annotations_store: Dict[str, List[Annotation]] = {}

# Basic health check
@router.get("/collaboration/health")
async def collaboration_health():
    """Health check for collaboration service."""
    return {"status": "healthy", "message": "Collaboration service running (Redis-free mode)"}

# Simplified Change Request Management (without real-time features)
@router.post("/workspaces/{workspace_id}/change-requests")
async def create_change_request(workspace_id: str, request_data: Dict[str, Any]):
    """Create a basic change request."""
    try:
        request_id = f"cr_{datetime.utcnow().timestamp()}"
        change_request = {
            "request_id": request_id,
            "workspace_id": workspace_id,
            "title": request_data.get("title", "Change Request"),
            "description": request_data.get("description", ""),
            "author_id": request_data.get("author_id", "anonymous"),
            "status": "draft",
            "created_at": datetime.utcnow().isoformat()
        }
        
        change_requests_store[request_id] = change_request
        logger.info(f"Created change request: {request_id}")
        
        return change_request
    
    except Exception as e:
        logger.error(f"Error creating change request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces/{workspace_id}/change-requests")
async def list_change_requests(workspace_id: str):
    """List change requests for a workspace."""
    try:
        requests = [cr for cr in change_requests_store.values() 
                   if cr.get("workspace_id") == workspace_id]
        return requests
    
    except Exception as e:
        logger.error(f"Error listing change requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Basic Comments (without real-time features)
@router.post("/workspaces/{workspace_id}/comments")
async def add_comment(workspace_id: str, comment_data: Dict[str, Any]):
    """Add a basic comment."""
    try:
        comment_id = f"comment_{datetime.utcnow().timestamp()}"
        comment = {
            "comment_id": comment_id,
            "workspace_id": workspace_id,
            "object_type": comment_data.get("object_type", "general"),
            "object_id": comment_data.get("object_id", ""),
            "author_id": comment_data.get("author_id", "anonymous"),
            "content": comment_data.get("content", ""),
            "created_at": datetime.utcnow().isoformat()
        }
        
        if workspace_id not in comments_store:
            comments_store[workspace_id] = []
        comments_store[workspace_id].append(comment)
        
        logger.info(f"Added comment: {comment_id}")
        return comment
    
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces/{workspace_id}/comments")
async def list_comments(workspace_id: str, object_type: Optional[str] = None, object_id: Optional[str] = None):
    """List comments for workspace or specific object."""
    try:
        comments = comments_store.get(workspace_id, [])
        
        if object_type and object_id:
            comments = [c for c in comments if c.get("object_type") == object_type and c.get("object_id") == object_id]
        
        return comments
    
    except Exception as e:
        logger.error(f"Error listing comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))
