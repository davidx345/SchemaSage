from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import sys
import httpx
import json
from typing import Dict, Any
from datetime import datetime

# Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://schemasage.vercel.app").split(",")

# Service URLs (configure these for your deployed services)
AUTHENTICATION_SERVICE_URL = os.getenv("AUTHENTICATION_SERVICE_URL", "https://schemasage-auth-9d6de1a32af9.herokuapp.com")
CODE_GENERATION_SERVICE_URL = os.getenv("CODE_GENERATION_SERVICE_URL", "https://schemasage-code-generation-56faa300323b.herokuapp.com")
SCHEMA_DETECTION_SERVICE_URL = os.getenv("SCHEMA_DETECTION_SERVICE_URL", "https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com")
PROJECT_MANAGEMENT_SERVICE_URL = os.getenv("PROJECT_MANAGEMENT_SERVICE_URL", "https://schemasage-project-management-48496f02644b.herokuapp.com")
AI_CHAT_SERVICE_URL = os.getenv("AI_CHAT_SERVICE_URL", "https://schemasage-ai-chat-b619aa05a30e.herokuapp.com")
WEBSOCKET_REALTIME_SERVICE_URL = os.getenv("WEBSOCKET_REALTIME_SERVICE_URL", "https://schemasage-websocket-realtime-11223b2de7f4.herokuapp.com")
DATABASE_MIGRATION_SERVICE_URL = os.getenv("DATABASE_MIGRATION_SERVICE_URL", "https://schemasage-database-migration-dfc50cf95a69.herokuapp.com")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SchemaSage API Gateway",
    description="Pure routing gateway for SchemaSage microservices",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domains in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# HTTP client for proxying requests
http_client = httpx.AsyncClient(timeout=30.0)

async def proxy_request(
    request: Request,
    target_url: str,
    service_name: str
) -> Response:
    """Proxy request to target service with proper error handling."""
    try:
        # Get request details
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        # Remove host-specific headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Build target URL
        path = request.url.path
        full_url = f"{target_url}{path}"
        if query_params:
            full_url += f"?{query_params}"
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        logger.info(f"🔄 Proxying {method} {path} to {service_name}")
        
        # Make the proxied request
        response = await http_client.request(
            method=method,
            url=full_url,
            headers=headers,
            content=body,
            follow_redirects=False  # Don't follow redirects - let the client handle them
        )
        
        # Create response with original headers
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }
        
        # Log redirect responses for debugging
        if response.status_code in [301, 302, 303, 307, 308]:
            logger.info(f"🔄 {service_name} returned redirect {response.status_code} to {response.headers.get('location', 'unknown')}")
        else:
            logger.info(f"✅ {service_name} responded with {response.status_code}")
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout connecting to {service_name}")
        raise HTTPException(status_code=504, detail=f"{service_name} service timeout")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error to {service_name}")
        raise HTTPException(status_code=503, detail=f"{service_name} service unavailable")
    except Exception as e:
        logger.error(f"❌ Proxy error for {service_name}: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)[:100]}")

# ===== AUTHENTICATION SERVICE ROUTES =====

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def auth_proxy(request: Request, path: str):
    """Proxy all authentication requests to the Authentication Service."""
    try:
        # Get request details
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        # Remove host-specific headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Build target URL with stripped path
        full_url = f"{AUTHENTICATION_SERVICE_URL}/{path}"
        if query_params:
            full_url += f"?{query_params}"
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        logger.info(f"🔄 Proxying {method} /api/auth/{path} to Authentication Service at /{path}")
        
        # Make the proxied request
        response = await http_client.request(
            method=method,
            url=full_url,
            headers=headers,
            content=body,
            follow_redirects=False  # Don't follow redirects - let the client handle them
        )
        
        # Create response with original headers
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }
        
        # Log redirect responses for debugging OAuth flows
        if response.status_code in [301, 302, 303, 307, 308]:
            logger.info(f"🔄 Authentication Service returned redirect {response.status_code} to {response.headers.get('location', 'unknown')}")
        else:
            logger.info(f"✅ Authentication Service responded with {response.status_code}")
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout connecting to Authentication Service")
        raise HTTPException(status_code=504, detail="Authentication service timeout")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error to Authentication Service")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except Exception as e:
        logger.error(f"❌ Auth proxy error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)[:100]}")

# ===== CODE GENERATION SERVICE ROUTES =====

@app.api_route("/api/code-generation/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def code_generation_proxy(request: Request, path: str):
    """Proxy code generation requests."""
    return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

@app.api_route("/api/generate/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def generate_proxy(request: Request, path: str):
    """Proxy generation requests."""
    return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

# ===== SCHEMA ROUTES =====

# Specific route for schema generation (goes to Code Generation Service)
@app.api_route("/api/schema/generate", methods=["POST", "OPTIONS"])
async def schema_generate_proxy(request: Request):
    """Proxy schema generation requests to Code Generation Service."""
    return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

# General schema detection routes (goes to Schema Detection Service)
@app.api_route("/api/schema/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def schema_proxy(request: Request, path: str):
    """Proxy schema detection requests."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

@app.api_route("/api/detect/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def detect_proxy(request: Request, path: str):
    """Proxy detection requests."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

# ===== PROJECT MANAGEMENT SERVICE ROUTES =====

@app.api_route("/api/projects/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def projects_proxy(request: Request, path: str):
    """Proxy project management requests."""
    return await proxy_request(request, PROJECT_MANAGEMENT_SERVICE_URL, "Project Management Service")

# ===== AI CHAT SERVICE ROUTES =====

@app.api_route("/api/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def chat_proxy(request: Request, path: str):
    """Proxy AI chat requests."""
    return await proxy_request(request, AI_CHAT_SERVICE_URL, "AI Chat Service")

@app.api_route("/api/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def ai_proxy(request: Request, path: str):
    """Proxy AI requests."""
    return await proxy_request(request, AI_CHAT_SERVICE_URL, "AI Chat Service")

# ===== DATABASE MIGRATION SERVICE ROUTES =====

@app.api_route("/api/database/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def database_proxy(request: Request, path: str):
    """Proxy database migration and connection requests."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

@app.api_route("/api/migration/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def migration_proxy(request: Request, path: str):
    """Proxy migration requests."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# ===== HEALTH AND STATUS =====

@app.get("/health")
async def health_check():
    """Gateway health check with service status."""
    services_status = {}
    
    # Check each service health
    services = {
        "authentication": AUTHENTICATION_SERVICE_URL,
        "code-generation": CODE_GENERATION_SERVICE_URL,
        "schema-detection": SCHEMA_DETECTION_SERVICE_URL,
        "project-management": PROJECT_MANAGEMENT_SERVICE_URL,
        "ai-chat": AI_CHAT_SERVICE_URL,
        "websocket-realtime": WEBSOCKET_REALTIME_SERVICE_URL,
        "database-migration": DATABASE_MIGRATION_SERVICE_URL
    }
    
    for service_name, service_url in services.items():
        try:
            response = await http_client.get(f"{service_url}/health", timeout=5.0)
            services_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code
            }
        except Exception as e:
            services_status[service_name] = {
                "status": "unreachable",
                "error": str(e)[:100]
            }
    
    # Overall health
    healthy_services = sum(1 for s in services_status.values() if s.get("status") == "healthy")
    total_services = len(services)
    
    return {
        "gateway": "healthy",
        "version": "3.0.0",
        "type": "api_gateway",
        "services": services_status,
        "services_healthy": f"{healthy_services}/{total_services}",
        "timestamp": "2025-08-20T00:00:00Z"
    }

@app.get("/")
async def root():
    """Root endpoint with gateway information."""
    return {
        "service": "SchemaSage API Gateway",
        "version": "3.0.0",
        "type": "pure_router",
        "status": "running",
        "description": "Routes requests to appropriate microservices",
        "routes": {
            "authentication": "/api/auth/*",
            "code_generation": "/api/code-generation/* | /api/generate/* | /api/schema/generate",
            "schema_detection": "/api/schema/* (except /api/schema/generate) | /api/detect/*",
            "project_management": "/api/projects/*",
            "ai_chat": "/api/chat/* | /api/ai/*",
            "database_migration": "/api/database/* | /api/migration/*",
            "websocket_realtime": "/ws/* (WebSocket connections)"
        },
        "services": {
            "authentication": AUTHENTICATION_SERVICE_URL,
            "code_generation": CODE_GENERATION_SERVICE_URL,
            "schema_detection": SCHEMA_DETECTION_SERVICE_URL,
            "project_management": PROJECT_MANAGEMENT_SERVICE_URL,
            "ai_chat": AI_CHAT_SERVICE_URL,
            "websocket_realtime": WEBSOCKET_REALTIME_SERVICE_URL,
            "database_migration": DATABASE_MIGRATION_SERVICE_URL
        }
    }

# ===== TOOL METRICS ENDPOINT =====

@app.get("/api/tools/metrics")
async def get_tool_metrics():
    """Return tool metrics (stub/example)."""
    # Example static response; replace with real metrics as needed
    return {
        "tools": [
            {"name": "Code Generation", "status": "healthy", "version": "1.0.0"},
            {"name": "Schema Detection", "status": "healthy", "version": "1.0.0"},
            {"name": "API Gateway", "status": "healthy", "version": "3.0.0"}
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Catch-all for unmatched routes
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(request: Request, path: str):
    """Handle unmatched routes."""
    logger.warning(f"🚫 Unmatched route: {request.method} /{path}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Route not found",
            "method": request.method,
            "path": f"/{path}",
            "available_routes": [
                "/api/auth/* -> Authentication Service",
                "/api/code-generation/* -> Code Generation Service",
                "/api/schema/generate -> Code Generation Service",
                "/api/schema/* -> Schema Detection Service",
                "/api/projects/* -> Project Management Service",
                "/api/chat/* -> AI Chat Service",
                "/api/database/* -> Database Migration Service"
            ]
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
