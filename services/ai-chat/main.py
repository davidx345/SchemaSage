"""
AI Chat Microservice with Database Persistence and Rate Limiting
Handles AI-powered chat functionality for schema assistance
"""
from fastapi import FastAPI, HTTPException, Request, status, Body, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional, List, Dict, Any
import logging
import sys
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from models.schemas import (
    ChatResponse, ChatMessage, ChatRequest, ChatErrorResponse, ApiHealthResponse
)
from core.chat_service import OpenAIChatService, ChatError
from core.database_service import chat_db
from core.auth import get_current_user, get_optional_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Service instances
openai_service = OpenAIChatService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with graceful shutdown."""
    # Startup
    logger.info("AI Chat Service starting up...")
    
    # Initialize database
    try:
        await chat_db.initialize()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
    
    # Check OpenAI configuration
    if settings.is_openai_configured():
        logger.info("OpenAI provider configured")
    else:
        logger.warning("OpenAI API key not configured")
    
    logger.info("✅ AI Chat Service ready")
    yield
    
    # Shutdown - cleanup resources
    logger.info("🛑 AI Chat Service shutting down gracefully...")
    try:
        await chat_db.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    logger.info("✅ AI Chat Service stopped")

app = FastAPI(
    title="AI Chat Service",
    description="Microservice for AI chat interactions using OpenAI API with rate limiting",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    # Test OpenAI configuration
    ai_providers = {
        "openai": settings.is_openai_configured()
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
@limiter.limit("20/minute")  # Max 20 requests per minute per IP
async def chat_endpoint(
    request: Request,  # Required for rate limiter - MUST be named 'request'
    chat_request: ChatRequest = Body(...),
    user_id: Optional[str] = Depends(get_optional_user)
):
    """Generate AI chat response using OpenAI with rate limiting"""
    try:
        logger.info(f"📨 /chat endpoint called from IP: {request.client.host if request.client else 'unknown'}")
        
        # User ID must be an integer from the users table
        if not user_id:
            # For anonymous users, require authentication or reject
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please log in to use the chat service."
            )
        
        # user_id comes from JWT - could be integer or string representation
        # Validate and convert to integer
        try:
            if isinstance(user_id, str):
                user_id_int = int(user_id)
            else:
                user_id_int = user_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format from JWT: {user_id} (type: {type(user_id)})")
            raise HTTPException(
                status_code=400,
                detail="Invalid user ID format. Please log in again."
            )
        
        # Generate session_id if not provided (use proper UUID)
        if not chat_request.session_id:
            session_id = str(uuid.uuid4())
        else:
            # Ensure session_id is a valid UUID string
            try:
                uuid.UUID(chat_request.session_id)  # Validate it's a valid UUID
                session_id = chat_request.session_id
            except ValueError:
                # If not a valid UUID, generate a new one
                session_id = str(uuid.uuid4())
        
        # Check if OpenAI is configured
        if not settings.is_openai_configured() and not chat_request.api_key:
            raise HTTPException(
                status_code=503, 
                detail="OpenAI API key not configured. Please configure OPENAI_API_KEY."
            )
        
        # Get user info from JWT token for session creation
        from core.auth import get_current_user_info, security
        try:
            # Extract Authorization header manually for user info
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                from fastapi.security import HTTPAuthorizationCredentials
                credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer", 
                    credentials=auth_header.split(" ")[1]
                )
                user_info = get_current_user_info(credentials)
                username = user_info.get("username")
            else:
                username = None
        except Exception:
            username = None
        
        # Ensure session exists in database before processing
        from core.database_service import chat_db
        logger.debug(f"Getting or creating session {session_id} for user {user_id_int}")
        await chat_db.get_or_create_session(
            session_id=session_id,
            user_id=user_id_int,  # Use the validated integer user ID
            username=username,  # Store username for convenience
            session_name=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        logger.info(f"✅ Session ready: {session_id}")
        
        # Get OpenAI response
        logger.info(f"🤖 Requesting OpenAI response for question: {chat_request.question[:50]}...")
        response = await openai_service.get_response(
            schema=chat_request.db_schema,
            messages=chat_request.messages,
            question=chat_request.question,
            user_id=user_id,
            session_id=session_id,
            api_key=chat_request.api_key
        )
        logger.info(f"✅ Chat request completed successfully for user {user_id_int}")
        return response
        
    except HTTPException:
        raise
    except ChatError as e:
        logger.error(f"OpenAI chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/chat")
async def chat_status(user_id: Optional[str] = Depends(get_optional_user)):
    """Get chat service status and user session info"""
    try:
        # Check if user is authenticated
        if not user_id:
            return {
                "status": "available",
                "service": "AI Chat Service",
                "version": settings.SERVICE_VERSION,
                "authenticated": False,
                "message": "Authentication required for chat functionality",
                "providers": {
                    "openai": settings.is_openai_configured()
                }
            }
        
        # For authenticated users, return session info
        try:
            user_id_int = int(user_id)
        except ValueError:
            user_id_int = None
        
        return {
            "status": "ready",
            "service": "AI Chat Service", 
            "version": settings.SERVICE_VERSION,
            "authenticated": True,
            "user_id": user_id,
            "providers": {
                "openai": settings.is_openai_configured()
            },
            "endpoints": {
                "chat": "POST /chat",
                "conversations": "GET /conversations",
                "test_providers": "GET /providers/test"
            }
        }
        
    except Exception as e:
        logger.error(f"Chat status error: {str(e)}")
        return {
            "status": "error",
            "service": "AI Chat Service",
            "message": str(e)
        }

@app.post("/chat/openai", response_model=ChatResponse)
async def chat_openai(
    chat_request: ChatRequest,
    user_id: Optional[str] = Depends(get_optional_user)
):
    """Generate chat response specifically using OpenAI"""
    try:
        # Require authentication
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please log in to use the chat service."
            )
        
        # Validate and convert user_id to integer
        try:
            if isinstance(user_id, str):
                user_id_int = int(user_id)
            else:
                user_id_int = user_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format from JWT: {user_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid user ID format. Please log in again."
            )
        
        # Check if OpenAI is configured
        if not settings.is_openai_configured() and not chat_request.api_key:
            raise HTTPException(
                status_code=400, 
                detail="OpenAI API key not configured"
            )
        
        # Generate session_id if not provided
        if not chat_request.session_id:
            session_id = str(uuid.uuid4())
        else:
            try:
                uuid.UUID(chat_request.session_id)
                session_id = chat_request.session_id
            except ValueError:
                session_id = str(uuid.uuid4())
        
        logger.info(f"📨 /chat/openai request from user {user_id_int}, session {session_id}")
        
        # Get OpenAI response with required parameters
        response = await openai_service.get_response(
            schema=chat_request.db_schema,
            messages=chat_request.messages,
            question=chat_request.question,
            user_id=user_id,
            session_id=session_id,
            api_key=chat_request.api_key
        )
        return response
        
    except ChatError as e:
        logger.error(f"OpenAI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected OpenAI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@app.get("/providers/test")
async def test_providers(user_id: Optional[str] = Depends(get_optional_user)):
    """Test OpenAI connection"""
    results = {}
    
    # Test OpenAI
    if settings.is_openai_configured():
        try:
            # Use a test user_id and session_id for provider testing
            test_user_id = user_id if user_id else "test_user"
            test_session_id = str(uuid.uuid4())
            
            logger.info(f"🧪 Testing OpenAI provider for user {test_user_id}")
            
            # Simple test request
            test_response = await openai_service.get_response(
                schema=None,
                messages=[],
                question="Hello, this is a test.",
                user_id=test_user_id,
                session_id=test_session_id
            )
            results["openai"] = {"status": "ok", "message": "Connection successful"}
            logger.info("✅ OpenAI provider test passed")
        except Exception as e:
            logger.error(f"❌ OpenAI provider test failed: {e}")
            results["openai"] = {"status": "error", "message": str(e)}
    else:
        results["openai"] = {"status": "not_configured", "message": "API key not set"}
    
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
            "conversations": "GET /conversations",
            "conversation_history": "GET /conversations/{conversation_id}",
            "continue_conversation": "GET /conversations/{conversation_id}/continue",
            "test_providers": "GET /providers/test",
            "health": "GET /health"
        }
    }

@app.get("/conversations")
async def get_user_conversations(
    user_id: str = Depends(get_current_user),
    limit: int = 20
):
    """Get user's conversation list"""
    try:
        conversations = await openai_service.get_user_conversations(user_id, limit)
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get conversation history"""
    try:
        history = await openai_service.get_conversation_history(conversation_id, user_id)
        return {
            "conversation_id": conversation_id,
            "messages": history
        }
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}/continue", response_model=ChatResponse)
async def continue_conversation(
    conversation_id: str,
    question: str,
    user_id: str = Depends(get_current_user),
    provider: str = "auto"
):
    """Continue an existing conversation"""
    try:
        # Get conversation history for context
        history = await openai_service.get_conversation_history(conversation_id, user_id)
        
        # Convert to ChatMessage format
        messages = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in history[-10:]  # Last 10 messages for context
        ]
        
        # Use OpenAI
        if not settings.is_openai_configured():
            raise HTTPException(status_code=503, detail="OpenAI API not configured")
        
        response = await openai_service.get_response(
            schema=None,
            messages=messages,
            question=question,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to continue conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
