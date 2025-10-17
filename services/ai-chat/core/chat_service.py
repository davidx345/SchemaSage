"""
OpenAI Chat Service with Database Persistence and Retry Logic
"""
from typing import List, Dict, Any, Optional
import logging
import time
import asyncio

# Try to import aiohttp, make it optional for local development
try:
    import aiohttp
    _aiohttp_available = True
except ImportError:
    aiohttp = None
    _aiohttp_available = False

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from config import settings
from models.schemas import ChatResponse, ChatMessage
from core.database_service import chat_db

logger = logging.getLogger(__name__)

class ChatError(Exception):
    """Base exception for chat service errors"""
    pass

class TransientAPIError(Exception):
    """Transient API error that should be retried"""
    pass

class OpenAIChatService:
    """Service for OpenAI chat completions with database persistence"""
    
    async def get_response(
        self, 
        schema: Any, 
        messages: List[ChatMessage], 
        question: str, 
        user_id: str,
        session_id: str,
        conversation_id: Optional[str] = None,
        api_key: str = None
    ) -> ChatResponse:
        """Generate a response using OpenAI's chat completion and save to database."""
        start_time = time.time()
        
        try:
            # Initialize database if not already done
            logger.debug("Initializing database connection")
            await chat_db.initialize()
            
            # Use provided API key or default from settings
            api_key = api_key or settings.OPENAI_API_KEY
            if not api_key:
                raise ChatError("OpenAI API key not configured")
            
            # Create conversation if none provided - do this before saving user message
            if not conversation_id:
                logger.debug(f"Creating new conversation for user {user_id}")
                conversation_id = await chat_db.create_conversation(
                    user_id=user_id,
                    ai_provider="openai",
                    model_name=settings.OPENAI_MODEL,
                    session_id=session_id,
                    title=f"Chat {time.strftime('%Y-%m-%d %H:%M')}"
                )
                logger.info(f"✅ Created conversation {conversation_id}")
            
            # Save user message to database BEFORE calling OpenAI
            # This ensures we capture the user's question even if OpenAI fails
            logger.debug(f"Saving user message to conversation {conversation_id}")
            user_message_start = time.time()
            await chat_db.add_message(
                conversation_id=conversation_id,
                role="user",
                content=question,
                session_id=session_id
            )
            logger.debug(f"✅ User message saved in {int((time.time() - user_message_start) * 1000)}ms")
            
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
            
            # Call OpenAI API with retry logic
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
            
            # Log before OpenAI call
            logger.info(f"🚀 Calling OpenAI API - Model: {settings.OPENAI_MODEL}, Messages: {len(openai_messages)}, User: {user_id}")
            logger.debug(f"OpenAI Request Payload: {payload}")
            
            # Use retry wrapper for transient errors
            data = await self._call_openai_with_retry(payload, headers)
            
            logger.info(f"✅ OpenAI API responded successfully - Tokens: {data.get('usage', {}).get('total_tokens', 0)}")
            
            answer = data["choices"][0]["message"]["content"]
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            token_usage = data.get("usage", {})
            
            # Save AI response to database
            logger.debug(f"Saving AI response to conversation {conversation_id}")
            db_save_start = time.time()
            await chat_db.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
                session_id=session_id,
                ai_provider="openai",
                model_name=settings.OPENAI_MODEL,
                token_usage=token_usage,
                response_time_ms=response_time_ms
            )
            logger.debug(f"✅ AI response saved in {int((time.time() - db_save_start) * 1000)}ms")
            
            # Update usage statistics - Fire and forget (don't block response)
            # This runs in background and doesn't delay the user's response
            logger.debug(f"Scheduling usage statistics update for user {user_id}")
            asyncio.create_task(
                self._update_stats_background(
                    user_id=user_id,
                    ai_provider="openai",
                    tokens_used=token_usage.get("total_tokens", 0),
                    cost_usd=self._calculate_cost(token_usage),
                    response_time_ms=response_time_ms
                )
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
            logger.error(f"❌ Failed to get OpenAI chat response: {str(e)}", exc_info=True)
            
            # Update error statistics - Fire and forget (don't block error response)
            asyncio.create_task(
                self._update_error_stats_background(user_id=user_id, ai_provider="openai")
            )
            
            raise ChatError(f"Failed to get chat response: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TransientAPIError),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _call_openai_with_retry(self, payload: Dict, headers: Dict) -> Dict:
        """
        Call OpenAI API with automatic retry on transient errors.
        
        Retries on:
        - 429 (Rate Limit)
        - 500, 502, 503 (Server Errors)
        - Network timeouts
        
        Args:
            payload: Request payload
            headers: Request headers
            
        Returns:
            API response data
            
        Raises:
            TransientAPIError: For retryable errors
            ChatError: For permanent errors
        """
        timeout = aiohttp.ClientTimeout(
            total=60,       # Total timeout for request
            connect=10,     # Connection timeout
            sock_read=30    # Socket read timeout
        )
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                logger.debug(f"Sending POST to {settings.OPENAI_API_BASE}/chat/completions")
                async with session.post(
                    f"{settings.OPENAI_API_BASE}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    # Retry on transient errors
                    if response.status in [429, 500, 502, 503]:
                        error_msg = f"Transient API error: HTTP {response.status}"
                        logger.warning(error_msg)
                        raise TransientAPIError(error_msg)
                    
                    # Permanent errors - don't retry
                    if response.status != 200:
                        error_text = await response.text()
                        # Log safely without exposing sensitive data
                        logger.error(
                            f"OpenAI API error: status={response.status}, error={error_text[:200]}"
                        )
                        raise ChatError(f"API error: status {response.status}")
                    
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                # Network errors are transient
                logger.warning(f"Network error calling OpenAI: {e}")
                raise TransientAPIError(f"Network error: {str(e)}")
            except asyncio.TimeoutError as e:
                # Timeout errors - log specifically
                logger.error(f"⏱️ TIMEOUT calling OpenAI API after {timeout.total}s: {e}")
                raise TransientAPIError(f"OpenAI API timeout after {timeout.total}s")
    
    async def _update_stats_background(
        self,
        user_id: str,
        ai_provider: str,
        tokens_used: int,
        cost_usd: str,
        response_time_ms: int
    ):
        """Update usage statistics in background without blocking the main response"""
        try:
            await chat_db.update_usage_statistics(
                user_id=user_id,
                ai_provider=ai_provider,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                response_time_ms=response_time_ms
            )
            logger.debug(f"✅ Usage statistics updated in background for user {user_id}")
        except Exception as e:
            # Log but don't fail - this is non-critical
            logger.warning(f"Background stats update failed for user {user_id}: {e}")
    
    async def _update_error_stats_background(self, user_id: str, ai_provider: str):
        """Update error statistics in background without blocking the error response"""
        try:
            await chat_db.update_usage_statistics(
                user_id=user_id,
                ai_provider=ai_provider,
                tokens_used=0,
                had_error=True
            )
            logger.debug(f"✅ Error statistics updated in background for user {user_id}")
        except Exception as e:
            # Log but don't fail - this is non-critical
            logger.warning(f"Background error stats update failed for user {user_id}: {e}")
    
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
