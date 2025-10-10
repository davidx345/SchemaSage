"""
OpenAI Chat Service with Database Persistence
"""
from typing import List, Dict, Any, Optional
import logging
import time

# Try to import aiohttp, make it optional for local development
try:
    import aiohttp
    _aiohttp_available = True
except ImportError:
    aiohttp = None
    _aiohttp_available = False

from config import settings
from models.schemas import ChatResponse, ChatMessage
from core.database_service import chat_db

logger = logging.getLogger(__name__)

class ChatError(Exception):
    """Base exception for chat service errors"""
    pass

class OpenAIChatService:
    """Service for OpenAI chat completions with database persistence"""
    
    async def get_response(
        self, 
        schema: Any, 
        messages: List[ChatMessage], 
        question: str, 
        user_id: str,
        conversation_id: Optional[str] = None,
        api_key: str = None
    ) -> ChatResponse:
        """Generate a response using OpenAI's chat completion and save to database."""
        start_time = time.time()
        
        try:
            # Initialize database if not already done
            await chat_db.initialize()
            
            # Use provided API key or default from settings
            api_key = api_key or settings.OPENAI_API_KEY
            if not api_key:
                raise ChatError("OpenAI API key not configured")
            
            # Create conversation if none provided
            if not conversation_id:
                conversation_id = await chat_db.create_conversation(
                    user_id=user_id,
                    ai_provider="openai",
                    model_name=settings.OPENAI_MODEL,
                    title=f"Chat {time.strftime('%Y-%m-%d %H:%M')}"
                )
            
            # Save user message to database
            await chat_db.add_message(
                conversation_id=conversation_id,
                role="user",
                content=question
            )
            
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
                    
                    # Calculate metrics
                    response_time_ms = int((time.time() - start_time) * 1000)
                    token_usage = data.get("usage", {})
                    
                    # Save AI response to database
                    await chat_db.add_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=answer,
                        ai_provider="openai",
                        model_name=settings.OPENAI_MODEL,
                        token_usage=token_usage,
                        response_time_ms=response_time_ms
                    )
                    
                    # Update usage statistics
                    await chat_db.update_usage_statistics(
                        user_id=user_id,
                        ai_provider="openai",
                        tokens_used=token_usage.get("total_tokens", 0),
                        cost_usd=self._calculate_cost(token_usage),
                        response_time_ms=response_time_ms
                    )
                    
                    return ChatResponse(
                        response=answer,
                        ai_model_used=settings.OPENAI_MODEL,
                        conversation_id=conversation_id,
                        suggestions=[
                            "Can you explain this in more detail?",
                            "What are the best practices for this?",
                            "Can you provide an example?",
                            "How can I implement this?"
                        ]
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get OpenAI chat response: {str(e)}")
            
            # Update error statistics
            try:
                await chat_db.update_usage_statistics(
                    user_id=user_id,
                    ai_provider="openai",
                    tokens_used=0,
                    had_error=True
                )
            except:
                pass  # Don't fail the main request if stats update fails
            
            raise ChatError(f"Failed to get chat response: {str(e)}")
    
    def _calculate_cost(self, token_usage: Dict[str, int]) -> str:
        """Calculate estimated cost for OpenAI usage"""
        if not token_usage:
            return "0.00"
        
        # GPT-4 pricing (approximate, update with current rates)
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        
        # Rates per 1K tokens (as of 2024)
        prompt_rate = 0.03 / 1000  # $0.03 per 1K prompt tokens
        completion_rate = 0.06 / 1000  # $0.06 per 1K completion tokens
        
        cost = (prompt_tokens * prompt_rate) + (completion_tokens * completion_rate)
        return f"{cost:.4f}"
    
    async def get_conversation_history(self, conversation_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history from database"""
        await chat_db.initialize()
        return await chat_db.get_conversation_history(conversation_id, user_id)
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's conversations from database"""
        await chat_db.initialize()
        return await chat_db.get_user_conversations(user_id, limit)
    
    async def suggest_schema(self, data):
        # Use LLM to suggest schema
        pass
