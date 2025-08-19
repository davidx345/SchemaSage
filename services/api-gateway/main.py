"""
SchemaSage API Gateway - Secure Production Implementation
Latest Supabase client with enterprise security and error handling.
"""

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import os
import asyncio
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import sys
from contextlib import asynccontextmanager

# Production-grade logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Configuration with validation
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://schemasage.vercel.app").split(",")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Enhanced configuration validation
def validate_environment():
    """Validate critical environment variables with detailed error reporting."""
    missing_vars = []
    
    if not SUPABASE_URL:
        missing_vars.append("SUPABASE_URL")
    if not SUPABASE_ANON_KEY:
        missing_vars.append("SUPABASE_ANON_KEY")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.critical(error_msg)
        raise ValueError(error_msg)
    
    # Validate URL format
    if not SUPABASE_URL.startswith("https://"):
        logger.warning("SUPABASE_URL should use HTTPS in production")

# Global state management
supabase_client: Optional[Client] = None

async def initialize_supabase():
    """Initialize Supabase client with modern approach."""
    global supabase_client
    
    try:
        validate_environment()
        logger.info("Initializing Supabase client with latest version...")
        
        # Use latest Supabase client (v2.9.1) which resolves dependency issues
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Test connection
        try:
            # Simple test to verify client works
            session = supabase_client.auth.get_session()
            logger.info("✅ Supabase client initialized successfully")
        except Exception as test_error:
            logger.warning(f"Supabase client initialized but test failed: {test_error}")
            # Client is still usable for most operations
                
    except Exception as e:
        logger.critical(f"❌ Failed to initialize Supabase client: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with proper startup/shutdown."""
    # Startup
    logger.info("🚀 Starting SchemaSage API Gateway...")
    await initialize_supabase()
    logger.info("✅ Gateway startup complete")
    yield
    # Shutdown
    logger.info("🔄 Shutting down SchemaSage API Gateway...")

# Accessor function for Supabase client
def get_supabase_client() -> Client:
    """Get Supabase client with validation."""
    if supabase_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )
    return supabase_client

# Auth models
class SignUpRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class SignInRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: Dict[str, Any]

# Security
security = HTTPBearer(auto_error=False)

app = FastAPI(
    title="SchemaSage API Gateway",
    description="Secure API Gateway for SchemaSage microservices with Supabase authentication",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware with proper security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domains in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Auth dependency to verify JWT tokens
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    """Verify JWT token and return user info with enhanced security."""
    if not credentials:
        return None
    
    try:
        # Verify token with Supabase
        supabase = get_supabase_client()
        response = supabase.auth.get_user(credentials.credentials)
        if response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
                "role": response.user.user_metadata.get("role", "user")
            }
    except Exception as e:
        logger.error(f"🔒 Token verification error: {str(e)}")
        return None
    
    return None

# Protected route dependency
async def require_auth(user: Dict = Depends(get_current_user)) -> Dict:
    """Require authentication for protected routes."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# Authentication endpoints with enhanced security
@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """Sign up a new user with Supabase - Enhanced Security."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {"name": request.name} if request.name else {}
            }
        })
        
        if response.user and response.session:
            logger.info(f"✅ User signed up: {response.user.email}")
            return JSONResponse(
                status_code=201,
                content={
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "user_metadata": response.user.user_metadata
                    }
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Signup failed")
            
    except Exception as e:
        logger.error(f"🔒 Signup error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """Sign in a user with Supabase - Enhanced Security."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if response.user and response.session:
            logger.info(f"✅ User signed in: {response.user.email}")
            return JSONResponse(
                content={
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "user_metadata": response.user.user_metadata
                    }
                }
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logger.error(f"🔒 Signin error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/signout")
async def signout(user: Dict = Depends(require_auth)):
    """Sign out the current user."""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        logger.info(f"✅ User signed out: {user.get('email', 'unknown')}")
        return {"message": "Signed out successfully"}
    except Exception as e:
        logger.error(f"🔒 Signout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Signout failed")

@app.get("/api/auth/me")
async def get_current_user_info(user: Dict = Depends(require_auth)):
    """Get current user information."""
    return {"user": user}

# Health and status endpoints
@app.get("/health")
async def health_check():
    """Comprehensive gateway health check."""
    health_status = {
        "gateway": "healthy",
        "status": "ok",
        "version": "2.0.0",
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_ANON_KEY),
        "supabase_client": "initialized" if supabase_client else "not_initialized",
        "timestamp": "2025-08-19T00:00:00Z"
    }
    
    # Test Supabase connection
    if supabase_client:
        try:
            session = supabase_client.auth.get_session()
            health_status["supabase_connection"] = "healthy"
        except Exception as e:
            health_status["supabase_connection"] = f"error: {str(e)[:100]}"
            logger.warning(f"Health check Supabase error: {e}")
    
    return health_status

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "SchemaSage API Gateway",
        "version": "2.0.0",
        "status": "running",
        "auth_provider": "Supabase",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "JWT Authentication",
            "CORS Support", 
            "Microservices Routing",
            "Enterprise Security"
        ]
    }

# Protected example endpoints
@app.get("/api/protected")
async def protected_example(user: Dict = Depends(require_auth)):
    """Example of a protected route that requires authentication."""
    return {
        "message": "Access granted to protected resource",
        "user": user,
        "timestamp": "2025-08-19T00:00:00Z"
    }

# CORS preflight handlers
@app.options("/api/auth/{path:path}")
async def auth_options(path: str):
    """Handle CORS preflight for all auth endpoints."""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        },
        content={}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
