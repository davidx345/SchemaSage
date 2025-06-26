"""Schema Detection Microservice - Independent Service."""

from fastapi import FastAPI, HTTPException, Request, status, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional
import logging
from contextlib import asynccontextmanager
import time

# Import local modules
from models.schemas import (
    DetectionRequest, DetectionResponse, SchemaResponse, 
    SchemaSettings, ColumnStatistics, TableInfo, ColumnInfo, Relationship
)
from core.schema_detector import SchemaDetector, SchemaValidationError
from config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Schema Detection Service starting up...")
    logger.info(f"Service version: {settings.VERSION}")
    logger.info(f"Max file size: {settings.MAX_FILE_SIZE} bytes")
    logger.info(f"Max sample rows: {settings.MAX_SAMPLE_ROWS}")
    yield
    # Shutdown
    logger.info("Schema Detection Service shutting down...")

app = FastAPI(
    title="Schema Detection Service",
    description="Advanced AI-powered schema detection and analysis",
    version=settings.VERSION,
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

@app.exception_handler(SchemaValidationError)
async def schema_validation_exception_handler(request: Request, exc: SchemaValidationError):
    """Handle schema validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": str(exc),
            "details": exc.details,
            "status": "error",
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error in Schema Detection Service: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "details": {"error": str(exc)},
            "status": "error",
        },
    )

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "schema-detection",
        "version": settings.VERSION,
        "features": {
            "json5_support": settings.ENABLE_JSON5,
            "relationship_detection": settings.ENABLE_RELATIONSHIP_DETECTION,
            "type_inference": settings.ENABLE_TYPE_INFERENCE
        },
        "limits": {
            "max_file_size": settings.MAX_FILE_SIZE,
            "max_sample_rows": settings.MAX_SAMPLE_ROWS,
            "processing_timeout": settings.PROCESSING_TIMEOUT
        }
    }

# Schema detection endpoints
@app.post("/detect", response_model=DetectionResponse)
async def detect_schema(request: DetectionRequest = Body(...)):
    """Detect schema from raw data"""
    try:
        start_time = time.time()
        
        # Validate input size
        if len(request.data) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Data size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Initialize detector with settings
        detector = SchemaDetector(request.settings)
        
        # Detect schema
        schema_result = await detector.detect_schema(
            data=request.data,
            format_hint=request.format_hint
        )
        
        # Create response
        schema_response = SchemaResponse(**schema_result)
        
        processing_time = time.time() - start_time
        logger.info(f"Schema detection completed in {processing_time:.2f}s")
        
        return DetectionResponse(
            schema=schema_response,
            success=True,
            message=f"Schema detected successfully in {processing_time:.2f}s"
        )
        
    except SchemaValidationError as e:
        logger.warning(f"Schema validation error: {e}")
        return DetectionResponse(
            schema=SchemaResponse(tables=[], relationships=[]),
            success=False,
            message=str(e),
            errors=[str(e)]
        )
    except Exception as e:
        logger.error(f"Unexpected error in schema detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema detection failed: {str(e)}"
        )

@app.post("/detect-file", response_model=DetectionResponse)
async def detect_schema_from_file(
    file: UploadFile = File(...),
    settings_param: Optional[str] = None
):
    """Detect schema from uploaded file"""
    try:
        # Validate file size
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Read file content
        file_content = await file.read()
        data_str = file_content.decode('utf-8')
        
        # Parse settings if provided
        detection_settings = None
        if settings_param:
            try:
                import json
                settings_dict = json.loads(settings_param)
                detection_settings = SchemaSettings(**settings_dict)
            except Exception as e:
                logger.warning(f"Invalid settings provided: {e}")
        
        # Create detection request
        request = DetectionRequest(
            data=data_str,
            settings=detection_settings,
            format_hint=None  # Auto-detect format
        )
        
        # Use the detect_schema endpoint
        return await detect_schema(request)
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid text file (UTF-8 encoded)"
        )
    except Exception as e:
        logger.error(f"File processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )

@app.get("/formats")
async def get_supported_formats():
    """Get supported input formats"""
    return {
        "formats": [
            {
                "name": "JSON",
                "description": "JavaScript Object Notation",
                "extensions": [".json"],
                "mime_types": ["application/json"],
                "supports_arrays": True,
                "supports_objects": True
            },
            {
                "name": "JSON5",
                "description": "JSON5 (Extended JSON)",
                "extensions": [".json5"],
                "mime_types": ["application/json5"],
                "supports_arrays": True,
                "supports_objects": True,
                "enabled": settings.ENABLE_JSON5
            },
            {
                "name": "CSV",
                "description": "Comma Separated Values",
                "extensions": [".csv"],
                "mime_types": ["text/csv"],
                "supports_arrays": True,
                "supports_objects": False
            },
            {
                "name": "TSV",
                "description": "Tab Separated Values",
                "extensions": [".tsv", ".txt"],
                "mime_types": ["text/tab-separated-values"],
                "supports_arrays": True,
                "supports_objects": False
            }
        ]
    }

@app.get("/settings")
async def get_default_settings():
    """Get default detection settings"""
    return SchemaSettings().dict()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Schema Detection Service",
        "status": "running",
        "version": settings.VERSION,
        "description": "Advanced AI-powered schema detection and analysis",
        "endpoints": {
            "detect": "POST /detect - Detect schema from raw data",
            "detect_file": "POST /detect-file - Detect schema from uploaded file",
            "formats": "GET /formats - Get supported input formats",
            "settings": "GET /settings - Get default detection settings", 
            "health": "GET /health - Service health check"
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
