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
    allow_origins=CORS_ORIGINS,  # Use specific origins instead of wildcard with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# HTTP client for proxying requests
# Increased timeout for long-running operations like schema extraction
http_client = httpx.AsyncClient(timeout=60.0)

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

# Phase 1: Query Cost Explainer
@app.api_route("/api/query/analyze-cost", methods=["POST", "GET", "OPTIONS"])
async def query_cost_analyzer_proxy(request: Request):
    """Proxy query cost analysis requests to Code Generation Service."""
    return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

# Phase 1 Week 2: SQL Dialect Translator
@app.api_route("/api/code/translate-sql", methods=["POST", "OPTIONS"])
async def sql_translator_proxy(request: Request):
    """Proxy SQL translation requests to Code Generation Service."""
    return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

# Phase 1 Week 3: Performance Benchmark Tool
@app.api_route("/api/performance/benchmark", methods=["POST", "OPTIONS"])
async def performance_benchmark_proxy(request: Request):
    """Proxy performance benchmark requests to Code Generation Service."""
    return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

# Specific route for API scaffolding (goes to Code Generation Service)
@app.api_route("/api/schema/scaffold", methods=["POST", "OPTIONS"])
async def schema_scaffold_proxy(request: Request):
     """Proxy API scaffolding requests to Code Generation Service."""
     return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

# Direct route for API scaffolding (frontend may POST to /api/scaffold)
@app.api_route("/api/scaffold", methods=["POST", "OPTIONS"])
async def scaffold_proxy(request: Request):
    """Proxy API scaffolding requests to Code Generation Service (direct route)."""
    # Special handling: strip /api prefix and forward to /scaffold
    try:
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        # Remove host-specific headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Build target URL - forward to /schema/scaffold (correct path based on router prefix)
        full_url = f"{CODE_GENERATION_SERVICE_URL}/schema/scaffold"
        if query_params:
            full_url += f"?{query_params}"
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        logger.info(f"🔄 Proxying {method} /api/scaffold to Code Generation Service at /schema/scaffold")
        
        # Make the proxied request
        response = await http_client.request(
            method=method,
            url=full_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        
        # Create response with original headers
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }
        
        logger.info(f"✅ Code Generation Service responded with {response.status_code}")
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout connecting to Code Generation Service")
        raise HTTPException(status_code=504, detail="Code Generation Service timeout")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error to Code Generation Service")
        raise HTTPException(status_code=503, detail="Code Generation Service unavailable")
    except Exception as e:
        logger.error(f"❌ Scaffold proxy error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)[:100]}")# ===== SCHEMA ROUTES =====

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

# Phase 1: PII Detection Scanner
@app.api_route("/api/compliance/detect-pii", methods=["POST", "OPTIONS"])
async def pii_detection_proxy(request: Request):
    """Proxy PII detection requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

# Phase 1 Week 2: Schema Compatibility Checker
@app.api_route("/api/schema/compatibility", methods=["POST", "OPTIONS"])
async def schema_compatibility_proxy(request: Request):
    """Proxy schema compatibility requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

# Phase 1 Week 3: Schema Diff Visualizer
@app.api_route("/api/schema/diff", methods=["POST", "OPTIONS"])
async def schema_diff_proxy(request: Request):
    """Proxy schema diff requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

# ===== PROJECT MANAGEMENT SERVICE ROUTES ====="

# Route for /api/projects (no subpath) - for listing and creating projects
@app.api_route("/api/projects", methods=["GET", "POST", "OPTIONS"])
async def projects_root_proxy(request: Request):
    """Proxy project management requests to /api/projects (root)."""
    return await proxy_request(request, PROJECT_MANAGEMENT_SERVICE_URL, "Project Management Service")

# Route for /api/projects/{path:path} - for specific project operations
@app.api_route("/api/projects/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def projects_proxy(request: Request, path: str):
    """Proxy project management requests with subpaths."""
    return await proxy_request(request, PROJECT_MANAGEMENT_SERVICE_URL, "Project Management Service")

# ===== AI CHAT SERVICE ROUTES =====

@app.api_route("/api/chat", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def chat_direct_proxy(request: Request):
    """Proxy AI chat requests to /chat endpoint."""
    try:
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        # Log received headers for debugging
        logger.info(f"🔍 Gateway received headers for /api/chat: {list(headers.keys())}")
        auth_header = headers.get('Authorization') or headers.get('authorization')
        logger.info(f"🔍 Gateway Authorization header: {auth_header[:50] if auth_header else 'None'}...")
        
        # Remove host-specific headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Log headers being forwarded
        logger.info(f"🔍 Gateway forwarding headers: {list(headers.keys())}")
        forward_auth = headers.get('Authorization') or headers.get('authorization')
        logger.info(f"🔍 Gateway forwarding Authorization: {forward_auth[:50] if forward_auth else 'None'}...")
        
        # Build target URL - forward to /chat
        full_url = f"{AI_CHAT_SERVICE_URL}/chat"
        if query_params:
            full_url += f"?{query_params}"
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        logger.info(f"🔄 Proxying {method} /api/chat to AI Chat Service at /chat")
        
        # Make the proxied request
        response = await http_client.request(
            method=method,
            url=full_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        
        # Log response
        logger.info(f"✅ AI Chat Service responded with {response.status_code}")
        
        # Create response with original headers
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout connecting to AI Chat Service")
        raise HTTPException(status_code=504, detail="AI Chat Service timeout")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error to AI Chat Service")
        raise HTTPException(status_code=503, detail="AI Chat Service unavailable")
    except Exception as e:
        logger.error(f"❌ Chat proxy error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)[:100]}")

@app.api_route("/api/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def chat_proxy(request: Request, path: str):
    """Proxy AI chat requests with subpaths."""
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

# Phase 1: Cost Comparison Widget
@app.api_route("/api/cost/compare", methods=["POST", "OPTIONS"])
async def cost_comparison_proxy(request: Request):
    """Proxy cost comparison requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Phase 1 Week 2: Migration Timeline Generator
@app.api_route("/api/migration/timeline", methods=["POST", "OPTIONS"])
async def migration_timeline_proxy(request: Request):
    """Proxy migration timeline requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Phase 1 Week 2: Data Type Mapper
@app.api_route("/api/migration/map-types", methods=["POST", "OPTIONS"])
async def type_mapper_proxy(request: Request):
    """Proxy data type mapping requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Phase 1 Week 3: Migration Monitor
@app.api_route("/api/migration/monitor", methods=["POST", "OPTIONS"])
async def migration_monitor_proxy(request: Request):
    """Proxy migration monitoring requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Phase 1 Week 3: Rollback Planner
@app.api_route("/api/migration/rollback-plan", methods=["POST", "OPTIONS"])
async def migration_rollback_proxy(request: Request):
    """Proxy rollback planning requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Phase 2.2: Health Benchmark System
@app.api_route("/api/health/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def health_proxy(request: Request, path: str):
    """Proxy health benchmark requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Phase 2.3: Schema Debt Tracker
@app.api_route("/api/debt/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def debt_proxy(request: Request, path: str):
    """Proxy schema debt tracker requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

# Phase 2.4: Cost Anomaly Detector
@app.api_route("/api/anomaly/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def anomaly_proxy(request: Request, path: str):
    """Proxy cost anomaly detector requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Phase 1 Week 4: Query Performance Predictor
@app.api_route("/api/query/predict-performance", methods=["POST", "OPTIONS"])
async def query_predictor_proxy(request: Request):
    """Proxy query performance prediction requests to Code Generation Service."""
    return await proxy_request(request, CODE_GENERATION_SERVICE_URL, "Code Generation Service")

# Phase 1 Week 4: Index Recommendation Engine
@app.api_route("/api/schema/recommend-indexes", methods=["POST", "OPTIONS"])
async def index_recommendation_proxy(request: Request):
    """Proxy index recommendation requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

# Phase 1 Week 4: Data Validation Suite
@app.api_route("/api/validation/validate-data", methods=["POST", "OPTIONS"])
async def data_validation_proxy(request: Request):
    """Proxy data validation requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

# Phase 1 Week 4: Enhanced Migration Cost Calculator
@app.api_route("/api/cost/calculate-migration", methods=["POST", "OPTIONS"])
async def enhanced_cost_calculator_proxy(request: Request):
    """Proxy enhanced cost calculation requests to Database Migration Service."""
    return await proxy_request(request, DATABASE_MIGRATION_SERVICE_URL, "Database Migration Service")

# Direct routes for database connection testing and import (frontend compatibility)
@app.api_route("/api/test-connection-url", methods=["POST", "OPTIONS"])
async def test_connection_url_proxy(request: Request):
    """Proxy database connection test requests (direct route for frontend)."""
    try:
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        # Remove host-specific headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Build target URL - forward to /database/test-connection-url (no /api prefix on migration service)
        full_url = f"{DATABASE_MIGRATION_SERVICE_URL}/database/test-connection-url"
        if query_params:
            full_url += f"?{query_params}"
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        logger.info(f"🔄 Proxying {method} /api/test-connection-url to Database Migration Service at /database/test-connection-url")
        
        # Make the proxied request
        response = await http_client.request(
            method=method,
            url=full_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        
        # Create response with original headers
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }
        
        logger.info(f"✅ Database Migration Service responded with {response.status_code}")
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout connecting to Database Migration Service")
        raise HTTPException(status_code=504, detail="Database Migration Service timeout")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error to Database Migration Service")
        raise HTTPException(status_code=503, detail="Database Migration Service unavailable")
    except Exception as e:
        logger.error(f"❌ Test connection proxy error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)[:100]}")

@app.api_route("/api/import-from-url", methods=["POST", "OPTIONS"])
async def import_from_url_proxy(request: Request):
    """Proxy database import requests (direct route for frontend)."""
    try:
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        # Remove host-specific headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Build target URL - forward to /database/import-from-url (no /api prefix on migration service)
        full_url = f"{DATABASE_MIGRATION_SERVICE_URL}/database/import-from-url"
        if query_params:
            full_url += f"?{query_params}"
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        logger.info(f"🔄 Proxying {method} /api/import-from-url to Database Migration Service at /database/import-from-url")
        
        # Make the proxied request
        response = await http_client.request(
            method=method,
            url=full_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        
        # Create response with original headers
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }
        
        logger.info(f"✅ Database Migration Service responded with {response.status_code}")
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout connecting to Database Migration Service")
        raise HTTPException(status_code=504, detail="Database Migration Service timeout")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error to Database Migration Service")
        raise HTTPException(status_code=503, detail="Database Migration Service unavailable")
    except Exception as e:
        logger.error(f"❌ Import from URL proxy error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)[:100]}")

@app.api_route("/api/import-status/{task_id}", methods=["GET", "OPTIONS"])
async def import_status_proxy(request: Request, task_id: str):
    """Proxy database import status requests (direct route for frontend)."""
    try:
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        # Remove host-specific headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Build target URL - forward to /database/import-status/{task_id} (no /api prefix on migration service)
        full_url = f"{DATABASE_MIGRATION_SERVICE_URL}/database/import-status/{task_id}"
        if query_params:
            full_url += f"?{query_params}"
        
        logger.info(f"🔄 Proxying {method} /api/import-status/{task_id} to Database Migration Service at /database/import-status/{task_id}")
        
        # Make the proxied request
        response = await http_client.request(
            method=method,
            url=full_url,
            headers=headers,
            follow_redirects=False
        )
        
        # Create response with original headers
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }
        
        logger.info(f"✅ Database Migration Service responded with {response.status_code}")
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout connecting to Database Migration Service")
        raise HTTPException(status_code=504, detail="Database Migration Service timeout")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error to Database Migration Service")
        raise HTTPException(status_code=503, detail="Database Migration Service unavailable")
    except Exception as e:
        logger.error(f"❌ Import status proxy error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)[:100]}")

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
            "code_generation": "/api/code-generation/* | /api/generate/* | /api/schema/generate | /api/query/analyze-cost | /api/code/translate-sql",
            "schema_detection": "/api/schema/* (except /api/schema/generate) | /api/detect/* | /api/compliance/* | /api/schema/compatibility",
            "project_management": "/api/projects/*",
            "ai_chat": "/api/chat/* | /api/ai/*",
            "database_migration": "/api/database/* | /api/migration/* | /api/health/* | /api/cost/compare | /api/migration/timeline | /api/migration/map-types | /api/test-connection-url | /api/import-from-url | /api/import-status/{task_id}",
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

# ===== DATA TRANSFORMATION PROXY ENDPOINT =====

@app.api_route("/api/transform", methods=["POST", "OPTIONS"])
async def transform_proxy(request: Request):
    """Proxy data transformation requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

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
                "/api/query/analyze-cost -> Code Generation Service (Phase 1 Week 1)",
                "/api/code/translate-sql -> Code Generation Service (Phase 1 Week 2)",
                "/api/schema/* -> Schema Detection Service",
                "/api/compliance/detect-pii -> Schema Detection Service (Phase 1 Week 1)",
                "/api/schema/compatibility -> Schema Detection Service (Phase 1 Week 2)",
                "/api/projects/* -> Project Management Service",
                "/api/chat/* -> AI Chat Service",
                "/api/database/* -> Database Migration Service",
                "/api/cost/compare -> Database Migration Service (Phase 1 Week 1)",
                "/api/migration/timeline -> Database Migration Service (Phase 1 Week 2)",
                "/api/migration/map-types -> Database Migration Service (Phase 1 Week 2)",
                "/api/test-connection-url -> Database Migration Service",
                "/api/import-from-url -> Database Migration Service",
                "/api/import-status/{task_id} -> Database Migration Service"
            ]
        }
    )

@app.api_route("/api/compliance/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def compliance_proxy(path: str, request: Request):
    """Proxy compliance requests to Schema Detection Service."""
    return await proxy_request(request, SCHEMA_DETECTION_SERVICE_URL, "Schema Detection Service")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
