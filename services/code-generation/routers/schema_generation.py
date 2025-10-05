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
            (CodeGenFormat.SQL, 'raw_sql'),
            (CodeGenFormat.DJANGO_ORM, 'django')
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
        
        # Step 3: Generate Prisma and TypeORM manually (if not in CodeGenFormat enum)
        try:
            prisma_code = await _generate_prisma_from_schema(schema_response)
            generated_code['prisma'] = prisma_code
        except Exception as e:
            logger.warning(f"Failed to generate Prisma: {e}")
            generated_code['prisma'] = f"// Error generating Prisma: {str(e)}"
        
        try:
            typeorm_code = await _generate_typeorm_from_schema(schema_response)
            generated_code['typeorm'] = typeorm_code
        except Exception as e:
            logger.warning(f"Failed to generate TypeORM: {e}")
            generated_code['typeorm'] = f"// Error generating TypeORM: {str(e)}"
        
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


async def _generate_prisma_from_schema(schema_response) -> str:
    """Generate Prisma schema from schema response"""
    prisma_code = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

"""
    
    # Generate models for each table
    for table in schema_response.tables:
        model_name = _to_pascal_case(table.name)
        prisma_code += f"model {model_name} {{\n"
        
        # Generate fields
        for column in table.columns:
            field_name = column.name
            field_type = _map_to_prisma_type(column.type)
            
            field_line = f"  {field_name} {field_type}"
            
            # Add modifiers
            if column.is_primary_key:
                field_line += " @id"
                if "id" in column.name.lower() and "int" in column.type.lower():
                    field_line += " @default(autoincrement())"
            
            if not column.nullable and not column.is_primary_key:
                # Field is already non-nullable by default in Prisma
                pass
            elif column.nullable:
                field_line += "?"
            
            if column.unique:
                field_line += " @unique"
            
            prisma_code += field_line + "\n"
        
        prisma_code += f"\n  @@map(\"{table.name}\")\n"
        prisma_code += "}\n\n"
    
    return prisma_code


async def _generate_typeorm_from_schema(schema_response) -> str:
    """Generate TypeORM entities from schema response"""
    typeorm_code = """import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, OneToMany, ManyToOne, JoinColumn } from 'typeorm';

"""
    
    # Generate entities for each table
    for table in schema_response.tables:
        class_name = _to_pascal_case(table.name)
        typeorm_code += f"@Entity('{table.name}')\n"
        typeorm_code += f"export class {class_name} {{\n"
        
        # Generate columns
        for column in table.columns:
            field_name = column.name
            field_type = _map_to_typescript_type(column.type)
            
            if column.is_primary_key and "id" in column.name.lower():
                typeorm_code += f"  @PrimaryGeneratedColumn()\n"
            else:
                column_options = []
                if column.type:
                    ts_type_info = _get_typeorm_column_info(column.type)
                    if ts_type_info:
                        column_options.append(ts_type_info)
                
                if column.unique:
                    column_options.append("unique: true")
                
                if not column.nullable:
                    column_options.append("nullable: false")
                
                options_str = "{ " + ", ".join(column_options) + " }" if column_options else ""
                typeorm_code += f"  @Column({options_str})\n"
            
            nullable_modifier = "?" if column.nullable else ""
            typeorm_code += f"  {field_name}{nullable_modifier}: {field_type};\n\n"
        
        typeorm_code += "}\n\n"
    
    return typeorm_code


def _to_pascal_case(text: str) -> str:
    """Convert text to PascalCase"""
    return ''.join(word.capitalize() for word in text.replace('_', ' ').replace('-', ' ').split())


def _map_to_prisma_type(sql_type: str) -> str:
    """Map SQL types to Prisma types"""
    type_map = {
        'integer': 'Int',
        'bigint': 'BigInt',
        'varchar': 'String',
        'text': 'String',
        'boolean': 'Boolean',
        'timestamp': 'DateTime',
        'date': 'DateTime',
        'decimal': 'Decimal',
        'float': 'Float',
        'double': 'Float'
    }
    
    sql_type_lower = sql_type.lower()
    for sql_key, prisma_type in type_map.items():
        if sql_key in sql_type_lower:
            return prisma_type
    
    return 'String'  # Default fallback


def _map_to_typescript_type(sql_type: str) -> str:
    """Map SQL types to TypeScript types"""
    type_map = {
        'integer': 'number',
        'bigint': 'number',
        'varchar': 'string',
        'text': 'string',
        'boolean': 'boolean',
        'timestamp': 'Date',
        'date': 'Date',
        'decimal': 'number',
        'float': 'number',
        'double': 'number'
    }
    
    sql_type_lower = sql_type.lower()
    for sql_key, ts_type in type_map.items():
        if sql_key in sql_type_lower:
            return ts_type
    
    return 'string'  # Default fallback


def _get_typeorm_column_info(sql_type: str) -> str:
    """Get TypeORM column type information"""
    type_map = {
        'varchar': 'type: "varchar"',
        'text': 'type: "text"',
        'integer': 'type: "int"',
        'bigint': 'type: "bigint"',
        'boolean': 'type: "boolean"',
        'timestamp': 'type: "timestamp"',
        'date': 'type: "date"',
        'decimal': 'type: "decimal"',
        'float': 'type: "float"'
    }
    
    sql_type_lower = sql_type.lower()
    for sql_key, typeorm_info in type_map.items():
        if sql_key in sql_type_lower:
            return typeorm_info
    
    return 'type: "varchar"'  # Default fallback


@router.get("/health")
async def health_check():
    """Health check for schema generation router"""
    return {
        "status": "healthy",
        "service": "Schema Generation Router",
        "endpoints": ["/generate"],
        "timestamp": datetime.now().isoformat()
    }