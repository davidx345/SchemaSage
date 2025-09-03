"""
Schema Detection Microservice - Clean Version

Independent service for schema detection and analysis.
"""
from fastapi import FastAPI, Request, status, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from contextlib import asynccontextmanager
import os
import jwt
from datetime import datetime

from models.schemas import DetectionResponse
from routers import detection_router, lineage_router, history_router, compliance_detection_router
from config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key_not_for_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://schemasage.vercel.app").split(",")

# Security scheme
security = HTTPBearer(auto_error=False)

# Rate limiting store
request_counts = {}


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token (optional authentication)"""
    if not credentials:
        return None  # Allow unauthenticated access
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None  # Invalid token, but allow access


def rate_limit_check(request: Request):
    """Simple rate limiting check"""
    client_ip = request.client.host
    current_time = datetime.now().timestamp()
    
    # Clean old requests (older than 1 minute)
    if client_ip in request_counts:
        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip]
            if current_time - req_time < 60
        ]
    else:
        request_counts[client_ip] = []
    
    # Check rate limit (max 100 requests per minute)
    if len(request_counts[client_ip]) >= 100:
        return False
    
    # Add current request
    request_counts[client_ip].append(current_time)
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Schema Detection Service starting up...")
    logger.info(f"Version: {settings.VERSION}")
    yield
    # Shutdown
    logger.info("Schema Detection Service shutting down...")


app = FastAPI(
    title="Schema Detection Service",
    description="AI-powered schema detection and analysis microservice",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detection_router)
app.include_router(lineage_router)
app.include_router(history_router)
app.include_router(compliance_detection_router)


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
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "status": "error"
        }
    )


# Middleware for rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    if not rate_limit_check(request):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "message": "Rate limit exceeded. Please try again later.",
                "status": "error"
            }
        )
    
    response = await call_next(request)
    return response


# Health and info endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "schema-detection",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Schema Detection Service",
        "version": settings.VERSION,
        "status": "running",
        "features": [
            "AI-powered schema detection",
            "Multi-format data parsing (JSON, CSV, XML, YAML)",
            "Relationship suggestion",
            "Data lineage tracking",
            "Schema history management",
            "Data quality analysis",
            "Documentation generation"
        ],
        "endpoints": {
            "schema_detection": "POST /detect/schema",
            "file_upload": "POST /detect/file", 
            "relationships": "POST /detect/relationships",
            "cross_dataset": "POST /detect/cross-dataset",
            "table_lineage": "GET /lineage/table/{table_name}",
            "column_lineage": "GET /lineage/column/{table_name}/{column_name}",
            "impact_analysis": "POST /lineage/impact-analysis",
            "schema_history": "GET /history/{table_name}",
            "create_snapshot": "POST /history/snapshot",
            "schema_diff": "GET /history/diff/{table_name}",
            "generate_docs": "POST /documentation/generate",
            "data_cleaning": "POST /cleaning/analyze",
            "health": "GET /health"
        },
        "documentation": "/docs"
    }


@app.get("/stats")
async def get_service_stats():
    """Get service statistics"""
    return {
        "active_connections": len(request_counts),
        "total_requests_last_minute": sum(len(reqs) for reqs in request_counts.values()),
        "service_uptime": "N/A",  # Would need to track startup time
        "features_enabled": {
            "ai_enhancement": bool(getattr(settings, 'GEMINI_API_KEY', None)),
            "rate_limiting": True,
            "authentication": "optional",
            "cors": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=getattr(settings, 'HOST', '0.0.0.0'), 
        port=getattr(settings, 'PORT', 8000)
    )
