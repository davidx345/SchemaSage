"""Schema Detection Microservice - Independent Service."""

from fastapi import FastAPI, HTTPException, Request, status, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional, List, Dict, Any
import logging
from contextlib import asynccontextmanager
import time
from datetime import datetime

# Import local modules
from models.schemas import (
    DetectionRequest, DetectionResponse, SchemaResponse, 
    SchemaSettings, ColumnStatistics, TableInfo, ColumnInfo, Relationship,
    RelationshipSuggestionRequest, RelationshipSuggestionResponse,
    CrossDatasetRelationshipRequest, CrossDatasetRelationshipResponse,
    TableLineageResponse, ColumnLineageResponse, ImpactAnalysisResponse,
    SchemaHistoryResponse, SchemaSnapshotModel, SchemaDiffResponse,
    DocumentationRequest, DocumentationResponse,
    DataCleaningRequest, DataCleaningResponse, CleaningSuggestion,
    ApplyCleaningRequest, ApplyCleaningResponse
)
from core.schema_detector import SchemaDetector, SchemaValidationError
from core.lineage import DataLineageGraph
from core.schema_history import SchemaHistory
from config import get_settings
from core.schema_detector import build_schema_inference_prompt
import json

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

# Relationship suggestion and cross-dataset inference endpoints
@app.post("/relationships/suggest", response_model=RelationshipSuggestionResponse)
async def suggest_relationships(request: RelationshipSuggestionRequest):
    """Suggest relationships between tables using AI/heuristics."""
    detector = SchemaDetector(request.settings)
    result = await detector.suggest_relationships(request.tables, context=request.context)
    return result

@app.post("/relationships/cross-dataset", response_model=CrossDatasetRelationshipResponse)
async def cross_dataset_relationships(request: CrossDatasetRelationshipRequest):
    """Infer relationships across multiple datasets."""
    detector = SchemaDetector(request.settings)
    result = await detector.cross_dataset_relationships(request.datasets, context=request.context)
    return result

# Lineage and impact analysis endpoints
@app.post("/lineage/table", response_model=TableLineageResponse)
async def get_table_lineage(
    schema: SchemaResponse = Body(...),
    table: str = Body(...),
    glossary: Optional[List[Dict[str, Any]]] = Body(None),
    context: Optional[Dict[str, Any]] = Body(None)
):
    graph = DataLineageGraph(schema.tables, schema.relationships, glossary=glossary, context=context)
    return graph.get_table_lineage(table)

@app.post("/lineage/column", response_model=ColumnLineageResponse)
async def get_column_lineage(
    schema: SchemaResponse = Body(...),
    table: str = Body(...),
    column: str = Body(...),
    glossary: Optional[List[Dict[str, Any]]] = Body(None),
    context: Optional[Dict[str, Any]] = Body(None)
):
    graph = DataLineageGraph(schema.tables, schema.relationships, glossary=glossary, context=context)
    return graph.get_column_lineage(table, column)

@app.post("/impact", response_model=ImpactAnalysisResponse)
async def impact_analysis(
    schema: SchemaResponse = Body(...),
    node_id: str = Body(...),
    glossary: Optional[List[Dict[str, Any]]] = Body(None),
    context: Optional[Dict[str, Any]] = Body(None)
):
    graph = DataLineageGraph(schema.tables, schema.relationships, glossary=glossary, context=context)
    return graph.impact_analysis(node_id)

# Schema versioning and history endpoints
# In-memory schema history for demo (replace with persistent storage in production)
schema_history = SchemaHistory()

@app.post("/history/add", response_model=SchemaSnapshotModel)
async def add_schema_snapshot(schema: SchemaResponse = Body(...)):
    """Add a new schema snapshot/version."""
    snap = schema_history.add_snapshot(schema)
    return SchemaSnapshotModel(id=snap.id, timestamp=snap.timestamp.isoformat(), schema=snap.schema)

@app.get("/history", response_model=SchemaHistoryResponse)
async def get_schema_history():
    """Get all schema versions/snapshots."""
    return SchemaHistoryResponse(history=[SchemaSnapshotModel(id=s.id, timestamp=s.timestamp.isoformat(), schema=s.schema) for s in schema_history.snapshots])

@app.get("/history/diff", response_model=SchemaDiffResponse)
async def diff_schema_versions(version_a: str, version_b: str):
    """Get diff between two schema versions."""
    diff = schema_history.diff(version_a, version_b)
    return SchemaDiffResponse(**diff)

# In-memory documentation store for demo (replace with persistent storage in production)
documentation_store = {}

@app.post("/documentation/generate", response_model=DocumentationResponse)
async def generate_documentation(request: DocumentationRequest):
    """Generate documentation for a schema/table/column/relationship/glossary."""
    object_type = (
        "table" if request.table else
        "column" if request.column else
        "relationship" if request.relationship else
        "glossary" if request.glossary_term else
        "schema"
    )
    object_id = request.table or request.column or str(request.relationship) or request.glossary_term or "schema"
    # Build a world-class prompt for documentation
    prompt = [
        "You are an expert technical writer and data architect.",
        f"Generate clear, concise, and business-aware documentation for the following {object_type}.",
        "Include:",
        "- A human-readable description of its purpose and business meaning.",
        "- Key fields, relationships, and usage examples if relevant.",
        "- Glossary/context matches (if provided).",
        "- Best practices, constraints, and any warnings.",
        "- Output only the documentation text (no markdown, no JSON, no explanations).",
        "",
    ]
    if request.glossary_term:
        prompt.append("Glossary term:\n" + json.dumps(request.glossary_term, indent=2))
    if request.context:
        prompt.append("Context:\n" + json.dumps(request.context, indent=2))
    if request.schema:
        if request.table:
            table = next((t for t in request.schema.tables if t.name == request.table), None)
            if table:
                prompt.append("Table definition:\n" + json.dumps(table.dict(), indent=2))
        elif request.column:
            for t in request.schema.tables:
                col = next((c for c in t.columns if c.name == request.column), None)
                if col:
                    prompt.append(f"Column definition in table {t.name}:\n" + json.dumps(col.dict(), indent=2))
        elif request.relationship:
            prompt.append("Relationship definition:\n" + json.dumps(request.relationship, indent=2))
        else:
            prompt.append("Schema definition:\n" + json.dumps(request.schema.dict(), indent=2))
    prompt.append("\nReturn only the documentation text. Do not include markdown, JSON, or explanations.")
    # TODO: Call LLM/AI here. For now, stub:
    doc = "\n".join(prompt)  # Replace with LLM call
    documentation_store[object_id] = {
        "object_type": object_type,
        "object_id": object_id,
        "documentation": doc,
        "generated": True,
        "last_updated": datetime.utcnow().isoformat(),
        "warnings": []
    }
    return DocumentationResponse(**documentation_store[object_id])

@app.get("/documentation/get", response_model=DocumentationResponse)
async def get_documentation(object_id: str):
    """Retrieve documentation for a schema/table/column/relationship/glossary."""
    doc = documentation_store.get(object_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    return DocumentationResponse(**doc)

@app.post("/documentation/update", response_model=DocumentationResponse)
async def update_documentation(object_id: str = Body(...), documentation: str = Body(...)):
    """Update (manual edit) documentation for a schema/table/column/relationship/glossary."""
    if object_id not in documentation_store:
        raise HTTPException(status_code=404, detail="Documentation not found")
    documentation_store[object_id]["documentation"] = documentation
    documentation_store[object_id]["generated"] = False
    documentation_store[object_id]["last_updated"] = datetime.utcnow().isoformat()
    return DocumentationResponse(**documentation_store[object_id])

@app.post("/data-cleaning/suggest", response_model=DataCleaningResponse)
async def suggest_data_cleaning(request: DataCleaningRequest):
    """Suggest data cleaning actions for a table and data sample."""
    suggestions = []
    data = request.data
    columns = request.columns or (data[0].keys() if data else [])
    for col in columns:
        values = [row.get(col) for row in data]
        nulls = sum(1 for v in values if v is None or v == "")
        if nulls > 0:
            suggestions.append(CleaningSuggestion(
                column=col,
                issue="Null or missing values",
                suggestion="Fill nulls with default or mean/mode",
                fix_code=f"UPDATE {request.table} SET {col} = <value> WHERE {col} IS NULL;",
                confidence=0.9
            ))
        if all(isinstance(v, str) and v.replace('.', '', 1).isdigit() for v in values if v not in (None, "")):
            suggestions.append(CleaningSuggestion(
                column=col,
                issue="Column values are strings but look like numbers",
                suggestion="Convert to numeric type",
                fix_code=f"ALTER TABLE {request.table} ALTER COLUMN {col} TYPE NUMERIC;",
                confidence=0.8
            ))
        if len(set(values)) < len(values):
            suggestions.append(CleaningSuggestion(
                column=col,
                issue="Duplicate values detected",
                suggestion="Deduplicate or add unique constraint",
                fix_code=f"-- Remove duplicates in {col}",
                confidence=0.7
            ))
    return DataCleaningResponse(table=request.table, suggestions=suggestions)

@app.post("/data-cleaning/apply", response_model=ApplyCleaningResponse)
async def apply_data_cleaning(request: ApplyCleaningRequest):
    """Apply cleaning actions to data (in-memory demo)."""
    return ApplyCleaningResponse(
        table=request.table,
        cleaned_data=request.data,
        applied_actions=request.actions,
        warnings=[]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
