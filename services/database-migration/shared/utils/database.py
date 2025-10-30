"""Database utilities."""

from typing import Optional, Dict, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, create_engine
from contextlib import asynccontextmanager


class DatabaseUtils:
    """Database utilities for services."""
    
    def __init__(self, database_url: str, echo: bool = False):
        self.database_url = database_url
        self.echo = echo
        
        # ✅ TRANSACTION POOLER CONFIGURATION
        # CRITICAL: Add prepared_statement_cache_size=0 to URL for asyncpg
        if "?" in database_url:
            database_url += "&prepared_statement_cache_size=0"
        else:
            database_url += "?prepared_statement_cache_size=0"
        
        self.engine = create_async_engine(
            database_url, 
            echo=echo,
            pool_size=3,  # Small pool for transaction pooler
            max_overflow=5,  # Limited overflow
            pool_timeout=10,  # Fail fast if pool exhausted
            pool_recycle=300,  # Recycle every 5 minutes
            pool_pre_ping=True,  # Verify connections
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
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connection."""
        await self.engine.dispose()
    
    def get_metadata(self) -> MetaData:
        """Get database metadata."""
        sync_engine = create_engine(
            self.database_url.replace('postgresql+asyncpg://', 'postgresql://'),
            echo=self.echo
        )
        metadata = MetaData()
        metadata.reflect(bind=sync_engine)
        return metadata
