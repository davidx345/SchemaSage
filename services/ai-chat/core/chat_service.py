"""
OpenAI Chat Service
"""
from typing import List, Dict, Any
import logging

# Try to import aiohttp, make it optional for local development
try:
    import aiohttp
    _aiohttp_available = True
except ImportError:
    aiohttp = None
    _aiohttp_available = False

from config import settings
from models.schemas import ChatResponse, ChatMessage

logger = logging.getLogger(__name__)

class ChatError(Exception):
    """Base exception for chat service errors"""
    pass

class OpenAIChatService:
    """Service for OpenAI chat completions"""
    
    async def get_response(self, schema: Any, messages: List[ChatMessage], question: str, api_key: str = None) -> ChatResponse:
        """Generate a response using OpenAI's chat completion."""
        try:
            # Use provided API key or default from settings
            api_key = api_key or settings.OPENAI_API_KEY
            if not api_key:
                raise ChatError("OpenAI API key not configured")
            
            # Format messages for OpenAI
            openai_messages = [
                {"role": "system", "content": "You are a helpful AI assistant. You can help with database schemas, SQL, software development, and any other topics. Provide clear, conversational responses in plain text. Avoid using bullet points (•), asterisks (*), or excessive formatting unless specifically requested. Be natural, friendly, and helpful."},
            ]
            
            # Add schema context if provided
            if schema:
                schema_context = f"Database schema context: {schema}"
                openai_messages.append({"role": "system", "content": schema_context})
            
            # Add conversation history
            for msg in messages:
                openai_messages.append({"role": msg.role, "content": msg.content})
                
            # Add current question
            openai_messages.append({"role": "user", "content": question})
            
            # Call OpenAI API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": settings.OPENAI_MODEL,
                "messages": openai_messages,
                "temperature": settings.TEMPERATURE,
                "max_tokens": settings.MAX_TOKENS
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OPENAI_API_BASE}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {error_text}")
                        raise ChatError(f"OpenAI API error: {error_text}")
                    
                    data = await response.json()
                    answer = data["choices"][0]["message"]["content"]
                    
                    return ChatResponse(
                        response=answer,
                        ai_model_used=settings.OPENAI_MODEL,
                        suggestions=[
                            "Can you explain this in more detail?",
                            "What are the best practices for this?",
                            "Can you provide an example?",
                            "How can I implement this?"
                        ]
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get OpenAI chat response: {str(e)}")
            raise ChatError(f"Failed to get chat response: {str(e)}")
    
    async def suggest_schema(self, data):
        # Use LLM to suggest schema
        pass
