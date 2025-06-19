"""
Code Generation Microservice
Generates code from database schemas in various formats
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from contextlib import asynccontextmanager

from config import settings, CodeGenFormat
from models.schemas import (
    CodeGenerationRequest, CodeGenerationResponse, ApiHealthResponse, ErrorResponse
)
from core.code_generator import CodeGenerator, CodeGenerationError

logger = logging.getLogger(__name__)

# Service instance
code_generator = CodeGenerator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Code Generation Service starting up...")
    logger.info(f"Templates loaded from: {settings.TEMPLATE_DIR}")
    logger.info(f"AI enhancement available: {settings.is_ai_enhanced()}")
    yield
    # Shutdown
    logger.info("Code Generation Service shutting down...")

app = FastAPI(
    title="Code Generation Service",
    description="Microservice for generating code from database schemas",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    import os
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
        logger.info(f"Generating {request.format} code for schema with {len(request.schema.tables)} tables")
        
        generated_code = await code_generator.generate_code(
            schema=request.schema,
            format=request.format,
            options=request.options
        )
        
        return CodeGenerationResponse(
            code=generated_code,
            format=request.format,
            metadata={
                "table_count": len(request.schema.tables),
                "relationship_count": len(request.schema.relationships),
                "generation_options": request.options or {}
            }
        )
        
    except CodeGenerationError as e:
        logger.error(f"Code generation failed: {e.message}")
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in code generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/generate/{format}", response_model=CodeGenerationResponse)
async def generate_code_format(format: CodeGenFormat, request: dict):
    """Generate code in specific format (alternative endpoint)"""
    try:
        # Convert dict to proper request model
        generation_request = CodeGenerationRequest(
            schema=request["schema"],
            format=format,
            options=request.get("options")
        )
        
        return await generate_code(generation_request)
        
    except Exception as e:
        logger.error(f"Error in format-specific generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        CodeGenFormat.SQL: "SQL DDL statements for database creation",
        CodeGenFormat.JSON: "JSON Schema definitions",
        CodeGenFormat.PYTHON_DATACLASSES: "Python dataclass definitions",
        CodeGenFormat.DBML: "Database Markup Language (DBML) schema"
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
            "base_class": {"type": "string", "default": "Base", "description": "Base class name"},
            "relationship_loading": {"type": "string", "default": "select", "description": "SQLAlchemy relationship loading strategy"},
            "bidirectional_relationships": {"type": "boolean", "default": True, "description": "Generate bidirectional relationships"}
        },
        CodeGenFormat.SQL: {
            "add_comments": {"type": "boolean", "default": True, "description": "Add comments to SQL"},
            "create_schema": {"type": "boolean", "default": False, "description": "Include schema creation"},
            "schema_name": {"type": "string", "default": "public", "description": "Schema name"},
            "generate_indexes": {"type": "boolean", "default": True, "description": "Generate indexes based on statistics"},
            "use_jsonb": {"type": "boolean", "default": False, "description": "Use JSONB instead of JSON for PostgreSQL"}
        },
        CodeGenFormat.JSON: {
            "draft_version": {"type": "string", "default": "2020-12", "description": "JSON Schema draft version"},
            "add_examples": {"type": "boolean", "default": True, "description": "Include example values"}
        },
        CodeGenFormat.PYTHON_DATACLASSES: {
            "use_typing": {"type": "boolean", "default": True, "description": "Include typing annotations"}
        }
    }
    
    result = common_options.copy()
    result.update(format_specific.get(format, {}))
    return result

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Code Generation Service",
        "status": "running",
        "version": settings.SERVICE_VERSION,
        "endpoints": {
            "generate": "POST /generate",
            "generate_format": "POST /generate/{format}",
            "formats": "GET /formats",
            "format_options": "GET /options/{format}",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
