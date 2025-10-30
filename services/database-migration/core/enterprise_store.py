"""
Enterprise Database Connection Store
PostgreSQL-backed persistent storage with encryption, audit trails, and user isolation
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from contextlib import asynccontextmanager

from models.database_tables import (
    DatabaseConnection, 
    ConnectionAuditLog, 
    ConnectionSecret, 
    UserConnectionQuota,
    SchemaSnapshot,
    Base
)
from core.encryption import connection_encryption
from core.auth import UserContext

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration for persistent storage"""
    
    @staticmethod
    def get_database_url():
        """Get database URL with proper async driver format"""
        database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://postgres:password@localhost:5432/schemasage_db"
        )
        
        # Convert to asyncpg driver if needed
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
            logger.info("🔄 Converted DATABASE_URL from postgres:// to postgresql+asyncpg://")
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            logger.info("🔄 Converted DATABASE_URL from postgresql:// to postgresql+asyncpg://")
        return database_url
    
    DATABASE_URL = get_database_url.__func__()
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes


class EnterpriseConnectionStore:
    """
    Enterprise-grade database connection store
    
    Features:
    - PostgreSQL persistence
    - AES-256 encryption for sensitive data
    - User isolation and multi-tenancy
    - Audit logging
    - Connection health monitoring
    - Schema versioning
    - Quota management
    """
    
    def __init__(self):
        self.config = DatabaseConfig()
        self._engine = None
        self._session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connection and create tables if needed"""
        if self._initialized:
            return
            
        try:
            # ✅ TRANSACTION POOLER CONFIGURATION
            # Use DATABASE_URL for API (transaction pooler)
            # Scripts should use DATABASE_URL_SESSION (session pooler)
            db_url = self.config.DATABASE_URL
            
            # CRITICAL: Add prepared_statement_cache_size=0 to URL for asyncpg
            if "?" in db_url:
                db_url += "&prepared_statement_cache_size=0"
            else:
                db_url += "?prepared_statement_cache_size=0"
            
            logger.info(f"🔧 PgBouncer transaction pooler: prepared_statement_cache_size=0 added to connection URL")
            
            # Create async engine with transaction pooler settings
            self._engine = create_async_engine(
                db_url,
                pool_size=3,  # Small pool for transaction pooler
                max_overflow=5,  # Limited overflow
                pool_timeout=10,  # Fail fast if pool exhausted
                pool_recycle=300,  # Recycle every 5 minutes
                pool_pre_ping=True,  # Verify connections
                echo=os.getenv("DEBUG_SQL", "false").lower() == "true",
                connect_args={
                    "statement_cache_size": 0,  # CRITICAL: No prepared statements
                    "command_timeout": 10,  # Fast timeout
                    "server_settings": {
                        "application_name": "database-migration-service",
                        "jit": "off",  # Disable JIT
                        "statement_timeout": "30000"  # 30s timeout
                    }
                },
                pool_reset_on_return="commit",  # Reset on return
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
            logger.info("✅ Enterprise connection store initialized with PostgreSQL backend")
            logger.info("✅ PgBouncer transaction pooler config: statement_cache_size=0")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection store: {e}")
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
    
    async def save_connection(
        self, 
        connection_data: Dict[str, Any], 
        user: UserContext,
        request_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save database connection with encryption and audit trail
        """
        try:
            async with self.get_session() as session:
                # Check user quota
                await self._check_user_quota(session, user.user_id)
                
                # Encrypt sensitive data
                sensitive_data = {
                    'password': connection_data.get('password', ''),
                    'connection_params': connection_data.get('connection_params', {}),
                    'ssl_cert_content': connection_data.get('ssl_cert_content', ''),
                    'ssl_key_content': connection_data.get('ssl_key_content', '')
                }
                
                encrypted_password, password_salt = connection_encryption.encrypt_password(
                    connection_data.get('password', '')
                )
                
                encrypted_params, params_salt, _ = connection_encryption.encrypt_connection_data(
                    sensitive_data
                )
                
                # Create connection record
                db_connection = DatabaseConnection(
                    user_id=user.user_id,
                    name=connection_data.get('name', ''),
                    description=connection_data.get('description', ''),
                    db_type=connection_data.get('type', ''),
                    host=connection_data.get('host', ''),
                    port=connection_data.get('port'),
                    database_name=connection_data.get('database', ''),
                    username=connection_data.get('username', ''),
                    encrypted_password=encrypted_password,
                    ssl_enabled=connection_data.get('ssl_enabled', False),
                    ssl_mode=connection_data.get('ssl_mode', 'prefer'),
                    status='created',
                    created_by=user.user_id,
                    environment=connection_data.get('environment', 'development'),
                    tags=connection_data.get('tags', {}),
                    team_id=connection_data.get('team_id')
                )
                
                session.add(db_connection)
                await session.flush()  # Get the ID
                
                # Create secret record
                connection_secret = ConnectionSecret(
                    connection_id=db_connection.id,
                    encrypted_data=encrypted_params,
                    salt=params_salt,
                    encryption_key_version=1
                )
                
                session.add(connection_secret)
                
                # Update user quota
                await self._update_user_quota(session, user.user_id, increment_connections=1)
                
                # Log audit event
                await self._log_audit_event(
                    session,
                    connection_id=db_connection.id,
                    user_id=user.user_id,
                    action="connection_created",
                    success=True,
                    request_context=request_context,
                    metadata=connection_encryption.mask_sensitive_data(connection_data)
                )
                
                logger.info(f"✅ Saved connection {db_connection.id} for user {user.user_id}")
                return str(db_connection.id)
                
        except Exception as e:
            logger.error(f"❌ Failed to save connection: {e}")
            await self._log_audit_event(
                None,
                connection_id=None,
                user_id=user.user_id,
                action="connection_create_failed",
                success=False,
                request_context=request_context,
                error_message=str(e)
            )
            raise ValueError(f"Failed to save connection: {e}")
    
    async def get_user_connections(
        self, 
        user: UserContext,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all connections for a user with decrypted data
        """
        try:
            async with self.get_session() as session:
                # Build query
                query = select(DatabaseConnection).where(
                    DatabaseConnection.user_id == user.user_id
                )
                
                if not include_inactive:
                    query = query.where(DatabaseConnection.is_active == True)
                
                query = query.order_by(desc(DatabaseConnection.updated_at))
                
                result = await session.execute(query)
                connections = result.scalars().all()
                
                # Convert to dict format with decrypted data
                connection_list = []
                for conn in connections:
                    connection_dict = {
                        'id': str(conn.id),
                        'name': conn.name,
                        'description': conn.description,
                        'type': conn.db_type,
                        'host': conn.host,
                        'port': conn.port,
                        'database': conn.database_name,
                        'username': conn.username,
                        'ssl_enabled': conn.ssl_enabled,
                        'ssl_mode': conn.ssl_mode,
                        'status': conn.status,
                        'environment': conn.environment,
                        'tags': conn.tags,
                        'created_at': conn.created_at.isoformat() if conn.created_at else None,
                        'updated_at': conn.updated_at.isoformat() if conn.updated_at else None,
                        'last_tested_at': conn.last_tested_at.isoformat() if conn.last_tested_at else None,
                        'connection_test_count': conn.connection_test_count,
                        'successful_connections': conn.successful_connections,
                        'failed_connections': conn.failed_connections,
                        'average_response_time_ms': conn.average_response_time_ms
                    }
                    
                    # Get decrypted password (only for connection testing)
                    try:
                        secret_query = select(ConnectionSecret).where(
                            ConnectionSecret.connection_id == conn.id
                        )
                        secret_result = await session.execute(secret_query)
                        secret = secret_result.scalar_one_or_none()
                        
                        if secret:
                            decrypted_data = connection_encryption.decrypt_connection_data(
                                secret.encrypted_data, 
                                secret.salt, 
                                secret.encryption_key_version
                            )
                            connection_dict['password'] = decrypted_data.get('password', '')
                        
                    except Exception as e:
                        logger.error(f"Failed to decrypt connection {conn.id}: {e}")
                        connection_dict['password'] = ''
                    
                    connection_list.append(connection_dict)
                
                return connection_list
                
        except Exception as e:
            logger.error(f"❌ Failed to get user connections: {e}")
            return []
    
    async def get_connection(
        self, 
        connection_id: str, 
        user: UserContext
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific connection with user access control
        """
        try:
            async with self.get_session() as session:
                query = select(DatabaseConnection).where(
                    and_(
                        DatabaseConnection.id == connection_id,
                        DatabaseConnection.user_id == user.user_id,
                        DatabaseConnection.is_active == True
                    )
                )
                
                result = await session.execute(query)
                connection = result.scalar_one_or_none()
                
                if not connection:
                    return None
                
                # Get all user connections and find the matching one
                connections = await self.get_user_connections(user)
                return next((conn for conn in connections if conn['id'] == connection_id), None)
                
        except Exception as e:
            logger.error(f"❌ Failed to get connection {connection_id}: {e}")
            return None
    
    async def update_connection_status(
        self, 
        connection_id: str, 
        user: UserContext,
        status: str,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update connection status and health metrics
        """
        try:
            async with self.get_session() as session:
                # Update connection
                update_data = {
                    'status': status,
                    'last_tested_at': datetime.utcnow(),
                    'last_connection_attempt': datetime.utcnow(),
                    'connection_test_count': DatabaseConnection.connection_test_count + 1
                }
                
                if status == 'connected':
                    update_data['successful_connections'] = DatabaseConnection.successful_connections + 1
                else:
                    update_data['failed_connections'] = DatabaseConnection.failed_connections + 1
                
                if response_time_ms is not None:
                    update_data['last_response_time_ms'] = response_time_ms
                    # Update average (simple moving average)
                    update_data['average_response_time_ms'] = func.coalesce(
                        (DatabaseConnection.average_response_time_ms + response_time_ms) / 2,
                        response_time_ms
                    )
                
                query = update(DatabaseConnection).where(
                    and_(
                        DatabaseConnection.id == connection_id,
                        DatabaseConnection.user_id == user.user_id
                    )
                ).values(**update_data)
                
                result = await session.execute(query)
                
                # Log audit event
                await self._log_audit_event(
                    session,
                    connection_id=connection_id,
                    user_id=user.user_id,
                    action="connection_tested",
                    success=status == 'connected',
                    request_context=request_context,
                    metadata={
                        'status': status,
                        'response_time_ms': response_time_ms,
                        'error_message': error_message
                    }
                )
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Failed to update connection status: {e}")
            return False
    
    async def delete_connection(
        self, 
        connection_id: str, 
        user: UserContext,
        request_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Soft delete connection (mark as inactive)
        """
        try:
            async with self.get_session() as session:
                query = update(DatabaseConnection).where(
                    and_(
                        DatabaseConnection.id == connection_id,
                        DatabaseConnection.user_id == user.user_id
                    )
                ).values(
                    is_active=False,
                    archived_at=datetime.utcnow(),
                    archived_by=user.user_id
                )
                
                result = await session.execute(query)
                
                if result.rowcount > 0:
                    # Update user quota
                    await self._update_user_quota(session, user.user_id, increment_connections=-1)
                    
                    # Log audit event
                    await self._log_audit_event(
                        session,
                        connection_id=connection_id,
                        user_id=user.user_id,
                        action="connection_deleted",
                        success=True,
                        request_context=request_context
                    )
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Failed to delete connection: {e}")
            return False
    
    async def get_user_stats(self, user: UserContext) -> Dict[str, Any]:
        """
        Get user connection statistics
        """
        try:
            async with self.get_session() as session:
                # Get connection counts by status
                status_query = select(
                    DatabaseConnection.status,
                    func.count(DatabaseConnection.id).label('count')
                ).where(
                    and_(
                        DatabaseConnection.user_id == user.user_id,
                        DatabaseConnection.is_active == True
                    )
                ).group_by(DatabaseConnection.status)
                
                status_result = await session.execute(status_query)
                status_counts = dict(status_result.fetchall())
                
                # Get total connection count
                total_query = select(func.count(DatabaseConnection.id)).where(
                    and_(
                        DatabaseConnection.user_id == user.user_id,
                        DatabaseConnection.is_active == True
                    )
                )
                total_result = await session.execute(total_query)
                total_connections = total_result.scalar()
                
                # Get user quota
                quota_query = select(UserConnectionQuota).where(
                    UserConnectionQuota.user_id == user.user_id
                )
                quota_result = await session.execute(quota_query)
                quota = quota_result.scalar_one_or_none()
                
                return {
                    'total_connections': total_connections,
                    'connected_connections': status_counts.get('connected', 0),
                    'disconnected_connections': status_counts.get('disconnected', 0),
                    'error_connections': status_counts.get('error', 0),
                    'max_connections': quota.max_connections if quota else 10,
                    'usage_percentage': (total_connections / (quota.max_connections if quota else 10)) * 100,
                    'subscription_plan': user.subscription_plan
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get user stats: {e}")
            return {}
    
    async def _check_user_quota(self, session: AsyncSession, user_id: str):
        """Check if user has available quota"""
        quota_query = select(UserConnectionQuota).where(
            UserConnectionQuota.user_id == user_id
        )
        quota_result = await session.execute(quota_query)
        quota = quota_result.scalar_one_or_none()
        
        if not quota:
            # Create default quota
            quota = UserConnectionQuota(user_id=user_id)
            session.add(quota)
            await session.flush()
        
        if quota.current_connections >= quota.max_connections:
            raise ValueError(f"Connection quota exceeded. Maximum {quota.max_connections} connections allowed.")
    
    async def _update_user_quota(self, session: AsyncSession, user_id: str, increment_connections: int = 0):
        """Update user quota usage"""
        query = update(UserConnectionQuota).where(
            UserConnectionQuota.user_id == user_id
        ).values(
            current_connections=UserConnectionQuota.current_connections + increment_connections,
            updated_at=datetime.utcnow()
        )
        
        await session.execute(query)
    
    async def _log_audit_event(
        self,
        session: Optional[AsyncSession],
        connection_id: Optional[str],
        user_id: str,
        action: str,
        success: bool,
        request_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """Log audit event"""
        try:
            if not session:
                async with self.get_session() as session:
                    await self._log_audit_event_internal(
                        session, connection_id, user_id, action, success,
                        request_context, metadata, error_message
                    )
            else:
                await self._log_audit_event_internal(
                    session, connection_id, user_id, action, success,
                    request_context, metadata, error_message
                )
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    async def _log_audit_event_internal(
        self,
        session: AsyncSession,
        connection_id: Optional[str],
        user_id: str,
        action: str,
        success: bool,
        request_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """Internal audit logging"""
        audit_log = ConnectionAuditLog(
            connection_id=connection_id,
            user_id=user_id,
            action=action,
            success=success,
            ip_address=request_context.get('ip_address') if request_context else None,
            user_agent=request_context.get('user_agent') if request_context else None,
            request_id=request_context.get('request_id') if request_context else None,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        session.add(audit_log)
    
    async def close(self):
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()


# Singleton instance
enterprise_store = EnterpriseConnectionStore()