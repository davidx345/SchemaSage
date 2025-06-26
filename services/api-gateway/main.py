"""API Gateway for SchemaSage Microservices."""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

# Service configuration
SERVICES = {
    "schema-detection": {
        "url": os.getenv("SCHEMA_DETECTION_URL", "http://localhost:8001"),
        "health_endpoint": "/health"
    },
    "code-generation": {
        "url": os.getenv("CODE_GENERATION_URL", "http://localhost:8002"),
        "health_endpoint": "/health"
    },
    "ai-chat": {
        "url": os.getenv("AI_CHAT_URL", "http://localhost:8003"),
        "health_endpoint": "/health"
    },
    "project-management": {
        "url": os.getenv("PROJECT_MANAGEMENT_URL", "http://localhost:8004"),
        "health_endpoint": "/health"
    },
    "authentication": {
        "url": os.getenv("AUTHENTICATION_URL", "http://authentication:8005"),
        "health_endpoint": "/health"
    }
}

# Route mappings
ROUTE_MAPPINGS = {
    "/api/schema/detect": "schema-detection",
    "/api/schema/detect-file": "schema-detection", 
    "/api/schema/generate-code": "code-generation",
    "/api/code/generate": "code-generation",
    "/api/code/formats": "code-generation",
    "/api/chat": "ai-chat",
    "/api/chat/": "ai-chat",
    "/api/database/projects": "project-management",
    "/api/projects": "project-management",
    "/api/auth/signup": "authentication",
    "/api/auth/login": "authentication",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("API Gateway starting up...")
    yield
    # Shutdown
    logger.info("API Gateway shutting down...")

app = FastAPI(
    title="SchemaSage API Gateway",
    description="API Gateway for SchemaSage Microservices",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def proxy_request(service_name: str, path: str, request: Request) -> JSONResponse:
    """Proxy request to appropriate microservice."""
    service_config = SERVICES.get(service_name)
    if not service_config:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    service_url = service_config["url"]
    target_url = f"{service_url}{path}"
    
    # Get request data
    method = request.method
    headers = dict(request.headers)
    # Remove host header to avoid conflicts
    headers.pop("host", None)
    
    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(target_url, headers=headers, params=request.query_params)
            elif method == "POST":
                body = await request.body()
                response = await client.post(target_url, headers=headers, content=body)
            elif method == "PUT":
                body = await request.body()
                response = await client.put(target_url, headers=headers, content=body)
            elif method == "DELETE":
                response = await client.delete(target_url, headers=headers)
            elif method == "OPTIONS":
                response = await client.options(target_url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail=f"Method {method} not allowed")
            
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except httpx.RequestError as e:
        logger.error(f"Request to {service_name} failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")
    except Exception as e:
        logger.error(f"Unexpected error proxying to {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for API Gateway and all services."""
    service_health = {}
    
    for service_name, config in SERVICES.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{config['url']}{config['health_endpoint']}", timeout=5.0)
                service_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            service_health[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    overall_healthy = all(s["status"] == "healthy" for s in service_health.values())
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "gateway": "healthy",
        "services": service_health,
        "version": "1.0.0"
    }

# Dynamic route handler
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_handler(path: str, request: Request):
    """Handle all requests and proxy to appropriate service."""
    full_path = f"/{path}"
    
    # Find matching service
    service_name = None
    service_path = full_path
    
    for route_prefix, service in ROUTE_MAPPINGS.items():
        if full_path.startswith(route_prefix):
            service_name = service
            # Remove the API prefix and map to service-specific path
            if route_prefix.startswith("/api/schema/"):
                service_path = full_path.replace("/api/schema", "")
            elif route_prefix.startswith("/api/code/"):
                service_path = full_path.replace("/api/code", "")
            elif route_prefix.startswith("/api/chat"):
                service_path = full_path.replace("/api/chat", "/chat")
            elif route_prefix.startswith("/api/database/"):
                service_path = full_path.replace("/api/database", "")
            elif route_prefix.startswith("/api/projects"):
                service_path = full_path.replace("/api", "")
            break
    
    if not service_name:
        raise HTTPException(status_code=404, detail=f"No service found for path: {full_path}")
    
    return await proxy_request(service_name, service_path, request)

@app.post("/api/schema/detect-file")
async def proxy_detect_file(request: Request):
    return await proxy_request("schema-detection", "/detect-file", request)

@app.post("/api/code/generate")
async def proxy_generate_code(request: Request):
    return await proxy_request("code-generation", "/generate", request)

@app.post("/api/projects")
async def proxy_create_project(request: Request):
    return await proxy_request("project-management", "/projects", request)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SchemaSage API Gateway",
        "status": "running",
        "version": "1.0.0",
        "services": list(SERVICES.keys()),
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
