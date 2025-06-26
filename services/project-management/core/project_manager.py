"""
Project Management Service Core Logic
"""
from typing import List, Optional, Dict, Any
import uuid
import json
import logging
from datetime import datetime
from models.schemas import Project, ProjectStatus, ProjectType, CreateProjectRequest, UpdateProjectRequest
from models.schemas import GlossaryTerm, GlossaryRequest, SchemaConsistencyCheckRequest, SchemaConsistencyCheckResponse

logger = logging.getLogger(__name__)

class ProjectError(Exception):
    """Base exception for project management errors"""
    pass

class ProjectManager:
    """In-memory project management service (can be extended with database)"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self._projects: Dict[str, Project] = {}
        self._glossary: Dict[str, GlossaryTerm] = {}
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
    
    async def list_glossary_terms(self) -> List[GlossaryTerm]:
        return list(self._glossary.values())

    async def add_glossary_term(self, request: GlossaryRequest) -> GlossaryTerm:
        import uuid
        now = datetime.utcnow()
        term_id = str(uuid.uuid4())
        term = GlossaryTerm(
            id=term_id,
            term=request.term,
            definition=request.definition,
            synonyms=request.synonyms or [],
            created_at=now,
            updated_at=now
        )
        self._glossary[term_id] = term
        return term

    async def update_glossary_term(self, term_id: str, request: GlossaryRequest) -> GlossaryTerm:
        term = self._glossary.get(term_id)
        if not term:
            raise ProjectError(f"Glossary term {term_id} not found")
        term.term = request.term
        term.definition = request.definition
        term.synonyms = request.synonyms or []
        term.updated_at = datetime.utcnow()
        self._glossary[term_id] = term
        return term

    async def delete_glossary_term(self, term_id: str) -> None:
        if term_id in self._glossary:
            del self._glossary[term_id]

    async def schema_consistency_check(self, request: SchemaConsistencyCheckRequest) -> SchemaConsistencyCheckResponse:
        # Simple checks: duplicate column names, missing foreign keys, etc.
        issues = []
        suggestions = []
        seen_columns = set()
        for table in request.tables:
            for col in getattr(table, 'columns', []):
                col_key = (table.name, col.name)
                if col_key in seen_columns:
                    issues.append(f"Duplicate column: {col.name} in table {table.name}")
                else:
                    seen_columns.add(col_key)
                if col.foreign_key and not col.foreign_key:
                    issues.append(f"Column {col.name} in {table.name} is marked as foreign key but has no reference.")
        consistent = len(issues) == 0
        if not consistent:
            suggestions.append("Review issues and update schema definitions.")
        return SchemaConsistencyCheckResponse(
            consistent=consistent,
            issues=issues,
            suggestions=suggestions
        )
