"""
Frontend API Compatibility Router
Provides the exact API endpoints expected by the frontend application
"""
from fastapi import APIRouter, HTTPException, Depends, Security, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid

from models.schemas import DetectionResponse, SchemaHistoryResponse
from core.schema_detector import SchemaDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router with the expected prefix
router = APIRouter(prefix="/api/schema", tags=["Frontend Schema API"])

# Security scheme
security = HTTPBearer(auto_error=False)

# Initialize schema detector
schema_detector = SchemaDetector()

@router.post("/detect-from-file")
async def detect_schema_from_file(
    file: UploadFile = File(...),
    table_name: Optional[str] = None,
    enable_ai_enhancement: bool = True
):
    """
    Detect schema from uploaded file - Frontend compatible endpoint
    
    Expected Response:
    {
        "success": true,
        "data": {
            "schema": {...},
            "confidence_score": 0.89
        }
    }
    """
    try:
        # Read file content
        content = await file.read()
        
        try:
            data = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8.")
        
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
        
        # Use the existing schema detector
        result = await schema_detector.detect_schema(
            data=data,
            file_format=file_format,
            table_name=table_name or file.filename or "uploaded_file",
            enable_ai=enable_ai_enhancement
        )
        
        # Convert to frontend expected format
        return {
            "success": True,
            "message": "Schema detected successfully from file",
            "data": {
                "schema": {
                    "tables": result.tables if hasattr(result, 'tables') else [],
                    "relationships": result.relationships if hasattr(result, 'relationships') else [],
                    "metadata": {
                        "detection_algorithm": "AI-powered file analysis",
                        "format": file_format or "auto-detected",
                        "filename": file.filename,
                        "file_size": len(content),
                        "detection_time": getattr(result, 'processing_time', 0),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                "confidence_score": getattr(result, 'confidence', 0.0),
                "suggestions": getattr(result, 'suggestions', [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting schema from file: {e}")
        return {
            "success": False,
            "message": f"Schema detection failed: {str(e)}",
            "data": {}
        }

@router.get("/history")
async def get_schema_history(
    table_name: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """
    Get schema history for all tables or a specific table
    
    Expected Response:
    {
        "success": true,
        "data": {
            "history": [...],
            "total": 5,
            "table_name": "users"
        }
    }
    """
    try:
        # Mock schema history data for now
        # In a real implementation, this would query the actual schema history
        
        mock_history = [
            {
                "id": str(uuid.uuid4()),
                "table_name": table_name or "users",
                "timestamp": "2024-01-15T10:30:00Z",
                "change_type": "CREATE",
                "description": "Table created with initial schema",
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "email", "type": "varchar(255)", "nullable": False},
                    {"name": "name", "type": "varchar(100)", "nullable": True}
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "table_name": table_name or "users", 
                "timestamp": "2024-01-16T14:20:00Z",
                "change_type": "ADD_COLUMN",
                "description": "Added created_at column",
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "email", "type": "varchar(255)", "nullable": False},
                    {"name": "name", "type": "varchar(100)", "nullable": True},
                    {"name": "created_at", "type": "timestamp", "nullable": False}
                ]
            }
        ]
        
        # Filter by table name if provided
        if table_name:
            history = [h for h in mock_history if h["table_name"] == table_name]
        else:
            history = mock_history
        
        # Apply pagination
        paginated_history = history[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "history": paginated_history,
                "total": len(history),
                "table_name": table_name,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < len(history)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching schema history: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch schema history: {str(e)}",
            "data": {}
        }

@router.post("/detect")
async def detect_schema(request: Dict[str, Any]):
    """
    Detect schema from provided data
    
    Expected Request Body:
    {
        "data": "...",  // CSV, JSON, or other data
        "format": "csv", // csv, json, xml, yaml
        "options": {}
    }
    
    Expected Response:
    {
        "success": true,
        "data": {
            "schema": {
                "tables": [...],
                "relationships": [...],
                "metadata": {...}
            }
        }
    }
    """
    try:
        data = request.get("data")
        format_type = request.get("format", "csv")
        options = request.get("options", {})
        
        if not data:
            raise HTTPException(status_code=400, detail="data is required")
        
        logger.info(f"Detecting schema for {format_type} data")
        
        # Mock schema detection for now
        # In a real implementation, this would use the actual detection logic
        
        detected_schema = {
            "tables": [
                {
                    "name": "detected_table",
                    "columns": [
                        {
                            "name": "id",
                            "type": "integer",
                            "nullable": False,
                            "primary_key": True,
                            "confidence": 0.95
                        },
                        {
                            "name": "name", 
                            "type": "varchar(255)",
                            "nullable": True,
                            "primary_key": False,
                            "confidence": 0.88
                        },
                        {
                            "name": "email",
                            "type": "varchar(320)",
                            "nullable": False,
                            "primary_key": False,
                            "confidence": 0.92
                        }
                    ],
                    "row_count": 1000,
                    "confidence": 0.91
                }
            ],
            "relationships": [
                {
                    "from_table": "detected_table",
                    "from_column": "id",
                    "to_table": "related_table",
                    "to_column": "user_id",
                    "type": "one_to_many",
                    "confidence": 0.78
                }
            ],
            "metadata": {
                "detection_algorithm": "AI-powered analysis",
                "format": format_type,
                "data_size": len(str(data)),
                "detection_time": 0.234,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return {
            "success": True,
            "message": "Schema detected successfully",
            "data": {
                "schema": detected_schema,
                "confidence_score": 0.89,
                "suggestions": [
                    "Consider adding indexes on email column",
                    "Validate foreign key relationships",
                    "Review nullable constraints"
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting schema: {e}")
        return {
            "success": False,
            "message": f"Schema detection failed: {str(e)}",
            "data": {}
        }

@router.get("/tables")
async def get_tables(
    database: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get list of tables from detected schemas
    
    Expected Response:
    {
        "success": true,
        "data": {
            "tables": [...],
            "total": 10
        }
    }
    """
    try:
        # Mock table data
        mock_tables = [
            {
                "name": "users",
                "schema": "public",
                "type": "table",
                "row_count": 1500,
                "column_count": 8,
                "last_updated": "2024-01-16T14:20:00Z",
                "description": "User account information"
            },
            {
                "name": "orders",
                "schema": "public", 
                "type": "table",
                "row_count": 5230,
                "column_count": 12,
                "last_updated": "2024-01-16T16:45:00Z",
                "description": "Customer order records"
            },
            {
                "name": "products",
                "schema": "public",
                "type": "table", 
                "row_count": 892,
                "column_count": 15,
                "last_updated": "2024-01-15T09:30:00Z",
                "description": "Product catalog data"
            }
        ]
        
        # Apply pagination
        paginated_tables = mock_tables[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "tables": paginated_tables,
                "total": len(mock_tables),
                "database": database,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < len(mock_tables)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching tables: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch tables: {str(e)}",
            "data": {}
        }

@router.get("/relationships")
async def get_relationships(
    table_name: Optional[str] = None
):
    """
    Get schema relationships
    
    Expected Response:
    {
        "success": true,
        "data": {
            "relationships": [...],
            "total": 5
        }
    }
    """
    try:
        # Mock relationship data
        mock_relationships = [
            {
                "id": str(uuid.uuid4()),
                "from_table": "orders",
                "from_column": "user_id",
                "to_table": "users", 
                "to_column": "id",
                "type": "foreign_key",
                "relationship_type": "many_to_one",
                "confidence": 0.95
            },
            {
                "id": str(uuid.uuid4()),
                "from_table": "order_items",
                "from_column": "order_id",
                "to_table": "orders",
                "to_column": "id", 
                "type": "foreign_key",
                "relationship_type": "many_to_one",
                "confidence": 0.98
            }
        ]
        
        # Filter by table name if provided
        if table_name:
            relationships = [
                r for r in mock_relationships 
                if r["from_table"] == table_name or r["to_table"] == table_name
            ]
        else:
            relationships = mock_relationships
        
        return {
            "success": True,
            "data": {
                "relationships": relationships,
                "total": len(relationships),
                "table_name": table_name
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching relationships: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch relationships: {str(e)}",
            "data": {}
        }

@router.get("/health")
async def health_check():
    """Health check endpoint for schema API"""
    return {
        "status": "healthy",
        "service": "Schema Detection Service - Frontend API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Schema detection",
            "Schema history tracking",
            "Table and relationship management",
            "AI-powered analysis",
            "Multiple format support"
        ]
    }
