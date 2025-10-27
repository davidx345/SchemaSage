"""
Database service for Project Management
Handles all database operations for projects, files, collaboration, and templates
"""
import os
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import asynccontextmanager

from models.database_models import (
    Project,
    ProjectFile,
    ProjectSchema,
    ProjectActivity,
    ProjectCollaboration,
    ProjectTemplate,
    Base
)

logger = logging.getLogger(__name__)

class ProjectManagementDatabaseService:
    """Database service for project management functionality"""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
            
        try:
            # Get database URL
            database_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/schemasage")
            
            # Convert to asyncpg driver if needed
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            # ✅ TRANSACTION POOLER CONFIGURATION
            # CRITICAL: Add prepared_statement_cache_size=0 to URL for asyncpg
            if "?" in database_url:
                database_url += "&prepared_statement_cache_size=0"
            else:
                database_url += "?prepared_statement_cache_size=0"
            
            logger.info(f"🔧 PgBouncer transaction pooler: prepared_statement_cache_size=0 added to connection URL")
            
            # Using NullPool-like settings for PgBouncer transaction mode
            # statement_cache_size=0 prevents "prepared statement" errors
            self._engine = create_async_engine(
                database_url,
                poolclass=None,  # Use default pool but with transaction-friendly settings
                pool_size=5,  # Small pool size for transaction pooler
                max_overflow=10,  # Limited overflow
                pool_timeout=30,
                pool_recycle=300,  # Recycle connections every 5 minutes
                pool_pre_ping=True,  # Verify connections before using
                echo=os.getenv("DEBUG_SQL", "false").lower() == "true",
                connect_args={
                    "statement_cache_size": 0,  # CRITICAL: Prevents prepared statement errors
                    "server_settings": {
                        "jit": "off",  # Disable JIT compilation for transaction pooler
                        "statement_timeout": "30000"  # 30 second query timeout
                    }
                },
                execution_options={
                    "compiled_cache": None  # Disable SQLAlchemy's compiled query cache
                }
            )
            
            # Create session factory
            self._session_factory = sessionmaker(
                self._engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            # Create tables if they don't exist
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("✅ Project Management database service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize project management database: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic rollback on error"""
        if not self._initialized:
            await self.initialize()
            
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_project(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        project_type: str = "database_migration",
        settings: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create a new project"""
        try:
            async with self.get_session() as session:
                project = Project(
                    user_id=user_id,
                    name=name,
                    description=description,
                    project_type=project_type,
                    settings=settings or {},
                    tags=tags or [],
                    last_accessed_at=datetime.utcnow()
                )
                
                session.add(project)
                await session.flush()
                
                # Log project creation activity
                await self._log_activity(
                    session,
                    project_id=str(project.id),
                    user_id=user_id,
                    activity_type="project_created",
                    activity_category="project",
                    action="created",
                    description=f"Project '{name}' created"
                )
                
                logger.info(f"Created project {project.id} for user {user_id}")
                return str(project.id)
                
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    async def get_user_projects(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[str] = None,
        project_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's projects"""
        try:
            async with self.get_session() as session:
                query = select(Project).where(Project.user_id == user_id)
                
                if status_filter:
                    query = query.where(Project.status == status_filter)
                
                if project_type_filter:
                    query = query.where(Project.project_type == project_type_filter)
                
                query = query.order_by(desc(Project.last_accessed_at)).limit(limit).offset(offset)
                
                result = await session.execute(query)
                projects = result.scalars().all()
                
                return [
                    {
                        "id": str(project.id),
                        "name": project.name,
                        "description": project.description,
                        "project_type": project.project_type,
                        "status": project.status,
                        "priority": project.priority,
                        "progress_percentage": project.progress_percentage,
                        "total_files": project.total_files,
                        "tags": project.tags,
                        "environment": project.environment,
                        "is_public": project.is_public,
                        "created_at": project.created_at.isoformat(),
                        "updated_at": project.updated_at.isoformat(),
                        "last_accessed_at": project.last_accessed_at.isoformat() if project.last_accessed_at else None
                    }
                    for project in projects
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user projects: {e}")
            return []
    
    async def get_project_details(
        self,
        project_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed project information"""
        try:
            async with self.get_session() as session:
                # Check if user has access (owner or collaborator)
                access_query = select(Project).where(
                    and_(
                        Project.id == project_id,
                        Project.user_id == user_id
                    )
                )
                
                result = await session.execute(access_query)
                project = result.scalar_one_or_none()
                
                if not project:
                    # Check if user is a collaborator
                    collab_query = select(ProjectCollaboration).where(
                        and_(
                            ProjectCollaboration.project_id == project_id,
                            ProjectCollaboration.collaborator_user_id == user_id,
                            ProjectCollaboration.invitation_status == "accepted"
                        )
                    )
                    
                    collab_result = await session.execute(collab_query)
                    collaboration = collab_result.scalar_one_or_none()
                    
                    if not collaboration:
                        return None
                    
                    # Get project through collaboration
                    project_query = select(Project).where(Project.id == project_id)
                    project_result = await session.execute(project_query)
                    project = project_result.scalar_one_or_none()
                    
                    if not project:
                        return None
                
                # Update last accessed
                await session.execute(
                    update(Project)
                    .where(Project.id == project_id)
                    .values(last_accessed_at=datetime.utcnow())
                )
                
                # Get project files count
                files_count_query = select(func.count(ProjectFile.id)).where(
                    ProjectFile.project_id == project_id
                )
                files_count_result = await session.execute(files_count_query)
                files_count = files_count_result.scalar()
                
                # Get schemas count
                schemas_count_query = select(func.count(ProjectSchema.id)).where(
                    ProjectSchema.project_id == project_id
                )
                schemas_count_result = await session.execute(schemas_count_query)
                schemas_count = schemas_count_result.scalar()
                
                return {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "project_type": project.project_type,
                    "status": project.status,
                    "priority": project.priority,
                    "progress_percentage": project.progress_percentage,
                    "settings": project.settings,
                    "preferences": project.preferences,
                    "tags": project.tags,
                    "category": project.category,
                    "environment": project.environment,
                    "is_public": project.is_public,
                    "is_template": project.is_template,
                    "collaborators": project.collaborators,
                    "files_count": files_count,
                    "schemas_count": schemas_count,
                    "estimated_hours": project.estimated_hours,
                    "actual_hours": project.actual_hours,
                    "health_score": project.health_score,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                    "last_accessed_at": project.last_accessed_at.isoformat() if project.last_accessed_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get project details: {e}")
            return None
    
    async def upload_project_file(
        self,
        project_id: str,
        user_id: str,
        filename: str,
        file_content: bytes,
        mime_type: Optional[str] = None
    ) -> str:
        """Upload a file to a project"""
        try:
            async with self.get_session() as session:
                # Verify project access
                project_query = select(Project).where(
                    and_(
                        Project.id == project_id,
                        Project.user_id == user_id
                    )
                )
                
                project_result = await session.execute(project_query)
                project = project_result.scalar_one_or_none()
                
                if not project:
                    raise ValueError("Project not found or access denied")
                
                # Create file hash
                file_hash = hashlib.sha256(file_content).hexdigest()
                
                # Extract file extension
                file_extension = filename.split('.')[-1].lower() if '.' in filename else None
                
                # Create project file
                project_file = ProjectFile(
                    project_id=project_id,
                    user_id=user_id,
                    filename=filename,
                    original_filename=filename,
                    file_extension=file_extension,
                    mime_type=mime_type,
                    file_size_bytes=len(file_content),
                    file_hash=file_hash,
                    file_content=file_content if len(file_content) < 10 * 1024 * 1024 else None  # Store in DB if < 10MB
                )
                
                session.add(project_file)
                await session.flush()
                
                # Update project file count
                await session.execute(
                    update(Project)
                    .where(Project.id == project_id)
                    .values(
                        total_files=Project.total_files + 1,
                        total_size_bytes=Project.total_size_bytes + len(file_content),
                        updated_at=datetime.utcnow()
                    )
                )
                
                # Log activity
                await self._log_activity(
                    session,
                    project_id=project_id,
                    user_id=user_id,
                    activity_type="file_uploaded",
                    activity_category="file",
                    action="uploaded",
                    description=f"File '{filename}' uploaded",
                    target_object_type="file",
                    target_object_id=str(project_file.id)
                )
                
                logger.info(f"Uploaded file {project_file.id} to project {project_id}")
                return str(project_file.id)
                
        except Exception as e:
            logger.error(f"Failed to upload project file: {e}")
            raise
    
    async def save_project_schema(
        self,
        project_id: str,
        user_id: str,
        schema_name: str,
        schema_data: Dict[str, Any],
        source_file_id: Optional[str] = None,
        external_schema_id: Optional[str] = None,
        is_primary: bool = False
    ) -> str:
        """Save a schema to a project"""
        try:
            async with self.get_session() as session:
                # Verify project access
                project_query = select(Project).where(
                    and_(
                        Project.id == project_id,
                        Project.user_id == user_id
                    )
                )
                
                project_result = await session.execute(project_query)
                project = project_result.scalar_one_or_none()
                
                if not project:
                    raise ValueError("Project not found or access denied")
                
                # Extract schema statistics
                tables_count = len(schema_data.get('tables', []))
                columns_count = sum(len(table.get('columns', [])) for table in schema_data.get('tables', []))
                relationships_count = len(schema_data.get('relationships', []))
                
                # Create project schema
                project_schema = ProjectSchema(
                    project_id=project_id,
                    user_id=user_id,
                    schema_name=schema_name,
                    source_file_id=source_file_id,
                    external_schema_id=external_schema_id,
                    schema_data=schema_data,
                    tables_count=tables_count,
                    columns_count=columns_count,
                    relationships_count=relationships_count,
                    is_primary=is_primary
                )
                
                session.add(project_schema)
                await session.flush()
                
                # Log activity
                await self._log_activity(
                    session,
                    project_id=project_id,
                    user_id=user_id,
                    activity_type="schema_added",
                    activity_category="schema",
                    action="created",
                    description=f"Schema '{schema_name}' added to project",
                    target_object_type="schema",
                    target_object_id=str(project_schema.id)
                )
                
                logger.info(f"Saved schema {project_schema.id} to project {project_id}")
                return str(project_schema.id)
                
        except Exception as e:
            logger.error(f"Failed to save project schema: {e}")
            raise
    
    async def _log_activity(
        self,
        session: AsyncSession,
        project_id: str,
        user_id: str,
        activity_type: str,
        activity_category: str,
        action: str,
        description: str,
        target_object_type: Optional[str] = None,
        target_object_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log project activity"""
        try:
            activity = ProjectActivity(
                project_id=project_id,
                user_id=user_id,
                activity_type=activity_type,
                activity_category=activity_category,
                action=action,
                description=description,
                target_object_type=target_object_type,
                target_object_id=target_object_id,
                details=details or {}
            )
            
            session.add(activity)
            
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            # Don't raise - activity logging shouldn't break main functionality
    
    async def get_project_activities(
        self,
        project_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get project activity log"""
        try:
            async with self.get_session() as session:
                # Verify project access
                access_query = select(Project).where(
                    and_(
                        Project.id == project_id,
                        Project.user_id == user_id
                    )
                )
                
                result = await session.execute(access_query)
                project = result.scalar_one_or_none()
                
                if not project:
                    return []
                
                # Get activities
                activities_query = (
                    select(ProjectActivity)
                    .where(ProjectActivity.project_id == project_id)
                    .order_by(desc(ProjectActivity.created_at))
                    .limit(limit)
                )
                
                activities_result = await session.execute(activities_query)
                activities = activities_result.scalars().all()
                
                return [
                    {
                        "id": str(activity.id),
                        "activity_type": activity.activity_type,
                        "activity_category": activity.activity_category,
                        "action": activity.action,
                        "description": activity.description,
                        "target_object_type": activity.target_object_type,
                        "target_object_id": activity.target_object_id,
                        "details": activity.details,
                        "user_id": activity.user_id,
                        "impact_level": activity.impact_level,
                        "is_automated": activity.is_automated,
                        "created_at": activity.created_at.isoformat()
                    }
                    for activity in activities
                ]
                
        except Exception as e:
            logger.error(f"Failed to get project activities: {e}")
            return []
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()

# Global database service instance
project_management_db = ProjectManagementDatabaseService()