"""
Code Generator Service
"""
from typing import Dict, List, Optional, Any
from jinja2 import Environment, FileSystemLoader, Template
import os
import json
import logging
from datetime import datetime
from ..config import settings, CodeGenFormat
from ..models.schemas import TableInfo, Relationship, SchemaResponse, ColumnStatistics
import httpx

logger = logging.getLogger(__name__)

class CodeGenerationError(Exception):
    """Custom exception for code generation errors."""
    def __init__(self, message: str, format: str, details: Optional[Dict] = None):
        self.message = message
        self.format = format
        self.details = details
        super().__init__(self.message)

class CodeGenerator:
    """Service for generating code from database schemas"""
    
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=True
        )
        # Add custom filters and globals
        self.env.filters['tojson'] = lambda x: json.dumps(x, ensure_ascii=False, indent=2)
        self.env.filters['sqlsafe'] = lambda x: x.replace('-', '_').replace(' ', '_')
        self.env.globals['now'] = datetime.utcnow
        logger.info("CodeGenerator initialized with templates from: %s", template_dir)

    def _get_sql_type(self, col_type: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Convert schema type to SQL type with options support."""
        type_mapping = {
            'Integer': 'INTEGER',
            'Float': 'FLOAT',
            'Boolean': 'BOOLEAN',
            'DateTime': 'TIMESTAMP',
            'JSON': 'JSONB' if options and options.get('use_jsonb', False) else 'JSON',
            'Text': 'TEXT',
            'String': 'VARCHAR(255)',
            'UUID': 'UUID'
        }
        
        # Handle VARCHAR with custom length
        if col_type.startswith('String') and options and options.get('varchar_length'):
            return f"VARCHAR({options['varchar_length']})"
            
        return type_mapping.get(col_type, 'TEXT')

    async def _prepare_sqlalchemy_relationships(self, schema: SchemaResponse, options: Optional[Dict[str, Any]] = None) -> Dict:
        """Prepare relationships for SQLAlchemy model generation."""
        table_relationships = {}
        for table in schema.tables:
            table_relationships[table.name] = {
                'outgoing': [],
                'incoming': []
            }
        
        for rel in schema.relationships:
            # Handle relationship naming options
            backref_suffix = options.get('backref_suffix', 's') if options else 's'
            use_plural = options.get('use_plural_relationships', True) if options else True
            
            backref_name = (
                f"{rel.target_table}{backref_suffix}" 
                if use_plural and rel.type in ['one-to-many', 'many-to-many']
                else rel.target_table
            )
            
            # Add outgoing relationship
            table_relationships[rel.source_table]['outgoing'].append({
                'target_table': rel.target_table,
                'source_column': rel.source_column,
                'target_column': rel.target_column,
                'type': rel.type,
                'backref_name': backref_name,
                'lazy': options.get('relationship_loading', 'select') if options else 'select'
            })
            
            # Add incoming relationship if bidirectional
            if options is None or options.get('bidirectional_relationships', True):
                table_relationships[rel.target_table]['incoming'].append({
                    'source_table': rel.source_table,
                    'source_column': rel.source_column,
                    'target_column': rel.target_column,
                    'type': rel.type,
                    'backref_name': f"{rel.source_table}{backref_suffix}" if use_plural else rel.source_table,
                    'lazy': options.get('relationship_loading', 'select') if options else 'select'
                })
        
        return table_relationships

    async def _prepare_sql_types(self, schema: SchemaResponse, options: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Convert schema types to SQL types with customization options."""
        sql_tables = []
        
        for table in schema.tables:
            sql_columns = []
            table_comments = []
            
            for col in table.columns:
                sql_type = self._get_sql_type(col.type, options)
                
                column_def = {
                    'name': col.name,
                    'type': sql_type,
                    'nullable': col.nullable,
                    'is_primary_key': col.is_primary_key,
                    'format': col.format,
                    'validation': col.validation
                }
                
                # Add column constraints based on validation
                if col.validation:
                    if col.validation == 'email':
                        column_def['check'] = "CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}$')"
                    elif col.validation == 'url':
                        column_def['check'] = "CHECK (url ~* '^https?://[^\\\\s/$.?#].[^\\\\s]*$')"
                
                sql_columns.append(column_def)
                
                # Add statistics as comments if enabled
                if options and options.get('include_statistics', True) and col.statistics:
                    comment = (f"Stats: {col.statistics.unique_count} unique values "
                             f"({col.statistics.unique_percentage:.1f}% unique), "
                             f"{col.statistics.null_count} nulls")
                    table_comments.append({
                        'type': 'COLUMN',
                        'column': col.name,
                        'text': comment
                    })
            
            # Generate indexes based on statistics if enabled
            indexes = []
            if options and options.get('generate_indexes', True):
                for col in table.columns:
                    if (col.statistics and 
                        col.statistics.unique_percentage > 80 and 
                        not col.is_primary_key):
                        indexes.append(
                            f"CREATE INDEX idx_{table.name}_{col.name} ON {table.name} ({col.name})"
                        )
            
            sql_tables.append({
                'name': table.name,
                'columns': sql_columns,
                'comments': table_comments,
                'indexes': indexes
            })
        
        return sql_tables

    async def generate_sqlalchemy_models(self, schema: SchemaResponse, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate SQLAlchemy model classes."""
        try:
            logger.debug("Preparing SQLAlchemy relationships")
            template = self.env.get_template('sqlalchemy_models.py.jinja2')
            relationships = await self._prepare_sqlalchemy_relationships(schema, options)
            
            # Prepare template context with options
            context = {
                'tables': schema.tables,
                'relationships': relationships,
                'metadata': schema.metadata,
                'use_mypy': options.get('use_mypy', True) if options else True,
                'use_validators': options.get('use_validators', True) if options else True,
                'base_class': options.get('base_class', 'Base') if options else 'Base'
            }
            
            logger.debug("Rendering SQLAlchemy template")
            code = await template.render_async(**context)
            logger.info("Successfully generated SQLAlchemy models")
            return code
        except Exception as e:
            logger.error("Failed to generate SQLAlchemy models", exc_info=True)
            raise CodeGenerationError(
                f"Failed to generate SQLAlchemy models: {str(e)}",
                "sqlalchemy",
                {"error": str(e)}
            )

    async def generate_sql_ddl(self, schema: SchemaResponse, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate SQL DDL statements."""
        try:
            logger.debug("Preparing SQL types")
            template = self.env.get_template('sql_ddl.sql.jinja2')
            sql_tables = await self._prepare_sql_types(schema, options)
            
            context = {
                'tables': sql_tables,
                'relationships': schema.relationships,
                'add_comments': options.get('add_comments', True) if options else True,
                'create_schema': options.get('create_schema', False) if options else False,
                'schema_name': options.get('schema_name', 'public') if options else 'public'
            }
            
            logger.debug("Rendering SQL DDL template")
            code = await template.render_async(**context)
            logger.info("Successfully generated SQL DDL")
            return code
        except Exception as e:
            logger.error("Failed to generate SQL DDL", exc_info=True)
            raise CodeGenerationError(
                f"Failed to generate SQL DDL: {str(e)}",
                "sql",
                {"error": str(e)}
            )

    async def generate_json_schema(self, schema: SchemaResponse, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate JSON Schema definition."""
        try:
            logger.debug("Rendering JSON Schema template")
            template = self.env.get_template('json_schema.json.jinja2')
            
            context = {
                'schema': schema,
                'draft_version': options.get('draft_version', '2020-12') if options else '2020-12',
                'add_examples': options.get('add_examples', True) if options else True,
                'include_stats': options.get('include_statistics', True) if options else True
            }
            
            code = await template.render_async(**context)
            logger.info("Successfully generated JSON Schema")
            return code
        except Exception as e:
            logger.error("Failed to generate JSON Schema", exc_info=True)
            raise CodeGenerationError(
                f"Failed to generate JSON schema: {str(e)}",
                "json",
                {"error": str(e)}
            )

    async def generate_python_dataclasses(self, schema: SchemaResponse, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate Python dataclasses."""
        try:
            logger.debug("Rendering Python dataclasses template")
            template = self.env.get_template('python_dataclasses.py.jinja2')
            context = {
                'schema': schema
            }
            code = await template.render_async(**context)
            logger.info("Successfully generated Python dataclasses")
            return code
        except Exception as e:
            logger.error("Failed to generate Python dataclasses", exc_info=True)
            raise CodeGenerationError(
                f"Failed to generate Python dataclasses: {str(e)}",
                "python_dataclasses",
                {"error": str(e)}
            )

    async def _call_gemini(self, prompt: str, api_key: Optional[str] = None) -> str:
        """Call Gemini API to generate code as a fallback."""
        api_key = api_key or settings.GEMINI_API_KEY
        if not api_key:
            raise CodeGenerationError("No Gemini API key configured.", "llm_fallback")
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, params=params, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            # Extract generated code from Gemini response
            try:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                raise CodeGenerationError("Gemini API response parsing failed.", "llm_fallback", {"response": result})

    async def generate_code(
        self, 
        schema: SchemaResponse, 
        format: CodeGenFormat,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate code in the specified format with customization options. Uses Gemini as fallback if enabled."""
        try:
            logger.info(f"Generating code in format: {format}")
            logger.debug(f"Schema contains {len(schema.tables)} tables")
            logger.debug(f"Using options: {options}")
            
            if not schema.tables:
                logger.error("Cannot generate code for empty schema")
                raise CodeGenerationError(
                    "Cannot generate code for empty schema",
                    format.value,
                    {"error": "No tables found in schema"}
                )

            # Try template-based generation first
            if format == CodeGenFormat.SQLALCHEMY:
                logger.debug("Generating SQLAlchemy models")
                return await self.generate_sqlalchemy_models(schema, options)
            elif format == CodeGenFormat.SQL:
                logger.debug("Generating SQL DDL")
                return await self.generate_sql_ddl(schema, options)
            elif format == CodeGenFormat.JSON:
                logger.debug("Generating JSON Schema")
                return await self.generate_json_schema(schema, options)
            elif format == CodeGenFormat.PYTHON_DATACLASSES:
                logger.debug("Generating Python dataclasses")
                return await self.generate_python_dataclasses(schema, options)
            elif format == CodeGenFormat.DBML:
                logger.warning("DBML format generation not implemented")
                raise NotImplementedError("DBML format generation not yet implemented")
            else:
                logger.error(f"Unsupported format: {format}")
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.warning(f"Template-based code generation failed: {e}")
            # Fallback to Gemini if enabled
            if settings.GEMINI_API_KEY:
                logger.info("Falling back to Gemini API for code generation.")
                prompt = self._build_llm_prompt(schema, format, options)
                return await self._call_gemini(prompt)
            if isinstance(e, (CodeGenerationError, NotImplementedError)):
                raise e
            raise CodeGenerationError(
                f"Code generation failed: {str(e)}",
                format.value,
                {"error": str(e)}
            )

    def _build_llm_prompt(self, schema: SchemaResponse, format: CodeGenFormat, options: Optional[Dict[str, Any]] = None) -> str:
        """Build a prompt for Gemini code generation fallback."""
        return (
            f"Generate {format.value} code for the following database schema. "
            f"Schema (JSON):\n{json.dumps(schema.dict(), indent=2)}"
        )
