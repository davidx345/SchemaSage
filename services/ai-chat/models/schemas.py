"""
Data models for AI Chat Service with input validation
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ChatMessage(BaseModel):
    """A single chat message with validation"""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., min_length=1, max_length=32000, description="Content of the message")
    timestamp: Optional[str] = Field(None, description="Timestamp of the message")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate message role"""
        allowed_roles = {'user', 'assistant', 'system'}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return v
    
    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Basic content sanitization"""
        # Remove null bytes and excessive whitespace
        v = v.replace('\x00', '').strip()
        if not v:
            raise ValueError("Content cannot be empty after sanitization")
        return v

class ChatRequest(BaseModel):
    """Request for chat completion with comprehensive validation"""
    model_config = ConfigDict(protected_namespaces=())
    
    messages: List[ChatMessage] = Field(
        default=[],
        max_length=50,
        description="List of chat messages (max 50 for context)"
    )
    question: str = Field(
        ..., 
        min_length=1,
        max_length=4000,
        description="Current question from user"
    )
    db_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Database schema context",
        alias="schema"
    )
    api_key: Optional[str] = Field(
        None,
        min_length=20,
        max_length=200,
        description="Optional API key override"
    )
    session_id: Optional[str] = Field(
        None,
        min_length=8,
        max_length=255,
        description="Browser session ID for tracking"
    )
    
    @field_validator('question')
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        """Sanitize and validate question for prompt injection attempts"""
        v = v.strip()
        
        if not v:
            raise ValueError("Question cannot be empty")
        
        # Check for potential prompt injection patterns
        dangerous_patterns = [
            'ignore previous',
            'ignore all previous',
            'system:',
            'assistant:',
            '<|endoftext|>',
            '<|im_start|>',
            '<|im_end|>'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Question contains disallowed pattern: {pattern}")
        
        return v
    
    @field_validator('db_schema')
    @classmethod
    def validate_schema_size(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate schema is not too large"""
        if v is not None:
            # Convert to string to check size
            import json
            schema_str = json.dumps(v)
            if len(schema_str) > 100000:  # 100KB limit
                raise ValueError("Database schema too large (max 100KB)")
        return v

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
