"""
Data models for AI Chat Service
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """A single chat message"""
    role: str = Field(..., description="Role of the message sender (user, assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[str] = Field(None, description="Timestamp of the message")

class ChatRequest(BaseModel):
    """Request for chat completion"""
    model_config = {"protected_namespaces": ()}
    
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    question: str = Field(..., description="Current question from user")
    db_schema: Optional[Dict[str, Any]] = Field(None, description="Database schema context", alias="schema")
    api_key: Optional[str] = Field(None, description="Optional API key override")
    session_id: Optional[str] = Field(None, description="Browser session ID for tracking")

class ChatResponse(BaseModel):
    """Response from chat service"""
    model_config = {"protected_namespaces": ()}
    
    response: str = Field(..., description="Generated response")
    suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    ai_model_used: Optional[str] = Field(None, description="AI model used for generation", alias="model_used")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for tracking")

class ApiHealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    ai_providers: Dict[str, bool] = Field(..., description="Status of AI providers")
    
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")

class ChatErrorResponse(BaseModel):
    """Chat error response model"""
    detail: str = Field(..., description="Error details")
    error_type: str = Field("chat_error", description="Type of the error")
