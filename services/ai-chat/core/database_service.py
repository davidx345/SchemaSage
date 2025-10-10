"""
Database service for AI Chat
Handles all database operations for chat conversations and messages
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import asynccontextmanager

from models.database_models import (
    ChatConversation, 
    ChatMessage, 
    UserChatPreferences, 
    ChatUsageStatistics,
    Base
)

logger = logging.getLogger(__name__)

class ChatDatabaseService:
    """Database service for chat functionality"""
    
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
            logger.info("✅ AI Chat database service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize chat database: {e}")
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
    
    async def create_conversation(
        self, 
        user_id: str, 
        ai_provider: str, 
        model_name: str,
        title: Optional[str] = None,
        conversation_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new chat conversation"""
        try:
            async with self.get_session() as session:
                conversation = ChatConversation(
                    user_id=user_id,
                    title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    ai_provider=ai_provider,
                    model_name=model_name,
                    conversation_settings=conversation_settings or {}
                )
                
                session.add(conversation)
                await session.flush()
                
                logger.info(f"Created conversation {conversation.id} for user {user_id}")
                return str(conversation.id)
                
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        ai_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        token_usage: Optional[Dict[str, int]] = None,
        response_time_ms: Optional[int] = None,
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to a conversation"""
        try:
            async with self.get_session() as session:
                # Get current message count for ordering
                count_query = select(func.count(ChatMessage.id)).where(
                    ChatMessage.conversation_id == conversation_id
                )
                result = await session.execute(count_query)
                message_order = result.scalar() + 1
                
                # Create message
                message = ChatMessage(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    message_order=message_order,
                    ai_provider=ai_provider,
                    model_name=model_name,
                    prompt_tokens=token_usage.get('prompt_tokens', 0) if token_usage else 0,
                    completion_tokens=token_usage.get('completion_tokens', 0) if token_usage else 0,
                    total_tokens=token_usage.get('total_tokens', 0) if token_usage else 0,
                    response_time_ms=response_time_ms,
                    processing_metadata=processing_metadata or {},
                    processed_at=datetime.utcnow() if role == 'assistant' else None
                )
                
                session.add(message)
                await session.flush()
                
                # Update conversation
                await session.execute(
                    update(ChatConversation)
                    .where(ChatConversation.id == conversation_id)
                    .values(
                        message_count=ChatConversation.message_count + 1,
                        last_message_at=datetime.utcnow(),
                        total_tokens_used=ChatConversation.total_tokens_used + (token_usage.get('total_tokens', 0) if token_usage else 0)
                    )
                )
                
                logger.info(f"Added {role} message to conversation {conversation_id}")
                return str(message.id)
                
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    async def get_conversation_history(
        self, 
        conversation_id: str, 
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            async with self.get_session() as session:
                # Get conversation and verify ownership
                conv_query = select(ChatConversation).where(
                    and_(
                        ChatConversation.id == conversation_id,
                        ChatConversation.user_id == user_id
                    )
                )
                conv_result = await session.execute(conv_query)
                conversation = conv_result.scalar_one_or_none()
                
                if not conversation:
                    return []
                
                # Get messages
                messages_query = (
                    select(ChatMessage)
                    .where(ChatMessage.conversation_id == conversation_id)
                    .order_by(ChatMessage.message_order)
                    .limit(limit)
                )
                
                messages_result = await session.execute(messages_query)
                messages = messages_result.scalars().all()
                
                return [
                    {
                        "id": str(msg.id),
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "ai_provider": msg.ai_provider,
                        "model_name": msg.model_name,
                        "token_usage": {
                            "prompt_tokens": msg.prompt_tokens,
                            "completion_tokens": msg.completion_tokens,
                            "total_tokens": msg.total_tokens
                        },
                        "response_time_ms": msg.response_time_ms
                    }
                    for msg in messages
                ]
                
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's conversations"""
        try:
            async with self.get_session() as session:
                query = (
                    select(ChatConversation)
                    .where(
                        and_(
                            ChatConversation.user_id == user_id,
                            ChatConversation.status == "active"
                        )
                    )
                    .order_by(desc(ChatConversation.last_message_at))
                    .limit(limit)
                    .offset(offset)
                )
                
                result = await session.execute(query)
                conversations = result.scalars().all()
                
                return [
                    {
                        "id": str(conv.id),
                        "title": conv.title,
                        "ai_provider": conv.ai_provider,
                        "model_name": conv.model_name,
                        "message_count": conv.message_count,
                        "created_at": conv.created_at.isoformat(),
                        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                        "total_tokens_used": conv.total_tokens_used
                    }
                    for conv in conversations
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []
    
    async def update_usage_statistics(
        self,
        user_id: str,
        ai_provider: str,
        tokens_used: int,
        cost_usd: str = "0.00",
        response_time_ms: Optional[int] = None,
        had_error: bool = False
    ):
        """Update daily usage statistics"""
        try:
            async with self.get_session() as session:
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Get or create today's stats
                stats_query = select(ChatUsageStatistics).where(
                    and_(
                        ChatUsageStatistics.user_id == user_id,
                        ChatUsageStatistics.date == today
                    )
                )
                
                result = await session.execute(stats_query)
                stats = result.scalar_one_or_none()
                
                if not stats:
                    stats = ChatUsageStatistics(user_id=user_id, date=today)
                    session.add(stats)
                
                # Update stats
                stats.total_tokens_used += tokens_used
                if ai_provider == "openai":
                    stats.openai_tokens_used += tokens_used
                    stats.openai_cost_usd = str(float(stats.openai_cost_usd) + float(cost_usd))
                elif ai_provider == "gemini":
                    stats.gemini_tokens_used += tokens_used
                    stats.gemini_cost_usd = str(float(stats.gemini_cost_usd) + float(cost_usd))
                
                stats.total_cost_usd = str(float(stats.total_cost_usd) + float(cost_usd))
                stats.ai_responses_received += 1
                
                if response_time_ms:
                    # Update average response time
                    current_avg = stats.average_response_time_ms
                    current_count = stats.ai_responses_received
                    new_avg = ((current_avg * (current_count - 1)) + response_time_ms) // current_count
                    stats.average_response_time_ms = new_avg
                
                if had_error:
                    stats.error_count += 1
                
                logger.info(f"Updated usage stats for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to update usage statistics: {e}")
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user chat preferences"""
        try:
            async with self.get_session() as session:
                query = select(UserChatPreferences).where(
                    UserChatPreferences.user_id == user_id
                )
                
                result = await session.execute(query)
                prefs = result.scalar_one_or_none()
                
                if not prefs:
                    # Create default preferences
                    prefs = UserChatPreferences(user_id=user_id)
                    session.add(prefs)
                    await session.commit()
                
                return {
                    "preferred_ai_provider": prefs.preferred_ai_provider,
                    "preferred_model": prefs.preferred_model,
                    "default_temperature": prefs.default_temperature,
                    "default_max_tokens": prefs.default_max_tokens,
                    "conversation_style": prefs.conversation_style,
                    "save_conversations": prefs.save_conversations,
                    "custom_settings": prefs.custom_settings or {}
                }
                
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()

# Global database service instance
chat_db = ChatDatabaseService()