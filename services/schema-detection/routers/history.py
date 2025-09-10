"""
Schema History and Documentation API Routes

Routes for schema history tracking and documentation generation.
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import logging
import tempfile
import os

from models.schemas import (
    SchemaHistoryResponse, SchemaSnapshotModel, SchemaDiffResponse,
    DocumentationRequest, DocumentationResponse,
    DataCleaningRequest, DataCleaningResponse, CleaningSuggestion,
    ApplyCleaningRequest, ApplyCleaningResponse
)
from core.schema_history import SchemaHistory

logger = logging.getLogger(__name__)

# Router for history and documentation endpoints
router = APIRouter(tags=["history", "documentation"])

# Service instance
schema_history = SchemaHistory()


# Schema History Endpoints
@router.get("/history/{table_name}", response_model=SchemaHistoryResponse)
async def get_schema_history(table_name: str):
    """Get schema history for a table"""
    try:
        history = schema_history.get_history(table_name)
        return history
    
    except Exception as e:
        logger.error(f"Get schema history error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/history/snapshot")
async def create_schema_snapshot(snapshot: SchemaSnapshotModel):
    """Create a new schema snapshot"""
    try:
        snapshot_id = schema_history.create_snapshot(
            table_name=snapshot.table_name,
            schema_definition=snapshot.schema_definition,
            version=snapshot.version,
            description=snapshot.description,
            created_by=snapshot.created_by
        )
        return {"message": "Snapshot created successfully", "snapshot_id": snapshot_id}
    
    except Exception as e:
        logger.error(f"Create snapshot error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/diff/{table_name}")
async def get_schema_diff(
    table_name: str, 
    version1: str, 
    version2: str
) -> SchemaDiffResponse:
    """Get differences between two schema versions"""
    try:
        diff = schema_history.get_schema_diff(table_name, version1, version2)
        return diff
    
    except Exception as e:
        logger.error(f"Get schema diff error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Documentation Endpoints
@router.post("/documentation/generate", response_model=DocumentationResponse)
async def generate_documentation(request: DocumentationRequest):
    """Generate documentation for schemas"""
    try:
        # This would integrate with a documentation generator
        # For now, return a placeholder response
        doc_content = f"""
# Schema Documentation

## Tables: {', '.join(request.table_names)}
## Format: {request.format}
## Include Examples: {request.include_examples}

Generated on: {request.timestamp or 'now'}
"""
        
        return DocumentationResponse(
            content=doc_content,
            format=request.format,
            generated_at=request.timestamp,
            tables_included=request.table_names
        )
    
    except Exception as e:
        logger.error(f"Generate documentation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documentation/export")
async def export_documentation(request: DocumentationRequest):
    """Export documentation as file"""
    try:
        # Generate documentation content
        doc_response = await generate_documentation(request)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=f'.{request.format}', 
            delete=False
        ) as temp_file:
            if request.format == 'pdf':
                # For PDF, we'd need to convert the content
                # This is a placeholder implementation
                temp_file.write(doc_response.content)
            else:
                temp_file.write(doc_response.content)
            
            temp_file_path = temp_file.name
        
        # Return file
        return FileResponse(
            path=temp_file_path,
            filename=f"schema_documentation.{request.format}",
            media_type=f"application/{request.format}"
        )
    
    except Exception as e:
        logger.error(f"Export documentation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Data Cleaning Endpoints
@router.post("/cleaning/analyze", response_model=DataCleaningResponse)
async def analyze_data_quality(request: DataCleaningRequest):
    """Analyze data quality and suggest cleaning operations"""
    try:
        suggestions = []
        
        # Analyze the provided data sample
        if request.data_sample:
            # Check for common data quality issues
            for i, row in enumerate(request.data_sample[:100]):  # Limit analysis
                if isinstance(row, dict):
                    for col_name, value in row.items():
                        # Check for empty strings
                        if value == "":
                            suggestions.append(CleaningSuggestion(
                                issue_type="empty_string",
                                column_name=col_name,
                                row_index=i,
                                current_value=value,
                                suggested_value=None,
                                confidence=0.9,
                                description="Empty string found, consider replacing with NULL"
                            ))
                        
                        # Check for inconsistent casing
                        if isinstance(value, str) and value.lower() != value and value.upper() != value:
                            suggestions.append(CleaningSuggestion(
                                issue_type="inconsistent_casing",
                                column_name=col_name,
                                row_index=i,
                                current_value=value,
                                suggested_value=value.lower(),
                                confidence=0.7,
                                description="Inconsistent casing detected"
                            ))
        
        # Limit suggestions to avoid overwhelming response
        suggestions = suggestions[:50]
        
        return DataCleaningResponse(
            total_issues=len(suggestions),
            suggestions=suggestions,
            summary={
                "empty_strings": sum(1 for s in suggestions if s.issue_type == "empty_string"),
                "inconsistent_casing": sum(1 for s in suggestions if s.issue_type == "inconsistent_casing"),
                "analyzed_rows": min(100, len(request.data_sample) if request.data_sample else 0)
            }
        )
    
    except Exception as e:
        logger.error(f"Data quality analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cleaning/apply", response_model=ApplyCleaningResponse)
async def apply_cleaning_suggestions(request: ApplyCleaningRequest):
    """Apply selected cleaning suggestions to data"""
    try:
        cleaned_data = request.data.copy() if request.data else []
        applied_count = 0
        skipped_count = 0
        
        for suggestion_id in request.suggestion_ids:
            # Find the corresponding suggestion
            suggestion = None
            for s in request.suggestions:
                if s.issue_type == suggestion_id:  # Simplified matching
                    suggestion = s
                    break
            
            if suggestion and suggestion.row_index < len(cleaned_data):
                row = cleaned_data[suggestion.row_index]
                if isinstance(row, dict) and suggestion.column_name in row:
                    # Apply the cleaning suggestion
                    row[suggestion.column_name] = suggestion.suggested_value
                    applied_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        return ApplyCleaningResponse(
            cleaned_data=cleaned_data,
            applied_suggestions=applied_count,
            skipped_suggestions=skipped_count,
            summary={
                "total_rows": len(cleaned_data),
                "modified_rows": applied_count,
                "cleaning_success_rate": applied_count / (applied_count + skipped_count) if (applied_count + skipped_count) > 0 else 0
            }
        )
    
    except Exception as e:
        logger.error(f"Apply cleaning error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/versions")
async def get_all_versions():
    """Get all available schema versions across all tables"""
    try:
        versions = schema_history.get_all_versions()
        return {"versions": versions}
    
    except Exception as e:
        logger.error(f"Get versions error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/history/{table_name}/{version}")
async def delete_schema_version(table_name: str, version: str):
    """Delete a specific schema version"""
    try:
        success = schema_history.delete_version(table_name, version)
        if success:
            return {"message": f"Version {version} of table {table_name} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Version not found")
    
    except Exception as e:
        logger.error(f"Delete version error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/diagram/save")
async def save_schema_diagram(
    diagram_data: Dict[str, Any],
    project_id: Optional[str] = None,
    diagram_name: Optional[str] = None
):
    """Save schema diagram with layout and visual information"""
    try:
        from datetime import datetime
        import uuid
        
        diagram_id = str(uuid.uuid4())
        
        # Extract diagram information
        schema_data = diagram_data.get("schema", {})
        layout_data = diagram_data.get("layout", {})
        visual_settings = diagram_data.get("visual_settings", {})
        
        # Mock saving diagram
        saved_diagram = {
            "diagram_id": diagram_id,
            "project_id": project_id,
            "diagram_name": diagram_name or f"Schema Diagram {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "schema_data": schema_data,
            "layout": {
                "nodes": layout_data.get("nodes", []),
                "edges": layout_data.get("edges", []),
                "viewport": layout_data.get("viewport", {"x": 0, "y": 0, "zoom": 1}),
                "grid_settings": layout_data.get("grid_settings", {"enabled": True, "size": 20})
            },
            "visual_settings": {
                "theme": visual_settings.get("theme", "light"),
                "node_colors": visual_settings.get("node_colors", {}),
                "font_settings": visual_settings.get("font_settings", {"family": "Arial", "size": 12}),
                "relationship_styles": visual_settings.get("relationship_styles", {})
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "created_by": diagram_data.get("created_by", "system"),
                "version": "1.0",
                "table_count": len(schema_data.get("tables", [])),
                "relationship_count": len(schema_data.get("relationships", []))
            },
            "export_formats": ["png", "svg", "pdf", "json"],
            "sharing_settings": {
                "is_public": diagram_data.get("is_public", False),
                "permissions": diagram_data.get("permissions", [])
            }
        }
        
        return {
            "status": "saved",
            "diagram": saved_diagram,
            "message": f"Schema diagram '{saved_diagram['diagram_name']}' saved successfully",
            "diagram_url": f"/api/diagrams/{diagram_id}",
            "share_url": f"/api/diagrams/{diagram_id}/share" if saved_diagram["sharing_settings"]["is_public"] else None
        }
        
    except Exception as e:
        logger.error(f"Save diagram error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save schema diagram")


@router.get("/diagram/{diagram_id}")
async def get_schema_diagram(diagram_id: str):
    """Get saved schema diagram by ID"""
    try:
        # Mock retrieving diagram
        diagram = {
            "diagram_id": diagram_id,
            "diagram_name": "Sample Database Schema",
            "schema_data": {
                "tables": [
                    {
                        "name": "users",
                        "columns": [
                            {"name": "id", "type": "INTEGER", "primary_key": True},
                            {"name": "username", "type": "VARCHAR(255)", "nullable": False},
                            {"name": "email", "type": "VARCHAR(255)", "nullable": False}
                        ]
                    },
                    {
                        "name": "orders", 
                        "columns": [
                            {"name": "id", "type": "INTEGER", "primary_key": True},
                            {"name": "user_id", "type": "INTEGER", "foreign_key": "users.id"},
                            {"name": "total", "type": "DECIMAL(10,2)", "nullable": False}
                        ]
                    }
                ],
                "relationships": [
                    {
                        "from_table": "orders",
                        "from_column": "user_id",
                        "to_table": "users", 
                        "to_column": "id",
                        "relationship_type": "many_to_one"
                    }
                ]
            },
            "layout": {
                "nodes": [
                    {"id": "users", "position": {"x": 100, "y": 100}, "size": {"width": 200, "height": 150}},
                    {"id": "orders", "position": {"x": 400, "y": 100}, "size": {"width": 200, "height": 150}}
                ],
                "edges": [
                    {"id": "orders_users", "source": "orders", "target": "users", "type": "relationship"}
                ],
                "viewport": {"x": 0, "y": 0, "zoom": 1}
            },
            "visual_settings": {
                "theme": "light",
                "node_colors": {"table": "#e3f2fd", "primary_key": "#1976d2"},
                "font_settings": {"family": "Arial", "size": 12}
            },
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "version": "1.0",
                "table_count": 2,
                "relationship_count": 1
            }
        }
        
        return {
            "diagram": diagram,
            "status": "found"
        }
        
    except Exception as e:
        logger.error(f"Get diagram error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schema diagram")


@router.put("/diagram/{diagram_id}")
async def update_schema_diagram(
    diagram_id: str,
    updates: Dict[str, Any]
):
    """Update saved schema diagram"""
    try:
        # Mock updating diagram
        updated_fields = []
        
        if "diagram_name" in updates:
            updated_fields.append("diagram_name")
        if "layout" in updates:
            updated_fields.append("layout") 
        if "visual_settings" in updates:
            updated_fields.append("visual_settings")
        if "schema_data" in updates:
            updated_fields.append("schema_data")
        
        return {
            "status": "updated",
            "diagram_id": diagram_id,
            "updated_fields": updated_fields,
            "updated_at": "2024-01-15T10:30:00Z",
            "message": f"Diagram {diagram_id} updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Update diagram error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schema diagram")


@router.delete("/diagram/{diagram_id}")
async def delete_schema_diagram(diagram_id: str, confirm: bool = False):
    """Delete saved schema diagram"""
    try:
        if not confirm:
            return {
                "message": "Diagram deletion requires confirmation",
                "diagram_id": diagram_id,
                "warning": "This action cannot be undone",
                "confirmation_required": True
            }
        
        # Mock deletion
        return {
            "status": "deleted",
            "diagram_id": diagram_id,
            "deleted_at": "2024-01-15T10:30:00Z",
            "message": f"Diagram {diagram_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Delete diagram error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schema diagram")


@router.get("/diagrams/list")
async def list_schema_diagrams(
    project_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """List all saved schema diagrams"""
    try:
        # Mock diagram list
        diagrams = [
            {
                "diagram_id": "diag_001",
                "diagram_name": "Main Database Schema",
                "project_id": "proj_1",
                "created_at": "2024-01-15T10:30:00Z",
                "table_count": 5,
                "relationship_count": 8,
                "is_public": False
            },
            {
                "diagram_id": "diag_002", 
                "diagram_name": "User Management Schema",
                "project_id": "proj_1",
                "created_at": "2024-01-14T15:45:00Z",
                "table_count": 3,
                "relationship_count": 2,
                "is_public": True
            },
            {
                "diagram_id": "diag_003",
                "diagram_name": "Analytics Schema",
                "project_id": "proj_2", 
                "created_at": "2024-01-13T09:20:00Z",
                "table_count": 7,
                "relationship_count": 12,
                "is_public": False
            }
        ]
        
        # Filter by project if specified
        if project_id:
            diagrams = [d for d in diagrams if d["project_id"] == project_id]
        
        # Apply pagination
        total_count = len(diagrams)
        diagrams = diagrams[offset:offset + limit]
        
        return {
            "diagrams": diagrams,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"List diagrams error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list schema diagrams")
