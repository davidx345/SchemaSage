from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from .api.routes import schema, chat, database  # Added database import
from .config import get_settings
from contextlib import asynccontextmanager
import aiohttp
import logging
import asyncio
from .services.gemini_service import verify_gemini_connection

settings = get_settings()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Removed OpenAI check
    yield
    # Shutdown
    print("Shutting down application...")

app = FastAPI(lifespan=lifespan)

# CORS middleware must be added before including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add trusted host middleware
if settings.ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.ALLOWED_HOSTS,
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
            "status": "error"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with better logging"""
    import traceback
    logger.error(f"Error: {str(exc)}\n{''.join(traceback.format_tb(exc.__traceback__))}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "details": {
                "error": str(exc),
                "path": request.url.path
            }
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "api": "healthy",
            "gemini": "configured" if settings.USE_GEMINI and settings.GEMINI_API_KEY else "not_configured"
        },
        "version": "1.0.0",
        "environment": settings.ENV
    }

# Include routers
app.include_router(schema.router, prefix="/api/schema", tags=["schema"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(database.router, prefix="/api/database", tags=["database"])  # Added database router

@app.get("/", tags=["health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SchemaSage API",
        "version": "1.0.0",
        "environment": settings.ENV,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.on_event("startup")
async def startup_event():
    """Verify Gemini API connection on startup"""
    try:
        if settings.USE_GEMINI and settings.GEMINI_API_KEY:
            is_valid, message = await verify_gemini_connection()
            if is_valid:
                logger.info(f"Gemini API connection verified: {message}")
            else:
                logger.warning(f"Gemini API connection failed: {message}")
        else:
            logger.warning("Gemini API is not configured or disabled")
    except Exception as e:
        logger.error(f"Failed to verify Gemini connection: {str(e)}")