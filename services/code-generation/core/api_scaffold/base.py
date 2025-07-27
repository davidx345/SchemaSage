"""
Base classes and utilities for API scaffolding
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class APIFramework(Enum):
    """Supported API frameworks"""
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO_REST = "django_rest"
    EXPRESS = "express"
    SPRING_BOOT = "spring_boot"
    ASPNET_CORE = "aspnet_core"

class ComponentType(Enum):
    """Types of API components"""
    MODEL = "model"
    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    ROUTE = "route"
    MIDDLEWARE = "middleware"
    VALIDATOR = "validator"
    SERIALIZER = "serializer"
    TEST = "test"
    CONFIG = "config"
    DOCUMENTATION = "documentation"

@dataclass
class APIComponent:
    """Represents a generated API component"""
    name: str
    component_type: ComponentType
    framework: APIFramework
    content: str
    file_path: str
    dependencies: List[str]
    imports: List[str]
    metadata: Dict[str, Any]

@dataclass
class APIScaffoldResult:
    """Result of API scaffolding generation"""
    framework: APIFramework
    components: List[APIComponent]
    project_structure: Dict[str, Any]
    package_dependencies: List[str]
    configuration_files: List[APIComponent]
    documentation: Optional[APIComponent]
    total_files: int
    estimated_loc: int

class TypeMapper:
    """Maps SQL types to programming language types"""
    
    def __init__(self):
        self.sql_to_python = {
            'int': 'int',
            'integer': 'int',
            'bigint': 'int',
            'smallint': 'int',
            'tinyint': 'int',
            'decimal': 'float',
            'numeric': 'float',
            'float': 'float',
            'double': 'float',
            'real': 'float',
            'varchar': 'str',
            'char': 'str',
            'text': 'str',
            'string': 'str',
            'boolean': 'bool',
            'bool': 'bool',
            'date': 'datetime.date',
            'datetime': 'datetime.datetime',
            'timestamp': 'datetime.datetime',
            'time': 'datetime.time',
            'json': 'dict',
            'jsonb': 'dict',
            'uuid': 'uuid.UUID',
            'binary': 'bytes',
            'blob': 'bytes'
        }
        
        self.sql_to_typescript = {
            'int': 'number',
            'integer': 'number',
            'bigint': 'number',
            'smallint': 'number',
            'tinyint': 'number',
            'decimal': 'number',
            'numeric': 'number',
            'float': 'number',
            'double': 'number',
            'real': 'number',
            'varchar': 'string',
            'char': 'string',
            'text': 'string',
            'string': 'string',
            'boolean': 'boolean',
            'bool': 'boolean',
            'date': 'Date',
            'datetime': 'Date',
            'timestamp': 'Date',
            'time': 'string',
            'json': 'object',
            'jsonb': 'object',
            'uuid': 'string',
            'binary': 'Buffer',
            'blob': 'Buffer'
        }
        
        self.sql_to_java = {
            'int': 'Integer',
            'integer': 'Integer',
            'bigint': 'Long',
            'smallint': 'Short',
            'tinyint': 'Byte',
            'decimal': 'BigDecimal',
            'numeric': 'BigDecimal',
            'float': 'Float',
            'double': 'Double',
            'real': 'Float',
            'varchar': 'String',
            'char': 'String',
            'text': 'String',
            'string': 'String',
            'boolean': 'Boolean',
            'bool': 'Boolean',
            'date': 'LocalDate',
            'datetime': 'LocalDateTime',
            'timestamp': 'LocalDateTime',
            'time': 'LocalTime',
            'json': 'Map<String, Object>',
            'jsonb': 'Map<String, Object>',
            'uuid': 'UUID',
            'binary': 'byte[]',
            'blob': 'byte[]'
        }
        
        self.sql_to_csharp = {
            'int': 'int',
            'integer': 'int',
            'bigint': 'long',
            'smallint': 'short',
            'tinyint': 'byte',
            'decimal': 'decimal',
            'numeric': 'decimal',
            'float': 'float',
            'double': 'double',
            'real': 'float',
            'varchar': 'string',
            'char': 'string',
            'text': 'string',
            'string': 'string',
            'boolean': 'bool',
            'bool': 'bool',
            'date': 'DateTime',
            'datetime': 'DateTime',
            'timestamp': 'DateTime',
            'time': 'TimeSpan',
            'json': 'object',
            'jsonb': 'object',
            'uuid': 'Guid',
            'binary': 'byte[]',
            'blob': 'byte[]'
        }
    
    def get_python_type(self, sql_type: str) -> str:
        """Map SQL type to Python type"""
        base_type = sql_type.lower().split('(')[0]
        return self.sql_to_python.get(base_type, 'str')
    
    def get_typescript_type(self, sql_type: str) -> str:
        """Map SQL type to TypeScript type"""
        base_type = sql_type.lower().split('(')[0]
        return self.sql_to_typescript.get(base_type, 'string')
    
    def get_java_type(self, sql_type: str) -> str:
        """Map SQL type to Java type"""
        base_type = sql_type.lower().split('(')[0]
        return self.sql_to_java.get(base_type, 'String')
    
    def get_csharp_type(self, sql_type: str) -> str:
        """Map SQL type to C# type"""
        base_type = sql_type.lower().split('(')[0]
        return self.sql_to_csharp.get(base_type, 'string')

class CodeTemplateEngine:
    """Simple template engine for code generation"""
    
    @staticmethod
    def render_template(template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables"""
        result = template
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, (list, dict)):
                # For complex types, convert to string representation
                value = str(value)
            result = result.replace(placeholder, str(value))
        
        return result
    
    @staticmethod
    def generate_imports(imports: List[str]) -> str:
        """Generate import statements"""
        return '\n'.join(f"import {imp}" for imp in sorted(set(imports)))
    
    @staticmethod
    def generate_class_name(table_name: str, suffix: str = "") -> str:
        """Generate class name from table name"""
        # Convert snake_case to PascalCase
        words = table_name.replace('-', '_').split('_')
        class_name = ''.join(word.capitalize() for word in words)
        return f"{class_name}{suffix}"
    
    @staticmethod
    def generate_variable_name(table_name: str) -> str:
        """Generate variable name from table name"""
        # Convert to camelCase
        words = table_name.replace('-', '_').split('_')
        if len(words) == 1:
            return words[0].lower()
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    @staticmethod
    def generate_route_path(table_name: str) -> str:
        """Generate REST API route path"""
        return f"/{table_name.lower().replace('_', '-')}"
