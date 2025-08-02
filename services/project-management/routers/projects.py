"""
Project Management API Routes

Core routes for project CRUD operations, search, and statistics.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from models.schemas import (
    Project, ProjectStatus, ProjectType, CreateProjectRequest, UpdateProjectRequest,
    ProjectListResponse
)
from core.project_manager import ProjectManager, ProjectError

# Router for project management endpoints
router = APIRouter(prefix="/projects", tags=["projects"])

# Service instance
project_manager = ProjectManager()


@router.post("", response_model=Project)
async def create_project(request: CreateProjectRequest):
    """Create a new project"""
    try:
        project = project_manager.create_project(request)
        return project
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[ProjectStatus] = Query(None, description="Filter by project status"),
    project_type: Optional[ProjectType] = Query(None, description="Filter by project type"),
    limit: int = Query(50, ge=1, le=100, description="Number of projects to return"),
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    created_by: Optional[str] = Query(None, description="Filter by creator user ID"),
    name_contains: Optional[str] = Query(None, description="Filter by project name containing text"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)")
):
    """List projects with filtering and pagination"""
    try:
        projects = project_manager.list_projects(
            status=status,
            project_type=project_type,
            limit=limit,
            offset=offset,
            created_by=created_by,
            name_contains=name_contains,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return projects
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a specific project by ID"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, request: UpdateProjectRequest):
    """Update an existing project"""
    try:
        project = project_manager.update_project(project_id, request)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        success = project_manager.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/{query}")
async def search_projects(query: str):
    """Search projects by name or description"""
    try:
        projects = project_manager.search_projects(query)
        return {"projects": projects, "count": len(projects)}
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/comments")
async def add_comment(project_id: str, comment_data: dict):
    """Add a comment to a project"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if "comments" not in project.metadata:
            project.metadata["comments"] = []
        
        comment = {
            "id": len(project.metadata["comments"]),
            "user": comment_data.get("user", "anonymous"),
            "text": comment_data.get("text", ""),
            "timestamp": comment_data.get("timestamp")
        }
        
        project.metadata["comments"].append(comment)
        project_manager.update_project(project_id, {"metadata": project.metadata})
        
        return {"success": True, "comment": comment}
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/comments")
async def get_comments(project_id: str):
    """Get comments for a project"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        comments = project.metadata.get("comments", [])
        return {"comments": comments}
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/comments/{comment_idx}")
async def delete_comment(project_id: str, comment_idx: int):
    """Delete a comment from a project"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        comments = project.metadata.get("comments", [])
        if comment_idx < 0 or comment_idx >= len(comments):
            raise HTTPException(status_code=404, detail="Comment not found")
        
        deleted_comment = comments.pop(comment_idx)
        project.metadata["comments"] = comments
        project_manager.update_project(project_id, {"metadata": project.metadata})
        
        return {"success": True, "deleted_comment": deleted_comment}
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Statistics router
stats_router = APIRouter(prefix="/stats", tags=["statistics"])


@stats_router.get("")
async def get_project_stats():
    """Get project statistics"""
    try:
        stats = project_manager.get_stats()
        return stats
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))
