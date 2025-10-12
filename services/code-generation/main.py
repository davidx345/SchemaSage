"""
Code Generation Microservice
Generates code from database schemas in various formats
"""
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import Dict, Any, Optional, List
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from uuid import uuid4
import os
import httpx

# Set up logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket service URL for push notifications
WEBSOCKET_SERVICE_URL = os.getenv("WEBSOCKET_SERVICE_URL", "https://schemasage-websocket-realtime.herokuapp.com")

from config import settings, CodeGenFormat
from models.schemas import (
    CodeGenerationRequest, CodeGenerationResponse, ApiHealthResponse, ErrorResponse
)
from models.database_models import CodeGenerationJob, GeneratedCodeFile, CodeTemplate
from core.database_service import CodeGenerationDatabaseService
from core.auth import get_current_user, get_optional_user
from core.code_generator import CodeGenerator, CodeGenerationError
from routers import compliance_generation_router

# Import optional components - don't fail if they have missing dependencies
try:
    from core.nl_schema_converter import NLSchemaConverter
    _nl_converter_available = True
except ImportError as e:
    logger.warning(f"NL Schema Converter not available: {e}")
    NLSchemaConverter = None
    _nl_converter_available = False

try:
    from core.etl_code_generator import ETLCodeGenerator
    _etl_generator_available = True
except ImportError as e:
    logger.warning(f"ETL Code Generator not available: {e}")
    ETLCodeGenerator = None
    _etl_generator_available = False

# Optional advanced components - only load core ones that work
_optional_components = {}

# Initialize core components
code_generator = CodeGenerator()

# Database service
db_service = CodeGenerationDatabaseService()

# Initialize optional components safely
nl_converter = NLSchemaConverter() if _nl_converter_available else None
etl_generator = ETLCodeGenerator() if _etl_generator_available else None

logger.info("Core code generator initialized")
if nl_converter:
    logger.info("NL Schema Converter available")
if etl_generator:
    logger.info("ETL Code Generator available")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Code Generation Service starting up...")
    logger.info(f"Templates loaded from: {settings.TEMPLATE_DIR}")
    logger.info(f"AI enhancement available: {settings.is_ai_enhanced()}")
    
    # Initialize database
    try:
        await db_service.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Code Generation Service shutting down...")
    try:
        await db_service.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

app = FastAPI(
    title="Code Generation Service",
    description="Microservice for generating code from database schemas",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://schemasage.vercel.app"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(compliance_generation_router)
from routers.additional_generation import router as additional_router
app.include_router(additional_router)
from routers.schema_generation import router as schema_generation_router
app.include_router(schema_generation_router)


async def send_webhook_notification(webhook_data: dict):
    """Send webhook notification to WebSocket service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{WEBSOCKET_SERVICE_URL}/webhooks/api-generated", json=webhook_data)
            logger.info("API generation webhook sent successfully")
    except Exception as e:
        # Don't fail the main request if webhook fails
        logger.warning(f"Failed to send API generation webhook: {e}")

# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Invalid request format",
            "details": exc.errors(),
            "status": "error",
        },
    )

@app.exception_handler(CodeGenerationError)
async def code_generation_exception_handler(request: Request, exc: CodeGenerationError):
    """Handle code generation errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": exc.message,
            "format": exc.format,
            "details": exc.details,
            "status": "error",
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Error in Code Generation Service: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "details": {"error": str(exc)},
        },
    )

@app.get("/health", response_model=ApiHealthResponse)
async def health_check():
    """Health check endpoint"""
    # Count available templates
    template_count = 0
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if os.path.exists(template_dir):
        template_count = len([f for f in os.listdir(template_dir) if f.endswith('.jinja2')])
    
    return ApiHealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        template_count=template_count,
        ai_enhanced=settings.is_ai_enhanced()
    )

@app.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code from schema in specified format"""
    try:
        logger.info(f"Received generation request: format={request.format}, schema_tables={len(request.schema.tables)}")
        
        generated_code = await code_generator.generate_code(
            schema=request.schema,
            format=request.format,
            options=request.options
        )
        
        # Send webhook notification for successful code generation
        webhook_data = {
            "user": getattr(request, 'user_id', 'anonymous'),
            "framework": request.format.value if hasattr(request.format, 'value') else str(request.format),
            "tables_count": len(request.schema.tables),
            "timestamp": datetime.now().isoformat()
        }
        await send_webhook_notification(webhook_data)
        
        return CodeGenerationResponse(
            code=generated_code.code,
            format=request.format,
            generated_at=datetime.now(),
            metadata=generated_code.metadata
        )
        
    except ValidationError as e:
        logger.error(f"❌ Validation error in /generate: {e}")
        logger.error(f"❌ Request validation details: {e.errors()}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Request validation failed: {e.errors()}"
        )
    except CodeGenerationError as e:
        logger.error(f"Code generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during code generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during code generation"
        )

# Add a debug endpoint to see what the frontend is sending
@app.post("/debug/generate")
async def debug_generate_request(request: dict):
    """Debug endpoint to see the raw request from frontend"""
    logger.info(f"Debug: Raw request received: {request}")
    logger.info(f"Debug: Request keys: {list(request.keys())}")
    logger.info(f"Debug: Request type: {type(request)}")
    
    # Try to parse with our schema
    try:
        parsed_request = CodeGenerationRequest(**request)
        return {
            "status": "success",
            "message": "Request parsed successfully",
            "parsed_format": parsed_request.format,
            "table_count": len(parsed_request.db_schema.tables)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to parse request: {str(e)}",
            "error_details": str(e),
            "received_keys": list(request.keys()) if isinstance(request, dict) else "Not a dict"
        }

@app.post("/generate-from-description")
async def generate_from_natural_language(
    description: str,
    format: CodeGenFormat,
    options: Optional[Dict[str, Any]] = None
):
    """Generate code from natural language description"""
    try:
        # Convert natural language to schema
        schema_response = nl_converter.convert_to_schema(description)
        
        # Generate code from schema
        generated_code = await code_generator.generate_code(
            schema=schema_response,
            format=format,
            options=options or {}
        )
        
        return {
            "schema": schema_response.dict(),
            "code": generated_code.code,
            "format": format.value,
            "metadata": generated_code.metadata
        }
        
    except Exception as e:
        logger.error(f"Error generating from description: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/schema-from-description")
async def generate_schema_from_description(
    description: str,
    options: Optional[Dict[str, Any]] = None
):
    """Generate schema from natural language description"""
    try:
        schema_response = nl_converter.convert_to_schema(
            description, 
            options=options or {}
        )
        
        return schema_response.dict()
        
    except Exception as e:
        logger.error(f"Error generating schema from description: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/formats")
async def list_formats():
    """List available code generation formats"""
    return {
        "formats": [
            {
                "value": format.value,
                "name": format.value.replace("_", " ").title(),
                "description": _get_format_description(format)
            }
            for format in CodeGenFormat
        ]
    }

@app.get("/options/{format}")
async def get_format_options(format: CodeGenFormat):
    """Get available options for a specific format"""
    return {
        "format": format.value,
        "options": _get_format_options(format)
    }

def _get_format_description(format: CodeGenFormat) -> str:
    """Get description for a code generation format"""
    descriptions = {
        CodeGenFormat.SQLALCHEMY: "SQLAlchemy ORM models with relationships",
        CodeGenFormat.PRISMA: "Prisma schema with relations and types",
        CodeGenFormat.TYPEORM: "TypeORM entity classes with decorators",
        CodeGenFormat.DJANGO_ORM: "Django ORM models with relationships",
        CodeGenFormat.SQL: "SQL DDL statements for database creation",
        CodeGenFormat.JSON: "JSON Schema definitions",
        CodeGenFormat.PYTHON_DATACLASSES: "Python dataclass definitions",
        CodeGenFormat.DBML: "Database Markup Language (DBML) schema",
        CodeGenFormat.TYPESCRIPT_INTERFACES: "TypeScript interface definitions"
    }
    return descriptions.get(format, "Code generation format")

def _get_format_options(format: CodeGenFormat) -> dict:
    """Get available options for a specific format"""
    common_options = {
        "include_statistics": {
            "type": "boolean",
            "default": True,
            "description": "Include statistical information in generated code"
        }
    }
    
    format_specific = {
        CodeGenFormat.SQLALCHEMY: {
            "use_mypy": {"type": "boolean", "default": True, "description": "Include MyPy type hints"},
            "use_validators": {"type": "boolean", "default": True, "description": "Include Pydantic validators"},
            "base_class": {"type": "string", "default": "Base", "description": "Base class name"}
        },
        CodeGenFormat.PRISMA: {
            "provider": {"type": "string", "default": "postgresql", "description": "Database provider"},
            "generate_client": {"type": "boolean", "default": True, "description": "Include Prisma client generation"}
        },
        CodeGenFormat.TYPEORM: {
            "decorators": {"type": "boolean", "default": True, "description": "Include TypeORM decorators"},
            "generate_migrations": {"type": "boolean", "default": False, "description": "Generate migration files"}
        },
        CodeGenFormat.DJANGO_ORM: {
            "app_name": {"type": "string", "default": "core", "description": "Django app name"},
            "abstract_base": {"type": "boolean", "default": False, "description": "Use abstract base classes"}
        },
        CodeGenFormat.SQL: {
            "dialect": {"type": "string", "default": "postgresql", "description": "SQL dialect"},
            "include_indexes": {"type": "boolean", "default": True, "description": "Include index definitions"}
        },
        CodeGenFormat.JSON: {
            "format": {"type": "string", "default": "draft-07", "description": "JSON Schema version"}
        },
        CodeGenFormat.PYTHON_DATACLASSES: {
            "frozen": {"type": "boolean", "default": False, "description": "Generate frozen dataclasses"},
            "slots": {"type": "boolean", "default": True, "description": "Use __slots__"}
        },
        CodeGenFormat.DBML: {
            "include_refs": {"type": "boolean", "default": True, "description": "Include relationship references"}
        },
        CodeGenFormat.TYPESCRIPT_INTERFACES: {
            "export_all": {"type": "boolean", "default": True, "description": "Export all interfaces"},
            "strict_null_checks": {"type": "boolean", "default": True, "description": "Use strict null checks"}
        }
    }
    
    return {**common_options, **format_specific.get(format, {})}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Code Generation Service",
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "endpoints": [
            "/health",
            "/generate",
            "/generate-from-description", 
            "/schema-from-description",
            "/formats",
            "/options/{format}",
            "/stats"
        ]
    }


@app.get("/stats")
async def get_generation_stats():
    """Get code generation statistics for WebSocket consumption"""
    try:
        # Get real stats from database
        total_jobs = await db_service.get_total_generation_jobs()
        successful_jobs = await db_service.get_successful_generation_jobs()
        
        stats = {
            "total_apis": total_jobs,
            "apis_scaffolded": successful_jobs,
            "apis_today": await db_service.get_jobs_today_count(),
            "templates_generated": await db_service.get_total_generated_files(),
            "most_popular_framework": "FastAPI",  # Could be calculated from jobs
            "total_frameworks": 5,
            "generation_success_rate": (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "service_status": "healthy",
            "database_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}")
        # Return safe defaults even on error
        return {
            "total_apis": 0,
            "apis_scaffolded": 0,
            "apis_today": 0,
            "templates_generated": 0,
            "most_popular_framework": "FastAPI",
            "total_frameworks": 0,
            "generation_success_rate": 0,
            "service_status": "error",
            "database_enabled": False,
            "timestamp": datetime.now().isoformat()
        }


# Database-backed code generation endpoints
@app.post("/api/generation-jobs")
async def create_generation_job(
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Create a new code generation job"""
    try:
        job_data = {
            "job_id": str(uuid4()),
            "user_id": user_id,
            "schema_input": request.get("schema_input", {}),
            "format_type": request.get("format_type", "sqlalchemy"),
            "options": request.get("options", {}),
            "status": "pending"
        }
        
        job = await db_service.create_generation_job(job_data)
        return {
            "status": "success",
            "job_id": job.job_id,
            "message": "Code generation job created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating generation job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create generation job"
        )


@app.get("/api/generation-jobs")
async def get_user_generation_jobs(
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """Get user's code generation jobs"""
    try:
        jobs = await db_service.get_user_generation_jobs(user_id, limit, offset)
        return {
            "status": "success",
            "jobs": [
                {
                    "job_id": job.job_id,
                    "format_type": job.format_type,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching generation jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch generation jobs"
        )


@app.get("/api/generation-jobs/{job_id}")
async def get_generation_job(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get specific generation job"""
    try:
        job = await db_service.get_generation_job(job_id, user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation job not found"
            )
        
        return {
            "status": "success",
            "job": {
                "job_id": job.job_id,
                "schema_input": job.schema_input,
                "format_type": job.format_type,
                "options": job.options,
                "status": job.status,
                "generated_code": job.generated_code,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching generation job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch generation job"
        )


@app.post("/api/code-files")
async def save_generated_code_file(
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Save a generated code file"""
    try:
        file_data = {
            "file_id": str(uuid4()),
            "job_id": request.get("job_id"),
            "user_id": user_id,
            "filename": request.get("filename"),
            "file_type": request.get("file_type"),
            "content": request.get("content"),
            "metadata": request.get("metadata", {})
        }
        
        code_file = await db_service.save_generated_file(file_data)
        return {
            "status": "success",
            "file_id": code_file.file_id,
            "message": "Code file saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving code file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save code file"
        )


@app.get("/api/code-files")
async def get_user_code_files(
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """Get user's generated code files"""
    try:
        files = await db_service.get_user_generated_files(user_id, limit, offset)
        return {
            "status": "success",
            "files": [
                {
                    "file_id": file.file_id,
                    "job_id": file.job_id,
                    "filename": file.filename,
                    "file_type": file.file_type,
                    "created_at": file.created_at.isoformat(),
                    "file_size": len(file.content) if file.content else 0
                }
                for file in files
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching code files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch code files"
        )


@app.post("/api/templates")
async def create_code_template(
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Create a custom code template"""
    try:
        template_data = {
            "template_id": str(uuid4()),
            "user_id": user_id,
            "name": request.get("name"),
            "description": request.get("description", ""),
            "format_type": request.get("format_type"),
            "template_content": request.get("template_content"),
            "variables": request.get("variables", {}),
            "is_public": request.get("is_public", False)
        }
        
        template = await db_service.create_code_template(template_data)
        return {
            "status": "success",
            "template_id": template.template_id,
            "message": "Code template created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating code template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create code template"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
