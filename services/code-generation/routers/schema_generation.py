"""
Schema Generation Router
Handles natural language to multiple code format generation
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from pydantic import BaseModel

from core.nl_schema_converter import NLSchemaConverter
from core.code_generator import CodeGenerator
from config import CodeGenFormat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schema", tags=["schema_generation"])

# Initialize components
nl_converter = NLSchemaConverter()
code_generator = CodeGenerator()


class SchemaGenerationRequest(BaseModel):
    """Request model for schema generation from natural language"""
    description: str
    options: Optional[Dict[str, Any]] = None


class MultiFormatResponse(BaseModel):
    """Response with multiple code formats"""
    sqlalchemy: str
    prisma: str
    typeorm: str
    django: str
    raw_sql: str
    generated_at: datetime
    description: str
    tables: list = []  # Add tables for visualization
    relationships: list = []  # Add relationships for visualization


@router.post("/generate", response_model=MultiFormatResponse)
async def generate_schema_multi_format(request: SchemaGenerationRequest):
    """
    Generate schema in multiple formats from natural language description
    
    This endpoint takes a natural language description and returns
    SQLAlchemy, Prisma, TypeORM, Django, and raw SQL code.
    """
    try:
        logger.info(f"Generating multi-format schema for: {request.description[:100]}...")
        
        # Step 1: Convert natural language to schema using our enhanced AI converter
        schema_response = nl_converter.convert_to_schema(
            request.description, 
            options=request.options or {}
        )
        
        if not schema_response:
            raise HTTPException(
                status_code=400,
                detail="Failed to generate schema from description"
            )
        
        # Step 2: Generate code in all required formats
        formats_to_generate = [
            (CodeGenFormat.SQLALCHEMY, 'sqlalchemy'),
            (CodeGenFormat.PRISMA, 'prisma'),
            (CodeGenFormat.TYPEORM, 'typeorm'),
            (CodeGenFormat.DJANGO_ORM, 'django'),
            (CodeGenFormat.SQL, 'raw_sql')
        ]
        
        generated_code = {}
        
        for format_enum, response_key in formats_to_generate:
            try:
                # Prepare options with description from request
                generation_options = (request.options or {}).copy()
                generation_options['description'] = request.description
                
                code_result = await code_generator.generate_code(
                    schema=schema_response,
                    format=format_enum,
                    options=generation_options
                )
                generated_code[response_key] = code_result.code
            except Exception as e:
                logger.warning(f"Failed to generate {response_key}: {e}")
                generated_code[response_key] = f"# Error generating {response_key}: {str(e)}"
        
        # Convert schema_response tables and relationships to dict for JSON serialization
        tables_data = []
        if hasattr(schema_response, 'tables'):
            for table in schema_response.tables:
                table_dict = {
                    "name": table.name,
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.type,
                            "nullable": col.nullable,
                            "is_primary_key": col.is_primary_key,
                            "is_foreign_key": getattr(col, 'is_foreign_key', False),
                            "default": col.default,
                            "unique": col.unique,
                            "description": col.description
                        }
                        for col in table.columns
                    ],
                    "primary_keys": table.primary_keys,
                    "foreign_keys": table.foreign_keys,
                    "description": table.description
                }
                tables_data.append(table_dict)
        
        relationships_data = []
        if hasattr(schema_response, 'relationships'):
            for rel in schema_response.relationships:
                rel_dict = {
                    "source_table": rel.source_table,
                    "source_column": rel.source_column,
                    "target_table": rel.target_table,
                    "target_column": rel.target_column,
                    "type": rel.type
                }
                relationships_data.append(rel_dict)
        
        return MultiFormatResponse(
            sqlalchemy=generated_code.get('sqlalchemy', ''),
            prisma=generated_code.get('prisma', ''),
            typeorm=generated_code.get('typeorm', ''),
            django=generated_code.get('django', ''),
            raw_sql=generated_code.get('raw_sql', ''),
            generated_at=datetime.now(),
            description=request.description,
            tables=tables_data,
            relationships=relationships_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-format schema generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema generation failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check for schema generation router"""
    return {
        "status": "healthy",
        "service": "Schema Generation Router",
        "endpoints": ["/generate"],
        "timestamp": datetime.now().isoformat()
    }