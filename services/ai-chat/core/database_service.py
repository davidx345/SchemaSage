"""
Database service for AI Chat
Handles all database operations for chat conversations and messages
"""
import os
import logging
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, func, desc, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import asynccontextmanager

from models.database_models import (
    ChatConversation, 
    ChatMessage, 
    ChatSession,
    UserChatPreferences, 
    ChatUsageStatistics,
    Base
)

logger = logging.getLogger(__name__)

# UUID Validation Helper
def validate_and_convert_uuid(value: Union[str, uuid.UUID, None], field_name: str) -> Optional[uuid.UUID]:
    """
    Safely convert string to UUID with validation.
    
    Args:
        value: String, UUID object, or None
        field_name: Name of the field for error messages
        
    Returns:
        UUID object or None
        
    Raises:
        ValueError: If the value is not a valid UUID format
    """
    if value is None:
        return None
    
    if isinstance(value, uuid.UUID):
        return value
    
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid UUID format for {field_name}: {value}") from e
    
    raise TypeError(f"{field_name} must be string or UUID, got {type(value)}")

class ChatDatabaseService:
    """Database service for chat functionality with thread-safe initialization"""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialized = False
        self._init_lock = asyncio.Lock()  # Prevent concurrent initialization
        
    async def initialize(self):
        """Initialize database connection with thread-safe double-check locking"""
        if self._initialized:
            return

        async with self._init_lock:
            # Double-check after acquiring lock
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
                # Optimized for PgBouncer transaction mode
                self._engine = create_async_engine(
                    database_url,
                    pool_size=3,           # Small pool for transaction pooler
                    max_overflow=5,        # Limited overflow
                    pool_timeout=10,       # Fail fast if pool exhausted
                    pool_recycle=300,      # Recycle every 5 minutes
                    pool_pre_ping=True,    # Verify connections
                    echo=os.getenv("DEBUG_SQL", "false").lower() == "true",
                    connect_args={
                        "statement_cache_size": 0,  # CRITICAL: No prepared statements
                        "command_timeout": 10,  # Fast timeout
                        "server_settings": {
                            "application_name": "ai-chat-service",
                            "jit": "off",  # Disable JIT
                            "statement_timeout": "30000"  # 30s timeout
                        }
                    },
                    pool_reset_on_return="commit"  # Reset on return
                )

                # Create session factory
                self._session_factory = sessionmaker(
                    self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )

                # Skip table creation - tables should already exist and be managed externally
                # Tables are managed via SQL migrations, not SQLAlchemy auto-creation
                logger.info("✅ Database connection established (tables managed externally)")
                logger.info("✅ PgBouncer transaction pooler config: statement_cache_size=0")

                self._initialized = True
                logger.info("✅ AI Chat database service initialized")

            except Exception as e:
                logger.error(f"❌ Failed to initialize chat database: {e}")
                raise
    
    async def close(self):
        """Close database connections gracefully"""
        if self._engine:
            await self._engine.dispose()
            logger.info("✅ Database connections closed")
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic rollback on error
        
        Note: Session cleanup is handled by the context manager,
        no need to manually close the session
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            # Session is automatically closed by the context manager
    
    async def get_or_create_session(
        self,
        session_id: str,
        user_id: Union[str, int],
        project_id: Optional[str] = None,
        session_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> str:
        """
        Get existing session or create new one if it doesn't exist
        
        Args:
            session_id: UUID string for the session
            user_id: User identifier (integer ID from users table)
            project_id: Optional project association
            session_name: Optional user-friendly session name
            
        Returns:
            str: The session ID (UUID as string)
        """
        try:
            async with self.get_session() as session:
                # Validate and convert session_id UUID
                session_id_uuid = validate_and_convert_uuid(session_id, "session_id")
                
                # Convert user_id to integer
                try:
                    user_id_int = int(user_id)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid user_id: {user_id}. Must be an integer.")
                
                # Check if session already exists
                existing_session_query = select(ChatSession).where(ChatSession.id == session_id_uuid)
                result = await session.execute(existing_session_query)
                existing_session = result.scalar_one_or_none()
                
                if existing_session:
                    logger.debug(f"Found existing session: {session_id}")
                    return str(existing_session.id)
                
                # Create new session
                project_id_uuid = None
                if project_id:
                    project_id_uuid = validate_and_convert_uuid(project_id, "project_id")
                
                new_session = ChatSession(
                    id=session_id_uuid,
                    user_id=user_id_int,
                    username=username,  # Store username for convenience (no FK needed)
                    project_id=project_id_uuid,
                    session_name=session_name,
                    session_context={},
                    last_message_at=datetime.utcnow()  # Ensure NOT NULL
                )
                
                session.add(new_session)
                await session.flush()
                
                logger.info(f"✅ Created new chat session: {session_id} for user: {user_id}")
                return str(new_session.id)
                
        except Exception as e:
            logger.error(f"Failed to get/create session {session_id}: {e}")
            raise
    
    async def update_session_activity(self, session_id: str) -> None:
        """Update the last_message_at timestamp for a session"""
        try:
            async with self.get_session() as session:
                session_id_uuid = validate_and_convert_uuid(session_id, "session_id")
                
                await session.execute(
                    update(ChatSession)
                    .where(ChatSession.id == session_id_uuid)
                    .values(last_message_at=datetime.utcnow())
                )
                
        except Exception as e:
            logger.warning(f"Failed to update session activity for {session_id}: {e}")
            # Don't raise - this is not critical for chat functionality
    
    async def create_conversation(
        self, 
        user_id: str, 
        ai_provider: str, 
        model_name: str,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        conversation_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new chat conversation with proper UUID handling"""
        try:
            async with self.get_session() as session:
                # Convert session_id to UUID if provided as string, otherwise generate new UUID
                if session_id:
                    session_uuid = validate_and_convert_uuid(session_id, "session_id")
                else:
                    session_uuid = uuid.uuid4()
                
                conversation = ChatConversation(
                    user_id=user_id,
                    title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    session_id=session_uuid,
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
        session_id: str,
        ai_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        token_usage: Optional[Dict[str, int]] = None,
        response_time_ms: Optional[int] = None,
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to a conversation with proper ordering via database-level sequence"""
        try:
            async with self.get_session() as session:
                # Validate and convert UUIDs with proper error messages
                conv_id_uuid = validate_and_convert_uuid(conversation_id, "conversation_id")
                session_id_uuid = validate_and_convert_uuid(session_id, "session_id")
                
                # OPTIMIZED: Use single query to get order and insert message
                # This reduces round trips to the database
                order_query = text("""
                    SELECT COALESCE(MAX(message_order), 0) + 1 
                    FROM chat_messages 
                    WHERE conversation_id = :conv_id
                """)
                result = await session.execute(order_query, {"conv_id": conv_id_uuid})
                message_order = result.scalar()
                
                # Create message
                message = ChatMessage(
                    conversation_id=conv_id_uuid,
                    session_id=session_id_uuid,
                    role=role,
                    message_type=role,  # Set message_type to match role (user/assistant/system)
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
                # Don't flush here - let commit handle it
                
                # Update conversation - combine with message insert in same transaction
                await session.execute(
                    update(ChatConversation)
                    .where(ChatConversation.id == conv_id_uuid)
                    .values(
                        message_count=ChatConversation.message_count + 1,
                        last_message_at=datetime.utcnow(),
                        total_tokens_used=ChatConversation.total_tokens_used + (token_usage.get('total_tokens', 0) if token_usage else 0)
                    )
                )
                
                # Commit will happen automatically via context manager
                # This commits both the message insert and conversation update in one transaction
                
                logger.debug(f"Added {role} message to conversation {conversation_id}")
                return str(message.id) if hasattr(message, 'id') and message.id else str(uuid.uuid4())
                
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    async def get_conversation_history(
        self, 
        conversation_id: str, 
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history with validated UUID"""
        try:
            async with self.get_session() as session:
                # Validate and convert conversation_id to UUID
                conv_id_uuid = validate_and_convert_uuid(conversation_id, "conversation_id")
                
                # Get conversation and verify ownership
                conv_query = select(ChatConversation).where(
                    and_(
                        ChatConversation.id == conv_id_uuid,
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
                    .where(ChatMessage.conversation_id == conv_id_uuid)
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
                
                # Update stats (ensure no None values)
                stats.total_tokens_used = (stats.total_tokens_used or 0) + tokens_used
                if ai_provider == "openai":
                    stats.openai_tokens_used = (stats.openai_tokens_used or 0) + tokens_used
                    current_openai_cost = float(stats.openai_cost_usd or 0)
                    stats.openai_cost_usd = str(current_openai_cost + float(cost_usd))
                elif ai_provider == "gemini":
                    stats.gemini_tokens_used = (stats.gemini_tokens_used or 0) + tokens_used
                    current_gemini_cost = float(stats.gemini_cost_usd or 0)
                    stats.gemini_cost_usd = str(current_gemini_cost + float(cost_usd))
                
                current_total_cost = float(stats.total_cost_usd or 0)
                stats.total_cost_usd = str(current_total_cost + float(cost_usd))
                stats.ai_responses_received = (stats.ai_responses_received or 0) + 1
                
                if response_time_ms:
                    # Update average response time
                    current_avg = stats.average_response_time_ms or 0
                    current_count = stats.ai_responses_received
                    new_avg = ((current_avg * (current_count - 1)) + response_time_ms) // current_count
                    stats.average_response_time_ms = new_avg
                
                if had_error:
                    stats.error_count = (stats.error_count or 0) + 1
                
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