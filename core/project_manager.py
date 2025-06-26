"""
Project Management Service Core Logic
"""
from typing import List, Optional, Dict, Any
import uuid
import json
import logging
from datetime import datetime
from models.schemas import Project, ProjectStatus, ProjectType, CreateProjectRequest, UpdateProjectRequest

logger = logging.getLogger(__name__)

class ProjectError(Exception):
    """Base exception for project management errors"""
    pass

class ProjectManager:
    """In-memory project management service (can be extended with database)"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self._projects: Dict[str, Project] = {}
        logger.info("ProjectManager initialized")
    
    async def create_project(self, request: CreateProjectRequest) -> Project:
        """Create a new project"""
        try:
            project_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            project = Project(
                id=project_id,
                name=request.name,
                description=request.description,
                type=request.type,
                status=ProjectStatus.DRAFT,
                created_at=now,
                updated_at=now,
                metadata=request.metadata or {}
            )
            
            self._projects[project_id] = project
            logger.info(f"Created project: {project.name} ({project_id})")
            return project
            
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            raise ProjectError(f"Failed to create project: {str(e)}")
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID"""
        try:
            project = self._projects.get(project_id)
            if project:
                logger.debug(f"Retrieved project: {project.name} ({project_id})")
            return project
        except Exception as e:
            logger.error(f"Failed to retrieve project {project_id}: {str(e)}")
            raise ProjectError(f"Failed to retrieve project: {str(e)}")
    
    async def update_project(self, project_id: str, request: UpdateProjectRequest) -> Optional[Project]:
        """Update a project"""
        try:
            project = self._projects.get(project_id)
            if not project:
                return None
            
            # Update fields if provided
            if request.name is not None:
                project.name = request.name
            if request.description is not None:
                project.description = request.description
            if request.status is not None:
                project.status = request.status
            if request.metadata is not None:
                project.metadata = request.metadata
            
            project.updated_at = datetime.utcnow()
            
            self._projects[project_id] = project
            logger.info(f"Updated project: {project.name} ({project_id})")
            return project
            
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {str(e)}")
            raise ProjectError(f"Failed to update project: {str(e)}")
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        try:
            if project_id in self._projects:
                project = self._projects.pop(project_id)
                logger.info(f"Deleted project: {project.name} ({project_id})")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {str(e)}")
            raise ProjectError(f"Failed to delete project: {str(e)}")
    
    def save_project(self, project):
        # Save project to storage (file/db)
        pass
    def load_project(self, project_id):
        # Load project from storage
        pass
    def list_projects(self, user_id=None):
        # List projects for user
        pass
    def update_project(self, project_id, data):
        # Update project
        pass
    def delete_project(self, project_id):
        # Delete project
        pass
    
    async def list_projects(
        self, 
        page: int = 1, 
        size: int = 20, 
        status: Optional[ProjectStatus] = None,
        type: Optional[ProjectType] = None
    ) -> tuple[List[Project], int]:
        """List projects with pagination and filtering"""
        try:
            projects = list(self._projects.values())
            
            # Apply filters
            if status:
                projects = [p for p in projects if p.status == status]
            if type:
                projects = [p for p in projects if p.type == type]
            
            # Sort by created_at (newest first)
            projects.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
            
            total = len(projects)
            
            # Apply pagination
            start = (page - 1) * size
            end = start + size
            paginated_projects = projects[start:end]
            
            logger.debug(f"Listed {len(paginated_projects)} projects (page {page}, total {total})")
            return paginated_projects, total
            
        except Exception as e:
            logger.error(f"Failed to list projects: {str(e)}")
            raise ProjectError(f"Failed to list projects: {str(e)}")
    
    async def get_project_count(self) -> int:
        """Get total number of projects"""
        return len(self._projects)
    
    async def search_projects(self, query: str) -> List[Project]:
        """Search projects by name or description"""
        try:
            query_lower = query.lower()
            results = []
            
            for project in self._projects.values():
                if (query_lower in project.name.lower() or 
                    (project.description and query_lower in project.description.lower())):
                    results.append(project)
            
            # Sort by relevance (name matches first, then description)
            results.sort(key=lambda x: (
                query_lower not in x.name.lower(),
                x.created_at or datetime.min
            ), reverse=True)
            
            logger.debug(f"Found {len(results)} projects matching '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search projects: {str(e)}")
            raise ProjectError(f"Failed to search projects: {str(e)}")
