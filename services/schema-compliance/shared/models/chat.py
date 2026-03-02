"""Chat and AI interaction models."""

from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID
from .base import BaseModel


class AIProvider(str, Enum):
    """AI providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class MessageType(str, Enum):
    """Chat message types."""
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSessionModel(BaseModel):
    """Chat session model."""
    
    user_id: UUID  # References auth.users(id)
    project_id: Optional[UUID] = None  # Optional project association
    session_name: Optional[str] = None
    session_context: Dict[str, Any] = {}
    
    # Session configuration
    ai_provider: AIProvider = AIProvider.OPENAI
    model_version: Optional[str] = None
    
    # Timestamps
    last_message_at: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "session_name": "Schema Analysis Chat",
                "ai_provider": "openai",
                "model_version": "gpt-4",
                "session_context": {
                    "project_name": "Customer Database Migration",
                    "current_task": "schema_optimization"
                }
            }
        }


class ChatMessageModel(BaseModel):
    """Chat message model."""
    
    session_id: UUID  # References chat_sessions(id)
    message_type: MessageType
    content: str
    
    # Enhanced metadata
    metadata: Dict[str, Any] = {}
    token_count: Optional[int] = None
    processing_time_ms: Optional[int] = None
    
    # Timestamps
    timestamp: Optional[str] = None
    
    # Search capabilities
    search_vector: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "message_type": "user",
                "content": "Can you help me optimize this database schema?",
                "metadata": {
                    "client_info": "web_app_v2.1",
                    "context": "schema_analysis"
                },
                "token_count": 12
            }
        }


class ChatSessionCreateRequest(BaseModel):
    """Request to create a chat session."""
    
    project_id: Optional[UUID] = None
    session_name: Optional[str] = None
    ai_provider: AIProvider = AIProvider.OPENAI
    model_version: Optional[str] = None
    initial_context: Dict[str, Any] = {}


class ChatMessageCreateRequest(BaseModel):
    """Request to create a chat message."""
    
    session_id: UUID
    content: str
    message_type: MessageType = MessageType.USER
    metadata: Dict[str, Any] = {}


class ChatSessionResponse(BaseModel):
    """Chat session response."""
    
    session: ChatSessionModel
    message_count: int = 0
    recent_messages: List[ChatMessageModel] = []


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    
    message: ChatMessageModel
    session_info: Optional[Dict[str, Any]] = None
