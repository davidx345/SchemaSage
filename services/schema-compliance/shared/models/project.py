"""Project-related models."""

from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID
from .base import BaseModel
from .schema import SchemaModel


class ProjectStatus(str, Enum):
    """Project status."""
    
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectModel(BaseModel):
    """Project model - enterprise grade with UUID support."""
    
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    user_id: UUID  # References auth.users(id)
    schema: Optional[SchemaModel] = None
    
    # Settings stored as JSONB
    settings: Dict[str, Any] = {}
    tags: List[str] = []
    
    # Sharing and collaboration
    is_public: bool = False
    collaborators: List[UUID] = []  # List of user UUIDs
    
    # File information (for display purposes)
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    
    # Enterprise features
    search_vector: Optional[str] = None  # Full-text search
    retention_until: Optional[str] = None  # Data retention
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Customer Database Migration",
                "description": "Migration of legacy customer data to new schema",
                "status": "active",
                "settings": {
                    "auto_backup": True,
                    "notification_preferences": ["email", "slack"]
                },
                "tags": ["customer-data", "migration", "production"]
            }
        }


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
    tags: List[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "name": "New Migration Project",
                "description": "Database migration for user system",
                "settings": {"auto_backup": True},
                "tags": ["migration", "users"]
            }
        }


class ProjectUpdateRequest(BaseModel):
    """Request to update a project."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    schema: Optional[SchemaModel] = None
