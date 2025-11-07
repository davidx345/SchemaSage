"""
Schema Detection Microservice - Clean Version

Independent service for schema detection and analysis.
"""
from fastapi import FastAPI, Request, status, Depends, Security, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from contextlib import asynccontextmanager
import os
import jwt
from datetime import datetime
from uuid import uuid4

from models.schemas import DetectionResponse
from models.database_models import SchemaDetectionJob, DetectedSchema, SchemaAnalysis
from core.database_service import SchemaDetectionDatabaseService
from core.auth import get_current_user, get_optional_user
from routers import detection_router, lineage_router, history_router, compliance_detection_router, enhanced_lineage
from routers import search, query, data_cleaning, data_dictionary, frontend_api
from routers.security_audit import router as security_audit_router
from routers.schema_analysis import router as schema_analysis_router
from routers.cloud_provision import router as cloud_provision_router
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

# Database service
db_service = SchemaDetectionDatabaseService()


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
    
    # Initialize database
    try:
        await db_service.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Schema Detection Service shutting down...")
    try:
        await db_service.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


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
app.include_router(enhanced_lineage.router)
app.include_router(search.router)
app.include_router(query.router)
app.include_router(data_cleaning.router)
app.include_router(data_dictionary.router)
app.include_router(frontend_api.router)
app.include_router(security_audit_router)
app.include_router(schema_analysis_router)
app.include_router(cloud_provision_router)

# Add the documentation router to match frontend calls
from routers.documentation import router as documentation_router
app.include_router(documentation_router)


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
            "get_docs": "GET /documentation/get",
            "data_dictionary": "GET /data-dictionary/get",
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
            "cors": True,
            "database_persistence": True
        }
    }


# Database-backed endpoints
@app.post("/api/detection-jobs")
async def create_detection_job(
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Create a new schema detection job"""
    try:
        job_data = {
            "job_id": str(uuid4()),
            "user_id": user_id,
            "job_type": request.get("job_type", "schema_detection"),
            "data_source": request.get("data_source"),
            "parameters": request.get("parameters", {}),
            "status": "pending"
        }
        
        job = await db_service.create_detection_job(job_data)
        return {
            "status": "success",
            "job_id": job.job_id,
            "message": "Detection job created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating detection job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create detection job"
        )


@app.get("/api/detection-jobs")
async def get_user_detection_jobs(
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """Get user's detection jobs"""
    try:
        jobs = await db_service.get_user_detection_jobs(user_id, limit, offset)
        return {
            "status": "success",
            "jobs": [
                {
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "data_source": job.data_source,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching detection jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch detection jobs"
        )


@app.get("/api/detection-jobs/{job_id}")
async def get_detection_job(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get specific detection job"""
    try:
        job = await db_service.get_detection_job(job_id, user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection job not found"
            )
        
        return {
            "status": "success",
            "job": {
                "job_id": job.job_id,
                "job_type": job.job_type,
                "data_source": job.data_source,
                "parameters": job.parameters,
                "status": job.status,
                "result": job.result,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching detection job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch detection job"
        )


@app.post("/api/schemas")
async def save_detected_schema(
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Save a detected schema"""
    try:
        schema_data = {
            "schema_id": str(uuid4()),
            "user_id": user_id,
            "schema_name": request.get("schema_name"),
            "table_name": request.get("table_name"),
            "schema_definition": request.get("schema_definition", {}),
            "data_source": request.get("data_source"),
            "detection_method": request.get("detection_method", "manual"),
            "confidence_score": request.get("confidence_score", 0.0),
            "tags": request.get("tags", [])
        }
        
        schema = await db_service.create_detected_schema(schema_data)
        return {
            "status": "success",
            "schema_id": schema.schema_id,
            "message": "Schema saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save schema"
        )


@app.get("/api/schemas")
async def get_user_schemas(
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """Get user's detected schemas"""
    try:
        schemas = await db_service.get_user_schemas(user_id, limit, offset)
        return {
            "status": "success",
            "schemas": [
                {
                    "schema_id": schema.schema_id,
                    "schema_name": schema.schema_name,
                    "table_name": schema.table_name,
                    "data_source": schema.data_source,
                    "detection_method": schema.detection_method,
                    "confidence_score": schema.confidence_score,
                    "created_at": schema.created_at.isoformat(),
                    "tags": schema.tags
                }
                for schema in schemas
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching schemas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch schemas"
        )


@app.post("/api/schemas/{schema_id}/analysis")
async def create_schema_analysis(
    schema_id: str,
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Create schema analysis"""
    try:
        analysis_data = {
            "analysis_id": str(uuid4()),
            "schema_id": schema_id,
            "user_id": user_id,
            "analysis_type": request.get("analysis_type", "quality"),
            "analysis_result": request.get("analysis_result", {}),
            "quality_score": request.get("quality_score", 0.0),
            "recommendations": request.get("recommendations", [])
        }
        
        analysis = await db_service.create_schema_analysis(analysis_data)
        return {
            "status": "success",
            "analysis_id": analysis.analysis_id,
            "message": "Schema analysis created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating schema analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schema analysis"
        )


from fastapi import UploadFile, File
from typing import List, Dict, Any
import pandas as pd
import io

@app.post("/api/transform")
async def transform_data(
    request: Request
):
    """
    Accepts: Uploaded data, transformation instructions, output format
    Request Format:
    {
      "data": [ /* array of objects, parsed from CSV/JSON */ ],
      "instructions": "Remove duplicates and normalize column names to lowercase",
      "output_format": "pandas", // or "sql", "pyspark"
      "steps": [ /* optional: previous transformation steps */ ]
    }
    """
    try:
        body = await request.json()
        data = body.get("data")
        instructions = body.get("instructions", "")
        output_format = body.get("output_format", "pandas")
        steps = body.get("steps", [])

        # Validate data
        if not isinstance(data, list) or not data:
            return {"success": False, "error": {"message": "No data provided or data is not a list."}}

        # Convert to DataFrame
        df = pd.DataFrame(data)
        preview = None
        code = ""
        explanation = ""

        # Example: Remove duplicates and normalize column names
        if "remove duplicates" in instructions.lower():
            df = df.drop_duplicates()
            code += "df = df.drop_duplicates()\n"
            explanation += "Removed duplicate rows. "
        if "normalize column names" in instructions.lower() or "lowercase column names" in instructions.lower():
            df.columns = [c.lower() for c in df.columns]
            code += "df.columns = [c.lower() for c in df.columns]\n"
            explanation += "Normalized column names to lowercase. "

        # Add more transformation logic here as needed

        preview = df.head(10).to_dict(orient="records")

        # Output code for requested format
        if output_format == "pandas":
            code = f"import pandas as pd\n{code}"
        elif output_format == "sql":
            code = "-- SQL transformation code generation not implemented yet."
        elif output_format == "pyspark":
            code = "# PySpark transformation code generation not implemented yet."

        return {
            "success": True,
            "data": {
                "code": code,
                "explanation": explanation,
                "preview": preview
            },
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": {"message": str(e)}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=getattr(settings, 'HOST', '0.0.0.0'), 
        port=getattr(settings, 'PORT', 8000)
    )
