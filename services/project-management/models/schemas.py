"""
Data models for Project Management Service
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ProjectStatus(str, Enum):
    """Project status options"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DRAFT = "draft"

class ProjectType(str, Enum):
    """Project type options"""
    SCHEMA_DETECTION = "schema_detection"
    CODE_GENERATION = "code_generation"
    DATABASE_MIGRATION = "database_migration"
    DATA_ANALYSIS = "data_analysis"

class Project(BaseModel):
    """Project information"""
    id: Optional[str] = Field(None, description="Project ID")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    type: ProjectType = Field(..., description="Type of project")
    status: ProjectStatus = Field(ProjectStatus.DRAFT, description="Project status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional project metadata")

class CreateProjectRequest(BaseModel):
    """Request to create a new project"""
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    type: ProjectType = Field(..., description="Type of project")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional project metadata")

class UpdateProjectRequest(BaseModel):
    """Request to update a project"""
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    status: Optional[ProjectStatus] = Field(None, description="Project status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional project metadata")

class ProjectListResponse(BaseModel):
    """Response for project listing"""
    projects: List[Project] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")

class ApiHealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    project_count: int = Field(..., description="Total number of projects")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
