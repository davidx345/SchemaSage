from fastapi import APIRouter, HTTPException, Body, Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from ...services.gemini_service import chat_with_gemini, GeminiServiceError
from ...config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    schema_data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None

@router.options("")
async def options_chat():
    """Handle CORS preflight requests for /api/chat"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest = Body(...)):
    """
    Generate a chat response using Google's Gemini API
    """
    try:
        # Convert Pydantic models to dictionaries
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Call the Gemini service
        result = await chat_with_gemini(
            messages=messages_dict,
            schema=request.schema_data
        )
        
        return result
        
    except GeminiServiceError as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
