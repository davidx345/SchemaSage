"""
SchemaSage API Gateway - Production-Grade Microservices Gateway
Enterprise-level authentication, routing, and error handling.
"""

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import os
import httpx
import asyncio
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
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
    """Initialize Supabase client with comprehensive error handling."""
    global supabase_client
    
    try:
        validate_environment()
        
        # Initialize with retry logic
        for attempt in range(3):
            try:
                supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                
                # Verify connection with a simple health check
                response = supabase_client.auth.get_session()
                logger.info("Supabase client initialized successfully")
                return
                
            except Exception as init_error:
                logger.warning(f"Supabase initialization attempt {attempt + 1} failed: {init_error}")
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
    except Exception as e:
        logger.critical(f"Failed to initialize Supabase client: {e}")
        # In production, you might want to use a fallback auth mechanism
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with proper startup/shutdown."""
    # Startup
    logger.info("Starting SchemaSage API Gateway...")
    await initialize_supabase()
    yield
    # Shutdown
    logger.info("Shutting down SchemaSage API Gateway...")

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
    description="API Gateway for SchemaSage microservices with Supabase authentication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Auth dependency to verify JWT tokens
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    """Verify JWT token and return user info."""
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
                "user_metadata": response.user.user_metadata
            }
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None
    
    return None

# Protected route dependency
async def require_auth(user: Dict = Depends(get_current_user)) -> Dict:
    """Require authentication for protected routes."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# Authentication endpoints
@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """Sign up a new user with Supabase."""
    try:
        # Sign up user with Supabase
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {"name": request.name} if request.name else {}
            }
        })
        
        if response.user and response.session:
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
                },
                headers={
                    "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Signup failed")
            
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """Sign in a user with Supabase."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if response.user and response.session:
            return JSONResponse(
                content={
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "user_metadata": response.user.user_metadata
                    }
                },
                headers={
                    "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/signout")
async def signout(user: Dict = Depends(require_auth)):
    """Sign out the current user."""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        return JSONResponse(
            content={"message": "Signed out successfully"},
            headers={
                "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        logger.error(f"Signout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Signout failed")

@app.post("/api/auth/google")
async def google_signin():
    """Initiate Google OAuth signin."""
    try:
        # Get Google OAuth URL from Supabase
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://schemasage.vercel.app/auth/callback"
            }
        })
        
        return JSONResponse(
            content={
                "auth_url": response.url,
                "message": "Redirect to Google for authentication"
            },
            headers={
                "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        logger.error(f"Google signin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Google signin failed")

@app.get("/api/auth/me")
async def get_current_user_info(user: Dict = Depends(require_auth)):
    """Get current user information."""
    return JSONResponse(
        content={"user": user},
        headers={
            "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Basic endpoints
@app.get("/health")
async def health_check():
    """Gateway health check."""
    return {
        "gateway": "healthy",
        "status": "ok",
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_ANON_KEY),
        "timestamp": "2025-08-10T00:00:00Z"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {"status": "working", "message": "API Gateway with Supabase Auth is responding"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SchemaSage API Gateway with Supabase Authentication",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "auth_provider": "Supabase"
    }

# CORS preflight handlers
@app.options("/api/auth/{path:path}")
async def auth_options(path: str):
    """Handle CORS preflight for all auth endpoints."""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        },
        content={}
    )

# Protected routes examples (for your other services)
@app.get("/api/protected-example")
async def protected_example(user: Dict = Depends(require_auth)):
    """Example of a protected route that requires authentication."""
    return {
        "message": "This is a protected route",
        "user": user
    }
