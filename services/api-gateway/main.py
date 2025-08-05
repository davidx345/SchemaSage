"""API Gateway for SchemaSage Microservices."""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import httpx

# Simple imports for now - avoid module import issues
logger = logging.getLogger(__name__)

# Basic configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://schemasage.vercel.app").split(",")
AUTHENTICATION_URL = os.getenv("AUTHENTICATION_URL", "https://schemasage-auth-9d6de1a32af9.herokuapp.com")

app = FastAPI(
    title="SchemaSage API Gateway",
    description="API Gateway for SchemaSage microservices architecture",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Gateway health check."""
    return {
        "gateway": "healthy",
        "status": "ok",
        "timestamp": "2025-07-27T00:00:00Z"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {"status": "working", "message": "API Gateway is responding"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SchemaSage API Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.options("/api/auth/signup")
async def auth_signup_options():
    """Handle CORS preflight for auth signup."""
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

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def auth_proxy(path: str, request: Request):
    """Proxy authentication requests."""
    # Handle CORS preflight requests
    if request.method == "OPTIONS":
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
    
    # Forward to authentication service
    async with httpx.AsyncClient() as client:
        try:
            # Get request body if present
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            # Forward the request
            response = await client.request(
                method=request.method,
                url=f"{AUTHENTICATION_URL}/api/auth/{path}",
                headers=dict(request.headers),
                content=body,
                timeout=30.0
            )
            
            # Return the response with CORS headers
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.content else {},
                headers={
                    "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except Exception as e:
            logger.error(f"Auth proxy error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Authentication service error"},
                headers={
                    "Access-Control-Allow-Origin": "https://schemasage.vercel.app",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
