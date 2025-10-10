"""
Gemini Integration for AI Chat Service with Database Persistence
Provides chat services using Google's Gemini API.
"""
import re
import json
import logging
import time
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from config import settings
from models.schemas import ChatResponse, ChatMessage
from core.database_service import chat_db

logger = logging.getLogger(__name__)

class GeminiServiceError(Exception):
    """Base exception for Gemini service errors"""
    pass

class GeminiChatService:
    """Service for Gemini chat completions"""
    
    def __init__(self):
        self._initialized = False
        
    def setup_gemini(self, api_key: Optional[str] = None):
        """Set up Gemini API with API key from settings or provided key"""
        if self._initialized:
            return
            
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            logger.error("Gemini API key is not configured")
            raise GeminiServiceError("Gemini API key is not configured")
        try:
            genai.configure(api_key=key)
            logger.info(f"Gemini API initialized with model: {settings.GEMINI_MODEL}")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            raise GeminiServiceError(f"Failed to initialize Gemini API: {str(e)}")

    async def get_response(
        self, 
        schema: Any, 
        messages: List[ChatMessage], 
        question: str, 
        user_id: str,
        conversation_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> ChatResponse:
        """Generate chat responses using Gemini API and save to database"""
        start_time = time.time()
        
        try:
            # Initialize database if not already done
            await chat_db.initialize()
            
            self.setup_gemini(api_key)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            # Create conversation if none provided
            if not conversation_id:
                conversation_id = await chat_db.create_conversation(
                    user_id=user_id,
                    ai_provider="gemini",
                    model_name=settings.GEMINI_MODEL,
                    title=f"Chat {time.strftime('%Y-%m-%d %H:%M')}"
                )
            
            # Save user message to database
            await chat_db.add_message(
                conversation_id=conversation_id,
                role="user",
                content=question
            )
            
            # Convert messages to Gemini format and include schema context
            prompt = "You are a helpful AI assistant. Provide clear, conversational responses in plain text. Avoid using bullet points (•), asterisks (*), or excessive formatting unless specifically requested. Be natural, friendly, and helpful with any topic.\n\n"
            
            # Add schema context if provided
            if schema:
                prompt += f"Database schema information: {json.dumps(schema)}\n\n"
            
            # Add conversation history
            for msg in messages:
                role = "user" if msg.role == "user" else "assistant"
                prompt += f"{role.capitalize()}: {msg.content}\n"
                
            # Add current question
            prompt += f"User: {question}\n\nAssistant:"
                
            # Generate response
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini API")
                raise GeminiServiceError("Empty response from Gemini API")
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Save AI response to database
            await chat_db.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response.text,
                ai_provider="gemini",
                model_name=settings.GEMINI_MODEL,
                response_time_ms=response_time_ms
            )
            
            # Update usage statistics (Gemini doesn't provide token counts easily)
            estimated_tokens = len(response.text.split()) * 1.3  # Rough estimate
            await chat_db.update_usage_statistics(
                user_id=user_id,
                ai_provider="gemini",
                tokens_used=int(estimated_tokens),
                cost_usd="0.00",  # Gemini pricing varies
                response_time_ms=response_time_ms
            )
                
            return ChatResponse(
                response=response.text,
                ai_model_used=settings.GEMINI_MODEL,
                conversation_id=conversation_id,
                suggestions=[
                    "Can you explain this in more detail?",
                    "What are the best practices for this?",
                    "Can you provide an example?",
                    "How can I implement this?"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error generating chat response with Gemini: {str(e)}")
            
            # Update error statistics
            try:
                await chat_db.update_usage_statistics(
                    user_id=user_id,
                    ai_provider="gemini",
                    tokens_used=0,
                    had_error=True
                )
            except:
                pass  # Don't fail the main request if stats update fails
            
            raise GeminiServiceError(f"Failed to generate chat response: {str(e)}")
    
    async def get_conversation_history(self, conversation_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history from database"""
        await chat_db.initialize()
        return await chat_db.get_conversation_history(conversation_id, user_id)
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's conversations from database"""
        await chat_db.initialize()
        return await chat_db.get_user_conversations(user_id, limit)

    async def verify_connection(self, api_key: Optional[str] = None) -> tuple[bool, str]:
        """Verify connection to Gemini API"""
        try:
            self.setup_gemini(api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Hello, world!")
            if response and response.text:
                return True, "API key is valid and working"
            return False, "API returned empty response"
        except Exception as e:
            return False, str(e)
