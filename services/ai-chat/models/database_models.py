"""
SQLAlchemy models for AI Chat service
Stores chat conversations, messages, and user interactions
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class ChatConversation(Base):
    """
    Chat conversations table
    Stores individual chat sessions between users and AI
    """
    __tablename__ = "chat_conversations"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # From JWT token
    
    # Conversation metadata
    title = Column(String(500), nullable=True)  # Auto-generated or user-set title
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Browser session UUID (consistent with ChatMessage)
    
    # AI service details
    ai_provider = Column(String(50), nullable=False, index=True)  # openai, gemini
    model_name = Column(String(100), nullable=False)  # gpt-4, gemini-pro, etc.
    model_version = Column(String(50), nullable=True)
    
    # Conversation settings
    conversation_settings = Column(JSONB, nullable=True)  # Temperature, max_tokens, etc.
    system_prompt = Column(Text, nullable=True)  # Custom system prompt if used
    
    # Status and lifecycle
    status = Column(String(50), default="active", index=True)  # active, archived, deleted
    is_public = Column(Boolean, default=False)  # For sharing conversations
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Statistics
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost_usd = Column(String(20), default="0.00")  # Store as string for precision
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatConversation(id='{self.id}', user_id='{self.user_id}', title='{self.title}')>"


class ChatMessage(Base):
    """
    Individual messages within a conversation
    Stores both user messages and AI responses
    """
    __tablename__ = "chat_messages"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('chat_conversations.id'), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False, index=True)  # Session UUID
    
    # Message details
    role = Column(String(20), nullable=False, index=True)  # user, assistant, system
    message_type = Column(String(50), nullable=False, default="user", index=True)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Message metadata
    message_order = Column(Integer, nullable=False)  # Order within conversation
    parent_message_id = Column(UUID(as_uuid=True), nullable=True)  # For message threading
    
    # AI response metadata (for assistant messages)
    ai_provider = Column(String(50), nullable=True)  # openai, gemini
    model_name = Column(String(100), nullable=True)  # gpt-4, gemini-pro, etc.
    finish_reason = Column(String(50), nullable=True)  # stop, length, content_filter, etc.
    
    # Token usage (for cost tracking)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(String(20), default="0.00")
    
    # Response quality and feedback
    response_time_ms = Column(Integer, nullable=True)  # AI response time
    user_rating = Column(Integer, nullable=True)  # 1-5 star rating from user
    user_feedback = Column(Text, nullable=True)  # User feedback on response
    
    # Processing details
    processing_metadata = Column(JSONB, nullable=True)  # Additional processing info
    error_details = Column(JSONB, nullable=True)  # Error info if request failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)  # When AI response was received
    
    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', role='{self.role}', conversation_id='{self.conversation_id}')>"


class UserChatPreferences(Base):
    """
    User preferences for chat interface and AI behavior
    """
    __tablename__ = "user_chat_preferences"
    
    # Primary key
    user_id = Column(String(255), primary_key=True)
    
    # AI preferences
    preferred_ai_provider = Column(String(50), default="openai")  # openai, gemini
    preferred_model = Column(String(100), nullable=True)  # gpt-4, gemini-pro, etc.
    default_temperature = Column(String(10), default="0.7")  # Store as string for precision
    default_max_tokens = Column(Integer, default=1000)
    
    # Interface preferences
    conversation_style = Column(String(50), default="helpful")  # helpful, concise, creative, etc.
    enable_message_sounds = Column(Boolean, default=True)
    enable_typing_indicator = Column(Boolean, default=True)
    theme_preference = Column(String(50), default="auto")  # light, dark, auto
    
    # Privacy and data preferences
    save_conversations = Column(Boolean, default=True)
    allow_conversation_analysis = Column(Boolean, default=True)
    auto_delete_after_days = Column(Integer, nullable=True)  # Auto-delete conversations after N days
    
    # Usage limits and quotas
    daily_message_limit = Column(Integer, default=100)
    monthly_token_limit = Column(Integer, default=50000)
    
    # Stored preferences as JSONB
    custom_settings = Column(JSONB, nullable=True)  # Additional user-defined settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserChatPreferences(user_id='{self.user_id}', provider='{self.preferred_ai_provider}')>"


class ChatUsageStatistics(Base):
    """
    Track usage statistics for billing and analytics
    """
    __tablename__ = "chat_usage_statistics"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    
    # Usage counters
    messages_sent = Column(Integer, default=0)
    ai_responses_received = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    
    # Token usage by provider
    openai_tokens_used = Column(Integer, default=0)
    gemini_tokens_used = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    
    # Cost tracking
    openai_cost_usd = Column(String(20), default="0.00")
    gemini_cost_usd = Column(String(20), default="0.00")
    total_cost_usd = Column(String(20), default="0.00")
    
    # Performance metrics
    average_response_time_ms = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Usage details as JSONB
    usage_details = Column(JSONB, nullable=True)  # Detailed breakdown
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Unique constraint on user_id + date
    __table_args__ = (
        {'schema': None}  # Use default schema
    )
    
    def __repr__(self):
        return f"<ChatUsageStatistics(user_id='{self.user_id}', date='{self.date}')>"


class ChatSession(Base):
    """
    Chat sessions table
    Tracks user browser/app sessions for chat continuity
    """
    __tablename__ = "chat_sessions"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # From JWT token or anonymous
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Associated project if any
    
    # Session metadata
    session_name = Column(String(255), nullable=True)  # User-friendly session name
    session_context = Column(JSONB, nullable=True)  # Session-specific context/settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    def __repr__(self):
        return f"<ChatSession(id='{self.id}', user_id='{self.user_id}')>"