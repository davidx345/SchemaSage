"""
Code Generation Microservice
Generates code from database schemas in various formats
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Dict, Any, Optional, List
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import os

from config import settings, CodeGenFormat
from models.schemas import (
    CodeGenerationRequest, CodeGenerationResponse, ApiHealthResponse, ErrorResponse
)
from core.code_generator import CodeGenerator, CodeGenerationError
from core.nl_schema_converter import NLSchemaConverter
from core.erd_generator import ERDGenerator
from core.api_scaffold_generator import APIScaffoldGenerator
from core.data_quality_analyzer import DataQualityAnalyzer
from core.data_cleaning_service import DataCleaningService
from core.ai_schema_critic import AISchemacritic

# Import modular components
from core.schema_merger import SchemaMerger
from core.schema_version_control import SchemaVersionControl
from core.performance_monitor import PerformanceMonitor
from core.security_compliance import SecurityComplianceManager
from core.real_time_collaboration import CollaborationManager
from core.enterprise_integration import EnterpriseIntegrationHub
from core.workflow_automation import WorkflowEngine
from core.etl_code_generator import ETLCodeGenerator
from core.etl_pipeline_builder import ETLPipelineBuilder
from core.vector_intelligence import VectorIntelligenceEngine
from core.schema_drift_detection import SchemaDriftDetector

# Initialize core components
code_generator = CodeGenerator()
nl_converter = NLSchemaConverter()
erd_generator = ERDGenerator()
api_scaffold_generator = APIScaffoldGenerator()
data_quality_analyzer = DataQualityAnalyzer()
data_cleaning_service = DataCleaningService()
ai_schema_critic = AISchemacritic()

# Initialize modular components
schema_merger = SchemaMerger()
schema_version_control = SchemaVersionControl("./schema_versions")
performance_monitor = PerformanceMonitor()
security_manager = SecurityComplianceManager()
collaboration_manager = CollaborationManager()
integration_hub = EnterpriseIntegrationHub()
workflow_engine = WorkflowEngine()
etl_generator = ETLCodeGenerator()
etl_pipeline_builder = ETLPipelineBuilder()
vector_intelligence = VectorIntelligenceEngine()
drift_detector = SchemaDriftDetector()

logger = logging.getLogger(__name__)

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
            code=generated_code.code,
            format=request.format,
            generated_at=datetime.now(),
            metadata=generated_code.metadata
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

@app.post("/generate-from-description")
async def generate_from_natural_language(
    description: str,
    format: CodeGenFormat,
    options: Optional[Dict[str, Any]] = None
):
    """Generate code from natural language description"""
    try:
        # Convert natural language to schema
        schema_response = await nl_converter.convert_to_schema(description)
        
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
        schema_response = await nl_converter.convert_to_schema(
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
            "base_class": {"type": "string", "default": "Base", "description": "Base class name"}
        },
        CodeGenFormat.SQL: {
            "dialect": {"type": "string", "default": "postgresql", "description": "SQL dialect"},
            "include_indexes": {"type": "boolean", "default": True, "description": "Include index definitions"}
        },
        CodeGenFormat.JSON: {
            "format": {"type": "string", "default": "draft-07", "description": "JSON Schema version"}
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
            "/options/{format}"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
