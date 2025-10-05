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
        schema_response = await nl_converter.convert_to_schema(
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
                code_result = await code_generator.generate_code(
                    schema=schema_response,
                    format=format_enum,
                    options=request.options or {}
                )
                generated_code[response_key] = code_result.code
            except Exception as e:
                logger.warning(f"Failed to generate {response_key}: {e}")
                generated_code[response_key] = f"# Error generating {response_key}: {str(e)}"
        
        return MultiFormatResponse(
            sqlalchemy=generated_code.get('sqlalchemy', ''),
            prisma=generated_code.get('prisma', ''),
            typeorm=generated_code.get('typeorm', ''),
            django=generated_code.get('django', ''),
            raw_sql=generated_code.get('raw_sql', ''),
            generated_at=datetime.now(),
            description=request.description
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