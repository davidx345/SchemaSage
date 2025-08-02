"""
Core Code Generator for SchemaSage
Handles generation of various code formats from database schemas
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from models.schemas import SchemaResponse, CodeGenFormat
from core.etl_code_generator.base import CodeGenerationError
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

@dataclass
class CodeGenerationResult:
    """Result of code generation operation"""
    code: str
    metadata: Dict[str, Any]
    format: CodeGenFormat
    generated_at: datetime


class CodeGenerator:
    """
    Main code generator that handles multiple output formats
    """
    
    def __init__(self):
        """Initialize the code generator with template environment"""
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Format mapping to template files
        self.format_templates = {
            CodeGenFormat.SQLALCHEMY: "sqlalchemy_models.py.jinja2",
            CodeGenFormat.SQL: "sql_ddl.sql.jinja2", 
            CodeGenFormat.JSON: "json_schema.json.jinja2",
            CodeGenFormat.PYTHON_DATACLASSES: "python_dataclasses.py.jinja2",
            CodeGenFormat.DBML: "dbml_schema.dbml.jinja2"
        }
        
        logger.info(f"CodeGenerator initialized with template directory: {self.template_dir}")
    
    async def generate_code(
        self,
        schema: SchemaResponse,
        format: CodeGenFormat,
        options: Optional[Dict[str, Any]] = None
    ) -> CodeGenerationResult:
        """
        Generate code from schema in specified format
        
        Args:
            schema: Database schema to generate from
            format: Output format for generated code
            options: Additional generation options
            
        Returns:
            CodeGenerationResult with generated code and metadata
            
        Raises:
            CodeGenerationError: If generation fails
        """
        try:
            logger.info(f"Generating {format.value} code for schema with {len(schema.tables)} tables")
            
            # Get template for format
            template_name = self.format_templates.get(format)
            if not template_name:
                raise CodeGenerationError(f"Unsupported format: {format.value}")
            
            # Load template
            try:
                template = self.env.get_template(template_name)
            except TemplateNotFound:
                raise CodeGenerationError(f"Template not found: {template_name}")
            
            # Prepare template context
            context = self._prepare_template_context(schema, options or {})
            
            # Generate code
            code = await self._render_template(template, context)
            
            # Prepare metadata
            metadata = {
                "format": format.value,
                "table_count": len(schema.tables),
                "column_count": sum(len(table.columns) for table in schema.tables),
                "relationship_count": len(schema.relationships) if schema.relationships else 0,
                "template_used": template_name,
                "generation_options": options or {},
                "schema_version": schema.metadata.version if schema.metadata else "1.0"
            }
            
            result = CodeGenerationResult(
                code=code,
                metadata=metadata,
                format=format,
                generated_at=datetime.now()
            )
            
            logger.info(f"Successfully generated {len(code)} characters of {format.value} code")
            return result
            
        except CodeGenerationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during code generation: {e}")
            raise CodeGenerationError(f"Code generation failed: {str(e)}") from e
    
    def _prepare_template_context(self, schema: SchemaResponse, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare context variables for template rendering
        
        Args:
            schema: Database schema
            options: Generation options
            
        Returns:
            Template context dictionary
        """
        context = {
            "schema": schema,
            "tables": schema.tables,
            "relationships": schema.relationships or [],
            "metadata": schema.metadata,
            "options": options,
            "generated_at": datetime.now(),
            "generator": "SchemaSage CodeGenerator"
        }
        
        # Add helper functions for templates
        context.update({
            "snake_to_camel": self._snake_to_camel,
            "camel_to_snake": self._camel_to_snake,
            "pluralize": self._pluralize,
            "singularize": self._singularize,
            "sql_type_to_python": self._sql_type_to_python,
            "get_primary_key_columns": self._get_primary_key_columns,
            "get_foreign_key_columns": self._get_foreign_key_columns
        })
        
        return context
    
    async def _render_template(self, template, context: Dict[str, Any]) -> str:
        """
        Render template asynchronously
        
        Args:
            template: Jinja2 template object
            context: Template context
            
        Returns:
            Rendered template as string
        """
        # Run template rendering in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, template.render, context)
    
    # Helper functions for templates
    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case to CamelCase"""
        components = snake_str.split('_')
        return ''.join(word.capitalize() for word in components)
    
    def _camel_to_snake(self, camel_str: str) -> str:
        """Convert CamelCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _pluralize(self, word: str) -> str:
        """Simple pluralization"""
        if word.endswith('y'):
            return word[:-1] + 'ies'
        elif word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        else:
            return word + 's'
    
    def _singularize(self, word: str) -> str:
        """Simple singularization"""
        if word.endswith('ies'):
            return word[:-3] + 'y'
        elif word.endswith(('ses', 'shes', 'ches', 'xes', 'zes')):
            return word[:-2]
        elif word.endswith('s') and not word.endswith('ss'):
            return word[:-1]
        else:
            return word
    
    def _sql_type_to_python(self, sql_type: str) -> str:
        """Map SQL types to Python types"""
        type_mapping = {
            'INTEGER': 'int',
            'INT': 'int',
            'BIGINT': 'int',
            'SMALLINT': 'int',
            'DECIMAL': 'float',
            'NUMERIC': 'float',
            'REAL': 'float',
            'FLOAT': 'float',
            'DOUBLE': 'float',
            'VARCHAR': 'str',
            'CHAR': 'str',
            'TEXT': 'str',
            'STRING': 'str',
            'BOOLEAN': 'bool',
            'BOOL': 'bool',
            'DATE': 'datetime.date',
            'TIME': 'datetime.time',
            'DATETIME': 'datetime.datetime',
            'TIMESTAMP': 'datetime.datetime',
            'UUID': 'str',
            'JSON': 'dict',
            'JSONB': 'dict'
        }
        
        sql_type_upper = sql_type.upper()
        return type_mapping.get(sql_type_upper, 'str')
    
    def _get_primary_key_columns(self, table) -> list:
        """Get primary key columns for a table"""
        return [col for col in table.columns if col.is_primary_key]
    
    def _get_foreign_key_columns(self, table) -> list:
        """Get foreign key columns for a table"""
        return [col for col in table.columns if col.is_foreign_key]


# Re-export the exception from etl_code_generator for compatibility
__all__ = ['CodeGenerator', 'CodeGenerationError', 'CodeGenerationResult']
