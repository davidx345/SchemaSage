"""
Database service for Schema Detection
Handles all database operations for schema detection and analysis
"""
import os
import logging
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import asynccontextmanager

from models.database_models import (
    SchemaDetectionJob,
    DetectedSchema,
    SchemaAnalysis,
    SchemaUsageStatistics,
    SchemaFeedback,
    Base
)

logger = logging.getLogger(__name__)

class SchemaDetectionDatabaseService:
    """Database service for schema detection functionality"""
    
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
            
            # Using transaction-friendly settings for PgBouncer
            self._engine = create_async_engine(
                database_url,
                poolclass=None,  # Use default pool with transaction-friendly settings
                pool_size=5,  # Small pool size for transaction pooler
                max_overflow=10,  # Limited overflow
                pool_timeout=30,
                pool_recycle=300,  # Recycle connections every 5 minutes
                pool_pre_ping=True,  # Verify connections before using
                echo=os.getenv("DEBUG_SQL", "false").lower() == "true",
                connect_args={
                    "statement_cache_size": 0,  # CRITICAL: Prevents prepared statement errors
                    "server_settings": {
                        "jit": "off",  # Disable JIT compilation
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
            logger.info("✅ Schema Detection database service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize schema detection database: {e}")
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
    
    async def create_detection_job(
        self,
        user_id: str,
        input_format: str,
        input_data: str,
        job_name: Optional[str] = None,
        detection_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new schema detection job"""
        try:
            async with self.get_session() as session:
                # Calculate input hash for deduplication
                input_hash = hashlib.sha256(input_data.encode()).hexdigest()
                
                # Create detection job
                job = SchemaDetectionJob(
                    user_id=user_id,
                    job_name=job_name or f"Schema Detection {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    input_format=input_format,
                    input_size_bytes=len(input_data.encode()),
                    input_hash=input_hash,
                    detection_settings=detection_settings or {},
                    ai_enhancement_enabled=detection_settings.get('enable_ai_enhancement', True) if detection_settings else True,
                    relationship_detection_enabled=detection_settings.get('detect_relations', True) if detection_settings else True,
                    confidence_threshold=detection_settings.get('confidence_threshold', 0.7) if detection_settings else 0.7
                )
                
                session.add(job)
                await session.flush()
                
                logger.info(f"Created schema detection job {job.id} for user {user_id}")
                return str(job.id)
                
        except Exception as e:
            logger.error(f"Failed to create detection job: {e}")
            raise
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress_percentage: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update job status and progress"""
        try:
            async with self.get_session() as session:
                update_data = {"status": status}
                
                if progress_percentage is not None:
                    update_data["progress_percentage"] = progress_percentage
                
                if error_message:
                    update_data["error_message"] = error_message
                
                if status == "processing" and progress_percentage == 0:
                    update_data["started_at"] = datetime.utcnow()
                elif status in ["completed", "failed"]:
                    update_data["completed_at"] = datetime.utcnow()
                
                await session.execute(
                    update(SchemaDetectionJob)
                    .where(SchemaDetectionJob.id == job_id)
                    .values(**update_data)
                )
                
                logger.info(f"Updated job {job_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            raise
    
    async def save_detected_schema(
        self,
        job_id: str,
        user_id: str,
        schema_name: str,
        schema_structure: Dict[str, Any],
        detection_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save a detected schema"""
        try:
            async with self.get_session() as session:
                # Extract schema statistics
                tables_data = schema_structure.get('tables', [])
                relationships_data = schema_structure.get('relationships', [])
                
                table_count = len(tables_data)
                column_count = sum(len(table.get('columns', [])) for table in tables_data)
                relationship_count = len(relationships_data)
                
                # Create detected schema
                schema = DetectedSchema(
                    detection_job_id=job_id,
                    user_id=user_id,
                    schema_name=schema_name,
                    schema_structure=schema_structure,
                    tables_data=tables_data,
                    relationships_data=relationships_data,
                    table_count=table_count,
                    column_count=column_count,
                    relationship_count=relationship_count,
                    detection_confidence=detection_metadata.get('confidence', 0.8) if detection_metadata else 0.8,
                    detection_method=detection_metadata.get('method', 'hybrid') if detection_metadata else 'hybrid',
                    ai_suggestions=detection_metadata.get('ai_suggestions', {}) if detection_metadata else {}
                )
                
                session.add(schema)
                await session.flush()
                
                # Update job with results
                await session.execute(
                    update(SchemaDetectionJob)
                    .where(SchemaDetectionJob.id == job_id)
                    .values(
                        detected_tables_count=table_count,
                        detected_columns_count=column_count,
                        detected_relationships_count=relationship_count,
                        overall_confidence_score=detection_metadata.get('confidence', 0.8) if detection_metadata else 0.8
                    )
                )
                
                logger.info(f"Saved detected schema {schema.id} for job {job_id}")
                return str(schema.id)
                
        except Exception as e:
            logger.error(f"Failed to save detected schema: {e}")
            raise
    
    async def get_user_detection_jobs(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's detection jobs"""
        try:
            async with self.get_session() as session:
                query = select(SchemaDetectionJob).where(
                    SchemaDetectionJob.user_id == user_id
                )
                
                if status_filter:
                    query = query.where(SchemaDetectionJob.status == status_filter)
                
                query = query.order_by(desc(SchemaDetectionJob.created_at)).limit(limit).offset(offset)
                
                result = await session.execute(query)
                jobs = result.scalars().all()
                
                return [
                    {
                        "id": str(job.id),
                        "job_name": job.job_name,
                        "input_format": job.input_format,
                        "status": job.status,
                        "progress_percentage": job.progress_percentage,
                        "detected_tables_count": job.detected_tables_count,
                        "detected_columns_count": job.detected_columns_count,
                        "detected_relationships_count": job.detected_relationships_count,
                        "overall_confidence_score": job.overall_confidence_score,
                        "processing_time_ms": job.processing_time_ms,
                        "created_at": job.created_at.isoformat(),
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                        "error_message": job.error_message
                    }
                    for job in jobs
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user detection jobs: {e}")
            return []
    
    async def get_user_schemas(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's detected schemas"""
        try:
            async with self.get_session() as session:
                query = (
                    select(DetectedSchema)
                    .where(DetectedSchema.user_id == user_id)
                    .order_by(desc(DetectedSchema.created_at))
                    .limit(limit)
                    .offset(offset)
                )
                
                result = await session.execute(query)
                schemas = result.scalars().all()
                
                return [
                    {
                        "id": str(schema.id),
                        "schema_name": schema.schema_name,
                        "schema_type": schema.schema_type,
                        "table_count": schema.table_count,
                        "column_count": schema.column_count,
                        "relationship_count": schema.relationship_count,
                        "detection_confidence": schema.detection_confidence,
                        "created_at": schema.created_at.isoformat(),
                        "last_accessed_at": schema.last_accessed_at.isoformat() if schema.last_accessed_at else None,
                        "access_count": schema.access_count
                    }
                    for schema in schemas
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user schemas: {e}")
            return []
    
    async def get_schema_details(
        self,
        schema_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed schema information"""
        try:
            async with self.get_session() as session:
                query = select(DetectedSchema).where(
                    and_(
                        DetectedSchema.id == schema_id,
                        DetectedSchema.user_id == user_id
                    )
                )
                
                result = await session.execute(query)
                schema = result.scalar_one_or_none()
                
                if not schema:
                    return None
                
                # Update access tracking
                await session.execute(
                    update(DetectedSchema)
                    .where(DetectedSchema.id == schema_id)
                    .values(
                        access_count=DetectedSchema.access_count + 1,
                        last_accessed_at=datetime.utcnow()
                    )
                )
                
                return {
                    "id": str(schema.id),
                    "schema_name": schema.schema_name,
                    "schema_type": schema.schema_type,
                    "schema_structure": schema.schema_structure,
                    "tables_data": schema.tables_data,
                    "relationships_data": schema.relationships_data,
                    "table_count": schema.table_count,
                    "column_count": schema.column_count,
                    "relationship_count": schema.relationship_count,
                    "detection_confidence": schema.detection_confidence,
                    "detection_method": schema.detection_method,
                    "ai_suggestions": schema.ai_suggestions,
                    "created_at": schema.created_at.isoformat(),
                    "access_count": schema.access_count + 1
                }
                
        except Exception as e:
            logger.error(f"Failed to get schema details: {e}")
            return None
    
    async def update_usage_statistics(
        self,
        user_id: str,
        detection_completed: bool = False,
        detection_failed: bool = False,
        processing_time_ms: Optional[int] = None,
        ai_tokens_used: int = 0,
        confidence_score: Optional[float] = None
    ):
        """Update daily usage statistics"""
        try:
            async with self.get_session() as session:
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Get or create today's stats
                stats_query = select(SchemaUsageStatistics).where(
                    and_(
                        SchemaUsageStatistics.user_id == user_id,
                        SchemaUsageStatistics.date == today
                    )
                )
                
                result = await session.execute(stats_query)
                stats = result.scalar_one_or_none()
                
                if not stats:
                    stats = SchemaUsageStatistics(user_id=user_id, date=today)
                    session.add(stats)
                
                # Update stats
                stats.detection_jobs_created += 1
                
                if detection_completed:
                    stats.detection_jobs_completed += 1
                    stats.schemas_detected += 1
                
                if detection_failed:
                    stats.detection_jobs_failed += 1
                
                if processing_time_ms:
                    stats.total_processing_time_ms += processing_time_ms
                    # Update average
                    total_jobs = stats.detection_jobs_completed + stats.detection_jobs_failed
                    if total_jobs > 0:
                        stats.average_processing_time_ms = stats.total_processing_time_ms // total_jobs
                
                if ai_tokens_used > 0:
                    stats.ai_tokens_consumed += ai_tokens_used
                    stats.ai_enhancements_used += 1
                
                if confidence_score:
                    # Update average confidence score
                    current_avg = stats.average_confidence_score
                    current_count = stats.schemas_detected
                    if current_count > 1:
                        new_avg = ((current_avg * (current_count - 1)) + confidence_score) / current_count
                        stats.average_confidence_score = new_avg
                    else:
                        stats.average_confidence_score = confidence_score
                
                stats.average_confidence_score = confidence_score
                
                logger.info(f"Updated usage stats for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to update usage statistics: {e}")
    
    # ============================================================================
    # Cloud Deployment Methods
    # ============================================================================
    
    async def create_cloud_deployment(self, deployment_data: Dict[str, Any]) -> Any:
        """Create a new cloud deployment record"""
        try:
            from models.database_models import CloudDeployment
            
            async with self.get_session() as session:
                deployment = CloudDeployment(**deployment_data)
                session.add(deployment)
                await session.commit()
                await session.refresh(deployment)
                
                logger.info(f"Created cloud deployment: {deployment.id}")
                return deployment
                
        except Exception as e:
            logger.error(f"Failed to create cloud deployment: {e}")
            raise
    
    async def get_cloud_deployment(self, deployment_id: str, user_id: str) -> Optional[Any]:
        """Get a cloud deployment by ID"""
        try:
            from models.database_models import CloudDeployment
            from uuid import UUID
            
            async with self.get_session() as session:
                result = await session.execute(
                    select(CloudDeployment).where(
                        and_(
                            CloudDeployment.id == UUID(deployment_id),
                            CloudDeployment.user_id == user_id
                        )
                    )
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Failed to get cloud deployment: {e}")
            return None
    
    async def update_deployment_status(
        self,
        deployment_id: str,
        status: str,
        progress: int = None,
        error_message: str = None
    ):
        """Update deployment status"""
        try:
            from models.database_models import CloudDeployment
            from uuid import UUID
            
            async with self.get_session() as session:
                stmt = (
                    update(CloudDeployment)
                    .where(CloudDeployment.id == UUID(deployment_id))
                    .values(status=status)
                )
                
                if progress is not None:
                    stmt = stmt.values(progress_percentage=progress)
                
                if error_message:
                    stmt = stmt.values(error_message=error_message)
                
                if status == "ready":
                    stmt = stmt.values(completed_at=datetime.now())
                elif status == "provisioning" and progress == 20:
                    stmt = stmt.values(started_at=datetime.now())
                
                await session.execute(stmt)
                await session.commit()
                
                logger.info(f"Updated deployment {deployment_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update deployment status: {e}")
    
    async def update_deployment_instance(
        self,
        deployment_id: str,
        cloud_instance_id: str = None,
        connection_string: str = None,
        endpoint: str = None,
        port: int = None
    ):
        """Update deployment instance details"""
        try:
            from models.database_models import CloudDeployment
            from uuid import UUID
            
            async with self.get_session() as session:
                values = {}
                if cloud_instance_id:
                    values['cloud_instance_id'] = cloud_instance_id
                if connection_string:
                    values['connection_string'] = connection_string
                if endpoint:
                    values['endpoint'] = endpoint
                if port:
                    values['port'] = port
                
                if values:
                    stmt = (
                        update(CloudDeployment)
                        .where(CloudDeployment.id == UUID(deployment_id))
                        .values(**values)
                    )
                    await session.execute(stmt)
                    await session.commit()
                    
                    logger.info(f"Updated deployment {deployment_id} instance details")
                    
        except Exception as e:
            logger.error(f"Failed to update deployment instance: {e}")
    
    async def list_cloud_deployments(
        self,
        user_id: str,
        status: str = None,
        provider: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Any]:
        """List cloud deployments for a user"""
        try:
            from models.database_models import CloudDeployment
            
            async with self.get_session() as session:
                query = select(CloudDeployment).where(
                    CloudDeployment.user_id == user_id
                )
                
                if status:
                    query = query.where(CloudDeployment.status == status)
                
                if provider:
                    query = query.where(CloudDeployment.provider == provider)
                
                query = query.order_by(desc(CloudDeployment.created_at))
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to list cloud deployments: {e}")
            return []
    
    async def count_cloud_deployments(
        self,
        user_id: str,
        status: str = None,
        provider: str = None
    ) -> int:
        """Count cloud deployments for a user"""
        try:
            from models.database_models import CloudDeployment
            
            async with self.get_session() as session:
                query = select(func.count(CloudDeployment.id)).where(
                    CloudDeployment.user_id == user_id
                )
                
                if status:
                    query = query.where(CloudDeployment.status == status)
                
                if provider:
                    query = query.where(CloudDeployment.provider == provider)
                
                result = await session.execute(query)
                return result.scalar()
                
        except Exception as e:
            logger.error(f"Failed to count cloud deployments: {e}")
            return 0
    
    async def delete_cloud_deployment(self, deployment_id: str, user_id: str) -> bool:
        """Delete a cloud deployment"""
        try:
            from models.database_models import CloudDeployment
            from uuid import UUID
            
            async with self.get_session() as session:
                stmt = delete(CloudDeployment).where(
                    and_(
                        CloudDeployment.id == UUID(deployment_id),
                        CloudDeployment.user_id == user_id
                    )
                )
                await session.execute(stmt)
                await session.commit()
                
                logger.info(f"Deleted cloud deployment: {deployment_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete cloud deployment: {e}")
            return False
    
    async def create_deployment_log(
        self,
        deployment_id: str,
        level: str,
        message: str,
        step: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Create a deployment log entry"""
        try:
            from models.database_models import DeploymentLog
            from uuid import UUID
            
            async with self.get_session() as session:
                log = DeploymentLog(
                    deployment_id=UUID(deployment_id),
                    level=level,
                    message=message,
                    step=step,
                    metadata=metadata
                )
                session.add(log)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to create deployment log: {e}")
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()


# Global database service instance
schema_detection_db = SchemaDetectionDatabaseService()