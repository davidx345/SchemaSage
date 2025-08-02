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
