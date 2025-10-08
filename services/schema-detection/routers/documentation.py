"""
Documentation API Routes

Routes specifically for schema documentation functionality to match frontend calls.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from models.schemas import DocumentationRequest, DocumentationResponse

logger = logging.getLogger(__name__)

# Router for documentation endpoints that match frontend expectations
router = APIRouter(prefix="/documentation", tags=["documentation"])


@router.get("/get")
async def get_documentation(
    object_id: str = Query(..., description="ID of the object to get documentation for"),
    table_name: Optional[str] = Query(None, description="Table name"),
    object_type: Optional[str] = Query("schema", description="Type of object (schema, table, column)")
):
    """Get documentation for a specific object (matches frontend GET call)"""
    try:
        # Mock documentation response that matches frontend expectations
        if object_id == "schema":
            documentation = {
                "object_type": "schema",
                "object_id": object_id,
                "documentation": f"""
# Schema Documentation

## Overview
This is the comprehensive documentation for the database schema.

## Tables
- **Users**: Stores user account information
- **Orders**: Manages customer orders and transactions
- **Products**: Product catalog and inventory

## Relationships
- Users have many Orders (one-to-many)
- Orders contain many Products (many-to-many through order_items)

## Data Types
- Primary keys: INTEGER AUTO_INCREMENT
- Text fields: VARCHAR with appropriate lengths
- Timestamps: DATETIME with timezone support

## Security
- All PII fields are encrypted at rest
- Access controls enforce least privilege principle
- Audit logging tracks all data modifications

## Generated on: {datetime.now().isoformat()}
""",
                "generated": True,
                "last_updated": datetime.now().isoformat(),
                "warnings": []
            }
        else:
            # Handle specific table or column documentation
            documentation = {
                "object_type": object_type,
                "object_id": object_id,
                "documentation": f"""
# {object_type.title()} Documentation: {object_id}

## Description
Documentation for {object_type} '{object_id}'

## Details
- Type: {object_type}
- ID: {object_id}
- Last Updated: {datetime.now().isoformat()}

## Usage
This {object_type} is used for managing data related to {object_id}.

## Generated automatically by SchemaSage
""",
                "generated": True,
                "last_updated": datetime.now().isoformat(),
                "warnings": []
            }
        
        return documentation
        
    except Exception as e:
        logger.error(f"Get documentation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get documentation")


@router.post("/generate", response_model=DocumentationResponse)
async def generate_documentation(request: DocumentationRequest):
    """Generate documentation (matches frontend POST call)"""
    try:
        logger.info(f"Generating documentation for tables: {request.table_names}")
        
        # Generate comprehensive documentation
        doc_content = f"""
# Schema Documentation

## Generated for Tables: {', '.join(request.table_names)}
## Format: {request.format}
## Include Examples: {request.include_examples}

Generated on: {request.timestamp or datetime.now().isoformat()}

## Tables Overview

"""
        
        # Add mock content for each table
        for table_name in request.table_names:
            doc_content += f"""
### Table: {table_name}

**Description**: Data table for managing {table_name} information

**Columns**:
- `id`: Primary key (INTEGER, AUTO_INCREMENT)
- `name`: Entity name (VARCHAR(255), NOT NULL)
- `email`: Contact email (VARCHAR(255), UNIQUE)
- `created_at`: Record creation timestamp (DATETIME)
- `updated_at`: Last modification timestamp (DATETIME)

**Relationships**:
- Related to other tables through foreign key constraints
- Supports referential integrity

**Indexes**:
- Primary key index on `id`
- Unique index on `email`
- Performance index on `created_at`

**Business Rules**:
- Email must be unique across all records
- Name field is required and cannot be empty
- Timestamps are automatically managed

---
"""
        
        doc_content += f"""
## Data Quality Guidelines

- All required fields must be populated
- Email addresses must follow valid format
- Foreign key relationships must be maintained
- Audit trails are maintained for all changes

## Security Considerations

- PII data is encrypted at rest
- Access controls limit data exposure
- Regular backups ensure data recovery
- Compliance with data protection regulations

## Maintenance Notes

- Regular index optimization recommended
- Data archiving policies in place
- Monitoring alerts configured
- Performance benchmarks established

---
*Documentation generated by SchemaSage on {datetime.now().isoformat()}*
"""
        
        return DocumentationResponse(
            content=doc_content,
            format=request.format,
            generated_at=datetime.now().isoformat(),
            tables_included=request.table_names,
            object_type="schema",
            object_id="schema_documentation",
            documentation=doc_content,
            generated=True,
            last_updated=datetime.now().isoformat(),
            warnings=[]
        )
        
    except Exception as e:
        logger.error(f"Generate documentation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate documentation")


@router.get("/health")
async def documentation_health():
    """Health check for documentation endpoints"""
    return {
        "status": "healthy",
        "service": "Documentation API",
        "endpoints": [
            "GET /documentation/get",
            "POST /documentation/generate"
        ],
        "timestamp": datetime.now().isoformat()
    }