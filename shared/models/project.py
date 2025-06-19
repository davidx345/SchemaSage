"""Project-related models."""

from typing import List, Optional, Dict, Any
from enum import Enum
from .base import BaseModel
from .schema import SchemaModel


class ProjectStatus(str, Enum):
    """Project status."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectModel(BaseModel):
    """Project model."""
    
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    user_id: str
    schema: Optional[SchemaModel] = None
    
    # Settings
    settings: Dict[str, Any] = {}
    tags: List[str] = []
    
    # Sharing and collaboration
    is_public: bool = False
    collaborators: List[str] = []
    
    # File information
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response model."""
    
    project: ProjectModel
    schema_summary: Optional[Dict[str, Any]] = None
    recent_activity: List[Dict[str, Any]] = []


class ProjectListResponse(BaseModel):
    """Project list response."""
    
    projects: List[ProjectModel] = []
    total: int = 0
    user_stats: Dict[str, Any] = {}


class ProjectCreateRequest(BaseModel):
    """Request to create a project."""
    
    name: str
    description: Optional[str] = None
    file_data: Optional[bytes] = None
    filename: Optional[str] = None
    settings: Dict[str, Any] = {}


class ProjectUpdateRequest(BaseModel):
    """Request to update a project."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    schema: Optional[SchemaModel] = None
