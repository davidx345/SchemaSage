"""
Gemini Integration for AI Chat Service
Provides chat services using Google's Gemini API.
"""
import re
import json
import logging
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from config import settings
from models.schemas import ChatResponse, ChatMessage

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

    async def get_response(self, schema: Any, messages: List[ChatMessage], question: str, api_key: Optional[str] = None) -> ChatResponse:
        """Generate chat responses using Gemini API"""
        try:
            self.setup_gemini(api_key)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            # Convert messages to Gemini format and include schema context
            prompt = "You are a helpful database schema expert assistant.\n\n"
            
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
                
            return ChatResponse(
                response=response.text,
                model_used=settings.GEMINI_MODEL,
                suggestions=[
                    "Tell me more about this schema",
                    "How can I optimize this schema?",
                    "What indexes should I add?",
                    "Show me example queries"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error generating chat response with Gemini: {str(e)}")
            raise GeminiServiceError(f"Failed to generate chat response: {str(e)}")

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
