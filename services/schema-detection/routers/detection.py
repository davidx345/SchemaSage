"""
Schema Detection API Routes

Core routes for schema detection functionality.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional, List, Dict, Any
import logging
import json
import httpx
import os
from datetime import datetime

from models.schemas import (
    DetectionRequest, DetectionResponse, SchemaResponse, 
    SchemaSettings, RelationshipSuggestionRequest, RelationshipSuggestionResponse,
    CrossDatasetRelationshipRequest, CrossDatasetRelationshipResponse
)
from core.schema_detector import SchemaDetector, SchemaValidationError

logger = logging.getLogger(__name__)

# Router for schema detection endpoints
router = APIRouter(prefix="/detect", tags=["detection"])

# WebSocket service URL for push notifications
WEBSOCKET_SERVICE_URL = os.getenv("WEBSOCKET_SERVICE_URL", "https://schemasage-websocket-realtime.herokuapp.com")

# Service instance
schema_detector = SchemaDetector()


async def send_webhook_notification(webhook_data: dict):
    """Send webhook notification to WebSocket service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{WEBSOCKET_SERVICE_URL}/webhooks/schema-generated", json=webhook_data)
            logger.info("Schema generation webhook sent successfully")
    except Exception as e:
        # Don't fail the main request if webhook fails
        logger.warning(f"Failed to send schema webhook: {e}")


@router.post("/schema", response_model=SchemaResponse)
async def detect_schema(request: DetectionRequest):
    """Detect schema from provided data"""
    try:
        # Configure detector settings
        if request.settings:
            schema_detector.configure_settings(request.settings)
        
        # Detect schema
        result = await schema_detector.detect_schema(
            data=request.data,
            file_format=request.file_format,
            table_name=request.table_name or "detected_table",
            enable_ai=request.enable_ai_enhancement
        )
        
        # Send webhook notification for successful schema detection
        webhook_data = {
            "user": getattr(request, 'user_id', 'anonymous'),
            "project": getattr(request, 'project_name', request.table_name or "unknown"),
            "schema_type": result.schema_type if hasattr(result, 'schema_type') else 'inferred',
            "timestamp": datetime.now().isoformat()
        }
        await send_webhook_notification(webhook_data)
        
        return result
    
    except SchemaValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Schema detection error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/file", response_model=SchemaResponse)
async def detect_schema_from_file(
    file: UploadFile = File(...),
    table_name: Optional[str] = None,
    enable_ai_enhancement: bool = True
):
    """Detect schema from uploaded file"""
    try:
        # Read file content
        content = await file.read()
        data = content.decode('utf-8')
        
        # Detect file format from filename
        file_format = None
        if file.filename:
            if file.filename.endswith('.json'):
                file_format = 'json'
            elif file.filename.endswith('.csv'):
                file_format = 'csv'
            elif file.filename.endswith('.tsv'):
                file_format = 'tsv'
            elif file.filename.endswith('.xml'):
                file_format = 'xml'
            elif file.filename.endswith(('.yml', '.yaml')):
                file_format = 'yaml'
        
        # Detect schema
        result = await schema_detector.detect_schema(
            data=data,
            file_format=file_format,
            table_name=table_name or file.filename or "uploaded_file",
            enable_ai=enable_ai_enhancement
        )
        
        # Send webhook notification for successful file schema detection
        webhook_data = {
            "user": "file_upload_user",  # You can add user tracking later
            "project": table_name or file.filename or "uploaded_file",
            "schema_type": f"file_{file_format or 'unknown'}",
            "timestamp": datetime.now().isoformat()
        }
        await send_webhook_notification(webhook_data)
        
        return result
    
    except SchemaValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8.")
    except Exception as e:
        logger.error(f"File schema detection error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/relationships", response_model=RelationshipSuggestionResponse)
async def suggest_relationships(request: RelationshipSuggestionRequest):
    """Suggest relationships between tables"""
    try:
        result = await schema_detector.suggest_relationships(
            tables=request.tables,
            enable_ai=request.enable_ai_enhancement
        )
        return result
    
    except Exception as e:
        logger.error(f"Relationship suggestion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cross-dataset", response_model=CrossDatasetRelationshipResponse)
async def analyze_cross_dataset_relationships(request: CrossDatasetRelationshipRequest):
    """Analyze relationships across multiple datasets"""
    try:
        result = await schema_detector.analyze_cross_dataset_relationships(
            datasets=request.datasets
        )
        return result
    
    except Exception as e:
        logger.error(f"Cross-dataset analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Additional route to match frontend expectation
@router.post("/relationships/cross-dataset", response_model=CrossDatasetRelationshipResponse)
async def analyze_cross_dataset_relationships_alt(request: CrossDatasetRelationshipRequest):
    """Analyze relationships across multiple datasets (alternative endpoint for frontend compatibility)"""
    return await analyze_cross_dataset_relationships(request)


@router.get("/settings")
async def get_detection_settings():
    """Get current detection settings"""
    return schema_detector.settings


@router.post("/settings")
async def update_detection_settings(settings: SchemaSettings):
    """Update detection settings"""
    try:
        schema_detector.configure_settings(settings)
        return {"message": "Settings updated successfully", "settings": settings}
    
    except Exception as e:
        logger.error(f"Settings update error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_detection_stats():
    """Get schema detection statistics for WebSocket consumption"""
    try:
        # In production, these would come from actual database queries
        # For now, providing realistic mock data that matches WebSocket expectations
        stats = {
            "total_schemas": 156,  # Total schemas detected/analyzed
            "schemas_generated": 89,  # Schemas successfully generated
            "schemas_today": 23,
            "most_common_format": "JSON",
            "ai_enhanced_schemas": 89,
            "detection_accuracy": 94.5,
            "files_processed": 203,
            "relationships_detected": 67,
            "service_status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting detection stats: {e}")
        # Return safe defaults even on error
        return {
            "total_schemas": 0,
            "schemas_generated": 0,
            "schemas_today": 0,
            "most_common_format": "JSON",
            "ai_enhanced_schemas": 0,
            "detection_accuracy": 0,
            "files_processed": 0,
            "relationships_detected": 0,
            "service_status": "error",
            "timestamp": datetime.now().isoformat()
        }
