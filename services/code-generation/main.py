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
    CodeGenerationRequest, CodeGenerationResponse, ApiHealthResponse, ErrorResponse,
    TableInfo, ColumnInfo, Relationship, SchemaMetadata, SchemaResponse
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

# CORS middleware - Enhanced for better compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development - restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add middleware to prevent response caching
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    """Add no-cache headers to prevent frontend caching of generated code"""
    response = await call_next(request)
    
    # Add no-cache headers for code generation endpoints
    if request.url.path in ["/generate", "/code-generation/generate"]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["ETag"] = f'"{uuid4()}"'
    
    return response

# Global exception handlers for better debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed logging"""
    logger.error(f"❌ VALIDATION ERROR for {request.method} {request.url}")
    logger.error(f"❌ Request headers: {dict(request.headers)}")
    
    # Log the request body if possible
    try:
        body = await request.body()
        logger.error(f"❌ Request body: {body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"❌ Could not read request body: {e}")
    
    # Log detailed validation errors
    logger.error(f"❌ Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": exc.errors(),
            "body": body.decode('utf-8') if 'body' in locals() else None
        }
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    logger.error(f"❌ PYDANTIC VALIDATION ERROR for {request.method} {request.url}")
    logger.error(f"❌ Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Data validation failed",
            "errors": exc.errors()
        }
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


# Utility: Detect JSON Schema
def is_json_schema(obj: dict) -> bool:
    return isinstance(obj, dict) and "$schema" in obj and "type" in obj and "properties" in obj

# Utility: Convert JSON Schema to database schema format
def convert_json_schema_to_db_schema(json_schema: dict) -> SchemaResponse:
    tables = []
    relationships = []
    metadata = SchemaMetadata(version="1.0", description=json_schema.get("title", "Converted from JSON Schema"))
    if json_schema.get("type") == "object" and "properties" in json_schema:
        columns = []
        for prop_name, prop in json_schema["properties"].items():
            col_type = prop.get("type", "string")
            columns.append(ColumnInfo(
                name=prop_name,
                type=col_type,
                nullable=not (prop_name in json_schema.get("required", [])),
                is_primary_key=False,
                is_foreign_key=False,
                unique=False
            ))
        tables.append(TableInfo(
            name=json_schema.get("title", "MainTable"),
            columns=columns,
            primary_keys=[],
            foreign_keys=[],
            indexes=[],
            description="Converted from JSON Schema"
        ))
    return SchemaResponse(tables=tables, relationships=relationships, metadata=metadata)

def fix_schema_columns(schema_data: dict) -> dict:
    """Fix schema columns by ensuring they have the 'type' field"""
    if "tables" in schema_data:
        for table in schema_data["tables"]:
            if "columns" in table:
                for column in table["columns"]:
                    # If column doesn't have 'type' but has other field names, infer type
                    if "type" not in column:
                        # Try to infer type from column name or set default
                        col_name = column.get("name", "").lower()
                        
                        # Primary key detection
                        if "id" in col_name and column.get("is_primary_key", False):
                            column["type"] = "INTEGER"
                        # Timestamp fields
                        elif any(keyword in col_name for keyword in ["created_at", "updated_at", "timestamp", "date"]):
                            column["type"] = "TIMESTAMP"
                        # Email fields
                        elif "email" in col_name:
                            column["type"] = "VARCHAR(255)"
                        # String fields
                        elif any(keyword in col_name for keyword in ["name", "title", "username", "first_name", "last_name"]):
                            column["type"] = "VARCHAR(255)"
                        # Text fields
                        elif any(keyword in col_name for keyword in ["description", "content", "body", "text", "message", "comment"]):
                            column["type"] = "TEXT"
                        # Numeric fields
                        elif any(keyword in col_name for keyword in ["price", "amount", "cost", "fee", "salary"]):
                            column["type"] = "DECIMAL(10,2)"
                        elif any(keyword in col_name for keyword in ["count", "quantity", "number", "age", "year"]):
                            column["type"] = "INTEGER"
                        # Boolean fields
                        elif any(keyword in col_name for keyword in ["active", "enabled", "verified", "confirmed", "deleted"]) or col_name.startswith("is_") or col_name.startswith("has_"):
                            column["type"] = "BOOLEAN"
                        # URL fields
                        elif any(keyword in col_name for keyword in ["url", "link", "website"]):
                            column["type"] = "TEXT"
                        # Phone fields
                        elif "phone" in col_name:
                            column["type"] = "VARCHAR(20)"
                        # Address fields
                        elif any(keyword in col_name for keyword in ["address", "street", "city", "state", "country", "zip"]):
                            column["type"] = "VARCHAR(255)"
                        # JSON/Object fields
                        elif any(keyword in col_name for keyword in ["json", "data", "metadata", "config", "settings"]):
                            column["type"] = "JSONB"
                        # UUID fields
                        elif "uuid" in col_name:
                            column["type"] = "UUID"
                        else:
                            # Default type based on common patterns
                            column["type"] = "VARCHAR(255)"
                        
                        logger.info(f"🔧 Inferred type '{column['type']}' for column '{column.get('name')}'")
                    else:
                        logger.info(f"✅ Column '{column.get('name')}' already has type '{column.get('type')}'")
    return schema_data

@app.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: Request):
    """Generate code from schema in specified format, auto-convert JSON Schema if detected"""
    try:
        body = await request.json()
        
        # Log the incoming request for debugging
        logger.info(f"📨 Incoming request keys: {list(body.keys())}")
        if "schema" in body:
            logger.info(f"📨 Schema structure: tables={len(body['schema'].get('tables', []))}")
            if body['schema'].get('tables'):
                first_table = body['schema']['tables'][0]
                logger.info(f"📨 First table columns: {[col.get('name') for col in first_table.get('columns', [])]}")
                if first_table.get('columns'):
                    first_col = first_table['columns'][0]
                    logger.info(f"📨 First column structure: {list(first_col.keys())}")
        
        # Fix schema columns by ensuring they have the 'type' field
        if "schema" in body:
            body["schema"] = fix_schema_columns(body["schema"])
            logger.info("🔧 Schema columns processed and types ensured")
        
        # If JSON Schema detected, convert
        if "schema" in body and is_json_schema(body["schema"]):
            logger.info("Detected JSON Schema, converting to database schema format.")
            converted_schema = convert_json_schema_to_db_schema(body["schema"])
            codegen_request = CodeGenerationRequest(
                schema=converted_schema,
                format=body.get("format"),
                options=body.get("options", {})
            )
        else:
            codegen_request = CodeGenerationRequest(**body)

        logger.info(f"Received generation request: format={codegen_request.format}, schema_tables={len(codegen_request.schema.tables)}")
        
        # Log the format change for debugging caching issues
        logger.info(f"🎯 Generating {codegen_request.format.value} code with {len(codegen_request.schema.tables)} tables")
        logger.info(f"🎯 Generation options: {codegen_request.options}")

        generated_code = await code_generator.generate_code(
            schema=codegen_request.schema,
            format=codegen_request.format,
            options=codegen_request.options
        )
        
        logger.info(f"✅ Successfully generated {len(generated_code.code)} characters of {codegen_request.format.value} code")

        # Send webhook notification for successful code generation
        webhook_data = {
            "user": getattr(codegen_request, 'user_id', 'anonymous'),
            "framework": codegen_request.format.value if hasattr(codegen_request.format, 'value') else str(codegen_request.format),
            "tables_count": len(codegen_request.schema.tables),
            "timestamp": datetime.now().isoformat()
        }
        await send_webhook_notification(webhook_data)

        # Create response with cache-busting headers
        response = CodeGenerationResponse(
            code=generated_code.code,
            format=codegen_request.format,
            generated_at=datetime.now(),
            metadata=generated_code.metadata
        )
        
        # Add cache-busting to metadata to ensure frontend doesn't cache
        response.metadata["cache_buster"] = str(uuid4())
        response.metadata["generation_timestamp"] = datetime.now().isoformat()
        
        return response

    except ValidationError as e:
        logger.error(f"❌ Validation error in /generate: {e}")
        logger.error(f"❌ Request validation details: {e.errors()}")
        
        # Enhanced debugging for column validation errors
        for error in e.errors():
            if 'tables' in error.get('loc', []) and 'columns' in error.get('loc', []):
                logger.error(f"❌ Column validation error: {error}")
                logger.error(f"❌ Error location: {error.get('loc')}")
                logger.error(f"❌ Error input: {error.get('input')}")
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Request validation failed",
                "errors": e.errors(),
                "help": "Each column must have a 'type' field. Common types: INTEGER, VARCHAR(255), TEXT, TIMESTAMP, BOOLEAN, DECIMAL"
            }
        )
    except CodeGenerationError as e:
        logger.error(f"Code generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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
            "table_count": len(parsed_request.schema.tables)
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
async def get_generation_stats(
    current_user: str = Depends(get_optional_user)
):
    """
    Get code generation statistics for authenticated user
    
    ✅ FIXED: Now filters by user_id to ensure data isolation
    """
    try:
        # Get real stats from database filtered by user
        from sqlalchemy import func, select
        
        async with db_service.get_session() as session:
            # Total generation jobs for this user
            total_jobs = await session.scalar(
                select(func.count(CodeGenerationJob.id))
                .where(CodeGenerationJob.user_id == current_user)
                .execution_options(prepared_statement_cache_size=0)
            ) or 0
            
            # Successful jobs for this user
            successful_jobs = await session.scalar(
                select(func.count(CodeGenerationJob.id))
                .where(CodeGenerationJob.user_id == current_user)
                .where(CodeGenerationJob.status == "completed")
                .execution_options(prepared_statement_cache_size=0)
            ) or 0
            
            # Jobs created today for this user
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            apis_today = await session.scalar(
                select(func.count(CodeGenerationJob.id))
                .where(CodeGenerationJob.user_id == current_user)
                .where(CodeGenerationJob.created_at >= today_start)
                .execution_options(prepared_statement_cache_size=0)
            ) or 0
            
            # Total generated files for this user
            templates_generated = await session.scalar(
                select(func.count(GeneratedCodeFile.id))
                .where(GeneratedCodeFile.user_id == current_user)
                .execution_options(prepared_statement_cache_size=0)
            ) or 0
            
            stats = {
                "total_apis": total_jobs,
                "apis_scaffolded": successful_jobs,
                "apis_today": apis_today,
                "templates_generated": templates_generated,
                "most_popular_framework": "FastAPI",  # Could be calculated from jobs
                "total_frameworks": 5,
                "generation_success_rate": round((successful_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0,
                "service_status": "healthy",
                "database_enabled": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Code generation stats for user {current_user}: {stats}")
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
