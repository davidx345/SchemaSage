"""
AI Chat Microservice
Handles AI-powered chat functionality for schema assistance
"""
from fastapi import FastAPI, HTTPException, Request, status, Body, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional
import logging
from contextlib import asynccontextmanager

from config import settings
from models.schemas import (
    ChatResponse, ChatMessage, ChatRequest, ChatErrorResponse
)
from core.chat_service import OpenAIChatService, ChatError
from core.gemini_service import GeminiChatService, GeminiServiceError

logger = logging.getLogger(__name__)

# Service instances
openai_service = OpenAIChatService()
gemini_service = GeminiChatService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("AI Chat Service starting up...")
    # Check AI provider configurations
    providers = []
    if settings.is_openai_configured():
        providers.append("OpenAI")
    if settings.is_gemini_configured():
        providers.append("Gemini")
    
    if providers:
        logger.info(f"AI providers configured: {', '.join(providers)}")
    else:
        logger.warning("No AI providers configured")
    yield
    # Shutdown
    logger.info("AI Chat Service shutting down...")

app = FastAPI(
    title="AI Chat Service",
    description="Microservice for AI chat interactions using OpenAI and Gemini APIs",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Invalid request format",
            "details": exc.errors(),
            "status": "error",
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Error in AI Chat Service: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "details": {"error": str(exc)},
        },
    )

@app.get("/health", response_model=ApiHealthResponse)
async def health_check():
    """Health check endpoint"""
    # Test AI provider configurations
    ai_providers = {
        "openai": settings.is_openai_configured(),
        "gemini": settings.is_gemini_configured()
    }
    
    return ApiHealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        ai_providers=ai_providers
    )

@app.options("/chat")
async def options_chat():
    """Handle CORS preflight requests for /chat"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest = Body(...)):
    """Generate AI chat response using available AI providers"""
    try:
        # Try OpenAI first if configured
        if settings.is_openai_configured():
            try:
                response = await openai_service.get_response(
                    schema=request.schema,
                    messages=request.messages,
                    question=request.question,
                    api_key=request.api_key
                )
                return response
            except ChatError as e:
                logger.warning(f"OpenAI chat failed: {str(e)}")
                # Fall through to try Gemini
                
        # Try Gemini if OpenAI failed or not configured
        if settings.is_gemini_configured():
            try:
                response = await gemini_service.get_response(
                    schema=request.schema,
                    messages=request.messages,
                    question=request.question,
                    api_key=request.api_key
                )
                return response
            except GeminiServiceError as e:
                logger.error(f"Gemini chat failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")
        
        # No AI providers configured
        raise HTTPException(
            status_code=503, 
            detail="No AI providers are configured. Please configure OpenAI or Gemini API keys."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/openai", response_model=ChatResponse)
async def chat_openai(request: ChatRequest):
    """Generate chat response specifically using OpenAI"""
    try:
        if not settings.is_openai_configured() and not request.api_key:
            raise HTTPException(
                status_code=400, 
                detail="OpenAI API key not configured"
            )
            
        response = await openai_service.get_response(
            schema=request.schema,
            messages=request.messages,
            question=request.question,
            api_key=request.api_key
        )
        return response
        
    except ChatError as e:
        logger.error(f"OpenAI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected OpenAI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/gemini", response_model=ChatResponse)
async def chat_gemini(request: ChatRequest):
    """Generate chat response specifically using Gemini"""
    try:
        if not settings.is_gemini_configured() and not request.api_key:
            raise HTTPException(
                status_code=400, 
                detail="Gemini API key not configured"
            )
            
        response = await gemini_service.get_response(
            schema=request.schema,
            messages=request.messages,
            question=request.question,
            api_key=request.api_key
        )
        return response
        
    except GeminiServiceError as e:
        logger.error(f"Gemini chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Gemini chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/providers/test")
async def test_providers():
    """Test AI provider connections"""
    results = {}
    
    # Test OpenAI
    if settings.is_openai_configured():
        try:
            # Simple test request
            test_response = await openai_service.get_response(
                schema=None,
                messages=[],
                question="Hello, this is a test."
            )
            results["openai"] = {"status": "ok", "message": "Connection successful"}
        except Exception as e:
            results["openai"] = {"status": "error", "message": str(e)}
    else:
        results["openai"] = {"status": "not_configured", "message": "API key not set"}
    
    # Test Gemini
    if settings.is_gemini_configured():
        try:
            success, message = await gemini_service.verify_connection()
            results["gemini"] = {
                "status": "ok" if success else "error", 
                "message": message
            }
        except Exception as e:
            results["gemini"] = {"status": "error", "message": str(e)}
    else:
        results["gemini"] = {"status": "not_configured", "message": "API key not set"}
    
    return results

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Chat Service",
        "status": "running",
        "version": settings.SERVICE_VERSION,
        "endpoints": {
            "chat": "POST /chat",
            "chat_openai": "POST /chat/openai", 
            "chat_gemini": "POST /chat/gemini",
            "test_providers": "GET /providers/test",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
