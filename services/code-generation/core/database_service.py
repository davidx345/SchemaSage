"""
Database service for Code Generation
Handles all database operations for code generation jobs, files, templates, and quality metrics
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
    CodeGenerationJob,
    GeneratedCodeFile,
    CodeTemplate,
    CodeGenerationUsageStatistics,
    CodeQualityMetrics,
    UserCodePreferences,
    Base
)

logger = logging.getLogger(__name__)

class CodeGenerationDatabaseService:
    """Database service for code generation functionality"""
    
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
            
            # Create async engine
            self._engine = create_async_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=1800,
                echo=os.getenv("DEBUG_SQL", "false").lower() == "true",
                connect_args={"statement_cache_size": 0}  # Fix for Supabase pgbouncer compatibility
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
            logger.info("✅ Code Generation database service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize code generation database: {e}")
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
    
    async def create_generation_job(
        self,
        user_id: str,
        schema_data: Dict[str, Any],
        output_format: str,
        target_language: str,
        job_name: Optional[str] = None,
        framework: Optional[str] = None,
        generation_settings: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        source_schema_id: Optional[str] = None
    ) -> str:
        """Create a new code generation job"""
        try:
            async with self.get_session() as session:
                job = CodeGenerationJob(
                    user_id=user_id,
                    job_name=job_name or f"Code Generation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    source_schema_id=source_schema_id,
                    project_id=project_id,
                    schema_data=schema_data,
                    output_format=output_format,
                    target_language=target_language,
                    framework=framework,
                    generation_settings=generation_settings or {},
                    include_relationships=generation_settings.get('include_relationships', True) if generation_settings else True,
                    include_constraints=generation_settings.get('include_constraints', True) if generation_settings else True,
                    include_indexes=generation_settings.get('include_indexes', True) if generation_settings else True,
                    include_documentation=generation_settings.get('include_documentation', True) if generation_settings else True
                )
                
                session.add(job)
                await session.flush()
                
                logger.info(f"Created code generation job {job.id} for user {user_id}")
                return str(job.id)
                
        except Exception as e:
            logger.error(f"Failed to create generation job: {e}")
            raise
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress_percentage: Optional[int] = None,
        error_message: Optional[str] = None,
        generation_time_ms: Optional[int] = None
    ):
        """Update job status and progress"""
        try:
            async with self.get_session() as session:
                update_data = {"status": status}
                
                if progress_percentage is not None:
                    update_data["progress_percentage"] = progress_percentage
                
                if error_message:
                    update_data["error_message"] = error_message
                
                if generation_time_ms:
                    update_data["generation_time_ms"] = generation_time_ms
                
                if status == "processing" and progress_percentage == 0:
                    update_data["started_at"] = datetime.utcnow()
                elif status in ["completed", "failed"]:
                    update_data["completed_at"] = datetime.utcnow()
                
                await session.execute(
                    update(CodeGenerationJob)
                    .where(CodeGenerationJob.id == job_id)
                    .values(**update_data)
                )
                
                logger.info(f"Updated generation job {job_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            raise
    
    async def save_generated_file(
        self,
        job_id: str,
        user_id: str,
        filename: str,
        generated_code: str,
        file_type: str = "model",
        language: str = "python",
        template_used: Optional[str] = None
    ) -> str:
        """Save a generated code file"""
        try:
            async with self.get_session() as session:
                # Create code hash
                code_hash = hashlib.sha256(generated_code.encode()).hexdigest()
                
                # Calculate metrics
                line_count = len(generated_code.split('\n'))
                file_size_bytes = len(generated_code.encode())
                
                # Create generated file
                generated_file = GeneratedCodeFile(
                    generation_job_id=job_id,
                    user_id=user_id,
                    filename=filename,
                    file_type=file_type,
                    generated_code=generated_code,
                    code_hash=code_hash,
                    file_size_bytes=file_size_bytes,
                    line_count=line_count,
                    template_used=template_used,
                    language=language,
                    syntax_valid=True  # TODO: Add syntax validation
                )
                
                session.add(generated_file)
                await session.flush()
                
                # Update job statistics
                await session.execute(
                    update(CodeGenerationJob)
                    .where(CodeGenerationJob.id == job_id)
                    .values(
                        generated_files_count=CodeGenerationJob.generated_files_count + 1,
                        total_lines_generated=CodeGenerationJob.total_lines_generated + line_count,
                        total_size_bytes=CodeGenerationJob.total_size_bytes + file_size_bytes
                    )
                )
                
                logger.info(f"Saved generated file {generated_file.id} for job {job_id}")
                return str(generated_file.id)
                
        except Exception as e:
            logger.error(f"Failed to save generated file: {e}")
            raise
    
    async def get_user_generation_jobs(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[str] = None,
        format_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's generation jobs"""
        try:
            async with self.get_session() as session:
                query = select(CodeGenerationJob).where(
                    CodeGenerationJob.user_id == user_id
                )
                
                if status_filter:
                    query = query.where(CodeGenerationJob.status == status_filter)
                
                if format_filter:
                    query = query.where(CodeGenerationJob.output_format == format_filter)
                
                query = query.order_by(desc(CodeGenerationJob.created_at)).limit(limit).offset(offset)
                
                result = await session.execute(query)
                jobs = result.scalars().all()
                
                return [
                    {
                        "id": str(job.id),
                        "job_name": job.job_name,
                        "output_format": job.output_format,
                        "target_language": job.target_language,
                        "framework": job.framework,
                        "status": job.status,
                        "progress_percentage": job.progress_percentage,
                        "generated_files_count": job.generated_files_count,
                        "total_lines_generated": job.total_lines_generated,
                        "generation_time_ms": job.generation_time_ms,
                        "code_quality_score": job.code_quality_score,
                        "created_at": job.created_at.isoformat(),
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                        "error_message": job.error_message
                    }
                    for job in jobs
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user generation jobs: {e}")
            return []
    
    async def get_generated_files(
        self,
        job_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get generated files for a job"""
        try:
            async with self.get_session() as session:
                # Verify job ownership
                job_query = select(CodeGenerationJob).where(
                    and_(
                        CodeGenerationJob.id == job_id,
                        CodeGenerationJob.user_id == user_id
                    )
                )
                
                job_result = await session.execute(job_query)
                job = job_result.scalar_one_or_none()
                
                if not job:
                    return []
                
                # Get generated files
                files_query = (
                    select(GeneratedCodeFile)
                    .where(GeneratedCodeFile.generation_job_id == job_id)
                    .order_by(GeneratedCodeFile.filename)
                )
                
                files_result = await session.execute(files_query)
                files = files_result.scalars().all()
                
                return [
                    {
                        "id": str(file.id),
                        "filename": file.filename,
                        "file_type": file.file_type,
                        "language": file.language,
                        "generated_code": file.generated_code,
                        "file_size_bytes": file.file_size_bytes,
                        "line_count": file.line_count,
                        "template_used": file.template_used,
                        "syntax_valid": file.syntax_valid,
                        "download_count": file.download_count,
                        "created_at": file.created_at.isoformat()
                    }
                    for file in files
                ]
                
        except Exception as e:
            logger.error(f"Failed to get generated files: {e}")
            return []
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user code generation preferences"""
        try:
            async with self.get_session() as session:
                query = select(UserCodePreferences).where(
                    UserCodePreferences.user_id == user_id
                )
                
                result = await session.execute(query)
                prefs = result.scalar_one_or_none()
                
                if not prefs:
                    # Create default preferences
                    prefs = UserCodePreferences(user_id=user_id)
                    session.add(prefs)
                    await session.commit()
                
                return {
                    "preferred_output_format": prefs.preferred_output_format,
                    "preferred_language": prefs.preferred_language,
                    "preferred_framework": prefs.preferred_framework,
                    "code_style": prefs.code_style,
                    "naming_convention": prefs.naming_convention,
                    "indentation_type": prefs.indentation_type,
                    "indentation_size": prefs.indentation_size,
                    "include_type_hints": prefs.include_type_hints,
                    "include_docstrings": prefs.include_docstrings,
                    "include_comments": prefs.include_comments,
                    "include_examples": prefs.include_examples,
                    "include_tests": prefs.include_tests,
                    "generate_migrations": prefs.generate_migrations,
                    "use_dataclasses": prefs.use_dataclasses,
                    "use_async_code": prefs.use_async_code,
                    "file_organization": prefs.file_organization,
                    "export_format": prefs.export_format,
                    "preferred_templates": prefs.preferred_templates or [],
                    "custom_variables": prefs.custom_variables or {}
                }
                
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    async def update_usage_statistics(
        self,
        user_id: str,
        output_format: str,
        generation_completed: bool = False,
        generation_failed: bool = False,
        files_generated: int = 0,
        lines_generated: int = 0,
        generation_time_ms: Optional[int] = None
    ):
        """Update daily usage statistics"""
        try:
            async with self.get_session() as session:
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Get or create today's stats
                stats_query = select(CodeGenerationUsageStatistics).where(
                    and_(
                        CodeGenerationUsageStatistics.user_id == user_id,
                        CodeGenerationUsageStatistics.date == today
                    )
                )
                
                result = await session.execute(stats_query)
                stats = result.scalar_one_or_none()
                
                if not stats:
                    stats = CodeGenerationUsageStatistics(user_id=user_id, date=today)
                    session.add(stats)
                
                # Update stats
                stats.generation_jobs_created += 1
                
                if generation_completed:
                    stats.generation_jobs_completed += 1
                    stats.files_generated += files_generated
                    stats.total_lines_generated += lines_generated
                
                if generation_failed:
                    stats.generation_jobs_failed += 1
                
                # Update format-specific counters
                if output_format == "sqlalchemy":
                    stats.sqlalchemy_generations += 1
                elif output_format == "django":
                    stats.django_generations += 1
                elif output_format == "sql":
                    stats.sql_generations += 1
                elif output_format == "typescript":
                    stats.typescript_generations += 1
                else:
                    stats.other_format_generations += 1
                
                if generation_time_ms:
                    stats.total_generation_time_ms += generation_time_ms
                    # Update average
                    total_jobs = stats.generation_jobs_completed + stats.generation_jobs_failed
                    if total_jobs > 0:
                        stats.average_generation_time_ms = stats.total_generation_time_ms // total_jobs
                
                logger.info(f"Updated usage stats for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to update usage statistics: {e}")
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()

# Global database service instance
code_generation_db = CodeGenerationDatabaseService()