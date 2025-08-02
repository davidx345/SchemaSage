"""API Gateway for SchemaSage Microservices."""

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

# Import modular components
from middleware.auth import verify_token, get_user_from_token
from middleware.rate_limit import check_rate_limit, get_rate_limit_info
from config.settings import CORS_ORIGINS, ROUTE_MAPPINGS, is_protected_route
from core.proxy import proxy_service
from core.health import health_monitor

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("API Gateway starting up...")
    yield
    # Shutdown
    logger.info("API Gateway shutting down...")
    await proxy_service.close()

app = FastAPI(
    title="SchemaSage API Gateway",
    description="API Gateway for SchemaSage microservices architecture",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://schemasage.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    client_ip = request.client.host
    
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)
    
    try:
        # Check rate limit
        check_rate_limit(client_ip)
        response = await call_next(request)
        
        # Add rate limit headers
        rate_info = get_rate_limit_info(client_ip)
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
        
        return response
        
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

@app.get("/health")
async def health_check():
    """Gateway and services health check."""
    try:
        health_data = await health_monitor.get_overall_health()
        status_code = 200 if health_data["status"] == "healthy" else 503
        
        return JSONResponse(
            content={
                "gateway": "healthy",
                "timestamp": "2025-07-27T00:00:00Z",
                **health_data
            },
            status_code=status_code
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            content={
                "gateway": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )

@app.get("/health/{service_name}")
async def service_health_check(service_name: str):
    """Check health of a specific service."""
    try:
        health_data = await health_monitor.get_service_health(service_name)
        status_code = 200 if health_data["status"] == "healthy" else 503
        
        return JSONResponse(
            content=health_data,
            status_code=status_code
        )
    except Exception as e:
        logger.error(f"Service health check error for {service_name}: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_handler(path: str, request: Request, user: Dict = Depends(get_user_from_token)):
    """Main proxy handler for all API routes."""
    full_path = f"/{path}"
    
    # Find matching route configuration
    route_config = None
    service_name = None
    
    for route_path, config in ROUTE_MAPPINGS.items():
        if full_path.startswith(route_path):
            route_config = config
            service_name = config.get("service")
            break
    
    # If no specific route found, try to infer service from path
    if not route_config:
        path_parts = path.split("/")
        if len(path_parts) >= 2 and path_parts[0] == "api":
            service_map = {
                "schema": "schema-detection",
                "code": "code-generation", 
                "chat": "ai-chat",
                "projects": "project-management",
                "auth": "authentication"
            }
            service_name = service_map.get(path_parts[1])
            route_config = {"service": service_name, "auth_required": True}
    
    if not service_name:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Check authentication requirement
    if route_config.get("auth_required", True) and not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Apply user-specific rate limiting if authenticated
    if user:
        check_rate_limit(request.client.host, user.get("user_id"), limit_per_minute=200)
    
    # Proxy the request
    try:
        return await proxy_service.proxy_request(service_name, f"/{path}", request)
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SchemaSage API Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Remove uvicorn.run() for Heroku deployment - use Procfile instead
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
